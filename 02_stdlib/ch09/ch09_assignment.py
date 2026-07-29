"""
Ch09 作业:itertools + functools —— 函数式利器。

5 个任务。在每处 TODO 写实现,然后:

    uv run pytest 02_stdlib/ch09/test_ch09_assignment.py -v

全绿 = 你掌握了 Ch09。

每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
from functools import lru_cache, reduce
from itertools import chain, combinations, groupby
from operator import mul


# ========== §9.1 itertools.chain ==========


def flatten(*lists):
    """
    【chain · §9.1】把传入的多个列表【串联】成一条流,返回扁平化的 list。

    示例:
        flatten([1,2], [3,4])       -> [1,2,3,4]
        flatten([1], [2,3], [4])    -> [1,2,3,4]

    思路:itertools.chain(*lists) 把多个可迭代对象首尾相接。包一层 list() 物化。
    """
    # TODO: list(chain(*lists))
    ...


# ========== §9.2 itertools.groupby(必须先排序!)==========


def group_by_sorted(items, key_func):
    """
    【groupby · §9.2】按 key_func 分组,返回 {key: [items]}。

    示例:
        group_by_sorted([1,2,1,3,2], lambda x: x)  -> {1:[1,1], 2:[2,2], 3:[3]}

    ⚠️ 关键陷阱:groupby 只合并【相邻】的相同 key。所以【必须先用 sorted 排序】,
       否则 [1,2,1] 会被分成 (1→[1])、(2→[2])、(1→[1]) 三组而不是 {1:[1,1]}。

    思路:
        ordered = sorted(items, key=key_func)
        return {k: list(g) for k, g in groupby(ordered, key=key_func)}
    """
    # TODO: 先 sorted,再 groupby 字典推导
    ...


# ========== §9.3 itertools.combinations ==========


def pair_combinations(items):
    """
    【combinations · §9.3】返回所有【两两组合】,list of tuple。

    示例:
        pair_combinations(["a","b","c"])  -> [("a","b"),("a","c"),("b","c")]
        pair_combinations([1,2,3,4])      -> 长度 6(= C(4,2))

    思路:itertools.combinations(items, 2) 生成所有 2 元子集。包 list()。
    """
    # TODO: list(combinations(items, 2))
    ...


# ========== §9.4 functools.reduce ==========


def multiply_all(nums):
    """
    【reduce · §9.4】连乘所有数。空列表返回 1(乘法单位元)。

    示例:
        multiply_all([2,3,4])  -> 24
        multiply_all([])       -> 1

    思路:functools.reduce(函数, 可迭代, 初始值) 反复把函数作用到累积值上:
        reduce(mul, [2,3,4], 1) = ((1*2)*3)*4 = 24
        mul 从 operator 导入(就是 a*b)。第三个参数 1 是初始值(空列表时返回它)。
    """
    # TODO: reduce(mul, nums, 1)
    ...


# ========== §9.5 functools.lru_cache ==========


# TODO: 给下面这个函数加上 @lru_cache(maxsize=None) 装饰器(开启无限缓存)
def cached_fib(n):
    """
    【lru_cache · §9.5】斐波那契,用 @lru_cache 记忆化,大 n 也秒算。
    fib(0)=0, fib(1)=1, fib(n)=fib(n-1)+fib(n-2)。

    示例:
        cached_fib(10)  -> 55
        cached_fib(50)  -> 12586269025   (没缓存会慢到不可用)

    思路:① 在 def 上一行加 @lru_cache(maxsize=None);
         ② 写普通递归:if n < 2: return n; return cached_fib(n-1) + cached_fib(n-2)
         装饰器会自动缓存每次调用的结果,重复调用直接命中。
    """
    # TODO: 加 @lru_cache 装饰器 + 递归实现
    ...


# ---------------------------------------------------------------------
if __name__ == "__main__":
    print("flatten:", flatten([1, 2], [3, 4]))
    print("group:", group_by_sorted([1, 2, 1, 3, 2], lambda x: x))
    print("pairs:", pair_combinations(["a", "b", "c"]))
    print("product:", multiply_all([2, 3, 4]))
    print("fib(50):", cached_fib(50))
    print("cache_info:", cached_fib.cache_info())
