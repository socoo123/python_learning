"""
Ch04 作业:函数 —— 一等公民、闭包、装饰器。

6 个函数覆盖:函数当参数/返回值、闭包、*args/**kwargs、装饰器(基础/带参/缓存)。
在每处 TODO 写实现,然后:

    uv run pytest 01_python_core/ch04/test_ch04_assignment.py -v

全绿 = 你掌握了 Ch04。

每题顶部的【对应小节】指向 tutorial.md 里的讲解。卡住 → 回查对应 §。
(提示只给思路和关键语法,不给完整代码——自己组合才有掌握感。)
"""
import functools


# ========== §4.1 函数是一等公民(高阶函数)==========


def apply_twice(func, x):
    """
    【高阶函数 · §4.1】把 func 连续作用两次,返回 func(func(x))。

    示例:
        apply_twice(lambda x: x + 3, 10)   -> 16   ( (10+3)+3 )
        apply_twice(lambda x: x * x, 2)    -> 16   ( (2*2)*(2*2) = 4*4 )

    思路:函数能当参数传(它就是个对象)。直接调用两次套起来返回即可。
    """
    # TODO: 返回 func(func(x))
    ...


# ========== §4.2 闭包 ==========


def make_multiplier(factor):
    """
    【闭包 · §4.2】返回一个【新函数】 multiplier(x),它记住外层的 factor,返回 x * factor。

    示例:
        triple = make_multiplier(3)
        triple(5)                  -> 15
        make_multiplier(10)(3)     -> 30   (每次调用造独立的闭包)

    思路:在 make_multiplier 内部【定义】一个内层函数 multiplier(x) 返回 x*factor,
         然后【return 这个内层函数】(不调用它)。内层函数捕获了外层的 factor 变量——这就是闭包。
    """
    # TODO: 定义内层函数并返回它
    ...


# ========== §4.3 *args / **kwargs ==========


def sum_prices(*prices) -> float:
    """
    【*args · §4.3】接受任意个价格参数,返回总和。无参返回 0。

    示例:
        sum_prices()                   -> 0
        sum_prices(599.0, 129.0, 99.0) -> 827.0

    思路:参数前的 * 让 prices 在函数内变成一个【元组】。直接 sum(prices)。
    """
    # TODO: prices 是元组,用 sum
    ...


def build_product(name, **fields) -> dict:
    """
    【**kwargs · §4.3】name 必填;其余任意「关键字=值」都收进 fields。
    返回合并后的字典 {"name": name, 加上所有 fields}。

    示例:
        build_product("机械键盘", price=599.0, stock=120)
            -> {"name": "机械键盘", "price": 599.0, "stock": 120}
        build_product("鼠标")  -> {"name": "鼠标"}

    思路:**fields 在函数内是个【字典】。返回新字典时,用 ** 把它【解包】进字面量:
         {"name": name, **fields}
    """
    # TODO: 返回 {"name": name, **fields}
    ...


# ========== §4.4 装饰器基础 ==========


def count_calls(func):
    """
    【装饰器基础 · §4.4】装饰器:统计 func 被调用的次数,结果存在 wrapper.call_count 上。

    示例:
        @count_calls
        def greet(name): return f"hi {name}"
        greet("a"); greet("b")
        greet.call_count   -> 2
        greet.__name__     -> "greet"   (functools.wraps 的功劳)

    思路:
      1. 定义内层 wrapper(*args, **kwargs):先把 wrapper.call_count 加 1,再 return func(*args, **kwargs)
      2. 用 @functools.wraps(func) 装饰 wrapper(保留原函数名/文档)
      3. 给 wrapper 加属性 wrapper.call_count = 0
      4. return wrapper
    """
    # TODO: 定义 wrapper + @functools.wraps + 加属性 + 返回
    ...


# ========== §4.5 带参数的装饰器 ==========


def retry(times):
    """
    【带参数的装饰器 · §4.5】retry(times=N) 是个【装饰器工厂】,返回真正的装饰器。
    被装饰函数若抛异常,最多重试到【累计调用 N 次】;N 次都失败则抛最后一次的异常。

    示例:
        @retry(times=3)
        def flaky(): ...
        # 失败会自动重试,最多调用 3 次

    思路(三层嵌套,这是带参装饰器的固定套路):
      1. 最外层 retry(times) 接收参数,返回 decorator
      2. 中层 decorator(func) 接收被装饰函数,返回 wrapper
      3. 最内层 wrapper(*args, **kwargs):for _ in range(times):
             try: return func(*args, **kwargs)
             except Exception as e: last_exc = e   # 记下异常,继续循环
         循环走完(都失败):raise last_exc
    """
    # TODO: 三层嵌套(decorator + wrapper),注意每层 return 什么
    ...


# ========== §4.6 缓存装饰器(综合)==========


def memoize(func):
    """
    【缓存装饰器 · §4.6】手写 memoize:相同入参只计算一次,结果存字典。
    禁止用 functools.lru_cache,自己实现。wrapper.miss_count 统计【真正调用 func】的次数。

    示例:
        @memoize
        def slow_square(x): ...   # 假设很慢
        slow_square(4)   # 计算并缓存,miss_count=1
        slow_square(4)   # 命中缓存,函数体不再执行,miss_count 仍=1

    思路:
      1. 闭包持有一个 cache = {} 字典
      2. wrapper(*args):args 天然可作为字典的键(元组)。
         if args not in cache: wrapper.miss_count += 1; cache[args] = func(*args)
         return cache[args]
      3. 给 wrapper 加 wrapper.miss_count = 0,return wrapper
    """
    # TODO: cache 字典 + wrapper(*args) + miss_count
    ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     uv run python 01_python_core/ch04/ch04_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    triple = make_multiplier(3)
    print("triple(5) =", triple(5))

    print("sum_prices =", sum_prices(599.0, 129.0, 99.0))
    print("build_product =", build_product("机械键盘", price=599.0, stock=120))

    @count_calls
    def greet(name):
        return f"hi {name}"
    greet("a"); greet("b")
    print("greet call_count =", greet.call_count)
