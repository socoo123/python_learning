# Ch07 · 类型注解与 Pythonic 风格

> **预计**:0.5 天 ｜ **前置**:Ch05 ｜ **M1 收官**
> **目标**:给 Python 加上「准静态类型」(mypy),让你从 Java 过来更舒服;并学会最地道的 Python 写法——**Protocol 结构化类型**、**EAFP 风格**、The Zen of Python。

> 📐 **本教程的契约**:下面每一节(§7.1–§7.5)都**精确对应**作业里的一个任务。本章你要【补全类型注解】+ 写实现。讲过的才考,考的必讲过。

---

## 🗺️ 本章地图(元学习 · 原则一)

读完这章 + 完成作业,你将能够:
- 给函数加完整**类型注解**(参数 + 返回值),理解它「运行时不强制」
- 用联合类型 `X | Y`、`Optional` 表达「可能为空」
- 用 `Callable` 标注「函数参数」的类型
- 用 **`Protocol`** 定义结构化类型(= Java interface 的鸭子类型版,不用 implements)
- 理解 **EAFP**(`try` 优先)vs LBYL(`if` 优先)的风格差异
- 用 **mypy** 做静态类型检查(模拟 Java 编译期)

**作业 ↔ 教程对应表**:

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `format_price` | §7.1 | 类型注解基础(参数+返回值) |
| `find_product` | §7.2 | 联合类型 `dict \| None` |
| `apply_operation` | §7.3 | `Callable[[int], int]` |
| `Named` / `get_name` | §7.4 | Protocol + @runtime_checkable |
| `safe_get` | §7.5 | EAFP 风格 |

---

## ⏱️ 学习路径:费曼五步(约 45-60 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 先猜 Python 怎么写 | 本页 ① |
| ② 先动手 | 打开 `ch07_assignment.py`,补注解 + 写实现 | assignment |
| ③ 提取+反馈 | 写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 讲清"Protocol 为何不用 implements""EAFP vs LBYL" | 本页 ④ |
| ⑤ 存闪卡 | 标 [`review.md`](./review.md) 复习日期 | review.md |

---

## ① 预览猜(2 分钟 · 激活你的 Java 直觉)

先别看答案,凭 Java 经验猜一猜:
1. Java 接口必须 `implements XxxInterface`。Python 有没有办法让一个类「长得像接口就自动算」(不用声明)?
2. Java 函数类型用 `Function<Integer,Integer>`。Python 怎么标注「一个接收 int 返回 int 的函数」?
3. Java 写 `if (map.containsKey(k)) v = map.get(k); else v = default;`(LBYL 三思后行)。Python 更推崇哪种风格?
4. Java 类型是编译期硬约束。Python 的类型注解运行时强制吗?
5. 一个函数可能返回对象或 null。Java 用 `Optional<X>`。Python 怎么写?

> 猜完,带着验证心态进入正文。

---

## §7.1 类型注解基础(对应:`format_price`)🟡

Ch01 §1.1 讲过:Python 类型注解**运行时不强制**,只是给人和工具看的提示。真正的检查靠 **mypy**(§7.6)。

```python
def format_price(price: float, currency: str = "¥") -> str:
    #             ↑ 参数注解                ↑ 返回值注解(-> 后)
    return f"{currency}{price:.2f}"
```

### 三种注解位置

```python
def f(a: int, b: str = "x") -> bool:     # 参数注解、默认值、返回注解
    ...

name: str = "Alice"                       # 变量注解(少用,一般靠推断)
items: list[int] = []                     # 容器类型注解
```

### 容器类型(3.9+ 用小写内置)

```python
xs: list[int]               # = Java List<Integer>
d: dict[str, float]         # = Java Map<String, Double>
t: tuple[int, str]          # = 固定长度,(int, str)
s: set[str]
```

> 🟡 **Java 对比**:Java 的类型是**编译期硬约束**(类型错编不过)。Python 注解是**文档**,运行时完全忽略——`add(1, "2")` 照样跑(到出错才报)。Python 的"约束"靠 mypy 在开发时静态检查,模拟 Java 编译期。

> ✅ 做 `format_price` 题:补 `price: float, currency: str = "¥", -> str`,实现 `f"{currency}{price:.2f}"`。

---

## §7.2 联合类型 / Optional(对应:`find_product`)🟡

函数可能返回「对象 or 空」。Java 用 `Optional<Product>`,Python 用**联合类型**:

```python
def find_product(products: list[dict], sku: str) -> dict | None:
    #                                                ↑ 联合类型:dict 或 None
    for p in products:
        if p["sku"] == sku:
            return p
    return None
```

### `X | Y` vs `Optional[X]` vs `Union`

```python
# 三种等价写法(3.10+ 推荐 |):
def f(x: int | None): ...              # ✅ 推荐,最简洁
def f(x: Optional[int]): ...           # 老写法,= int | None
def f(x: Union[int, str, None]): ...   # 多类型联合,= int | str | None
```

> 🟡 **Java 对比**:Java 没有「联合类型」(`int | str`),只能用接口/继承表达。Python 的 `|` 让你直接说「这值可能是 A 或 B」,更灵活。`Optional[X]` ≈ Java `Optional<X>`,但 Python 的 None 是真 null(单例对象),不是包装类。

> ✅ 做 `find_product` 题:补返回类型 `dict | None`,实现遍历查找。

---

## §7.3 Callable(对应:`apply_operation`)🟡

函数当参数时,怎么标注它的类型?用 `Callable`:

```python
from typing import Callable

def apply_operation(func: Callable[[int], int], x: int) -> int:
    #                     ↑ 接收 int,返回 int 的函数
    return func(x)

apply_operation(lambda n: n * 2, 5)   # 10
apply_operation(abs, -7)              # 7
```

### Callable 语法

```python
Callable[[参数类型...], 返回类型]
Callable[[int, str], bool]      # 接收 (int, str) 返回 bool
Callable[[], None]              # 无参无返回
Callable[..., int]              # 任意参数,返回 int
```

> 🟡 **Java 对比**:= `Function<Integer,Integer>` / `BiFunction` / 各种函数式接口。Python 一个 `Callable[[...],...]` 通吃,不用记一堆接口名。

> ✅ 做 `apply_operation` 题:给 func 标注 `Callable[[int], int]`,实现 `return func(x)`。

---

## §7.4 Protocol(对应:`Named`、`get_name`)🔴

这是本章最 Pythonic、Java 没有的概念。**Protocol = 结构化类型**:一个类只要「长得对」(有要求的属性/方法),就算实现了这个 Protocol——**不需要 `implements` 声明**。

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Named(Protocol):
    name: str                    # 只声明结构,不写值(= 接口里的方法签名)

def get_name(obj: Named) -> str:
    return obj.name

class Cat:                       # 注意:没有 (Named),没 implements!
    name = "Tom"

class Dog:
    name = "Rex"

get_name(Cat())                  # "Tom" —— Cat 自动算 Named
isinstance(Cat(), Named)         # True  —— @runtime_checkable 让运行时能检查
```

### 为什么这是革命性的?

Java 的接口是**名义类型**(nominal):必须显式 `implements`,编译器才认。
Python 的 Protocol 是**结构化类型**(structural):有结构就匹配,不用声明。

```java
// Java:Cat 必须显式 implements Named,才能当 Named 用
class Cat implements Named { ... }
```
```python
# Python:Cat 有 name 属性就自动是 Named,完全不用提 Named
class Cat:
    name = "Tom"
```

> 🤯 **Java 老手震惊点**:这就是 **Go 语言的隐式接口**思想!「不要问是谁,只问能做什么」——鸭子类型的升级版,带上了静态类型检查(mypy 能验证)。

### `@runtime_checkable`

默认 Protocol 只能被 mypy 静态检查。加 `@runtime_checkable` 后,还能用 `isinstance` **运行时**检查(只检查属性/方法是否存在,不检查类型)。

> ✅ 做 `Named`/`get_name` 题:给 Named 加 `@runtime_checkable` + `name: str`;给 get_name 的 obj 标注 `Named`,实现 `return obj.name`。

---

## §7.5 EAFP vs LBYL(对应:`safe_get`)🟡

两种风格,Python 强烈倾向 **EAFP**:

| 风格 | 全称 | 做法 | 倾向 |
|------|------|------|------|
| **LBYL** | Look Before You Leap(三思后行) | 先 `if` 检查再操作 | Java |
| **EAFP** | Easier to Ask Forgiveness than Permission(请求宽恕比许可容易) | 直接做,`try/except` 兜底 | **Python** ✅ |

```python
# LBYL(Java 思维,Python 里不推荐)
def safe_get_lbyl(d, key, default=None):
    if key in d:              # 先检查
        return d[key]
    return default

# EAFP(Pythonic,推荐)
def safe_get(d, key, default=None):
    try:
        return d[key]         # 直接做
    except KeyError:          # 出错再兜
        return default
```

### 为什么 Python 偏好 EAFP?

1. **异常在 Python 便宜**(不像 Java 抛异常有栈开销大),「乐观路径」直接走 try 更快。
2. **避免竞态**:`if key in d: return d[key]` 两步之间 dict 可能被改(LBYL 的检查和操作之间有时间窗);EAFP 一步原子。
3. **代码更简洁**:成功路径不被 `if` 污染。

> 🟡 但 EAFP 不是万能:循环里高频失败的场景(异常真的频繁),LBYL 更好。日常取字典/查属性,EAFP。

> ✅ 做 `safe_get` 题:用 `try/except KeyError` 实现(不是 `if key in d`)。

---

## §7.6 mypy + TypedDict(了解,本章简介)

### mypy:模拟 Java 编译期

```bash
uv run mypy 01_python_core/ch07/ch07_assignment.py
```
mypy 会静态分析你的注解,报告类型不匹配——让 Python 获得接近 Java 的编译期保护。生产项目强烈建议配 mypy(配 IDE 插件实时红线)。

### TypedDict:字典的强类型

普通 dict 注解 `dict[str, X]` 不知道有哪些键。`TypedDict` 给字典定义精确结构:

```python
from typing import TypedDict

class ProductDict(TypedDict):
    id: int
    name: str
    price: float

p: ProductDict = {"id": 1, "name": "键盘", "price": 599.0}   # 键/类型都固定
```
= Java 的 record / 强类型 POJO,但底层还是 dict。本章不出题,知道有这工具即可。

---

## §7.7 The Zen of Python(Python 哲学)

在 REPL 里敲 `import this`,会打印 19 条 Python 设计哲学。几条对 Java 老手最有启发的:

- **明确胜于晦涩**(Explicit is better than implicit)——Java 也信奉
- **简单胜于复杂,复杂胜于繁复**
- **扁平胜于嵌套**——别写 5 层 if/for
- **可读性很重要**(Readability counts)
- **如果实现难以解释,那它可能不是好主意**
- **请求宽恕比许可容易**(EAFP,§7.5)
- **应该有一种——最好只有一种——显而易见的方式**(对比 Perl "多种方式")

> 🟡 写 Python 时多想想这几条,代码会越来越地道。`import this` 是 Python 程序员的"座右铭"。

---

## §7.8 Java 老手常踩的坑 ⚠️

1. **注解运行时不强制**:别以为标了 `int` 就不能传字符串——要约束用 mypy。
2. **别用 `if x == None`**:判空用 `if x is None`(Ch01 讲过)。
3. **别滥用 Optional**:Python 里 `X | None` 很自然,不像 Java Optional 那样要 `.get()`/`.orElse()`——直接用,但要处理 None。
4. **Protocol 别写成 Java interface**:不需要 `implements`,别画蛇添足。
5. **EAFP 不是 try-catch 滥用**:只在「乐观路径为主、偶尔失败」时用;高频失败用 LBYL。

---

## 📝 本章作业

打开 **`ch07_assignment.py`**,5 个任务(补注解 + 写实现)。

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `format_price` | 类型注解基础 | 🟢 |
| `find_product` | `dict \| None` 联合类型 | 🟢 |
| `apply_operation` | `Callable` | 🟡 |
| `Named` / `get_name` | Protocol + @runtime_checkable | 🔴 |
| `safe_get` | EAFP 风格 | 🟡 |

```bash
uv run pytest 01_python_core/ch07/test_ch07_assignment.py -v
# 可选:静态类型检查
uv run mypy 01_python_core/ch07/ch07_assignment.py
```
全绿 = 掌握 Ch07 = **M1 语言核心毕业** 🎓。

---

## ✅ 自测:你真的掌握了吗?

- [ ] 能说清「Protocol 为什么不用 implements?它和 Java interface、Go interface 的关系」(§7.4)
- [ ] 能解释 EAFP vs LBYL,以及为什么 Python 偏好 EAFP(§7.5)
- [ ] 知道类型注解运行时不强制,真正检查靠 mypy(§7.1/§7.6)
- [ ] 会用 `X | None`、`Callable[[int],int]` 标注类型
- [ ] 5 个作业全绿

---

## 🎓 费曼挑战(直觉 · Ultralearning 原则八)

> 用大白话讲给「Java 同事」听。讲不清 = 没懂,回查对应 §。

任选一题,讲清楚(1-2 分钟):
1. 「Protocol 是什么?为什么 Cat 不写 implements 就能当 Named 用?」— 卡壳重读 §7.4
2. 「EAFP 和 LBYL 是什么?为什么 Python 偏好 EAFP,而 Java 习惯 LBYL?」— 卡壳重读 §7.5
3. 「Python 类型注解运行时不强制,那它有什么用?靠什么真正检查?」— 卡壳重读 §7.1/§7.6

✅ 自检:不查资料,能说清「为什么」吗?

## 🧠 记忆闪卡(⑤ · 原则七)

→ 本章闪卡在 [`review.md`](./review.md)。学完标复习日期(1/3/7 天)。

---

## ⏭️ 下一步:M1 毕业,进入 M2

恭喜!Ch01–Ch07 完成后,你已建立完整的 **Python 思维**——不再是「用 Java 写 Python」。

下一站 **M2 标准库(Ch08–Ch12)**:collections(Counter/defaultdict/deque)、itertools/functools、正则、json/csv/datetime、现代工具链。这些都是 Python「自带电池(batteries included)」的精华,日常效率起飞。

> 建议:先回头把 Ch02–Ch07 的【费曼挑战】和【闪卡】过一遍(M1 知识成体系了),再进 M2。
