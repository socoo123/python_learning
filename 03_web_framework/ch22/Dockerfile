# Ch22 · Dockerfile 多阶段构建(FastAPI + uvicorn 生产镜像)
# 对应 tutorial.md §22.4。逐行讲解见教程。

# ===== 第 1 阶段:builder(装依赖到独立虚拟环境)=====
# 选 slim 而非 alpine:Python 编译扩展(C 扩展)在 alpine 上要装 gcc/musl,
# 反而更慢更大。slim 是基于 Debian 的精简版, wheels 直接可用。
FROM python:3.14-slim AS builder

# 装uv(比 pip 快 10-100x,= Maven 的依赖加速器)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 设工作目录
WORKDIR /app

# 打开 bytecode 编译(--system 表示直接装到系统解释器,不建额外 venv)
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# 关键:先只拷 pyproject.toml + uv.lock,利用 Docker 层缓存。
# 源码天天变,但依赖不常变 —— 这样改业务代码不会重装依赖(= Maven 分层)。
COPY pyproject.toml uv.lock ./

# 只装 web 这一组依赖到 .venv(开发/生产统一用 uv sync)
RUN uv sync --frozen --no-dev --extra web

# ===== 第 2 阶段:runtime(最终镜像,小而干净)=====
FROM python:3.14-slim AS runtime

# 运行时不需要 gcc/构建工具 → 镜像更小、攻击面更小。
# 装最小运行依赖(如 libpq 给 postgres 客户端,按需)
# RUN apt-get update && apt-get install -y --no-install-recommends libpq5 \
#     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 从 builder 拷整个虚拟环境(已装好依赖)
COPY --from=builder /app/.venv /app/.venv

# 拷应用源码(变化最频繁,放最后)
COPY 03_web_framework/ ./03_web_framework/

# 用非 root 用户跑应用(安全最佳实践,= 不用 root 跑 jar)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 把虚拟环境加到 PATH,uvicorn 直接可调
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# 健康检查:打 /health 端点(对应 ch22_assignment.health)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

# 生产启动:uvicorn 单进程。
# 真实高并发用 gunicorn + uvicorn worker(见 §22.2):
#   CMD ["gunicorn", "03_web_framework.ch22.ch22_assignment:app", \
#        "-w", "4", "-k", "uvicorn.workers.UvicornWorker", \
#        "-b", "0.0.0.0:8000"]
CMD ["uvicorn", "03_web_framework.ch22.ch22_assignment:app", \
     "--host", "0.0.0.0", "--port", "8000"]
