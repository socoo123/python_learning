# Ch36 · 哈希表 / 前缀和

> **预计**:1 天 ｜ **前置**:Ch34(Pythonic 刷题利器)、Ch35(双指针/滑动窗口)｜ **M6 重点**
> **目标**:掌握哈希表把 **O(n²) 暴力降到 O(n)** 的核心套路。Python 用 `dict` / `defaultdict` / `Counter` 一行初始化;Java 要 `new HashMap<>()` 反复 `put`/`get`/`containsKey`。

> 📐 **本教程的契约**:§36.2–§36.5 对应作业 4 个函数,**纯 stdlib**(`collections.defaultdict`),不 import 外部库。

---

## 🗺️ 本章地图:作业 ↔ 知识点对应表

| 作业(函数) | 对应小节 | 核心知识点 | LC 题号 |
|------|----------|-----------|---------|
| `two_sum` | §36.2 | 哈希查 complement,O(n) 一次遍历 | LC1 |
| `group_anagrams` | §36.3 | 排序后的字符串作 key + `defaultdict(list)` 聚合 | LC49 |
| `subarray_sum` | §36.4 | 前缀和 + 哈希记次数,`{0:1}` 初始项的玄机 | LC560 |
| `longest_consecutive` | §36.5 | `set` 去重,只从「序列起点」开始数 | LC128 |

---

## ⏱️ 学习路径:费曼五步(约 60 分钟)

① **预览猜** → ② **写 assignment** → ③ **pytest 红绿** → ④ **费曼(对空气讲一遍)** → ⑤ **存闪卡**。

每道题:先猜思路 → 看本节 → 默写实现 → 跑测试 → 合上教程讲一遍「为什么这么做」。

---

## ① 预览猜(先别看答案)

1. `two_sum`:给你一个数组和一个 target,找两个数的下标使它们之和 = target。暴力双循环 O(n²)。能不能只扫一遍?
2. `group_anagrams`:把「字母相同、顺序不同」的单词归到一组(`eat/tea/ate` 一组)。怎么给每个词算一个「分组指纹」?
3. `subarray_sum`:数一数有多少个**连续子数组**之和 = k。前缀和 `prefix[j]-prefix[i] = k` 那个等式怎么用?为什么不能像 Ch35 那样滑窗?
4. `longest_consecutive`:找最长连续整数序列的长度(`1,2,3,4` 长 4)。排序是 O(n log n),能不能 O(n)?关键是「从哪开始数」?

想完再往下看。

---

## §36.1 哈希表的「降维」威力(讲透)🟢

哈希表(`dict` / `HashMap`)的杀手锏:**把「找一个东西在不在」从 O(n) 线性扫,降到 O(1) 平均**。

很多题的暴力解都是嵌套循环「外层固定一个、内层再找一个匹配的」→ O(n²)。一旦你意识到「内层那个查找」可以用哈希表 O(1) 完成,整个算法就降到 **O(n)**。本章四题全是这个套路的不同变体:

| 题 | 暴力 | 哈希优化 | 关键洞察 |
|----|------|----------|----------|
| two_sum | 双循环 O(n²) | dict 查 complement | `target - num` 在不在已扫过的里 |
| group_anagrams | 两两比较 O(n²·L) | dict 按 key 聚合 | 异位词的「规范形式」相同 |
| subarray_sum | 枚举所有子数组 O(n²) | dict 记前缀和次数 | `prefix[j]-prefix[i]=k` ⟺ `prefix[i]=prefix[j]-k` |
| longest_consecutive | 排序 O(n log n) | set O(1) 查 | 只从「起点」数,不重复 |

> 🟢 **Java 老手秒懂**:`HashMap<Integer,Integer> map = new HashMap<>();` → `map.put(k,v)` / `map.get(k)` / `map.containsKey(k)`。Python 对应 `d = {}` → `d[k] = v` / `d.get(k)` / `k in d`。**零样板**——没有泛型尖括号,没有 `.containsKey`,直接 `in`。

> 🔴 **Python 特有**:
> - `defaultdict(list)`——不存在的 key 自动建空 list,省掉「先 `if k not in d: d[k]=[]` 再 append」三行。
> - `Counter`——`Counter([1,1,2])` 一行出 `{1:2, 2:1}`(本章 §36.3 也会用到)。
> - `dict.get(k, default)`——键不存在时返回 default,**不会抛 KeyError**,这在前缀和题里极其顺手。
> - 字典推导 `{k: f(v) for k,v in d.items()}`、3.7+ 保证插入顺序(本章不强依赖顺序)。

---

## §36.2 LC1 两数之和 `two_sum`(对应)🟢

> **题面**:给定整数数组 `nums` 和整数 `target`,返回和为 `target` 的两个元素的下标。题面保证恰好有一个解,同一元素不能重复用。

### 为什么这么做(讲透)

暴力:两层循环 `for i: for j>i: if nums[i]+nums[j]==target` → O(n²)。

观察:扫到 `nums[i]` 时,我们要找的是「前面有没有一个数 = `target - nums[i]`」。**这个查找是 O(n²) 的唯一来源**,用哈希表换成 O(1) 就行。

```python
def two_sum(nums, target):
    seen = {}  # 值 -> 下标
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:          # O(1) 查
            return [seen[complement], i]
        seen[num] = i
    return []
```

**为什么不先全部存进 dict 再查**:边扫边查能天然保证「两个下标不同」(查的是已扫过的,当前 i 还没登记),且只遍历一次。先全存会引入「同元素用两次」的坑(如 `nums=[3], target=6`,会误以为 3+3 命中),还得加下标判断。

### Java 对比

```java
Map<Integer,Integer> seen = new HashMap<>();
for (int i = 0; i < nums.length; i++) {
    int complement = target - nums[i];
    if (seen.containsKey(complement)) {           // ← Python 一行 `in`
        return new int[]{seen.get(complement), i};
    }
    seen.put(nums[i], i);                          // ← Python 一行 `seen[num] = i`
}
```

> 🟢 Java 老手秒懂:逻辑一模一样,Python 省了 `containsKey`/`put`/`get` 三个方法名,变成 `in`/`[]=`/`[]`。**`enumerate` 一行同时拿 index 和 value**,比 Java 的 `for(int i...)`+`nums[i]` 干净。

> 🟡 **差异**:`enumerate(nums)` 默认从 0 开始下标;Java 是手写 `for(int i=0; i<nums.length; i++)`。
>
> 🔴 **Python 特有**:`complement in seen` 直接判键存在,不像 Java 必须 `.containsKey()`。

### 复杂度

- 时间 **O(n)**:一次遍历,每次 dict 查/插平均 O(1)。
- 空间 **O(n)**:最坏把所有数存进 dict。

### 常见坑 ⚠️

1. **返回下标不是值**——题面要 `[i, j]`,不是 `[nums[i], nums[j]]`。
2. **不能先全存 dict 再查**——会允许「同元素用两次」。要边扫边查。
3. **重复元素**(`[3,3], 6`):第一个 3 先登记,扫到第二个 3 时 `complement=3 in seen` 命中,返回 `[0,1]`,正确。别担心「同值会被覆盖」——覆盖之前已经查过了。

> ✅ 做 `two_sum`:边扫边查,`if (target-num) in seen: return [seen[...], i]`,否则登记。

---

## §36.3 LC49 字母异位词分组 `group_anagrams`(对应)🟡

> **题面**:给定字符串数组,把「字母异位词」(字母相同、顺序不同)归为一组。返回分组列表。

### 为什么这么做(讲透)

关键洞察:**互为异位词的字符串,排序后字符序列完全相同**。`sorted("eat")` 和 `sorted("tea")` 都是 `['a','e','t']`,拼成字符串都是 `"aet"`。这个排序结果就是天然的「分组指纹(key)」。

于是:每个词算一个 key → 同 key 的词聚到一组。**分组聚合**是 `defaultdict(list)` 的拿手好戏:

```python
from collections import defaultdict

def group_anagrams(strs):
    buckets = defaultdict(list)       # key 不存在时自动建 []
    for word in strs:
        key = "".join(sorted(word))   # 异位词的规范形式
        buckets[key].append(word)     # 直接 append, 不用判 key 在不在
    return list(buckets.values())
```

`defaultdict(list)` 省掉的三行 Java 样板:

```python
# 普通 dict 写法(啰嗦):
buckets = {}
for word in strs:
    key = "".join(sorted(word))
    if key not in buckets:           # ← 这两行
        buckets[key] = []            # ← 被 defaultdict 自动做了
    buckets[key].append(word)
```

### key 的其它选法

排序当 key 是最直观的(O(L log L),L 是词长)。还有两种常见 key:
- **字符计数 tuple**:`key = tuple(sorted(Counter(word).items()))`,或更紧凑的「26 字母频次 tuple」——O(L),对长词更快,但代码长。
- 进阶题里(超大输入)频次 tuple 更优;本题排序就够。

### Java 对比

```java
Map<String, List<String>> map = new HashMap<>();
for (String w : strs) {
    char[] arr = w.toCharArray();
    Arrays.sort(arr);
    String key = new String(arr);                 // ← Python: "".join(sorted(w))
    map.computeIfAbsent(key, k -> new ArrayList<>()).add(w);  // ← defaultdict 自动做这个
}
return new ArrayList<>(map.values());
```

> 🟡 **差异**:`"".join(sorted(word))` 一行搞定「字符数组排序再拼回字符串」,Java 要 `toCharArray` → `Arrays.sort` → `new String(arr)` 三步。
>
> 🔴 **Python 特有**:`defaultdict(list)` + `computeIfAbsent` 的角色由「不存在的 key 自动建空 list」一步完成。`list(buckets.values())` 一行把 dict 的所有 value 转成 list of lists。

### 复杂度

- 时间 **O(n · L log L)**:n 个词,每个词排序 O(L log L)。L 为最长词长。如果用频次 tuple 当 key 可降到 O(n·L)。
- 空间 **O(n·L)**:存所有词。

### 常见坑 ⚠️

1. **key 要是不可哈希的才能当 dict key**:排序结果是 list 不能直接当 key,要 `"".join(...)` 拼成字符串(或 `tuple(...)`)。
2. **空字符串 `""`**:sorted 出来还是 `[]`,拼成 `""`,单独成一组 `[[""]]`,正确处理即可。
3. **题面不强制组内/组间顺序**——测试时用「每组内排序 + 组间再排序」做规整后再比,别直接 `==`。

> ✅ 做 `group_anagrams`:`key = "".join(sorted(word))` → `defaultdict(list).append` → `list(values())`。

---

## §36.4 LC560 和为 K 的子数组个数 `subarray_sum`(对应)🔴

> **题面**:给定整数数组 `nums` 和整数 `k`,返回和等于 `k` 的**连续子数组**个数。

### 前缀和(讲透这个概念)

**前缀和** `prefix[i]` = `nums[0] + nums[1] + ... + nums[i-1]`,约定 `prefix[0] = 0`(空前缀)。则任意连续子数组 `nums[i..j]` 之和 = `prefix[j+1] - prefix[i]`。

```
nums:   [1, 2, 3]
prefix: [0, 1, 3, 6]      # prefix[0]=0, prefix[1]=1, prefix[2]=3, prefix[3]=6
nums[1..2] = 2+3 = 5 = prefix[3] - prefix[1] = 6 - 1
```

子数组和 = `k` 等价于 **`prefix[j] - prefix[i] == k`**,即 **`prefix[i] == prefix[j] - k`**。

### 为什么用哈希(讲透)

我们要数「有多少对 (i, j) 使 prefix[j] - prefix[i] = k」。固定 j,等价于数「有多少个 i < j 满足 prefix[i] = prefix[j] - k」。

**这就是一次 O(1) 哈希查找!** 维护一个 dict:`{前缀和值: 出现次数}`,扫到 j 时:

```python
count += prefix_count.get(cur - k, 0)   # 多少个历史前缀和 == cur-k, 就多少个子数组和=k
prefix_count[cur] = prefix_count.get(cur, 0) + 1   # 把当前前缀和登记
```

整体:

```python
def subarray_sum(nums, k):
    count = 0
    prefix_count = {0: 1}   # ← 关键: 前缀和 0 出现过一次 (空前缀)
    cur = 0
    for num in nums:
        cur += num
        count += prefix_count.get(cur - k, 0)
        prefix_count[cur] = prefix_count.get(cur, 0) + 1
    return count
```

### `{0: 1}` 初始项的玄机(必懂)

为什么要预置 `prefix_count = {0: 1}`?

考虑 `nums=[5], k=5`:扫到 5,`cur=5`,`cur-k=0`。如果不预置 `{0:1}`,查 `prefix_count[0]` 会得 0,**漏数了「整个前缀本身和就是 k」的子数组**(从下标 0 开始的子数组)。预置 `{0:1}` 表示「前缀和 0 出现过一次(空前缀,对应 prefix[0])」,这样 `prefix[j] - prefix[0] = cur - 0 = cur = k` 就能命中。

> 记忆口诀:**前缀和问题,dict 初始要塞 `{0: 1}`,否则从下标 0 开始的子数组永远漏数。** 这是这类题最高频的坑。

### 为什么不能像 Ch35 那样滑窗?

Ch35 滑动窗口要求「窗口扩/缩时和单调变化」——即 `nums` 全正。本题 `nums` **可含负数**,前缀和不单调,缩窗不一定让和变小、扩窗不一定让和变大,**滑窗失效**。哈希前缀和是通用解。

### Java 对比

```java
int count = 0, cur = 0;
Map<Integer,Integer> map = new HashMap<>();
map.put(0, 1);                                    // ← Python: {0: 1}
for (int num : nums) {
    cur += num;
    count += map.getOrDefault(cur - k, 0);        // ← Python: .get(cur-k, 0)
    map.merge(cur, 1, Integer::sum);              // ← Python: pc[cur] = pc.get(cur,0)+1
}
```

> 🔴 **Python 特有**:
> - `dict.get(k, default)` 等价 Java `getOrDefault`,一行写完「查不到给默认值」。
> - 字面量初始化 `{0: 1}` 比 Java `new HashMap<>(); map.put(0,1);` 简洁太多。
> - `prefix_count[cur] = prefix_count.get(cur,0) + 1` 一行「不存在则 0、再 +1、写回」,Java 要 `merge` 或手写 if-else。

> 🟡 **差异**:`count += prefix_count.get(cur - k, 0)` 这行是「查询并累加」,Java 要么 `getOrDefault` 要么先判 null。

### 复杂度

- 时间 **O(n)**:一次遍历,每次 dict 操作平均 O(1)。
- 空间 **O(n)**:最坏每个前缀和都不同。

### 常见坑 ⚠️

1. **忘预置 `{0:1}`**——从下标 0 开始的子数组全部漏数。这是本题第一坑。
2. **顺序错了**(先登记 cur 再查 cur-k)——会把当前元素自己也算进去(同元素用两次)。必须**先查后登记**。
3. **误用滑窗**——nums 有负数时滑窗失效,必须哈希前缀和。
4. **返回个数不是子数组本身**——题面要「个数」(int),不是 list。

> ✅ 做 `subarray_sum`:`{0:1}` 起手 → 每步 `cur+=num` → `count+=pc.get(cur-k,0)` → `pc[cur]+=1`(先查后登记)。

---

## §36.5 LC128 最长连续序列 `longest_consecutive`(对应)🟡

> **题面**:给定未排序整数数组,返回最长连续元素序列的长度(如 `[100,4,200,1,3,2]` 的最长连续序列是 `[1,2,3,4]`,长 4)。要求 **O(n)**。

### 为什么不能排序

排序是 O(n log n),题目要求 O(n)。**不能用排序。** 只能用哈希(`set` 去重 + O(1) 查询)。

### 关键洞察:只从「序列起点」开始数

把所有数塞进 `set`(O(1) 查「在不在」)。对每个数 `n`,如果 `n-1` 也在 set 里,说明 `n` 不是序列起点(它前面还有更小的),**跳过**——因为从 `n-1` 那边数的时候会覆盖到 `n`,从 `n` 数就重复了。

只有当 **`n-1` 不在 set 里**(`n` 是某个连续序列的最小值)时,才从 `n` 开始往 `n+1, n+2, ...` 数,数到不在 set 为止,记录长度。

```python
def longest_consecutive(nums):
    num_set = set(nums)     # 去重 + O(1) 查
    best = 0
    for n in num_set:
        if n - 1 in num_set:
            continue        # n 不是起点, 跳过
        length = 1
        m = n + 1
        while m in num_set: # 从起点往后数
            length += 1
            m += 1
        best = max(best, length)
    return best
```

### 为什么是 O(n)

直觉怀疑:外层 for + 内层 while,会不会 O(n²)?

不会。每个元素 `x` 被「内层 while」访问到**当且仅当**它是某个从起点延伸的序列的一部分,且**只被那一个起点对应的 while 访问一次**(因为别的非起点元素都 `continue` 了)。所以内层 while 的总执行次数 = 所有「非起点但属于某序列」的元素个数 ≤ n。整体 O(n) + O(n) = **O(n)**。

### Java 对比

```java
Set<Integer> set = new HashSet<>(nums.length);     // ← Python: set(nums)
for (int x : nums) set.add(x);
int best = 0;
for (int n : set) {
    if (set.contains(n - 1)) continue;             // ← Python: n-1 in num_set
    int len = 1, m = n + 1;
    while (set.contains(m)) { len++; m++; }        // ← Python: while m in num_set
    best = Math.max(best, len);
}
```

> 🟡 **差异**:`set(nums)` 一行把 list 去重转 set,Java 要 `new HashSet<>(Arrays.asList(...))` 或循环 `add`。`n - 1 in num_set` 直接判存在,Java 是 `set.contains(...)`。
>
> 🔴 **Python 特有**:`set(nums)` 构造器吃任何可迭代对象;`while m in num_set:` 的 `in` 直接当循环条件,极简。

### 复杂度

- 时间 **O(n)**:见上分析。
- 空间 **O(n)**:set 存所有数。

### 常见坑 ⚠️

1. **忘跳过非起点元素**——不 `continue` 就退化成 O(n²)(每个数都往后续数一遍,大量重复)。
2. **遍历 `nums` 而不是 `num_set`**——`nums` 有重复元素时,同一个起点会数多次(虽然答案对,但浪费时间)。应遍历去重后的 `num_set`。
3. **起点判断方向反了**——是 `n-1 not in set`(`n` 是起点)才数,**不是** `n+1 not in set`。数列往大数方向延伸。
4. **空数组**——返回 0,`best=0` 初值天然处理。

> ✅ 做 `longest_consecutive`:`set(nums)` → 只对 `n-1 not in set` 的起点 → `while m in set: 数` → `max(best, length)`。

---

## §36.6 四题对比总结(讲透)

| 题 | 哈希表的角色 | dict 存什么 | 关键操作 |
|----|-------------|-------------|----------|
| two_sum | 查 complement | `{值: 下标}` | `complement in seen` |
| group_anagrams | 按 key 聚合 | `defaultdict(list): {key: [词...]}` | `buckets[key].append` |
| subarray_sum | 计数(值→出现次数) | `{前缀和: 次数}` | `count += pc.get(cur-k, 0)` |
| longest_consecutive | O(1) 成员查询 | `set` | `n-1 in num_set` |

四个截然不同的用法:**当 map 用 / 当 group-by 用 / 当频次表用 / 当 set 用**。哈希表就是「以查询换遍历」的万能瑞士军刀。

---

## §36.7 Pythonic 技巧速查(本章用到)🔴

| 技巧 | 代码 | 替代的 Java 样板 |
|------|------|-----------------|
| 字面量建 dict | `d = {"a": 1}` 或 `d = {}` | `Map<K,V> d = new HashMap<>();` |
| 判键存在 | `k in d` | `d.containsKey(k)` |
| 安全取值(带默认) | `d.get(k, default)` | `d.getOrDefault(k, default)` |
| 自动建默认值的 dict | `defaultdict(list)` / `defaultdict(int)` | `computeIfAbsent(k, k->new ArrayList<>())` |
| 计数 | `Counter(seq)` | 手写循环 `map.merge(x,1,Integer::sum)` |
| list 去重 + O(1) 查 | `set(seq)` | `new HashSet<>(seq)` |
| list 转字符串拼接 | `"".join(parts)` | `String.join("", parts)` 或 `StringBuilder` |
| 同时拿 index+value | `for i, x in enumerate(seq)` | `for (int i=0; i<a.length; i++) x=a[i]` |
| 排序副本 | `sorted(seq)` | `Arrays.sort(arr.clone())` |

---

## §36.8 Java 老手常踩的坑 ⚠️

1. **`{0:1}` 忘记预置**(§36.4):前缀和题第一坑,从下标 0 起的子数组全漏。
2. **`defaultdict` 和普通 dict 混用**:普通 `dict` 不存在 key 会 `KeyError`,而 `d[k] += 1` 在 Java 里靠 `getOrDefault` 才安全;Python 直接 `defaultdict(int)` 或 `d.get(k,0)+1`。
3. **把可变对象当 key**:list 不能当 dict key(不可哈希),要 `tuple(...)` 或 `"".join(...)`(§36.3 异位词 key)。
4. **遍历有重复的 nums 而非去重 set**(§36.5):浪费时间。
5. **顺序错(先登记后查)**:two_sum / subarray_sum 都要**先查后登记**,否则同元素用两次。
6. **滑窗乱用**:有负数的子数组和题不能滑窗,要哈希前缀和。
7. **返回下标 vs 值 vs 个数搞混**:two_sum 返下标、group_anagrams 返分组、subarray_sum 返个数——看清题面。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `two_sum` | dict 查 complement,O(n) | 🟢 |
| `group_anagrams` | 排序 key + `defaultdict` 聚合 | 🟡 |
| `subarray_sum` | 前缀和 + dict 计数,`{0:1}` 玄机 | 🔴 |
| `longest_consecutive` | set + 只从起点数,O(n) | 🟡 |

```bash
uv run pytest 06_leetcode/ch36/test_ch36_assignment.py -v
```

全绿 = 掌握 Ch36 的哈希套路。

---

## ✅ 自测

- [ ] 能说清哈希表怎么把 O(n²) 降到 O(n)(「查询换遍历」)
- [ ] `two_sum` 边扫边查,知道为什么不能先全存 dict
- [ ] `group_anagrams` 会用 `defaultdict(list)` + `"".join(sorted(word))` 作 key
- [ ] `subarray_sum` 知道前缀和 `prefix[j]-prefix[i]=k`、`{0:1}` 初始项的玄机、为什么有负数不能滑窗
- [ ] `longest_consecutive` 知道为什么只从「起点」(n-1 不在 set)开始数才 O(n)
- [ ] 4 个作业全绿

## 🎓 费曼挑战

1. 「为什么 `subarray_sum` 必须 `prefix_count={0:1}` 预置?不预置会漏什么?」— 重读 §36.4
2. 「`longest_consecutive` 为什么是 O(n) 而不是 O(n²)?内层 while 不会重复数吗?」— 重读 §36.5
3. 「`two_sum` 为什么不能先把所有数存进 dict 再查?」— 重读 §36.2
4. 「`group_anagrams` 除了排序当 key,还有什么 key 写法?时间复杂度差别?」— 重读 §36.3

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步:Ch37 栈 / 队列 / 单调栈

哈希表是「以查询换遍历」。下一章栈/队列是 **LIFO/FIFO** 的顺序结构,而**单调栈**能在 O(n) 内解决「下一个更大元素」这类题(像 LC739 每日温度、LC42 接雨水)。从「查」到「维护单调顺序」。
