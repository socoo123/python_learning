# Ch34 · Python 刷题利器总览(stdlib 工具箱)

> **预计**:0.5 天 ｜ **前置**:M1-M2(尤其 Ch08 collections、Ch09 itertools)｜ **M6 开篇**
> **目标**:Java 老手刷 LeetCode,常常一半脑力耗在「样板代码」上——统计频次要 HashMap+排序、分组要 containsKey 判空、top-k 要 PriorityQueue、二分要手写 while、多键排序要 Comparator 链、记忆化要手写 HashMap 缓存。Python 标准库把这些高频套路封装成**一行调用**。本章是 M6 的**工具箱总览**:10 件利器 × 10 道题,先让你尝到「Pythonic 刷题有多爽」,Ch35-40 再深入题型套路(双指针/哈希/栈/树/DP/回溯)。

> 📐 **本教程的契约**:§34.2–§34.11 每节**精确对应**作业里的一个函数,讲过的才考,考的必讲过。§34.1 是开胃、§34.12 是坑清单,讲透不出题。卡住时按对应表回查小节。

---

## 🗺️ 本章地图

读完这章 + 完成作业,你将能够:
- 用 `Counter(x).most_common(k)` 一行做「频次统计 + top-k」
- 用 `defaultdict(int)` 分组聚合,告别 `containsKey` 判空
- 用 `heapq.nlargest(k, nums)[-1]` 拿第 k 大,说清何时比全排序划算
- 用 `deque(maxlen=n)` 做定长滑窗,满了自动踢旧
- 用 `bisect_left` 一行统一「查找」和「插入点」两种语义
- 用 `sorted(key=lambda r: (-r[1], r[0]))` 元组 key 做多键排序
- 用 `itertools.accumulate` 一行出前缀和
- 用切片 `nums[-k:] + nums[:-k]` 一行轮转数组,并避开 `-0` 和空数组的坑
- 用 `@lru_cache(maxsize=None)` 给递归加记忆化
- 用 `float('inf')` 哨兵写一趟扫描,并把前面的函数组装成综合题

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业题 | 对应小节 | 核心知识点 |
|--------|----------|-----------|
| `char_frequency` | §34.2 | Counter.most_common 频次统计 + top-k |
| `sum_by_category` | §34.3 | defaultdict(int) 分组聚合免判空 |
| `kth_largest` | §34.4 | heapq.nlargest 第 k 大 |
| `moving_averages` | §34.5 | deque(maxlen=n) 定长滑窗 |
| `search_insert_pos` | §34.6 | bisect.bisect_left 二分查找 + 插入点 |
| `sort_students` | §34.7 | sorted + key=lambda 元组多键排序 |
| `running_sum` | §34.8 | itertools.accumulate 前缀和 |
| `rotate_array` | §34.9 | 切片 + 星号解包数组轮转 |
| `fib` | §34.10 | @lru_cache 记忆化递归 |
| `array_report` | §34.11 | 综合:float('inf') 哨兵 + 复用前面函数 |

---

## ⏱️ 学习路径:费曼五步(约 60 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(3分钟) | 下面 8 个问题,先猜答案 | 本页 ① |
| ② 先动手 | 打开 `ch34_assignment.py`,**先试着写**(别看教程) | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清「stdlib 替代的是样板,不是算法」 | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性原则**:别通读!先猜 ① → 去 ② 写作业 → **哪题卡了,回对应 § 查** → 改 → 再跑。

---

## ① 预览猜(先想,别急着翻答案)

1. 统计字符串里每个字符出现几次、取前 3——Java 的 HashMap + 遍历 + 排序,Python 能几行?
2. 「按类目汇总金额」,每次累加前都要 `if (map.containsKey(cat))`?Python 有没有办法让 key 不存在时**自动**从 0 开始?
3. 找数组里第 2 大的数——`sorted` 全排序后取下标够吗?如果数组上亿、只要第 2 大,全排序划算吗?
4. 「最近 3 次的平均值」:窗口每滑动一步,最旧的那个元素怎么踢掉?Java 的 `ArrayDeque` 有「定长自动踢旧」吗?
5. 有序数组 `[1,3,5,6]` 里查 `2`,不在就返回「该插哪」——Java 手写 `while(lo<=hi)`,Python 呢?
6. 成绩榜「分数降序、同分按名字升序」——Java 的 `Comparator.comparing().reversed().thenComparing()` 链,Python 一个 lambda 怎么表达?
7. `[1,2,3,4]` 的前缀和 `[1,3,6,10]`——不写 `sum += x` 循环,一行能出来吗?
8. `fib(50)` 裸递归会指数爆炸。Java 手写 HashMap 缓存,Python 能不能**只加一行**就自动记忆化?

> 猜完带着验证心态进入正文。第 2、4、8 题是 🔴(Python 特有),是本章爽点最密集的地方。

---

## §34.1 总览:Java 样板 vs Python 一行(不出题)🟡

刷算法题的核心难点是**算法思路**(双指针/DP/回溯),不是**语言细节**。但 Java 的样板代码(声明集合、判空、写循环、管缓存)会**稀释你的注意力**——脑子里一半在想「算法」,一半在想「HashMap 怎么遍历」。

Python 的标准库把这些高频套路封装成**语义化的一行**:

| 你想干的事 | Java 写法 | Python 一行 | 本节 |
|-----------|-----------|------------|------|
| 频次统计 + top-k | `HashMap` + `merge` + 排序 | `Counter(x).most_common(k)` | §34.2 |
| 分组聚合(免判空) | `map.merge(k, v, Integer::sum)` | `defaultdict(int)` + `+=` | §34.3 |
| 第 k 大 | `PriorityQueue` 小顶堆 | `heapq.nlargest(k, nums)[-1]` | §34.4 |
| 定长滑窗 | `ArrayDeque` + 手写 `poll` | `deque(maxlen=n)` | §34.5 |
| 有序数组二分 | `Arrays.binarySearch` / 手写 while | `bisect.bisect_left(nums, x)` | §34.6 |
| 多键排序 | `Comparator` 链 | `sorted(key=lambda r: (-r[1], r[0]))` | §34.7 |
| 前缀和 | 手写 `sum += x` 循环 | `list(accumulate(nums))` | §34.8 |
| 数组轮转 | 三次反转 / `arraycopy` | `nums[-k:] + nums[:-k]` | §34.9 |
| 记忆化递归 | 手写 `HashMap` 缓存 | `@lru_cache(maxsize=None)` | §34.10 |
| 最值扫描初始化 | `Integer.MAX_VALUE` | `float('inf')` | §34.11 |

> 🟡 **Java 对比**:不是说 Java 写不出来,而是 Java 要你**手写底层**,Python 帮你**封装好了**。面试时 Python 让你把脑力留给算法本身。但记住:**这些 stdlib 替代的是「样板」,不替代「算法思路」**——DP、回溯、图论还得你自己想(Ch35-40)。

下面逐件讲透。

---

## §34.2 Counter 频次统计:char_frequency 🔴

**题目**(LC347 前 K 个高频元素的字符版):返回字符串中出现次数最多的前 3 个字符,按 `(字符, 次数)` 降序。

### Java 对照最小例

```java
// Java:HashMap 统计 + Stream 排序,十几行
Map<Character, Integer> freq = new HashMap<>();
for (char c : text.toCharArray()) {
    freq.merge(c, 1, Integer::sum);
}
List<Map.Entry<Character, Integer>> top3 = freq.entrySet().stream()
    .sorted(Map.Entry.<Character, Integer>comparingByValue().reversed())
    .limit(3)
    .toList();
```

```python
# Python:Counter 一行秒杀
from collections import Counter

def char_frequency(text: str) -> list[tuple[str, int]]:
    return Counter(text).most_common(3)
```

### 真实场景例(已验证)

```python
Counter("aabbbc")     # {'a': 2, 'b': 3, 'c': 1} —— dict 子类,{元素: 次数}
Counter("aabbbc").most_common(3)   # [('b', 3), ('a', 2), ('c', 1)]
Counter("mississippi").most_common(3)
# [('i', 4), ('s', 4), ('p', 2)] —— i 和 s 同 4 次,i 先出现所以排前
Counter("").most_common(3)         # [] —— 空输入不报错
Counter("ab").most_common(3)       # [('a', 1), ('b', 1)] —— 不足 3 个返回实际数量
```

### ❌ 错误写法 → ✅ 正确写法

```python
# ❌ 用 set 统计——set 只存「有没有」,不存「几次」
len(set(text))                      # 只能得到「几种字符」,次数丢了

# ❌ 手写 dict + if 判空(Ch08 之前的老习惯)
freq = {}
for c in text:
    if c in freq:                   # 每次都在重复 defaultdict 能自动做的事
        freq[c] += 1
    else:
        freq[c] = 1

# ✅ Counter 一步到位,most_common 直接给 top-k
Counter(text).most_common(3)
```

> 🔴 **Python 特有**:`Counter` 是 stdlib 专门为「频次统计」造的轮子,Java 没有直接对应物(要么手写 `HashMap.merge/getOrDefault`,要么上 Guava 的 `Multiset`)。
>
> **常踩的坑**:① `most_common()` 不传参数返回**全部**降序;传 3 只取前 3。② 频次相同时,Python 3.7+ 按**首次出现顺序**排(文档明写,可依赖)。③ 返回的是 `(元素, 次数)` **元组**列表,解包时注意顺序。

**复杂度**:Counter 构建 O(n);`most_common(k)` 内部用堆,O(n log k)。空间 O(不同字符数)。

---

## §34.3 defaultdict 分组免判空:sum_by_category 🔴

**题目**:订单流水是 `(类目, 金额)` 列表,同一类目出现多次要累加,返回 `{类目: 总额}`(金额可为负=退款)。

### Java 对照最小例

```java
// Java:merge 一行能干,但很多老手还在写 containsKey 两段式
Map<String, Integer> totals = new HashMap<>();
for (var rec : records) {
    totals.merge(rec.category(), rec.amount(), Integer::sum);
}
```

```python
# Python:defaultdict(int) —— 缺 key 时自动调 int() 得 0,直接 +=
from collections import defaultdict

totals = defaultdict(int)
for category, amount in records:
    totals[category] += amount      # 不用判 key 在不在
```

### 真实场景例(已验证)

```python
sum_by_category([("书", 30), ("衣", 200), ("书", 25)])
# {"书": 55, "衣": 200}        —— "书" 出现两次,自动累加

sum_by_category([("书", 30), ("书", -5)])
# {"书": 25}                   —— 退款:负数照常 +=

sum_by_category([])            # {}
```

### ❌ 错误写法 → ✅ 正确写法

```python
# ❌ 普通 dict + 每次判空(Java containsKey 思维残留)
totals = {}
for cat, amount in records:
    if cat not in totals:
        totals[cat] = 0
    totals[cat] += amount

# 🟡 普通 dict + get 默认值(能跑,Ch02 学过;但「默认值是 0」藏在循环里)
totals[cat] = totals.get(cat, 0) + amount

# ✅ defaultdict(int):「缺 key 时默认值是 int()=0」声明在创建处,意图最清晰
totals = defaultdict(int)
for cat, amount in records:
    totals[cat] += amount
```

> 🔴 **关键机制**:`defaultdict(int)` 里的 `int` 是**工厂函数**——访问不存在的 key 时自动调用 `int()` 得到 `0` 并存入。换成 `defaultdict(list)` 就自动得到 `[]`(分组列表神器,Ch36 字母异位词分组会用);`defaultdict(set)` 自动得到空 set。
>
> **常踩的坑**:① 工厂要传**类型本身**(`defaultdict(int)`),不是实例(`defaultdict(0)` 会报错,0 不可调用)。② 读不存在的 key 也会**创建**它——`defaultdict` 做「只读查询」要小心key越查越多;所以作业里返回前 `dict(totals)` 转回普通 dict,把「自动建 key」的副作用关在函数内。③ `defaultdict` == 普通 `dict` 比较时按内容,相等(但 `type` 不同,测试里专门查了这一点)。

**复杂度**:O(n) 时间,O(类目数) 空间。

---

## §34.4 heapq 第 k 大:kth_largest 🟢

**题目**(LC215 / LC703 简化版):返回数组第 k 大的元素。

### Java 对照最小例

```java
// Java:PriorityQueue 小顶堆,超过 size 就 poll
PriorityQueue<Integer> heap = new PriorityQueue<>();
for (int x : nums) {
    heap.offer(x);
    if (heap.size() > k) heap.poll();   // 堆里只留最大的 k 个
}
int kth = heap.peek();                  // 堆顶 = 第 k 大
```

```python
# Python:heapq.nlargest 内部就是同样的堆
import heapq

def kth_largest(nums: list[int], k: int) -> int:
    return heapq.nlargest(k, nums)[-1]
```

### 真实场景例(已验证)

```python
heapq.nlargest(2, [3, 2, 1, 5, 6, 4])   # [6, 5] —— 最大的 2 个,【降序列表】
heapq.nlargest(2, [3, 2, 1, 5, 6, 4])[-1]  # 5 —— 列表最后一个 = 第 2 大

kth_largest([3, 2, 1, 5, 6, 4], 1)      # 6(k=1 就是最大值)
kth_largest([3, 2, 1, 5, 6, 4], 6)      # 1(k=len 就是最小值)
kth_largest([-1, -5, -3], 2)            # -3(负数一样排)
```

### ❌ 错误写法 → ✅ 正确写法

```python
# ❌ 忘了 nlargest 返回的是列表,直接当单值用
heapq.nlargest(k, nums)                 # [6, 5] —— 这是 list,不是第 k 大!

# ❌ 和 nsmallest 记反:nlargest 是「最大的 k 个」,
#    第 k 大 = 这 k 个里最小的 = 列表【最后一个】
heapq.nlargest(k, nums)[0]              # 6 —— 这是最大值,不是第 k 大(除非 k=1)

# ✅ nlargest(k, nums)[-1];k 接近 n 时直接全排序常数更小
heapq.nlargest(k, nums)[-1]
sorted(nums, reverse=True)[k - 1]       # k≈n 时这个反而更快
```

> 🟢 **何时用哪个**:k 很小(如 top 3,n 上亿)→ `nlargest` 只维护 size=k 的堆,O(n log k),**不排全量**省内存;k 接近 n → 直接 `sorted(reverse=True)[k-1]`,O(n log n) 但常数小。面试说得出这个权衡是加分项。
>
> **常踩的坑**:① 返回值是**列表**,要 `[-1]`。② 有重复元素时按「降序排序后第 k 个」理解:`[5,5,4]` 第 2 大是 5。③ heapq 的堆是**最小堆**,`heappush/heappop` 弹的是最小值;`nlargest` 是帮你封装好的高层 API,优先用它。

**复杂度**:O(n log k) 时间,O(k) 空间(k=n 时退化成 O(n log n))。

---

## §34.5 deque(maxlen) 定长滑窗:moving_averages 🟡

**题目**(LC346 数据流移动平均的离线版):窗口从左到右滑过数组,每步返回**当前窗口**的平均值;窗口未满时按实际长度平均。

### Java 对照最小例

```java
// Java:ArrayDeque 没有「定长」语义,要自己判断踢旧
Deque<Integer> window = new ArrayDeque<>();
for (int x : nums) {
    window.offerLast(x);
    if (window.size() > size) {
        window.pollFirst();             // 手动踢最旧
    }
    double avg = window.stream().mapToInt(Integer::intValue).average().orElse(0);
}
```

```python
# Python:deque(maxlen=size) —— 满了再 append,自动从左边踢最旧
from collections import deque

window = deque(maxlen=2)
window.append(1)          # deque([1])
window.append(2)          # deque([1, 2])
window.append(3)          # deque([2, 3]) —— 1 被自动踢掉,不用你管
```

### 真实场景例(已验证):最近 N 次调用的平均耗时

```python
moving_averages([1, 2, 3, 8], 2)
# [1.0, 1.5, 2.5, 5.5]
#  窗口:[1]   [1,2]   [2,3]   [3,8]

moving_averages([1, 10, 3, 5], 2)
# [1.0, 5.5, 6.5, 4.0]
#  关键:第 3 步窗口是 [10,3] 不是 [1,10,3] —— 1 已被踢出

moving_averages([1, 2], 5)    # [1.0, 1.5] —— size > len:窗口永远装不满
moving_averages([], 3)        # []
```

### ❌ 错误写法 → ✅ 正确写法

```python
# ❌ 用 list 当队列,pop(0) 踢最旧——每次 O(n) 搬数据
window = []
window.append(x)
if len(window) > size:
    window.pop(0)                     # list 头部删除是 O(n),队列场景的标配大坑

# ❌ 以为 deque(maxlen) 满了会报错或拒绝——它不会,它是「静默踢旧」
#    反过来,以为普通 deque 会自动踢旧也不对:不加 maxlen 它无限长

# ✅ deque(maxlen=size):左进右出/右进左出都是 O(1),定长自动踢旧
window = deque(maxlen=size)
for x in nums:
    window.append(x)
    result.append(sum(window) / len(window))
```

> 🟡 **Java 对比**:Java 的 `ArrayDeque` 和 Python `deque` 都是双端队列、两端 O(1),但 **`maxlen` 是 Python 独有**——「定长缓冲」这一个参数,把「最近 N 条日志」「滑动窗口」「LRU 草稿」这类场景的踢旧逻辑全省了。
>
> **常踩的坑**:① `list.pop(0)` 是 O(n)(数组整体搬移),队列操作必须用 `deque.popleft()` O(1)——这是 Python 刷题的**标配坑**,BFS(Ch38)里写错会直接 TLE。② `maxlen` 只在 append/appendleft/extend 时生效,已满时**另一端**的元素被丢弃。③ `sum(window)/len(window)` 窗口未满时 `len` 是实际长度,不用特判。

**复杂度**:O(n) 时间(每步 sum 一个定长窗口,视为 O(size)),O(size) 空间。

---

## §34.6 bisect 二分:search_insert_pos 🟢

**题目**(LC35 搜索插入位置):升序数组找 `target`,找到返回下标;找不到返回它「为保持有序该插入」的下标。

### Java 对照最小例

```java
// Java:Arrays.binarySearch 找不到时返回 -(insertionPoint) - 1,要取反换算
int idx = Arrays.binarySearch(nums, target);
if (idx < 0) {
    idx = -idx - 1;                   // 反推插入点,每次都得多想一层
}
// 或者手写 while (lo <= hi) { int mid = (lo + hi) / 2; ... } —— 边界地狱
```

```python
# Python:bisect_left 直接给「插入点」语义,命中/不命中一行统一
from bisect import bisect_left

def search_insert_pos(nums: list[int], target: int) -> int:
    return bisect_left(nums, target)   # 第一个 >= target 的下标
```

### 真实场景例(已验证)

```python
search_insert_pos([1, 3, 5, 6], 5)    # 2 —— 命中
search_insert_pos([1, 3, 5, 6], 2)    # 1 —— 2 不在,插到 3 前面
search_insert_pos([1, 3, 5, 6], 7)    # 4 —— 比所有都大,插末尾
search_insert_pos([1, 3, 5, 6], 0)    # 0 —— 比所有都小,插开头
search_insert_pos([], 5)              # 0 —— 空数组
search_insert_pos([1, 2, 2, 2, 3], 2) # 1 —— 有重复,left 给最左那个
```

### ❌ 错误写法 → ✅ 正确写法

```python
# ❌ 对乱序数组用 bisect——它不检查、不排序,结果毫无意义
bisect_left([3, 1, 2], 2)             # 返回什么都别信:前提是【已升序】

# ❌ 有重复元素时用错左右:bisect_right 会插到重复元素【后面】
from bisect import bisect_right
bisect_right([1, 2, 2, 2, 3], 2)      # 4 —— LC35 要的是 1

# ✅ LC35 语义 = bisect_left(最左 >= target);要「最右 > target」才用 bisect_right
bisect_left([1, 2, 2, 2, 3], 2)       # 1
```

> 🟢 **常踩的坑**:① **前提是 nums 已升序**,bisect 不检查。② `bisect_left` vs `bisect_right`:有重复时 left 返回最左 `>= target`,right 返回最右 `> target`;无重复时等价。LC35 用 left。③ 还有个 `insort_left(nums, x)` = 找到插入点**并真的插进去**(O(n) 搬移),「维护有序列表」场景好用。④ 边界全自动:空数组返回 0,target 最大返回 `len(nums)`。

**复杂度**:O(log n) 时间,O(1) 空间。

---

## §34.7 sorted + key 多键排序:sort_students 🟡

**题目**:成绩榜排序——分数**降序**,同分按名字**字典序升序**;返回新列表,不改入参。

### Java 对照最小例

```java
// Java:Comparator 链,reversed + thenComparing
records.sort(Comparator
    .comparing(Student::score).reversed()
    .thenComparing(Student::name));
```

```python
# Python:key 返回元组,数值键取负,一行
def sort_students(records):
    return sorted(records, key=lambda r: (-r[1], r[0]))
```

### 真实场景例(已验证)

```python
sort_students([("amy", 90), ("bob", 95), ("ada", 95), ("zed", 80)])
# [("ada", 95), ("bob", 95), ("amy", 90), ("zed", 80)]
#  -95 打平时比名字:"ada" < "bob"

sort_students([("c", 60), ("a", 60), ("b", 60)])
# [("a", 60), ("b", 60), ("c", 60)] —— 全同分,纯按名字
sort_students([])                     # []
```

**为什么元组 key 能一行搞定**:sorted 按 key 算出的**元组逐元素**比较——先比 `-r[1]`(负号把「分数降序」转成「负数升序」),打平再比 `r[0]`(名字升序)。一层嵌一层,正好对应 `thenComparing` 链。

### ❌ 错误写法 → ✅ 正确写法

```python
# ❌ 给字符串键加负号——只有数值能取负!
sorted(records, key=lambda r: (-r[1], -r[0]))   # TypeError: bad operand type for unary -

# ❌ 用 list.sort() 原地排——入参被改了(测试专门查了这一点)
records.sort(key=lambda r: (-r[1], r[0]))       # records 本身变了!

# ❌ 双重条件写成 if-else 冒泡——几行 bug 换一个一行 API,不值

# ✅ 数值降序取负、字符串升序照写,元组一层层比;sorted 返回新列表
sorted(records, key=lambda r: (-r[1], r[0]))

# ✅ 字符串也要降序时:利用 sorted 的【稳定性】排两次(先次键后主键)
#    先按名字降序,再按分数降序——后排的主键赢,同分时保住先排的次序
tmp = sorted(records, key=lambda r: r[0], reverse=True)
result = sorted(tmp, key=lambda r: r[1], reverse=True)
```

> 🟡 **Java 对比**:`sorted` 和 Java `List.sort`/`Stream.sorted` 一样,都是**稳定排序**(等值元素保持原相对顺序)——「排两次,先次键后主键」的技巧就靠稳定性撑着。差异在:key 是**一次性算出**的比较键(算一次缓存),不是 Java 那样两两调用 comparator,所以 key 函数里别写贵操作。
>
> **常踩的坑**:① `sorted()` 返回新列表,`list.sort()` 原地排返回 `None`——`xs = xs.sort()` 会把 xs 变成 `None`,经典翻车。② 混合升降序:数值用负号,字符串用稳定性排两次。③ key 里 `r[1]`/`r[0]` 别写反,顺序 = 主键在前。

**复杂度**:O(n log n) 时间(Timsort),O(n) 空间。

---

## §34.8 itertools.accumulate 前缀和:running_sum 🔴

**题目**(LC1480 一维数组的动态和):返回累加序列,第 i 项 = `nums[0] + ... + nums[i]`。

前缀和是「区间和」类题目的**地基**——`区间和(i..j) = prefix[j+1] - prefix[i]`,Ch36 的 LC560(和为 K 的子数组)就要靠它。

### Java 对照最小例

```java
// Java:没有前缀和 API,手写累加循环
int[] prefix = new int[nums.length];
int sum = 0;
for (int i = 0; i < nums.length; i++) {
    sum += nums[i];
    prefix[i] = sum;
}
```

```python
# Python:itertools.accumulate 一行
from itertools import accumulate

def running_sum(nums: list[int]) -> list[int]:
    return list(accumulate(nums))
```

### 真实场景例(已验证):每日新增 → 累计总数

```python
running_sum([1, 2, 3, 4])       # [1, 3, 6, 10]    —— 每日新增 1,2,3,4 的累计
running_sum([1, 1, 1, 1, 1])    # [1, 2, 3, 4, 5]
running_sum([-1, 1])            # [-1, 0]          —— 负数照常累加
running_sum([3, 1, -2, 5])      # [3, 4, 2, 7]
running_sum([])                 # []
```

### ❌ 错误写法 → ✅ 正确写法

```python
# ❌ 忘了 accumulate 返回的是【迭代器】,直接返回/打印
accumulate([1, 2, 3])           # <itertools.accumulate object ...> —— 不是列表!
list(accumulate([1, 2, 3]))     # ✅ [1, 3, 6] —— 用 list() 物化

# ❌ 手写累加还写错 off-by-one(prefix[i] 到底含不含 nums[i])
prefix = [0] * len(nums)
for i in range(len(nums)):
    prefix[i] = prefix[i - 1] + nums[i]   # i=0 时 prefix[-1] 是最后一个元素!

# ✅ accumulate 没有下标,就没有 off-by-one
list(accumulate(nums))
```

> 🔴 **Python 特有**:Java 完全没有对应物(`Stream.reduce` 只给最终值,不给中间过程)。`accumulate` 还有两个进阶参数:**`func`** 换运算——`accumulate(nums, func=operator.mul)` 变前缀积;**`initial`** 在开头补初值——`accumulate(nums, initial=0)` 得到 `[0, 1, 3, 6]`,做区间和公式时这个前导 0 能省掉一堆 `if i > 0` 特判(Ch36 会用到)。
>
> **常踩的坑**:① 返回迭代器,**用一次就没**,要 `list()` 存住。② 求区间和时想清楚「含不含端点」:`prefix[j] - prefix[i-1]`(无前导 0)还是 `prefix[j+1] - prefix[i]`(有 initial=0)。

**复杂度**:O(n) 时间,O(n) 空间(输出列表)。

---

## §34.9 切片与星号:rotate_array 🟡

**题目**(LC189 轮转数组的非原地版):数组向右轮转 k 位,返回**新列表**。

### Java 对照最小例

```java
// Java 经典解:三次反转(先整体反转,再分别反转前后两段)
reverse(nums, 0, n - 1);
reverse(nums, 0, k - 1);
reverse(nums, k, n - 1);
// 或者 System.arraycopy 拼图:先拷尾部 k 个,再挪前段
```

```python
# Python:切片拼接,一行
def rotate_array(nums: list[int], k: int) -> list[int]:
    if not nums:
        return []                 # k % 0 会 ZeroDivisionError,先挡空数组
    k %= len(nums)                # k 可能大于长度,取模归一
    return nums[-k:] + nums[:-k]  # 尾部 k 个切下来拼到前面
```

### 真实场景例(已验证)

```python
rotate_array([1, 2, 3, 4, 5, 6, 7], 3)   # [5, 6, 7, 1, 2, 3, 4]
#   nums[-3:] = [5,6,7](最后 3 个)   nums[:-3] = [1,2,3,4](其余)

rotate_array([1, 2], 3)   # [2, 1] —— 3 % 2 = 1,右移 1 位
rotate_array([1, 2, 3], 0)  # [1, 2, 3]
rotate_array([1, 2, 3], 3)  # [1, 2, 3] —— 整圈,内容不变
rotate_array([], 5)         # [] —— 不判空会崩在 k % 0
```

### ❌ 错误写法 → ✅ 正确写法

```python
# ❌ 忘了取模:k > len 时 nums[-k:] 语法上能跑但语义错(切出全列表)
#    [1,2][-3:] == [1,2] —— 拼出来是 [1,2]+[] 的错答案
# ✅ k %= len(nums)

# ❌ 忘了挡空数组:k % 0 → ZeroDivisionError
# ✅ if not nums: return []

# 🟡 冷知识:k=0 时 nums[-0:] + nums[:-0] 碰巧正确——
#    -0 == 0,nums[-0:] 是全列表、nums[:-0] 是 [],拼起来刚好是原样拷贝。
#    但这是「碰巧对」,别依赖,判空 + 取模写全才稳。

# ✅ 星号解包等价写法(结果一样,看个人口味):
return [*nums[-k:], *nums[:-k]]
```

> 🟡 **切片/解包速记**(Ch02 讲过,刷题天天用):`nums[-k:]` = 最后 k 个;`nums[:-k]` = 去掉最后 k 个;`nums[::-1]` = 反转。解包:`first, *rest = nums` 拆「头 + 尾」;`[*a, *b]` 拼两个列表(= `a + b`);`*mid, last = nums` 拆「前面所有 + 最后一个」。
>
> **常踩的坑**:① 切片**越界不报错**(`nums[5:100]` 静默截断),安全但会掩盖逻辑错误。② `nums[-k:]` 当 k=0 时是**全列表**不是空——上面 `-0` 的例子。③ 返回新列表 vs 原地:LC189 原题要求原地(`nums[:] = ...` 切片赋值可以 O(1) 额外空间),作业练的是返回新列表的版本。

**复杂度**:O(n) 时间(切片拷贝),O(n) 空间(新列表)。

---

## §34.10 lru_cache 记忆化:fib 🔴

**题目**(LC509 斐波那契数):`fib(0)=0, fib(1)=1, fib(n)=fib(n-1)+fib(n-2)`。

裸递归是**指数级爆炸**(O(2^n)):`fib(50)` 要算约 2^50 次,跑不完。记忆化(memoization)= 把算过的 `(n -> 结果)` 存起来,下次直接查表,降到 O(n)。

### Java 对照最小例

```java
// Java:手写 HashMap 缓存,查-算-存三步全要自己来
Map<Integer, Long> cache = new HashMap<>();
long fib(int n) {
    if (cache.containsKey(n)) return cache.get(n);   // ① 查缓存
    long v = (n < 2) ? n : fib(n - 1) + fib(n - 2);  // ② 算
    cache.put(n, v);                                  // ③ 存缓存
    return v;
}
```

```python
# Python:递归体原封不动,只加一行装饰器
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n: int) -> int:
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)
```

### 真实场景例(已验证)

```python
fib(0)    # 0
fib(1)    # 1
fib(10)   # 55
fib(20)   # 6765
fib(50)   # 12586269025 —— 裸递归这里会卡死,记忆化后秒出(测试专门考这条)
```

### ❌ 错误写法 → ✅ 正确写法

```python
# ❌ 装饰器忘加括号写成 @lru_cache —— 它会把 fib 当 maxsize 参数传进去
@lru_cache                              # ❌ 少括号 + 少参数
def fib(n): ...

# ❌ 给「参数不可 hash」的函数加缓存——list 参数直接 TypeError
@lru_cache(maxsize=None)
def path_sum(grid): ...                 # grid 是 list,不可 hash → 崩
# ✅ 改传 tuple,或函数内手动 memo

# ✅ @lru_cache(maxsize=None) 紧贴 def 上一行,@ 和括号都不能少
@lru_cache(maxsize=None)
def fib(n: int) -> int: ...
```

> 🔴 **Python 特有(本章高光)**:装饰器把「缓存」这个**横切关注点**从业务逻辑里抽出来——递归体还是教科书上的数学定义,缓存逻辑零侵入。Java 老手第一次见通常会很震撼。
>
> **常踩的坑**:① 参数必须 **hashable**(int/str/tuple 行;list/dict/set 不行)。② `maxsize=None` = 缓存无限大;参数空间巨大时设具体条数(如 128),LRU 自动淘汰最久未用。③ lru_cache 只解决「重复子问题」;递归深度 >1000 还是会栈溢出(`sys.setrecursionlimit` 或改迭代,Ch39 DP 会讲)。④ 同一个被装饰函数**共享缓存**,多次调用越跑越快——测试里 `fib(50)` 秒出靠的就是前面调用攒下的缓存。

**复杂度**:记忆化后 O(n) 时间(每个 n 只算一次),O(n) 空间(缓存 + 递归栈)。

---

## §34.11 float('inf') 哨兵 + 综合:array_report 🟡

**题目**(综合):给整数数组出一份「速览报告」,**复用本章前面的函数**:

```python
{
    "count":       元素个数,
    "min":         最小值(用 float('inf') 哨兵一趟扫描,不准调 min()),
    "kth_largest": 第 k 大(复用 §34.4 的 kth_largest),
    "prefix_sums": 前缀和(复用 §34.8 的 running_sum),
}
```

### 为什么练 inf 哨兵而不是 min()

`min(nums)` 当然一行能求最小值,但面试常要求「**一趟循环同时干多件事**」(比如同时求 min 和 max、同时计数),那时内置函数帮不了你,`float('inf')` 哨兵是标准起手式:

### Java 对照最小例

```java
// Java:用类型的极值做哨兵
int min = Integer.MAX_VALUE;          // 「比任何 int 都大」
for (int x : nums) {
    if (x < min) min = x;
}
```

```python
# Python:float('inf') 比任何数都大,而且和 int 比较自如
min_val = float("inf")
for x in nums:
    if x < min_val:
        min_val = x
```

### 真实场景例(已验证)

```python
array_report([3, 1, 4, 1, 5], 2)
# {"count": 5, "min": 1, "kth_largest": 4, "prefix_sums": [3, 4, 8, 9, 14]}
#   min: inf→3→1(1<3 刷新),后面 4,1,5 都刷不动 1

array_report([-3, -1, -2], 1)
# min = -3 —— inf 哨兵能被负数正常刷新;错用 0 初始化这里就露馅

array_report([], 1)
# {"count": 0, "min": None, "kth_largest": None, "prefix_sums": []} —— 约定
```

### ❌ 错误写法 → ✅ 正确写法

```python
# ❌ 用 0 或 nums[0] 当哨兵初值——负数数组 / 逻辑都容易错
min_val = 0                           # 数组全是负数时,0 永远是「最小值」!

# ❌ 在空数组上直接扫——返回 inf 泄漏给调用方
# ✅ 先特判空数组(作业约定 min=None),再进扫描

# ✅ float('inf') 起手;同时求 max 就用一对哨兵
min_val, max_val = float("inf"), float("-inf")
for x in nums:
    if x < min_val: min_val = x
    if x > max_val: max_val = x
```

> 🟡 **Java 对比**:`float('inf')` ≈ `Double.POSITIVE_INFINITY`,但 Python 里它和 int/float 混比都没问题(`1 < float('inf')` 恒 True),不用区分 `Integer.MAX_VALUE`/`Long.MAX_VALUE` 一堆类型极值。`math.inf` 和 `float('inf')` 是**同一个东西**,用哪个都行。DP 初始化也常用它:`dp = [float('inf')] * (n+1)`(「不可达」语义,Ch39 零钱兑换会见到)。
>
> **常踩的坑**:① `inf` 是 **float**,参与运算结果变 float——报告里 `min` 最终是 int(被数组元素刷新过),但空数组时还是 inf,所以作业约定空数组返回 None 而不是把 inf 漏出去。② 求最大值用 `-inf`(或 `float('-inf')`),别用 `0`。③ `float('inf') > 任何数`、`float('-inf') < 任何数`,包括它们自己之外的一切;`inf == inf` 为 True。

**复杂度**:扫描 O(n);加上 kth_largest 的 O(n log k) 和 running_sum 的 O(n),整体 O(n log k)。

---

## §34.12 Java 老手常踩的坑(汇总)⚠️(不出题)

1. **分组还在 `if key not in dict`** → `defaultdict(int/list)` 声明默认值,直接 `+=`/`append`(§34.3)。
2. **用 `list.pop(0)` 当队列** → 头部删除 O(n);队列用 `deque`,定长用 `deque(maxlen=n)`(§34.5)。
3. **`nlargest(k,...)` 忘加 `[-1]`** → 返回的是降序列表,不是单值(§34.4)。
4. **对乱序数组用 bisect** → 前提是已升序,它**不检查**(§34.6)。
5. **`bisect_left` / `bisect_right` 混淆** → 有重复时插入点不同,LC35 用 left(§34.6)。
6. **元组 key 给字符串加负号** → `-"amy"` 直接 TypeError;字符串降序靠稳定性排两次(§34.7)。
7. **`xs = xs.sort()`** → `list.sort()` 原地排返回 `None`;要新列表用 `sorted()`(§34.7)。
8. **`accumulate` 忘加 `list()`** → 返回的是迭代器,不是列表,用一次就没(§34.8)。
9. **轮转忘挡空数组** → `k % 0` 是 ZeroDivisionError;也别依赖 `-0` 的碰巧正确(§34.9)。
10. **`@lru_cache` 参数不可 hash** → list 参数会崩,改 tuple 或手动 memo(§34.10)。
11. **最值扫描用 `0` 当哨兵** → 负数数组全错;用 `float('inf')` / `float('-inf')`(§34.11)。
12. **以为 stdlib 能替代算法** → 它只替代样板,DP/回溯/图论还得自己想(§34.1)。

---

## 📚 延伸阅读(本章不出题)

- **`dict.fromkeys` 有序去重**:`list(dict.fromkeys(items))` = Java 的 `LinkedHashSet` 语义(dict key 去重 + 3.7+ 保插入序)。**别用 `list(set(items))`**——set 不保序。Ch02 已讲过 dict 有序,这里记住这个组合拳即可。
- **`itertools` 更多刷题件**:`pairwise(xs)`(3.10+)给相邻对 `(xs[0],xs[1]), (xs[1],xs[2])...`,「比较相邻元素」类题不用写下标;`combinations(xs, 2)` 枚举所有两两组合(回溯章 Ch40 的前菜)。
- **heapq 手写堆**:`heapify(nums)` 原地建堆 + `heappush/heappop` 弹最小值——`nlargest` 搞不定的花式 top-k(如带 key、数据流持续推送)用它,LC703 正式版就是手写堆。
- **`bisect` 家族的 insort**:`insort_left(nums, x)` 找到插入点并插入,维护「一直有序」的列表。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `char_frequency` | Counter 频次统计 + top-k | 🔴 |
| `sum_by_category` | defaultdict 分组免判空 | 🔴 |
| `kth_largest` | heapq 第 k 大 | 🟢 |
| `moving_averages` | deque(maxlen) 定长滑窗 | 🟡 |
| `search_insert_pos` | bisect 二分插入点 | 🟢 |
| `sort_students` | sorted + key 元组多键 | 🟡 |
| `running_sum` | accumulate 前缀和 | 🔴 |
| `rotate_array` | 切片 + 星号轮转 | 🟡 |
| `fib` | lru_cache 记忆化 | 🔴 |
| `array_report` | 综合:inf 哨兵 + 复用 | 🟡 |

```bash
uv run pytest 06_leetcode/ch34/test_ch34_assignment.py -v
```

全绿 = 你掌握了 Ch34,Pythonic 刷题入门钥匙到手。

---

## ✅ 自测

- [ ] 能说出 10 件 stdlib 利器各自替代 Java 的什么写法
- [ ] 知道 `Counter(text).most_common(3)` 空输入返回 `[]`,平局按首次出现序
- [ ] 知道 `defaultdict(int)` 的 `int` 是工厂函数,并能说出 `defaultdict(list)` 干嘛用
- [ ] 知道 `heapq.nlargest(k, nums)` 返回列表要 `[-1]`,并能说清何时该全排序
- [ ] 知道 `deque(maxlen=n)` 满了自动踢旧,`list.pop(0)` 为什么是坑
- [ ] 知道 `bisect_left` 统一「查找」和「插入点」,前提是数组升序
- [ ] 会用 `key=lambda r: (-r[1], r[0])` 多键排序,知道字符串键不能取负
- [ ] 知道 `accumulate` 返回迭代器要 `list()`,知道 `initial=0` 的用处
- [ ] 会写 `nums[-k:] + nums[:-k]` 轮转,记得挡空数组和取模
- [ ] 会用 `@lru_cache(maxsize=None)`,知道参数必须 hashable
- [ ] 会用 `float('inf')` 做一趟扫描的哨兵,知道空数组要特判
- [ ] 10 个作业全绿

## 🎓 费曼挑战

1. 「Python 刷题为什么爽?举 3 个 stdlib 一行秒杀 Java 样板的例子。」— 重读 §34.1
2. 「`defaultdict(int)` 凭什么能免判空?它和 `dict.get(k, 0)` 差在哪?」— 重读 §34.3
3. 「`deque(maxlen=n)` 和 Java `ArrayDeque` 最大的差异是什么?`list.pop(0)` 为什么慢?」— 重读 §34.5
4. 「`key=lambda r: (-r[1], r[0])` 为什么能实现『分数降序、同分名字升序』?字符串要降序怎么办?」— 重读 §34.7
5. 「`@lru_cache` 做了什么?Java 里实现同样效果要写什么?它有什么局限?」— 重读 §34.10

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步:Ch35 双指针/滑动窗口

本章是「工具箱总览」——你尝到了 stdlib 一行秒杀的甜头。但**真·算法题**光靠 stdlib 不够。Ch35 进入题型专项:**双指针**(对撞/快慢)和**滑动窗口**——LC 最高频套路(两数之和、三数之和、最长无重复子串)。从「用工具」升级到「想策略」。本章的 `deque(maxlen)` 和「窗口」直觉,到那边马上会用上。
