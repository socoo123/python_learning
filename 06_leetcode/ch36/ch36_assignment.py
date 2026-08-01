"""Ch36 · 哈希表 / 前缀和

哈希表把 O(n²) 暴力降到 O(n)。Python 用 `dict` / `defaultdict` / `Counter`
一行初始化;Java 要 `new HashMap<>()` 反复 `put`/`get`/`containsKey`。

本章 4 道 LeetCode 经典题:
  - two_sum             (LC1)   哈希查 complement
  - group_anagrams      (LC49)  排序后的字符串作 key, defaultdict 聚合
  - subarray_sum        (LC560) 前缀和 + 哈希记次数
  - longest_consecutive (LC128) set 去重, 只从序列起点开始数

运行测试:
    uv run pytest 06_leetcode/ch36/test_ch36_assignment.py -v
"""

from collections import defaultdict


def two_sum(nums: list[int], target: int) -> list[int]:
    """LC1 两数之和。详见 tutorial §36.2。

    思路:一次遍历,用 dict 存「值 → 下标」。对每个 num,查 complement = target - num
    是否已在 dict 里——在就直接返回两个下标,不在就把 num 登记进 dict。
    一次遍历 O(n),比暴力双循环 O(n²) 快得多。

    返回:[i, j] 两数下标(任意顺序,题面保证恰好有一个解)。

    例:two_sum([2,7,11,15], 9) == [0,1]
    """
    # TODO: 按上方「思路」实现(dict 存 值→下标,先查后登记)
    ...


def group_anagrams(strs: list[str]) -> list[list[str]]:
    """LC49 字母异位词分组。详见 tutorial §36.3。

    思路:互为异位词的字符串,排序后字符序列相同。把 sorted(word) 拼成的字符串
    作 key,用 defaultdict(list) 聚合所有同 key 的原词。最后返回各分组。

    「"".join(sorted(word))」是 Pythonic 一行算 key;Java 要 toCharArray → sort → new String。

    组内顺序、组间顺序题面均不强制(只要分组正确即可)。

    例:group_anagrams(["eat","tea","tan","ate","nat","bat"]) 的分组等价于
       [["eat","tea","ate"],["tan","nat"],["bat"]](顺序不强制)。
    """
    # TODO: 按上方「思路」实现(defaultdict(list),key = "".join(sorted(word)))
    ...


def subarray_sum(nums: list[int], k: int) -> int:
    """LC560 和为 K 的子数组个数。详见 tutorial §36.4。

    思路:前缀和 + 哈希。
      prefix[j] - prefix[i] == k  ⟺  prefix[i] == prefix[j] - k
    所以一边扫一边维护 dict {某前缀和值: 出现次数}。每到一个新前缀和 cur,
    看看 cur - k 在 dict 里出现过几次——就有几个以当前位置结尾、和为 k 的子数组。
    初始 dict 要放 {0: 1},表示「前缀和 0 出现过一次」(空前缀),否则从下标 0
    开始的子数组和正好等于 k 的情况会漏数。

    O(n) 时间、O(n) 空间。注意 nums 可含负数,前缀和不单调,不能滑窗。

    例:subarray_sum([1,1,1], 2) == 2; subarray_sum([1,2,3], 3) == 2。
    """
    # TODO: 按上方「思路」实现(前缀和 + dict 记次数,初始含 {0:1})
    ...


def longest_consecutive(nums: list[int]) -> int:
    """LC128 最长连续序列。详见 tutorial §36.5。

    思路:把所有数塞进 set(O(1) 查询)。只从「序列起点」开始往后数——
    起点 = n 满足 n-1 不在 set 里(否则 n 不是起点,从它开始数会重复浪费)。
    从每个起点往 n+1, n+2 ... 数,命中最长。每个元素最多被起点判定和数长度各访问
    常数次,整体 O(n),不是 O(n log n)(没排序)。

    例:longest_consecutive([100,4,200,1,3,2]) == 4  (序列 1,2,3,4)。
    """
    # TODO: 按上方「思路」实现(set 去重,只从序列起点 n-1 不在 set 开始数)
    ...
