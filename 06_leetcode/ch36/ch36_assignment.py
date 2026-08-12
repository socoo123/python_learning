"""
Ch36 作业:哈希表 / 前缀和。

哈希表把 O(n²) 暴力降到 O(n)——「以查询换遍历」。Python 用 `dict` /
`defaultdict` / `Counter` / `set` 一行初始化;Java 要 `new HashMap<>()`
反复 `put`/`get`/`containsKey`。

本章 6 道 LeetCode 经典题,覆盖哈希表的 6 种角色:
  - is_anagram          (LC242) Counter 计数指纹判异位词
  - two_sum             (LC1)   dict {值: 下标},边扫边查
  - group_anagrams      (LC49)  排序 key + defaultdict(list) 聚合
  - subarray_sum        (LC560) 前缀和 + {前缀和: 次数},{0: 1} 预置
  - find_max_length     (LC525) 0→-1 变换 + {前缀和: 最早下标}
  - longest_consecutive (LC128) set 去重,只从序列起点开始数

在每处 TODO 写实现,然后:

    uv run pytest 06_leetcode/ch36/test_ch36_assignment.py -v

全绿 = 你掌握了 Ch36 的哈希套路。

每题 docstring 顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""

from collections import Counter, defaultdict


# ========== §36.2 计数指纹:is_anagram ==========


def is_anagram(s: str, t: str) -> bool:
    """
    【Counter · §36.2】判断 t 是否是 s 的字母异位词(LC242)。

    异位词 = 字母完全相同、顺序不同(如 "anagram"/"nagaram")。

    示例:
        is_anagram("anagram", "nagaram") -> True
        is_anagram("listen", "silent")   -> True
        is_anagram("rat", "car")         -> False
        is_anagram("aab", "abb")         -> False  # 字母种类相同但次数不同
        is_anagram("ab", "a")            -> False  # 长度不同
        is_anagram("", "")               -> True

    思路(Counter 计数指纹,一行):
        Counter(s) == Counter(t)
        Counter 是 dict 子类,{字符: 次数};== 按键值全等比较,
        次数一字不差才是异位词。Java 等价:排序 char 数组再 Arrays.equals,
        或手写 int[26] 计数。

        备选(不用库):sorted(s) == sorted(t) 也对,O(L log L);
        Counter 是 O(L)。面试可作为第二答案。

    边界:
        - 空串互为异位词(Counter("") == Counter("") -> True)。
        - 长度不同必然 False(Counter 键数量就不同)。
        - 千万别用 set 判:set 只存「有没有」不存「几次」,
          set("aab") == set("abb") 会误判 True(测试专门考这条)。
    """
    # TODO: return Counter(s) == Counter(t),一行
    ...


# ========== §36.3 查表:two_sum ==========


def two_sum(nums: list[int], target: int) -> list[int]:
    """
    【dict 查表 · §36.3】返回和为 target 的两个元素的【下标】(LC1)。

    题面保证恰好一个解,同一元素不能重复用。

    示例:
        two_sum([2, 7, 11, 15], 9)        -> [0, 1]   # 2+7=9
        two_sum([3, 2, 4], 6)             -> [1, 2]   # 2+4=6
        two_sum([3, 3], 6)                -> [0, 1]   # 同值两个,OK
        two_sum([-1, -2, -3, -4, -5], -8) -> [2, 4]   # 负数照常

    思路(边扫边查,先查后登记):
        seen = {}   # {值: 下标}
        for i, num in enumerate(nums):
            complement = target - num
            if complement in seen:        # O(1) 查「前面有没有配对的」
                return [seen[complement], i]
            seen[num] = i                 # 查完才登记自己

        为什么不能先把所有数存进 dict 再统一查?
        先全存会允许「同元素用两次」:[3,2,4], 6 会在 i=0 处拿 3 配 3,
        错返回 [0,0]。边扫边查时当前 i 还没登记,天然保证两下标不同。

        Java 等价:HashMap + containsKey/get/put 三件套。

    边界:
        - 返回【下标】不是值。
        - 重复元素([3,3], 6)放心:先登记 3→0,扫到第二个 3 命中 [0,1]。
    """
    # TODO: dict 存 值→下标,边扫边查(先查后登记)
    ...


# ========== §36.4 分组聚合:group_anagrams ==========


def group_anagrams(strs: list[str]) -> list[list[str]]:
    """
    【defaultdict · §36.4】把互为字母异位词的词归为一组(LC49)。

    组内顺序、组间顺序题面均不强制(只要分组正确)。

    示例:
        group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
            -> 等价于 [["eat","tea","ate"], ["tan","nat"], ["bat"]]
        group_anagrams(["aab", "aba", "baa", "abc"])
            -> 等价于 [["aab","aba","baa"], ["abc"]]
        group_anagrams([""]) -> [[""]]
        group_anagrams([])   -> []

    思路(排序 key + defaultdict(list) 聚合):
        buckets = defaultdict(list)      # key 不存在时自动建 []
        for word in strs:
            key = "".join(sorted(word))  # 异位词指纹:排序后字符序列相同
            buckets[key].append(word)    # 直接 append,不判 key 在不在
        return list(buckets.values())

        "eat"/"tea"/"ate" 的 key 都是 "aet"。
        Java 等价:toCharArray → Arrays.sort → new String,
        再 map.computeIfAbsent(key, k -> new ArrayList<>()).add(w)。

    边界:
        - dict key 必须可哈希:sorted 结果是 list,不能直接当 key
          (TypeError: unhashable),要 "".join(...) 拼成 str。
        - 空字符串 key 是 "",正常单独成组,不用特判。
    """
    # TODO: defaultdict(list) + key = "".join(sorted(word)) + list(values())
    ...


# ========== §36.5 前缀和 + 频次表:subarray_sum ==========


def subarray_sum(nums: list[int], k: int) -> int:
    """
    【前缀和 + dict 频次表 · §36.5】返回和等于 k 的【连续子数组个数】(LC560)。

    示例:
        subarray_sum([1, 1, 1], 2)         -> 2   # [1,1](0-1) 和 [1,1](1-2)
        subarray_sum([1, 2, 3], 3)         -> 2   # [1,2] 和 [3]
        subarray_sum([5], 5)               -> 1   # 整个数组,考验 {0:1}
        subarray_sum([0, 0, 0], 0)         -> 6   # 6 个非空子数组和全为 0
        subarray_sum([1, -1, 1, -1, 1], 0) -> 6   # 含负数,滑窗失效
        subarray_sum([1, 2, 3], 100)       -> 0
        subarray_sum([], 5)                -> 0

    思路(前缀和 + {前缀和: 次数}):
        prefix[j] - prefix[i] == k  ⟺  prefix[i] == prefix[j] - k
        边扫边维护 dict {前缀和值: 出现次数},每到一个新前缀和 cur,
        查 cur - k 出现过几次——就有几个以当前位置结尾、和为 k 的子数组。

        count = 0
        prefix_count = {0: 1}        # 关键预置:前缀和 0 出现过一次(空前缀)
        cur = 0
        for num in nums:
            cur += num
            count += prefix_count.get(cur - k, 0)        # 先查
            prefix_count[cur] = prefix_count.get(cur, 0) + 1  # 后登记

        {0: 1} 的玄机:不预置会漏掉「从下标 0 开始、整个前缀和就是 k」的子数组
        (如 [5], 5)。顺序也不能反:先登记会把当前位置自己数进去
        ([0], 0 会错成 2)。

        nums 可含负数,前缀和不单调,不能滑窗(Ch35 滑窗要求全正)。

    边界:
        - 空数组 -> 0(循环不执行)。
        - 返回【个数】(int),不是子数组列表。
    """
    # TODO: {0:1} 起手 → cur+=num → count+=pc.get(cur-k,0) → pc[cur]+=1(先查后登记)
    ...


# ========== §36.6 前缀和变体:find_max_length ==========


def find_max_length(nums: list[int]) -> int:
    """
    【前缀和 + 最早下标 · §36.6】返回 0 和 1 个数相等的【最长】连续子数组长度(LC525)。

    示例:
        find_max_length([0, 1])             -> 2   # 整段平衡:1 - (-1) = 2
        find_max_length([0, 1, 0])          -> 2   # [0,1] 或 [1,0]
        find_max_length([0, 0, 1, 0, 0])    -> 2
        find_max_length([0, 1, 1, 0, 1, 1]) -> 4   # 子数组下标 0-3
        find_max_length([0, 0, 0, 1, 1, 1]) -> 6   # 整组全平衡
        find_max_length([1, 0, 1, 0])       -> 4   # 整段,考验 {0:-1}
        find_max_length([1, 1, 1])          -> 0
        find_max_length([])                 -> 0

    思路(0→-1 变换 + {前缀和: 最早下标}):
        洞察 1:把 0 看成 -1,「0 和 1 个数相等」⟺「子数组和为 0」。
        洞察 2:和为 0 ⟺ 两处前缀和相等。dict 存 {前缀和: 最早下标},
        同一前缀和再次出现时,i - first[cur] 就是一段平衡子数组长度。

        first = {0: -1}            # 前缀和 0 的「最早下标」是 -1(空前缀末尾)
        cur = best = 0
        for i, x in enumerate(nums):
            cur += 1 if x == 1 else -1
            if cur in first:
                best = max(best, i - first[cur])
            else:
                first[cur] = i     # 只在第一次出现时登记,绝不覆盖

        与 subarray_sum 对照:同骨架,但 560 数「个数」→ value 存次数;
        本题求「最长」→ value 存最早下标(越早越长,覆盖会算错:
        [0,1] 若覆盖 first[0]=1,长度算成 0)。
        {0: -1} 语义:空前缀的「下标」是 -1,没有它会漏掉从下标 0 起的解
        ([1,0,1,0] 会错成 2)。

    边界:
        - 空数组 / 全 0 / 全 1 -> 0(永远不平衡)。
        - 返回【长度】(int)。
    """
    # TODO: 0→-1 变换 → first={0:-1} → cur 见过就 i-first[cur] 刷 best,没见过才登记
    ...


# ========== §36.7 成员查询:longest_consecutive ==========


def longest_consecutive(nums: list[int]) -> int:
    """
    【set 成员查询 · §36.7】返回最长连续元素序列的长度(LC128),要求 O(n)。

    示例:
        longest_consecutive([100, 4, 200, 1, 3, 2])         -> 4  # 序列 1,2,3,4
        longest_consecutive([0, 3, 7, 2, 5, 8, 4, 6, 0, 1]) -> 9  # 序列 0..8
        longest_consecutive([1, 1, 1, 1])                   -> 1  # 重复只算一次
        longest_consecutive([10, 20, 30, 40])               -> 1
        longest_consecutive([-1, -2, -3, 0, 1])             -> 5  # 负数序列 -3..1
        longest_consecutive([])                             -> 0

    思路(set 去重 + 只从「序列起点」开始数):
        num_set = set(nums)        # 去重 + O(1) 查
        best = 0
        for n in num_set:
            if n - 1 in num_set:
                continue           # n 不是起点,跳过(从 n-1 那头数会覆盖它)
            length, m = 1, n + 1
            while m in num_set:    # 从起点往大数方向数
                length += 1
                m += 1
            best = max(best, length)

        为什么不能排序?排序 O(n log n),题目要求 O(n)。
        为什么整体是 O(n) 而不是 O(n²)?内层 while 访问到的每个元素
        只被【一个】起点对应的 while 访问一次(非起点全 continue 了),
        while 总次数 ≤ n。

    边界:
        - 空数组 -> 0(best 初值天然处理)。
        - 起点方向别反:是 n-1 not in set 才数,不是 n+1
          (n+1 not in set 是「终点」,从终点往大数永远长 1)。
        - 遍历 num_set 而不是 nums(有重复时少做无用功)。
    """
    # TODO: set(nums) → 跳过非起点(n-1 in set 就 continue)→ 从起点 while 数 → max
    ...
