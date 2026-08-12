"""
Ch40 · 回溯 / 贪心 + 综合(M6 LeetCode 实战收官章)

本章主题:
  - 回溯(Backtracking)= DFS + 撤销选择。四道经典:全排列 / 子集 / 组合总和 / 全排列 II。
    Python 里回溯模板极简:`for x in 选择: 路径.append(x); dfs(); 路径.pop()`,
    append/pop 配对 = 「做选择 / 撤销选择」,比 Java 的 list.add/remove 干净。
  - 贪心(Greedy)= 每步取局部最优。两道经典:股票一次交易 / 跳跃游戏。
    贪心没有通用模板,关键是想清楚「局部最优 = 全局最优」的贪心选择性。

跑测试:
  uv run pytest 06_leetcode/ch40/test_ch40_assignment.py -v

约定:
  - 纯 stdlib,不 import 外部库。
  - 每个函数顶部 docstring 指向 tutorial 对应 §,给「思路」提示。
  - LeetCode 返回的列表答案「顺序不限」时,测试用 sorted 规范化后比较。
"""

from __future__ import annotations


# =====================================================================
# §40.2 全排列 (LC46)
# =====================================================================
def permute(nums: list[int]) -> list[list[int]]:
    """LC46 全排列(数组无重复)。对应 tutorial §40.2。

    示例:
      >>> permute([1, 2, 3])   # 输出顺序与 used 标记法的 DFS 顺序一致
      [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]
      >>> permute([1])
      [[1]]
      >>> permute([])
      [[]]

    思路提示:回溯 + used 标记数组。
      - path 记录当前已选;used[i] 标记 nums[i] 是否已在路径上。
      - 每层 for i in range(n) 扫全体(排列顺序敏感,不能只往后选),跳过 used 的。
      - append → dfs → pop,used=True → dfs → used=False,两对都别漏。
      - len(path) == n 时收 res.append(path.copy())(必须 copy!)。
    """
    # TODO: 回溯 + used 标记;path 满长度收 copy;append/pop、used=True/False 配对
    ...


# =====================================================================
# §40.3 子集 (LC78)
# =====================================================================
def subsets(nums: list[int]) -> list[list[int]]:
    """LC78 子集(数组无重复,返回所有子集含空集)。对应 tutorial §40.3。

    示例:
      >>> len(subsets([1, 2, 3]))
      8
      >>> sorted(map(sorted, subsets([0])))
      [[], [0]]
      >>> subsets([])
      [[]]

    思路提示:回溯,用 start 下标「只往后选」去重。
      - 每个节点都是答案:进 dfs 第一件事就 res.append(path.copy())(含空集)。
      - for i in range(start, n):选 nums[i] → dfs(i+1) → pop 撤销。
      - 每个元素只选一次 → 传 i+1(可重复选才传 i,见 §40.4)。
    """
    # TODO: 进 dfs 先收 copy;for i in range(start, n);dfs(i+1);pop
    ...


# =====================================================================
# §40.4 组合总和 (LC39)
# =====================================================================
def combination_sum(candidates: list[int], target: int) -> list[list[int]]:
    """LC39 组合总和(候选无重复、每个可无限次用,返回所有和=target 的组合)。
    对应 tutorial §40.4。

    示例:
      >>> sorted(map(sorted, combination_sum([2, 3, 6, 7], 7)))
      [[2, 2, 3], [7]]
      >>> combination_sum([2], 1)
      []
      >>> combination_sum([2, 3], 0)
      [[]]

    思路提示:回溯 + 排序剪枝。
      - 先 sorted(candidates),否则不敢 break。
      - dfs(start, remain):remain 是还差多少;remain == 0 收 path.copy()。
      - 剪枝:if candidates[i] > remain → break(排序后后面更大,都不可能)。
      - 可重复选 → dfs(i, remain - cand) 传 i 不是 i+1;去重靠 range(start, n)。
    """
    # TODO: 先排序;remain==0 收 copy;cand > remain 就 break;dfs(i, ...) 可重复选
    ...


# =====================================================================
# §40.5 全排列 II (LC47) —— 回溯综合
# =====================================================================
def permute_unique(nums: list[int]) -> list[list[int]]:
    """LC47 全排列 II(数组可能含重复,返回不重复的全排列)。对应 tutorial §40.5。

    示例:
      >>> permute_unique([1, 1, 2])
      [[1, 1, 2], [1, 2, 1], [2, 1, 1]]
      >>> permute_unique([1, 1, 1])
      [[1, 1, 1]]
      >>> permute_unique([1])
      [[1]]

    思路提示:在 permute 骨架上加「排序 + 同层去重」两行。
      - 先 sorted(nums):等值相邻,才能和前一个比较。
      - 同层去重:if i > 0 and nums[i] == nums[i-1] and not used[i-1] → continue。
        含义:前一个等值元素已在本层选过又撤销(不在路径上)→ 本分支整棵重复。
      - 其余与 permute 完全相同:used 标记、append/pop 配对、叶子收 copy。
    """
    # TODO: sorted + permute 骨架 + 同层去重(等值且 used[i-1] 为 False → continue)
    ...


# =====================================================================
# §40.6 买卖股票最佳时机 (LC121) —— 贪心
# =====================================================================
def max_profit(prices: list[int]) -> int:
    """LC121 买卖股票的最佳时机(只允许一次交易,先买后卖;不赚返回 0)。
    对应 tutorial §40.6。

    示例:
      >>> max_profit([7, 1, 5, 3, 6, 4])
      5
      >>> max_profit([7, 6, 4, 3, 1])
      0
      >>> max_profit([])
      0

    思路提示:贪心,一次遍历维护两个变量。
      - min_price:历史最低价(初值 float('inf'),别用 0!);best:最大利润(初值 0)。
      - 每天 price:先当卖价算 price - min_price 更新 best,再更新 min_price。
      - 空数组循环不进,自然返回 0。
    """
    # TODO: 一次遍历维护 min_price 与 best;空数组返回 0
    ...


# =====================================================================
# §40.7 跳跃游戏 (LC55) —— 贪心
# =====================================================================
def can_jump(nums: list[int]) -> bool:
    """LC55 跳跃游戏(能否从下标 0 跳到最后下标)。对应 tutorial §40.7。

    示例:
      >>> can_jump([2, 3, 1, 1, 4])
      True
      >>> can_jump([3, 2, 1, 0, 4])
      False
      >>> can_jump([0])
      True

    思路提示:贪心,维护「当前最远可达位置」farthest。
      - 关键洞察:可达位置是连续区间 [0, farthest],能到 k 就能到 0..k。
      - 遍历 i:先判断 if i > farthest → False(顺序!先判断再更新);
        再 farthest = max(farthest, i + nums[i]);farthest >= n-1 → True。
      - 空数组 / 单元素都在末尾 → True。
    """
    # TODO: 维护 farthest;i > farthest 返回 False(在更新之前判断);够到末尾返回 True
    ...
