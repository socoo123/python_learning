# Ch07 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | Python 类型注解运行时强制吗?`add("1","2")`(注解 int)会怎样? | **不强制**,运行时完全忽略——`add("1","2")` 静默返回 `"12"`。注解只是文档,真正的检查靠 **mypy** 静态分析(模拟 Java 编译期) | ⬜ |
| 2 | 函数可能返回「对象或空」,怎么标注?调用方怎么处理? | 联合类型 `-> dict \| None`(3.10+ 推荐;老写法 `Optional[dict]`)。调用方 `if p is not None:`。❌ 别返回 `{}`/`-1` 当「没找到」 | ⬜ |
| 3 | 标注「接收 float 返回 float 的函数参数」?等价于 Java 什么? | `Callable[[float], float]`(从 typing 导入)。= Java `Function<Double,Double>`,但一个 Callable 通吃所有函数式接口。注意参数列表要包一层 `[]` | ⬜ |
| 4 | Protocol 是什么?为什么 Cat 不写 `implements Named` 就能当 Named 用? | **结构化类型**:有要求的属性/方法就算实现,不用声明(= Go 隐式接口、Java interface 的鸭子类型版)。对第三方类零侵入;`class Cat(Named)` 反而画蛇添足 | ⬜ |
| 5 | `@runtime_checkable` 有什么用?忘了加会怎样? | 让 Protocol 能用 `isinstance` 做【运行时】结构检查(只查属性/方法是否存在,不查类型)。不加就 isinstance → `TypeError` | ⬜ |
| 6 | `T = TypeVar("T")` 解决什么?为什么不用 `object` 当返回类型? | T 保持**类型关联**:进 `list[str]` 出 `str | None`。用 object 则返回类型信息全丢,调用方要强转(= Java 泛型前的黑暗年代) | ⬜ |
| 7 | Python 写泛型类(如 `Page<T>`)怎么写?忘了关键一步会怎样? | `class Page(Generic[T]): ...`,T 是 TypeVar。忘写 `(Generic[T])` → `Page[int]` 参数化时 `TypeError: type is not subscriptable` | ⬜ |
| 8 | TypedDict 解决什么?运行时校验数据吗? | 给 dict 定义**精确的键和类型**(`dict[str, Any]` 不知道有哪些键),mypy 连键名拼错都能抓。**运行时不校验**,就是普通 dict;要运行时校验上 Pydantic(Ch14) | ⬜ |
| 9 | EAFP vs LBYL?Python 偏哪个,为什么? | LBYL=先 if 检查再操作(Java 习惯);EAFP=直接做、try/except 兜底。**Python 偏 EAFP**:异常便宜、检查+操作一步原子(防竞态)、乐观路径干净。高频失败场景才回 LBYL | ⬜ |
| 10 | 商品 dict 的值有 str/int/float,注解怎么写?为什么不能写裸 `dict`? | `dict[str, Any]`。Any = 任意类型(mypy 对该位置免责);strict 模式下裸泛型(不带参数的 `dict`/`list`)会被要求补全参数 | ⬜ |
| 11 | `import this` 是什么?说一条你最有共鸣的 | 打印 19 条 Python 设计哲学(The Zen)。如:明确胜于晦涩、扁平胜于嵌套、可读性很重要、应该只有一种显而易见的方式 | ⬜ |

## 🎓 费曼自检(复习时口头说一遍)

- [ ] 能说清「Protocol 不用 implements 就能匹配,原理是什么?和 Java/Go interface 的关系」?
- [ ] 能说清「TypeVar 保持类型关联是什么意思?`list[T] -> T | None` 比 `object` 强在哪」?
- [ ] 能说清「EAFP vs LBYL,为何 Python 偏 EAFP」?
- [ ] 能说清「注解运行时不强制,那它和 Java 类型约束差在哪、靠什么补」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 复习日期到了,把这一行登记到根 [`REVIEW.md`](../../REVIEW.md) 的「复习日程」表。
