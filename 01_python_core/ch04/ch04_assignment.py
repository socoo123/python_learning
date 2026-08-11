"""
Ch04 作业:函数 —— 一等公民、闭包、装饰器。

场景:你在电商后台负责「营销 + 稳定性」两条工具线——
上午给运营做促销工具(试算折扣、发券工厂、购物车合计、统一 API 响应体);
下午给服务加稳定性埋点(调用计数、耗时统计、失败重试、结果缓存)。

8 个函数,每个刚好砸在一个函数知识点上。
在每处 TODO 写你的实现,然后:

    uv run pytest 01_python_core/ch04/test_ch04_assignment.py -v

全绿 = 你掌握了 Ch04。

每题 docstring 里标了【对应小节】,卡住 → 回 tutorial.md 查对应 §。
(提示只给思路和关键语法,不给完整代码——自己组合才有掌握感。)
"""
import functools
import time


# ========== §4.1 函数是一等公民 ==========


def apply_discount(prices: list[float], discount_fn) -> list[float]:
    """
    【场景】运营做大促前要先「试算」:同一批商品价格,分别套不同算法
    (全场半价、每单减 20……)看效果。算法本身也是一个函数,当参数传进来。

    【转换点】函数是一等公民:函数就是个对象,能当参数传(≈ Java 的
    Function<Double,Double>,但没有接口包袱)。注意:传参时写 discount_fn
    【不带括号】——带括号就变成「先调用、传结果」了。

    任务:返回对 prices 每个元素应用 discount_fn 后的【新列表】(不改原列表)。
         边界:空列表返回 []。
    示例:
        apply_discount([100.0, 200.0], lambda p: p * 0.5)        -> [50.0, 100.0]
        apply_discount([100.0, 200.0], lambda p: max(p - 20, 0)) -> [80.0, 180.0]
        apply_discount([], lambda p: p)                          -> []

    提示:
        return [discount_fn(p) for p in prices]
    """
    # TODO: 一行列表推导式,对每个 p 调用 discount_fn(p)
    ...


# ========== §4.2 闭包 ==========


def make_coupon(threshold: float, off: float):
    """
    【场景】运营后台发券:满 200 减 30、满 500 减 80……每种券逻辑一样,
    只是门槛/减额不同。写一个【工厂函数】批量印券:传入门槛和减额,
    返回一张「券」(函数),结算时调用它算出券后价。

    【转换点】闭包 = 内层函数 + 它记住的外层变量。make_coupon 返回后,
    threshold/off 本该消亡,但内层函数 coupon 捕获了它们——只要券还在,
    参数就一直活着。每次调用工厂造出独立闭包,各记各的。
    (≈ Java lambda 捕获 effectively final,但 Python 用嵌套 def 写。)

    任务:返回内层函数 coupon(price):
         price 满 threshold(含等于)→ 返回 price - off;否则返回原价。
         边界:刚好等于门槛也要减(测试会查)。
    示例:
        coupon = make_coupon(200, 30)
        coupon(599.0)   -> 569.0
        coupon(150.0)   -> 150.0   (不够门槛)
        coupon(200.0)   -> 170.0   (满门槛含等于)
        make_coupon(500, 80)(600.0) -> 520.0   (每张券独立记忆)

    提示:
        def coupon(price):
            return price - off if price >= threshold else price
        return coupon      # 返回函数对象,【不加括号】!
    """
    # TODO: 定义内层函数 coupon 并返回它(返回时不加括号)
    ...


# ========== §4.3 *args / **kwargs ==========


def cart_total(*prices) -> float:
    """
    【场景】结算页购物车有几件商品不确定,让函数「来几件收几件」,
    返回合计金额。

    【转换点】*args:参数前的 * 让 prices 在函数内变成一个【元组】,
    收集所有多余的位置参数。Java 的 double... prices 最接近,但 Python
    还可以同时有 **kwargs(下题)。
    ⚠️ 调用处若手上是列表,必须 cart_total(*prices) 打散——直接传
    cart_total(prices) 会把整个列表塞进元组的第一个位置!

    任务:返回所有价格之和;无参返回 0。
    示例:
        cart_total(599.0, 159.0, 75.5) -> 833.5
        cart_total()                   -> 0
        cart_total(*[599.0, 159.0])    -> 758.0   (调用处 * 打散列表)

    提示:
        return sum(prices)     # prices 已是元组,别再加 *
    """
    # TODO: prices 是元组,用 sum
    ...


def build_response(data, **meta) -> dict:
    """
    【场景】后端约定:所有接口返回统一响应体 {"ok": True, "data": ...},
    再带分页等元信息(total/page/...)。元信息字段不确定,用 **kwargs 全收。

    【转换点】**kwargs:参数前的 ** 让 meta 在函数内变成一个【字典】,
    收集所有多余的关键字参数。返回时用 **meta 把这个字典【解包】铺进
    新字典字面量(Ch02 的字典合并语法)。这是 FastAPI(Ch14+)自动解析
    查询参数的语法地基。

    任务:返回 {"ok": True, "data": data, 加上 meta 里所有键值对};
         meta 必须【展开铺平】,不能嵌套成 {"meta": {...}};无 meta 也合法。
    示例:
        build_response(["机械键盘", "无线鼠标"], total=10, page=1)
            -> {"ok": True, "data": ["机械键盘", "无线鼠标"], "total": 10, "page": 1}
        build_response("pong")  -> {"ok": True, "data": "pong"}

    提示:
        return {"ok": True, "data": data, **meta}
    """
    # TODO: 返回 {"ok": True, "data": data, **meta}
    ...


# ========== §4.4 装饰器基础 ==========


def count_calls(func):
    """
    【场景】监控埋点:想统计「价格查询」这类函数被调用了多少次,
    但【不能改原函数源码】(别处还在引用)。用装饰器包一层。

    【转换点】装饰器 = 「接收函数、返回新函数」的函数。
    @count_calls 贴在 def 上,等价于 query_price = count_calls(query_price)
    ——在函数【定义时】执行一次,把名字指向包装版。
    铁律:wrapper 永远用 *args, **kwargs 通用签名 + @functools.wraps(func)。

    任务:返回包装版函数:每次被调 call_count 加 1,原样返回 func 的结果;
         计数器挂在包装版函数对象上,初值 0;保留原函数 __name__/__doc__。
    示例:
        @count_calls
        def query_price(sku): return 599.0
        query_price("KB-001"); query_price("MS-002")
        query_price.call_count -> 2
        query_price.__name__   -> "query_price"   (functools.wraps 的功劳)

    提示(标准骨架,建议背下来):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            wrapper.call_count += 1
            return func(*args, **kwargs)
        wrapper.call_count = 0      # 初始化属性再返回
        return wrapper
    """
    # TODO: wrapper(*args, **kwargs) + @functools.wraps + 初始化属性 + 返回
    ...


def timer(func):
    """
    【场景】排查慢接口:给函数包一层计时,把【每次调用的耗时(秒)】
    追加到 wrapper.records 列表,事后可以翻出来分析。返回值保持不变,
    调用方无感。

    【转换点】和 count_calls 同一张骨架,只是「增强逻辑」换成计时:
    调真函数【前】记起点 time.perf_counter(),【后】把差值 append 进列表。
    perf_counter 是高精度计时器,专测时间间隔。
    铁律不变:wrapper 通用签名 + @functools.wraps(func)。

    任务:返回包装版函数:每次调用把耗时(秒,float)append 到
         wrapper.records;原样返回 func 的结果;records 初值空列表。
    示例:
        @timer
        def query_stock(sku): return 120
        query_stock("KB-001")            -> 120
        query_stock("KB-001")
        len(query_stock.records)         -> 2    (每次调用一条耗时)
        all(r >= 0 for r in query_stock.records) -> True

    提示:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            wrapper.records.append(time.perf_counter() - start)
            return result
        wrapper.records = []
        return wrapper
    """
    # TODO: wrapper 里 perf_counter 前后差,append 到 wrapper.records
    ...


# ========== §4.5 带参数的装饰器 ==========


def retry(times: int):
    """
    【场景】调第三方支付网关,网络偶发抖动抛异常。希望:失败自动重试,
    最多试 times 次;times 次都失败,把【最后一次】异常抛出来交给告警。

    【转换点】带参装饰器 = 三层嵌套。@retry(times=3) 等价于
    f = retry(times=3)(f) —— 先调 retry(times=3) 拿到【真正的装饰器】,
    再用它包 f。口诀:外层收参数、中层收函数、内层干活。
    (≈ Spring Retry 的 @Retry(maxAttempts=3),这边是 15 行纯函数。)

    任务:wrapper 里 for _ in range(times):
             try: return func(*args, **kwargs)   # 成功立刻返回,绝不再试
             except Exception as e: last_exc = e  # 记下异常,继续尝试
         循环走完(全失败):raise last_exc
    示例:
        @retry(times=3)
        def call_payment_gateway(order_id): ...
        # 成功:立刻返回,只调 1 次;全失败:恰好调 3 次,抛最后一次异常

    提示(三层骨架,每层各 return 下一层):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                ...for/try/except/raise...
            return wrapper
        return decorator
    """
    # TODO: 三层嵌套(decorator + wrapper),注意每层 return 什么
    ...


# ========== §4.6 缓存装饰器(综合)==========


def memoize(func):
    """
    【场景】外部汇率服务调用很贵(又慢又按次计费)。同一个币种查过一次
    就该记住:相同入参直接给缓存结果,不再真调。

    【转换点】闭包 + 装饰器合体:cache 字典放在 memoize 的函数体里、
    wrapper 外面——它是闭包变量,【每次装饰】新建一份,每个被装饰函数
    都有自己独立的缓存(放 wrapper 内 → 每次调用新建,永远 miss;
    放模块全局 → 各函数串账)。args 是元组,天然可当字典键。
    禁止用 functools.lru_cache(那是它的完善版,Ch09 讲),自己手写。

    任务:相同入参只真调一次;wrapper.miss_count 统计【真调用】次数;
         保留原函数 __name__。
    示例:
        @memoize
        def get_exchange_rate(currency): ...   # 假设内部是昂贵网络调用
        get_exchange_rate("USD")   # 真调一次,miss_count=1
        get_exchange_rate("USD")   # 命中缓存,函数体不再执行,miss_count 仍=1

    提示:
        cache = {}
        @functools.wraps(func)
        def wrapper(*args):
            if args not in cache:
                wrapper.miss_count += 1
                cache[args] = func(*args)
            return cache[args]
        wrapper.miss_count = 0
        return wrapper
    """
    # TODO: cache 放闭包位 + wrapper(*args) + miss_count + functools.wraps
    ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     uv run python 01_python_core/ch04/ch04_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    from conftest import load_mock_json

    products = load_mock_json("products.json")
    prices = [p["price"] for p in products]

    print("半价试算:", apply_discount(prices, lambda p: p * 0.5))

    coupon = make_coupon(200, 30)
    print("满200减30券 @599:", coupon(599.0), "@150:", coupon(150.0))

    print("购物车合计:", cart_total(599.0, 159.0, 75.5))
    print("统一响应体:", build_response(prices[:2], total=10, page=1))

    @count_calls
    def query_price(sku):
        return 599.0
    query_price("KB-001"); query_price("MS-002")
    print("query_price 调用次数:", query_price.call_count)

    @timer
    def query_stock(sku):
        return 120
    query_stock("KB-001"); query_stock("MS-002")
    print("query_stock 耗时记录条数:", len(query_stock.records))

    attempts = []

    @retry(times=3)
    def flaky_gateway():
        attempts.append(1)
        raise RuntimeError("网关抖动")
    try:
        flaky_gateway()
    except RuntimeError as e:
        print(f"重试 {len(attempts)} 次后仍失败:", e)

    @memoize
    def get_rate(currency):
        print(f"  (真调一次汇率服务: {currency})")
        return 7.2
    get_rate("USD"); get_rate("USD")
    print("汇率 miss_count:", get_rate.miss_count)
