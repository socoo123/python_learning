# Ch02 · 数据结构:list / tuple / dict / set

> **预计**:1 天 ｜ **前置**:Ch01
> **目标**:掌握 Python 四大内置容器,精确对应 Java 的 `ArrayList` / 不可变 List / `LinkedHashMap` / `HashSet`,并学会 **Pythonic** 用法(切片、推导式、集合运算)。
> 本章主线:你在给电商后台写一个「商品数据中台」——热销榜、价格区间、价格速查表、类目分组、库存货值、引流款分析、组合筛选器,全部跑在 `products.json`(10 个商品)上。

> 📐 **本教程的契约**:下面每一节(§2.1–§2.7)都**精确对应**作业里的题。讲过的才考,考的必讲过。卡住时,按对应表回查小节即可。

---

## 🗺️ 本章地图(元学习 · 原则一)

学完这章,你将能够:
- 说出四大容器分别对应 Java 的什么,行为差在哪(如 `dict` 是 `LinkedHashMap` 不是 `HashMap`)
- 用**切片**(Java 完全没有)取子序列/反转/取前 N 名,且不踩「越界不报错」的坑
- 用 `sorted(key=lambda ...)` 排序,说清它和 `.sort()` 的区别(改不改原列表)
- 用元组解包让函数「返回多个值」,一行交换变量
- 用 `dict.get()` / `setdefault` / `defaultdict` 做读取、分组、聚合(对比 `getOrDefault` / `computeIfAbsent`)
- 用 `set` 一行去重、用 `&` `|` `-` 做集合运算(对比 `retainAll` / `addAll`)
- 用 `min/max + key` 找「每类最便宜」这类最值问题
- 避开 **可变默认参数陷阱**(面试必考 + 实战高频 bug,Java 没有)

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业题 | 对应小节 | 核心知识点 |
|--------|----------|-----------|
| `get_top_products_by_price` | §2.1 | list 切片 + `sorted(key=...)` |
| `price_range` | §2.2 | tuple 多返回值 + 解包 |
| `build_price_map` | §2.3 | `d[k]` vs `.get()` + 字典推导式 |
| `group_by_category` | §2.4 | `setdefault` 分组 |
| `category_inventory_value` | §2.4 | `defaultdict` 聚合 |
| `all_categories` | §2.5 | set 推导式 + 去重 |
| `find_cheapest_per_category` | §2.6 | `min(key=...)` + 复用分组 |
| `filter_products` | §2.7 | 可变默认参数陷阱 + 组合过滤 |

---

## ⏱️ 学习路径:费曼五步(约 60-90 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(1分钟) | 下面 5 个 Java 操作,猜 Python 怎么写 | 本页 ① |
| ② 先动手 | 打开 `ch02_assignment.py`,**先试着写**(别看教程) | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清"可变默认参数为何是 bug""dict 为何有序" | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性原则**:别通读!先猜 ① → 去 ② 写作业 → **哪题卡了,回对应 § 查** → 改 → 再跑。

---

## ① 预览猜(1 分钟 · 激活你的 Java 直觉)

先别看答案,凭 Java 经验猜一猜(猜错记得更牢):
1. Java 取子列表:`list.subList(1, 3)`。Python 一行怎么写?**反转**整个列表呢?
2. Java 方法要返回「最低价、最高价」两个值,得造个 record。Python 怎么返回?
3. Java `map.get("x")` 键不存在返回 `null`。Python `d["x"]` 键不存在会怎样?
4. Java 求两个 Set 的交集 `a.retainAll(b)`——注意它会**顺手改掉 a**!Python 用什么,改不改原集合?
5. `def add_tag(item, tags=[]): tags.append(item); return tags` 连续调用两次 `add_tag("a")`、`add_tag("b")`,第二次返回什么?

> 猜完带着验证心态进入正文。第 5 题是本章最大的坑,答案在 §2.7。

---

## 速查:四大容器 vs Java

| Python | Java 对应 | 可变? | 有序? | 典型用途 |
|--------|-----------|--------|--------|----------|
| `list` | `ArrayList` | ✅ | ✅(插入序) | 有序集合、栈/队列 |
| `tuple` | 不可变 `List` / `record` | ❌ | ✅ | 多返回值、固定结构、字典键 |
| `dict` | **`LinkedHashMap`**(3.7+) | ✅ | ✅(插入序) | 键值映射 |
| `set` | `HashSet` | ✅ | ❌ | 去重、集合运算 |
| `frozenset` | 不可变 `Set` | ❌ | ❌ | 可哈希,能当字典键 |

> 🟡 **最重要的一个差异**:Python `dict` 从 3.7 起**保证插入有序**,行为 = Java `LinkedHashMap`,不是你直觉里的无序 `HashMap`。遍历顺序 = 插入顺序,写代码可以依赖这一点。

---

## §2.1 list:索引、切片与排序(对应:`get_top_products_by_price`)🔴

### 创建与索引 🟢

```java
// Java
List<String> names = new ArrayList<>(List.of("机械键盘", "无线鼠标", "设计模式"));
names.get(0);                          // "机械键盘"
names.get(names.size() - 1);           // "设计模式" —— 取最后一个好啰嗦
```

```python
# Python
names = ["机械键盘", "无线鼠标", "设计模式"]
names[0]        # "机械键盘"
names[-1]       # "设计模式"   负索引:从末尾数,Java 没有
names[-2]       # "无线鼠标"
```

真实场景:运营问「最新上架的商品是哪个」——mock 数据按上架顺序排,最后一个就是:

```python
products[-1]["name"]    # "人体工学椅"(products.json 里 id=10)
products[0]["name"]     # "机械键盘"
```

### 切片 🔴(Java 完全没有,本章头号利器)

骨架:`a[起:止:步长]`,**左闭右开**,任意一段都可省略:

```python
a = [10, 20, 30, 40, 50]
a[1:3]      # [20, 30]    ≈ Java subList(1, 3),但返回独立新列表
a[:2]       # [10, 20]    省略开头 = 从头
a[2:]       # [30, 40, 50] 省略结尾 = 到尾
a[-2:]      # [40, 50]    最后两个
a[::2]      # [10, 30, 50] 步长 2
a[::-1]     # [50, 40, 30, 20, 10]   反转!经典技巧
```

真实场景(全部能用 products.json 验证):

```python
products[:3]                     # 前 3 个商品:热销榜「Top 3 展位」
products[-2:]                    # 最后 2 个:智能水杯、人体工学椅
[p["price"] for p in products][::-1]   # 价格倒序列表(反转技巧)
```

🟡 **和 Java 的关键差异:切片越界不报错**:

```java
list.subList(0, 100);   // ❌ IndexOutOfBoundsException
```

```python
products[0:100]         # ✅ 不报错,自动截到末尾,返回全部 10 个
products[5:3]           # ✅ 不报错,返回 [](起 > 止 = 空)
```

这就是为什么 `get_top_products_by_price(products, n=100)` 用 `[:n]` 切片天然安全——**n 超过总数不会炸**。

### `sorted()` vs `.sort()` 🟡(Java 老手必踩)

```python
a = [3, 1, 2]
b = sorted(a)     # ✅ b = [1, 2, 3],a 不变(≈ stream().sorted().collect())
a.sort()          # ✅ a 就地变成 [1, 2, 3],返回值是 None
```

❌ 错误写法 → ✅ 正确写法:

```python
b = a.sort()                  # ❌ b 是 None!sort() 就地排序不返回新列表
b = sorted(a)                 # ✅ 要新列表用 sorted()
```

**为什么本章作业必须用 `sorted` 而不是 `.sort()`**:你的函数收到调用方传来的 `products` 列表,如果用 `products.sort()` 就**改乱了人家的数据**(副作用!后台系统里别的模块还在用这个列表)。测试专门有一条「调用后原列表顺序不变」的用例,就是拦这个的。

### lambda:排序的「比较钥匙」🔴

`sorted` / `min` / `max` 都收一个 `key=...` 参数,告诉它**按什么比**。值通常是一个 lambda(匿名函数):

```python
# Python lambda:lambda 参数: 表达式
sorted(products, key=lambda p: p["price"])                 # 按价格升序
sorted(products, key=lambda p: p["price"], reverse=True)   # 按价格降序
```

```java
// Java 等价,几乎一一对应:
products.stream()
        .sorted(Comparator.comparing(p -> p.getPrice()))
        .toList();
```

> 🟡 **和 Java lambda 的唯一区别**:Python lambda 只能写**单个表达式**(不能多行、不能有语句),返回该表达式的值。复杂逻辑用 `def`。
> 一句话记住:`key=lambda p: p["price"]` =「按 p 的 price 字段比较」。

### 组合起来:热销榜(get_top_products_by_price 原型)

```python
def get_top_products_by_price(products, n=3):
    top = sorted(products, key=lambda p: p["price"], reverse=True)[:n]
    return [p["name"] for p in top]

get_top_products_by_price(products, 3)
# ["27寸4K显示器", "人体工学椅", "降噪耳机"]   (2199 / 1599 / 1299)
get_top_products_by_price(products, 100)     # 10 个全返回,切片不炸
```

读法:「按价格降序排 → 切片取前 n → 推导式只留名字」。三步各对应本节一个知识点。

### 附:list 常用方法速查 🟢

| Python | Java `ArrayList` | 说明 |
|--------|------------------|------|
| `a.append(x)` | `add(x)` | 尾部追加 |
| `a.extend(xs)` | `addAll(xs)` | 批量追加 |
| `a.pop()` | `remove(size-1)` | 删并返回末尾;`a.pop(0)` = `pollFirst` |
| `a.remove(x)` | `remove(Object)` | 删第一个**等于 x** 的元素(不是按索引!) |
| `x in a` | `contains(x)` | 成员判断 |
| `len(a)` | `a.size()` | 注意是**函数**不是方法 |

> ✅ **做 `get_top_products_by_price` 题**:`sorted(..., reverse=True)` → `[:n]` → 列表推导取 name。**别用 `.sort()`**,会改乱调用方的列表。

---

## §2.2 tuple:解包与多返回值(对应:`price_range`)🟡

tuple 是**不可变**序列。对 Java 老手,它两个最香的用途是:**多返回值** 和 **解包**。

### Java 对照:返回两个值有多麻烦

```java
// Java:想返回 (最低价, 最高价),得先造个类型
record PriceRange(double low, double high) {}
PriceRange priceRange(List<Product> products) { ... }
```

```python
# Python:return 时用逗号一写,就是一个 tuple
def price_range(products):
    prices = [p["price"] for p in products]
    return min(prices), max(prices)     # 实际返回 (min, max) 一个 tuple

result = price_range(products)          # result == (75.5, 2199.0)
low, high = price_range(products)       # 解包:low=75.5, high=2199.0
```

> 🟢 Python 函数**只能返回一个值**,但 tuple 让它**看起来**返回了多个——这是全 Python 生态的通用做法。

### 解包:一行接住多个值 🟡

```python
point = (3, 4)
x, y = point                  # 解包:x=3, y=4
a, b = b, a                   # 交换(Ch01 讲过:右边先打包成 tuple,再解包)

# 星号解包:收集「剩下的」(了解即可,Ch03 详讲)
first, *rest = [1, 2, 3, 4]   # first=1, rest=[2, 3, 4]
```

真实场景:接口返回 (状态码, 响应体)、CSV 解析返回 (表头, 行列表)……凡是「一包多个值」的地方都是解包:

```python
low, high = price_range(products)
f"全场 {low} 元起,最贵 {high} 元"     # "全场 75.5 元起,最贵 2199.0 元"
```

### 坑:单元素 tuple 必须带逗号 ❌→✅

```python
t = (1)       # ❌ 这是 int 1,不是 tuple!括号只是运算优先级
t = (1,)      # ✅ 逗号才是 tuple 的标志
type((1))     # <class 'int'>
type((1,))    # <class 'tuple'>
```

> 记忆:**tuple 的灵魂是逗号,不是括号**。`t = 1,` 不加括号也是 tuple。

### 何时用 tuple 而非 list?

- 不可变 → 可作 dict 的**键**(list 不行):`{(2026, 8): "月度报表"}`
- 固定结构(坐标、RGB、日期范围)
- 想了解「带字段名的 tuple」→ `namedtuple` ≈ Java `record`,Ch08 详讲;更常用的 `@dataclass` 在 Ch05。

> ✅ **做 `price_range` 题**:列表推导取所有 price → `return min(prices), max(prices)`。测试会验 `isinstance(..., tuple)`。

---

## §2.3 dict:读取、遍历与字典推导式(对应:`build_price_map`)🟡

### 创建 🟢

```python
d = {"机械键盘": 599.0, "无线鼠标": 159.0}   # 字面量
d = dict(a=1, b=2)                            # 关键字构造 → {"a": 1, "b": 2}
d = {}                                        # ⚠️ 这是空 dict,不是空 set!
empty = set()                                 # 空集合只能这样写(§2.5 细说)
```

### 读取:`d[k]` vs `d.get(k, default)` 🟡(本章高频坑)

```java
map.get("color");                 // null —— 安安静静返回 null
```

```python
p = {"name": "机械键盘", "price": 599.0}
p["price"]              # 599.0
p["color"]              # ❌ KeyError —— 直接抛异常,比 Java 严格!
p.get("color")          # None     —— 不抛,≈ Java Map.get
p.get("color", "黑色")  # "黑色"   —— 带默认值,≈ getOrDefault
```

❌ 错误写法 → ✅ 正确写法(真实场景:商品 JSON 有些字段可能缺):

```python
tag = p["tag"]                        # ❌ 上游数据缺 tag 字段就炸 KeyError
tag = p.get("tag", "无标签")          # ✅ 缺字段走默认
```

**什么时候用哪个**:字段**按契约必须存在**用 `d[k]`(缺了是 bug,该炸就炸);字段**可有可无**用 `d.get(k, default)`。

### 成员判断与遍历 🟢

```python
"price" in p            # True   ≈ containsKey,O(1)
for k in p:             # 默认遍历键
for v in p.values():    # 遍历值
for k, v in p.items():  # 遍历键值对 ≈ Java entrySet(),最常用
```

### 字典推导式 🔴(Java stream toMap 的优雅版)

真实场景:商品价格速查表——前端拿到 name 就要 O(1) 查出 price:

```java
Map<String, Double> priceMap = products.stream()
    .collect(Collectors.toMap(Product::getName, Product::getPrice));
```

```python
price_map = {p["name"]: p["price"] for p in products}
price_map["机械键盘"]     # 599.0

# 带条件:只要千元以上商品
{ p["name"]: p["price"] for p in products if p["price"] >= 1000 }
# {"降噪耳机": 1299.0, "27寸4K显示器": 2199.0, "人体工学椅": 1599.0}
```

骨架:`{键表达式: 值表达式 for 变量 in 可迭代对象 if 条件}`——和列表推导式(Ch01)同构,只换外层 `{}` 和 `键: 值`。

### 坑:键重复时**后写的赢** 🟡

```python
{"a": 1, "a": 2}        # {"a": 2}   后值覆盖前值,不报错!
```

推导式同理:两个商品重名时,后出现的覆盖先出现的。测试里有这条用例。

### 增删速查 🟢

```python
d["c"] = 3              # put
del d["a"]              # remove(不存在则 KeyError)
d.pop("a")              # remove 并返回值
d.pop("z", None)        # 安全删除
```

> ✅ **做 `build_price_map` 题**:一行字典推导 `{p["name"]: p["price"] for p in products}`。

---

## §2.4 dict 分组与聚合:setdefault / defaultdict(对应:`group_by_category`、`category_inventory_value`)🟡

分组聚合是后端最高频的 dict 用法:**按某个字段把记录归堆,再在堆上算总数**。

### Java 对照:computeIfAbsent

```java
Map<String, List<Product>> groups = new HashMap<>();
for (Product p : products) {
    groups.computeIfAbsent(p.getCategory(), k -> new ArrayList<>()).add(p);
}
```

### Python 写法 1:setdefault

```python
groups = {}
for p in products:
    groups.setdefault(p["category"], []).append(p)
    # 语义:键不存在就先放入默认值 [],返回该值;存在就直接返回已有值
```

❌ 错误写法 → ✅ 正确写法:

```python
groups = {}
for p in products:
    groups[p["category"]].append(p)        # ❌ 普通 dict 首次访问必 KeyError

for p in products:
    groups.setdefault(p["category"], []).append(p)   # ✅
```

### Python 写法 2:defaultdict(更优雅)

```python
from collections import defaultdict

groups = defaultdict(list)     # 缺键时自动调 list() 造默认值
for p in products:
    groups[p["category"]].append(p)        # ✅ 不用 setdefault,直接 append
```

> 🟡 `defaultdict(list)` 的参数是「默认值**工厂**」:缺键时调用它造默认值。`defaultdict(float)` 缺键就是 `0.0`——**聚合求和神器**。Ch08 会把它和 `Counter` 一起讲透。

### 真实场景 1:按类目分组(group_by_category 原型)

```python
groups = {}
for p in products:
    groups.setdefault(p["category"], []).append(p)

set(groups.keys())      # {"电脑外设", "图书", "影音设备", "生活用品"}
len(groups["电脑外设"])  # 4(键盘/鼠标/显示器/扩展坞)
```

### 真实场景 2:每类库存货值(category_inventory_value 原型)

财务要看每个类目压在库存里的钱:Σ(单价 × 库存)。这就是「分组 + 累加」:

```python
value = defaultdict(float)          # 缺键自动 0.0
for p in products:
    value[p["category"]] += p["price"] * p["stock"]

value["电脑外设"]     # 277715.0 = 599*120 + 159*300 + 2199*45 + 269*220
value["生活用品"]     # 47970.0  = 199*0(水杯缺货) + 1599*30(工学椅)
```

等价的 Java:

```java
Map<String, Double> value = new HashMap<>();
for (Product p : products) {
    value.merge(p.getCategory(), p.getPrice() * p.getStock(), Double::sum);
}
```

> ⚠️ defaultdict 是 dict 的子类,直接返回也没问题;作业里 `return dict(value)` 转成普通 dict,是为了不让调用方再触发「自动造键」的副作用。

> ✅ **做 `group_by_category` 题**:空 dict + `setdefault` 循环。
> ✅ **做 `category_inventory_value` 题**:`defaultdict(float)` + `+=` 累加,最后 `dict(...)`。

---

## §2.5 set:去重与集合运算(对应:`all_categories`)🔴

### 创建与去重 🟡

```python
s = {1, 2, 3}                       # 字面量
s = set([1, 2, 2, 3])               # 从 list 去重 → {1, 2, 3}
s = set()                           # 空集合只能这样!
e = {}                              # ❌ 这是空 dict,不是空 set(坑)
```

❌ 错误写法 → ✅ 正确写法:

```python
seen = {}              # ❌ 想当 set 用,结果 add 方法都没有
seen.add(1)            # AttributeError
seen = set()           # ✅
seen.add(1)            # ✅
```

### 集合推导式:和列表推导式同构 🔴

真实场景:运营后台的类目筛选项,要从所有商品里抽出 category 并去重:

```python
cats = {p["category"] for p in products}
# {"电脑外设", "图书", "影音设备", "生活用品"} —— 10 个商品自动去重成 4 个
```

骨架:`{表达式 for 变量 in 可迭代对象}`——换 `{}` 就自动去重。这正是 `all_categories` 作业。

### 去重的坑:set 不保序 🟡

```python
names = ["b", "a", "b", "c"]
list(set(names))       # 去重了,但顺序可能乱(set 无序)
```

要「去重且保序」,Ch08 教你 `dict.fromkeys` 技巧;本章作业对顺序无要求。

### 集合运算 🔴(Java 写起来又啰嗦又有副作用)

```java
Set<String> a = new HashSet<>(Set.of("KB-001", "MS-002", "CP-009"));
Set<String> b = new HashSet<>(Set.of("CP-009"));
a.retainAll(b);   // 交集 —— 但 a 被改掉了!想保留 a 得先 copy
```

```python
a = {1, 2, 3}
b = {2, 3, 4}
a | b     # 并集 {1, 2, 3, 4}    ≈ addAll,但返回新集合,不改原集合
a & b     # 交集 {2, 3}          ≈ retainAll,但无副作用
a - b     # 差集 {1}             ≈ removeAll,但无副作用
a ^ b     # 对称差 {1, 4}        (Java 没有直接对应)
a <= b    # 子集判断             ≈ containsAll
```

真实场景:找**缺货 SKU** = 全部 SKU − 有货 SKU:

```python
all_skus = {p["sku"] for p in products}
in_stock = {p["sku"] for p in products if p["stock"] > 0}
all_skus - in_stock        # {"CP-009"} —— 智能水杯,一行差集搞定
```

### 增删速查 🟢

```python
s.add(4)          # 加
s.discard(4)      # 删,不存在也不报错(安全,推荐)
s.remove(4)       # 删,不存在抛 KeyError
s.update([5, 6])  # 批量加 ≈ addAll
```

> 了解:`frozenset` 是不可变 set,可哈希 → 能当 dict 的键。本章作业用不到,知道有它即可。

> ✅ **做 `all_categories` 题**:一行集合推导式。

---

## §2.6 min/max + key:最值问题(对应:`find_cheapest_per_category`)🟡

### Java 对照:Stream min

```java
Product cheapest = products.stream()
    .min(Comparator.comparing(Product::getPrice))
    .orElseThrow();
```

```python
cheapest = min(products, key=lambda p: p["price"])
cheapest["name"]     # "设计模式"(75.5)
```

> 🟢 `min`/`max` 加 `key=` 后,返回的是**整个元素**(这里是一个商品 dict),不是那个最小值本身。这点和 Java 的 `Optional<Product>` 一致。

### 坑:并列最小,返回**先出现的**那个 🟡

```python
items = [{"name": "A", "price": 100}, {"name": "B", "price": 100}]
min(items, key=lambda x: x["price"])["name"]   # "A" —— 不是 B
```

`min` 从左往右扫描,遇到**严格更小**才替换,所以并列时保留先出现的。测试有专门用例。

### 组合:每类引流款(find_cheapest_per_category 原型)

运营要找每个类目的「引流款」(最便宜的商品)。**复用** §2.4 的分组函数:

```python
def find_cheapest_per_category(products):
    result = {}
    for cat, ps in group_by_category(products).items():   # 复用!
        cheapest = min(ps, key=lambda p: p["price"])      # 组内找最值
        result[cat] = cheapest["name"]
    return result

# {"电脑外设": "无线鼠标", "图书": "设计模式", "影音设备": "蓝牙音箱", "生活用品": "智能水杯"}
```

读法:分组 → 每组 `min(key=...)` → 取名字。三步全是前几节的东西——**这就是「综合题」的样子:没有新知识,全是组合**。

> ✅ **做 `find_cheapest_per_category` 题**:复用你的 `group_by_category`,别重写分组逻辑。

---

## §2.7 ⚠️ 可变默认参数陷阱 + 组合过滤(对应:`filter_products`)🔴

本章最重要的一个坑,**Java 没有,Java 老手必踩**。

### Bug 演示

```python
def add_tag(product, tags=[]):     # ❌ 危险!默认参数是个可变 list
    tags.append(product["name"])
    return tags

add_tag({"name": "机械键盘"})    # ["机械键盘"]
add_tag({"name": "无线鼠标"})    # ["机械键盘", "无线鼠标"]  ← !!!上次的还在!
```

**为什么**:Python 的默认参数值在**函数定义时只求值一次**,那个 list 对象被所有调用**共享**。Java 根本没有「默认参数」这个语法,所以你没有这方面的直觉。

> 🔑 口诀:**默认参数只用不可变对象**(`None` / `int` / `str` / `tuple`);需要可变的,就在函数体内现造。

### ✅ 正确写法:None 哨兵

```python
def add_tag(product, tags=None):
    if tags is None:       # 判 None 用 is(Ch01 §1.10 坑 2)
        tags = []          # 每次调用新建,互不共享
    tags.append(product["name"])
    return tags

add_tag({"name": "机械键盘"})   # ["机械键盘"]
add_tag({"name": "无线鼠标"})   # ["无线鼠标"]  ✅
```

### 组合过滤:filter_products 原型

真实场景:后台商品列表页的筛选器——价格下限、类目、只看有货,三个条件**都是可选的、可叠加**:

```python
def filter_products(products, min_price=None, category=None, in_stock_only=False):
    result = products
    if min_price is not None:                            # 注意:is not None
        result = [p for p in result if p["price"] >= min_price]
    if category is not None:
        result = [p for p in result if p["category"] == category]
    if in_stock_only:                                    # bool 直接当条件
        result = [p for p in result if p["stock"] > 0]
    return sorted(result, key=lambda p: p["price"])      # 升序返回新列表
```

两个细节都埋着考点:

1. **判可选参数用 `is not None`,不要用 truthiness**:`if min_price:` 会把 `min_price=0` 也当没传(0 是 falsy,Ch01 §1.4 的坑)。
2. **`sorted` 返回新列表**,不改传入的 `products`——§2.1 的副作用原则,测试会查。

```python
filter_products(products, min_price=1000)
# [降噪耳机(1299), 人体工学椅(1599), 27寸4K显示器(2199)]  升序
filter_products(products, category="图书")
# [设计模式(75.5), Python编程:从入门到实践(89)]
filter_products(products, in_stock_only=True)     # 9 个,排除缺货的智能水杯
```

> ✅ **做 `filter_products` 题**:三段可选过滤 + 最后 `sorted`。默认值照抄签名里的 `None` / `False`,**别手贱改成 `[]`**。

---

## §2.8 选择指南(速查)

| 需求 | 用什么 |
|------|--------|
| 有序、可变、可重复 | `list` |
| 取子序列 / 前 N 名 / 反转 | 切片 `a[1:3]` `a[:n]` `a[::-1]` |
| 排序(不改原列表) | `sorted(x, key=..., reverse=...)` |
| 固定结构、多返回值、当字典键 | `tuple` |
| 键值映射 | `dict` |
| 分组(键→列表) | `setdefault` / `defaultdict(list)` |
| 聚合(键→累加值) | `defaultdict(float)` |
| 去重、交并差集 | `set` + `&` `\|` `-` |
| 找最值元素 | `min(xs, key=...)` |
| 可选的可变参数 | 默认值写 `None`,函数体内现造 |

---

## 📝 本章作业(8 个函数,全部围绕 products.json)

打开 **`ch02_assignment.py`**,你在给电商后台写「商品数据中台」:

| 函数 | 场景 | 难度 |
|------|------|------|
| `get_top_products_by_price` | 热销榜 Top N | 🟢 |
| `price_range` | 价格区间展示「¥75.5 起」 | 🟢 |
| `build_price_map` | 前端价格速查表 | 🟢 |
| `group_by_category` | 类目管理页分组 | 🟡 |
| `category_inventory_value` | 财务看每类库存货值 | 🟡 |
| `all_categories` | 筛选项的类目列表 | 🟢 |
| `find_cheapest_per_category` | 每类引流款分析 | 🟡 |
| `filter_products` | 商品列表页组合筛选器 | 🟡 |

**完成方式**:

```bash
uv run pytest 01_python_core/ch02/test_ch02_assignment.py -v
```

全绿 = 你掌握了 Ch02。**哪题卡住 → 回对应 § 查**(见顶部对应表)。

---

## ✅ 自测

- [ ] 能闭眼写出:反转 `a[::-1]`、前 N 名 `sorted(...)[:n]`
- [ ] 说清 `sorted()` 和 `.sort()` 的区别,以及为什么函数里该用前者
- [ ] 知道 `d[k]` 不存在抛 `KeyError`,`d.get(k, default)` 返回默认值
- [ ] 能默写分组套路 `groups.setdefault(k, []).append(x)`
- [ ] 能默写三个集合运算符号 `&` `|` `-`,且知道它们不改原集合
- [ ] 能解释为什么 `def f(x=[])` 是 bug,以及 None 哨兵修法
- [ ] 8 个作业全绿

---

## 🎓 费曼挑战(直觉 · Ultralearning 原则八)

> 用大白话讲给「Java 同事」听。**讲不清 = 没懂**,回去重读对应小节。

任选一题,讲清楚:
1. 「`def f(x=[])` 为什么是 bug?根源在默认参数的求值时机是什么?」— 卡壳重读 §2.7
2. 「Python `dict` 从 3.7 起保证插入有序,相当于 Java 的哪个类?为什么 `HashMap` 不是正确答案?」— 卡壳重读 §2.3 + 速查表
3. 「`sorted` 和 `.sort()` 都能排序,为什么给别人用的函数里用 `.sort()` 是事故?」— 卡壳重读 §2.1

✅ 自检:不查资料能说清「为什么默认值只创建一次、且被所有调用共享」吗?

## 🧠 记忆闪卡(⑤ · 原则七)

→ 本章闪卡在 [`review.md`](./review.md)。学完标复习日期(1/3/7 天)。
> 每天开学习前,先翻根 [`REVIEW.md`](../../REVIEW.md) 的「今日复习」总览。

---

## ⏭️ 下一步

Ch02 掌握后,进 **Ch03 · 控制流、迭代器、生成器、推导式**——本章的推导式只是热身,Ch03 把 `for-else`、生成器 `yield`、迭代器协议讲透,并用生成器流式处理「GB 级大日志文件」。
