# Ch12 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | logging 四要素?各对应 Java logback 什么? | Logger(记录器)+ Handler(输出目标=Appender)+ Formatter(格式=Layout)+ Level(级别)。Python logging 标准库内置,不用三方包 | ⬜ |
| 2 | 日志级别从低到高?设了 INFO 还能看到什么? | DEBUG(10)<INFO(20)<WARNING(30)<ERROR(40)<CRITICAL(50)。设了 INFO 只看到【不低于】INFO 的,DEBUG 被过滤 | ⬜ |
| 3 | `logging.getLogger(name)` 的关键特性? | 【单例】:同名返回同一个 logger。所以跨模块用同名 getLogger 拿到同一个,配置一次到处用。还有父子层级(子 logger 继承父配置) | ⬜ |
| 4 | 为什么配置走环境变量/`.env` 而非写进代码? | API key/密码/端口等敏感+环境相关的东西,写进代码会泄露且无法区分 dev/prod。环境变量部署时注入,`.env` 开发本地(且【不进 git】) | ⬜ |
| 5 | `pyproject.toml` 和 `uv.lock` 各是什么?对应 Java 什么? | pyproject.toml = pom.xml(项目配置+依赖);uv.lock = 锁定精确版本,保证不同机器环境一致。`uv run`/`uv add`/`uv sync` 管理它们 | ⬜ |
| 6 | print 和 logging 怎么选? | 正式代码用 logging(可控制级别、写文件、分模块)。print 只用于临时调试,没法关级别/写文件 | ⬜ |
| 7 | `.env` 文件解析要注意什么? | 跳过空行和 `#` 注释;`split("=", 1)` 只切第一个等号(value 可含 =);值都是字符串(8ooo 是 "8000" 不是 int) | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「logging 四要素 vs logback,为何别用 print」?
- [ ] 能说清「配置为何走环境变量,`.env` 为何不进 git」?
- [ ] 能说清「pyproject.toml + uv.lock 的作用」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
