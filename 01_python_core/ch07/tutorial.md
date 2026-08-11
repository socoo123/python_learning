# Ch07 · 类型注解与 Pythonic 风格

> **预计**:0.5 天 ｜ **前置**:Ch05 ｜ **M1 收官**
> **目标**:给 Python 加上「准静态类型」,让你从 Java 过来更舒服;并学会最地道的 Python 写法——**Protocol 结构化类型**、**泛型(TypeVar/Generic)**、**EAFP 风格**、The Zen of Python。
> 本章主线:你是电商平台结算组的工程师,要交付一个**「促销对账工具集」**——价格格式化、按 sku 查商品(`products.json`)、折扣策略注入、泛型取首条/分页包装、订单行金额计算(TypedDict)、营销配置容错解析(EAFP),最后串成一张对账单。

> 📐 **本教程的契约**:下面每一节(§7.1–§7.9)都**精确对应**作业里的一个任务。本章你要【补全类型注解】+ 写实现。讲过的才考,考的必讲过。卡住时,按对应表回查小节。

---

## 🗺️ 本章地图(元学习 · 原则一)

读完这章 + 完成作业,你将能够:
- 给函数加完整**类型注解**(参数 + 返回值 + 容器),说清它「运行时不强制」靠什么兜底
- 用联合类型 `X | Y`、`X | None` 表达「可能是 A 或 B / 可能为空」
- 用 `Callable[[...], ...]` 标注「函数参数」的类型(= Java 一堆函数式接口)
- 用 **`Protocol`** 定义结构化类型(= Java interface 的鸭子类型版,不用 implements)
- 用 **`TypeVar`/`Generic`** 写泛型函数和泛型类(= Java 的 `<T>`)
- 用 **`TypedDict`** 给字典定义精确的键结构(= Java record 的 dict 版)
- 说清 **EAFP**(try 优先)vs LBYL(if 优先),知道 Python 为什么偏 EAFP
- 用 **mypy** 做静态类型检查(模拟 Java 编译期)

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业题 | 对应小节 | 核心知识点 |
|--------|----------|-----------|
| `format_price` | §7.1 | 类型注解基础(参数 + 默认值 + 返回值) |
| `find_product` | §7.2 | 联合类型 `dict \| None` |
| `apply_discount` | §7.3 | `Callable[[float], float]` 策略注入 |
| `make_named_protocol` | §7.4 | Protocol + @runtime_checkable |
| `first_or_none` | §7.5 | TypeVar 泛型函数 |
| `make_page_class` | §7.6 | Generic[T] 泛型类 |
| `order_amount` | §7.7 | TypedDict 字典精确结构 |
| `extract_discount_rate` | §7.8 | EAFP 风格(try 优先) |
| `build_reconciliation_rows` | §7.9 | 综合:复用前面函数串流水线 |

---

## ⏱️ 学习路径:费曼五步(约 45-60 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 下面 5 个 Java 场景,猜 Python 怎么写 | 本页 ① |
| ② 先动手 | 打开 `ch07_assignment.py`,**先试着写**(别看教程) | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 讲清「Protocol 为何不用 implements」「TypeVar 解决什么」「EAFP vs LBYL」 | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性原则**:别通读!先猜 ① → 去 ② 写作业 → **哪题卡了,回对应 § 查** → 改 → 再跑。

---

## ① 预览猜(2 分钟 · 激活你的 Java 直觉)

先别看答案,凭 Java 经验猜一猜(猜错记得更牢):
1. Java 接口必须 `implements XxxInterface`。Python 有没有办法让一个类「长得像接口就自动算」(不改第三方类的源码)?
2. Java 函数类型用 `Function<Double,Double>`。Python 怎么标注「一个接收 float 返回 float 的函数」?
3. Java 泛型方法 `<T> T firstOrNull(List<T> list)`。Python 没有 `<T>` 语法,怎么表达「类型参数」?
4. Java 写 `if (map.containsKey(k)) ... else ...`(LBYL 三思后行)。Python 更推崇哪种风格?
5. Java 类型是编译期硬约束。Python 的类型注解运行时强制吗?那它有什么用?

> 猜完,带着验证心态进入正文。第 1 题(Protocol)和第 3 题(TypeVar)是本章的灵魂。

---

## §7.1 类型注解基础(对应:`format_price`)🟢

语法你基本秒懂,直接上对照:

```java
// Java
String formatPrice(double amount, String currency) {
    return String.format("%s%.2f", currency, amount);
}
```

```python
# Python:参数注解 + 默认值 + 返回值注解(-> 后)
def format_price(amount: float, currency: str = "¥") -> str:
    return f"{currency}{amount:.2f}"
```

**真实场景例**(本章主线:对账单的金额列必须统一格式,财务系统直接读这列):

```python
def export_row(order_id: str, amount: float) -> str:
    return f"{order_id},{format_price(amount)}"

export_row("A001", 119.0)     # "A001,¥119.00"
```

### 三种注解位置 + 容器注解

```python
def f(a: int, b: str = "x") -> bool: ...   # 参数注解、默认值、返回注解

name: str = "Alice"          # 变量注解(少用,一般靠推断)
items: list[int] = []        # 容器注解:3.9+ 用小写内置,不用 typing.List
d: dict[str, float]          # = Java Map<String, Double>
t: tuple[int, str]           # 固定长度异构元组
```

> 🟡 **唯一的思维差异**:Java 类型是**编译期硬约束**(类型错编不过)。Python 注解只是**文档**,运行时完全忽略——注解还活在 `__annotations__` 里供工具和测试查看,但解释器不管:

```python
def add(a: int, b: int) -> int:
    return a + b

add("1", "2")                # 运行正常,返回 "12"!注解根本没生效
add.__annotations__          # {'a': <class 'int'>, 'b': <class 'int'>, 'return': <class 'int'>}
```

❌ **错误认知**:「标了 `int` 传字符串就会报错」——不会,甚至静默通过(如上 `"1"+"2"`)。
✅ **正确认知**:约束靠 **mypy 静态检查**(§7.10),配 IDE 插件实时标红 = 模拟 Java 编译期。

> ✅ 做 `format_price` 题:给签名补 `amount: float, currency: str = "¥", -> str`,实现 `f"{currency}{amount:.2f}"`。

---

## §7.2 联合类型与 None(对应:`find_product`)🟡

函数可能返回「对象 or 空」。Java 用 `Optional<Product>`,Python 用**联合类型**:

```java
// Java
Optional<Product> findBySku(List<Product> products, String sku) { ... }
```

```python
# Python:dict 或 None,直接用 | 写出来
from typing import Any

def find_product(products: list[dict[str, Any]], sku: str) -> dict[str, Any] | None:
    for p in products:
        if p["sku"] == sku:
            return p
    return None
```

> 🟡 **`Any` 是什么**:商品 dict 的值类型杂(`str`/`int`/`float` 混在一起),没法用一个类型写死,`dict[str, Any]` 声明「键是 str,值是任意类型」。`Any` ≈ Java 的 `Object`,但更「免责」——mypy 对 Any 位置不做检查。注意别写裸 `dict`:本仓库 mypy 开了 `strict` 模式,裸泛型(不带参数的 `dict`/`list`)会被要求补全参数。

**真实场景例**(客服后台按 sku 查商品,查不到要明确表示「没有」,用 `assets/mock_data/products.json`):

```python
products = load_mock_json("products.json")   # 10 个商品
p = find_product(products, "KB-001")
if p is not None:                            # 调用方必须处理 None 分支
    print(p["name"], p["price"])             # 机械键盘 599.0
```

### 三种等价写法(3.10+ 推荐 `|`)

```python
def f(x: int | None): ...             # ✅ 推荐,最简洁(PEP 604)
def f(x: Optional[int]): ...          # 老写法,= int | None,需 from typing import Optional
def f(x: Union[int, str, None]): ...  # 多类型联合的老写法,= int | str | None
```

> 🟡 **Java 对比**:Java 没有联合类型(`int | str`),只能用公共接口/继承绕。Python 的 `|` 直接说「这值可能是 A 或 B」。`X | None` ≈ Java `Optional<X>`,但 Python 的 None 是真 null(单例),不用 `.get()`/`.orElse()` 解包——直接用,但要自己处理 None。
>
> 附带收益:`isinstance(x, int | str)` 也支持 `|`(3.10+)。

❌ **错误写法**(返回「空对象」当没找到,Java 空对象模式惯性):

```python
def find_product(products, sku) -> dict:
    ...
    return {}      # 调用方分不清「没找到」和「真的是个空商品」!
```

✅ **正确写法**:`-> dict | None` + `return None`,调用方 `if p is not None:`(判空用 `is None`,不是 `== None`,Ch01 讲过)。

> ✅ 做 `find_product` 题:补 `products: list[dict[str, Any]], sku: str, -> dict[str, Any] | None`,实现遍历按 sku 查找,找不到 `return None`。

---

## §7.3 Callable:给「函数参数」标类型(对应:`apply_discount`)🟡

函数当参数时(策略模式!),用 `Callable` 标注它的签名:

```java
// Java:策略注入要挑对函数式接口
BigDecimal applyDiscount(BigDecimal amount, Function<BigDecimal, BigDecimal> strategy) { ... }
```

```python
# Python:一个 Callable 通吃,不用记 Function/BiFunction/Predicate/UnaryOperator...
from typing import Callable

def apply_discount(amount: float, strategy: Callable[[float], float]) -> float:
    #                                        ↑ 接收 float、返回 float 的函数
    return round(strategy(amount), 2)        # 金额统一两位小数
```

**真实场景例**(大促定价:折扣策略运营随时换,代码不改——策略模式):

```python
apply_discount(599.0, lambda p: p * 0.8)    # 八折 → 479.2
apply_discount(599.0, lambda p: p - 50)     # 立减50 → 549.0

def member_price(p: float) -> float:        # 具名函数也行
    return p * 0.7
apply_discount(599.0, member_price)         # 会员价 → 419.3
```

### Callable 语法变体

```python
Callable[[int, str], bool]     # 接收 (int, str) 返回 bool
Callable[[], None]             # 无参无返回(≈ Java Runnable)
Callable[..., int]             # 任意参数,返回 int(参数签名懒得写时)
```

凡是可以「被调用」的东西都满足 Callable:lambda、def 函数、实现了 `__call__` 的实例、`functools.partial` 产物。

❌ **经典笔误**(参数列表忘了包一层 `[]`):

```python
def apply_discount(amount: float, strategy: Callable[float, float]) -> float: ...
#                                                   ↑ mypy 报错:Callable 第一个参数必须是参数列表
```

✅ **正确写法**:`Callable[[float], float]`——外层 `[]` 是 Callable 的泛型参数,内层 `[float]` 是「参数列表」。

> ✅ 做 `apply_discount` 题:补 `amount: float, strategy: Callable[[float], float], -> float`,实现 `round(strategy(amount), 2)`。

---

## §7.4 Protocol:不用 implements 的接口(对应:`make_named_protocol`)🔴

本章最 Pythonic、Java 没有的概念。**Protocol = 结构化类型**:一个类只要「长得对」(有要求的属性/方法),就算实现了这个 Protocol——**不需要 `implements` 声明,甚至不需要知道 Protocol 的存在**。

### 最小对照例

```java
// Java:名义类型(nominal)——必须显式 implements,编译器才认
interface Named { String getName(); }
class Cat implements Named { ... }     // 不写 implements 就不是 Named
```

```python
# Python:结构化类型(structural)——有结构就匹配
from typing import Protocol, runtime_checkable

@runtime_checkable
class Named(Protocol):
    name: str                    # 只声明结构,不写值(= 接口里的签名)

def get_name(obj: Named) -> str:
    return obj.name

class Cat:                       # 注意:没有 (Named),没 implements!
    name = "Tom"

get_name(Cat())                  # "Tom" —— Cat 自动算 Named
isinstance(Cat(), Named)         # True  —— @runtime_checkable 让运行时也能检查
```

### 真实场景例:平台通讯录

平台里「店铺 / 商品 / 客服」三类是**不同团队写的,你不能改它们的源码去 implements**。只要它们恰好有 `.name`,就能进通讯录:

```python
class Shop:          # 交易团队的类,单继承自他们自己的基类,你改不了
    name = "官方旗舰店"

class Agent:         # 客服团队的类
    def __init__(self, name: str):
        self.name = name

contacts = [Shop(), Agent("小芳"), Cat()]
for c in contacts:
    if isinstance(c, Named):     # 运行时也能筛:有 name 的才算
        print(get_name(c))       # 官方旗舰店 / 小芳 / Tom
```

> 🤯 **Java 老手震惊点**:这就是 **Go 语言的隐式接口**思想!「不要问是谁,只问能做什么」——鸭子类型的升级版,而且带静态检查:mypy 能验证「传给 `get_name` 的对象确实有 `name: str`」。

### Protocol 也能声明方法

```python
class SupportsRender(Protocol):
    def render(self) -> str: ...     # 方法成员:只写签名,body 是 ...

class Invoice:
    def render(self) -> str:         # 没继承 SupportsRender,照样匹配
        return "发票#123"
```

### `@runtime_checkable` 的作用

默认 Protocol 只能被 mypy **静态**检查;加 `@runtime_checkable` 后才能 `isinstance` **运行时**检查(注意:只查属性/方法**是否存在**,不查类型是否匹配)。

❌ **错误写法 1**(Java 惯性,显式继承):

```python
class Shop(Named):      # 语法上能跑,但失去意义:第三方类你根本加不上这个括号
    name = "官方旗舰店"
```

✅ **正确写法**:不声明、不继承,有结构就自动匹配——对第三方代码零侵入。

❌ **错误写法 2**(忘加装饰器就 isinstance):

```python
class Named(Protocol):
    name: str

isinstance(Cat(), Named)
# TypeError: Instance and class checks can only be used with @runtime_checkable protocols
```

✅ **正确写法**:Protocol 上加 `@runtime_checkable`。

> ✅ 做 `make_named_protocol` 题:在函数体内定义上面这个 `@runtime_checkable class Named(Protocol)`(含 `name: str`),然后 `return Named`(**返回类本身**,不是实例)。为什么用「类工厂」写法?——类也是对象(Ch01),函数可以造类、返回类,`collections.namedtuple` 就是官方类工厂;这样每题一个独立函数,测试和网页练习都能单独跑。

---

## §7.5 TypeVar:泛型函数(对应:`first_or_none`)🟡

先看不带泛型的问题:写一个「取列表首元素,空列表返回 None」的工具,元素类型由调用方定。

```java
// Java:不用泛型就得返回 Object,调用方强制转换(泛型前的黑暗年代)
Object firstOrNull(List list) { ... }
String s = (String) firstOrNull(names);   // 强转,可能 ClassCastException

// Java 泛型:<T> 让「进什么类型,出什么类型」
<T> T firstOrNull(List<T> list) { ... }
```

Python 没有 `<T>` 语法,用 **`TypeVar`** 声明一个类型变量:

```python
from typing import TypeVar

T = TypeVar("T")                          # 模块级定义一次,处处引用

def first_or_none(items: list[T]) -> T | None:
    return items[0] if items else None
```

**真实场景例**(库存预警队列 / 消息队列取首条,队列里放什么是调用方定的):

```python
first_or_none(["CP-009", "MN-003"])   # mypy 推出 str | None
first_or_none([599, 159])             # mypy 推出 int | None
first_or_none([])                     # None(空队列安全)
```

### TypeVar 到底解决了什么?

`T` 的价值是**类型关联**:「参数 list 里的元素类型」和「返回值类型」绑定。对比:

❌ **错误写法**(用 `object` 当万金油,类型信息全丢):

```python
def first_or_none(items: list[object]) -> object | None:
    return items[0] if items else None

x = first_or_none(["CP-009"])
# mypy 眼里 x 是 object | None,调 x.upper() 直接报错——还得自己 cast,退回 Java 泛型前
```

✅ **正确写法**:`list[T] -> T | None`,进 `list[str]` 就推出 `str | None`,调用方零强转。

> 🟡 **Java 对比**:`T = TypeVar("T")` ≈ 方法签名里的 `<T>`;区别是 Python 要把 T 先**命名定义**出来再引用。作业里 `T` 已在文件顶部给你定义好,直接用即可。

> ✅ 做 `first_or_none` 题:补 `items: list[T], -> T | None`,实现 `return items[0] if items else None`。

---

## §7.6 Generic:泛型类(对应:`make_page_class`)🔴

你写过的 Spring Data `Page<T>`:`List<T> content` + `long total` + 页码。Python 泛型类用 `Generic[T]` 基类:

```java
// Java
class Page<T> {
    List<T> items;
    long total;
    int page;
    int pageCount(int size) { return (int) Math.ceil(total * 1.0 / size); }
}
```

```python
# Python:@dataclass(Ch05)+ Generic[T] 组合,字段声明即构造器
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")

@dataclass
class Page(Generic[T]):
    items: list[T]
    total: int
    page: int = 1

    def page_count(self, page_size: int) -> int:
        return -(-self.total // page_size)    # ceil 整除技巧,免去 import math
```

**真实场景例**(商品列表接口的统一分页包装,前端只认这一种结构):

```python
products_page = Page(items=[{"sku": "KB-001"}], total=45, page=2)
products_page.page_count(10)          # 5(45 条每页 10 条 → 5 页)

skus_page: Page[str] = Page(items=["KB-001", "MS-002"], total=2)
#            ↑ 参数化:告诉 mypy 这页装的是 str,取 items[0].upper() 不报错
```

> 🔴 **Java 对比**:Java 泛型靠**编译期擦除**(运行时 `Page<Integer>` 和 `Page<String>` 是同一个 `Page`);Python 效果类似——`Page[int]` 与 `Page[str]` 运行时也是同一个类,类型约束全靠 mypy。区别是 Python 的 `Page[int]` 在运行时**可以写、不报错**(返回一个参数化别名),常用来给字段/变量做精确注解。

❌ **错误写法**(忘了继承 `Generic[T]`):

```python
@dataclass
class Page:                  # 没写 (Generic[T])
    items: list[T]           # 用了 T 但类没声明泛型
    total: int

Page[int](items=[1], total=1)
# TypeError: type 'Page' is not subscriptable —— 普通类不能用 [T] 参数化
```

✅ **正确写法**:`class Page(Generic[T]):`,类才能 `Page[int]` 参数化。

> ✅ 做 `make_page_class` 题:在函数体内定义 `@dataclass class Page(Generic[T])`(字段 `items: list[T]`、`total: int`、`page: int = 1`,方法 `page_count`),`return Page`。测试会构造 `Page[str](items=..., total=...)` 验证泛型可用。

---

## §7.7 TypedDict:字典的精确结构(对应:`order_amount`)🟡

JSON 解析出来是 dict。`dict[str, object]` 这个注解等于没说——不知道有哪些键、值是什么类型。`TypedDict` 给字典定义**精确的键结构**:

```java
// Java:Jackson 把 JSON 绑到 POJO/record
record OrderLine(String id, String sku, int qty, double unitPrice) {}
```

```python
# Python:TypedDict —— 底层还是普通 dict,注解精确到每个键
from typing import TypedDict

class OrderDict(TypedDict):
    id: str
    sku: str
    qty: int
    unit_price: float

def order_amount(order: OrderDict) -> float:
    return round(order["qty"] * order["unit_price"], 2)
```

**真实场景例**(对账时算订单行金额;订单来自 `json.loads`,本身就是 dict,**零转换成本**——不像 Java 要先绑定 POJO):

```python
raw = '{"id": "A001", "sku": "KB-001", "qty": 2, "unit_price": 59.5}'
order: OrderDict = json.loads(raw)     # dict 直接当 OrderDict 用,不用 new
order_amount(order)                    # 119.0
```

mypy 对 TypedDict 的保护非常实用:**键名拼错都能抓**——`order["qyt"]` 直接报「TypedDict has no key "qyt"」,`order["qty"] + "abc"` 报类型错。

> 🟡 可选键:默认所有键必填;`class XD(TypedDict, total=False)` 全部可选,或用 `NotRequired[str]` 标记单个可选键(了解即可)。

❌ **错误认知**:「TypedDict 会在运行时校验数据」——**不会**!

```python
order_amount({"id": "A1", "sku": "X", "qty": "2", "unit_price": 59.5})  # qty 是 str
# 运行时不拦,mypy 才拦;运行时到 "2" * 59.5 那步才 TypeError
```

✅ **正确认知**:TypedDict 是给 mypy 看的**纯注解**,运行时就是普通 dict。运行时要真校验 → 上 **Pydantic**(M3 Ch14 见,那才是 Java Bean Validation 的对应物)。

> ✅ 做 `order_amount` 题:`OrderDict` 已在文件顶部给你定义好。给参数补 `order: OrderDict, -> float`,实现 `round(order["qty"] * order["unit_price"], 2)`。

---

## §7.8 EAFP vs LBYL(对应:`extract_discount_rate`)🟡

两种防御风格,Python 强烈倾向 **EAFP**:

| 风格 | 全称 | 做法 | 倾向 |
|------|------|------|------|
| **LBYL** | Look Before You Leap(三思后行) | 先 `if` 检查再操作 | Java |
| **EAFP** | Easier to Ask Forgiveness than Permission(请求宽恕比许可容易) | 直接做,`try/except` 兜底 | **Python** ✅ |

**真实场景例**(营销系统推送的 promo 配置是嵌套 dict,字段经常缺、类型经常乱——下游要容错):

```python
# LBYL(Java 思维):层层判空,又臭又长
def extract_discount_rate(payload: dict[str, Any]) -> float:
    if "promo" in payload:
        promo = payload["promo"]
        if isinstance(promo, dict) and "rate" in promo:
            try:
                return float(promo["rate"])
            except ValueError:
                return 0.0
    return 0.0

# EAFP(Pythonic):乐观路径一把梭,出错兜底
def extract_discount_rate(payload: dict[str, Any]) -> float:
    try:
        return float(payload["promo"]["rate"])
    except (KeyError, TypeError, ValueError):
        return 0.0
```

两种写法行为完全等价,但 EAFP 版 3 行说清「我想做什么」,LBYL 版 10 行全是「我怕什么」。

```python
extract_discount_rate({"promo": {"rate": 0.15}})    # 0.15
extract_discount_rate({"promo": {"rate": "0.2"}})   # 0.2(float() 兼容数字字符串)
extract_discount_rate({})                           # 0.0(KeyError)
extract_discount_rate({"promo": None})              # 0.0(TypeError)
extract_discount_rate({"promo": {"rate": "abc"}})   # 0.0(ValueError)
```

### 为什么 Python 偏好 EAFP?

1. **异常在 Python 便宜**:不像 Java 抛异常要捕获完整栈快照,开销大,所以 Java 文化躲着异常走;Python 异常轻,「乐观路径」直接走 try 反而更快(命中时零检查开销)。
2. **避免竞态**:`if key in d: return d[key]` 检查和操作是两步,中间 dict 可能被别的线程改;EAFP 的 `d[key]` 一步原子。
3. **代码更简洁**:成功路径不被防御性 `if` 污染。

> 🟡 EAFP 不是万能:**循环里高频失败**的场景(异常真的频繁触发,如逐行解析脏数据且坏行占多数),LBYL 更好。日常取字典/查属性这种「偶尔失败」场景,一律 EAFP。

❌ **错误写法 1**(裸 `except`,Ch06 的教训):

```python
try:
    return float(payload["promo"]["rate"])
except:                  # 连 KeyboardInterrupt/SystemExit 都吞!
    return 0.0
```

✅ **正确写法**:`except (KeyError, TypeError, ValueError):`——只捕你预期的那几个。

❌ **错误写法 2**:以为 `dict.get` 链能优雅替代——`payload.get("promo", {}).get("rate", 0.0)` 在 `promo` 是 `None` 时照样 `AttributeError` 炸(`.get` 防不了 None)。嵌套结构容错,try 才是真解。

> ✅ 做 `extract_discount_rate` 题:用 `try/except (KeyError, TypeError, ValueError)` 实现,不要用 if 判空链。

---

## §7.9 综合:串起整条对账流水线(对应:`build_reconciliation_rows`)

最后一题,把前面的零件组装成**对账单生成器**:遍历订单 → 算行金额(`order_amount`)→ 应用折扣策略(`apply_discount`)→ 格式化(`format_price`)→ 一行一条:

```python
def build_reconciliation_rows(
    orders: list[OrderDict],
    strategy: Callable[[float], float],
) -> list[str]:
    rows = []
    for od in orders:
        base = order_amount(od)                    # §7.7:qty * unit_price
        final = apply_discount(base, strategy)     # §7.3:策略注入 + round
        rows.append(f"{od['id']}: {format_price(final)}")   # §7.1:格式化
    return rows
```

```python
orders = [
    {"id": "A001", "sku": "KB-001", "qty": 2, "unit_price": 59.5},
    {"id": "A002", "sku": "BK-005", "qty": 1, "unit_price": 75.5},
]
build_reconciliation_rows(orders, lambda a: a * 0.9)
# ["A001: ¥107.10", "A002: ¥67.95"]   —— 119.0×0.9=107.1,75.5×0.9≈67.95
```

这就是 Python 的日常:**一堆小函数,每个标注清楚类型,像乐高一样拼出流水线**——对应 Java 里 Stream + Function 的组合,但写法更直白。

> ✅ 做 `build_reconciliation_rows` 题:复用前面三个函数实现(注意:本地 uv 工作流里请**按顺序**完成前面的题,本题依赖它们)。

---

## §7.10 mypy:模拟 Java 编译期(了解)

注解写完,谁来检查?**mypy**——Python 事实标准的静态类型检查器:

```bash
uv run --with mypy mypy 01_python_core/ch07/ch07_assignment.py
```

- 它会静态分析注解,报告类型不匹配、键名拼错(TypedDict)、Protocol 不满足——让 Python 获得接近 Java 的编译期保护。
- 本仓库 `pyproject.toml` 里开了 `[tool.mypy] strict = true`:要求所有函数都有注解、裸泛型(裸 `dict`/`list`)要补全参数(所以作业里写 `dict[str, Any]`)。
- IDE 里(VS Code + Pylance / PyCharm)实时红线,底层就是同一套检查。
- 本章作业补全注解后跑 mypy 应该是**零报错**——这就是本章的「隐藏验收标准」。

---

## §7.11 The Zen of Python(Python 哲学)

REPL 里敲 `import this`,打印 19 条设计哲学。对 Java 老手最有启发的几条:

- **明确胜于晦涩**(Explicit is better than implicit)——Java 也信奉
- **简单胜于复杂,复杂胜于繁复**
- **扁平胜于嵌套**——别写 5 层 if/for
- **可读性很重要**(Readability counts)
- **如果实现难以解释,那它可能不是好主意**
- **请求宽恕比许可容易**(EAFP,§7.8)
- **应该有一种——最好只有一种——显而易见的方式**(对比 Perl 的「条条大路」)

> 🟡 写 Python 时多想想这几条,代码会越来越地道。

---

## §7.12 Java 老手常踩的坑 ⚠️

1. **注解运行时不强制**:别以为标了 `int` 就不能传字符串——`add("1","2")` 静默返回 `"12"`。要约束用 mypy(§7.1)。
2. **判空用 `is None`**:别写 `if x == None`(Ch01)。`==` 可以被 `__eq__` 重载骗过,`is` 不能。
3. **别滥用「空对象」**:找不到就返回 `None`,别返回 `{}`/`-1` 让调用方猜(§7.2)。
4. **Protocol 别写 implements**:`class Cat(Named)` 画蛇添足;对第三方类你也加不上(§7.4)。
5. **isinstance 查 Protocol 前加 `@runtime_checkable`**,且它只查结构存在性、不查类型(§7.4)。
6. **TypedDict 不做运行时校验**:运行时就是普通 dict,要真校验上 Pydantic(§7.7)。
7. **EAFP 不是 try-catch 滥用**:只在「乐观路径为主、偶尔失败」时用;高频失败场景回 LBYL;永远别裸 `except:`(§7.8)。

---

## 📝 本章作业

打开 **`ch07_assignment.py`**,9 个任务(补注解 + 写实现),主线是「促销对账工具集」:

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `format_price` | 类型注解基础 | 🟢 |
| `find_product` | `dict \| None` 联合类型 | 🟢 |
| `apply_discount` | `Callable` 策略注入 | 🟡 |
| `make_named_protocol` | Protocol + @runtime_checkable | 🔴 |
| `first_or_none` | TypeVar 泛型函数 | 🟡 |
| `make_page_class` | Generic[T] 泛型类 | 🔴 |
| `order_amount` | TypedDict | 🟡 |
| `extract_discount_rate` | EAFP 风格 | 🟡 |
| `build_reconciliation_rows` | 综合:流水线组装 | 🟡 |

```bash
uv run pytest 01_python_core/ch07/test_ch07_assignment.py -v
# 可选:静态类型检查(本章隐藏验收标准,应零报错)
uv run --with mypy mypy 01_python_core/ch07/ch07_assignment.py
```

全绿 = 掌握 Ch07 = **M1 语言核心毕业** 🎓。

---

## ✅ 自测:你真的掌握了吗?

- [ ] 能说清「Protocol 为什么不用 implements?它和 Java interface、Go interface 的关系」(§7.4)
- [ ] 能说清「TypeVar 解决什么?为什么不用 object 当返回类型」(§7.5)
- [ ] 能解释 EAFP vs LBYL,以及为什么 Python 偏好 EAFP(§7.8)
- [ ] 知道类型注解运行时不强制,真正检查靠 mypy(§7.1/§7.10)
- [ ] 会用 `X | None`、`Callable[[float], float]`、`list[T]` 标注类型
- [ ] 知道 TypedDict 运行时就是普通 dict、不校验(§7.7)
- [ ] 9 个作业全绿

---

## 🎓 费曼挑战(直觉 · Ultralearning 原则八)

> 用大白话讲给「Java 同事」听。讲不清 = 没懂,回查对应 §。

任选一题,讲清楚(1-2 分钟):
1. 「Protocol 是什么?为什么 Cat 不写 implements 就能当 Named 用?」— 卡壳重读 §7.4
2. 「`T = TypeVar("T")` 干了什么?和 Java 的 `<T>` 什么关系?」— 卡壳重读 §7.5/§7.6
3. 「EAFP 和 LBYL 是什么?为什么 Python 偏好 EAFP,而 Java 习惯 LBYL?」— 卡壳重读 §7.8
4. 「Python 类型注解运行时不强制,那它有什么用?靠什么真正检查?」— 卡壳重读 §7.1/§7.10

✅ 自检:不查资料,能说清「为什么」吗?

## 🧠 记忆闪卡(⑤ · 原则七)

→ 本章闪卡在 [`review.md`](./review.md)。学完标复习日期(1/3/7 天)。

---

## ⏭️ 下一步:M1 毕业,进入 M2

恭喜!Ch01–Ch07 完成后,你已建立完整的 **Python 思维**——不再是「用 Java 写 Python」。

下一站 **M2 标准库(Ch08–Ch12)**:collections(Counter/defaultdict/deque)、itertools/functools、正则、json/csv/datetime、现代工具链。这些都是 Python「自带电池(batteries included)」的精华,日常效率起飞。

> 建议:先回头把 Ch02–Ch07 的【费曼挑战】和【闪卡】过一遍(M1 知识成体系了),再进 M2。
