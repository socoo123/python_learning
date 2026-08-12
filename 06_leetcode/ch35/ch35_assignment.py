"""
Ch35 作业:双指针 / 滑动窗口(M6 LeetCode 实战)。

数组/字符串题最高频的两类手法:
  - **对撞双指针**:两端往中间走,每步按规则动一头(two_sum_sorted / max_area / three_sum)。
  - **快慢指针**:都从左边出发,快的探路、慢的落定(move_zeroes)。
  - **滑动窗口**:两指针夹一段「窗口」,右扩探索、左缩优化
    (length_of_longest_substring / min_sub_array_len / min_window)。
  Python 的切片 + set / Counter 让窗口操作很简洁,Java 要手写 HashSet/HashMap。

7 道题,纯 stdlib(set / collections.Counter)。在每处 TODO 写实现,然后:

    uv run pytest 06_leetcode/ch35/test_ch35_assignment.py -v

全绿 = 你掌握了 Ch35 的双指针 / 滑动窗口套路。

每题 docstring 顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
from collections import Counter


# ========== §35.2 对撞双指针原型:two_sum_sorted ==========


def two_sum_sorted(nums: list[int], target: int) -> list[int] | None:
    """
    【对撞双指针原型 · §35.2】在【已排序】数组里找两个数之和等于 target,返回它们的值;不存在返回 None。

    示例:
        two_sum_sorted([1, 2, 3, 4, 6], 6)  -> [2, 4]
        two_sum_sorted([1, 2, 3, 9], 8)     -> None
        two_sum_sorted([], 0)               -> None

    提示(对撞双指针):
        - lo, hi 分别从头、尾出发,循环条件是「两指针未相遇」。
        - 当前和 < target:哪头动?(想想:右端已是当前最大,谁该「永久出局」)
        - 当前和 > target:动另一头。相等即返回。
        - 每步淘汰一个数,最多 n 步 → O(n) / O(1)。
    """
    # TODO: 对撞双指针:lo/hi 夹逼,按「和 vs target」决定动哪头
    ...


# ========== §35.3 快慢指针原地分区:move_zeroes(LC283) ==========


def move_zeroes(nums: list[int]) -> list[int]:
    """
    【快慢指针 · §35.3 · LC283】把所有 0 移到末尾,非零元素保持相对顺序;【原地】修改并返回 nums。

    示例:
        move_zeroes([0, 1, 0, 3, 12])  -> [1, 3, 12, 0, 0]
        move_zeroes([0, 0, 1])         -> [1, 0, 0]
        move_zeroes([1, 2, 3])         -> [1, 2, 3]
        move_zeroes([])                -> []

    提示(快慢指针):
        - slow = 下一个非零该落定的位置;fast 负责探路找非零。
        - nums[fast] != 0 时,交换 nums[slow] 与 nums[fast](Python 元组交换一行),slow 前进一步。
        - 循环不变式:nums[0..slow-1] 永远是「已就位的非零段」。
        - 别遍历中 list.remove(O(n) 且跳元素);也别返回新数组(题目要求原地,测试会查)。
        - O(n) / O(1)。
    """
    # TODO: 快慢指针:slow 落定、fast 探路,非零即交换并 slow += 1
    ...


# ========== §35.4 对撞 + 贪心:max_area(LC11) ==========


def max_area(height: list[int]) -> int:
    """
    【对撞双指针 · §35.4 · LC11】
    n 条竖线,第 i 条高度 height[i];两线 + x 轴围成容器,求最大盛水量。
    盛水 = 两线间距 * min(两线高度)(短板决定水位)。

    示例:
        max_area([1, 8, 6, 2, 5, 4, 8, 3, 7])  -> 49
        max_area([1, 1])                       -> 1
        max_area([4, 3, 2, 1, 4])              -> 16

    提示(对撞 + 贪心):
        - lo/hi 从两端夹逼;每步用「宽 * min(两端高度)」更新最大值。
        - 关键贪心:移动【较短】的一边。宽必然变小,只有 min(高度) 可能变大才有希望;
          移动长边则 min 被短边卡死,面积只会更小(那批方案直接剪掉)。
        - 注意:移动条件比的是【高度】,循环条件比的是【下标】,别混。
        - O(n) / O(1)。
    """
    # TODO: 对撞;每步 max(area, 宽*min(h));移动较短边
    ...


# ========== §35.5 滑动窗口入门:length_of_longest_substring(LC3) ==========


def length_of_longest_substring(s: str) -> int:
    """
    【滑动窗口 · §35.5 · LC3】找不含重复字符的最长子串的【长度】。

    示例:
        length_of_longest_substring("abcabcbb")  -> 3   # "abc"
        length_of_longest_substring("bbbbb")     -> 1   # "b"
        length_of_longest_substring("pwwkew")    -> 3   # "wke"
        length_of_longest_substring("")          -> 0

    提示(滑动窗口 + set):
        - 窗口 s[left..right] 始终保持无重复;set 存窗口内字符。
        - for 右扩:若新字符已在 set 中,【while】左缩(remove s[left]、left+=1)直到不重复。
          注意是 while 不是 if——可能要连吐好几个。
        - 窗口合法后放入新字符,用「right - left + 1」更新 best。
        - 均摊 O(n):right 走 n 次,left 全程总共也走 ≤ n 次(每个字符至多 add/remove 各一次)。
    """
    # TODO: 滑动窗口 + set;右扩、冲突 while 左缩、合法后更新 best
    ...


# ========== §35.6 窗口求「最短满足」:min_sub_array_len(LC209) ==========


def min_sub_array_len(target: int, nums: list[int]) -> int:
    """
    【滑动窗口 · §35.6 · LC209】
    【正整数】数组 nums,找和 >= target 的最短连续子数组,返回其长度;不存在返回 0。

    示例:
        min_sub_array_len(7, [2, 3, 1, 2, 4, 3])  -> 2   # [4,3]
        min_sub_array_len(4, [1, 4, 4])           -> 1   # [4]
        min_sub_array_len(11, [1, 1, 1, 1, 1, 1, 1, 1]) -> 0
        min_sub_array_len(15, [1, 2, 3, 4, 5])    -> 5   # 整个数组

    提示(滑动窗口 + 正数单调性):
        - 窗口状态就是一个整数 window_sum:右扩 += nums[right]。
        - 求「最短」,更新答案要写在收缩循环【里面】——每次 while 迭代窗口都合法,都要抢答。
          (对比 LC3 求最长,更新写在 while 之后。)
        - while window_sum >= target:更新 best → 吐掉 nums[left](-= 且 left+=1)。
        - 哨兵 best = float('inf');最后「0 if best == inf else best」区分没找到。
        - 正整数保证单调性(右扩只增、左缩只减),left 永不回头 → O(n) / O(1)。
    """
    # TODO: 右扩累加;while 和达标:内更新 best 并左缩;inf 哨兵,没找到返回 0
    ...


# ========== §35.7 排序 + 对撞:three_sum(LC15) ==========


def three_sum(nums: list[int]) -> list[list[int]]:
    """
    【排序 + 对撞双指针 · §35.7 · LC15】找所有【不重复】的三元组 [a,b,c] 使 a+b+c == 0。

    示例:
        three_sum([-1, 0, 1, 2, -1, -4])  -> [[-1, -1, 2], [-1, 0, 1]]
        three_sum([0, 1, 1])              -> []
        three_sum([0, 0, 0])              -> [[0, 0, 0]]
        three_sum([])                     -> []

    提示(排序 + 固定 i + 对撞 lo/hi):
        - 先 sort():对撞的前提是有序,且相同值相邻便于去重。
        - 固定首数 nums[i],剩两数退化成 §35.2 的 two_sum_sorted(目标和 = -nums[i])。
        - 去重有两处,缺一不可:
          ① 固定 i:nums[i] == nums[i-1] 就跳过(看【身后】:同首数上一轮已找全);
          ② 命中后:lo/hi 各自越过相邻重复值,再各前进一步(忘了会死循环)。
        - 外层 range(n - 2):不足 3 个数自然返回 []。
        - O(n²):外层 n × 内层对撞 n。
    """
    # TODO: sort → 固定 i(去重①)→ 对撞 lo/hi(命中后去重②再各走一步)
    ...


# ========== §35.8 滑窗巅峰:min_window(LC76 · Hard) ==========


def min_window(s: str, t: str) -> str:
    """
    【滑动窗口 + Counter · §35.8 · LC76 · Hard】
    找 s 中涵盖 t 所有字符(含重复次数)的【最短】子串;没有则返回 ""。

    示例:
        min_window("ADOBECODEBANC", "ABC")  -> "BANC"
        min_window("a", "a")                -> "a"
        min_window("a", "aa")               -> ""   # s 里 a 不够
        min_window("a", "b")                -> ""

    提示(右扩到满足 → 左缩到刚不满足,记录最短):
        - need = Counter(t):need[c] > 0 缺、== 0 刚好、< 0 冗余(Counter 读新 key 返回 0,不会 KeyError)。
        - missing = len(t) 管「总缺口」,增量维护,避免每次 sum(need.values()):
          右扩时【need[ch] > 0 才】missing -= 1(冗余字符不减少缺口),然后 need[ch] -= 1;
          左缩时出窗口字符 need += 1,【变正才】missing += 1。
        - missing == 0 时窗口合法:while 里更新最短(单独记 start/length,别用循环结束时的指针),
          然后吐左端继续缩,直到「刚不满足」。
        - 哨兵 length = len(s) + 1;最后「length <= len(s)」判是否找到过。
        - O(|s| + |t|):right 走 |s| 次,left 全程 ≤ |s| 次。
    """
    # TODO: need/missing 增量维护;右扩、missing==0 时 while 左缩并记最短;哨兵区分没找到
    ...
