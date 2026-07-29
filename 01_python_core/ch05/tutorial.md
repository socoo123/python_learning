# Ch05 · OOP:魔术方法、继承、dataclass

> **预计**:1 天 ｜ **前置**:Ch04
> **目标**:理解 Python OOP 和 Java 的本质区别——**没有重载、有多继承、靠「魔术方法」让自定义类支持 `len()`/`in`/`+`/`for`**。你会手写一个 `ShoppingCart`,让它像内置类型一样好用。

> 📐 **本教程的契约**:下面每一节(§5.1–§5.3)都**精确对应**作业里的代码。讲过的才考,考的必讲过。卡住时,按方法名回查对应小节。

---

## 🗺️ 本章地图(元学习 · 原则一)

读完这章 + 完成作业,你将能够:
- 用 `@dataclass` 一行定义数据类(= Java Lombok `@Data` / record)
- 用**魔术方法**让自定义类支持 `len()`/`in`/`for`/`+`/`repr()`(Java 基本做不到)
- 用 `@property` 把方法变成「像属性一样访问」(= 受控 getter)
- 用**继承 + `super()`** 复用父类逻辑
- 说清 Python OOP 和 Java 的 5 个本质区别

**作业 ↔ 教程对应表**:

| 作业代码 | 对应小节 | 核心知识点 |
|----------|----------|-----------|
| `Product` | §5.1 | @dataclass |
| `ShoppingCart.__init__` / `add` | §5.2 | 类基础、self |
| `ShoppingCart.__len__` | §5.2 | 魔术方法 → `len()` |
| `ShoppingCart.__contains__` | §5.2 | 魔术方法 → `in` |
| `ShoppingCart.__iter__` | §5.2 | 魔术方法 → `for` |
| `ShoppingCart.total` (@property) | §5.2 | @property |
| `ShoppingCart.__add__` | §5.2 | 运算符重载 → `+` |
| `ShoppingCart.__repr__` | §5.2 | 调试显示 |
| `DiscountedCart` | §5.3 | 继承 + super() |

---

## ⏱️ 学习路径:费曼五步(约 60-90 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 看下面的差异,先猜 Python 怎么写 | 本页 ① |
| ② 先动手 | 打开 `ch05_assignment.py`,**先试着写** | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清"魔术方法怎么让对象支持 len/in/+" | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性**:先猜 ① → 写作业。魔术方法名字(`__len__` 等)记不住没关系,回 §5.2 速查表。

---

## ① 预览猜(2 分钟 · 激活你的 Java 直觉)

先别看答案,凭 Java 经验猜一猜:
1. Java `new Product(...)`。Python 创建对象要不要 `new`?
2. Java 让对象能 `for` 遍历要 `implements Iterable`。Python 怎么让一个自定义类支持 `for p in cart`?
3. Java `BigInteger` 相加要 `a.add(b)`,不能写 `a + b`。Python 能让自定义类支持 `+` 吗?
4. Java 调用 `cart.getTotal()`,带括号。Python 能不能写成 `cart.total`(像字段)?
5. Java Lombok `@Data` 自动生成 getter/setter/equals。Python 标准库有没有类似的?

> 猜完,带着验证心态进入正文。

---

## §5.1 @dataclass(对应:`Product`)🟡

Java 老手写数据类要一堆样板(字段 + 构造器 + getter + equals + hashCode + toString),要么靠 Lombok,要么用 record:

```java
// Java record(Java 14+)
public record Product(String name, double price, int stock) {}
```

Python 标准库的 `@dataclass` 装饰器自动生成 `__init__`/`__repr__`/`__eq__`:

```python
from dataclasses import dataclass

@dataclass
class Product:
    name: str
    price: float
    stock: int = 0          # ← 有默认值的字段【必须】放最后

p = Product("键盘", 599.0, 10)      # 自动生成 __init__,不用自己写
p2 = Product("鼠标", 159.0)          # stock 用默认值 0
p == Product("键盘", 599.0, 10)      # True —— 自动生成 __eq__
repr(p)                            # Product(name='键盘', price=599.0, stock=10) —— 自动 __repr__
```

> 🟡 **Java 对比**:就是 Java `record`(不可变)或 Lombok `@Data`(可变)。Python 的 `@dataclass` 默认可变,加 `frozen=True` 可变不可变。
>
> **字段顺序**:有默认值的字段必须在没默认值的后面——和 Java 的「带默认值参数在后」同理,否则没法位置传参。

> ✅ 做 `Product` 题:加 `@dataclass` 装饰器,定义 `name: str`、`price: float`、`stock: int = 0`。就这么几行。

---

## §5.2 魔术方法 + @property(对应:`ShoppingCart` 的各方法)🔴

这是本章精华。Python 的设计哲学:**自定义类通过实现「魔术方法」(双下划线方法 `__xxx__`),就能和语言内置操作无缝集成**——让 `len(cart)`、`p in cart`、`for p in cart`、`cart1 + cart2` 全部对你自己的类生效。

### 魔术方法速查表

| 你想支持 | 实现哪个魔术方法 | Java 对应 |
|----------|-----------------|-----------|
| `len(obj)` | `__len__(self)` | `obj.size()`(无统一协议) |
| `x in obj` | `__contains__(self, x)` | `obj.contains(x)` / Iterable |
| `for x in obj` | `__iter__(self)` | `implements Iterable` |
| `obj[i]` | `__getitem__(self, i)` | `obj.get(i)` |
| `obj1 + obj2` | `__add__(self, other)` | ❌ 无运算符重载 |
| `str(obj)` / `print(obj)` | `__str__` | `toString()` |
| 调试/REPL 显示 | `__repr__` | `toString()`(调试用) |
| `obj == other` | `__eq__` | `equals()` |
| `hash(obj)` | `__hash__` | `hashCode()` |

> 🤯 **Java 老手震惊点**:Java 里 `a + b` 只对基本类型和 String 有效,对象相加必须写 `a.add(b)`。Python 通过 `__add__` 让**任何类**都能定义 `+` 的含义——这叫「运算符重载」,Java 基本没有(只有 `BigInteger`/`String` 等语言特供)。

### `__init__`:初始化(对应 Java 构造器)

```python
class ShoppingCart:
    def __init__(self):           # self = Java 的 this(必须显式写第一个参数)
        self._items: list[Product] = []    # 实例属性
```

- Python **没有 `new`**:`ShoppingCart()` 直接造对象。
- `__init__` 是**初始化**(对象已造好,填属性),不是构造(构造是 `__new__`,99% 不用碰)。
- 第一个参数永远是 `self`(= Java `this`),调用时不传,Python 自动填。
- `_items` 前面下划线 = 约定「内部属性」(仅约定,不强制,= Java 的 private 是假的)。

### `__len__`:让 `len(cart)` 生效

```python
def __len__(self):
    return len(self._items)
```
实现后,`len(cart)` 会自动调你的 `__len__`。Java 没有这种统一协议(各自 `size()`/`length()`/`count()`)。

### `__contains__`:让 `in` 生效

```python
def __contains__(self, item):
    if isinstance(item, Product):         # 判断类型
        return item in self._items
    return any(p.name == item for p in self._items)   # 当字符串名字处理
```
实现后,`kb in cart` 和 `"键盘" in cart` 都能用。`isinstance(x,Cls)` = Java 的 `x instanceof Cls`。

### `__iter__`:让 `for p in cart` 生效

```python
def __iter__(self):
    return iter(self._items)     # 直接复用列表的迭代器
```
实现后,`for p in cart:` 自动遍历。= Java `implements Iterable<T>` 的 `iterator()`。

### `@property`:方法变属性(对应 Java getter)

```python
@property
def total(self) -> float:
    return sum(p.price for p in self._items)

cart.total         # 758.0  ← 像【字段】一样访问,【不带括号】!
```

`@property` 把方法包装成「只读属性」:外部用 `cart.total`(像字段),内部实际是计算。好处:
- 访问简洁(`cart.total` vs Java `cart.getTotal()`)
- 想从「字段」改成「计算」时,调用方代码不用改(都是 `cart.total`)
- 默认**只读**(本题 test 验证:`cart.total = x` 会抛 `AttributeError`)。要可写再加 `@total.setter`。

### `__add__`:运算符重载,让 `+` 生效

```python
def __add__(self, other):
    new = ShoppingCart()
    new._items = self._items + other._items
    return new

c3 = c1 + c2       # 等价于 c1.__add__(c2),返回合并后的新车
```
**注意返回新对象,不改原对象**(本题 test 验证原 cart 不变)。

### `__repr__`:调试显示

```python
def __repr__(self):
    return f"ShoppingCart({len(self)} items, ¥{self.total})"
```
`__repr__` 是「给程序/调试看的官方表示」(Ch01 §1.5 讲过 repr)。REPL 里直接敲 `cart` 回显、`print` 都用它(没定义 `__str__` 时)。

> 🟡 **`__repr__` vs `__str__`**:和 Ch01 的 `repr()`/`str()` 一一对应。`__str__` 给人看(`print`),`__repr__` 给程序看(调试/REPL)。只定义一个时,通常定义 `__repr__`(够用)。= Java 的 `toString()` 只有一个,Python 分两个钩子。

> ✅ 做 `ShoppingCart` 的各方法:按上面对照逐个实现,方法签名照抄。

---

## §5.3 继承 + super()(对应:`DiscountedCart`)🟡

```python
class DiscountedCart(ShoppingCart):       # ← 继承,括号里写父类
    def __init__(self, discount: float = 0.1):
        super().__init__()                 # 调用父类 __init__(= Java super())
        self.discount = discount

    @property
    def total(self) -> float:              # 覆盖父类的 total
        original = super().total           # super() 复用父类计算
        return round(original * (1 - self.discount), 2)
```

要点:
- **继承语法**:`class 子类(父类):`,Java 是 `class 子类 extends 父类`。
- **`super()`**:= Java `super`,调用父类方法。`super().__init__()` 先初始化父类部分。
- **覆盖(override)**:子类同名方法覆盖父类。本例覆盖 `total` property 实现打折,但用 `super().total` 复用父类的求和逻辑。
- 子类自动拥有父类的 `add`/`__len__`/`__contains__` 等(test 验证继承来的方法直接可用)。

> 🟡 **`super().total` 调父类 property**:在子类 property 里用 `super().total` 能拿到父类同名 property 的值,这是常见复用手法。

---

## §5.4 多继承与 MRO(本章了解)

Python 支持**多继承**(一个类继承多个父类),Java 只能单继承+多接口:

```python
class Flyer: def fly(self): ...
class Swimmer: def swim(self): ...
class Duck(Flyer, Swimmer): pass     # 多继承

Duck().fly(); Duck().swim()
```

多继承时方法查找顺序由 **MRO**(Method Resolution Order,C3 线性化)决定,用 `ClassName.__mro__` 查看。本章不出题,知道有这回事即可。实战中**尽量用单继承 + 组合**,多继承主要用于「混入(Mixin)」。

> ⚠️ Java 老手别滥用多继承——菱形继承(diamond)容易出诡异 bug。能用组合(has-a)就别用继承(is-a)。

---

## §5.5 Java 老手常踩的坑 ⚠️

1. **忘了 `self`**:每个实例方法第一个参数必须是 `self`。Java 的 `this` 是隐式的,Python 的 `self` 是显式的。
2. **`__init__` 不是 `__new__`**:`__init__` 是初始化(对象已存在),构造是 `__new__`(几乎不用)。
3. **没有方法重载**:同名方法后定义的覆盖前面的。要可选参数用**默认参数**(Ch01 §1.3),不是重载。
4. **`@property` 不带括号**:定义了 `@property def total`,访问是 `cart.total`(不是 `cart.total()`)。
5. **下划线不强制 private**:`_x` 只是约定「内部用」,外部仍能访问(没有 Java 的编译期 private)。双下划线 `__x` 触发名称改写,半私有。真正的封装靠约定 + 类型检查。
6. **`@dataclass` 字段顺序**:有默认值的字段必须在无默认值的后面。

---

## 📝 本章作业

打开 **`ch05_assignment.py`**,定义 `Product` + `ShoppingCart` + `DiscountedCart`。

| 难度 | 要点 |
|------|------|
| 🟢 | `Product`(@dataclass)、`__init__`/`add`/`__len__`/`__iter__` |
| 🟡 | `__contains__`(双类型)、`@property`、`__repr__` |
| 🔴 | `__add__`(运算符重载)、`DiscountedCart` 继承 + super() |

```bash
uv run pytest 01_python_core/ch05/test_ch05_assignment.py -v
```
全绿 = 掌握 Ch05。哪个魔术方法卡了 → 回 §5.2 速查表。

---

## ✅ 自测:你真的掌握了吗?

- [ ] 能说清「魔术方法是什么?为什么 Python 能让自定义类支持 `len()`/`in`/`+`」(§5.2)
- [ ] 能解释 `@property` 和普通方法的区别,以及为什么 `cart.total` 不带括号(§5.2)
- [ ] 知道 `@dataclass` 自动生成了哪些方法(§5.1)
- [ ] 能说清 `super()` 的作用(§5.3)
- [ ] 作业全绿

---

## 🎓 费曼挑战(直觉 · Ultralearning 原则八)

> 用大白话讲给「Java 同事」听。讲不清 = 没懂,回查对应 §。

任选一题,讲清楚(1-2 分钟):
1. 「Python 怎么让一个自定义类支持 `len()`/`in`/`+`?这和 Java 有什么本质不同?」— 卡壳重读 §5.2
2. 「`@property` 到底干了什么?为什么 `cart.total` 不带括号还能是计算出来的?」— 卡壳重读 §5.2
3. 「`@dataclass` 帮我省了哪些样板代码?对应 Java 的什么?」— 卡壳重读 §5.1

✅ 自检:不查资料,能说清「为什么」吗?

## 🧠 记忆闪卡(⑤ · 原则七)

→ 本章闪卡在 [`review.md`](./review.md)。学完标复习日期(1/3/7 天)。
> 每天开学习前,先翻根 [`REVIEW.md`](../../REVIEW.md) 的「今日复习」总览。

---

## ⏭️ 下一步

Ch05 掌握后,进 **Ch06 · 异常、上下文管理器、文件 IO**——Python 的 `with` 语句(= Java try-with-resources 的优雅版),以及异常体系和自定义异常。
