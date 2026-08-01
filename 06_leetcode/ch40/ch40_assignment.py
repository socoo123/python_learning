"""
Ch40 · 回溯 / 贪心 + 综合(M6 LeetCode 实战收官章)

本章主题:
  - 回溯(Backtracking)= DFS + 撤销选择。三道经典:全排列 / 子集 / 组合总和。
    Python 里回溯模板极简:`for x in 选择: 路径.append(x); dfs(); 路径.pop()`,
    append/pop 配对 = 「做选择 / 撤销选择」,比 Java 的 list.add/remove 干净。
  - 贪心(Greedy)= 每步取局部最优。两道经典:股票一次交易 / 跳跃游戏。
    贪心没有通用模板,关键是想清楚「局部最优 = 全局最优」的贪心选择性。

跑测试:
  uv run pytest 06_leetcode/ch40/test_ch40_assignment.py -v

约定:
  - 纯 stdlib,不 import 外部库。
  - 每个函数顶部 docstring 指向 tutorial 对应 §,给「思路」提示。
  - LeetCode 返回的列表答案「顺序不限」时,测试用 sorted 或集合比较。
"""

from __future__ import annotations


# =====================================================================
# §40.2 全排列 (LC46)
# =====================================================================
def permute(nums: list[int]) -> list[list[int]]:
    """LC46 全排列(无重复元素)。对应 tutorial §40.2。

    思路:回溯 + used 标记数组。
      - 路径 path 记录当前已选元素;used[i] 标记 nums[i] 是否已用。
      - 每层 for 遍历所有 nums,跳过 used 的,选一个 → dfs → 撤销(pop + used=False)。
      - path 长度 == nums 长度时收集一份拷贝(path 还要被后续分支复用,必须 copy)。
    复杂度:时间 O(n * n!),空间 O(n)(递归栈 + path + used)。
    """
    # TODO: 按上方「思路」实现(回溯 + used 标记;path 满长度收集 copy;append/pop 配对)
    ...


# =====================================================================
# §40.3 子集 (LC78)
# =====================================================================
def subsets(nums: list[int]) -> list[list[int]]:
    """LC78 子集(无重复元素,返回所有子集含空集)。对应 tutorial §40.3。

    思路:回溯「选 / 不选」,用 start 下标避免重复选前面的元素。
      - 每到一个节点先把当前 path 收进结果(子集问题每个节点都是答案,
        不像全排列要等叶子)。
      - for i in range(start, n):选 nums[i] → dfs(i+1) → pop 撤销。
      - start 保证每个元素只往后选,不会出现 [2,1] 和 [1,2] 重复。
    复杂度:时间 O(n * 2^n)(2^n 个子集,每个拷贝 O(n)),空间 O(n)。
    """
    # TODO: 按上方「思路」实现(回溯 + start 下标;每节点收集 copy;选 i → dfs(i+1) → pop)
    ...


# =====================================================================
# §40.4 组合总和 (LC39)
# =====================================================================
def combination_sum(candidates: list[int], target: int) -> list[list[int]]:
    """LC39 组合总和(候选无重复、每个可无限次用,返回所有和=target 的组合)。
    对应 tutorial §40.4。

    思路:回溯 + 排序剪枝。
      - 先排序 candidates,方便剪枝。
      - dfs(start, remain):从 start 往后选(保证不重复),remain 是还差多少凑够。
      - remain == 0 收集答案;remain < 0 不可能(剪枝保证不会到这)。
      - 剪枝:for 里若 candidates[i] > remain,后面更大,直接 break(排序的功劳)。
      - 可重复用同一元素 → dfs(i, ...)(不是 i+1);去重靠「只往后选」(i 不是 i-1)。
    复杂度:最坏指数级(取决于候选与 target),空间 O(target/min)(递归深度)。
    """
    # TODO: 按上方「思路」实现(排序剪枝;remain==0 收集;dfs(i,...) 可重复选;cand>remain break)
    ...


# =====================================================================
# §40.5 买卖股票最佳时机 (LC121) —— 贪心
# =====================================================================
def max_profit(prices: list[int]) -> int:
    """LC121 买卖股票的最佳时机(只允许一次交易)。对应 tutorial §40.5。

    思路:贪心,一次遍历。
      - 维护历史最低价 min_price 和当前最大利润 best。
      - 每天当作「卖出日」:能赚 = price - min_price,更新 best;
        再用今天的 price 更新 min_price(为后面做准备)。
      - 「今天卖出」vs「今天买入」的顺序无所谓——更新 best 先于更新 min_price,
        保证买卖不是同一天(其实同一天利润 0 也不影响)。
    复杂度:时间 O(n),空间 O(1)。
    """
    # TODO: 按上方「思路」实现(一次遍历维护 min_price 与 best;空数组返回 0)
    ...


# =====================================================================
# §40.6 跳跃游戏 (LC55) —— 贪心
# =====================================================================
def can_jump(nums: list[int]) -> bool:
    """LC55 跳跃游戏(能否从下标 0 跳到末尾)。对应 tutorial §40.5/§40.6。

    思路:贪心,维护「当前最远可达位置」farthest。
      - 从左到右遍历,若 i > farthest 说明这个位置到不了 → False。
      - 否则用 nums[i] 更新 farthest = max(farthest, i + nums[i])。
      - farthest >= 末尾下标 → True。
      - 关键洞察:可达位置是连续的区间 [0, farthest],不存在「跳得过去但中间够不到」。
    复杂度:时间 O(n),空间 O(1)。
    """
    # TODO: 按上方「思路」实现(贪心维护 farthest;i>farthest 返回 False,够到末尾返回 True)
    ...
