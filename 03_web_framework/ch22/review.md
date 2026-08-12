# Ch22 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆，再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | ASGI 是什么？FastAPI 和 uvicorn 的关系？ | ASGI=异步服务器网关接口。FastAPI 是 ASGI【应用】,uvicorn 是跑它的【ASGI 服务器】。≈ Spring MVC 控制器 vs Tomcat | ⬜ |
| 2 | uvicorn 和 gunicorn 各用于什么场景？ | uvicorn=开发（单进程+--reload);gunicorn=生产（-w N -k uvicorn.workers.UvicornWorker 多进程)。K8s 里单进程 uvicorn+多 Pod | ⬜ |
| 3 | 为什么 Python 生产要多进程，Java 多线程就够？ | **GIL**：单进程内多线程不能真并行 CPU，用多核必须多进程/多容器。Java 无 GIL，多线程即用多核 | ⬜ |
| 4 | gunicorn worker 数怎么定？公式？ | `workers = 2 × CPU核数 + 1`(IO 等待时让 CPU 不闲着),下限 1。`worker_count_for_cores(4)` = 9 | ⬜ |
| 5 | 为什么命令用 list[str] 拼而不是 f-string 拼长串？ | 一个参数一个元素，避免空格截断/shell 注入；subprocess 直接吃 list。数字要 str() 转 | ⬜ |
| 6 | pydantic-settings 的 BaseSettings 对应 Java 什么？特性？ | = @ConfigurationProperties + application.yml。环境变量/.env 自动加载、类型校验转换("false"→False)、类型不符启动 fail-fast、大小写不敏感可配 | ⬜ |
| 7 | get_settings 为什么用 @lru_cache？测试怎么重读环境？ | 一个进程只构造一次 Settings，不每请求重读 .env。测试调 `get_settings.cache_clear()` 后重读。配合 Depends 注入（Ch16) | ⬜ |
| 8 | 启动日志想打印配置，secret_key 怎么处理？ | mask_secret 脱敏（露前 4 位+总长；太短全 "***";None/空 → "(unset)");model_dump() 转 dict 后覆盖敏感字段再进日志。直接 f"{settings}" 会泄露 | ⬜ |
| 9 | 多阶段 Dockerfile 为什么把 `COPY pyproject.toml uv.lock` 放在源码前？ | Docker 层缓存：依赖不常变放前，源码常变放后，改业务代码不重装依赖。多阶段还让 runtime 不带构建工具（更小）。= Maven 分层 | ⬜ |
| 10 | 容器里怎么给 Settings 注入配置？docker run 命令哪部分？ | `docker run -e KEY=VALUE`;K8s 里是 env:/Secret。代码里生成命令时 env 要 **排序** 保证确定性 | ⬜ |
| 11 | /health 端点干嘛的？对应 Spring 什么？ | K8s liveness/readiness 探针、Docker HEALTHCHECK 打它判断应用活着。= Actuator /actuator/health。返回 app/environment/version/debug | ⬜ |
| 12 | 上线前检查清单查哪 4 条？为什么返回 list 不抛异常？ | ①prod 开 DEBUG ②SECRET_KEY 是默认值 ③密钥<16 位 ④prod 用 SQLite。返回问题列表一次看全（= Maven 列全部编译错误）,空 list 才可上线 | ⬜ |
| 13 | FastAPI/Flask/Django 怎么选？新项目 API？ | FastAPI（现代/类型/异步/文档零配置，新 API 首选）;Flask（轻量/老项目）;Django（全栈全家桶含 admin/ORM/auth) | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「GIL → Python 多进程 vs Java 多线程」?
- [ ] 能说清「Dockerfile 层缓存：依赖文件拷在前」?
- [ ] 能讲清「为什么检查清单返回 list 而不是抛异常」?

## 📅 复习日程

- [ ] +1 天　日期：________
- [ ] +3 天　日期：________
- [ ] +7 天　日期：________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
