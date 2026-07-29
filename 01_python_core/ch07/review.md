# Ch07 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | Protocol 是什么?为什么 Cat 不写 `implements Named` 就能当 Named 用? | **结构化类型**:有要求的属性/方法就算实现,不用声明。= Go 的隐式接口、Java interface 的鸭子类型版。加 `@runtime_checkable` 后还能 `isinstance` 检查 | ⬜ |
| 2 | EAFP vs LBYL 各是什么?Python 偏好哪个,为什么? | LBYL=先 `if` 检查再操作(Java 习惯);EAFP=直接做、`try/except` 兜底。**Python 偏好 EAFP**:异常便宜、避免竞态、成功路径干净 | ⬜ |
| 3 | Python 类型注解运行时强制吗?靠什么真正检查? | **不强制**,运行时完全忽略,只是文档。真正的类型检查靠 **mypy** 静态分析(模拟 Java 编译期) | ⬜ |
| 4 | 写出:可能为 None 的 int、接收 int 返回 int 的函数类型 | `int \| None`(或 `Optional[int]`);`Callable[[int], int]`(从 typing 导入) | ⬜ |
| 5 | `@runtime_checkable` 加在 Protocol 上有什么用? | 让 Protocol 能用 `isinstance(obj, Protocol)` 做【运行时】结构检查(只查属性/方法是否存在,不查类型)。不加则只能 mypy 静态检查 | ⬜ |
| 6 | `import this` 是什么?说一条你最有共鸣的 | 打印 19 条 Python 哲学(The Zen)。如:明确胜于晦涩、扁平胜于嵌套、可读性很重要、应该只有一种显而易见的方式 | ⬜ |
| 7 | TypedDict 解决什么问题? | 给 dict 定义【精确的键和类型结构】(普通 `dict[str,X]` 不知道有哪些键)。= Java record 的 dict 版 | ⬜ |

## 🎓 费曼自检(复习时口头说一遍)

- [ ] 能说清「Protocol 不用 implements 就能匹配,原理是什么」?
- [ ] 能说清「EAFP vs LBYL,为何 Python 偏 EAFP」?
- [ ] 能说清「注解运行时不强制,那它和 Java 类型约束差在哪、靠什么补」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 复习日期到了,把这一行登记到根 [`REVIEW.md`](../../REVIEW.md) 的「复习日程」表。
