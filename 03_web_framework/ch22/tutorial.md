# Ch22 · 部署：uvicorn / gunicorn / Docker + 框架对比

> **预计**：0.5 天 ｜ **前置**：Ch16（依赖注入）、Ch20（测试）｜ **M3 收官**
> **目标**：把 FastAPI 应用送上生产——理解 ASGI/uvicorn/gunicorn 的分工，会用 pydantic-settings 管配置，会做容量规划与上线前安全检查，能读懂生产级 Dockerfile，并清楚 FastAPI/Flask/Django 怎么选。

> 📐 **本教程的契约**：讲过的才考，考的必讲过。作业 8 处填空全部对应 §22.2–§22.6。

---

## 🗺️ 本章地图

**主线场景**：你负责的「订单服务 order-service」明天上线。作为发布工程师，你要走完这条真实流水线：

```
容量规划(算 worker 数) → 生成启动命令 → 读生产配置 → 打印脱敏配置(启动日志)
      → 生成 docker run 命令 → 上线前安全检查 → 暴露 /health 给 K8s 探针
```

**作业 ↔ 教程对应表**：

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `worker_count_for_cores` | §22.2 | gunicorn 容量规划公式 `2×CPU+1` |
| `build_gunicorn_command` | §22.2 | gunicorn + uvicorn worker 命令行 |
| `get_settings` | §22.3 | pydantic-settings + `lru_cache` 单例依赖 |
| `mask_secret` | §22.3 | 配置脱敏（日志安全） |
| `safe_config_dict` | §22.3 | `model_dump()` + 脱敏后打启动日志 |
| `build_docker_run_command` | §22.4 | `docker run -e` 注入环境变量 |
| `health` | §22.5 | `Depends(get_settings)` + 健康检查端点 |
| `check_production_readiness` | §22.6 | 上线前检查清单（把坑列表变成代码） |

---

## ⏱️ 学习路径：费曼五步（约 60 分钟）

| 步骤 | 做什么 | 时间 |
|------|--------|------|
| ① 预览猜 | 先看下面 6 个问题，激活你的 Tomcat/Spring Boot 直觉 | 5 min |
| ② 先动手 | 打开 `ch22_assignment.py`，不看答案先试着填 | 20 min |
| ③ pytest 红绿 | 跑测试，红 → 对照对应 § → 改 → 绿，逐个点亮 | 20 min |
| ④ 费曼 | 合上教程，讲清 §22.2（GIL 与多进程）、§22.4（层缓存） | 10 min |
| ⑤ 存闪卡 | 把 `review.md` 的闪卡过一遍，标记掌握度 | 5 min |

---

## ① 预览猜（先想，别急着翻答案）

1. Java Web 用 Tomcat/Jetty 当 Servlet 容器。FastAPI 跑在什么「服务器」上？它自己能监听端口吗？
2. 开发要热重载，生产要多进程扛并发。分别用什么命令？为什么 Python 生产必须多进程而 Java 多线程就够？
3. Spring Boot 配置用 `application.yml` + `@ConfigurationProperties`。FastAPI 怎么从环境变量/`.env` 读配置并类型校验？
4. 启动日志里想打印当前配置确认无误，但 `secret_key` 直接打出来会怎样？怎么处理？
5. Java 用 jib / Spring Boot layered jar。Python 的 Dockerfile 怎么写才镜像小、层缓存好？
6. 上线前 5 分钟，你会检查哪几项配置？（提示：DEBUG、SECRET_KEY、数据库）

---

## §22.1 ASGI + uvicorn：开发服务器 🟢

FastAPI 本身只是个**应用框架**，不会自己监听端口——需要一个 **ASGI 服务器**跑它。

**ASGI**（Asynchronous Server Gateway Interface）= 异步版 WSGI。分层关系：

```
请求 → ASGI 服务器(uvicorn) → FastAPI 应用 → 你的端点函数
             ≈ Tomcat          ≈ Spring MVC     ≈ @GetMapping 方法
```

> 🟢 **Java 对照最小例**：`uvicorn main:app` 里的 `main:app` ≈ 指向主类的 `com.example.Application`。uvicorn ≈ Tomcat，只不过它跑的是 ASGI 应用而不是 Servlet。

**真实场景例**（跑本章的作业 app）：

```bash
uv run uvicorn 03_web_framework.ch22.ch22_assignment:app --reload --port 8000
#   └─ 模块:变量 ──────────────────────┘        └─ 改代码自动重启
curl http://localhost:8000/health
```

> ❌ **错误写法**：生产环境也带 `--reload`。它靠 fork 子进程 + 文件监控实现热重载，既吃性能又不稳定。
> ✅ **正确写法**:`--reload` 只在开发用；生产用 §22.2 的 gunicorn（或容器内单进程 uvicorn）。

---

## §22.2 gunicorn：生产多进程与容量规划（对应：`worker_count_for_cores` / `build_gunicorn_command`）🔴

### 为什么单进程 uvicorn 上不了生产

uvicorn 默认**单进程单线程**（一个事件循环）。两个问题：

1. **用不了多核**:Python 有 **GIL**（全局解释器锁），单进程内开再多线程，同一时刻也只有一个线程在执行 Python 字节码。想用满 8 核 CPU，只能开 8 个**进程**。
2. **单点故障**：唯一的进程崩了 = 服务全挂。

> 🔴 **Java 最大差异**:Java 没有 GIL，`new Thread()` 开 8 个线程就能用满 8 核。所以 Tomcat 一个进程 + 线程池搞定的事，Python 必须靠**多进程**。这是全章最重要的认知差异。

### gunicorn = 进程管理器

**gunicorn** 起 N 个 worker 进程，每个 worker 是一个 uvicorn 实例；worker 挂了自动拉起，请求在 worker 间负载均衡：

```bash
uv run gunicorn 03_web_framework.ch22.ch22_assignment:app \
    -w 4 \                              # 4 个 worker 进程
    -k uvicorn.workers.UvicornWorker \  # worker 类型:用 uvicorn 跑(支持 ASGI/异步)
    -b 0.0.0.0:8000                     # 监听地址
```

> 🟡 **Java 对比**:gunicorn ≈ 「Nginx + 多个 Tomcat 实例」的一体化——Master 进程管 worker，类似 Nginx 的 master/worker 模型。

### 容量规划：worker 数怎么定（对应 `worker_count_for_cores`）

gunicorn 官方推荐公式：**`workers = 2 × CPU核数 + 1`**。依据：worker 一半时间在等 IO（DB、下游 API），2 倍核数能让 CPU 在 IO 等待时不闲着；+1 是经验余量。

> 🟢 **Java 对照最小例**:≈ Tomcat 连接器线程数估算（IO 密集型 `线程数 ≈ 核数 × (1 + 平均等待/平均计算)`)，只是 Python 这边单位是**进程**不是线程。

**真实场景例**:order-service 部署到 4 核容器，发布脚本里算 worker 数：

```python
def worker_count_for_cores(cpu_cores: int) -> int:
    return max(1, 2 * cpu_cores + 1)   # 下限 1:0 核/异常值也不能起 0 个进程

worker_count_for_cores(4)   # → 9   (2×4+1)
worker_count_for_cores(1)   # → 3
worker_count_for_cores(0)   # → 1   (防御:max(1, ...) 兜底)
```

> ✅ 做 `worker_count_for_cores` 题：一行 `max(1, 2 * cpu_cores + 1)`。注意 0 和负数都要兜到 1。

### 命令是数据：生成 gunicorn 命令（对应 `build_gunicorn_command`）

发布系统/部署脚本里，命令通常**用 list 拼出来**再交给进程执行（M4 的 `subprocess.run(list)` 就吃这个）：

```python
def build_gunicorn_command(app_target: str, workers: int, port: int) -> list[str]:
    return [
        "gunicorn", app_target,
        "-w", str(workers),
        "-k", "uvicorn.workers.UvicornWorker",
        "-b", f"0.0.0.0:{port}",
    ]

build_gunicorn_command("order_service.main:app", 9, 8000)
# → ['gunicorn', 'order_service.main:app', '-w', '9',
#    '-k', 'uvicorn.workers.UvicornWorker', '-b', '0.0.0.0:8000']
```

> ❌ **错误写法**：拼成一个长字符串 `f"gunicorn {app} -w {workers} ..."` 再 `shell=True` 执行——参数里有空格/特殊字符就被 shell 截断，还有注入风险。
> ✅ **正确写法**：始终用 `list[str]`，一个参数一个元素；数字参数用 `str(workers)` 显式转。

| 场景 | 用什么 |
|------|--------|
| 开发 | `uvicorn --reload`（单进程，热重载） |
| 裸机/虚机生产 | `gunicorn -w N -k uvicorn.workers.UvicornWorker`（多进程） |
| 容器/K8s | 单进程 uvicorn + 多 Pod 水平扩展（编排层做副本，容器内不再套 gunicorn） |

---

## §22.3 配置管理：pydantic-settings（对应：`get_settings` / `mask_secret` / `safe_config_dict`）🔴

生产配置（API key、DB 连接串、环境名）**绝不写进代码**。**pydantic-settings** 的 `BaseSettings` 自动从环境变量/`.env` 加载 + 类型校验：

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    app_name: str = "order-service"
    environment: str = "dev"          # dev / staging / prod
    debug: bool = True
    database_url: str = "sqlite:///./app.db"
    secret_key: str = "dev-secret-change-me"
    redis_url: str | None = None      # 可选:不设就是 None
```

> 🟢 **Java 对照最小例**：整个 `Settings` ≈ Spring Boot 的 `@ConfigurationProperties(prefix="app")` + `application.yml`。字段即配置项，类型自动校验转换。

**真实场景例**（环境变量覆盖默认值，字符串自动转类型）：

```bash
export ENVIRONMENT=prod
export DEBUG=false                      # 字符串 "false" → bool False
export ACCESS_TOKEN_EXPIRE_MINUTES=120  # 字符串 "120"   → int 120
```

```python
Settings().environment   # → "prod"(环境变量优先于默认值)
Settings().debug         # → False(自动类型转换;"true/1/yes/on" → True)
```

类型转换失败**启动即报错**(fail-fast)——`ACCESS_TOKEN_EXPIRE_MINUTES=不是数字` 会在 `Settings()` 时抛 `ValidationError`,= Spring 启动校验失败直接拒绝启动。这比运行到一半才崩好得多。

> ❌ **错误写法**：配置散落在代码里 `os.getenv("DB_URL")`,读到的是字符串，`"false"` 当 bool 用永远是 truthy（非空字符串），debug 关不掉。
> ✅ **正确写法**：全部收敛到一个 `Settings(BaseSettings)`，类型校验 + 默认值 + 必填检查一站搞定。

### `get_settings`：lru_cache 单例依赖（对应作业）

```python
import functools

@functools.lru_cache
def get_settings() -> Settings:
    return Settings()           # lru_cache 缓存:一个进程只构造一次

@app.get("/health")
def health(settings: Settings = Depends(get_settings)):   # 注入(Ch16 模式)
    ...
```

**两个关键点**：

- `@lru_cache` 让 `get_settings()` 返回**同一实例**——读一次环境/`.env` 就缓存，不会每个请求都重新解析文件。
- 测试要重读环境变量时，调 `get_settings.cache_clear()` 清缓存（Ch09 学过 `lru_cache`，忘了回去翻）。

> ✅ 做 `get_settings` 题：装饰器已给好，函数体就一行 `return Settings()`。

### 配置脱敏：别把 secret 打进日志（对应 `mask_secret`）

服务启动时打印当前配置是好习惯（排障时一眼确认连的是哪个库），但 **`secret_key` 直接打出来 = 泄露**——日志会被收集到 ELK/Loki，看过日志的人都拿到了签名密钥。

> 🟢 **Java 对照最小例**:Spring 里给字段加 `@ToString.Exclude` / 自定义 `toString()` 打码；Python 这边自己写个 4 行函数。

**真实场景例**（脱敏规则：太短全遮，正常长度露前 4 位 + 总长，None/空串显示未设置）：

```python
def mask_secret(secret: str | None, visible: int = 4) -> str:
    if not secret:                          # None 和 "" 都是 falsy
        return "(unset)"
    if len(secret) <= visible:              # 太短:露前 4 位就等于全露了
        return "***"
    return f"{secret[:visible]}...({len(secret)} chars)"

mask_secret("super-secret-xyz")   # → "supe...(16 chars)"
mask_secret("abc")                # → "***"
mask_secret(None)                 # → "(unset)"
```

露前几位 + 总长的格式，排障时能区分「配错了」和「没配」（长度对不上 = 配错值），又不泄露内容。

> ✅ 做 `mask_secret` 题：`if not secret` 同时兜住 None 和空串；`len(secret) <= visible` 是边界。

### 打印启动配置：model_dump + 脱敏（对应 `safe_config_dict`）

pydantic 模型的 `model_dump()` 把实例转成 `dict`（= Java 里 `objectMapper.convertValue(obj, Map.class)`)。配合 `mask_secret`：

```python
def safe_config_dict(settings: Settings) -> dict:
    config = settings.model_dump()          # 全部字段 → dict
    config["secret_key"] = mask_secret(settings.secret_key)   # 只脱敏敏感字段
    return config

safe_config_dict(Settings())
# → {'app_name': 'order-service', ..., 'secret_key': 'dev-...(20 chars)', 'redis_url': None}
```

启动时 `logger.info("config loaded: %s", safe_config_dict(get_settings()))`,日志里配置全可见、密钥不泄露。

> ❌ **错误写法**:`logger.info(f"settings: {settings}")`——BaseSettings 的默认 repr 会带真实 `secret_key` 值。
> ✅ **正确写法**：日志只打 `safe_config_dict()` 的结果；养成「任何 dict 进日志前先过一遍敏感字段」的习惯。
>
> 🟡 延伸（不要求实现）:`database_url` / `redis_url` 里也常带密码（`postgresql://user:PASS@db/...`),严格场景要用 `urllib.parse` 把密码段也打码。

---

## §22.4 Docker：多阶段构建 + 运行时注入配置（对应：`build_docker_run_command`）🟡

项目里的 `Dockerfile`（读它对照本节）用**多阶段构建**，逐行讲：

**第 1 阶段 builder**——装依赖：

```dockerfile
FROM python:3.14-slim AS builder              # slim 而非 alpine:C 扩展 wheels 直接可用
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/   # 装 uv
WORKDIR /app
COPY pyproject.toml uv.lock ./                # ★ 先只拷依赖文件(层缓存关键)
RUN uv sync --frozen --no-dev --extra web     # 装依赖到 .venv
```

**第 2 阶段 runtime**——最终镜像：

```dockerfile
FROM python:3.14-slim AS runtime
COPY --from=builder /app/.venv /app/.venv     # 只拷装好的 venv(不带构建工具)
COPY 03_web_framework/ ./03_web_framework/    # 拷源码(变化最频繁,放最后)
RUN useradd -m appuser && chown -R appuser /app
USER appuser                                  # 非 root 跑(安全)
CMD ["uvicorn", "03_web_framework.ch22.ch22_assignment:app", "--host", "0.0.0.0", "--port", "8000"]
```

**为什么多阶段**：

- **镜像小**:runtime 阶段不带 gcc/uv/构建缓存（builder 的中间层被整体丢弃）。
- **层缓存**:`COPY pyproject.toml uv.lock` 在前（依赖不常变）,`COPY 源码` 在后（天天变）。改业务代码不会触发重装依赖。

> 🟡 **Java 对比**：多阶段 ≈ Spring Boot layered jar / jib 分层；`COPY 依赖文件在前` ≈ Maven `dependency:go-offline` 先拉依赖再编源码；非 root 跑 ≈ 不用 root 起 jar。

### 运行时注入配置：docker run -e（对应 `build_docker_run_command`）

§22.3 的 `Settings` 读环境变量，容器里环境变量靠 `docker run -e KEY=VALUE` 注入（K8s 里就是 `env:` / `Secret`)。发布脚本生成命令：

```python
def build_docker_run_command(image: str, port: int, env: dict[str, str] | None = None) -> list[str]:
    cmd = ["docker", "run", "-d", "-p", f"{port}:8000"]
    for key in sorted(env or {}):              # 排序:同一输入永远生成同一命令(可测试、可 diff)
        cmd += ["-e", f"{key}={env[key]}"]
    return cmd + [image]

build_docker_run_command("order-service:1.0.0", 8000,
                         {"SECRET_KEY": "x" * 32, "DATABASE_URL": "postgresql://db/orders"})
# → ['docker', 'run', '-d', '-p', '8000:8000',
#    '-e', 'DATABASE_URL=postgresql://db/orders', '-e', 'SECRET_KEY=xxxx...', 'order-service:1.0.0']
```

> ❌ **错误写法**：遍历 `dict` 不排序直接拼——Python 3.7+ dict 保序（插入序），但调用方构造顺序不同，生成的命令就不同，diff 和测试都不稳定。
> ✅ 做 `build_docker_run_command` 题：`sorted(env or {})` 遍历；每个环境变量拆成 `"-e"` 和 `"KEY=VALUE"` 两个元素；镜像名放最后。

---

## §22.5 健康检查端点（对应：`health`）🟢

生产部署（K8s/Docker）的 **liveness/readiness 探针**会定时打这个端点，判断应用是否活着：

```python
@app.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "version": APP_VERSION,
        "debug": settings.debug,
    }
```

> 🟢 **Java 对照最小例**:= Spring Boot Actuator 的 `/actuator/health`。

**真实场景例**：本章 `Dockerfile` 里配了 `HEALTHCHECK`，每 30s 打一次 `/health`，连续 3 次失败 Docker 就判定容器 unhealthy；K8s 的 `livenessProbe` 同理，失败就重启 Pod。

> ✅ 做 `health` 题：按上面 dict 返回即可。注意 `version` 用模块常量 `APP_VERSION`。

---

## §22.6 上线前检查清单（对应：`check_production_readiness`）🔴

§22.8 的坑列表，高手会把它**变成代码**：上线流水线里跑一个检查函数，有问题直接拦住发布。order-service 的清单：

```python
def check_production_readiness(settings: Settings) -> list[str]:
    """返回配置问题列表;空列表 = 可以上线。"""
    problems = []
    if settings.environment == "prod" and settings.debug:
        problems.append("生产环境必须关闭 DEBUG")
    if settings.secret_key == DEFAULT_SECRET_KEY:
        problems.append("SECRET_KEY 仍是开发默认值,必须更换")
    if len(settings.secret_key) < 16:
        problems.append("SECRET_KEY 太短(至少 16 字符)")
    if settings.environment == "prod" and settings.database_url.startswith("sqlite"):
        problems.append("生产环境不应使用 SQLite")
    return problems
```

**真实场景例**（同一份配置，不同环境结论不同）：

```python
# 全默认的开发配置:只有 secret 默认值这 1 条提醒(dev 用 sqlite 没问题)
check_production_readiness(Settings())
# → ['SECRET_KEY 仍是开发默认值,必须更换']

# 直接拿默认配置上 prod:3 条问题,流水线直接拒绝发布
check_production_readiness(Settings(environment="prod"))
# → ['生产环境必须关闭 DEBUG', 'SECRET_KEY 仍是开发默认值,必须更换',
#    '生产环境不应使用 SQLite']

# 换了个太短的 secret:默认值那条没了,撞上"太短"那条
check_production_readiness(Settings(environment="prod", secret_key="abc"))
# → ['生产环境必须关闭 DEBUG', 'SECRET_KEY 太短(至少 16 字符)',
#    '生产环境不应使用 SQLite']
```

> 🔴 **认知点**:**返回问题列表而不是抛异常**——检查清单的价值在于一次看全所有问题（= Maven 构建失败时列出全部编译错误，而不是只报第一个）。调用方判断 `if problems: 拒绝发布`。

> ✅ 做 `check_production_readiness` 题：四个 `if` 各 append 一条，最后返回。顺序固定（测试按顺序断言）。注意「dev 用 sqlite」不算问题——环境问题才拦。

---

## §22.7 FastAPI vs Flask vs Django 怎么选

|  | FastAPI | Flask | Django |
|---|---|---|---|
| **类型注解** | ✅ 原生（驱动一切） | ❌ | 部分（DRF） |
| **异步** | ✅ 原生 | ⚠️ 弱 | 部分 |
| **自动文档** | ✅ /docs 开箱即用 | 需 flask-restx | 需 drf-yasg |
| **ORM** | 无（配 SQLAlchemy） | 无 | ✅ 自带 Django ORM |
| **Admin 后台** | ❌ | ❌ | ✅ 自带 |
| **学习曲线** | 中（类型驱动） | 低 | 高（全家桶） |
| **定位** | 现代 API 服务 | 轻量灵活 | 全栈全家桶 |
| **≈ Java** | Spring Boot（现代） | 轻量 Servlet | Spring 全家桶 + Admin |

**选型**：

- **新项目做 API/微服务** → **FastAPI**（现代、类型安全、异步、文档零配置）。本课程主线。
- **老项目维护/极简脚本** → Flask。
- **全栈（admin/ORM/auth 全要）+ 大团队** → Django(= Spring 全家桶)。

> 掌握 FastAPI 后，迁移到 Flask/Django 成本很低（路由/请求处理概念通用）。

---

## §22.8 Java 老手常踩的坑 ⚠️

1. **生产忘加 gunicorn**：单进程 uvicorn 撑不住，崩了全挂。裸机生产 gunicorn 多 worker；K8s 里靠多 Pod。
2. **GIL**：单进程多线程**不能**用多核 CPU。要用多核得**多进程**(`gunicorn -w`）或多容器。Java 多线程就行，这是最大区别。
3. **`--reload` 进生产**：有性能开销和稳定性问题，只开发用。
4. **配置硬编码**:`SECRET_KEY`/`DATABASE_URL` 绝不进代码。用 pydantic-settings + 环境变量。
5. **secret 打进日志**:`logger.info(f"{settings}")` 直接泄露。用 `safe_config_dict` 脱敏。
6. **Dockerfile 拷源码在前**：改代码就重装依赖（缓存失效）。依赖文件（pyproject/lock）拷在前。
7. **root 跑容器**：安全风险。用非 root 用户。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `worker_count_for_cores` | gunicorn 容量公式 `2×CPU+1` | 🟢 |
| `build_gunicorn_command` | 命令是 list[str] 数据 | 🟢 |
| `get_settings` | pydantic-settings + lru_cache | 🟢 |
| `mask_secret` | 配置脱敏 | 🟢 |
| `safe_config_dict` | model_dump + 脱敏 | 🟢 |
| `build_docker_run_command` | docker run -e 注入配置 | 🟡 |
| `health` | 健康检查端点 | 🟢 |
| `check_production_readiness` | 上线前检查清单（小综合） | 🟡 |

```bash
uv run pytest 03_web_framework/ch22/test_ch22_assignment.py -v
```

（另：读 `Dockerfile` + `.env.example`，对照 §22.4 理解多阶段构建）

---

## ✅ 自测

- [ ] 能说清 uvicorn（开发）vs gunicorn（生产）的区别
- [ ] 知道 GIL 导致 Python 必须多进程用多核（和 Java 多线程的区别）
- [ ] 会算 worker 数：`2×CPU+1`，能解释为什么
- [ ] 会用 pydantic-settings 从环境变量读配置 + 类型校验
- [ ] 知道为什么 secret 不能进日志，会用 mask + model_dump 打安全启动日志
- [ ] 能读懂多阶段 Dockerfile，知道为什么依赖文件拷在前
- [ ] 能把上线前检查清单写成代码（返回问题列表而非抛异常）
- [ ] 能说清 FastAPI/Flask/Django 怎么选
- [ ] 8 个作业全绿

## 🎓 费曼挑战

1. 「为什么 Python 生产要用 gunicorn 多 worker，而 Java 多线程就够了？」— 重读 §22.2(GIL)
2. 「Dockerfile 为什么把 `COPY pyproject.toml uv.lock` 放在 `COPY 源码` 前面？」— 重读 §22.4（层缓存）
3. 「为什么检查清单返回 list 而不是发现第一个问题就抛异常？」— 重读 §22.6

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ M3 毕业 → 考试系统 Lab

恭喜！**Ch13–22 全部学完，M3 FastAPI 模块毕业** 🎓。你现在能：调 API(httpx)→ 写 API(FastAPI+Pydantic)→ 参数路由 → 依赖注入 → 中间件/异常 → 异步 → 数据库（SQLAlchemy)→ 测试 → JWT 认证 → **部署上线**。

下一站是**考试系统 Lab**(`03_web_framework/lab/`)——综合用 Ch16 依赖注入 + Ch19 SQLAlchemy + Ch21 JWT，搭一个完整的考试系统。需求等你来定，我们讨论后开干。
