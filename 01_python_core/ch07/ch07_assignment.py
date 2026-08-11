"""
Ch07 作业:类型注解与 Pythonic 风格。

场景:你是电商平台结算组的工程师,要交付一个「促销对账工具集」——
价格格式化、按 sku 查商品、折扣策略注入、泛型取首条、分页包装、
订单行金额计算(TypedDict)、营销配置容错解析(EAFP),
最后用 build_reconciliation_rows 把这些零件串成一张对账单。

本章特殊:类型注解运行时不强制(真正的检查靠 mypy)。所以每题你要
【补全类型注解】+ 写实现。测试会检查行为,也会抽查注解存在性(__annotations__)。

    uv run pytest 01_python_core/ch07/test_ch07_assignment.py -v

全绿 = 你掌握了 Ch07。补全注解后再跑 mypy(strict 模式,应零报错):

    uv run --with mypy mypy 01_python_core/ch07/ch07_assignment.py

每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
from dataclasses import dataclass
from typing import Any, Callable, Generic, Protocol, TypeVar, TypedDict, runtime_checkable

# §7.5/§7.6 用的类型变量(已给你定义好):T 代表「任意类型,且进出一致」
T = TypeVar("T")


# §7.7 用的订单行 TypedDict(已给你定义好):
# 精确描述一条订单 dict 有哪些键、各是什么类型。底层就是普通 dict。
class OrderDict(TypedDict):
    id: str
    sku: str
    qty: int
    unit_price: float


# ========== §7.1 类型注解基础 ==========


def format_price(amount, currency="¥"):
    """
    【类型注解基础 · §7.1】对账单金额格式化:带币种符号,保留两位小数。

    任务:先给签名补全注解(amount: float,currency: str = "¥",返回 -> str),
         再实现格式化逻辑。

    示例:
        format_price(599.0)            -> "¥599.00"
        format_price(75.5, currency="$") -> "$75.50"
        format_price(0)                -> "¥0.00"

    提示:f-string 里 {amount:.2f} 表示保留两位小数(Ch01 讲过)。
    """
    # TODO: 补全签名注解,返回 f"{currency}{amount:.2f}"
    ...


# ========== §7.2 联合类型(dict | None)==========


def find_product(products, sku):
    """
    【联合类型 · §7.2】客服后台按 sku 查商品;查不到要明确返回 None。

    任务:补全注解(products: list[dict[str, Any]],sku: str,
         返回 -> dict[str, Any] | None;商品 dict 的值类型杂,str/int/float 都有,
         用 Any 声明「值是任意类型」),遍历查找,命中返回该商品 dict,
         找不到返回 None。

    示例(products 用 assets/mock_data/products.json 的 10 条商品):
        find_product(products, "KB-001")["name"]  -> "机械键盘"
        find_product(products, "NOPE")            -> None
        find_product([], "KB-001")                -> None

    提示:for p in products: if p["sku"] == sku: return p;循环结束 return None。
         ❌ 别返回 {} 当「没找到」——调用方分不清「没找到」和「空商品」。
    """
    # TODO: 补全签名注解,遍历按 sku 查找,找不到 return None
    ...


# ========== §7.3 Callable(函数类型注解)==========


def apply_discount(amount, strategy):
    """
    【Callable 策略注入 · §7.3】大促定价:折扣策略运营随时换,代码不改。

    任务:补全注解(amount: float,strategy: Callable[[float], float],
         返回 -> float),调用 strategy(amount) 并对结果 round(..., 2)。

    示例:
        apply_discount(599.0, lambda p: p * 0.8)   -> 479.2   # 八折
        apply_discount(599.0, lambda p: p - 50)    -> 549.0   # 立减50
        apply_discount(100, lambda p: p * 0.333)   -> 33.3    # 验证 round

    提示:Callable[[float], float] = 接收 float、返回 float 的函数
         (= Java Function<Double,Double>);注意参数列表要包一层 []。
    """
    # TODO: 补全签名注解,return round(strategy(amount), 2)
    ...


# ========== §7.4 Protocol(结构化类型)==========


def make_named_protocol():
    """
    【Protocol · §7.4】定义一个「有名字的」协议并返回它(类工厂模式)。

    场景:平台通讯录——店铺/商品/客服是不同团队写的类,你改不了它们的源码,
         但只要恰好有 .name 属性,就该能进通讯录。Protocol = 结构化类型:
         不用 implements,有结构就自动匹配。

    任务:在函数体内定义并返回这个类(返回类本身,不是实例!),
         可顺便给工厂签名补 -> type:
         @runtime_checkable
         class Named(Protocol):
             name: str

    示例:
        Named = make_named_protocol()
        class Cat: name = "Tom"
        isinstance(Cat(), Named)   -> True     # 有 name,自动算 Named
        class Rock: pass
        isinstance(Rock(), Named)  -> False    # 没 name,不算

    提示:@runtime_checkable 和 Protocol 都已在文件顶部 import;
         忘加 @runtime_checkable 时 isinstance 会抛 TypeError。
    """
    # TODO: 定义 @runtime_checkable class Named(Protocol) 含 name: str,return Named
    ...


# ========== §7.5 TypeVar(泛型函数)==========


def first_or_none(items):
    """
    【TypeVar 泛型函数 · §7.5】取列表首元素;空列表返回 None。

    场景:库存预警队列取第一条待处理——队列里放什么是调用方定的,
         所以要用 T 保持「进什么类型,出什么类型」。

    任务:补全注解(items: list[T],返回 -> T | None;T 已在文件顶部定义),
         实现取首元素。

    示例:
        first_or_none(["CP-009", "MN-003"])  -> "CP-009"
        first_or_none([599, 159])            -> 599
        first_or_none([])                    -> None
        first_or_none([0, False])            -> 0     # 首元素是假值也要原样返回

    提示:return items[0] if items else None。
         ❌ 别把返回类型标成 object——调用方会失去类型信息(= Java 泛型前的黑暗年代)。
    """
    # TODO: 补全签名注解(list[T] -> T | None),return items[0] if items else None
    ...


# ========== §7.6 Generic(泛型类)==========


def make_page_class():
    """
    【Generic 泛型类 · §7.6】定义通用分页容器并返回它(= Spring Data 的 Page<T>)。

    场景:商品列表接口的统一分页返回结构,前端只认这一种格式。

    任务:在函数体内定义并返回这个类(返回类本身),
         可顺便给工厂签名补 -> type:
         @dataclass
         class Page(Generic[T]):
             items: list[T]
             total: int
             page: int = 1

             def page_count(self, page_size: int) -> int:
                 ...    # 总页数 = ceil(total / page_size)

    示例:
        Page = make_page_class()
        Page(items=["a", "b"], total=7, page=2).page_count(3)  -> 3   # 7条每页3条→3页
        Page(items=[], total=0).page                              -> 1   # page 默认值
        Page[str](items=["a"], total=1).items                   -> ["a"]  # 泛型参数化

    提示:dataclass 和 Generic 已在文件顶部 import;T 已定义。
         总页数用整除技巧 -(-total // page_size),免去 import math;
         忘写 (Generic[T]) 的话 Page[str] 会报 TypeError: type is not subscriptable。
    """
    # TODO: 定义 @dataclass class Page(Generic[T]) 含 page_count 方法,return Page
    ...


# ========== §7.7 TypedDict(字典的精确结构)==========


def order_amount(order):
    """
    【TypedDict · §7.7】对账时计算订单行金额:qty × unit_price,保留两位小数。

    场景:订单来自 json.loads,本身就是 dict——TypedDict 让 mypy 知道这个 dict
         精确有哪些键(键名拼错都能抓),运行时零转换成本。

    任务:补全注解(order: OrderDict,返回 -> float;OrderDict 已在文件顶部定义),
         实现金额计算。

    示例:
        order_amount({"id": "A001", "sku": "KB-001", "qty": 2, "unit_price": 59.5})
            -> 119.0
        order_amount({"id": "A002", "sku": "BK-005", "qty": 3, "unit_price": 19.9})
            -> 59.7

    提示:round(order["qty"] * order["unit_price"], 2)。
         记住:TypedDict 是【纯注解】,运行时就是普通 dict,不做校验。
    """
    # TODO: 补全签名注解(order: OrderDict -> float),round(qty * unit_price, 2)
    ...


# ========== §7.8 EAFP 风格 ==========


def extract_discount_rate(payload):
    """
    【EAFP · §7.8】从营销系统推送的嵌套配置里提取折扣率;数据脏就返回 0.0。

    场景:营销系统的 promo 配置字段经常缺、类型经常乱,下游对账必须容错,
         不能因为一条脏配置中断整晚的对账批处理。

    任务:补全注解(payload: dict[str, Any],返回 -> float),用 EAFP 风格实现:
         try: return float(payload["promo"]["rate"])
         except (KeyError, TypeError, ValueError): return 0.0

    示例:
        extract_discount_rate({"promo": {"rate": 0.15}})    -> 0.15
        extract_discount_rate({"promo": {"rate": "0.2"}})   -> 0.2
        extract_discount_rate({})                           -> 0.0   # KeyError
        extract_discount_rate({"promo": None})              -> 0.0   # TypeError
        extract_discount_rate({"promo": {"rate": "abc"}})   -> 0.0   # ValueError

    提示:EAFP = 直接做、出错兜底;❌ 别写 if "promo" in payload 层层判空(LBYL),
         ❌ 更别用裸 except:(会吞 KeyboardInterrupt)。
    """
    # TODO: try 取 float(payload["promo"]["rate"]),except 三个异常 return 0.0
    ...


# ========== §7.9 综合:对账单流水线 ==========


def build_reconciliation_rows(orders, strategy):
    """
    【综合 · §7.9】把前面的零件串成对账单:每个订单一行 "订单号: 折后金额"。

    任务:补全注解(orders: list[OrderDict],strategy: Callable[[float], float],
         返回 -> list[str]),对每个订单:
         base = order_amount(od)                  # §7.7
         final = apply_discount(base, strategy)   # §7.3
         拼行:f"{od['id']}: {format_price(final)}"   # §7.1

    示例:
        orders = [
            {"id": "A001", "sku": "KB-001", "qty": 2, "unit_price": 59.5},
            {"id": "A002", "sku": "BK-005", "qty": 1, "unit_price": 75.5},
        ]
        build_reconciliation_rows(orders, lambda a: a * 0.9)
            -> ["A001: ¥107.10", "A002: ¥67.95"]
        build_reconciliation_rows([], lambda a: a)  -> []

    提示:直接调用本文件里你已经写好的三个函数——这就是组合的力量。
         ⚠️ 本地练习请按顺序完成前面的题,本题依赖它们。
    """
    # TODO: for od in orders → order_amount → apply_discount → format_price 拼行
    ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     uv run python 01_python_core/ch07/ch07_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    print(format_price(599.0))
    print(format_price(75.5, currency="$"))

    products: list[dict[str, Any]] = [
        {"id": 1, "name": "机械键盘", "sku": "KB-001", "price": 599.0},
        {"id": 5, "name": "设计模式", "sku": "BK-005", "price": 75.5},
    ]
    print(find_product(products, "KB-001"))
    print(find_product(products, "NOPE"))

    print(apply_discount(599.0, lambda p: p * 0.8))

    Named = make_named_protocol()

    class Cat:
        name = "Tom"

    print("Cat is Named?", isinstance(Cat(), Named))
    print(first_or_none(["CP-009", "MN-003"]), first_or_none([]))

    Page = make_page_class()
    print(Page(items=["a", "b"], total=7, page=2).page_count(3))

    orders: list[OrderDict] = [
        {"id": "A001", "sku": "KB-001", "qty": 2, "unit_price": 59.5},
        {"id": "A002", "sku": "BK-005", "qty": 1, "unit_price": 75.5},
    ]
    print(order_amount(orders[0]))
    print(extract_discount_rate({"promo": {"rate": 0.15}}))
    print(build_reconciliation_rows(orders, lambda a: a * 0.9))
