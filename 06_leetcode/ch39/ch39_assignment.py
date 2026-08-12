"""
Ch39 作业:动态规划(Dynamic Programming)。

DP 是面试核心。核心思想:**把大问题拆成子问题,记住子问题的答案避免重复计算**。
两种写法:
  - 自顶向下(记忆化搜索):写递归 + 用缓存记住已算的子问题。Python 用 @lru_cache
    写得极优雅;Java 要手写数组/HashMap 当缓存。
  - 自底向上(迭代 DP):从最小子问题开始填表,用 list 当 DP 表。

本章 8 道经典题,从 Easy 递进到 Hard,覆盖 DP 六大原型:
  1. 一维递推(爬楼梯:斐波那契型)
  2. 「以 i 结尾」(最大子数组和:Kadane)
  3. 「选 / 不选」(打家劫舍)
  4. 完全背包求最少(零钱兑换 + 哨兵)
  5. 「以 i 结尾」不连续版(LIS)
  6. 二维计数(不同路径)
  7. 二维双串(LCS)
  8. 二维双串升级(编辑距离 Hard)

纯 stdlib。在每处 TODO 写实现,然后:

    uv run pytest 06_leetcode/ch39/test_ch39_assignment.py -v

全绿 = 你掌握了 Ch39。
"""
from functools import lru_cache


# ========== §39.2 爬楼梯:climb_stairs ==========


def climb_stairs(n: int) -> int:
    """
    【爬楼梯 LC70 · §39.2】每次能爬 1 或 2 步,爬到第 n 阶有几种不同走法?(n >= 1)

    示例:
        climb_stairs(2)  -> 2   # 1+1, 2
        climb_stairs(3)  -> 3   # 1+1+1, 1+2, 2+1
        climb_stairs(5)  -> 8
        climb_stairs(1)  -> 1
        climb_stairs(10) -> 89

    提示(@lru_cache 记忆化递归):
        到达第 n 阶,最后一步要么从 n-1 爬 1 步、要么从 n-2 爬 2 步,
        所以 f(n) = f(n-1) + f(n-2),边界 f(1)=1, f(2)=2(斐波那契)。
        在内部递归函数上加 @lru_cache(None) 自动缓存子问题答案,把 O(2^n) 砍成 O(n)。
        也可写自底向上:dp[i] = dp[i-1] + dp[i-2]。
    """
    # TODO: 按上方「提示」实现(记忆化递归或自底向上填表均可)
    ...


# ========== §39.3 最大子数组和:max_sub_array ==========


def max_sub_array(nums: list[int]) -> int:
    """
    【最大子数组和 LC53 · §39.3】找一个【连续】子数组使其和最大,返回最大和。
    数组可含负数;保证至少有一个元素。

    示例:
        max_sub_array([-2, 1, -3, 4, -1, 2, 1, -5, 4]) -> 6   # [4,-1,2,1]
        max_sub_array([5, 4, -1, 7, 8])  -> 23  # 整个数组
        max_sub_array([1])               -> 1
        max_sub_array([-2, -1])          -> -1  # 全负时取最大的一个

    提示(Kadane,「以 i 结尾」状态):
        dp[i] = 以 nums[i] 结尾的连续子数组最大和 = max(nums[i], dp[i-1] + nums[i])。
        直觉:前面那段和是负的,就扔掉包袱从 nums[i] 重新开始。
        答案 = max(dp)(不是 dp[-1]!最大子数组可以以任何位置结尾)。
        用两个滚动变量 cur / best 即可 O(1) 空间;注意用 nums[0] 初始化,别用 0(全负数会错)。
    """
    # TODO: 按上方「提示」实现(cur = max(x, cur + x);best 全程取 max;nums[0] 初始化)
    ...


# ========== §39.4 打家劫舍:rob ==========


def rob(nums: list[int]) -> int:
    """
    【打家劫舍 LC198 · §39.4】一排房子每间有现金 nums[i],不能偷相邻两家,
    求最多能偷多少。

    示例:
        rob([1, 2, 3, 1])     -> 4   # 偷 1 号和 3 号:1+3
        rob([2, 7, 9, 3, 1])  -> 12  # 2+9+1
        rob([2, 1, 1, 2])     -> 4   # 贪心「见大就偷」只得 3,最优 2+2=4
        rob([])               -> 0
        rob([5])              -> 5

    提示(「选 / 不选」原型):
        dp[i] = 前 i 间房能偷到的最大值。
        对第 i 间:不偷 → dp[i-1];偷 → dp[i-2] + nums[i-1]。
        dp[i] = max(dp[i-1], dp[i-2] + nums[i-1])。
        边界 dp[0]=0, dp[1]=nums[0];滚动两个变量 prev2/prev1 即可 O(1) 空间。
        注意和爬楼梯对比:方案数用 +,最值用 max。
    """
    # TODO: 按上方「提示」实现(prev2, prev1 = prev1, max(prev1, prev2 + x))
    ...


# ========== §39.5 零钱兑换:coin_change ==========


def coin_change(coins: list[int], amount: int) -> int:
    """
    【零钱兑换 LC322 · §39.5】用最少的硬币凑成 amount,凑不出返回 -1。
    每种硬币无限个(完全背包)。

    示例:
        coin_change([1, 2, 5], 11) -> 3   # 5+5+1
        coin_change([1, 3, 4], 6)  -> 2   # 3+3(贪心 4+1+1=3 是错的)
        coin_change([2], 3)        -> -1
        coin_change([1], 0)        -> 0

    提示(自底向上 DP,完全背包求最小):
        dp[i] = 凑成金额 i 所需的最少硬币数。
        转移:dp[i] = min(dp[i-coin] + 1)  for coin in coins if coin <= i
        初始:dp[0] = 0,其余初始化成 amount+1(哨兵,表示"不可达")。
        最后 dp[amount] > amount 说明凑不出,返回 -1。
        哨兵用 amount+1 是因为最多用 amount 个 1 元硬币,真实答案不可能超过它。
        内层 if c <= i 必须判,否则 dp[i-c] 负下标会静默绕到表尾(Python 特有坑)。
    """
    # TODO: 按上方「提示」实现(自底向上,哨兵 amount+1,不可达返回 -1)
    ...


# ========== §39.6 最长递增子序列:length_of_lis ==========


def length_of_lis(nums: list[int]) -> int:
    """
    【最长递增子序列 LC300 · §39.6】返回严格递增子序列的最大长度(不要求连续)。

    示例:
        length_of_lis([10, 9, 2, 5, 3, 7, 101, 18]) -> 4   # [2,3,7,101]
        length_of_lis([0, 1, 0, 3, 2, 3])          -> 4    # [0,1,2,3]
        length_of_lis([1, 2, 3, 0])                -> 3    # 答案不在末尾!
        length_of_lis([7, 7, 7, 7])                -> 1
        length_of_lis([])                          -> 0

    提示(O(n^2) DP,「以 i 结尾」):
        dp[i] = 以 nums[i] 结尾的 LIS 长度,初始全 1(至少包含自己)。
        对所有 j<i 且 nums[j]<nums[i]:dp[i] = max(dp[i], dp[j]+1)。
        答案 = max(dp),不是 dp[-1](LIS 不一定以最后一个元素结尾)。
        空数组返回 0;严格递增用 < 不是 <=。
    """
    # TODO: 按上方「提示」实现(dp[i]=以 nums[i] 结尾的 LIS,答案 max(dp);空数组 0)
    ...


# ========== §39.7 不同路径:unique_paths ==========


def unique_paths(m: int, n: int) -> int:
    """
    【不同路径 LC62 · §39.7】m 行 n 列网格,从左上到右下,每步只能向右或向下,
    共有多少条不同路径?

    示例:
        unique_paths(3, 7)  -> 28
        unique_paths(3, 2)  -> 3
        unique_paths(1, 1)  -> 1
        unique_paths(1, 5)  -> 1   # 单行只有一条路

    提示(二维计数 DP):
        dp[i][j] = 走到 (i,j) 的路径数 = dp[i-1][j](上方) + dp[i][j-1](左方)。
        边界:第一行 / 第一列全 1(只能一直向右或一直向下)。
        建表用 [[1] * n for _ in range(m)] —— 千万别写 [[1]*n]*m(浅拷贝,m 行同一对象)!
        答案 = dp[m-1][n-1]。
        (验算彩蛋:math.comb(m+n-2, m-1) 一行可得同样答案。)
    """
    # TODO: 按上方「提示」实现(二维表,dp[i][j] = 上 + 左;边界全 1)
    ...


# ========== §39.8 最长公共子序列:longest_common_subsequence ==========


def longest_common_subsequence(text1: str, text2: str) -> int:
    """
    【最长公共子序列 LC1143 · §39.8】两个字符串的最长公共子序列长度(可不连续)。

    示例:
        longest_common_subsequence("abcde", "ace") -> 3   # "ace"
        longest_common_subsequence("abc", "abc")   -> 3
        longest_common_subsequence("abc", "def")   -> 0
        longest_common_subsequence("", "abc")      -> 0

    提示(二维 DP,双串):
        dp[i][j] = text1 前 i 个字符 与 text2 前 j 个字符 的 LCS 长度。
        - 若 text1[i-1]==text2[j-1]:dp[i][j] = dp[i-1][j-1] + 1(这对字符配对)
        - 否则:dp[i][j] = max(dp[i-1][j], dp[i][j-1])(各退一格取较大)
        边界:dp[0][*]=dp[*][0]=0(空串与任何串的 LCS=0),答案 = dp[len1][len2]。
        表开 (len1+1)x(len2+1) 让 i-1/j-1 不越界;
        建表用列表推导式 [[0]*(len2+1) for _ in range(len1+1)],别用 * 浅拷贝。
    """
    # TODO: 按上方「提示」实现(二维 DP;相等 +1,否则 max(上,左))
    ...


# ========== §39.9 编辑距离:min_distance ==========


def min_distance(word1: str, word2: str) -> int:
    """
    【编辑距离 LC72 Hard · §39.9】把 word1 变成 word2 最少需要几次操作
    (插入 / 删除 / 替换 一个字符)。

    示例:
        min_distance("horse", "ros")         -> 3
        min_distance("intention", "execution") -> 5
        min_distance("kitten", "sitting")    -> 3
        min_distance("abc", "abc")           -> 0   # 全白嫖
        min_distance("", "a")                -> 1   # 插 a
        min_distance("a", "")                -> 1   # 删 a

    提示(二维 DP,LCS 升级版——多了「替换」):
        dp[i][j] = word1 前 i 个字符 变成 word2 前 j 个字符 的最少操作数。
        - 若 word1[i-1]==word2[j-1]:dp[i][j] = dp[i-1][j-1](相等白嫖,不 +1!)
        - 否则 1 + min(
              dp[i-1][j],     # 删除 word1[i-1]
              dp[i][j-1],     # 在 word1 插入 word2[j-1]
              dp[i-1][j-1],   # 替换 word1[i-1] 成 word2[j-1]
          )
        边界必须显式填:dp[i][0] = i(全删),dp[0][j] = j(全插)。
    """
    # TODO: 按上方「提示」实现(相等白嫖;不等 1+min(删/插/替);边界 dp[i][0]=i, dp[0][j]=j)
    ...


# ---------------------------------------------------------------------
if __name__ == "__main__":
    print("climb_stairs(5) =", climb_stairs(5))  # 8
    print("max_sub_array([-2,1,-3,4,-1,2,1,-5,4]) =", max_sub_array([-2, 1, -3, 4, -1, 2, 1, -5, 4]))  # 6
    print("rob([2,7,9,3,1]) =", rob([2, 7, 9, 3, 1]))  # 12
    print("coin_change([1,2,5], 11) =", coin_change([1, 2, 5], 11))  # 3
    print("length_of_lis([10,9,2,5,3,7,101,18]) =", length_of_lis([10, 9, 2, 5, 3, 7, 101, 18]))  # 4
    print("unique_paths(3, 7) =", unique_paths(3, 7))  # 28
    print("longest_common_subsequence('abcde','ace') =", longest_common_subsequence("abcde", "ace"))  # 3
    print("min_distance('horse','ros') =", min_distance("horse", "ros"))  # 3
