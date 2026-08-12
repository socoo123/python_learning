"""
Ch22 作业:部署 uvicorn/gunicorn/Docker + 框架对比。

主线场景:「订单服务 order-service」明天上线,你是发布工程师。8 个函数串成上线流水线:
  ① worker_count_for_cores   容量规划:算 gunicorn worker 数(§22.2)
  ② build_gunicorn_command   生成生产启动命令(§22.2)
  ③ get_settings             pydantic-settings 读配置,lru_cache 单例(§22.3)
  ④ mask_secret              配置脱敏,别让密钥进日志(§22.3)
  ⑤ safe_config_dict         打印脱敏后的启动配置(§22.3)
  ⑥ build_docker_run_command 生成 docker run 命令,注入环境变量(§22.4)
  ⑦ health                   /health 健康检查端点,给 K8s 探针用(§22.5)
  ⑧ check_production_readiness 上线前安全检查清单(§22.6)

Dockerfile(多阶段构建)在同目录,是文件交付,对照 §22.4 读,不进 pytest。

    uv run pytest 03_web_framework/ch22/test_ch22_assignment.py -v

每题【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
import functools

from fastapi import Depends, FastAPI
from pydantic_settings import BaseSettings, SettingsConfigDict

# 应用版本(写死,演示;真实项目从 pyproject.toml 或 git tag 读)
APP_VERSION = "1.0.0"

# 开发用默认密钥。它出现在代码里只是为了本地能跑;生产必须用环境变量覆盖,
# 否则任何看过源码的人都能伪造 JWT/会话(Ch21)。
DEFAULT_SECRET_KEY = "dev-secret-change-me"


# ---------- §22.3 配置管理:Settings(pydantic-settings)----------


class Settings(BaseSettings):
    """应用配置。从环境变量(或 .env 文件)自动加载,带类型校验。

    对应 §22.3。等价于 Spring Boot 的 @ConfigurationProperties —— 字段即配置项,
    类型自动校验转换;类型不符(如 ACCESS_TOKEN_EXPIRE_MINUTES="abc")实例化即
    抛 ValidationError(fail-fast,= Spring 启动校验)。

    字段说明(全部有默认,开发零配置能跑;生产用环境变量覆盖):
        app_name:        应用名,默认 "order-service"
        environment:     运行环境 dev/staging/prod,默认 "dev"
        debug:           是否调试模式,默认 True(生产必须 false)
        database_url:    数据库连接串,默认 sqlite(生产必须换)
        secret_key:      JWT/会话密钥,默认开发值(生产必须换)
        access_token_expire_minutes: token 有效期分钟数,默认 30
        redis_url:       Redis 连接串,可选(默认 None)
    """
    model_config = SettingsConfigDict(
        env_file=".env",          # 自动读项目根的 .env 文件
        env_file_encoding="utf-8",
        case_sensitive=False,     # DATABASE_URL / database_url 都能匹配
        extra="ignore",           # .env 里多余的字段忽略(不报错)
    )

    app_name: str = "order-service"
    environment: str = "dev"
    debug: bool = True
    database_url: str = "sqlite:///./app.db"
    secret_key: str = DEFAULT_SECRET_KEY
    access_token_expire_minutes: int = 30
    redis_url: str | None = None


# ---------- §22.2 容量规划:gunicorn worker 数 ----------


def worker_count_for_cores(cpu_cores: int) -> int:
    """【场景】order-service 部署到 N 核容器,发布脚本要算 gunicorn 起几个 worker。

    对应 §22.2。gunicorn 官方推荐公式:workers = 2 × CPU核数 + 1
    (worker 一半时间在等 IO,2 倍核数让 CPU 不闲着;+1 是经验余量)。
    Python 有 GIL,单进程多线程用不满多核,所以单位是「进程」不是「线程」。

    示例:
        worker_count_for_cores(4)  -> 9     # 2×4+1
        worker_count_for_cores(1)  -> 3
        worker_count_for_cores(0)  -> 1     # 下限兜底:总不能起 0 个进程
        worker_count_for_cores(-2) -> 1     # 异常输入也兜到 1

    提示:一行搞定,max(下限, 公式)。想想下限是多少。
    """
    # TODO: 返回 max(下限, 2×核数+1)
    ...


# ---------- §22.2 生成生产启动命令 ----------


def build_gunicorn_command(app_target: str, workers: int, port: int) -> list[str]:
    """【场景】发布系统要拉起 order-service,用 list 拼出 gunicorn 命令交给 subprocess。

    对应 §22.2。生产命令形如下面的字符串,但代码里永远用 list[str] 表示
    (一个参数一个元素,避免 shell 截断/注入,M4 subprocess 直接吃这个):

        gunicorn order_service.main:app -w 9 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

    示例:
        build_gunicorn_command("order_service.main:app", 9, 8000)
        -> ["gunicorn", "order_service.main:app",
            "-w", "9", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]

        build_gunicorn_command("ch22_assignment:app", 3, 9000)
        -> ["gunicorn", "ch22_assignment:app",
            "-w", "3", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:9000"]

    提示:数字参数要 str() 转换(list 里必须全是 str);监听地址用 f-string 拼。
    """
    # TODO: 返回 ["gunicorn", app_target, "-w", str(...), "-k", "uvicorn.workers.UvicornWorker", "-b", ...]
    ...


# ---------- §22.3 get_settings 依赖(lru_cache 单例)----------


@functools.lru_cache
def get_settings() -> Settings:
    """返回全局唯一 Settings 实例(lru_cache 缓存)。

    对应 §22.3。这是 FastAPI 生产配置的标准模式:
      ① 用 lru_cache 保证一个进程只构造一次 Settings(读一次环境/文件),
         避免每个请求都重新解析 .env。
      ② 端点用 Depends(get_settings) 注入(Ch16 模式),测试时可替换。
      ③ 测试需要重读环境变量时,调 get_settings.cache_clear() 清缓存。

    示例:
        s1 = get_settings(); s2 = get_settings()
        s1 is s2            # -> True(缓存生效,同一实例)
        s1.app_name         # -> "order-service"(或环境变量 APP_NAME 的值)

    提示:装饰器已给好,函数体就一行——构造并返回 Settings 实例,
    缓存的事 lru_cache 自动做。
    """
    # TODO: 构造并返回 Settings 实例(lru_cache 会自动缓存)
    ...


# ---------- §22.3 配置脱敏:密钥不进日志 ----------


def mask_secret(secret: str | None, visible: int = 4) -> str:
    """【场景】启动日志要打印配置,但 secret_key 直接打出来 = 泄露给所有能看日志的人。

    对应 §22.3。脱敏规则:
      - None 或空串 -> "(unset)"(排障时能区分「没配」和「配错」)
      - 长度 <= visible -> "***"(太短,露前几位就等于全露)
      - 否则 -> 前 visible 位 + "..." + "(总长度 chars)"

    示例:
        mask_secret("super-secret-xyz")  -> "supe...(16 chars)"
        mask_secret("abc")               -> "***"       # 长度 3 <= 4
        mask_secret(None)                -> "(unset)"
        mask_secret("")                  -> "(unset)"

    提示:`if not secret` 能同时兜住 None 和空串;切片 secret[:visible] 取前几位。
    """
    # TODO: None/空 -> "(unset)";长度<=visible -> "***";否则 前visible位 + "...(N chars)"
    ...


# ---------- §22.3 打印脱敏后的启动配置 ----------


def safe_config_dict(settings: Settings) -> dict:
    """【场景】服务启动时打一行配置日志,排障一眼确认连的是哪个库、什么环境。

    对应 §22.3。用 model_dump() 把 Settings 转成 dict(= Jackson 的
    objectMapper.convertValue(obj, Map.class)),再把 secret_key 替换成脱敏值。

    示例:
        d = safe_config_dict(Settings())
        d["app_name"]      -> "order-service"
        d["secret_key"]    -> mask_secret("dev-secret-change-me"),即 "dev-...(20 chars)"
        d["environment"]   -> "dev"(原样,不敏感)

        s = Settings(secret_key="abc")
        safe_config_dict(s)["secret_key"]  -> "***"

    提示:先 dump 再覆盖敏感字段——config = settings.model_dump();
    config["secret_key"] = mask_secret(...)。复用上面的 mask_secret。
    """
    # TODO: model_dump() 转 dict → 用 mask_secret 覆盖 secret_key → 返回
    ...


# ---------- §22.4 生成 docker run 命令 ----------


def build_docker_run_command(image: str, port: int, env: dict[str, str] | None = None) -> list[str]:
    """【场景】发布脚本生成 docker run 命令:后台跑、端口映射、注入生产环境变量。

    对应 §22.4。Settings 从环境变量读配置,容器里环境变量靠 -e KEY=VALUE 注入。
    命令形如(list 形式):

        docker run -d -p 8000:8000 -e DATABASE_URL=... -e SECRET_KEY=... order-service:1.0.0

    示例:
        build_docker_run_command("order-service:1.0.0", 8000,
                                 {"SECRET_KEY": "abc", "DATABASE_URL": "postgresql://db/orders"})
        -> ["docker", "run", "-d", "-p", "8000:8000",
            "-e", "DATABASE_URL=postgresql://db/orders",
            "-e", "SECRET_KEY=abc", "order-service:1.0.0"]

        build_docker_run_command("order-service:1.0.0", 8000)      # 无环境变量
        -> ["docker", "run", "-d", "-p", "8000:8000", "order-service:1.0.0"]

    提示:
      - env 按 key 排序遍历(sorted)——同一输入永远生成同一命令,可测试、可 diff。
      - 每个环境变量拆成 "-e" 和 "KEY=VALUE" 两个元素。
      - env 可能为 None,`env or {}` 兜底;镜像名放最后。
    """
    # TODO: ["docker","run","-d","-p",f"{port}:8000"] + 按序追加 "-e"/"K=V" + 镜像名
    ...


# ---------- §22.1 ASGI app + §22.5 健康检查端点 ----------

app = FastAPI(
    title="order-service",
    description="Ch22 部署演示:配置 + 健康检查",
    version=APP_VERSION,
)


@app.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict:
    """【场景】K8s/Docker 探针定时打 /health 判断 order-service 是否活着。

    对应 §22.5。= Spring Boot Actuator 的 /actuator/health。
    用 Depends(get_settings) 注入配置(Ch16 模式),返回应用名/环境/版本/调试开关,
    排障时一眼看出「这个 Pod 跑的是什么配置」。Dockerfile 的 HEALTHCHECK 就打它。

    示例(TestClient 实测):
        GET /health  -> 200
        {"status": "ok", "app": "order-service", "environment": "dev",
         "version": "1.0.0", "debug": true}

        设 ENVIRONMENT=prod 且 get_settings.cache_clear() 后再打:
        -> body["environment"] == "prod"

    提示:返回 dict,五个 key——status 写死 "ok";version 用模块常量 APP_VERSION;
    其余从注入的 settings 上取。
    """
    # TODO: 返回 dict(status="ok" / app / environment / version=APP_VERSION / debug)
    ...


# ---------- §22.6 上线前安全检查清单 ----------


def check_production_readiness(settings: Settings) -> list[str]:
    """【场景】发布流水线最后一步:自动检查配置,有问题直接拒绝上线。

    对应 §22.6。把 §22.8 的坑列表变成代码。依次检查 4 条(顺序固定,测试按序断言):
      ① prod 环境却开着 DEBUG
      ② SECRET_KEY 仍是开发默认值(= DEFAULT_SECRET_KEY)
      ③ SECRET_KEY 太短(少于 16 字符,扛不住暴力破解)
      ④ prod 环境却用 SQLite(单文件库,扛不住并发写)

    返回问题描述列表;空列表 = 可以上线。注意是「收集全部问题」而不是
    发现第一个就抛异常——一次看全才好修(= Maven 列出全部编译错误)。

    示例:
        check_production_readiness(Settings())
        -> ["SECRET_KEY 仍是开发默认值,必须更换"]
        # dev 环境:DEBUG 和 sqlite 都不算问题,只有默认密钥要提醒

        check_production_readiness(Settings(environment="prod"))
        -> ["生产环境必须关闭 DEBUG",
            "SECRET_KEY 仍是开发默认值,必须更换",
            "生产环境不应使用 SQLite"]

        ok = Settings(environment="prod", debug=False,
                      secret_key="x" * 32, database_url="postgresql://db/orders")
        check_production_readiness(ok) -> []

    提示:四个 if 各 append 一条中文问题描述,最后返回 list。
    环境判断:settings.environment == "prod";SQLite 判断:database_url.startswith("sqlite")。
    """
    # TODO: problems=[] → 四个 if 依次检查(prod+debug / 默认密钥 / 密钥<16位 / prod+sqlite)→ 返回
    ...


# ---------- 启动命令速查(文档,不测)----------
#
# 开发(单进程,热重载):
#     uv run uvicorn ch22_assignment:app --reload --port 8000
#
# 生产(多进程,gunicorn + uvicorn worker,= build_gunicorn_command 的产物):
#     uv run gunicorn ch22_assignment:app \
#         -w 4 -k uvicorn.workers.UvicornWorker \
#         -b 0.0.0.0:8000
#
# Dockerfile 启动(容器内单进程,多副本靠 K8s):
#     CMD ["uvicorn", "ch22_assignment:app", "--host", "0.0.0.0", "--port", "8000"]
