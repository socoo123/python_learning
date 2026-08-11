# Ch09 · itertools + functools:函数式利器

> **预计**:0.5 天 ｜ **前置**:Ch08 ｜ **M2 第二章**
> **目标**:掌握 Python 函数式编程两大支柱——`itertools`(迭代器组合,对比 Java Stream 但更强大)和 `functools`(`reduce` / `lru_cache` / `partial`)。数据处理、刷题、写服务缓存都高频。
> 本章主线:你是电商平台的数据分析师,**大促前**要基于 `assets/mock_data/products.json`(10 个商品)做一轮盘点:合并多仓到货批次 → 按类目分组 → 生成搭配套餐候选 → 排促销定价矩阵 → 算库存总值 → 从实时事件流取样 → 给商品查询接口加缓存 → 做折扣定价器 → 输出类目盘点报告。

> 📐 **本教程的契约**:下面每一节(§9.1–§9.9)都**精确对应**作业里的一个任务。讲过的才考,考的必讲过。卡住时,按对应表回查小节。

---

## 🗺️ 本章地图(元学习 · 原则一)

读完这章 + 完成作业,你将能够:
- 用 `chain` 把多个可迭代对象串成一条流(= Java `Stream.concat`,但不限个数、更省内存)
- 用 `groupby` 分组,并说清为什么**必须先排序**(它和 `defaultdict` 分组的取舍)
- 用 `combinations` / `product` 一行生成组合与笛卡尔积(Java 要手写循环)
- 用 `reduce` 做累积运算(= Java `stream.reduce`),并说清什么时候**不该**用它
- 用 `islice` 从**可能是无限的**迭代器里安全取前 n 个(迭代器不能 `[:n]`!)
- 用 `@lru_cache` 一行给函数加记忆化(= Java 手写 Map 缓存 / Guava),用 `cache_info()` 验证命中
- 用 `partial` 固定参数生成新函数(= 柯里化替代,Ch04 闭包的简化版)

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业题 | 对应小节 | 核心知识点 |
|--------|----------|-----------|
| `merge_batches` | §9.1 | itertools.chain 多路合并 |
| `group_by_category` | §9.2 | itertools.groupby(先排序) |
| `bundle_pairs` | §9.3 | itertools.combinations |
| `promo_matrix` | §9.4 | itertools.product 笛卡尔积 |
| `inventory_value` | §9.5 | functools.reduce 累积 |
| `take_first` | §9.6 | itertools.islice 惰性切片 |
| `query_product` | §9.7 | functools.lru_cache 记忆化 |
| `make_discounter` | §9.8 | functools.partial 偏函数 |
| `category_report` | §9.9 | 综合:分组 + 累积出报告 |

---

## ⏱️ 学习路径:费曼五步(约 45-60 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 下面 5 个 Java 场景,猜 Python 怎么写 | 本页 ① |
| ② 先动手 | 打开 `ch09_assignment.py`,**先试着写**(别看教程) | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清「groupby 为何先排序」「lru_cache 怎么提速」 | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性原则**:别通读!先猜 ① → 去 ② 写作业 → **哪题卡了,回对应 § 查** → 改 → 再跑。

---

## ① 预览猜(2 分钟 · 激活你的 Java 直觉)

先别看答案,凭 Java 经验猜一猜(猜错记得更牢):
1. Java 拼两个 Stream 用 `Stream.concat(a, b)`,拼三个就得套娃。Python 拼任意多个可迭代对象的函数叫?
2. Java 分组用 `Collectors.groupingBy`,收完再分、自动正确。Python 的 `groupby` 是流式的,用之前必须先做一件事,是什么?
3. 10 个商品生成所有「两两搭配」,Java 写双重 for 循环。Python 标准库哪个函数一行搞定?
4. Java 给递归斐波那契加速要手写 `Map` 缓存(或 Guava)。Python 一个装饰器搞定,叫?
5. 实时事件流是个**无限迭代器**,Python 里 `stream[:100]` 直接报错。想取前 100 条该用什么?

> 猜完,带着验证心态进入正文。第 2 题的「先排序」和第 5 题的「无限流」是本章最容易踩的两个坑。

---

## §9.1 itertools.chain:多路合并(对应:`merge_batches`)🟢

`chain` 把多个可迭代对象首尾相接成**一条惰性流**,像把几节车厢连成一列火车。

### Java 对照最小例

```java
// Java:合并三批到货清单
Stream<Product> all = Stream.concat(batch1.stream(),
                        Stream.concat(batch2.stream(), batch3.stream()));  // 套娃
// 或:Stream.of(batch1, batch2, batch3).flatMap(Collection::stream)
```

```python
# Python:一个 chain,任意多个
from itertools import chain
all_items = chain(batch1, batch2, batch3)
```

### 真实场景例:大促前,三个仓库的到货批次合并处理

```python
from itertools import chain

batch_east  = [{"sku": "KB-001"}, {"sku": "MS-002"}]   # 华东仓
batch_north = [{"sku": "MN-003"}]                       # 华北仓
batch_south = [{"sku": "HP-006"}, {"sku": "SP-007"}]    # 华南仓

merged = list(chain(batch_east, batch_north, batch_south))
[item["sku"] for item in merged]
# ['KB-001', 'MS-002', 'MN-003', 'HP-006', 'SP-007']  ← 按批次顺序首尾相接
```

### chain vs 列表 `+`:省内存 🔴

```python
list1 + list2 + list3        # ❌ 立刻物化,创建 2 个中间列表(数据大时浪费内存)
chain(list1, list2, list3)   # ✅ 惰性:逐个产出,不创建任何中间列表
```

`chain` 产出的是**迭代器**:不调 `list()` 就不消费,可以喂给 `for`、生成器表达式、甚至 `Counter(...)`(Ch08)直接统计。

### 变体:chain.from_iterable

手里是「列表的列表」(而不是散开的一个个列表)时用 `from_iterable`,不用打星号:

```python
batches = [batch_east, batch_north, batch_south]
chain(*batches)                # 打星号解包,可以
chain.from_iterable(batches)   # 等价,更直白(还能接生成器)
```

❌ **错误写法**(Java 思维,循环 extend):

```python
merged = []
for batch in batches:
    merged.extend(batch)      # 能跑,但立刻物化 + 手写循环,没必要
```

✅ **正确写法**:`chain.from_iterable(batches)` 或 `chain(*batches)`。

> 🟡 **Java 对比**:`Stream.concat` 一次只能拼两个,`chain` 拼任意个;`chain(*lists)` 中的 `*` 是 Ch04 学过的「参数解包」——把列表打散成位置参数。

> ✅ 做 `merge_batches` 题:函数签名 `merge_batches(*batches)` 收到的 `batches` 是元组,`chain(*batches)` 或 `chain.from_iterable(batches)` 都行,记得 `list()` 物化返回。

---

## §9.2 itertools.groupby:分组(对应:`group_by_category`)🔴

⚠️ **本章最大的坑**:`groupby` 只合并**相邻**的相同 key,不是全局分组!

```python
from itertools import groupby

# ❌ 不排序直接 groupby:相同的 key 只要不相邻,就会被切成多段
[(k, list(g)) for k, g in groupby([1, 2, 1])]
# [(1, [1]), (2, [2]), (1, [1])]   ← 两个 1 没合并!

# ✅ 先排序,再 groupby
ordered = sorted([1, 2, 1, 3, 2])
{k: list(g) for k, g in groupby(ordered)}
# {1: [1, 1], 2: [2, 2], 3: [3]}   ← 正确合并
```

**为什么这样设计**?`groupby` 是**惰性流式**的——边遍历边产出,不预先把全部数据读进内存。代价是只能看到「当前连续段」。要全局分组,就得先排序让相同 key 变成连续段。

### 标准用法(本节作业)

```python
def group_by_category(products):
    ordered = sorted(products, key=lambda p: p["category"])        # ① 先按 key 排序
    return {k: list(g) for k, g in groupby(ordered, key=lambda p: p["category"])}  # ② 再分组
```

两个细节:
- `groupby(可迭代, key=函数)`:key 函数指定「按什么分组」。**sorted 和 groupby 要用同一个 key 函数**,否则还是乱的。
- `g` 是个**迭代器**,必须 `list(g)` 物化(否则用完即弃,而且外层循环一走它就空了)。

### 真实场景例:按类目分组盘点(products.json 实际结果)

```python
g = group_by_category(products)   # 10 个商品
list(g.keys())        # ['图书', '影音设备', '生活用品', '电脑外设']  ← 排序后分组,key 有序
len(g['电脑外设'])     # 4
[p['sku'] for p in g['图书']]   # ['BK-004', 'BK-005']
sum(len(v) for v in g.values())  # 10  ← 总数校验,一条没丢
```

### groupby vs defaultdict(Ch08):怎么选?🟡

| | `defaultdict(list)` 分组 | `sorted` + `groupby` |
|---|---|---|
| 输入要求 | 任意顺序 | 任意顺序(自己先排) |
| 结果顺序 | 按首次出现 | 按 key 排序 |
| 内存 | 全量驻留 | 排序那一下全量,分组过程流式 |
| 适合 | **日常分组(默认选它)** | 数据已排序(如按时间排好的日志)、需要 key 有序 |

❌ **错误写法**(只 groupby 不排序,数据恰好有序时能蒙对,换个顺序就碎):

```python
{k: list(g) for k, g in groupby(products, key=lambda p: p["category"])}
# products.json 里「电脑外设」被「图书」隔开 → 得到两个「电脑外设」组!
```

✅ **正确写法**:`sorted(...)` + `groupby(...)`,两步缺一不可。

> 🤯 **Java 对比**:Java 的 `Collectors.groupingBy` 是「收完再分」,自动正确;Python 的 `groupby` 是「流式分组」,要手动排序。各有利弊:流式能处理排好序的超大数据(不用全量建 Map)。

> ✅ 做 `group_by_category` 题:照「标准用法」两段式。测试会验返回的是普通 `dict`、key 有序、且**乱序输入也必须正确合并**(防你只写 groupby 不排序)。

---

## §9.3 itertools.combinations:组合(对应:`bundle_pairs`)🟢

运营要做「搭配套餐」:从候选商品里列出所有**两两组合**给人评审。这就是数学里的 C(n, 2)。

### Java 对照最小例

```java
// Java:所有两两组合(不计顺序)
for (int i = 0; i < items.size(); i++)
    for (int j = i + 1; j < items.size(); j++)   // 注意 j = i+1,写错就重复
        pairs.add(List.of(items.get(i), items.get(j)));
```

```python
# Python:一行
from itertools import combinations
pairs = list(combinations(items, 2))
```

### 真实场景例:搭配套餐候选(products.json 前 3 个商品)

```python
names = [p["name"] for p in products[:3]]   # ['机械键盘', '无线鼠标', '27寸4K显示器']
list(combinations(names, 2))
# [('机械键盘', '无线鼠标'), ('机械键盘', '27寸4K显示器'), ('无线鼠标', '27寸4K显示器')]
```

- `combinations(序列, r)`:从 n 个里选 r 个的所有组合,**不计顺序**(选了 a,b 就不会再出 b,a)。
- 组合数 = C(n, r):10 个商品两两搭配 = C(10,2) = **45** 对;不足 r 个时返回空。
- 产出的是元组迭代器,`list()` 物化。

### 兄弟函数:permutations(本章不考,刷题常用)🟡

| 函数 | 含义 | `items=[1,2,3], r=2` |
|------|------|---------------------|
| `combinations(items, r)` | 组合(**不计顺序**) | (1,2), (1,3), (2,3) 共 3 个 |
| `permutations(items, r)` | 排列(**计顺序**) | (1,2), (2,1), (1,3), (3,1), (2,3), (3,2) 共 6 个 |

LeetCode 回溯题(Ch40)会大量遇到这两个。记住:**组合用 combinations,排列用 permutations,别手写回溯重造轮子**。

❌ **错误写法**(手写双重循环,`j = i + 1` 写错就出重复对):

```python
[(a, b) for i, a in enumerate(items) for b in items[i+1:]]   # 能跑,但为什么要自己写?
```

✅ **正确写法**:`list(combinations(items, 2))`,语义明确、不会错。

> ✅ 做 `bundle_pairs` 题:入参是商品 dict 列表,返回 `[("名字A", "名字B"), ...]`——先把商品映射成名字(生成器表达式),再喂给 `combinations(..., 2)`。

---

## §9.4 itertools.product:笛卡尔积(对应:`promo_matrix`)🟡

大促定价:4 个类目 × 3 档折扣,每个组合都要生成一条促销规则——这就是**笛卡尔积**。

### Java 对照最小例

```java
// Java:类目 × 折扣,双重循环
for (String cat : categories)
    for (double d : discounts)
        rules.add(new Rule(cat, d));
```

```python
# Python:一行
from itertools import product
rules = list(product(categories, discounts))
```

### 真实场景例:促销规则矩阵

```python
list(product(["图书", "影音设备"], [0.9, 0.8]))
# [('图书', 0.9), ('图书', 0.8), ('影音设备', 0.9), ('影音设备', 0.8)]
#   ↑ 外层是第一个可迭代对象,内层是第二个——顺序 = 双重 for 的嵌套顺序

len(list(product(['图书','影音设备','生活用品','电脑外设'], [0.95, 0.9, 0.8])))   # 4×3 = 12
```

### 要点

- `product(a, b, ...)`:任意多个可迭代对象的笛卡尔积,产出元组。
- **顺序规则**:右边的可迭代对象跑得最快(= 嵌套 for 的最内层)。
- `product(items, repeat=2)`:`items × items`,等价于 `product(items, items)`。刷题里生成「所有两位组合(可重复)」常用。
- 任一输入为空 → 结果为空(0 乘任何数都是 0)。

❌ **错误认知**:以为顺序是「左边跑最快」——正好相反,`product([A,B],[1,2])` 是 `(A,1),(A,2),(B,1),(B,2)`,**右边**先轮完。

> 🟡 **Java 对比**:Java 没有内置笛卡尔积,嵌套 for 或 `flatMap` 套娃。Python 一行,且是惰性迭代器(大矩阵不炸内存)。

> ✅ 做 `promo_matrix` 题:`list(product(categories, discounts))`。注意参数顺序决定矩阵的行序,测试会验。

---

## §9.5 functools.reduce:累积运算(对应:`inventory_value`)🟡

`reduce(函数, 可迭代, 初始值)` 反复把「函数」作用到累积值和下一个元素上,最终压成一个结果。

### Java 对照最小例

```java
// Java:库存总价值 = Σ price*stock
double total = products.stream()
    .map(p -> p.getPrice() * p.getStock())
    .reduce(0.0, Double::sum);
```

```python
# Python:reduce + operator.add
from functools import reduce
from operator import add
total = reduce(add, (p["price"] * p["stock"] for p in products), 0.0)
```

### 三要素

```python
reduce(mul, [2, 3, 4], 1)    # ((1*2)*3)*4 = 24
```

- **函数**:接 `(累积值, 当前元素)`,返回新累积值。`operator.mul` = `lambda a, b: a * b`。
- **可迭代对象**:通常配一个**生成器表达式**先做一次映射(如上例的 `price*stock`)。
- **初始值**:第三个参数。空可迭代时返回它(`reduce(mul, [], 1)` = 1)。**不传则用第一个元素当初始值,空序列直接 TypeError**——所以「空输入要有合理默认」时务必传。

`operator` 模块提供 `add` / `mul` / `or_` 等运算符的函数形式,省得写 lambda。

### 真实场景例:库存总价值(products.json 实际结果)

```python
reduce(add, (p["price"] * p["stock"] for p in products), 0.0)
# 549055.0   ← 机械键盘 599×120=71880 + 无线鼠标 159×300=47700 + ... 共 10 项
reduce(add, (p["price"] * p["stock"] for p in []), 0.0)
# 0.0   ← 空列表返回初始值,不报错
```

### 可读性忠告:reduce 不是万能胶 🔴

Python 社区**不鼓励**滥用 reduce(Guido 当年想把它移出标准库):

```python
reduce(add, nums, 0)     # 😐 能跑,但 sum(nums) 更直白
reduce(mul, nums, 1)     # 😐 能跑,但 math.prod(nums)(3.8+)更直白
```

**规则**:有现成函数(`sum` / `max` / `min` / `math.prod` / `"".join`)就别用 reduce;reduce 留给「没有现成函数的自定义累积」——比如本章作业里的「price×stock 再求和」、合并多个 dict、流水线式聚合。

> 🟡 **Java 对比**:`reduce(mul, nums, 1)` ≈ `nums.stream().reduce(1, (a,b)->a*b)`。三要素一一对应,Java 老手零障碍——难点只在「什么时候不用它」。

> ✅ 做 `inventory_value` 题:`reduce(add, (生成器表达式), 0.0)`。初始值传 `0.0`,空列表返回 `0.0`。

---

## §9.6 itertools.islice:惰性切片(对应:`take_first`)🟡

实时事件流(消息队列消费、`tail -f` 式的日志流)是个**迭代器**,而且可能**无限长**。问题来了:

```python
stream[:100]       # ❌ TypeError:迭代器没有切片!
list(stream)[:100] # ❌ 无限流:这一行永远跑不完(内存先炸)
```

`islice` 就是「迭代器版的切片」——**惰性**地取前 n 个,取到就停:

### 最小例

```python
from itertools import islice, count

list(islice([10, 20, 30, 40, 50], 3))   # [10, 20, 30]
list(islice(count(1), 3))                # [1, 2, 3]  ← count(1) 是无限计数器,islice 也能安全取样
```

### 真实场景例:从事件流取前 n 条处理

大促当晚监控:订单事件从 MQ 不断涌来(用 `count` 模拟无限流),先取前 3 条看看格式:

```python
events = (f"order-{i}" for i in count(1))   # 无限生成器:order-1, order-2, ...
sample = list(islice(events, 3))
# ['order-1', 'order-2', 'order-3']   ← 取到 3 条就停,不会卡死
```

### 两种调用形式

```python
islice(iterable, n)           # 前 n 个(最常用)
islice(iterable, start, stop) # [start, stop) 区间,如 islice(it, 2, 5) 跳过前 2 取 3 个
```

注意:`islice` 也是迭代器,用完即弃;且**消费掉的元素就没了**(迭代器特性,Ch03)。

❌ **错误写法**(对无限流物化):

```python
[x for x in events][:3]    # 💀 无限循环,你的 pytest 会卡死在这里
```

✅ **正确写法**:`list(islice(events, 3))`。

> 🟡 **Java 对比**:`stream.limit(n)`——Java Stream 天生惰性,limit 自然是流式的。Python 的 list 切片很香,但迭代器世界要用 `islice` 补上这块。**判断标准:手里是 list 用 `[:n]`,是迭代器/生成器用 `islice`**。

> ✅ 做 `take_first` 题:`list(islice(stream, n))`。测试会传一个**真·无限迭代器**——写成 `list(stream)` 或推导式会卡死,只有 islice 能过。

---

## §9.7 functools.lru_cache:记忆化(对应:`query_product`)🔴

大促期间,商品详情查询接口被疯狂调用,**同一个 sku 一秒被查几千次**。查询要扫库(这里用「遍历目录」模拟),太贵——加个缓存:相同入参直接返回上次结果。

`@lru_cache` 一行搞定:**自动缓存「入参 → 返回值」,重复调用命中缓存,不重算**。

### Java 对照最小例

```java
// Java:手写缓存(或引 Guava CacheBuilder / Spring @Cacheable)
private final Map<String, Product> cache = new ConcurrentHashMap<>();
public Product query(String sku) {
    return cache.computeIfAbsent(sku, this::scanCatalog);
}
```

```python
# Python:一个装饰器
from functools import lru_cache

@lru_cache(maxsize=None)      # None = 不限容量;填数字则 LRU 淘汰最久未用
def query_product(sku):
    ...                        # 昂贵的查询逻辑,照常写
```

### 为什么提速这么猛?(经典最小例:递归 fib)

```python
@lru_cache(maxsize=None)
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)

fib(100)   # 秒算。没缓存是 O(2ⁿ),fib(5) 会把 fib(3) 重复算 N 次;
           # 有缓存每个 n 只算一次 → O(n)
```

### 调试工具:cache_info() / cache_clear()

```python
query_product("KB-001")   # 第一次:miss,真查
query_product("KB-001")   # 第二次:hit,直接返回缓存

query_product.cache_info()
# CacheInfo(hits=1, misses=1, maxsize=None, currsize=1)
#                ↑ 命中     ↑ 真算次数(= 不同入参数)

query_product.cache_clear()   # 清空缓存(测试/数据变更时用)
```

### 适用条件(重要!)🔴

lru_cache 只适合**纯函数**(相同输入永远相同输出、无副作用):
- ✅ 数学计算、按 key 查静态表(本节作业)
- ❌ 依赖时间/随机数/数据库的函数——缓存住旧结果,数据变了还是旧的
- ❌ **参数不可哈希**:`query_product(["KB-001"])` 传 list 会 TypeError——缓存拿入参当 dict 键,必须可哈希(int/str/tuple 行,list/dict/set 不行)
- ⚠️ 注意:异常**不**被缓存(查不到 sku 抛 KeyError,下次再查还是会真查再抛)

> 🤯 **Java 对比**:手写 `Map` + `computeIfAbsent`,或 Guava `CacheBuilder`,或 Spring `@Cacheable`。Python 把「记忆化」下沉成一个装饰器(Ch04 装饰器语法的最佳实战)。

> ✅ 做 `query_product` 题:**① 在 def 上一行加 `@lru_cache(maxsize=None)`**;② 函数体照常写遍历查找,找不到 `raise KeyError(sku)`。测试会调 `cache_clear()` 后数 hits/misses,**不加装饰器过不了缓存测试**。

---

## §9.8 functools.partial:偏函数(对应:`make_discounter`)🟢

大促定价:普通会员 9 折、VIP 8 折、SVIP 5 折——同一套「原价 × 折扣率」逻辑,只是乘数不同。`partial` 把一个函数的某些参数**预先固定**,生成新函数。

### 最小例

```python
from functools import partial
from operator import mul

vip_price = partial(mul, 0.8)   # 固定 mul 的第一个参数为 0.8
vip_price(100)                  # 80.0   ← 等价于 mul(0.8, 100)
vip_price(599.0)                # 479.2  ← 599 × 0.8
```

`partial(func, *固定位置参数, **固定关键字参数)` 返回一个可调用对象,调用时把「固定参数 + 新传参数」拼起来交给原函数。

### 真实场景例:一套定价逻辑,三档折扣器

```python
make_discounter = lambda rate: partial(mul, rate)   # 作业里你写这个函数

vip8  = make_discounter(0.8)
svip5 = make_discounter(0.5)
vip8(100)    # 80.0
svip5(100)   # 50.0   ← 两个折扣器互不干扰,各自固化了自己的 rate
```

### partial vs Ch04 闭包 vs lambda

```python
# 三种写法等价,按场景选:
def make1(rate):                    # 闭包(Ch04):灵活,能写多行逻辑
    def apply(price): return rate * price
    return apply
make2 = lambda rate: lambda price: rate * price   # 双层 lambda:紧凑但可读性差
make3 = lambda rate: partial(mul, rate)           # partial:语义最直白——「固定参数」
```

原函数本身就是「前几个参数固定一下就行」时,`partial` 最省;需要额外逻辑(校验、日志)时回闭包。

> 🟡 **Java 对比**:Java 没有偏函数,要手写 `Function<Double,Double>` lambda 包装。partial ≈ 「参数柯里化」的标准库答案。

> ✅ 做 `make_discounter` 题:函数体一行 `return partial(mul, rate)`。测试会验「两个不同 rate 的折扣器互不影响」。

---

## §9.9 综合:类目盘点报告(对应:`category_report`)🔴

最后把本章家伙什合起来,产出大促盘点报告:**每个类目的商品数、总库存、库存总价值、最高单价**。

```python
def category_report(products):
    ordered = sorted(products, key=lambda p: p["category"])            # §9.2
    report = {}
    for cat, group in groupby(ordered, key=lambda p: p["category"]):   # §9.2
        items = list(group)                                            # g 是迭代器,先物化
        report[cat] = {
            "count": len(items),
            "total_stock": sum(p["stock"] for p in items),
            "total_value": reduce(add, (p["price"] * p["stock"] for p in items), 0.0),  # §9.5
            "max_price": max(p["price"] for p in items),
        }
    return report
```

对 products.json 跑出来的真实结果:

```python
{
  '图书':     {'count': 2, 'total_stock': 700, 'total_value': 59600.0,  'max_price': 89.0},
  '影音设备': {'count': 2, 'total_stock': 230, 'total_value': 163770.0, 'max_price': 1299.0},
  '生活用品': {'count': 2, 'total_stock': 30,  'total_value': 47970.0,  'max_price': 1599.0},
  '电脑外设': {'count': 4, 'total_stock': 685, 'total_value': 277715.0, 'max_price': 2199.0},
}
```

验算一条:「电脑外设」总价值 = 599×120 + 159×300 + 2199×45 + 269×220 = 71880 + 47700 + 98955 + 59180 = **277715**。库存 = 120+300+45+220 = **685**。

> 🟡 **设计要点**:分组管「归类」(§9.2),reduce 管「聚合」(§9.5),生成器表达式管「映射」——每个工具干自己那段,组合出完整报表。这就是函数式工具链的手感。

> ✅ 做 `category_report` 题:照上面结构实现(键名 `count` / `total_stock` / `total_value` / `max_price` 测试逐个验)。**内联实现、别调前面的函数**(web 端单题跑时其他函数还是骨架)。空列表返回 `{}`。

---

## §9.10 Java 老手常踩的坑 ⚠️

1. **`groupby` 忘排序**:得到破碎的分组(「电脑外设」出现两次)。记住:sorted + groupby 缺一不可;不要 key 有序的话,直接用 Ch08 的 `defaultdict`。
2. **`groupby` 的 `g` 是迭代器**:不 `list(g)` 物化,外层循环一走它就空了;想反复用必须物化。
3. **对迭代器写 `stream[:n]`**:TypeError。迭代器切片用 `islice`;无限流物化 `list(stream)` 会卡死。
4. **`reduce` 漏初始值**:空序列 TypeError。需要「空输入有默认」就传第三个参数(加法 0、乘法 1、这里 0.0)。
5. **`lru_cache` 用在非纯函数**:依赖时间/随机/外部状态的函数,缓存住旧结果就是 bug。
6. **`lru_cache` 参数不可哈希**:传 list/dict 当参数直接 TypeError。要缓存的结构复杂时,先转成 tuple 再传。
7. **`combinations` vs `permutations` 记反**:组合不计顺序(C(n,r)),排列计顺序(P(n,r))。搭配套餐用组合,排队方案用排列。
8. **`product` 顺序记反**:右边的可迭代对象跑最快(= 嵌套 for 最内层)。

---

## 📖 延伸阅读:更多 itertools/functools 好物(本章不考)

- **`accumulate`**:累积序列(前缀和一行:`accumulate([1,2,3])` → 1,3,6),Ch36 前缀和刷题见。
- **`zip_longest`**:不等长序列 zip,短的用 fillvalue 补齐。
- **`tee`**:把一个迭代器克隆成 n 个(迭代器只能消费一次,想遍历两遍用它)。
- **`starmap`**:map 的参数是元组时自动解包(`starmap(mul, [(2,3),(4,5)])` → 6, 20)。
- **`functools.cache`**(3.9+):= `lru_cache(maxsize=None)` 的简写,更短。
- **`functools.singledispatch`**:按第一个参数的类型分派函数(= Java 重载的 Python 式替代)。

知道有即可,日常 90% 用本章这 8 个。

---

## 📝 本章作业

打开 **`ch09_assignment.py`**,9 个任务,一条主线串起来:合并到货批次 → 按类目分组 → 搭配套餐 → 促销矩阵 → 库存总值 → 流式取样 → 查询缓存 → 折扣定价器 → 盘点报告。

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `merge_batches` | itertools.chain | 🟢 |
| `group_by_category` | itertools.groupby(先排序) | 🔴 |
| `bundle_pairs` | itertools.combinations | 🟢 |
| `promo_matrix` | itertools.product | 🟡 |
| `inventory_value` | functools.reduce | 🟡 |
| `take_first` | itertools.islice | 🟡 |
| `query_product` | functools.lru_cache | 🔴 |
| `make_discounter` | functools.partial | 🟢 |
| `category_report` | 综合 | 🔴 |

```bash
uv run pytest 02_stdlib/ch09/test_ch09_assignment.py -v
```

全绿 = 掌握 Ch09。卡住 → 按对应表回查 §。

---

## ✅ 自测:你真的掌握了吗?

- [ ] 能说清「chain 为什么比列表 `+` 省内存」,知道 `chain.from_iterable` 什么时候用(§9.1)
- [ ] 能解释「groupby 为何必须先排序」+ 它和 `defaultdict` 分组的取舍(§9.2)
- [ ] 不假思索分清 `combinations` / `permutations` / `product`(§9.3/§9.4)
- [ ] 说清 reduce 三要素,以及「什么时候不该用 reduce」(§9.5)
- [ ] 知道迭代器为什么不能 `[:n]`,`islice` 怎么做到惰性取样(§9.6)
- [ ] 能解释 lru_cache 提速原理 + 两个适用条件(纯函数、参数可哈希),会用 `cache_info()` 验证命中(§9.7)
- [ ] 能用 partial 固定参数,并说清它和闭包怎么选(§9.8)
- [ ] 9 个作业全绿

---

## 🎓 费曼挑战(直觉 · Ultralearning 原则八)

> 用大白话讲给「Java 同事」听。讲不清 = 没懂,回查对应 §。

任选一题,讲清楚(1-2 分钟):
1. 「`groupby` 为什么只合并相邻的 key?要正确全局分组得怎么做?和 `defaultdict` 怎么选?」— 卡壳重读 §9.2
2. 「`lru_cache` 是怎么让递归 fib 从 O(2ⁿ) 降到 O(n) 的?什么函数不能加?」— 卡壳重读 §9.7
3. 「迭代器和列表的本质区别是什么?为什么 `islice` 能对无限流取样而 `[:n]` 不行?」— 卡壳重读 §9.6

✅ 自检:不查资料,能说清「为什么」吗?

## 🧠 记忆闪卡(⑤ · 原则七)

→ 本章闪卡在 [`review.md`](./review.md)。学完标复习日期(1/3/7 天)。

---

## ⏭️ 下一步

Ch09 掌握后,进 **Ch10 · 正则表达式**——从 nginx 日志里一行提取 IP/method/path/status,对比 Java `Pattern`/`Matcher`。本章的盘点脚本到那里能再加「日志解析」一段。
