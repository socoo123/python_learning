# Ch22 · 部署:uvicorn / gunicorn / Docker + 框架对比

> **预计**:0.5 天 ｜ **前置**:Ch20 ｜ **M3 收官**
> **目标**:把 FastAPI 应用部署上生产——理解 ASGI/uvicorn/gunicorn,会写生产级 Dockerfile,用 pydantic-settings 管配置,并清楚 FastAPI/Flask/Django 怎么选。这是 M3 的收尾。

> 📐 **本教程的契约**:作业两处填空(get_settings / health,§22.3)。Dockerfile(§22.4)和部署命令(§22.1/§22.2)是文件/文档交付,不进 pytest。

---

## 🗺️ 本章地图

**作业 ↔ 教程对应表**:

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `get_settings` | §22.3 | pydantic-settings + lru_cache 单例依赖 |
| `health` 端点 | §22.5 | Depends(get_settings) + 健康检查 |

（Dockerfile §22.4、uvicorn/gunicorn §22.1/§22.2、框架对比 §22.6 是讲透+文件交付）

---

## ⏱️ 学习路径:费曼五步(约 45 分钟)

① 预览猜 → ② 填 get_settings/health → ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## ① 预览猜

1. Java Web 用 Tomcat/Jetty/Undertow 当 Servlet 容器。FastAPI 跑在什么「服务器」上?
2. 开发要热重载,生产要多进程扛并发。分别用什么命令?
3. Spring Boot 配置用 `application.yml` + `@Value`/`@ConfigurationProperties`。FastAPI 怎么从环境变量/`.env` 读配置并类型校验?
4. Java 用 jib/Spring Boot layered Docker。Python FastAPI 的 Dockerfile 怎么写才镜像小、层缓存好?
5. Flask/Django/FastAPI 三选一,新项目默认选哪个?为什么?

---

## §22.1 ASGI + uvicorn:开发服务器

FastAPI 本身只是个**应用框架**,它不会自己监听端口——需要一个 **ASGI 服务器**跑它。

**ASGI**(Asynchronous Server Gateway Interface)= 异步版 WSGI。FastAPI 是 ASGI 应用(支持异步),需要一个 ASGI 服务器承载。

```
请求 → ASGI 服务器(uvicorn)→ FastAPI 应用 → 你的端点
                ≈ Tomcat         ≈ Spring MVC 控制器
```

**uvicorn** 是最常用的 ASGI 服务器(基于 uvloop,快)。开发模式:

```bash
uv run uvicorn 03_web_framework.ch22.ch22_assignment:app --reload --port 8000
#                                              ↑ app 对象的路径(模块:变量)
#                                    --reload 改代码自动重启(开发用,生产别开)
```

> 🟡 **Java 对比**:uvicorn ≈ Tomcat(但它跑 ASGI 应用)。`模块:app` 的写法 ≈ 指向 main 类。

---

## §22.2 gunicorn + uvicorn worker:生产多进程

uvicorn 默认**单进程单线程**(事件循环)。单进程无法利用多核 CPU,也崩了就全挂。生产用 **gunicorn** 管理多个 **uvicorn worker**:

```bash
uv run gunicorn 03_web_framework.ch22.ch22_assignment:app \
    -w 4 \                              # 4 个 worker 进程(= 4 核)
    -k uvicorn.workers.UvicornWorker \  # 每个 worker 用 uvicorn 跑(支持异步)
    -b 0.0.0.0:8000                     # 监听地址
```

gunicorn 是「进程管理器」:起 N 个 worker,每个 worker 是一个 uvicorn 实例。worker 挂了自动重启,负载均衡。这是 Python Web 生产标准。

> 🟡 **Java 对比**:gunicorn 多 worker ≈ Tomcat 多连接器/多实例 + 负载均衡。Python 因为 **GIL**(全局解释器锁,单进程内多线程不能真并行 CPU),必须靠**多进程**用多核——这是和 Java 最大的不同(Java 多线程就能用多核)。

| 场景 | 用什么 |
|------|--------|
| 开发 | `uvicorn --reload`(单进程,热重载) |
| 生产 | `gunicorn -w N -k uvicorn.workers.UvicornWorker`(多进程) |
| 容器/K8s | 单进程 uvicorn + 用 K8s 多 Pod 水平扩展(容器编排层面做多副本) |

---

## §22.3 配置管理:pydantic-settings(对应:`get_settings`)🔴

生产配置(API key、DB 连接、环境)绝不通进代码。**pydantic-settings** 的 `BaseSettings` 自动从环境变量/`.env` 加载 + 类型校验:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    app_name: str = "Product API"                    # 有默认
    database_url: str = "sqlite:///./app.db"
    debug: bool = True
    secret_key: str                                  # 无默认 = 必填(缺失启动报错 fail-fast)
    redis_url: str | None = None                     # 可选

s = Settings()           # 自动读环境变量 + .env,类型校验
s.debug                  # True(环境变量 DEBUG=false 会转成 bool False)
```

> 🟡 **Java 对比**:= Spring Boot 的 `@ConfigurationProperties` + `application.yml`。字段即配置项,类型自动校验,缺必填项**启动即报错**(fail-fast,比运行时才崩好)。

### `get_settings`:lru_cache 单例依赖(对应作业)

```python
import functools

@functools.lru_cache
def get_settings() -> Settings:
    return Settings()           # lru_cache 缓存:一个进程只构造一次

@app.get("/health")
def health(settings: Settings = Depends(get_settings)):   # 注入(Ch16 模式)
    return {"app": settings.app_name, ...}
```

**两个关键点**:
- `@lru_cache` 让 `get_settings()` 返回**同一实例**(读一次环境就缓存,不每请求重读)。
- `Depends(get_settings)` 注入,测试时可用 `app.dependency_overrides` 替换(Ch20 学过)。测试要重读环境变量时调 `get_settings.cache_clear()`。

> ✅ 做 `get_settings` 题:`@functools.lru_cache` + `return Settings()`。

---

## §22.4 Docker 多阶段构建(文件交付,Dockerfile 逐行讲)

项目里的 `Dockerfile`(读它对照本节)用**多阶段构建**:

**第 1 阶段 builder**——装依赖:
```dockerfile
FROM python:3.14-slim AS builder              # slim 而非 alpine(C 扩展 wheels 直接可用)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/   # 装 uv
COPY pyproject.toml uv.lock ./                # ★ 先只拷依赖文件(层缓存关键)
RUN uv sync --frozen --no-dev --extra web     # 装依赖到 .venv
```

**第 2 阶段 runtime**——最终镜像:
```dockerfile
FROM python:3.14-slim AS runtime
COPY --from=builder /app/.venv /app/.venv     # 只拷装好的 venv(不带构建工具)
COPY 03_web_framework/ ./03_web_framework/    # 拷源码(放最后,变化最频繁)
RUN useradd -m appuser && USER appuser        # 非 root 跑(安全)
CMD ["uvicorn", "...:app", "--host", "0.0.0.0", "--port", "8000"]
```

**为什么多阶段**:
- **镜像小**:runtime 阶段不带 gcc/构建工具(builder 阶段的中间层被丢弃)。
- **层缓存**:`COPY pyproject.toml uv.lock` 在前(依赖不常变),`COPY 源码`在后(常变)。改业务代码不会重装依赖。= Java 的分层 jar。

构建运行:
```bash
docker build -t myapi .
docker run -p 8000:8000 -e DATABASE_URL=... -e SECRET_KEY=... myapi
```

> 🟡 **Java 对比**:多阶段 ≈ Spring Boot layered jar / jib。`COPY 依赖文件在前` ≈ Maven 分层缓存。非 root 跑 ≈ 不用 root 跑 jar。

---

## §22.5 健康检查端点(对应:`health`)🟢

```python
@app.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict:
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment, ...}
```

生产部署(K8s/Docker)的 **liveness/readiness 探针**打这个端点,判断应用是否健康。Dockerfile 里也配了 `HEALTHCHECK` 打它。

> 🟡 **Java 对比**:= Spring Boot Actuator 的 `/actuator/health`。

> ✅ 做 `health` 题:`return {"status":"ok", "app":settings.app_name, ...}`。

---

## §22.6 FastAPI vs Flask vs Django 怎么选

|  | FastAPI | Flask | Django |
|---|---|---|---|
| **类型注解** | ✅ 原生(驱动一切) | ❌ | 部分(DRF) |
| **异步** | ✅ 原生 | ⚠️ 弱 | 部分 |
| **自动文档** | ✅ /docs 开箱即用 | 需 flask-restx | 需 drf-yasg |
| **ORM** | 无(配 SQLAlchemy) | 无 | ✅ 自带 Django ORM |
| **Admin 后台** | ❌ | ❌ | ✅ 自带 |
| **学习曲线** | 中(类型驱动) | 低 | 高(全家桶) |
| **定位** | 现代 API 服务 | 轻量灵活 | 全栈全家桶 |
| **= Java** | Spring Boot(现代) | 轻量 Servlet | Spring 全家桶 + Admin |

**选型**:
- **新项目做 API/微服务** → **FastAPI**(现代、类型安全、异步、文档零配置)。本课程主线。
- **老项目维护/极简脚本** → Flask。
- **全栈(含 admin/ORM/auth 全要)+ 大团队** → Django(= Spring 全家桶)。

> 掌握 FastAPI 后,迁移到 Flask/Django 成本很低(路由/请求处理概念通用)。

---

## §22.7 Java 老手常踩的坑 ⚠️

1. **生产忘加 gunicorn**:单进程 uvicorn 撑不住,崩了全挂。生产 gunicorn 多 worker(或 K8s 多 Pod)。
2. **GIL**:单进程多线程**不能**用多核 CPU。要用多核得**多进程**(gunicorn -w)或多容器。Java 多线程就行,这是大区别。
3. **`--reload` 进生产**:reload 有性能开销和稳定性问题,只开发用。
4. **配置硬编码**:SECRET_KEY/DATABASE_URL 绝不进代码。用 pydantic-settings + 环境变量。
5. **Dockerfile 拷源码在前**:会导致改代码就重装依赖(缓存失效)。依赖文件(pyproject/lock)拷在前。
6. **root 跑容器**:安全风险。用非 root 用户。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `get_settings` | pydantic-settings + lru_cache | 🟢 |
| `health` | 健康检查端点 | 🟢 |

```bash
uv run pytest 03_web_framework/ch22/test_ch22_assignment.py -v
```
（另:读 `Dockerfile` + `.env.example`,对照 §22.4 理解多阶段构建）

---

## ✅ 自测

- [ ] 能说清 uvicorn(开发)vs gunicorn(生产)的区别
- [ ] 知道 GIL 导致 Python 必须多进程用多核(和 Java 多线程的区别)
- [ ] 会用 pydantic-settings 从环境变量读配置 + 类型校验
- [ ] 能读懂多阶段 Dockerfile,知道为什么依赖文件拷在前
- [ ] 能说清 FastAPI/Flask/Django 怎么选
- [ ] 2 个作业全绿

## 🎓 费曼挑战

1. 「为什么 Python 生产要用 gunicorn 多 worker,而 Java 多线程就够了?」— 重读 §22.2(GIL)
2. 「Dockerfile 为什么把 `COPY pyproject.toml uv.lock` 放在 `COPY 源码` 前面?」— 重读 §22.4(层缓存)

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ M3 毕业 → 考试系统 Lab

恭喜!**Ch13–22 全部学完,M3 FastAPI 模块毕业** 🎓。你现在能:调 API(httpx)→ 写 API(FastAPI+Pydantic)→ 参数路由 → 依赖注入 → 中间件/异常 → 异步 → 数据库(SQLAlchemy)→ 测试 → JWT 认证 → 部署。

下一站是**考试系统 Lab**(`03_web_framework/lab/`)——综合用 Ch16 依赖注入 + Ch19 SQLAlchemy + Ch21 JWT,搭一个完整的考试系统。需求等你来定,我们讨论后开干。
