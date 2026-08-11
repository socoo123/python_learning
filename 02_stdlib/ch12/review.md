# Ch12 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | logging 四要素?各对应 logback 什么? | Logger(记录器)+ Handler(输出目标=Appender)+ Formatter(格式=PatternLayout)+ Level(级别)。标准库内置,不用三方包 | ⬜ |
| 2 | 级别数值顺序?`setLevel(INFO)` 的过滤语义? | DEBUG(10)<INFO(20)<WARNING(30)<ERROR(40)<CRITICAL(50);只输出【不低于】级别的日志 | ⬜ |
| 3 | `getLogger(name)` 两个关键特性?为什么不用 root? | 【单例】(同名同一实例,配置一次处处生效)+【层级】(`order.db` 继承 `order`)。root 无模块名、库/应用日志混一团,业务代码用具名 | ⬜ |
| 4 | handler 重复添加会怎样?怎么防? | `addHandler` 是【追加】——初始化跑两次日志打两遍。加前查重:`any(isinstance(h, StreamHandler) for h in logger.handlers)`,幂等 | ⬜ |
| 5 | 配置里的字符串 `"debug"` 怎么变成 logging 常量?非法值怎么办? | `logging.getLevelNamesMapping()`(3.11+)查表,先 `strip().upper()` 归一;未命中【raise ValueError】——宁抛勿吞,别用私有 `_nameToLevel` | ⬜ |
| 6 | 什么时候用 `logger.log(level, msg)` 而不是 `logger.info(msg)`? | 级别是【变量】时(来自配置/事件字段)——便捷方法把级别写死在方法名里,`log` 接受级别参数 | ⬜ |
| 7 | 结构化日志长什么样?为什么比拼人话强? | `event=order_created order_id=123 amount=99.9`(key=value,空格分隔)。ELK/Loki 自动切字段,可检索可聚合;「订单 123 创建成功」只能正则抠 | ⬜ |
| 8 | `os.environ.get(key, default)` 为什么不能写成 `get(key) or default`? | 显式设空串 `KEY=""` 是有意的配置,`or` 会把它吞成 default;`.get` 的默认值只在【键不存在】时生效 | ⬜ |
| 9 | .env 解析 5 条规则? | ①跳空行/`#`注释 ②去 `export ` 前缀 ③`split("=", 1)` 只切第一刀 ④键值 strip ⑤去成对引号。值永远是【字符串】 | ⬜ |
| 10 | .env 和环境变量同时存在谁赢?怎么合并才对? | 环境变量赢(12-Factor/Spring 同理)。只遍历【文件里已有的键】查覆盖——不把整个 os.environ 倒进来:「形状由文件定义,值由环境覆盖」 | ⬜ |
| 11 | dictConfig 四件套?对应 logback.xml 什么? | `version`(固定 1)/ `formatters`(≈encoder pattern)/ `handlers`(≈appender,按名字引用 formatter)/ `root`(挂 handler 列表)。加载时校验,配错启动即炸 | ⬜ |
| 12 | `pyproject.toml` 和 `uv.lock` 各对应 Maven 什么?哪个进 git? | pyproject = pom.xml(依赖+工具配置);uv.lock = 锁定精确版本。【两个都进 git】;`.env` 反而必须 gitignore | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「logging 四要素 vs logback,handler 为什么要幂等防重」?
- [ ] 能说清「配置为何外置,环境变量和 .env 谁优先、怎么合并」?
- [ ] 能说清「dictConfig 四件套 + pyproject/uv.lock 对应 Maven 什么」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
