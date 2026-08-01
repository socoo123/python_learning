"""
Ch39 作业:动态规划(Dynamic Programming)。

DP 是面试核心。核心思想:**把大问题拆成子问题,记住子问题的答案避免重复计算**。
两种写法:
  - 自顶向下(记忆化搜索):写递归 + 用缓存记住已算的子问题。Python 用 @lru_cache
    写得极优雅;Java 要手写数组/HashMap 当缓存。
  - 自底向上(迭代 DP):从最小子问题开始填表,用 list 当 DP 表。

本章 5 道经典题,覆盖 DP 三大原型:
  1. 一维递推(爬楼梯:斐波那契型)
  2. 背包/凑硬币(完全背包求最少硬币)
  3. 子序列(LIS、LCS)
  4. 区间/双串(编辑距离)

纯 stdlib。在每处 TODO 写实现,然后:

    uv run pytest 06_leetcode/ch39/test_ch39_assignment.py -v

全绿 = 你掌握了 Ch39。
"""
from functools import lru_cache


# ========== §39.2 爬楼梯:climb_stairs ==========


def climb_stairs(n: int) -> int:
    """
    【爬楼梯 LC70 · §39.2】每次能爬 1 或 2 步,爬到第 n 阶有几种不同走法?

    示例:
        climb_stairs(2) -> 2   # 1+1, 2
        climb_stairs(3) -> 3   # 1+1+1, 1+2, 2+1
        climb_stairs(5) -> 8
        climb_stairs(1) -> 1

    思路(@lru_cache 记忆化递归,f(n)=f(n-1)+f(n-2)):
        到达第 n 阶,最后一步要么从 n-1 爬 1 步、要么从 n-2 爬 2 步,
        所以走法 = f(n-1) + f(n-2)。这就是斐波那契,f(1)=1, f(2)=2。
        用 @lru_cache(None) 自动缓存子问题答案,避免指数级重复计算。
    """
    # TODO: 按上方「思路」实现(可用 @lru_cache 记忆化:f(n)=f(n-1)+f(n-2),f(1)=1,f(2)=2)
    ...


# ========== §39.3 零钱兑换:coin_change ==========


def coin_change(coins: list[int], amount: int) -> int:
    """
    【零钱兑换 LC322 · §39.3】用最少的硬币凑成 amount,凑不出返回 -1。每种硬币无限个。

    示例:
        coin_change([1,2,5], 11)  -> 3   # 5+5+1
        coin_change([2], 3)       -> -1
        coin_change([1], 0)       -> 0
        coin_change([1], 2)       -> 2

    思路(自底向上 DP,完全背包求最小):
        dp[i] = 凑成金额 i 所需的最少硬币数。
        转移:dp[i] = min(dp[i-coin] + 1)  for coin in coins if coin <= i
        初始:dp[0] = 0(金额 0 不要硬币),其余初始化成 amount+1(表示"无穷大/不可达")。
        最后 dp[amount] > amount 说明凑不出,返回 -1。
        用 amount+1 当哨兵是因为最多用 amount 个 1 元硬币,真实答案不可能超过它。
    """
    # TODO: 按上方「思路」实现(自底向上 DP,dp[i]=min(dp[i-c]+1),哨兵 amount+1)
    ...


# ========== §39.4 最长递增子序列:length_of_lis ==========


def length_of_lis(nums: list[int]) -> int:
    """
    【最长递增子序列 LC300 · §39.4】返回严格递增子序列的最大长度(不要求连续)。

    示例:
        length_of_lis([10,9,2,5,3,7,101,18]) -> 4   # [2,3,7,101] 或 [2,5,7,101]
        length_of_lis([0,1,0,3,2,3])         -> 4   # [0,1,2,3]
        length_of_lis([7,7,7,7])             -> 1
        length_of_lis([])                    -> 0

    思路(O(n^2) DP):
        dp[i] = 以 nums[i] 结尾的 LIS 长度。
        对所有 j<i 且 nums[j]<nums[i]:dp[i] = max(dp[i], dp[j]+1)。
        全程初始化 dp[i]=1(至少包含自己)。答案 = max(dp)。
        空数组返回 0。
    """
    # TODO: 按上方「思路」实现(dp[i]=以 nums[i] 结尾的 LIS,答案 max(dp);空数组 0)
    ...


# ========== §39.5 最长公共子序列:longest_common_subsequence ==========


def longest_common_subsequence(text1: str, text2: str) -> int:
    """
    【最长公共子序列 LC1143 · §39.5】两个字符串的最长公共子序列长度(可不连续)。

    示例:
        longest_common_subsequence("abcde", "ace") -> 3   # "ace"
        longest_common_subsequence("abc", "abc")   -> 3
        longest_common_subsequence("abc", "def")   -> 0

    思路(二维 DP):
        dp[i][j] = text1 前 i 个字符 与 text2 前 j 个字符 的 LCS 长度。
        - 若 text1[i-1]==text2[j-1]:dp[i][j] = dp[i-1][j-1] + 1  (这对字符配对)
        - 否则:dp[i][j] = max(dp[i-1][j], dp[i][j-1])  (扔掉一个字符取较大)
        初始:dp[0][*]=dp[*][0]=0(空串与任何串的 LCS=0)。
        答案 = dp[len1][len2]。
        为了让 i-1/j-1 不越界,dp 表开 (len1+1)x(len2+1),第 0 行/列全 0。
    """
    # TODO: 按上方「思路」实现(二维 DP;相等 +1,否则 max(上,左))
    ...


# ========== §39.6 编辑距离:min_distance ==========


def min_distance(word1: str, word2: str) -> int:
    """
    【编辑距离 LC72 Hard · §39.6】把 word1 变成 word2 最少需要几次操作
    (插入 / 删除 / 替换 一个字符)。

    示例:
        min_distance("horse", "ros")     -> 3   # horse->rorse->rose->ros
        min_distance("intention", "execution") -> 5
        min_distance("", "")             -> 0
        min_distance("a", "")            -> 1   # 删 a
        min_distance("", "a")            -> 1   # 插 a

    思路(二维 DP,LCS 的升级版——多了"替换"操作):
        dp[i][j] = word1 前 i 个字符 变成 word2 前 j 个字符 的最少操作数。
        - 若 word1[i-1]==word2[j-1]:dp[i][j] = dp[i-1][j-1]  (这对字符已相等,不操作)
        - 否则取三种操作的最小值 +1:
            dp[i-1][j]   + 1   # 删除 word1[i-1]
            dp[i][j-1]   + 1   # 在 word1 插入一个字符(等价于删除 word2[j-1])
            dp[i-1][j-1] + 1   # 替换 word1[i-1] 成 word2[j-1]
        初始:
            dp[i][0] = i  (把 word1 前 i 个字符全删了变成空串)
            dp[0][j] = j  (从空串插入 j 个字符变成 word2 前 j 个)
    """
    # TODO: 按上方「思路」实现(二维 DP;相等不+1,否则 1+min(删/插/替);边界 dp[i][0]=i,dp[0][j]=j)
    ...


# ---------------------------------------------------------------------
if __name__ == "__main__":
    print("climb_stairs(5) =", climb_stairs(5))  # 8
    print("coin_change([1,2,5], 11) =", coin_change([1, 2, 5], 11))  # 3
    print("length_of_lis([10,9,2,5,3,7,101,18]) =", length_of_lis([10, 9, 2, 5, 3, 7, 101, 18]))  # 4
    print("longest_common_subsequence('abcde','ace') =", longest_common_subsequence("abcde", "ace"))  # 3
    print("min_distance('horse','ros') =", min_distance("horse", "ros"))  # 3
