# Ch36 · 哈希表 / 前缀和

> **预计**:1 天 ｜ **前置**:Ch34(stdlib 工具箱:`Counter`/`defaultdict`)、Ch35(双指针/滑动窗口)｜ **M6 重点**
> **目标**:掌握哈希表把 **O(n²) 暴力降到 O(n)** 的核心套路——「以查询换遍历」。Python 用 `dict` / `defaultdict` / `Counter` / `set` 一行初始化;Java 要 `new HashMap<>()` 反复 `put`/`get`/`containsKey`。本章 6 道 LeetCode 经典题,覆盖哈希表的 **6 种角色**:计数指纹 → 查表 → 分组聚合 → 频次表 → 最早下标 → 成员查询。

> 📐 **本教程的契约**:§36.2–§36.7 每节**精确对应**作业里的一个函数,讲过的才考,考的必讲过。§36.1 是开胃、§36.8/§36.9 是总结与坑清单,讲透不出题。卡住时按对应表回查小节。

---

## 🗺️ 本章地图

读完这章 + 完成作业,你将能够:
- 用 `Counter(s) == Counter(t)` 一行判异位词,说清为什么 `set` 会蒙混过关
- 用「边扫边查」写 `two_sum`,说清为什么不能先全存 dict 再查
- 用 `defaultdict(list)` + `"".join(sorted(word))` 做分组聚合
- 用「前缀和 + `{前缀和: 次数}`」数出和为 k 的子数组,记住 `{0: 1}` 预置的玄机
- 用「0→-1 变换 + `{前缀和: 最早下标}`」求最长平衡子数组,说出它和上一题 dict 里存的东西有何不同
- 用 `set` + 「只从序列起点数」把 LC128 做到 O(n)

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业(函数) | 对应小节 | 核心知识点 | LC 题号 |
|------|----------|-----------|---------|
| `is_anagram` | §36.2 | `Counter` 计数指纹判异位词 | LC242 |
| `two_sum` | §36.3 | dict `{值: 下标}`,边扫边查(先查后登记) | LC1 |
| `group_anagrams` | §36.4 | 排序 key + `defaultdict(list)` 聚合 | LC49 |
| `subarray_sum` | §36.5 | 前缀和 + `{前缀和: 次数}`,`{0: 1}` 预置 | LC560 |
| `find_max_length` | §36.6 | 0→-1 变换 + `{前缀和: 最早下标}`,只记最早 | LC525 |
| `longest_consecutive` | §36.7 | `set` 成员查询,只从「序列起点」开始数 | LC128 |

---

## ⏱️ 学习路径:费曼五步(约 70 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(3分钟) | 下面 6 个问题,先猜答案 | 本页 ① |
| ② 先动手 | 打开 `ch36_assignment.py`,**先试着写**(别看教程) | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清「哈希表以查询换遍历」 | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性原则**:别通读!先猜 ① → 去 ② 写作业 → **哪题卡了,回对应 § 查** → 改 → 再跑。

---

## ① 预览猜(先想,别急着翻答案)

1. 判断两个单词是不是「字母异位词」(`anagram`/`nagaram`)——Java 排序 char 数组再 `Arrays.equals`,Python 能不能一行?用 `set` 判为什么会被 `"aab"` vs `"abb"` 打脸?
2. `two_sum`:找两个数的下标使其和 = target。暴力双循环 O(n²),只扫一遍怎么做?为什么不能先把所有数存进 dict 再查?
3. `group_anagrams`:给每个词算一个「分组指纹」把异位词聚到一起。指纹用什么?sorted 出来的 list 能直接当 dict 的 key 吗?
4. `subarray_sum`:数有多少个**连续子数组**和 = k。前缀和等式 `prefix[j] - prefix[i] = k` 怎么变成一次 O(1) 查询?为什么 dict 初始要塞 `{0: 1}`?
5. `find_max_length`:0 和 1 个数相等的最长连续子数组。把 0 换成什么就能套用上一题的前缀和?这题 dict 里存的为什么不是「次数」而是「最早下标」?
6. `longest_consecutive`:不准排序(O(n log n)),怎么 O(n) 找最长连续整数序列?为什么「只从起点开始数」就不会退化成 O(n²)?

> 猜完带着验证心态进入正文。第 4、5 题是 🔴(前缀和 + 哈希组合),是本章最值钱的套路。

---

## §36.1 总览:哈希表的「降维」套路(不出题)🟡

哈希表的杀手锏:**把「找一个东西在不在」从 O(n) 线性扫,降到 O(1) 平均**。

很多题的暴力解都是嵌套循环:「外层固定一个、内层再找一个匹配的」→ O(n²)。一旦你意识到「内层那个查找」可以用哈希表 O(1) 完成,整个算法就降到 **O(n)**。本章 6 题全是这个套路的变体:

| 题 | 暴力 | 哈希优化 | dict / set 的角色 |
|----|------|----------|------------------|
| is_anagram (LC242) | 排序比较 O(L log L) | `Counter` 一行 | **计数指纹** |
| two_sum (LC1) | 双循环 O(n²) | dict 查 complement | **查表** `{值: 下标}` |
| group_anagrams (LC49) | 两两比较 O(n²·L) | dict 按 key 聚合 | **分组** `{指纹: [词...]}` |
| subarray_sum (LC560) | 枚举所有子数组 O(n²) | dict 记前缀和次数 | **频次表** `{前缀和: 次数}` |
| find_max_length (LC525) | 枚举所有子数组 O(n²) | dict 记前缀和最早下标 | **最值索引** `{前缀和: 最早下标}` |
| longest_consecutive (LC128) | 排序 O(n log n) | set O(1) 查 | **成员查询** |

### Java 对照最小例

```java
// Java:每用一次哈希表都是一套样板
Map<Integer, Integer> map = new HashMap<>();
map.put(k, v);
if (map.containsKey(k)) { ... }
Integer cnt = map.getOrDefault(k, 0);
map.merge(k, 1, Integer::sum);
```

```python
# Python:字面量 + in + get,零样板
d = {}
d[k] = v
if k in d: ...
d.get(k, 0)                     # 不存在给默认值,不抛 KeyError
```

> 🔴 **Python 特有**(Ch08/Ch34 学过,本章全程在用):
> - `defaultdict(list)` / `defaultdict(int)`——不存在的 key 自动建默认值,省掉「先判 `if k not in d` 再初始化」三行(对应 Java `computeIfAbsent`)。
> - `Counter(seq)`——`Counter("aab")` 一行出 `{'a': 2, 'b': 1}`,频次统计专用 dict 子类。
> - `dict.get(k, default)`——等价 Java `getOrDefault`,前缀和题里极其顺手。
> - `set(seq)`——一行去重 + O(1) 成员查询,对应 Java `new HashSet<>(...)`。

> 🟡 **记住这张地图**:哈希表不是「一种用法」,而是「以查询换遍历」的万能瑞士军刀。做题时先问:**这题 dict 里该存什么?(下标?次数?最早下标?还是只要 set?)** 本章 6 题 = 6 个答案。

---

## §36.2 Counter 计数指纹:is_anagram(LC242)🟢

**题目**:给定两个字符串 `s` 和 `t`,判断 `t` 是否是 `s` 的字母异位词(字母完全相同、顺序不同)。

### Java 对照最小例

```java
// Java:要么排序比较,要么 int[26] 计数
char[] a = s.toCharArray(), b = t.toCharArray();
Arrays.sort(a); Arrays.sort(b);
boolean ok = Arrays.equals(a, b);
```

```python
# Python:Counter 一行——字母频次指纹完全相同 ⟺ 异位词
from collections import Counter

def is_anagram(s: str, t: str) -> bool:
    return Counter(s) == Counter(t)
```

### 真实场景例(已验证)

```python
is_anagram("anagram", "nagaram")   # True
is_anagram("listen", "silent")     # True
is_anagram("rat", "car")           # False —— 字母不同
is_anagram("aab", "abb")           # False —— 字母【种类】相同({a,b}),但次数不同!
is_anagram("ab", "a")              # False —— 长度不同必然 False
is_anagram("", "")                 # True  —— 空串互为异位词
```

### ❌ 错误写法 → ✅ 正确写法

```python
# ❌ 用 set 比——set 只存「有没有」,丢了「几次」
set("aab") == set("abb")           # True —— 误判!两边都是 {'a','b'}

# ❌ Counter 用 & 当「相等」——& 是【交集】(次数取 min),不是判等
Counter("aab") & Counter("abb")    # Counter({'a': 1, 'b': 1}) —— 和判等无关

# ✅ Counter 直接 ==:dict 子类按键值全等比较,次数一字不差才 True
Counter("aab") == Counter("abb")   # False
Counter("anagram") == Counter("nagaram")  # True

# ✅ 备选:sorted 比较也行,O(L log L),面试可作为「不用库」的第二答案
sorted("anagram") == sorted("nagaram")    # True
```

> 🟢 **Java 老手秒懂**:`Counter` ≈ 你手写的 `Map<Character, Integer>` 频次表,只是 stdlib 帮你封装好了,还支持 `==` 直接比较(Java 的 `Map.equals` 也是按内容,语义一致)。
>
> **常踩的坑**:① **set 不能替代 Counter**——`"aab"`/`"abb"` 种类相同但频次不同,set 判等会蒙混过关(测试专门考了这条)。② `Counter` 的 `&`(交集)/`|`(并集)是「次数取 min/max」,**不是判等**。③ 排序法 `sorted(s) == sorted(t)` 也对,但 O(L log L);Counter 是 O(L)。④ 频次指纹这个直觉记住——§36.4 分组题就是它的推广。

**复杂度**:O(L) 时间(L 为字符串长度),O(不同字符数) 空间。

---

## §36.3 dict 查表:two_sum(LC1)🟢

**题目**:给定整数数组 `nums` 和 `target`,返回和为 `target` 的两个元素的**下标**。题面保证恰好一个解,同一元素不能重复用。

### 为什么这么做

暴力:两层循环 `for i: for j>i: if nums[i]+nums[j]==target` → O(n²)。

观察:扫到 `nums[i]` 时,要找的是「前面有没有一个数 = `target - nums[i]`」。**这个查找是 O(n²) 的唯一来源**,用 dict 换成 O(1) 就行——dict 里存 `{值: 下标}`,边扫边查。

### Java 对照最小例

```java
Map<Integer, Integer> seen = new HashMap<>();
for (int i = 0; i < nums.length; i++) {
    int complement = target - nums[i];
    if (seen.containsKey(complement)) {      // ← Python: complement in seen
        return new int[]{seen.get(complement), i};
    }
    seen.put(nums[i], i);                    // ← Python: seen[num] = i
}
```

```python
def two_sum(nums, target):
    seen = {}                                # 值 -> 下标
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:               # O(1) 查
            return [seen[complement], i]
        seen[num] = i                        # 先查后登记
    return []
```

### 真实场景例(已验证)

```python
two_sum([2, 7, 11, 15], 9)        # [0, 1] —— 2+7=9
two_sum([3, 2, 4], 6)             # [1, 2] —— 2+4=6
two_sum([3, 3], 6)                # [0, 1] —— 同值两个,先登记 3→0,扫到第二个命中
two_sum([-1, -2, -3, -4, -5], -8) # [2, 4] —— 负数照常(-3 + -5)
two_sum([10, 20, 30, 40, 50], 90) # [3, 4] —— 注意返回【下标】不是值
```

### ❌ 错误写法 → ✅ 正确写法

```python
# ❌ 先把所有数存进 dict 再统一查——允许「同元素用两次」
seen = {num: i for i, num in enumerate(nums)}
for i, num in enumerate(nums):
    if target - num in seen:
        return [seen[target - num], i]
# 反例:two_sum([3, 2, 4], 6) → i=0 时 complement=3 在 dict 里
# → 返回 [0, 0]!3+3=6 是假的,同一个下标用了两次

# ✅ 边扫边查:查的是【已扫过的】元素,当前 i 还没登记,
#    天然保证两个下标不同,且只遍历一次
for i, num in enumerate(nums):
    if target - num in seen:
        return [seen[target - num], i]
    seen[num] = i
```

> 🟢 **差异**:`enumerate(nums)` 一行同时拿下标和值,比 Java 的 `for(int i...)` + `nums[i]` 干净;`in` 替代 `containsKey`,`[]=` 替代 `put`。
>
> **常踩的坑**:① **返回下标不是值**——题面要 `[i, j]`。② **先查后登记**顺序不能反,也不能先全存——否则同元素用两次。③ 重复元素别怕:`[3,3], 6` 第一个 3 先登记,扫到第二个 3 时命中返回 `[0,1]`——「同值覆盖」发生在命中之后,不影响正确性。④ `dict` 推导式 `{num: i for ...}` 会把同值的下标**覆盖成最后一个**,又一个「先全存」的暗坑。

**复杂度**:时间 **O(n)**(一次遍历,dict 查/插平均 O(1));空间 **O(n)**。

---

## §36.4 defaultdict 分组聚合:group_anagrams(LC49)🟡

**题目**:给定字符串数组,把互为字母异位词的词归为一组,返回分组列表(组内/组间顺序不强制)。

### 为什么这么做

关键洞察(§36.2 的推广):**互为异位词的字符串,排序后字符序列完全相同**——`sorted("eat")` 和 `sorted("tea")` 都得到 `"aet"`。这个排序串就是天然的「分组指纹(key)」。

于是:每个词算 key → 同 key 聚一组。「按 key 分组聚合」正是 `defaultdict(list)` 的拿手好戏。

### Java 对照最小例

```java
Map<String, List<String>> map = new HashMap<>();
for (String w : strs) {
    char[] arr = w.toCharArray();
    Arrays.sort(arr);
    String key = new String(arr);                          // ← Python: "".join(sorted(w))
    map.computeIfAbsent(key, k -> new ArrayList<>()).add(w); // ← defaultdict 自动做这个
}
return new ArrayList<>(map.values());
```

```python
from collections import defaultdict

def group_anagrams(strs):
    buckets = defaultdict(list)     # key 不存在时自动建 []
    for word in strs:
        key = "".join(sorted(word)) # 异位词的规范形式(指纹)
        buckets[key].append(word)   # 直接 append,不判 key 在不在
    return list(buckets.values())
```

### 真实场景例(已验证)

```python
group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
# 等价于 [["eat","tea","ate"], ["tan","nat"], ["bat"]] —— 3 组(顺序不强制)
#   "eat"/"tea"/"ate" 的 key 都是 "aet";"tan"/"nat" 都是 "ant";"bat" 是 "abt"

group_anagrams(["aab", "aba", "baa", "abc"])
# [["aab","aba","baa"], ["abc"]] —— key "aab" 聚 3 个,"abc" 单独

group_anagrams([""])   # [[""]]  —— sorted("")=[],join 得 "",单独成组
group_anagrams([])     # []      —— 空输入空输出
```

### ❌ 错误写法 → ✅ 正确写法

```python
# ❌ 把 sorted 的结果(list)直接当 dict key——list 可变、不可哈希
buckets[sorted(word)].append(word)      # TypeError: unhashable type: 'list'

# ❌ 普通 dict + 每次判空(Java containsKey 思维残留)
buckets = {}
for word in strs:
    key = "".join(sorted(word))
    if key not in buckets:              # ← 这两行
        buckets[key] = []               # ← defaultdict 帮你做了
    buckets[key].append(word)

# ✅ defaultdict(list) 一行建桶;key 用 "".join(...) 拼成 str(不可变、可哈希)
buckets = defaultdict(list)
buckets["".join(sorted(word))].append(word)
```

> 🟡 **差异**:`"".join(sorted(word))` 一行搞定「字符排序再拼回字符串」,Java 要 `toCharArray` → `Arrays.sort` → `new String(arr)` 三步;`list(buckets.values())` 一行把所有分组转成 list of lists。
>
> **常踩的坑**:① **dict key 必须可哈希**——list 不行,要么 `"".join(...)` 成 str,要么 `tuple(sorted(word))`。② key 的备选:排序 O(L log L) 最直观;进阶可用「26 字母频次 tuple」O(L)(如 `tuple(Counter(word) 展开成 26 槽)`),长词更快,本题排序就够。③ 空字符串 `""` 的 key 是 `""`,正常成组,不用特判。④ 返回分组**顺序不强制**——测试里「组内排序 + 组间排序」规整后再比,自己写测试别直接 `==` 原始顺序。

**复杂度**:时间 **O(n · L log L)**(n 个词各排序一次);空间 **O(n·L)**。

---

## §36.5 前缀和 + 频次表:subarray_sum(LC560)🔴

**题目**:给定整数数组 `nums`(可含负数)和整数 `k`,返回和等于 `k` 的**连续子数组个数**。

### 前缀和(讲透这个概念)

**前缀和** `prefix[i]` = `nums[0] + ... + nums[i-1]`,约定 `prefix[0] = 0`(空前缀)。则任意连续子数组 `nums[i..j]` 之和 = `prefix[j+1] - prefix[i]`:

```
nums:   [1, 2, 3]
prefix: [0, 1, 3, 6]      # prefix[0]=0, prefix[1]=1, prefix[2]=3, prefix[3]=6
nums[1..2] = 2+3 = 5 = prefix[3] - prefix[1] = 6 - 1
```

子数组和 = `k` ⟺ `prefix[j] - prefix[i] == k` ⟺ **`prefix[i] == prefix[j] - k`**。

### 为什么用哈希(讲透)

要数「有多少对 (i<j) 使 prefix[j] - prefix[i] = k」。固定 j,等价于数「之前有多少个前缀和 == `prefix[j] - k`」——**这就是一次 O(1) 哈希查询!** 维护 `{前缀和值: 出现次数}`,边扫边查:

### Java 对照最小例

```java
int count = 0, cur = 0;
Map<Integer, Integer> map = new HashMap<>();
map.put(0, 1);                                // ← Python: {0: 1}
for (int num : nums) {
    cur += num;
    count += map.getOrDefault(cur - k, 0);    // ← Python: .get(cur - k, 0)
    map.merge(cur, 1, Integer::sum);          // ← Python: pc[cur] = pc.get(cur, 0) + 1
}
```

```python
def subarray_sum(nums, k):
    count = 0
    prefix_count = {0: 1}        # ← 关键:前缀和 0 出现过一次(空前缀)
    cur = 0
    for num in nums:
        cur += num
        count += prefix_count.get(cur - k, 0)        # 先查
        prefix_count[cur] = prefix_count.get(cur, 0) + 1  # 后登记
    return count
```

### 真实场景例(已验证)

```python
subarray_sum([1, 1, 1], 2)        # 2 —— [1,1](0-1) 和 [1,1](1-2)
subarray_sum([1, 2, 3], 3)        # 2 —— [1,2] 和 [3]
subarray_sum([5], 5)              # 1 —— 整个数组本身,考验 {0:1} 预置
subarray_sum([0, 0, 0], 0)        # 6 —— n(n+1)/2 个非空子数组和全为 0
subarray_sum([1, -1, 1, -1, 1], 0)  # 6 —— 含负数,滑窗做不了,哈希照杀
subarray_sum([1, 2, 3], 100)      # 0
subarray_sum([], 5)               # 0
```

### `{0: 1}` 初始项的玄机(必懂)

为什么要预置 `prefix_count = {0: 1}`?考虑 `nums=[5], k=5`:扫到 5,`cur=5`,`cur-k=0`。不预置的话 `prefix_count.get(0)` 是 0,**漏数了「从下标 0 开始、整个前缀和就是 k」的子数组**。预置 `{0: 1}` 表示「前缀和 0 出现过一次(空前缀)」,`prefix[j] - prefix[0] = cur = k` 就能命中。

> 记忆口诀:**前缀和计数题,dict 起手塞 `{0: 1}`,否则从下标 0 开始的子数组永远漏数。** 这类题第一坑。

### 为什么不能像 Ch35 那样滑窗?

滑窗要求「窗口扩/缩时和单调变化」——即 `nums` 全正。本题**可含负数**,前缀和不单调:缩窗不一定让和变小、扩窗不一定变大,**滑窗失效**。哈希前缀和是通用解。

### ❌ 错误写法 → ✅ 正确写法

```python
# ❌ 忘预置 {0: 1}——从下标 0 起的子数组全漏
prefix_count = {}
# subarray_sum([5], 5) → 0(正确是 1)

# ❌ 先登记后查——把「当前位置自己」也算成一个子数组(空子数组)
for num in nums:
    cur += num
    prefix_count[cur] = prefix_count.get(cur, 0) + 1   # 先登记
    count += prefix_count.get(cur - k, 0)              # 再查
# 反例:subarray_sum([0], 0) → 2(正确是 1):
#   cur=0 先登记使 pc[0]=2,再查 cur-k=0 把刚登记的自己数了进去

# ✅ {0: 1} 起手 + 先查后登记
count += prefix_count.get(cur - k, 0)
prefix_count[cur] = prefix_count.get(cur, 0) + 1
```

> 🔴 **Python 特有**:`dict.get(k, default)` 一行写完「查不到给 0」,等价 Java `getOrDefault`;字面量 `{0: 1}` 比起 `new HashMap<>(); map.put(0,1);` 简洁太多。
>
> **常踩的坑**:① 忘 `{0:1}`(上面)。② 顺序错(上面)——和 two_sum 一样**先查后登记**。③ 误用滑窗(负数失效)。④ 返回**个数**(int),不是子数组列表。

**复杂度**:时间 **O(n)**;空间 **O(n)**(最坏每个前缀和都不同)。

---

## §36.6 前缀和变体:find_max_length(LC525)🔴

**题目**:给定只含 0 和 1 的数组,返回「0 和 1 个数相等」的**最长**连续子数组长度。

### 两个关键洞察

**洞察 1:0→-1 变换。** 把 0 看成 -1,则「0 和 1 个数相等」⟺「子数组和为 0」。问题变成:**和为 0 的最长连续子数组**——前缀和的主场(§36.5)。

**洞察 2:dict 里存的东西变了。** 上一题数「个数」→ dict 存 `{前缀和: 出现次数}`;这题求「最长」→ dict 存 `{前缀和: 最早出现的下标}`。同一前缀和再次出现时,`i - first[cur]` 就是一个平衡子数组长度。**只记最早、绝不覆盖**——下标越早,算出的长度越长。

### Java 对照最小例

```java
Map<Integer, Integer> first = new HashMap<>();
first.put(0, -1);                              // 前缀和 0 在「下标 -1」(空前缀)
int cur = 0, best = 0;
for (int i = 0; i < nums.length; i++) {
    cur += (nums[i] == 1) ? 1 : -1;
    if (first.containsKey(cur)) {
        best = Math.max(best, i - first.get(cur));
    } else {
        first.put(cur, i);                     // 只记最早;Java 也可 putIfAbsent
    }
}
```

```python
def find_max_length(nums):
    first = {0: -1}              # 前缀和 0 的「最早下标」是 -1(空前缀末尾)
    cur = best = 0
    for i, x in enumerate(nums):
        cur += 1 if x == 1 else -1
        if cur in first:
            best = max(best, i - first[cur])
        else:
            first[cur] = i       # 只在第一次出现时登记
    return best
```

### 为什么初始是 `{0: -1}` 而不是 `{0: 1}`

§36.5 数次数,空前缀「出现 1 次」→ `{0: 1}`;本题算长度,空前缀的「下标」是 **-1**(一个元素都还没取)。若从下标 0 开始的整段前缀就平衡(`[0,1]`),`cur=0` 在 `i=1` 处命中,长度 = `1 - (-1) = 2` ✓。没有 `{0: -1}` 就会漏掉所有「从下标 0 开始」的答案。

### 真实场景例(已验证)

```python
find_max_length([0, 1])                # 2 —— 整段平衡:1 - (-1) = 2
find_max_length([0, 1, 0])             # 2 —— [0,1] 或 [1,0]
find_max_length([0, 0, 1, 0, 0])       # 2
find_max_length([0, 1, 1, 0, 1, 1])    # 4 —— 子数组 [0,1,1,0](下标 0-3)
find_max_length([0, 0, 0, 1, 1, 1])    # 6 —— 整组全平衡
find_max_length([1, 0, 1, 0])          # 4 —— 整段;没有 {0:-1} 这题会错成 2
find_max_length([1, 1, 1])             # 0 —— 永远不平衡
find_max_length([])                    # 0
```

手推 `[0, 0, 0, 1, 1, 1]`(0→-1 后 `-1,-1,-1,1,1,1`),`first` 起手 `{0:-1}`:

| i | cur | first 里有没有 | 动作 | best |
|---|-----|---------------|------|------|
| 0 | -1 | 无 | `first[-1]=0` | 0 |
| 1 | -2 | 无 | `first[-2]=1` | 0 |
| 2 | -3 | 无 | `first[-3]=2` | 0 |
| 3 | -2 | 有(下标 1) | `best = max(0, 3-1) = 2` | 2 |
| 4 | -1 | 有(下标 0) | `best = max(2, 4-0) = 4` | 4 |
| 5 |  0 | 有(下标 -1) | `best = max(4, 5-(-1)) = 6` | **6** |

### ❌ 错误写法 → ✅ 正确写法

```python
# ❌ 无条件覆盖 first[cur]——「最早下标」被后来的刷掉,长度算短甚至算错
first[cur] = i                       # 写在 if 外面 / if 里都错
# 反例:[0,1] → i=1 时 cur=0,先覆盖 first[0]=1,长度算成 1-1=0(正确是 2)

# ❌ 抄 560 记次数——求「最长」要的是下标差,次数毫无意义

# ✅ 只在「没见过」时登记;见过就拿最早下标算长度
if cur in first:
    best = max(best, i - first[cur])
else:
    first[cur] = i
```

> 🔴 **和 §36.5 的对照组(费曼点)**:同一个「前缀和 + 哈希」骨架——560 问「多少个」→ dict 存**次数**,每次命中累加;525 问「最长多少」→ dict 存**最早下标**,每次命中取 `i - first[cur]` 刷最大值。**前缀和题先想清楚:dict 的 value 该存什么?初始 `{0: ?}` 的 `?` 是什么语义(次数 1 / 下标 -1)?**
>
> **常踩的坑**:① 忘 0→-1 变换,直接对 0/1 求和找不到目标。② 覆盖最早下标(上面)。③ 初始 `{0: -1}` 写成 `{0: 0}`——从下标 0 起的平衡段长度会少 1。

**复杂度**:时间 **O(n)**;空间 **O(n)**。

---

## §36.7 set 成员查询:longest_consecutive(LC128)🟡

**题目**:给定未排序整数数组,返回最长连续元素序列的长度(如 `[100,4,200,1,3,2]` 的最长连续序列是 `[1,2,3,4]`,长 4)。要求 **O(n)**。

### 为什么不能排序

排序是 O(n log n),题目要求 O(n) → 只能用哈希:`set` 去重 + O(1) 查「在不在」。

### 关键洞察:只从「序列起点」开始数

把所有数塞进 `set`。对每个 `n`:如果 `n-1` **也在** set 里,说明 `n` 不是序列起点(前面还有更小的),**跳过**——从 `n-1` 那头数时会覆盖到 `n`,从 `n` 数纯属重复。只有当 **`n-1` 不在 set 里**(`n` 是某段连续序列的最小值)才从 `n` 往 `n+1, n+2, ...` 数,数到不在为止。

### Java 对照最小例

```java
Set<Integer> set = new HashSet<>();
for (int x : nums) set.add(x);
int best = 0;
for (int n : set) {
    if (set.contains(n - 1)) continue;     // 不是起点,跳过
    int len = 1, m = n + 1;
    while (set.contains(m)) { len++; m++; }
    best = Math.max(best, len);
}
```

```python
def longest_consecutive(nums):
    num_set = set(nums)          # 去重 + O(1) 查
    best = 0
    for n in num_set:
        if n - 1 in num_set:
            continue             # n 不是起点,跳过
        length, m = 1, n + 1
        while m in num_set:      # 从起点往大数方向数
            length += 1
            m += 1
        best = max(best, length)
    return best
```

### 真实场景例(已验证)

```python
longest_consecutive([100, 4, 200, 1, 3, 2])      # 4 —— 序列 1,2,3,4
longest_consecutive([0, 3, 7, 2, 5, 8, 4, 6, 0, 1])  # 9 —— 序列 0..8
longest_consecutive([1, 1, 1, 1])                # 1 —— 重复只算一次
longest_consecutive([10, 20, 30, 40])            # 1 —— 谁也不挨着谁
longest_consecutive([-1, -2, -3, 0, 1])          # 5 —— 负数序列 -3..1
longest_consecutive([1, 2])                      # 2
longest_consecutive([])                          # 0
```

### 为什么是 O(n) 而不是 O(n²)

外层 for + 内层 while,直觉像 O(n²)。但内层 while 访问到的每个元素 `x`,**当且仅当**它属于「某个从起点延伸的序列」,且只被**那一个**起点的 while 访问一次(非起点元素全 `continue` 了)。所以 while 总执行次数 ≤ n,整体 O(n) + O(n) = **O(n)**。

### ❌ 错误写法 → ✅ 正确写法

```python
# ❌ 不跳过非起点——答案仍对,但每个数都往后续数一遍,退化 O(n²)
for n in num_set:
    length, m = 1, n + 1
    while m in num_set: ...      # 没有 if n-1 in num_set: continue

# ❌ 起点判断方向反了——n+1 not in set 是「序列终点」,
#    从终点往大数方向数永远 length=1
if n + 1 not in num_set:         # [1,2,3] 会错答成 1
    ...

# ✅ n-1 not in num_set 才是起点;往 n+1 方向数
if n - 1 in num_set:
    continue
```

> 🟡 **差异**:`set(nums)` 一行把 list 去重转 set,Java 要循环 `add`;`while m in num_set:` 把 `in` 直接当循环条件,极简。
>
> **常踩的坑**:① 忘跳非起点(上面)。② 起点方向反(上面)。③ 遍历 `nums` 而不是 `num_set`——有重复时同一起点重复数,答案对但白耗时。④ 空数组返回 0(`best=0` 初值天然处理)。

**复杂度**:时间 **O(n)**;空间 **O(n)**。

---

## §36.8 六题对比总结(不出题)

| 题 | 哈希表角色 | 存什么 | 关键操作 | 初始项 |
|----|-----------|--------|----------|--------|
| is_anagram | 计数指纹 | `Counter` 词频 | `Counter(s) == Counter(t)` | — |
| two_sum | 查表 | `{值: 下标}` | `complement in seen` | `{}` |
| group_anagrams | 分组聚合 | `{指纹: [词...]}` | `buckets[key].append` | `defaultdict(list)` |
| subarray_sum | 频次表 | `{前缀和: 次数}` | `count += pc.get(cur-k, 0)` | `{0: 1}` |
| find_max_length | 最值索引 | `{前缀和: 最早下标}` | `best = max(best, i - first[cur])` | `{0: -1}` |
| longest_consecutive | 成员查询 | `set` | `n - 1 in num_set` | `set(nums)` |

三条通用规律:
1. **先查后登记**(two_sum / subarray_sum)——查的是「历史」,别把自己算进去。
2. **前缀和题先想 value 语义**——数个数存次数(`{0:1}`),求最值存下标(`{0:-1}`)。
3. **dict / set 选型看问题**——要映射用 dict,只要「在不在」用 set,要次数用 Counter,要分组用 defaultdict。

---

## §36.9 Java 老手常踩的坑(汇总)⚠️(不出题)

1. **用 `set` 判异位词** → 种类同、次数不同会误判;用 `Counter ==`(§36.2)。
2. **two_sum 先全存 dict 再查** → 同元素用两次;边扫边查、先查后登记(§36.3)。
3. **把 list 当 dict key** → 不可哈希直接 TypeError;`"".join(sorted(w))` 或 `tuple(...)`(§36.4)。
4. **普通 dict 分组手写判空** → `defaultdict(list)` 把「默认值」声明在创建处(§36.4)。
5. **前缀和忘预置初始项** → 计数题 `{0: 1}`、最值题 `{0: -1}`,漏了就错掉「从下标 0 起」的解(§36.5/§36.6)。
6. **先登记后查** → 把当前位置自己数进去(§36.5 反例 `[0],k=0` 错成 2)。
7. **525 里覆盖最早下标** → 只记第一次出现,越早已知越长(§36.6)。
8. **有负数还用滑窗** → 前缀和不单调,滑窗失效,上哈希(§36.5)。
9. **longest_consecutive 不跳非起点 / 起点方向反** → O(n²) 或全错(§36.7)。
10. **返回类型看错** → 下标(two_sum)/ 分组(group_anagrams)/ 个数(subarray_sum)/ 长度(find_max_length、longest_consecutive),看清题面。

---

## 📚 延伸阅读(本章不出题)

- **LC974 和可被 K 整除的子数组**:前缀和再升级——`{前缀和 % k: 次数}`(同余的前缀和之差必被 k 整除),初始 `{0: 1}`。会了 560 这就是送分。
- **LC523 连续的子数组和**:560 的「和为 k 倍数 + 长度 ≥ 2」版,dict 存 `{余数: 最早下标}`——正好缝合本章两种 value 语义。
- **`Counter` 的算术**:`Counter` 支持 `+`/`-`/`&`/`|`,但那些是「次数加减/取 min/max」,判等只有 `==`(§36.2)。
- **`tuple` 当 key 的更多玩法**:26 字母频次 tuple 作异位词 key(O(L)),或 LC49 变体里把「排序串」换成「计数签名」。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `is_anagram` | Counter 计数指纹 | 🟢 |
| `two_sum` | dict 查 complement,先查后登记 | 🟢 |
| `group_anagrams` | 排序 key + defaultdict 聚合 | 🟡 |
| `subarray_sum` | 前缀和 + 频次表,`{0:1}` | 🔴 |
| `find_max_length` | 0→-1 + 最早下标,`{0:-1}` | 🔴 |
| `longest_consecutive` | set + 只从起点数,O(n) | 🟡 |

```bash
uv run pytest 06_leetcode/ch36/test_ch36_assignment.py -v
```

全绿 = 掌握 Ch36 的哈希套路。

---

## ✅ 自测

- [ ] 一句话说清哈希表怎么把 O(n²) 降到 O(n)(「以查询换遍历」)
- [ ] `is_anagram` 会用 `Counter ==`,说清为什么 `set` 会误判 `"aab"/"abb"`
- [ ] `two_sum` 边扫边查,知道为什么不能先全存 dict(同元素用两次)
- [ ] `group_anagrams` 会用 `defaultdict(list)` + `"".join(sorted(word))`,知道 list 不能当 key
- [ ] `subarray_sum` 会写 `prefix[j]-prefix[i]=k` 的等价式,记得 `{0:1}` 和先查后登记
- [ ] `find_max_length` 会说清 0→-1 变换、dict 为什么存「最早下标」、`{0:-1}` 的语义
- [ ] `longest_consecutive` 知道为什么只从「起点」(n-1 不在 set)数才 O(n)
- [ ] 能背出六题 dict/set 里各存什么(§36.8 表)
- [ ] 6 个作业全绿

## 🎓 费曼挑战

1. 「为什么 `subarray_sum` 必须预置 `{0:1}`?举 `nums=[5], k=5` 讲漏数的情况。」— 重读 §36.5
2. 「`find_max_length` 和 `subarray_sum` 是同一个骨架,dict 的 value 为什么一个是次数一个是最早下标?初始项为什么一个 1 一个 -1?」— 重读 §36.6
3. 「`two_sum` 为什么不能先把所有数存进 dict 再查?举 `[3,2,4], 6` 讲。」— 重读 §36.3
4. 「`longest_consecutive` 有内层 while,为什么还是 O(n)?」— 重读 §36.7
5. 「`set` 为什么不能用来判异位词?`Counter` 的 `&` 又为什么不能当判等?」— 重读 §36.2

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步:Ch37 栈 / 队列 / 单调栈

哈希表是「以查询换遍历」。下一章栈/队列是 **LIFO/FIFO** 的顺序结构,而**单调栈**能在 O(n) 内解决「下一个更大元素」这类题(LC739 每日温度、LC42 接雨水)。从「查」到「维护单调顺序」。
