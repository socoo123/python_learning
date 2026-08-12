"""
Ch34 作业:Python 刷题利器总览(stdlib 工具箱)。

Java 老手刷 LeetCode 时,一半脑力耗在「样板代码」上:统计频次要 HashMap + 排序、
分组要 containsKey 判空、找 top-k 要 PriorityQueue、滑窗要手写队列、二分要手写
while、多键排序要 Comparator 链、前缀和要手写累加、轮转要三次反转、记忆化要手写
HashMap 缓存。Python 标准库把这九类高频套路全封装成了【一行调用】:

  1. collections.Counter.most_common   —— 频次统计 + top-k
  2. collections.defaultdict           —— 分组聚合,免去 containsKey 判空
  3. heapq.nlargest                    —— 第 k 大(小顶堆,不排全量)
  4. collections.deque(maxlen=n)       —— 定长滑动窗口,满了自动踢左边
  5. bisect.bisect_left                —— 有序数组二分查找 + 插入点
  6. sorted + key=lambda               —— 多键排序一行秒杀 Comparator 链
  7. itertools.accumulate              —— 前缀和(累加序列)
  8. 切片 nums[-k:] + nums[:-k]        —— 数组轮转(替代三次反转)
  9. functools.lru_cache               —— 记忆化递归(一个装饰器)
 10. float('inf') 哨兵                 —— 一趟扫描求最值的初始化技巧

10 个函数,纯 stdlib(collections / heapq / bisect / itertools / functools)。
前 9 题各练一件利器,第 10 题 array_report 是综合,复用前面的函数。

在每处 TODO 写实现,然后:

    uv run pytest 06_leetcode/ch34/test_ch34_assignment.py -v

全绿 = 你掌握了 Ch34,Pythonic 刷题的入门钥匙到手。

每题 docstring 顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
import heapq
from bisect import bisect_left
from collections import Counter, defaultdict, deque
from functools import lru_cache
from itertools import accumulate


# ========== §34.2 频次统计:char_frequency ==========


def char_frequency(text: str) -> list[tuple[str, int]]:
    """
    【Counter · §34.2】返回字符串中出现次数最多的前 3 个字符,按 (字符, 次数) 降序。

    对应 LeetCode 思路:LC347 前 K 个高频元素的字符版。

    示例:
        char_frequency("aabbbc")     -> [('b', 3), ('a', 2), ('c', 1)]
        char_frequency("mississippi") -> [('i', 4), ('s', 4), ('p', 2)]
        char_frequency("")           -> []
        char_frequency("ab")         -> [('a', 1), ('b', 1)]  # 不足 3 个返回实际数量

    思路(Counter + most_common,一行秒杀):
        Counter(text) 把可迭代对象统计成 {字符: 次数} 的 dict 子类。
        .most_common(3) 返回按次数降序的前 3 个 (元素, 次数) 元组列表;
        次数相同按【首次出现顺序】(Python 3.7+ 文档保证)。
        Java 要写 HashMap + merge + stream 排序;Python 一个 Counter 搞定。

    边界:
        - 空串 -> Counter 为空 -> most_common(3) 返回 [](不报错)。
        - 不足 3 种字符 -> 返回实际数量,不会补 None。
    """
    # TODO: Counter(text).most_common(3),一行
    ...


# ========== §34.3 分组免判空:sum_by_category ==========


def sum_by_category(records: list[tuple[str, int]]) -> dict[str, int]:
    """
    【defaultdict · §34.3】订单流水按类目汇总金额,返回 {类目: 总额}。

    records 是 (类目, 金额) 流水,同一类目出现多次要累加;金额可为负(退款)。

    示例:
        sum_by_category([("书", 30), ("衣", 200), ("书", 25)]) -> {"书": 55, "衣": 200}
        sum_by_category([("书", 30), ("书", -5)])              -> {"书": 25}  # 含退款
        sum_by_category([])                                    -> {}

    思路(defaultdict(int),免去 containsKey 判空):
        totals = defaultdict(int)   # 缺 key 时自动调 int() 得 0
        for cat, amount in records:
            totals[cat] += amount   # 不用 if cat in totals,直接 +=
        return dict(totals)         # 转回普通 dict,避免下游误触发自动建 key

        Java 等价:map.merge(cat, amount, Integer::sum)。
        对比普通 dict:totals[cat] = totals.get(cat, 0) + amount —— 也能跑,
        但 defaultdict 把「默认值是什么」声明在创建处,意图更清晰。

    边界:
        - 空流水 -> 空 dict。
        - 负数金额直接累加(退款场景)。
    """
    # TODO: defaultdict(int) → 循环 += → dict(...) 返回
    ...


# ========== §34.4 第 k 大:kth_largest ==========


def kth_largest(nums: list[int], k: int) -> int:
    """
    【heapq · §34.4】返回数组中第 k 大的元素(LC215 / LC703 简化版)。

    示例:
        kth_largest([3, 2, 1, 5, 6, 4], 2) -> 5   # 第 2 大是 5(6 是第 1 大)
        kth_largest([3, 2, 1, 5, 6, 4], 1) -> 6   # k=1 返回最大值
        kth_largest([3, 2, 1, 5, 6, 4], 6) -> 1   # k=len 返回最小值
        kth_largest([1], 1)                    -> 1

    思路(heapq.nlargest,一行秒杀):
        heapq.nlargest(k, nums) 返回最大的 k 个元素,【降序】列表;
        [-1] 取最后一个 = 第 k 大那个。
        k 远小于 n 时内部只维护 size=k 的小顶堆,O(n log k),
        比 sorted(nums, reverse=True)[k-1] 的 O(n log n) 省。

        Java 等价:PriorityQueue 小顶堆,超过 size 就 poll()。

    边界(题目保证 1 <= k <= len(nums)):
        - k == 1         -> 最大值;k == len(nums) -> 最小值。
        - 有重复元素时按「排序后第 k 个」理解:[5,5,4] 第 2 大是 5。
    """
    # TODO: heapq.nlargest(k, nums)[-1],一行;注意别漏 [-1]
    ...


# ========== §34.5 定长滑窗:moving_averages ==========


def moving_averages(nums: list[int], size: int) -> list[float]:
    """
    【deque(maxlen) · §34.5】滑动窗口平均值(LC346 数据流移动平均的离线版)。

    窗口从左到右滑过 nums,每步返回【当前窗口】的平均值;窗口未满时按实际长度平均。

    示例:
        moving_averages([1, 2, 3, 8], 2) -> [1.0, 1.5, 2.5, 5.5]
            # [1]=1.0 [1,2]=1.5 [2,3]=2.5 [3,8]=5.5
        moving_averages([3, 6, 9, 12], 3) -> [3.0, 4.5, 6.0, 9.0]
            # [3]=3.0 [3,6]=4.5 [3,6,9]=6.0 [6,9,12]=9.0
        moving_averages([], 3)           -> []
        moving_averages([1, 2], 5)       -> [1.0, 1.5]   # size > len:窗口永远装不满

    思路(deque(maxlen=size),定长队列自动踢旧):
        window = deque(maxlen=size)   # 满了再 append,自动从【左边】踢出最旧元素
        for x in nums:
            window.append(x)
            result.append(sum(window) / len(window))

        Java 的 ArrayDeque 没有 maxlen 语义,要自己 if (q.size() > n) q.poll();
        Python 的 deque(maxlen=n) 把「踢旧」内置了——这是它和 Java 最大的差异。

    边界:
        - 空数组 -> [](循环不执行)。
        - size >= 1(题目保证);size > len(nums) 时窗口始终 = 当前已见全部元素。
    """
    # TODO: deque(maxlen=size) → 逐个 append → 每步 sum(window)/len(window) 收集
    ...


# ========== §34.6 二分查找插入点:search_insert_pos ==========


def search_insert_pos(nums: list[int], target: int) -> int:
    """
    【bisect · §34.6】升序数组找 target 下标,找不到返回它该插入的位置(LC35)。

    示例:
        search_insert_pos([1, 3, 5, 6], 5) -> 2   # 命中,下标 2
        search_insert_pos([1, 3, 5, 6], 2) -> 1   # 2 不在,插到 3 前面
        search_insert_pos([1, 3, 5, 6], 7) -> 4   # 比所有都大,插末尾
        search_insert_pos([1, 3, 5, 6], 0) -> 0   # 比所有都小,插开头
        search_insert_pos([], 5)            -> 0   # 空数组

    思路(bisect.bisect_left,一行秒杀):
        bisect_left(升序数组, target) 返回【第一个 >= target 的下标】:
          - target 在数组里 -> 就是它的位置(命中)。
          - target 不在     -> 就是它「为保持有序」该插入的位置。
        两种语义一行统一,不用写 if。

        Java 的 Arrays.binarySearch 找不到时返回 -(insertionPoint)-1,
        还得取反换算;手写 while (lo <= hi) 更是边界地狱。

    边界:
        - 前提:nums 【已升序】,bisect 不检查,传乱序结果无意义。
        - 空数组 -> 0;target 最小 -> 0;target 最大 -> len(nums)。
        - 有重复时 left 返回最左那个 >= target(LC35 要的语义)。
    """
    # TODO: bisect_left(nums, target),一行
    ...


# ========== §34.7 多键排序:sort_students ==========


def sort_students(records: list[tuple[str, int]]) -> list[tuple[str, int]]:
    """
    【sorted + key · §34.7】成绩榜排序:分数【降序】,同分按名字【字典序升序】。

    records 是 (姓名, 分数) 列表。返回【新列表】,不得修改入参。

    示例:
        sort_students([("amy", 90), ("bob", 95), ("ada", 95), ("zed", 80)])
            -> [("ada", 95), ("bob", 95), ("amy", 90), ("zed", 80)]
            # 95 同分:"ada" < "bob" 字典序在前
        sort_students([("solo", 60)]) -> [("solo", 60)]
        sort_students([])             -> []

    思路(key 返回元组,数值键取负):
        return sorted(records, key=lambda r: (-r[1], r[0]))
        - key 算出 (-分数, 姓名) 元组,sorted 按元组【逐元素】比较:
          先比 -分数(负号把降序转升序),打平再比姓名(升序)。
        - Java 等价:Comparator.comparing(Student::score).reversed()
                              .thenComparing(Student::name),三行链式。

        坑:字符串键不能取负(-"amy" 会 TypeError),只有数值能加负号;
        字符串要降序得用 reverse 参数或借助稳定性两次排(见 tutorial)。

    边界:
        - 空列表 -> []。
        - sorted 返回新列表,入参不动(别用 list.sort(),那是原地排序)。
    """
    # TODO: sorted(records, key=lambda r: (-r[1], r[0])),一行
    ...


# ========== §34.8 前缀和:running_sum ==========


def running_sum(nums: list[int]) -> list[int]:
    """
    【itertools.accumulate · §34.8】一维数组的前缀和(LC1480 动态和)。

    返回第 i 项 = nums[0] + ... + nums[i] 的累加序列。前缀和是「区间和」类题目的
    地基(Ch36 的 LC560 和为 K 的子数组就要用它)。

    示例:
        running_sum([1, 2, 3, 4])    -> [1, 3, 6, 10]
        running_sum([1, 1, 1, 1, 1]) -> [1, 2, 3, 4, 5]
        running_sum([-1, 1])         -> [-1, 0]          # 支持负数
        running_sum([])              -> []

    思路(itertools.accumulate,一行秒杀):
        return list(accumulate(nums))
        - accumulate(nums) 返回【迭代器】,产出累计值,要 list() 物化。
        - Java 没有对应物,得手写 sum += nums[i] 的循环。

        进阶(教程有):accumulate(nums, func=operator.mul) 变前缀积;
        accumulate(nums, initial=0) 在开头补 0(区间和公式常用)。

    边界:
        - 空列表 -> [](accumulate 空迭代,list 得 [])。
        - 负数正常累加。
    """
    # TODO: list(accumulate(nums)),一行;别忘 list()
    ...


# ========== §34.9 切片轮转:rotate_array ==========


def rotate_array(nums: list[int], k: int) -> list[int]:
    """
    【切片 · §34.9】数组向右轮转 k 位,返回【新列表】(LC189 的非原地版)。

    示例:
        rotate_array([1, 2, 3, 4, 5, 6, 7], 3) -> [5, 6, 7, 1, 2, 3, 4]
        rotate_array([1, 2], 3)                -> [2, 1]   # k > len:先取模 3%2=1
        rotate_array([1, 2, 3], 0)             -> [1, 2, 3]
        rotate_array([], 5)                    -> []

    思路(切片拼接,一行秒杀):
        if not nums:
            return []                       # k % 0 会 ZeroDivisionError,先挡空数组
        k %= len(nums)                      # k 可能大于长度,取模归一
        return nums[-k:] + nums[:-k]        # 尾部 k 个切下来,拼到前面

        - nums[-k:]  = 最后 k 个元素;nums[:-k] = 除最后 k 个之外的前段。
        - Java 的经典解法是「三次反转」或 System.arraycopy 拼图;Python 切片直接拼。
        - 教程还会讲:为什么 k=0 时 nums[-0:] 碰巧正确(-0 == 0),以及
          星号写法 [*nums[-k:], *nums[:-k]]。

    边界:
        - 空数组 -> [](必须先判,否则 k % 0 崩)。
        - k == 0 或 k == len(nums) 的整数倍 -> 内容不变的拷贝。
    """
    # TODO: 先挡空数组 → k %= len(nums) → nums[-k:] + nums[:-k]
    ...


# ========== §34.10 记忆化递归:fib ==========


@lru_cache(maxsize=None)
def fib(n: int) -> int:
    """
    【lru_cache · §34.10】斐波那契第 n 项(LC509):fib(0)=0, fib(1)=1。

    示例:
        fib(0)  -> 0
        fib(1)  -> 1
        fib(10) -> 55
        fib(20) -> 6765
        fib(50) -> 12586269025   # 普通递归这里会指数爆炸,记忆化后秒出

    思路(@lru_cache 一个装饰器秒杀):
        裸递归 fib(n) = fib(n-1) + fib(n-2) 会重复计算同一子问题,O(2^n)。
        记忆化 = 把算过的 (n -> 结果) 存起来,下次直接查表,降到 O(n)。

        Java 要手写:Map<Integer, Long> cache,先 containsKey 查、算完再 put。
        Python 只在 def 上加 @lru_cache(maxsize=None),递归体原封不动。

        maxsize=None = 缓存不限条数(本题 n 小,够用);
        参数空间巨大时设具体条数,LRU 自动淘汰最久未用。

    边界:
        - 递归基:n < 2 返回 n(即 fib(0)=0, fib(1)=1)。
        - n < 0 题目不要求;想防御可 raise ValueError。

    注意:
        - 被装饰函数的参数必须 hashable(int 没问题;list 会 TypeError)。
        - 装饰器已就位,别删 @lru_cache 那一行。
    """
    # TODO: 递归基 if n < 2: return n;否则 fib(n-1) + fib(n-2)
    ...


# ========== §34.11 综合 + inf 哨兵:array_report ==========


def array_report(nums: list[int], k: int) -> dict:
    """
    【综合 · §34.11】给整数数组出一份「速览报告」dict,复用本章前面的函数。

    返回:
        {
            "count":       元素个数,
            "min":         最小值(用 float('inf') 哨兵一趟扫描,【不准】调 min()),
            "kth_largest": 第 k 大(复用 §34.4 的 kth_largest),
            "prefix_sums": 前缀和(复用 §34.8 的 running_sum),
        }
    空数组返回 {"count": 0, "min": None, "kth_largest": None, "prefix_sums": []}。

    示例:
        array_report([3, 1, 4, 1, 5], 2)
            -> {"count": 5, "min": 1, "kth_largest": 4, "prefix_sums": [3, 4, 8, 9, 14]}
        array_report([7], 1)
            -> {"count": 1, "min": 7, "kth_largest": 7, "prefix_sums": [7]}
        array_report([], 1)
            -> {"count": 0, "min": None, "kth_largest": None, "prefix_sums": []}

    思路(float('inf') 哨兵 + 函数复用):
        if not nums:
            return {"count": 0, "min": None, "kth_largest": None, "prefix_sums": []}
        min_val = float("inf")         # 「比任何数都大」的哨兵,第一个元素必刷新它
        for x in nums:
            if x < min_val:
                min_val = x
        return {
            "count": len(nums),
            "min": min_val,
            "kth_largest": kth_largest(nums, k),   # 复用 §34.4
            "prefix_sums": running_sum(nums),      # 复用 §34.8
        }

        为什么练手写 inf 扫描而不是 min(nums)?面试常要求「一趟循环同时干多件事」
        (比如同时求 min 和 max),那时 min() 帮不了你,inf 哨兵是标准起手式。
        Java 等价:Integer.MAX_VALUE / Double.POSITIVE_INFINITY。

    边界:
        - 空数组 -> 按上方约定的 dict(min / kth_largest 为 None)。
        - 题目保证非空时 1 <= k <= len(nums)。
    """
    # TODO: 空数组特判 → float('inf') 哨兵一趟扫 min → 复用 kth_largest / running_sum
    ...
