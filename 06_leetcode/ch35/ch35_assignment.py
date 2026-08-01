"""
Ch35 作业:双指针 / 滑动窗口(M6 LeetCode 实战)。

本章是数组/字符串题的高频套路章。两类手法:
  - **对撞双指针**:两端往中间走,每次按规则移动一头(LC11 盛水容器、LC15 三数之和)。
  - **滑动窗口**:左右两指针夹一段「窗口」,右扩探索、左缩优化(LC3 无重复子串、LC76 最小覆盖子串)。
  Python 的切片 + set / Counter 让窗口操作很简洁,Java 要手写 HashSet/HashMap。

4 道经典题,纯 stdlib(set / collections.Counter)。在每处 TODO 写实现,然后:

    uv run pytest 06_leetcode/ch35/test_ch35_assignment.py -v

全绿 = 你掌握了 Ch35 的双指针 / 滑动窗口套路。
"""
from collections import Counter


# ========== §35.2 对撞双指针原型(讲透,不出题) ==========


def two_sum_sorted(nums: list[int], target: int) -> list[int] | None:
    """
    【对撞双指针原型 · §35.2】在【已排序】数组里找两个数之和等于 target,返回它们的值。

    示例:
        two_sum_sorted([1, 2, 3, 4, 6], 6)  -> [2, 4]
        two_sum_sorted([1, 2, 3, 9], 8)     -> None

    思路(对撞双指针,左小则左进、右大则右退):
        lo, hi = 0, len(nums) - 1
        while lo < hi:
            s = nums[lo] + nums[hi]
            if s == target: return [nums[lo], nums[hi]]
            if s < target: lo += 1
            else:           hi -= 1
        return None
    """
    # TODO: 按上方「思路」实现(对撞双指针)
    ...


# ========== §35.3 LC11 盛最多水的容器:max_area ==========


def max_area(height: list[int]) -> int:
    """
    【对撞双指针 · §35.3 · LC11】
    n 条竖线,第 i 条高度 height[i];两线 + x 轴围成容器,求最大盛水量。
    盛水 = 两线间距 * min(两线高度)(短板决定水位)。

    示例:
        max_area([1,8,6,2,5,4,8,3,7])  -> 49
        max_area([1,1])                -> 1
        max_area([4,3,2,1,4])          -> 16

    思路(对撞双指针,O(n)):
        lo=0, hi=n-1, area=0
        while lo < hi:
            area = max(area, (hi-lo) * min(height[lo], height[hi]))
            # 关键贪心:移动【较短】的一边——长边不动,因为换掉短边才可能变更大
            if height[lo] < height[hi]: lo += 1
            else:                       hi -= 1
        return area

    为什么移动短的?:面积 = 宽 * min(h_lo,h_hi),宽在缩小;只有 min(高度) 变大才可能扳回。
    若移动长边,宽变小、min 不变(被短边卡死)→ 面积只会更小。故必须移动短边碰运气。
    """
    # TODO: 按上方「思路」实现(对撞双指针,移动较短边)
    ...


# ========== §35.4 LC3 无重复字符的最长子串:length_of_longest_substring ==========


def length_of_longest_substring(s: str) -> int:
    """
    【滑动窗口 · §35.4 · LC3】
    找不含重复字符的最长子串的【长度】。

    示例:
        length_of_longest_substring("abcabcbb")  -> 3   # "abc"
        length_of_longest_substring("bbbbb")     -> 1   # "b"
        length_of_longest_substring("pwwkew")    -> 3   # "wke"
        length_of_longest_substring("")          -> 0
        length_of_longest_substring(" ")         -> 1
        length_of_longest_substring("au")        -> 2

    思路(滑动窗口 + set,O(n)):
        chars = set()           # 窗口内已出现的字符
        left = 0                # 窗口左端(收缩用)
        best = 0
        for right, ch in enumerate(s):      # right = 窗口右端(扩张)
            while ch in chars:              # 右端字符已在窗口里 → 重复了
                chars.remove(s[left])       # 左端不断吐出,直到把【重复那个】踢掉
                left += 1
            chars.add(ch)                   # 现在窗口无重复,放心放入右端
            best = max(best, right - left + 1)
        return best

    为什么对?:右指针只前进 n 次,左指针总共也只前进不超过 n 次(每个字符至多被 add/remove 各一次),
    所以是 O(n),不是 O(n^2)。这是滑动窗口「均摊 O(1)」的精髓。
    """
    # TODO: 按上方「思路」实现(滑动窗口 + set)
    ...


# ========== §35.5 LC15 三数之和:three_sum ==========


def three_sum(nums: list[int]) -> list[list[int]]:
    """
    【排序 + 对撞双指针 · §35.5 · LC15】
    找所有【不重复】的三元组 [a,b,c] 使 a+b+c == 0。

    示例:
        three_sum([-1,0,1,2,-1,-4])  -> [[-1,-1,2],[-1,0,1]]
        three_sum([0,1,1])            -> []
        three_sum([0,0,0])            -> [[0,0,0]]
        three_sum([])                 -> []

    思路(排序 + 固定 i + 对撞 lo/hi,O(n^2)):
        nums.sort()
        res = []
        for i in range(len(nums) - 2):
            if i > 0 and nums[i] == nums[i-1]: continue   # 去重 i(跳过相同的首数)
            lo, hi = i+1, len(nums)-1
            while lo < hi:
                s = nums[i] + nums[lo] + nums[hi]
                if s == 0:
                    res.append([nums[i], nums[lo], nums[hi]])
                    while lo < hi and nums[lo]  == nums[lo+1]:  lo += 1   # 去重 lo
                    while lo < hi and nums[hi]  == nums[hi-1]:  hi -= 1   # 去重 hi
                    lo += 1; hi -= 1
                elif s < 0: lo += 1
                else:       hi -= 1
        return res

    两个去重关键:
      1. 固定的 i:若 nums[i]==nums[i-1] 跳过(同首数的三元组上一轮已找全)。
      2. 找到一组后,lo/hi 要越过相邻重复值,否则会塞进一模一样的三元组。
    排序后三元组天然升序,直接 append 不用再排序去重。
    """
    # TODO: 按上方「思路」实现(排序 + 固定 i + 对撞 lo/hi,注意两处去重)
    ...


# ========== §35.6 LC76 最小覆盖子串(Hard):min_window ==========


def min_window(s: str, t: str) -> str:
    """
    【滑动窗口 + Counter · §35.6 · LC76 · Hard】
    找 s 中涵盖 t 所有字符(含重复)的【最短】子串;没有则返回 ""。

    示例:
        min_window("ADOBECODEBANC", "ABC")  -> "BANC"
        min_window("a", "a")                -> "a"
        min_window("a", "aa")               -> ""   # s 里 a 不够
        min_window("a", "b")                -> ""

    思路(右扩到满足 → 左缩到刚不满足 → 记录最短,O(|s|+|t|)):
        need  = Counter(t)              # 还差多少个各字符
        missing = len(t)                # 总共还差几个字符(= sum(need.values()) 的快表)
        left = 0
        start, length = 0, len(s) + 1   # 记录最优窗口(初值 length 设成「不可能大」)
        for right, ch in enumerate(s):
            # 1) 右扩:把 s[right] 纳入窗口
            if need[ch] > 0:            # 这个字符是 t 需要的 → 减少一个缺口
                missing -= 1
            need[ch] -= 1               # 不管需不需要都 -1(负数=窗口里这种字符超了)
            # 2) 已满足(t 全覆盖)→ 尝试左缩到【刚不满足】为止,沿途更新最短
            while missing == 0:
                if right - left + 1 < length:
                    start, length = left, right - left + 1
                need[s[left]] += 1      # 左端字符要出窗口
                if need[s[left]] > 0:   # 出窗口后这种字符变成「缺」了 → 缺口 +1
                    missing += 1
                left += 1
        return s[start:start+length] if length <= len(s) else ""

    两个 Counter 技巧(Java 老手重点):
      - need[ch] 正数=t 还差这个字符;0=刚好;负数=窗口里这种字符多出来了。
      - missing 一个计数器管「总缺口」,避免每次 while 都 sum(need.values())。
    """
    # TODO: 按上方「思路」实现(右扩到满足 → 左缩到刚不满足,记录最短)
    ...


# ---------------------------------------------------------------------
if __name__ == "__main__":
    print("two_sum_sorted:", two_sum_sorted([1, 2, 3, 4, 6], 6))
    print("max_area:", max_area([1, 8, 6, 2, 5, 4, 8, 3, 7]))
    print("length_of_longest_substring:", length_of_longest_substring("abcabcbb"))
    print("three_sum:", three_sum([-1, 0, 1, 2, -1, -4]))
    print("min_window:", min_window("ADOBECODEBANC", "ABC"))
