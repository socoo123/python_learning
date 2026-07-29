# Ch09 · itertools + functools:函数式利器

> **预计**:0.5 天 ｜ **前置**:Ch08 ｜ **M2 第二章**
> **目标**:掌握 Python 函数式编程两大支柱——`itertools`(迭代器组合,对比 Java Stream 但更强大)和 `functools`(`reduce`、`lru_cache` 记忆化)。刷题和数据处理的神器。

> 📐 **本教程的契约**:下面每一节(§9.1–§9.5)都**精确对应**作业里的一个任务。讲过的才考,考的必讲过。

---

## 🗺️ 本章地图

读完这章 + 完成作业,你将能够:
- 用 `itertools.chain` 串联多个序列、`groupby` 分组(注意先排序)、`combinations` 组合
- 用 `functools.reduce` 做累积运算(= Java `stream.reduce`)
- 用 `functools.lru_cache` 一行实现记忆化(刷题神器,Java 要手写 Map 缓存)

**作业 ↔ 教程对应表**:

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `flatten` | §9.1 | itertools.chain |
| `group_by_sorted` | §9.2 | itertools.groupby(先排序) |
| `pair_combinations` | §9.3 | itertools.combinations |
| `multiply_all` | §9.4 | functools.reduce |
| `cached_fib` | §9.5 | functools.lru_cache |

---

## ⏱️ 学习路径:费曼五步(约 45-60 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜 | 先猜 Python 怎么写 | 本页 ① |
| ② 先动手 | 打开 `ch09_assignment.py`,先写 | assignment |
| ③ 提取+反馈 | 写完 → `uv run pytest` 红绿 | test |
| ④ 费曼 | 讲清"groupby 为何要先排序""lru_cache 怎么提速" | 本页 ④ |
| ⑤ 存闪卡 | 标 [`review.md`](./review.md) 复习日期 | review.md |

---

## ① 预览猜

1. Java 把多个 Stream 拼起来要 `Stream.concat` 套娃。Python 一个函数叫?
2. Java 按 key 分组用 `Collectors.groupingBy`,稳定正确。Python 的 `groupby` 有个必须注意的前置步骤,是什么?
3. Java 求阶乘/连乘用 `stream.reduce(1, (a,b)->a*b)`。Python 对应什么?
4. Java 写递归斐波那契会慢到不可用,要手写 `Map` 缓存或用 Guava。Python 一个装饰器搞定,叫?
5. 列出 [a,b,c] 所有两两配对,Java 要双重循环,Python 一个函数?

---

## §9.1 itertools.chain:串联多个序列(对应:`flatten`)🟢

`chain` 把多个可迭代对象首尾相接,像一条流。比「列表相加 `+`」省内存(不创建中间列表)。

```python
from itertools import chain

list(chain([1,2], [3,4], [5]))     # [1,2,3,4,5]
list(chain("ab", "cd"))            # ['a','b','c','d']

# chain.from_iterable 接收一个「列表的列表」(不用打星号)
list(chain.from_iterable([[1,2],[3,4]]))   # [1,2,3,4]
```

> 🟡 **Java 对比**:= `Stream.concat(s1, s2)`(但只能拼两个,套娃很难看)。Python `chain` 一次拼任意多个。
>
> `flatten(*lists)` 用 `chain(*lists)` 把传入的多个列表打撒星号喂给 chain。

> ✅ 做 `flatten` 题:`list(chain(*lists))`。

---

## §9.2 itertools.groupby:分组(对应:`group_by_sorted`)🔴

⚠️ **本章最大的坑**:`groupby` 只合并**相邻**的相同 key,不是全局分组!

```python
from itertools import groupby

# ❌ 不排序直接 groupby:[1,2,1] 会被切成三段
[(k, list(g)) for k, g in groupby([1,2,1])]
# [(1, [1]), (2, [2]), (1, [1])]   ← 两个 1 没合并!

# ✅ 先排序,再 groupby
ordered = sorted([1,2,1,3,2])
{k: list(g) for k, g in groupby(ordered)}
# {1: [1, 1], 2: [2, 2], 3: [3]}   ← 正确合并
```

**为什么这样设计**?`groupby` 是**惰性流式**的——它边遍历边产出,不预先把全部数据读进内存。代价是只能看到「当前连续段」。要全局分组,你得先排序(让它变成连续的)。

> 🤯 **Java 对比**:Java 的 `Collectors.groupingBy` 是「收完再分」,自动正确;Python 的 `groupby` 是「流式分组」,要手动排序。各有利弊:Python 版能处理流式/无限数据(配合 sorted 不行,但配合已有序列可以)。日常分组其实 Ch08 的 `defaultdict` 更稳,**`groupby` 主要用于数据已排序的场景**(如按时间已排好的日志)。

### 标准用法(本节作业)

```python
def group_by_sorted(items, key_func):
    ordered = sorted(items, key=key_func)             # ① 先按 key 排序
    return {k: list(g) for k, g in groupby(ordered, key=key_func)}  # ② 再分组
```

注意 `groupby(可迭代, key=函数)`:key 函数指定「按什么分组」(如 `lambda log: log["status"]`)。`g` 是个迭代器,要 `list(g)` 物化(否则用完即弃)。

> ✅ 做 `group_by_sorted` 题:见上。

---

## §9.3 itertools.combinations:组合(对应:`pair_combinations`)🟢

```python
from itertools import combinations

list(combinations(["a","b","c"], 2))   # [('a','b'),('a','c'),('b','c')]
list(combinations([1,2,3], 3))         # [(1,2,3)]   全选
# combinations(序列, r):从 n 个里选 r 个的所有组合(不计顺序)
```

### 顺带认识兄弟函数(本章不出题,刷题常用)

| 函数 | 含义 | 示例(items=[1,2,3]) |
|------|------|---------------------|
| `combinations(items, r)` | 组合(不计顺序) | `(1,2),(1,3),(2,3)` |
| `permutations(items, r)` | 排列(计顺序) | `(1,2),(2,1),(1,3),...` |
| `product(items, repeat=n)` | 笛卡尔积 | `repeat=2` → `(1,1),(1,2),...` |
| `islice(iterable, n)` | 切片前 n 个(迭代器版) | 惰性取前 n |

> 🟡 **Java 对比**:Java 没有内置组合/排列工具,要手写回溯或用 Guava。Python 标准库直接给。LeetCode 回溯题(Ch40)会大量用。

> ✅ 做 `pair_combinations` 题:`list(combinations(items, 2))`。

---

## §9.4 functools.reduce:累积运算(对应:`multiply_all`)🟡

`reduce(函数, 可迭代, 初始值)` 反复把「函数」作用到累积值和下一个元素上,最终得到一个结果。

```python
from functools import reduce
from operator import mul, add

reduce(mul, [2,3,4], 1)    # ((1*2)*3)*4 = 24   连乘
reduce(add, [1,2,3,4], 0)  # ((0+1)+2)+3+4 = 10  连加(等价于 sum)
```

### 三要素

- **函数**:接受 `(累积值, 当前元素)`,返回新累积值。`mul` = `lambda a,b: a*b`。
- **初始值**:reduce 的第三个参数。空可迭代时返回它(`reduce(mul, [], 1)` = 1)。不传则用第一个元素当初始值(空序列会报错)。
- `operator` 模块提供 `mul`/`add`/`or_` 等运算符的函数形式,省得写 lambda。

> 🟡 **Java 对比**:= `stream.reduce(identity, accumulator)`。`reduce(mul, nums, 1)` ≈ `nums.stream().reduce(1, (a,b)->a*b)`。
>
> 注意:Python 社区**不太推荐**滥用 reduce——简单的求和用 `sum()`,简单的连乘用 for 循环更可读。reduce 适合「真正需要累积」的场景。

> ✅ 做 `multiply_all` 题:`reduce(mul, nums, 1)`(mul 从 operator 导入)。

---

## §9.5 functools.lru_cache:记忆化(对应:`cached_fib`)🔴

**一行装饰器,自动缓存函数结果**——相同入参直接返回缓存,不重算。递归优化的神器。

```python
from functools import lru_cache

@lru_cache(maxsize=None)      # None = 无限缓存;也可填数字(如 128)
def fib(n):
    if n < 2:
        return n
    return fib(n-1) + fib(n-2)

fib(100)    # 秒算!没缓存的话,这个递归复杂度是 O(2^n),100 根本算不完
```

### 为什么这么强?

递归 fib 没有 lru_cache 时,`fib(5)` 会重复算 `fib(3)`、`fib(2)` 很多次(指数爆炸)。加了 lru_cache,每个 n 只算一次,后续命中缓存 → 复杂度降到 O(n)。

### 调试工具:`cache_info()`

```python
fib(50)
fib.cache_info()
# CacheInfo(hits=49, misses=51, maxsize=None, currsize=51)
#                ↑ 命中次数   ↑ 未命中(实际计算)次数
```

### 适用条件(重要!)

lru_cache 只适合**纯函数**(相同输入永远相同输出,无副作用):
- ✅ 数学计算(fib、阶乘)、数据查询缓存
- ❌ 依赖外部状态(时间、随机数、数据库)的函数——缓存会失效或出错
- ❌ 参数不可哈希(list/dict 当参数)——lru_cache 用参数当字典键,不可哈希会报错

> 🤯 **Java 对比**:Java 要手写 `Map<Input,Output>` 缓存逻辑,或用 Guava `CacheBuilder`。Python 一个 `@lru_cache` 装饰器搞定。这就是装饰器的威力(Ch04 学过)。

> ✅ 做 `cached_fib` 题:`def` 上一行加 `@lru_cache(maxsize=None)`,写普通递归。

---

## §9.6 functools.partial:偏函数(了解,本章不考)

`partial(函数, *固定参数)` 把一个函数的某些参数「固定」,生成新函数(= 柯里化的替代)。

```python
from functools import partial
from operator import mul

double = partial(mul, 2)     # 固定第一个参数为 2
double(5)                    # 10
double(10)                   # 20

# 等价于 Ch04 的闭包 make_multiplier(2),但 partial 更简洁
```

知道有这个工具即可。

---

## §9.7 Java 老手常踩的坑 ⚠️

1. **`groupby` 忘排序**:得到破碎的分组。记住:groupby = 排序 + 分组,缺一不可。日常分组更推荐 Ch08 的 `defaultdict`。
2. **`groupby` 的 `g` 是迭代器**:`list(g)` 物化后才能反复用,否则用完即弃。
3. **`reduce` 漏写初始值**:空序列会报错(或行为不符预期)。需要「空输入有合理默认」时,传第三个参数(如乘法传 1、加法传 0)。
4. **`lru_cache` 用在非纯函数**:依赖时间/随机/外部状态的函数加了缓存会出错。
5. **`lru_cache` 参数不可哈希**:传 list/dict 当参数会报错。可哈希才行(int/str/tuple/冻结集合)。

---

## 📝 本章作业

打开 **`ch09_assignment.py`**,5 个任务。

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `flatten` | itertools.chain | 🟢 |
| `group_by_sorted` | itertools.groupby(先排序) | 🟡 |
| `pair_combinations` | itertools.combinations | 🟢 |
| `multiply_all` | functools.reduce | 🟡 |
| `cached_fib` | functools.lru_cache | 🟡 |

```bash
uv run pytest 02_stdlib/ch09/test_ch09_assignment.py -v
```
全绿 = 掌握 Ch09。

---

## ✅ 自测

- [ ] 能说清「groupby 为何必须先排序?它和 defaultdict 分组有何区别」(§9.2)
- [ ] 能解释 lru_cache 为何能把递归 fib 从 O(2ⁿ) 降到 O(n),以及它的适用条件(§9.5)
- [ ] 知道 reduce 的初始值参数有什么用(§9.4)
- [ ] 5 个作业全绿

---

## 🎓 费曼挑战

1. 「groupby 为什么只合并相邻的 key?要正确全局分组得怎么做?」— 重读 §9.2
2. 「lru_cache 是怎么让递归斐波那契变快的?什么情况下不能用?」— 重读 §9.5
3. 「itertools 和 Java Stream 相比,各自的设计哲学是什么?」— 重读 §9.1/§9.3

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步

Ch09 掌握后,进 **Ch10 · 正则表达式**——从 nginx 日志里一行提取 IP/method/path/status,对比 Java `Pattern`/`Matcher`。
