"""
Ch37 作业:栈 / 队列 / 单调栈(LeetCode 高频)。

本章 4 道经典题,覆盖「栈」这个数据结构在 LC 里的三大典型场景:
  1. 配对/嵌套类(括号匹配、表达式求值)—— 普通栈
  2. O(1) 取最值的栈 —— 辅助栈(空间换时间)
  3. 「下一个更大/更小」类 —— 单调栈(LC 高频难点)
  4. 单调栈进阶 —— 接雨水(Hard)

Python 里 list 当栈(.append 入、.pop 出,都 O(1) amortized);队列用 collections.deque。
本章纯 stdlib。在每处 TODO 写实现,然后:

    uv run pytest 06_leetcode/ch37/test_ch37_assignment.py -v

全绿 = 你掌握了 Ch37。
"""

from collections import deque


# ========== §37.2 LC20 有效的括号 ==========


def is_valid_parens(s: str) -> bool:
    """
    【栈 · §37.2】LC20 有效的括号。给定只含 ()[]{} 的字符串,判断是否合法。
    合法 = 每个右括号都能和「最近的未匹配左括号」配对,且最终栈空。

    示例:
        is_valid_parens("()")      -> True
        is_valid_parens("()[]{}")  -> True
        is_valid_parens("(]")      -> False
        is_valid_parens("([)]")    -> False
        is_valid_parens("{[]}")    -> True
        is_valid_parens("")        -> True
        is_valid_parens("(")       -> False

    思路(栈 + 哈希表/字典做配对):
        1. 左括号 -> 入栈
        2. 右括号 -> 看栈顶是不是「它对应的左括号」;不匹配或栈空 -> False
        3. 走完字符串,栈必须为空(否则有左括号没闭合)

    技巧:用 dict {')':'(', ']':'[', '}':'{'} 反向映射,右括号 -> 期望的左括号。
    """
    # TODO: 用栈 + 字典做括号配对
    ...


# ========== §37.3 LC155 最小栈 ==========


class MinStack:
    """
    【辅助栈 · §37.3】LC155 最小栈。push/pop/top/get_min 都 O(1) 的栈。

    难点:get_min O(1)。一个普通栈无法 O(1) 取最小(得遍历)。
    解法:维护一个【辅助栈 mins】,与主栈同步增减,栈顶始终是「到当前为止的最小值」。

    示例:
        ms = MinStack()
        ms.push(-2); ms.push(0); ms.push(-3)
        ms.get_min()  -> -3
        ms.pop()
        ms.top()      -> 0
        ms.get_min()  -> -2
    """

    def __init__(self) -> None:
        # 主栈 + 辅助栈(辅助栈栈顶 = 当前最小值)。__init__ 已写好。
        self.stack: list[int] = []
        self.mins: list[int] = []

    def push(self, val: int) -> None:
        """
        入栈:主栈直接 append;辅助栈 append「min(val, 当前最小)」。
        空栈时直接放 val。
        """
        # TODO
        ...

    def pop(self) -> None:
        """
        出栈:主栈、辅助栈同步 pop。(题意保证对非空栈调用)
        """
        # TODO
        ...

    def top(self) -> int:
        """
        取栈顶(不删除)。return self.stack[-1]。
        """
        # TODO
        ...

    def get_min(self) -> int:
        """
        取当前最小值 O(1)。return self.mins[-1]。
        """
        # TODO
        ...


# ========== §37.4 LC739 每日温度 ==========


def daily_temperatures(temps: list[int]) -> list[int]:
    """
    【单调栈 · §37.4】LC739 每日温度。
    返回数组 ans,ans[i] = 第 i 天之后,第一个比 temps[i] 高的天,距离今天几天;没有则 0。

    示例:
        daily_temperatures([73,74,75,71,69,72,76,73]) -> [1,1,4,2,1,1,0,0]
        daily_temperatures([30,40,50,60])             -> [1,1,1,0]
        daily_temperatures([30])                       -> [0]

    思路(单调递减栈,存「下标」):
        1. 栈里存「还没找到更高温度的天的下标」,保持栈内下标对应的温度【单调递减】
        2. 遍历每天 i:
             while 栈非空 且 temps[i] > temps[栈顶]:
                 j = 栈.pop()           # 第 j 天找到了「下一个更高温」就是第 i 天
                 ans[j] = i - j
             栈.append(i)                # 第 i 天入栈,等它的更高温
        3. 栈里剩下的下标永远没等到更高温,ans 默认 0 即可
    """
    # TODO: 单调递减栈存下标
    ...


# ========== §37.5 LC42 接雨水(Hard) ==========


def trap(height: list[int]) -> int:
    """
    【单调栈/双指针 · §37.5】LC42 接雨水(Hard)。
    给定 n 个非负整数表示每根柱子高度,返回能接多少雨水。

    示例:
        trap([0,1,0,2,1,0,1,3,2,1,2,1]) -> 6
        trap([4,2,0,3,2,5])             -> 9
        trap([])                        -> 0
        trap([1])                       -> 0

    思路 A(对撞双指针,O(n) 时间 O(1) 空间 —— 推荐):
        - 每根柱子能接的水 = min(它左边的最高, 它右边的最高) - 它自身高度(取正部分)
        - 用左右两个指针 left/right 和左侧最大 left_max、右侧最大 right_max:
            if height[left] < height[right]:
                # 左边较矮,水量由 left_max 决定(右边一定有更高的挡着)
                left_max = max(left_max, height[left])
                ans += left_max - height[left]
                left += 1
            else:
                right_max = max(right_max, height[right])
                ans += right_max - height[right]
                right -= 1
        - 关键直觉:哪边更矮就处理哪边 —— 矮的那边的水位由它这一侧的 max 决定,
          因为另一侧一定有更高的柱子挡着(否则指针早移过来了)。

    本实现用双指针(更省空间)。也可用单调栈:弹出中间凹槽时按「宽×高」累加。
    """
    # TODO: 对撞双指针
    ...


# ========== §37.6 (附)双端队列 deque:队列/滑动窗口常客 ==========
# Python list 的 pop(0) 是 O(n)(整体前移),当队列用性能差。
# collections.deque 是双向链表式结构,append/popleft 都 O(1),当队列/BFS 用。
# 这里给个最小示意,作业不考,但 BFS 题(LC239 滑动窗口最大值)会用到。

def _deque_demo() -> None:
    """deque 基本用法(仅演示,不测试)。"""
    q: deque[int] = deque()
    q.append(1)      # 入队(右)
    q.append(2)
    q.popleft()      # 出队(左) O(1) —— list.pop(0) 是 O(n),别用错
    # q.appendleft(0) # 也能从左入;双向的
