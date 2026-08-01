# Ch34 · Python 刷题利器总览(stdlib 五件套)

> **预计**:半天 ｜ **前置**:M1-M5 全部 ｜ **M6 开篇**
> **目标**:Java 老手刷 LeetCode 时常常在写「样板代码」——统计频次要 HashMap+排序,找 top-k 要 PriorityQueue,二分要手写 while 循环,有序去重要 LinkedHashSet,记忆化要手写缓存。Python 标准库把这五类高频套路封装成**一行调用**。本章是 M6 的**工具箱总览**,先让你尝到「Pythonic 刷题有多爽」,后面 Ch35-40 再深入各类题型(双指针/哈希/栈/树/DP/回溯)。

> 📐 **本教程的契约**:§34.2–§34.6 对应作业 5 个函数,**纯 stdlib**,不装任何外部库。

---

## 🗺️ 本章地图

| 作业函数 | 对应小节 | 核心知识点(一行秒杀) |
|----------|----------|----------------------|
| `char_frequency` | §34.2 | `collections.Counter(text).most_common(3)` —— 频次统计 + top-k |
| `kth_largest` | §34.3 | `heapq.nlargest(k, nums)[-1]` —— 第 k 大 |
| `search_insert_pos` | §34.4 | `bisect.bisect_left(nums, target)` —— 二分查找 + 插入点 |
| `dedup_keep_order` | §34.5 | `list(dict.fromkeys(items))` —— 有序去重 |
| `fib` | §34.6 | `@functools.lru_cache` —— 记忆化递归(一行装饰器) |

---

## ⏱️ 学习路径:费曼五步(约 60 分钟)

① 预览猜 → ② 写 assignment → ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## ① 预览猜(先别看答案,猜一下)

1. 给一个字符串,统计每个字符出现几次,再按次数排序取前 3——你 Java 怎么写?HashMap + 遍历 + 排序?Python 能几行搞定?
2. 找数组里第 2 大的数——排序后取 `nums[-2]` 够吗?如果数组上亿、只要第 2 大,全排序划算吗?
3. 有序数组 `[1,3,5,6]` 里查 `2` 在不在,不在就返回它「该插在哪」。你 Java 是不是得手写二分 `while(lo<=hi)`?
4. `[1,2,2,3,1,4]` 去重但保首次出现顺序——Java 用 `LinkedHashSet`,Python 的 `set` **不保序**,那怎么办?
5. 斐波那契递归 `fib(n)=fib(n-1)+fib(n-2)` 是指数级爆炸的。Java 你会手写 `HashMap<Integer,Long>` 缓存;Python 能不能**只加一行**就自动记忆化?

> 💡 全程带着这个问题刷:「同样的逻辑,Java 写多少行样板?Python 用哪个 stdlib 一行替代?」这就是 Pythonic 刷题的爽点。

---

## §34.1 为什么 Python 刷题爽(总览)🟡

刷算法题的核心难点是**算法思路**(双指针/DP/回溯),不是**语言细节**。但 Java 的样板代码(声明集合、写循环、管缓存)会**稀释你的注意力**——你脑子里一半在想「算法」,一半在想「HashMap 怎么遍历」。

Python 的标准库把这些高频套路封装成**语义化的一行**:

| 你想干的事 | Java 写法 | Python 一行 |
|-----------|-----------|------------|
| 统计频次 + top-k | `HashMap + for + sort` | `Counter(text).most_common(k)` |
| 第 k 大 | `PriorityQueue` 或全排序 | `heapq.nlargest(k, nums)[-1]` |
| 有序数组二分 | `while(lo<=hi) mid=...` | `bisect.bisect_left(nums, x)` |
| 有序去重 | `LinkedHashSet + ArrayList` | `list(dict.fromkeys(items))` |
| 记忆化递归 | `HashMap` 手写存取 | `@lru_cache(maxsize=None)` |

> 🟡 **Java 对比**:不是说 Java 写不出来,而是 Java 要你**手写底层**,Python 帮你**封装好了**。面试时 Python 能让你把更多脑力留给算法本身。但记住:**这些 stdlib 替代的是「样板」,不替代「算法思路」**——DP、回溯、图论还得你自己想(Ch35-40 会讲)。

下面逐个讲透。

---

## §34.2 频次统计:char_frequency 🔴(Python 特有)

**题目**:返回字符串中出现次数最多的前 3 个字符,按 `(字符, 次数)` 降序。

```python
from collections import Counter

def char_frequency(text: str) -> list[tuple[str, int]]:
    return Counter(text).most_common(3)
```

**Counter 是什么**:`Counter(可迭代对象)` 把元素统计成 `{元素: 出现次数}` 的 dict 子类。`Counter("aabbbc")` = `{'a':2, 'b':3, 'c':1}`。

**most_common(k)**:返回按次数降序的前 k 个 `(元素, 次数)` 元组列表。`Counter("aabbbc").most_common(3)` = `[('b',3),('a',2),('c',1)]`。

> 🔴 **Python 特有**:`Counter` 是 stdlib 专门为「频次统计」造的轮子,Java 没有直接对应物(Java 人要么用 `HashMap<Character,Integer>` 手写 `merge/getOrDefault`,要么上 Guava 的 `Multiset`)。一行 `Counter(text).most_common(3)` 抵 Java 十几行。

> **Java 老手常踩的坑**:
> 1. 别用 `set` 去数——`set` 不存次数。要存次数必须用 `Counter`/dict。
> 2. `most_common(3)` 不传参数时返回**全部**降序;传 3 只取前 3。空集合返回 `[]` 不报错。
> 3. 频次相同的元素,顺序由 Counter 内部决定(Python 3.7+ 按首次出现顺序),题目通常允许。

**复杂度**:Counter 构建 O(n)(n=len(text));most_common 用堆,取前 k 是 O(n log k)。空间 O(不同字符数)。

---

## §34.3 第 k 大:kth_largest 🟢

**题目**:返回数组第 k 大的元素(LC703 数据流第 K 大简化版 / LC215 数组中第 K 个最大元素)。

```python
import heapq

def kth_largest(nums: list[int], k: int) -> int:
    return heapq.nlargest(k, nums)[-1]
```

**heapq.nlargest(k, nums)**:返回 `nums` 中最大的 k 个元素,**降序**排列成列表。`[-1]` 取最后一个 = 第 k 大那个。

> 🟢 **Java 对比**:Java 要么 `nums` 全排序后取 `nums[n-k]`(O(n log n)),要么用 `PriorityQueue` 维护 size=k 的小顶堆(O(n log k))。Python 的 `heapq.nlargest` 内部就是后者——当 k 远小于 n 时,它只维护一个 size=k 的堆,**不排全量**,省内存。

> **Java 老手常踩的坑**:
> 1. `nlargest(k, nums)` 返回的是**列表**(降序),不是单个值;要 `[-1]` 取第 k 大。
> 2. 别和 `nsmallest` 混——`nlargest` 是「最大的 k 个」,第 k 大 = 其中最小的那个 = 列表最后一个。
> 3. **何时该用 nlargest 何时全排序**:k 很小(如 top 3)→ `nlargest` 更省;k 接近 n → 直接 `sorted(nums, reverse=True)[k-1]` 更快(常数小)。面试题 k 远小于 n 时优先 heapq。

**复杂度**:O(n log k) 时间(堆),O(k) 空间(维护的堆)。k=n 时退化成 O(n log n)。

---

## §34.4 二分查找插入点:search_insert_pos 🟢

**题目**(LC35 搜索插入位置):有序数组找 `target`,找到返回下标;找不到返回它「为保持有序该插入」的下标。

```python
from bisect import bisect_left

def search_insert_pos(nums: list[int], target: int) -> int:
    return bisect_left(nums, target)
```

**bisect_left**:在**升序**数组里二分查找,返回**第一个 `>= target` 的下标**。妙处是它**统一了两种情况**:
- `target` 在数组里 → 该下标就是它的位置(命中)。
- `target` 不在 → 该下标就是它该插入的位置(保持有序)。

不用你写 `if 找到 else 没找到`——`bisect_left` 一行全包。

> 🟢 **Java 对比**:Java 没有内置的二分插入函数,要么 `Arrays.binarySearch`(返回负数表示没找到,还要算 `-(insertionPoint)-1` 反推),要么手写 `while(lo<=hi){ int mid=(lo+hi)/2; ... }`。Python 的 `bisect` 模块直接给你「插入点」语义,省心到离谱。

> **Java 老手常踩的坑**:
> 1. **前提是 nums 已升序**——bisect 不检查、不排序,传乱序数组结果无意义。
> 2. `bisect_left` vs `bisect_right`:有重复元素时,`left` 返回最左那个 `>=target`,`right` 返回最右 `>target`。LC35 用 `left`(插入到重复元素前面)。无重复时两者等价。
> 3. 空数组 → 返回 0;target 比所有大 → 返回 `len(nums)`;比所有小 → 返回 0。边界全自动。

**复杂度**:O(log n) 时间(二分),O(1) 空间。

---

## §34.5 有序去重:dedup_keep_order 🟡

**题目**:去重但**保持首次出现的顺序**(LinkedHashSet 语义)。

```python
def dedup_keep_order(items: list) -> list:
    return list(dict.fromkeys(items))
```

**dict.fromkeys(items)**:用 `items` 的元素做 dict 的 key(值全为 None)。dict key 天然去重,且 **Python 3.7+ dict 保持插入顺序**——所以结果顺序 = 首次出现顺序。`list()` 取出 keys。

> 🟡 **Java 对比**:Java 直接 `new ArrayList<>(new LinkedHashSet<>(items))`——`LinkedHashSet` 专门为「有序去重」存在。Python 的 `set` **不保序**(底层是哈希表,遍历顺序不固定),所以**不能**用 `list(set(items))`(顺序会乱)。Python 的「有序 set」等价物就是「dict 当 set 用」——因为 dict 保序,`dict.fromkeys` 这招成了社区标准写法。

> **Java 老手常踩的坑**:
> 1. **最大的坑:误用 `set`**。`list(set(items))` 能去重但**乱序**!要保序必须 `dict.fromkeys`。
> 2. 元素必须 **hashable**(int/str/tuple 行,list/set/dict 不行——会抛 TypeError)。和 Java HashSet 要求一致。
> 3. 等价手写:`seen=set(); [x for x in items if not (x in seen or seen.add(x))]`——能跑但难读,`fromkeys` 更直观、C 层实现更快。

**复杂度**:O(n) 时间(遍历建 dict),O(不同元素数) 空间。

---

## §34.6 记忆化递归:fib 🔴(Python 特有)

**题目**(LC509 斐波那契数):`fib(0)=0, fib(1)=1, fib(n)=fib(n-1)+fib(n-2)`。

普通递归 `fib(n)=fib(n-1)+fib(n-2)` 是**指数级爆炸**(O(2^n)),`fib(50)` 根本算不完。记忆化(memoization)= 把算过的 `(n -> 结果)` 存起来,下次直接查表,时间降到 O(n)。

```python
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n: int) -> int:
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)
```

**lru_cache 是什么**:一个装饰器,**自动**把函数的「参数 → 返回值」缓存起来。下次用相同参数调用,直接返回缓存,不再算。`maxsize=None` = 缓存无限大。**递归体照写**,装饰器帮你 memo。

> 🔴 **Python 特有(本章的高光)**:同样的递归结构,Java 老手要**手写**:
> ```java
> Map<Integer, Long> cache = new HashMap<>();
> long fib(int n) {
>     if (cache.containsKey(n)) return cache.get(n);   // 查缓存
>     long v = (n < 2) ? n : fib(n-1) + fib(n-2);
>     cache.put(n, v);                                  // 存缓存
>     return v;
> }
> ```
> Python 只需在 `def` 上加 **一行** `@lru_cache(maxsize=None)`,递归体原封不动。这就是「装饰器」的威力——把「横切关注点」(缓存)从业务逻辑里抽出来。Java 老手第一次见通常会很震撼。

> **Java 老手常踩的坑**:
> 1. **装饰器位置**:`@lru_cache(maxsize=None)` 必须在 `def` 之上一行,`@` 不能漏。
> 2. **参数必须 hashable**:lru_cache 用参数做 dict key。`fib(int)` 没问题;若函数参数是 list(不可 hash),会抛错。
> 3. **maxsize 选择**:已知结果集有限(如 fib 的 n)→ `None`(无限);参数空间巨大(可能爆内存)→ 设一个 maxsize(如 128),LRU 自动淘汰最久未用。
> 4. lru_cache 不是万能——它只解决「重复子问题」的记忆化。DP 题如果递归太深(>1000)会栈溢出,那时改迭代(Ch39 DP 会讲)。

**复杂度**:记忆化后 O(n) 时间(每个 n 只算一次),O(n) 空间(缓存 + 递归栈)。

---

## §34.7 五件套横向对比(讲透,不出题)

| 函数 | stdlib 利器 | Java 等价物 | 时间复杂度 | 适用题型 |
|------|------------|------------|-----------|---------|
| `char_frequency` | `Counter.most_common` | `HashMap`+sort / Guava `Multiset` | O(n log k) | 频次统计、top-k 高频 |
| `kth_largest` | `heapq.nlargest` | `PriorityQueue` | O(n log k) | top-k、第 k 大/小 |
| `search_insert_pos` | `bisect.bisect_left` | `Arrays.binarySearch` / 手写二分 | O(log n) | 二分查找、插入点、lower_bound |
| `dedup_keep_order` | `dict.fromkeys` | `LinkedHashSet` | O(n) | 有序去重 |
| `fib` | `@lru_cache` | 手写 `HashMap` 缓存 | O(n) | 记忆化搜索、递归优化 |

**记住一个心法**:**Python 的 stdlib 是「算法题的语法糖」**——它把高频样板封装成语义化 API。面试时第一反应应该是「这题有没有 stdlib 直接用?」而不是「我从头手写」。但 Ch35-40 的**真·算法题**(双指针/DP/回溯)stdlib 帮不了你,还得练思路。

---

## §34.8 Java 老手常踩的坑(汇总)⚠️

1. **去重用 `set` 导致乱序** → 保序必须 `dict.fromkeys`(§34.5)。
2. **二分传了乱序数组** → bisect 不检查,结果无意义(§34.4)。
3. **`nlargest(k,...)[-1]` 漏了 `[-1]`** → 返回的是列表不是单值(§34.3)。
4. **lru_cache 参数不可 hash** → list 参数会崩,改 tuple 或手动 memo(§34.6)。
5. **以为 stdlib 能替代算法** → 它只替代样板,DP/回溯还得自己想(§34.7)。
6. **bisect_left vs bisect_right 混淆** → 有重复时插入点不同,LC35 用 left(§34.4)。
7. **Counter 频次相同时的顺序** → Python 3.7+ 按首次出现,题目通常允许(§34.2)。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `char_frequency` | Counter 频次统计 + top-k | 🔴 |
| `kth_largest` | heapq 第 k 大 | 🟢 |
| `search_insert_pos` | bisect 二分插入点 | 🟢 |
| `dedup_keep_order` | dict.fromkeys 有序去重 | 🟡 |
| `fib` | lru_cache 记忆化递归 | 🔴 |

```bash
uv run pytest 06_leetcode/ch34/test_ch34_assignment.py -v
```

全绿 = 你掌握了 Ch34,Pythonic 刷题入门钥匙到手。

---

## ✅ 自测

- [ ] 能说出 5 个 stdlib 利器各自替代 Java 的什么写法
- [ ] 知道 `Counter(text).most_common(3)` 返回什么、空输入返回什么
- [ ] 知道 `heapq.nlargest(k, nums)` 返回列表不是单值,要 `[-1]` 取第 k 大
- [ ] 知道 `bisect_left` 统一了「查找」和「插入点」两种语义,且前提是数组升序
- [ ] 知道**不能用 `set` 去重保序**,要用 `dict.fromkeys`
- [ ] 会用 `@lru_cache(maxsize=None)` 给递归加记忆化,知道它和 Java 手写 HashMap 缓存的对应关系
- [ ] 5 个作业全绿

## 🎓 费曼挑战

1. 「Python 刷题为什么爽?举 3 个 stdlib 一行秒杀 Java 样板的例子。」— 重读 §34.1 / §34.7
2. 「为什么去重保序不能用 `set`?`dict.fromkeys` 凭什么能保序?」— 重读 §34.5
3. 「`@lru_cache` 装饰器做了什么?Java 里实现同样效果要写什么?它有什么局限?」— 重读 §34.6

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步:Ch35 双指针/滑动窗口

本章是「工具箱总览」——你尝到了 stdlib 一行秒杀的甜头。但**真·算法题**光靠 stdlib 不够。Ch35 开始进入题型专项:**双指针**(对撞指针 / 快慢指针)和**滑动窗口**——这是 LC 最高频的套路之一(两数之和、三数之和、最长无重复子串)。从「用工具」升级到「想策略」。
