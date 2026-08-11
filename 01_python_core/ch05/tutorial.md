# Ch05 · OOP:魔术方法、继承、dataclass

> **预计**:1 天 ｜ **前置**:Ch04
> **目标**:理解 Python OOP 和 Java 的本质区别——**没有重载、有多继承、靠「魔术方法」让自定义类支持 `len()`/`in`/`for`/`[]`/`+`/`==`**。
> 本章主线:你是电商后台的「领域建模」负责人,一天之内交付一整套领域类——商品、订单、库存清单、价目表、金额、折扣购物车、结算台。交付标准只有一条:**像内置类型一样好用**。

> 📐 **本教程的契约**:下面每一节(§5.1–§5.6)都**精确对应**作业里的题。讲过的才考,考的必讲过。卡住时,按对应表回查小节即可。
>
> 🏭 **作业形态说明(重要)**:本章每题是一个「类工厂」函数——**在函数体内定义题目要求的类,然后 `return` 这个类本身**(不是实例!)。测试拿到你的类后做全套质检。为什么可以返回类?§5.1 讲。

---

## 🗺️ 本章地图(元学习 · 原则一)

学完这章,你将能够:
- 用 `@dataclass` 一行定义数据类(= Java Lombok `@Data` / record),说清字段顺序规则
- 用 `@property` 把方法变成「像字段一样访问」,知道为什么只读属性不用写 setter
- 实现**容器协议** `__len__` / `__contains__` / `__iter__` / `__getitem__`,让自定义类支持 `len()`/`in`/`for`/`[]`
- 实现 `__add__` / `__eq__` / `__hash__` / `__repr__`,说清「定义 `__eq__` 后 `__hash__` 去哪了」
- 用**继承 + `super()`** 复用父类逻辑,知道 MRO 是什么、为什么组合优先于多继承

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业题 | 对应小节 | 核心知识点 |
|--------|----------|-----------|
| `make_product_class` | §5.1 | 类基础 + @dataclass |
| `make_order_class` | §5.2 | 手写 __init__ + @property |
| `make_inventory_class` | §5.3 | __len__ / __contains__ / __iter__ |
| `make_price_list_class` | §5.3 | __getitem__ |
| `make_money_class` | §5.4 | __add__ / __eq__ / __hash__ / __repr__ |
| `make_discount_cart_class` | §5.5 | 继承 + super() |
| `make_checkout_class` | §5.6 | 综合(全部协议) |

---

## ⏱️ 学习路径:费曼五步(约 60-90 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 下面 5 个 Java 问题,猜 Python 怎么写 | 本页 ① |
| ② 先动手 | 打开 `ch05_assignment.py`,**先试着写**(别看教程) | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清"魔术方法怎么让对象支持 len/in/+" | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性原则**:别通读!先猜 ① → 去 ② 写作业 → **哪题卡了,回对应 § 查** → 改 → 再跑。§5.4(Money 四契约)最容易卡,卡住先看「`__eq__` 与 `__hash__` 的协定」。

---

## ① 预览猜(2 分钟 · 激活你的 Java 直觉)

先别看答案,凭 Java 经验猜一猜(猜错记得更牢):
1. Java `Product p = new Product("键盘", 599.0);`。Python 创建对象要不要写 `new`?
2. Java 拿订单总额要写 `order.getTotal()`,带括号。Python 能不能写成 `order.total`,像访问字段一样?
3. Java 让对象能 `for` 遍历要 `implements Iterable<T>`。Python 想让自定义类支持 `len(inv)`、`sku in inv`、`for sku in inv`,要 implements 什么接口?
4. Java 不支持运算符重载,`BigInteger` 相加只能 `a.add(b)`。Python 能让 `Money(100) + Money(50)` 生效吗?
5. Java 约定「重写 `equals` 必须重写 `hashCode`」,靠 Code Review 盯。Python 里你只定义了 `__eq__` 没管 hash,猜猜会发生什么?(提示:Python 比 Java 狠)

> 猜完,带着验证心态进入正文。第 5 题的答案在 §5.4,是本章最容易踩的坑。

---

## §5.1 类的基础与 @dataclass(对应:`make_product_class`)🟡

### Java 对照:一个数据类要多少样板

```java
// Java:要么手写一堆样板……
public class Product {
    private final String name;
    private final double price;
    private final int stock;
    public Product(String name, double price, int stock) { ... }
    // getter × 3 + equals + hashCode + toString ……
}
// ……要么 Lombok @Data,要么 Java 14+ 的 record:
public record Product(String name, double price, int stock) {}
```

### Python 最小类:没有 `new`,`self` 显式

```python
class Product:
    def __init__(self, name, price):     # self = Java 的 this,必须显式写第一个
        self.name = name                 # 实例属性挂在 self 上
        self.price = price

p = Product("机械键盘", 599.0)            # ✅ 没有 new,类名直接调用
p.name                                   # "机械键盘"
```

- 🟢 `__init__` ≈ Java 构造器,但严格说它是**初始化**(对象已被 `__new__ 造好,`__init__` 只填属性)。99% 的场景只碰 `__init__`。
- 🟡 调用 `Product("机械键盘", 599.0)` 时,Python 自动把新对象塞进第一个参数 `self`——**调用时不传,定义时必须写**。

❌ **忘写 `self`** 的经典报错,读法要会:

```python
class Product:
    def __init__(name, price): ...       # ❌ 忘了 self
Product("机械键盘", 599.0)
# TypeError: __init__() takes 2 positional arguments but 3 were given
#                                    ↑ 多出来的那个就是自动传入的 self
```

### 🔴 类也是对象:为什么本章作业是「类工厂」

Ch01 说过「一切皆对象」,类也不例外。**类可以在函数里定义、当返回值返回**——这在 Java 里没有对应物(匿名内部类不算):

```python
def make_product_class():
    class Product:                       # 类定义在函数体内
        ...
    return Product                       # 返回类本身,不加括号!

Product = make_product_class()           # 拿到类
p = Product("机械键盘", 599.0, 10)        # 再实例化
```

标准库里的 `collections.namedtuple` 就是官方类工厂:`Point = namedtuple("Point", ["x", "y"])` 返回的就是一个类。本章作业全是这个形态:**你在函数体内造类,测试拿你的类做质检**。

> 📝 类定义在函数内时,自动 `__repr__` 会带 `make_product_class.<locals>.Product(...)` 这样的限定名前缀——正常现象,不是bug。

### @dataclass:标准库自带的 Lombok

```python
from dataclasses import dataclass

@dataclass
class Product:
    name: str
    price: float
    stock: int = 0          # ← 有默认值的字段【必须】放最后

p = Product("机械键盘", 599.0, 120)       # 自动生成 __init__
p2 = Product("无线鼠标", 159.0)            # stock 用默认值 0
p == Product("机械键盘", 599.0, 120)       # True —— 自动生成 __eq__
repr(p2)  # "...Product(name='无线鼠标', price=159.0, stock=0)" —— 自动 __repr__
```

> 🟡 **三个关键点**:
> 1. **字段顺序**:有默认值的字段必须在无默认值的后面(和函数默认参数同理,否则没法位置传参)。
> 2. **默认可变**:字段可以改(`p.stock = 5` 合法),≈ Lombok `@Data`;加 `frozen=True` 才是 Java record 那种不可变。
> 3. **自动 `__eq__` 带类型检查**:和别的类型比较直接 `False`,不抛异常。

❌ 错误写法 → ✅ 正确写法:

```python
@dataclass
class Product:
    stock: int = 0          # ❌ 默认值字段在前
    name: str               # TypeError: non-default argument 'name' follows default argument

@dataclass
class Product:
    name: str               # ✅ 无默认值的先排
    price: float
    stock: int = 0
```

> ✅ **做 `make_product_class` 题**:`@dataclass` + 三个字段(注意顺序)+ `return Product`(返回类,不加括号!)。

---

## §5.2 @property:把计算伪装成字段(对应:`make_order_class`)🟡

### Java 对照:getter 的括号包袱

```java
// Java:拿订单总额,方法调用带括号
public double getTotal() {
    return items.stream().mapToDouble(i -> i.price * i.qty).sum();
}
order.getTotal();
```

```python
# Python:@property 让方法像字段一样被访问
class Order:
    def __init__(self):
        self._items: list[dict] = []

    def add_item(self, name, price, qty=1):
        self._items.append({"name": name, "price": price, "qty": qty})

    @property
    def total(self):
        return round(sum(i["price"] * i["qty"] for i in self._items), 2)

o = Order()
o.add_item("机械键盘", 599.0, 2)
o.add_item("无线鼠标", 159.0)
o.total          # 1357.0 ← 像字段!不带括号!内部其实是每次现算
```

### 为什么 Java 老手会喜欢这个设计

- **访问简洁**:`o.total` vs `o.getTotal()`,调用方代码干净。
- **实现可换**:今天是现算,明天想加缓存——只要保持 `o.total` 这个访问形态,调用方一行不用改。Java 里「字段改方法」是破坏性变更,Python 靠 `@property` 抹平。
- **天然只读**:不定义 setter,`o.total = 999` 直接抛 `AttributeError`。要可写再补 `@total.setter`(了解即可,作业不用)。

### ❌ 错误写法 → ✅ 正确写法

```python
o.total()        # ❌ TypeError: 'float' object is not callable
                 #    total 已经是算好的 float 了,你又在调用它
o.total          # ✅ property 访问不带括号
```

### 🔴 经典坑:实例属性 vs 类属性(测试会拦!)

```python
class Order:
    _items = []                      # ❌ 写在类体里 = 类属性(≈ Java static)!
    def add_item(self, name, price, qty=1):
        self._items.append(...)      # 所有实例共享同一个列表

a, b = Order(), Order()
a.add_item("机械键盘", 599.0, 1)
b.total          # 599.0?? b 的订单里凭空多了键盘——串单事故!
```

```python
class Order:
    def __init__(self):
        self._items = []             # ✅ 实例属性必须在 __init__ 里创建
```

Java 里 `static` 关键字明晃晃写着,Python 里区别只在**写在类体还是 `__init__`**——视觉上很像,语义天差地别。这是 Java 老手在 Python OOP 里栽的第一个坑。

> ✅ **做 `make_order_class` 题**:`__init__` 里建空列表 → `add_item` 追加 dict → `@property total` 现算总和(`round(..., 2)`)。别定义 setter,测试会验证只读;也别缓存结果,测试会验证「加完商品 total 会重算」。

---

## §5.3 容器协议:len / in / for / [](对应:`make_inventory_class`、`make_price_list_class`)🔴

### 协议速查表

| 你想支持 | 实现哪个魔术方法 | Java 对应 |
|---------|-----------------|-----------|
| `len(obj)` | `__len__(self)` | `obj.size()` / `arr.length`(各自为政) |
| `x in obj` | `__contains__(self, x)` | `obj.contains(x)` |
| `for x in obj` | `__iter__(self)` | `implements Iterable<T>` |
| `obj[key]` | `__getitem__(self, key)` | `obj.get(key)`(语法层面没有) |

> 🔴 **本质区别**:Java 里这些能力是**接口**(`Iterable`/`Collection`),要写 implements;Python 里是**协议**——不用继承任何东西,只要类上有对应魔术方法,内置语法就认。这就是「鸭子类型」的地基。

### 真实场景一:库存清单(三件套)

仓管拿清单做盘点:有几种 SKU(`len`)、某 SKU 在不在(`in`)、逐个打印盘点(`for`):

```python
class Inventory:
    def __init__(self, stock: dict):
        self._stock = dict(stock)        # ← 防御性拷贝,下面讲

    def __len__(self):
        return len(self._stock)

    def __contains__(self, sku):
        return sku in self._stock

    def __iter__(self):
        return iter(self._stock)         # 直接复用 dict 的迭代器

inv = Inventory({"KB-001": 120, "MS-002": 300})
len(inv)            # 2
"KB-001" in inv     # True
"XX-000" in inv     # False
for sku in inv:     # 按插入顺序逐个给 "KB-001"、"MS-002"
    print(sku)
```

两个细节:

1. **`iter(self._stock)` 技巧**:不用手写迭代器类,内置容器的迭代器直接借来用(Ch03 讲过迭代器协议)。
2. **防御性拷贝 `dict(stock)`**:≈ Java 的 `new HashMap<>(m)`。不拷的话,调用方构造完又改原字典,你的清单就被「隔山打牛」了。作业测试会构造后改原字典来拦你。

> 🟡 **冷知识**:没定义 `__contains__` 时,`in` 不会报错——Python 退化成用 `__iter__` 逐个比对(O(n) 慢)。定义了 `__contains__` 就走 O(1) 哈希查找。两个都没有才 TypeError。

### 真实场景二:价目表(`__getitem__`)

调用方查价想写得像字典:`price_list["KB-001"]`,而不是 `price_list.getBySku("KB-001")`:

```python
class PriceList:
    def __init__(self, prices: dict):
        self._prices = dict(prices)

    def __getitem__(self, sku):
        return self._prices[sku]         # dict 对缺失 key 天然抛 KeyError

pl = PriceList({"KB-001": 599.0, "MS-002": 159.0})
pl["KB-001"]       # 599.0
pl["NOPE"]         # KeyError: 'NOPE' ← 不用自己判断,字典帮你抛
```

`__getitem__` 是 `[]` 语法的入口。以后你还会看到它支持切片(`obj[1:3]` 传进来的是 `slice` 对象)、支持负数索引——`list`/`str` 的 `[]` 能力全是它。

> ✅ **做 `make_inventory_class` 题**:三件套 + 构造时 `dict(stock)` 拷贝。
> ✅ **做 `make_price_list_class` 题**:`__getitem__` 里直接用字典取值,让 KeyError 自然发生。

---

## §5.4 运算符与显示:__add__ / __eq__ / __hash__ / __repr__(对应:`make_money_class`)🔴

### Java 对照:运算符重载?不存在的

```java
// Java:BigInteger 相加,只能方法调用
BigInteger total = price.add(tax);
```

```python
# Python:任何类都能定义 + 的含义——实现 __add__ 即可
Money(100.0) + Money(50.0)     # Money(150.00)
```

### `__add__` 的两条契约

```python
class Money:
    def __init__(self, amount):
        self.amount = amount

    def __add__(self, other):
        if not isinstance(other, Money):
            return NotImplemented              # ← 契约二:不认识的类型
        return Money(self.amount + other.amount)  # ← 契约一:返回新对象
```

- **契约一:返回新对象,不改自己**。`a + b` 算出的是新金额,`a` 和 `b` 都不能动——否则链式表达式 `a + b + c` 会把 `a` 改得面目全非。
- **契约二:不认识的类型返回 `NotImplemented`**(不是抛异常!)。Python 拿到 `NotImplemented` 会再去试对方的反向方法(`__radd__`),双方都不认识才抛 `TypeError`。
  - 🟡 `isinstance(x, Cls)` = Java 的 `x instanceof Cls`。

❌ 错误写法 → ✅ 正确写法:

```python
def __add__(self, other):
    self.amount += other.amount      # ❌ 把 a 改了!a + b 之后 a 变成 150
    return self

def __add__(self, other):
    if not isinstance(other, Money):
        return NotImplemented
    return Money(self.amount + other.amount)   # ✅ 新对象
```

### 🔴 `__eq__` 与 `__hash__` 的协定(预览猜第 5 题答案)

Java 约定「重写 `equals` 必须重写 `hashCode`」,靠纪律;**Python 强制执行:你在类里一定义 `__eq__`,`__hash__` 就被自动设为 `None`**——实例直接不可哈希,set / dict key 全废:

```python
class Money:
    def __eq__(self, other): ...
    # 没写 __hash__ → Python 把它置 None

{Money(10.0), Money(20.0)}       # ❌ TypeError: unhashable type
```

解法:手写 `__hash__`,且必须和 `__eq__` 一致(相等的对象哈希值必须相同):

```python
def __eq__(self, other):
    if not isinstance(other, Money):
        return NotImplemented
    return self.amount == other.amount

def __hash__(self):
    return hash(self.amount)

{Money(10.0), Money(10.0)}       # {Money(10.00)} —— 去重成功
agg = {Money(10.0): 1}
agg[Money(10.0)] += 1            # 同金额命中同一个 key → 「按金额聚合计数」
```

> 🟡 **顺带**:`@dataclass` 默认生成 `__eq__` 但不生成 `__hash__`(同样置 None);要可哈希得 `frozen=True` 或 `eq=True, unsafe_hash=True`。作业里 `Product` 不需要哈希,`Money` 需要手写——正好对比着记。

### `__repr__`:给调试看的「官方表示」

- `__repr__`:给程序/调试看(REPL 回显、日志、`repr()`),目标**无歧义**,理想是能 `eval` 回去。
- `__str__`:给终端用户看(`print()`),目标好读。**只定义一个时定义 `__repr__`**——没 `__str__` 时 `print` 会拿 `__repr__` 兜底。
- ≈ Java 的 `toString()`,只是 Python 分了「给人看 / 给程序看」两个钩子。

金额显示用到 f-string 的格式说明符(Ch02 见过,这里复习):`f"{amount:.2f}"` = 保留两位小数:

```python
def __repr__(self):
    return f"Money({self.amount:.2f})"

repr(Money(12.5))      # "Money(12.50)"
repr(Money(100.0))     # "Money(100.00)"
```

> ⚠️ 真实账务别用 float(`0.1 + 0.2 = 0.30000000000000004`),用 `Decimal`。本章为聚焦 OOP 用 float 简化,测试也避开了精度雷区。

> ✅ **做 `make_money_class` 题**:四件套照上面契约写。最容易漏的是 `__hash__`——漏了它,set 去重测试直接 TypeError。

---

## §5.5 继承与 super()(对应:`make_discount_cart_class`)🟡

### 语法对照

```java
// Java
public class DiscountedCart extends Cart {
    private final double discount;
    public DiscountedCart(double discount) {
        super();
        this.discount = discount;
    }
    @Override
    public double getTotal() {
        return Math.round(super.getTotal() * (1 - discount) * 100.0) / 100.0;
    }
}
```

```python
# Python:括号里写父类;没有 extends,也没有 @Override 注解,同名即覆盖
class DiscountedCart(Cart):
    def __init__(self, discount=0.1):
        super().__init__()              # 先初始化父类部分(= Java super())
        self.discount = discount

    @property
    def total(self):                    # 覆盖父类的 total property
        return round(super().total * (1 - self.discount), 2)
        #       ^^^^^^^^^^^^^^ 复用父类的求和逻辑,自己只加打折
```

### 真实场景:大促折扣车(就是作业)

普通车 `Cart` 已经能加商品、算总价;大促要整单打折,**复用而不是复制**:

```python
c = DiscountedCart(discount=0.2)   # 整单 8 折
c.add("机械键盘", 599.0)            # add 是父类继承来的,直接用
c.add("无线鼠标", 159.0)
c.total                            # 606.4  (758.0 × 0.8)
DiscountedCart().discount          # 0.1    (默认 9 折)
```

要点:
- **`super()` 无参写法**:Python 自动填「当前类 + self」;老代码里的 `super(DiscountedCart, self)` 是 Python 2 遗物,认识即可。
- **`super().total` 拿父类 property 的值**:子类覆盖同名 property 时,这是「复用父类计算」的标准手法。
- 子类自动继承父类的 `add`、`__init__` 以外的所有方法——测试会验证 `add` 确实是继承来的。

### 多继承与 MRO(了解,作业不考)

Python 支持**多继承**(Java 只能单继承 + 多接口):

```python
class Flyer:   def fly(self): return "fly"
class Swimmer: def swim(self): return "swim"
class Duck(Flyer, Swimmer): pass        # 多继承

Duck.__mro__     # 方法查找顺序(MRO,C3 线性化算法):
                 # (Duck, Flyer, Swimmer, object)
```

> ⚠️ **Java 老手自诫**:多继承的菱形问题(diamond)能出诡异 bug。工程实践里**单继承 + 组合优先**(has-a 优于 is-a),多继承主要给「Mixin」用。面试能说出「MRO = 方法查找顺序,`Cls.__mro__` 可查」就够。

> ✅ **做 `make_discount_cart_class` 题**:函数体内先写父类 `Cart`(`__init__`/`add`/`@property total`),再写子类 `DiscountedCart(Cart)` 覆盖 `total`,用 `super().total` 复用。**返回子类**,别返回父类。

---

## §5.6 综合实战:结算台 Checkout(对应:`make_checkout_class`)🔴

毕业题:一个类集成本章全部协议。先画「需求 → 魔术方法」对照表,再动手:

| 收银台需求 | Python 写法 | 你要实现的 |
|-----------|------------|-----------|
| 加商品(可带数量) | `c.add("机械键盘", 599.0, 2)` | `add(name, price, qty=1)` |
| 一共几件? | `len(c)` | `__len__` → Σ qty(注意:不是明细条数) |
| 键盘在单里吗? | `"机械键盘" in c` | `__contains__` |
| 打印每条明细 | `for item in c` | `__iter__` |
| 两台并一台 | `c1 + c2` | `__add__` → 新对象,不改原件 |
| 总金额 | `c.total` | `@property` → Σ price×qty,round 2 位 |
| 小票头 | `repr(c)` | `__repr__` → `"Checkout(2 种商品, 共 3 件, ¥1357.0)"` |

**集成技巧**:类内部可以用自己的魔术方法,不用重复实现:

```python
def __repr__(self):
    return f"Checkout({len(self._items)} 种商品, 共 {len(self)} 件, ¥{self.total})"
    #                                                 ^^^^^^^^^^  ^^^^^^^^^^
    #                                          调自己的 __len__   用自己的 property
```

> ✅ **做 `make_checkout_class` 题**:照着对照表逐个实现。`__len__` 是「总件数 Σqty」、repr 里的「种数」是明细条数 `len(self._items)`——两个口径别搞混,测试各查各的。

---

## ⚠️ Java 老手常踩的坑(本章汇总)

1. **忘写 `self`**:实例方法第一个参数必须是 `self`,报错读法「takes N arguments but N+1 given」。(§5.1)
2. **字段写进类体**:类体里 `_items = []` 是**类属性**,所有实例共享同一个列表——≈ 误加 `static`。实例属性必须在 `__init__` 里 `self._items = []`。(§5.2)
3. **property 加括号**:`o.total()` 是在调用一个 float,`TypeError: 'float' object is not callable`。(§5.2)
4. **`@dataclass` 字段顺序**:带默认值的字段必须放最后,否则 `TypeError: non-default argument follows default argument`。(§5.1)
5. **定义 `__eq__` 忘写 `__hash__`**:`__hash__` 被置 None,实例不可哈希,set/dict key 全废——Python 版「equals/hashCode 协定」,但它是强制的。(§5.4)
6. **`__add__` 改 `self`**:运算符必须返回新对象;改自己会让 `a + b` 把 `a` 毁掉。(§5.4)
7. **对不认识的类型抛异常**:`__eq__`/`__add__` 里应返回 `NotImplemented`,让 Python 协调反向方法;直接抛异常会破坏对称性。(§5.4)
8. **以为有方法重载**:同名方法后定义的覆盖前面的。可选参数用默认值(`qty=1`),不是重载。(§5.5)
9. **`__init__` 不是构造器**:构造是 `__new__`(99% 不碰),`__init__` 只是初始化。创建对象不写 `new`。(§5.1)

---

## 📝 本章作业(7 个类工厂,电商领域建模主线)

打开 **`ch05_assignment.py`**,每题 docstring 里标了【对应小节】,卡住回查:

| 函数 | 场景 | 知识点 | 难度 |
|------|------|--------|------|
| `make_product_class` | 商品模型 | @dataclass | 🟢 |
| `make_order_class` | 订单总金额 | __init__ + @property | 🟡 |
| `make_inventory_class` | 库存清单盘点 | __len__ / __contains__ / __iter__ | 🟡 |
| `make_price_list_class` | 价目表查价 | __getitem__ | 🟢 |
| `make_money_class` | 金额对账/聚合 | __add__ / __eq__ / __hash__ / __repr__ | 🔴 |
| `make_discount_cart_class` | 大促折扣车 | 继承 + super() | 🟡 |
| `make_checkout_class` | 结算台小票 | 综合(全部协议) | 🔴 |

```bash
uv run pytest 01_python_core/ch05/test_ch05_assignment.py -v
```

全绿 = 掌握 Ch05。哪题卡了 → 回对应 § 速查。

---

## ✅ 自测:你真的掌握了吗?

- [ ] 能写对一个最小类(`__init__` + `self.xxx`),说清 `self` 和 `new` 的事(§5.1)
- [ ] 能说清 `@dataclass` 自动生成了什么、字段顺序规则、默认可变还是不可变(§5.1)
- [ ] 能解释 `@property` 为什么不带括号、为什么天然只读(§5.2)
- [ ] 能默写容器协议四件套:`__len__`/`__contains__`/`__iter__`/`__getitem__`(§5.3)
- [ ] 能说清「定义 `__eq__` 后 `__hash__` 怎么了」,以及 `NotImplemented` 是干嘛的(§5.4)
- [ ] 能用 `super()` 复用父类逻辑,知道 `Cls.__mro__` 查什么(§5.5)
- [ ] 7 个作业全绿

---

## 🎓 费曼挑战(直觉 · Ultralearning 原则八)

> 用大白话讲给「Java 同事」听。**讲不清 = 没懂**,回查对应 §。

任选一题,讲清楚(1-2 分钟):
1. 「Python 怎么让一个自定义类支持 `len()`/`in`/`+`?这和 Java 的 implements 接口有什么本质不同?」— 卡壳重读 §5.3/§5.4
2. 「为什么 Python 里定义了 `__eq__`,`__hash__` 就没了?这和 Java 的 equals/hashCode 协定什么关系?」— 卡壳重读 §5.4
3. 「`@property` 到底干了什么?为什么 `order.total` 不带括号还能是现算出来的?」— 卡壳重读 §5.2

✅ 自检:不查资料、不堆术语,能说清「为什么」吗?

## 🧠 记忆闪卡(⑤ · 原则七)

→ 本章闪卡在 [`review.md`](./review.md)。学完标复习日期(1/3/7 天)。
> 每天开学习前,先翻根 [`REVIEW.md`](../../REVIEW.md) 的「今日复习」总览。

---

## ⏭️ 下一步

Ch05 掌握后,进 **Ch06 · 异常、上下文管理器、文件 IO**——Python 的 `with` 语句(= Java try-with-resources 的优雅版)、异常体系和自定义异常。你在本章写的领域类,到那章要学会「出错时怎么体面地抛、安全地关资源」。
