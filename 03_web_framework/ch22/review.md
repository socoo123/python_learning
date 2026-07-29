# Ch22 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | uvicorn 和 gunicorn 各用于什么场景? | uvicorn=ASGI 服务器,开发用(单进程+--reload);gunicorn=进程管理器,生产用(-w N -k uvicorn.workers.UvicornWorker 多进程)。= Tomcat 开发/生产 | ⬜ |
| 2 | 为什么 Python 生产要多进程(gunicorn -w),Java 多线程就够? | **GIL**(全局解释器锁):单进程内多线程不能真并行 CPU。要用多核必须多进程(或多容器)。Java 无 GIL,多线程即用多核 | ⬜ |
| 3 | pydantic-settings 的 BaseSettings 对应 Java 什么?有何特性? | = @ConfigurationProperties + application.yml。从环境变量/.env 自动加载、类型校验、缺必填项启动 fail-fast、大小写不敏感可配 | ⬜ |
| 4 | get_settings 为什么用 @lru_cache? | 让一个进程只构造一次 Settings(读一次环境/文件),不每请求重读。测试要重读环境调 cache_clear()。配合 Depends 注入(Ch16) | ⬜ |
| 5 | 多阶段 Dockerfile 为什么把 `COPY pyproject.toml uv.lock` 放在源码前? | Docker 层缓存:依赖不常变放前,源码常变放后。改业务代码不会触发重装依赖。= Maven 分层。多阶段还让 runtime 镜像不带构建工具(更小) | ⬜ |
| 6 | FastAPI/Flask/Django 怎么选?新项目 API? | FastAPI(现代/类型/异步/文档零配置,新 API 首选);Flask(轻量/老项目);Django(全栈全家桶含 admin/ORM/auth)。掌握 FastAPI 迁移其他成本低 | ⬜ |
| 7 | ASGI 是什么?FastAPI 和 uvicorn 的关系? | ASGI=异步服务器网关接口。FastAPI 是 ASGI【应用】,uvicorn 是跑它的【ASGI 服务器】。≈ Spring MVC 控制器 vs Tomcat | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「GIL → Python 多进程 vs Java 多线程」?
- [ ] 能说清「Dockerfile 层缓存:依赖文件拷在前」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
