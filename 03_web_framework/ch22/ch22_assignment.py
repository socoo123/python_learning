"""
Ch22 作业:部署 uvicorn/gunicorn/Docker + 框架对比。

本章是工程化/理论章,pytest 可测部分轻量:
① Settings(pydantic-settings 的 BaseSettings)——从环境变量读配置
② get_settings() 依赖(lru_cache 缓存单例,Ch16 依赖注入模式)
③ /health 端点(用 get_settings 注入,暴露应用名/环境/版本)

Dockerfile(多阶段构建)在 §22.4 讲解,是文件交付,不进 pytest。

    uv run pytest 03_web_framework/ch22/test_ch22_assignment.py -v

每题【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
import functools

from fastapi import Depends, FastAPI
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 应用版本(写死,演示;真实项目从 pyproject.toml 或 git tag 读)
APP_VERSION = "1.0.0"


# ---------- §22.3 配置管理:Settings(pydantic-settings)----------


class Settings(BaseSettings):
    """应用配置。从环境变量(或 .env 文件)自动加载,带类型校验。

    对应 §22.3。等价于 Spring Boot 的 @ConfigurationProperties —— 字段即配置项,
    类型自动校验,缺失必填项启动即报错(fail-fast)。

    字段说明:
        app_name:        应用名,默认 "Product API"
        environment:     运行环境(dev/staging/prod),默认 "dev"
        debug:           是否调试模式,默认 True
        database_url:    数据库连接串【必填】(无默认 → 缺失即报错)
        secret_key:      JWT/会话密钥【必填】
        access_token_expire_minutes: token 有效期,默认 30
        redis_url:       Redis 连接串,可选(默认 None)
    """
    model_config = SettingsConfigDict(
        env_file=".env",          # 自动读项目根的 .env 文件
        env_file_encoding="utf-8",
        case_sensitive=False,     # DATABASE_URL / database_url 都能匹配
        extra="ignore",           # .env 里多余的字段忽略(不报错)
    )

    app_name: str = "Product API"
    environment: str = "dev"
    debug: bool = True
    database_url: str = Field(default="sqlite:///./app.db")  # 有默认 → 不必填
    secret_key: str = Field(default="dev-secret-change-me")
    access_token_expire_minutes: int = 30
    redis_url: str | None = None


# ---------- §22.3 get_settings 依赖(lru_cache 单例)----------


@functools.lru_cache
def get_settings() -> Settings:
    """返回全局唯一 Settings 实例(lru_cache 缓存)。

    对应 §22.3 / §22.4。这是 FastAPI 生产配置的标准模式:
      ① 用 lru_cache 保证一个进程只构造一次 Settings(读一次环境/文件),
         避免每个请求都重新解析 .env。
      ② 端点用 Depends(get_settings) 注入(Ch16 模式),测试时可替换。
      ③ 测试需要重读环境变量时,调 get_settings.cache_clear() 清缓存。

    思路:
        @functools.lru_cache 装饰函数,函数体就一行: return Settings()

    关键语法:@functools.lru_cache(无参,自动按「无参数」缓存单例)。
    测试断言:s1 = get_settings(); s2 = get_settings(); s1 is s2(同一实例)。

    返回:
        Settings: 全局配置单例。
    """
    # TODO: 构造并返回 Settings 实例(lru_cache 会自动缓存)
    ...


# ---------- §22.1 ASGI app + §22.3 注入配置 ----------

app = FastAPI(
    title="Product API",
    description="Ch22 部署演示:配置 + 健康检查",
    version=APP_VERSION,
)


@app.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict:
    """健康检查端点(= Spring Boot Actuator 的 /actuator/health)。

    用 Depends(get_settings) 注入配置,返回 app_name / environment / version / debug。
    生产部署里 K8s/Docker 的 liveness/readiness 探针就打这个端点。

    思路:
        return {
            "status": "ok",
            "app": settings.app_name,
            "environment": settings.environment,
            "version": APP_VERSION,
            "debug": settings.debug,
        }

    关键语法:Depends(get_settings)(Ch16)、settings.xxx 访问字段、APP_VERSION 是模块级常量。
    """
    # TODO: 返回 dict(status="ok" / app / environment / version=APP_VERSION / debug)
    ...


# ---------- §22.2 启动命令速查(文档,不测)----------
#
# 开发(单进程,热重载):
#     uv run uvicorn ch22_assignment:app --reload --port 8000
#
# 生产(多进程,gunicorn + uvicorn worker,= Tomcat 多连接器):
#     uv run gunicorn ch22_assignment:app \
#         -w 4 -k uvicorn.workers.UvicornWorker \
#         -b 0.0.0.0:8000
#
# Dockerfile 启动:
#     CMD ["uvicorn", "ch22_assignment:app", "--host", "0.0.0.0", "--port", "8000"]
