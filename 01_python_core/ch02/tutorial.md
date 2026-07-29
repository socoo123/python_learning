# Ch02 · 数据结构:list / tuple / dict / set

> **预计**:1 天 ｜ **前置**:Ch01
> **目标**:掌握 Python 四大内置容器,精确对应 Java 的 `ArrayList` / 不可变 List / `HashMap` / `HashSet`,并学会 **Pythonic** 用法(切片、推导式、集合运算)。
> 这章是你举的「商品数据解析」例子的主场——所有作业都围绕 `products.json` 展开。

---

## 🗺️ 本章地图(元学习 · 原则一)

学完这章,你将能够:
- 四大容器(list/tuple/dict/set)分别对应 Java 的什么,行为有何差异
- 用**切片**(Java 完全没有)和**推导式**写出 Pythonic 代码
- 用 `dict.get()` / `defaultdict` / `setdefault`(对比 Java `getOrDefault`/`computeIfAbsent`)
- 用 `set` 做集合运算(交并差,对比 Java `retainAll`/`addAll`)
- 避开 **可变默认参数陷阱**(面试必考 + 实战高频 bug)

**本章主线:四大容器 + 一个经典坑**,全部围绕 `products.json` 商品数据实战。

---

## ⏱️ 学习路径:费曼五步(约 40-60 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(30秒) | 下面 5 个 Java 操作,猜 Python 怎么写 | 本页 ① |
| ② 先动手 | 打开 `ch02_assignment.py`,**先试着写**(别看教程) | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清"可变默认参数为何是 bug""dict 为何有序" | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性**:别通读!先猜 ① → 去 ② 写作业 → 卡住才回 📖 教程正文。

---

## ① 预览猜(30 秒 · 用 Java 经验猜 Python)

先别看答案,猜一猜(猜错记得更牢):
1. Java 取 list 第 2~3 个元素:`list.subList(1,3)`。Python 一行怎么写?
2. Java 方法要返回「最低价、最高价」两个值,得造个 Pair/类。Python 怎么返回?
3. Java `map.get("x")` 不存在返回 null。Python `d["x"]` 不存在会怎样?
4. Java 求两个 Set 交集要 `a.retainAll(b)`。Python 一个符号是什么?
5. `def add_tag(item, tags=[])` 这个 Python 函数,连续调用两次会有什么诡异现象?

> 猜完带着验证心态进入下面的速查表和 §2.1。

---

## 速查:四大容器 vs Java

| Python | Java 对应 | 可变? | 有序? | 典型用途 |
|--------|-----------|--------|--------|----------|
| `list` | `ArrayList` | ✅ | ✅(插入序) | 有序集合、栈/队列 |
| `tuple` | 不可变 `List` / `record` | ❌ | ✅ | 多返回值、固定结构、字典键 |
| `dict` | `LinkedHashMap`(3.7+) | ✅ | ✅(插入序) | 键值映射 |
| `set` | `HashSet` | ✅ | ❌ | 去重、集合运算 |
| `frozenset` | 不可变 `Set` | ❌ | ❌ | 可哈希,能当字典键 |

> 🟡 **注意**:Python `dict` 从 3.7 起**保证插入有序**(= Java `LinkedHashMap`),不是 `HashMap` 那种无序。这是和 Java 的一个重要差异。

---

## §2.1 list —— 对比 ArrayList

### 创建 🟢
```python
xs = [1, 2, 3]              # 字面量
xs = list((1, 2, 3))        # 从可迭代对象
xs = [0] * 5                # [0,0,0,0,0]  (Java: Collections.nCopies)
xs = [i for i in range(5)]  # 列表推导式 → [0,1,2,3,4]  (Ch03 详讲)
```

### 索引与切片 🔴(Java 没有,重点)
Java 取子串要 `subList`/循环,Python 用**切片**一行搞定:

```python
a = [10, 20, 30, 40, 50]
a[0]        # 10      正向索引
a[-1]       # 50      负索引(从末尾),Java 没有
a[1:3]      # [20,30] 切片 [起:止) 左闭右开
a[:2]       # [10,20] 省略开头
a[2:]       # [30,40,50] 省略结尾
a[::2]      # [10,30,50] 步长 2
a[::-1]     # [50,40,30,20,10] 反转!经典技巧
```
> 切片同样适用于字符串、tuple —— 「序列」协议统一。

### 常用方法(对比 ArrayList)🟢
```python
a.append(x)      # add()
a.extend([x,y])  # addAll()
a.insert(0, x)   # add(0, x)
a.remove(x)      # 删第一个等于 x 的元素(不是按索引!)
a.pop()          # 删并返回末尾; a.pop(0) = pollFirst
a.index(x)       # indexOf()
a.count(x)       # Collections.frequency
a.sort()         # 就地排序(对比 Collections.sort)
a.reverse()      # 就地反转
len(a)           # a.size()  —— 注意是函数不是方法
```

### `sorted()` vs `.sort()` 🟡
```python
a = [3, 1, 2]
b = sorted(a)         # 返回新列表,a 不变(对比 stream sorted)
a.sort()              # 就地修改 a,返回 None
# 带 key(对比 Comparator.comparing):
sorted(products, key=lambda p: p["price"])              # 升序
sorted(products, key=lambda p: p["price"], reverse=True)# 降序
```

> ⚠️ Java 老手常犯:`a.sort()` 返回 `None`,别写 `b = a.sort()`。

### 💡 关键前置:lambda 表达式(sorted / min / max 的 key 都靠它)🔴

本章多个作业(sorted、min、max)都要传一个 `key=...` 参数,里面用的是 **lambda**(匿名函数)。Java 也有 lambda,几乎一一对应:

```python
# Python lambda:   lambda 参数: 表达式
sorted(products, key=lambda p: p["price"])           # 按价格升序
min(products, key=lambda p: p["price"])              # 最便宜的那个商品(dict)
max(products, key=lambda p: p["price"])              # 最贵的那个商品(dict)
sorted(products, key=lambda p: p["price"], reverse=True)  # 降序
```
```java
// Java 等价(对比一下,几乎一样):
products.stream()
    .min(Comparator.comparing(p -> p.getPrice()))
    .get();
```

> 🟡 **和 Java lambda 的区别**:Python lambda 只能写**单个表达式**(不能写语句/不能多行),返回该表达式的值。复杂逻辑请用 `def` 定义具名函数。
> 本章记住一句话:`key=lambda p: p["price"]` =「按 p 的 price 字段比较」。

### 列表推导式(基础 + 带条件)🔴

本章 `filter_products`、`get_top_products_by_price` 都要用列表推导式。基础(取字段)在 Ch01 §1.6 讲过,这里补**带条件过滤**的形式——这是本章必会的:

```python
[p for p in products]                              # 全部(Ch01 已讲)
[p for p in products if p["price"] >= 1000]        # ✨ 带过滤:只留贵的
[p["name"] for p in products if p["stock"] > 0]    # 过滤 + 取字段
```

骨架:`[表达式 for 变量 in 可迭代对象 if 条件]`。等价的传统写法:
```python
result = []
for p in products:
    if p["price"] >= 1000:       # 同一个 if 条件
        result.append(p)          # 同一个表达式
```

> 推导式同样适用于 dict(§2.3 `{k:v for ...}`)和 set(§2.4 `{x for ...}`),语法一致,只换外层括号。

---

## §2.2 tuple —— 对比不可变 List / record

tuple 是**不可变**序列。两个核心用途:**多返回值** 和 **固定结构记录**。

### 解包(Java 老手会爱)🟡
```python
point = (3, 4)
x, y = point             # 解包(Java 要 point.x()/point.y())
a, b = 1, 2
a, b = b, a              # 交换(Ch01 见过)

# 星号解包(Java 没有)
first, *rest = [1, 2, 3, 4]   # first=1, rest=[2,3,4]
head, *mid, tail = [1,2,3,4]  # head=1, mid=[2,3], tail=4
```

### 多返回值 🟢
```python
def price_range(products):
    prices = [p["price"] for p in products]
    return min(prices), max(prices)   # 看似返回两个值,实际是一个 tuple

low, high = price_range(products)     # 调用方解包
```
> = Java 里要返回 `Pair<Double,Double>` 或自定义类,Python 直接 `return a, b`。

### namedtuple —— 对比 Java record 🟡
```python
from collections import namedtuple
# Java:  record Point(int x, int y) {}
Point = namedtuple("Point", ["x", "y"])
p = Point(3, 4)
p.x, p.y          # 按名字访问,比 p[0] 可读
```
> Ch08 会讲更现代的 `typing.NamedTuple` 和 `dataclass`。

### 何时用 tuple 而非 list?
- 不可变 → 可作 dict 的**键**(list 不行)
- 表示固定结构(坐标、RGB)
- 微小性能优势

---

## §2.3 dict —— 对比 LinkedHashMap

### 创建 🟢
```python
d = {"a": 1, "b": 2}
d = dict(a=1, b=2)
d = {}                       # 注意!空 dict,不是空 set
empty_set = set()            # 空集合必须用 set()
```

### 读取:`d[k]` vs `d.get(k, default)` 🟡
```python
d = {"a": 1}
d["a"]              # 1
d["z"]              # ❌ KeyError(Java: get 返回 null)
d.get("z")          # None   —— 不抛异常(Java: getOrDefault)
d.get("z", 0)       # 0      —— 带默认值
```
> 🟡 差异:Java `Map.get` 不存在返回 `null`;Python `d[k]` 不存在**抛 `KeyError`**。要安全取值用 `.get()`。

### 增删改 🟢
```python
d["c"] = 3          # put
del d["a"]          # remove(不存在则 KeyError)
d.pop("a")          # remove 并返回值
d.pop("z", None)    # 安全删除(不存在返回 None)
"a" in d            # containsKey  (O(1))
```

### 遍历 🟡
```python
for k in d:                  # 默认遍历键
for k in d.keys():           # 显式遍历键
for v in d.values():         # 遍历值
for k, v in d.items():       # 遍历键值对(= Java entrySet,最常用)
```

### 字典推导式 🔴(Java stream toMap 的优雅版)
```python
# name -> price 映射
price_map = {p["name"]: p["price"] for p in products}

# 等价 Java:
# products.stream().collect(Collectors.toMap(P::getName, P::getPrice))

# 带条件
expensive = {p["name"]: p["price"] for p in products if p["price"] > 500}
```

### `setdefault` / `defaultdict`(分组神器)🟡
分组是高频场景,Java 要 `computeIfAbsent`,Python 有两种写法:

```python
# 写法 1:setdefault
groups = {}
for p in products:
    groups.setdefault(p["category"], []).append(p)
    # 意思:键不存在时先设为 [],再 append

# 写法 2:defaultdict(Ch08 详讲,更优雅)
from collections import defaultdict
groups = defaultdict(list)   # 默认值工厂 = list
for p in products:
    groups[p["category"]].append(p)  # 键不存在自动建 []
```

---

## §2.4 set / frozenset —— 对比 HashSet

### 创建 🟡
```python
s = {1, 2, 3}         # 字面量(注意:空集合不能用 {},那是 dict)
s = set([1, 2, 2, 3]) # 从 list 去重 → {1, 2, 3}
s = set()             # 空集合
s = {p["category"] for p in products}   # ✨ 集合推导式:和列表推导式同理,换{}自动去重
```
> `all_categories` 作业就用最后一行:从所有商品里抽出 category,`{}` 自动去重成 set。

### 去重(最常见用途)🟢
```python
names = ["a", "b", "a", "c"]
unique = list(set(names))   # 去重 O(n)(对比 Java new ArrayList(new HashSet))
# 注意:set 无序,去重后顺序可能变。要保序见 Ch08 dict.fromkeys 技巧
```

### 集合运算 🔴(Java 写起来很啰嗦,Python 用符号)
```python
a = {1, 2, 3}
b = {2, 3, 4}

a | b    # 并集 {1,2,3,4}      (Java: union,要 addAll)
a & b    # 交集 {2,3}          (Java: retainAll)
a - b    # 差集 {1}            (Java: removeAll)
a ^ b    # 对称差 {1,4}        (Java: 没有直接对应)
a <= b   # 子集判断            (Java: containsAll)
2 in a   # 成员判断 O(1)       (Java: contains)
```
> 🟢 记忆:就当集合是数学符号,`|` & `-` `^` 和数学一致。

### 方法 vs 运算符 🟡
```python
a.add(4)          # add
a.remove(4)       # 不存在抛 KeyError
a.discard(4)      # 不存在不报错(更安全)
a.update([5, 6])  # addAll
```

### frozenset
不可变 set,可哈希 → 能当 dict 的键或放进另一个 set。普通 set 不行。

---

## §2.5 ⚠️ 可变默认参数陷阱(本章最重要的一个坑)

🟡 Python 函数的**默认参数在函数定义时只求值一次**,不是每次调用新建。如果默认值是**可变对象**(list/dict/set),所有调用**共享同一个对象**——这是经典 bug。

### Bug 演示
```python
def add_item(item, basket=[]):   # ❌ 危险!
    basket.append(item)
    return basket

print(add_item("苹果"))   # ['苹果']
print(add_item("香蕉"))   # ['苹果', '香蕉']  ← ！！！上次的苹果还在！
```
> Java 没这个坑,因为 Java 不允许 list 作为默认参数值。所以 Java 老手特别容易踩。

### 正确写法:用 `None` 哨兵
```python
def add_item(item, basket=None):   # ✅ 正确
    if basket is None:
        basket = []                # 每次调用新建
    basket.append(item)
    return basket

print(add_item("苹果"))   # ['苹果']
print(add_item("香蕉"))   # ['香蕉']  ← 正确
```

> 🔑 **口诀**:默认参数永远用不可变对象(`None`/`int`/`str`/`tuple`),需要可变就在函数体内创建。你会在 `filter_products()` 作业里实践这个规范。

---

## §2.6 选择指南

| 需求 | 用什么 |
|------|--------|
| 有序、可变、可重复 | `list` |
| 固定结构、多返回值、要当字典键 | `tuple` |
| 键值映射 | `dict` |
| 去重、集合运算 | `set` |
| 键值映射 + 默认值工厂 | `defaultdict` |
| 计数 | `Counter`(Ch08) |
| 取子序列 | 切片 `a[1:3]` |
| 排序 | `sorted(x, key=...)` |

---

## 📝 本章作业(8 个函数,全用 products.json)

打开 **`ch02_assignment.py`**,8 个函数围绕商品数据处理:

| 函数 | 数据结构 | 难度 | 说明 |
|------|----------|------|------|
| `get_top_products_by_price` | list + 切片 + 排序 | 🟢 | 价格前 N 的商品名 |
| `price_range` | tuple | 🟢 | (最低价, 最高价) |
| `build_price_map` | dict 推导 | 🟢 | name → price |
| `group_by_category` | dict + setdefault | 🟡 | 按类目分组 |
| `category_inventory_value` | defaultdict | 🟡 | 每类库存货值 Σ(price×stock) |
| `all_categories` | set 推导 | 🟢 | 所有类目(去重) |
| `find_cheapest_per_category` | 综合 | 🟡 | 每类最便宜的商品名 |
| `filter_products` | 综合 + 可变默认参数 | 🟡 | 过滤+排序(你举的例子) |

**完成方式**:
```bash
pytest 01_python_core/ch02/test_ch02_assignment.py -v
```
全绿 = 你掌握了 Ch02。

---

## ✅ 自测

- [ ] 能闭眼写出切片反转 `a[::-1]`
- [ ] 知道 `d[k]` 不存在会抛 `KeyError`,而 `d.get(k)` 返回 `None`
- [ ] 会用 `dict.items()` 遍历键值对
- [ ] 能解释为什么 `def f(x=[])` 是 bug
- [ ] 8 个作业全绿

---

## 🎓 费曼挑战(直觉 · Ultralearning 原则八)

> 用大白话讲给「Java 同事」听。**讲不清 = 没懂**,回去重读。

任选一题,讲清楚:
1. 「`def f(x=[])` 为什么是 bug?怎么修?」— 卡壳重读 §2.5(本章最重要的坑)
2. 「Python `dict` 从 3.7 起保证插入有序,相当于 Java 的哪个类?为什么重要?」— 卡壳重读 §2.3

✅ 自检:能说清「为什么默认值只创建一次、且被所有调用共享」吗?

## 🧠 记忆闪卡(⑤ · 原则七)

→ 本章闪卡在 [`review.md`](./review.md)。学完标复习日期(1/3/7 天)。
> 每天开学习前,先翻根 [`REVIEW.md`](../../REVIEW.md) 的「今日复习」总览。

---

## ⏭️ 下一步

Ch02 掌握后,进 **Ch03 · 控制流、迭代器、生成器、推导式**——把列表/字典推导式、`for-else`、生成器 `yield` 这些 Python 效率利器一次性讲透,并用生成器流式处理「大日志文件」。
