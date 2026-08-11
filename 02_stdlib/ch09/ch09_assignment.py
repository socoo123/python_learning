"""
Ch09 作业:itertools + functools —— 函数式利器。

场景:你是电商平台的数据分析师,大促前基于 products.json 做一轮盘点:
合并多仓到货批次 → 按类目分组 → 搭配套餐候选 → 促销定价矩阵 → 库存总值 →
实时事件流取样 → 商品查询缓存 → 折扣定价器 → 类目盘点报告。

9 个任务围绕 assets/mock_data/products.json(10 个商品)展开。
在每处 TODO 写实现,然后:

    uv run pytest 02_stdlib/ch09/test_ch09_assignment.py -v

全绿 = 你掌握了 Ch09。

约定:
- products 是 list[dict],每个 dict 形如
    {"id": 1, "name": "机械键盘", "category": "电脑外设",
     "price": 599.00, "stock": 120, "sku": "KB-001"}
- PRODUCT_CATALOG(§9.7 用)已作为【脚手架】给出,内容和 products.json 一致,不用改。
- 每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
  (提示只给思路和关键语法,不给完整代码——自己组合才有掌握感。)
"""
from functools import lru_cache, partial, reduce
from itertools import chain, combinations, groupby, islice, product
from operator import add, mul


# ========== §9.1 itertools.chain:多路合并 ==========


def merge_batches(*batches: list[dict]) -> list[dict]:
    """
    【chain · §9.1】大促补货:多个仓库各发来一批到货清单,合并成一条流统一处理。

    示例:
        merge_batches([{"sku": "KB-001"}, {"sku": "MS-002"}], [{"sku": "MN-003"}])
            -> [{"sku": "KB-001"}, {"sku": "MS-002"}, {"sku": "MN-003"}]
        merge_batches(products[:2], products[2:4])  -> 前 4 个商品(id 1,2,3,4)
        merge_batches([], [])                       -> []
        merge_batches()                             -> []   (一批都没到)

    提示:batches 是【元组】(因为 * 收集),itertools.chain(*batches) 把多批首尾相接;
         或 chain.from_iterable(batches) 等价。chain 产出惰性迭代器,list() 物化返回。
    """
    # TODO: list(chain(*batches)) 或 list(chain.from_iterable(batches))
    ...


# ========== §9.2 itertools.groupby:分组(必须先排序!)==========


def group_by_category(products: list[dict]) -> dict[str, list[dict]]:
    """
    【groupby · §9.2】按 category 分组盘点,返回 {类目: [商品, ...]}(普通 dict)。

    示例(products.json 的 10 个商品):
        g = group_by_category(products)
        list(g.keys())                  -> ["图书", "影音设备", "生活用品", "电脑外设"]
        len(g["电脑外设"])               -> 4
        [p["sku"] for p in g["图书"]]   -> ["BK-004", "BK-005"]
        group_by_category([])           -> {}

    ⚠️ 关键陷阱:groupby 只合并【相邻】的相同 key。products.json 里「电脑外设」
       被「图书」隔开,不排序直接 groupby 会裂成两组。必须【先 sorted 再 groupby】,
       且两处用【同一个】key 函数。

    提示:
        ordered = sorted(products, key=lambda p: p["category"])
        return {k: list(g) for k, g in groupby(ordered, key=lambda p: p["category"])}
        g 是迭代器,要 list(g) 物化;最外层字典推导产出普通 dict。
    """
    # TODO: 先 sorted(同一 key 函数),再 groupby 字典推导
    ...


# ========== §9.3 itertools.combinations:组合 ==========


def bundle_pairs(products: list[dict]) -> list[tuple[str, str]]:
    """
    【combinations · §9.3】运营要做「搭配套餐」:列出所有【两两组合】的商品名对。

    示例:
        bundle_pairs(products[:3])
            -> [("机械键盘", "无线鼠标"),
                ("机械键盘", "27寸4K显示器"),
                ("无线鼠标", "27寸4K显示器")]
        len(bundle_pairs(products))     -> 45   (C(10,2),10 个商品两两搭配)
        bundle_pairs(products[:1])      -> []   (不足 2 个,无对可搭)
        bundle_pairs([])                -> []

    提示:combinations(序列, 2) 生成所有 2 元组合(不计顺序,不会出现 (B,A) 重复)。
         先拿名字:生成器表达式 (p["name"] for p in products),再喂给 combinations,
         最后 list() 物化。
    """
    # TODO: list(combinations((p["name"] for p in products), 2))
    ...


# ========== §9.4 itertools.product:笛卡尔积 ==========


def promo_matrix(categories: list[str], discounts: list[float]) -> list[tuple[str, float]]:
    """
    【product · §9.4】大促定价:每个类目 × 每档折扣,生成促销规则矩阵。

    示例:
        promo_matrix(["图书", "影音设备"], [0.9, 0.8])
            -> [("图书", 0.9), ("图书", 0.8), ("影音设备", 0.9), ("影音设备", 0.8)]
            (顺序 = 双重 for:外层类目、内层折扣——【右边】的列表跑最快)
        len(promo_matrix(["图书", "影音设备", "生活用品", "电脑外设"], [0.95, 0.9, 0.8]))
            -> 12   (4 类目 × 3 折扣)
        promo_matrix([], [0.9])  -> []
        promo_matrix(["图书"], [])  -> []

    提示:itertools.product(a, b) = a × b 的笛卡尔积(惰性迭代器),list() 物化。
    """
    # TODO: list(product(categories, discounts))
    ...


# ========== §9.5 functools.reduce:累积运算 ==========


def inventory_value(products: list[dict]) -> float:
    """
    【reduce · §9.5】算库存总价值(Σ 单价×库存),给老板的大促备货汇报。

    示例(products.json 实际值):
        inventory_value(products)   -> 549055.0
            (机械键盘 599×120=71880 + 无线鼠标 159×300=47700 + ... 共 10 项)
        inventory_value([])         -> 0.0   (空列表返回初始值,不报错)
        inventory_value([{"price": 10.0, "stock": 2}]) -> 20.0

    提示:reduce(函数, 可迭代, 初始值) 三要素:
        reduce(add, (p["price"] * p["stock"] for p in products), 0.0)
        add 从 operator 导入;生成器表达式先做「单价×库存」映射;0.0 是初始值
        (空列表时返回它——不写初始值,空列表会 TypeError)。
    """
    # TODO: reduce(add, 生成器表达式, 0.0)
    ...


# ========== §9.6 itertools.islice:惰性切片 ==========


def take_first(stream, n: int) -> list:
    """
    【islice · §9.6】从实时事件流取前 n 条。stream 是【迭代器】,而且可能【无限长】
    (消息队列消费、tail -f 式日志流),千万别物化它。

    示例:
        take_first(iter(["a", "b", "c"]), 2)  -> ["a", "b"]
        take_first(count(1), 3)               -> [1, 2, 3]
            (count(1) 是无限计数器:1,2,3,4...,islice 取到 3 个就停,不会卡死)
        take_first([1, 2], 10)                -> [1, 2]   (不够 n 条就全给)
        take_first([], 5)                     -> []

    提示:stream[:n] 对迭代器是 TypeError;list(stream) 对无限流会卡死(pytest 挂住)。
         只有 islice(stream, n) 是惰性取样,包 list() 返回。
    """
    # TODO: list(islice(stream, n))
    ...


# ========== §9.7 functools.lru_cache:记忆化 ==========

# 【脚手架】商品目录,和 assets/mock_data/products.json 一致,不用改。
# 你的任务:给 query_product 加 @lru_cache 装饰器 + 实现遍历查找。
PRODUCT_CATALOG = [
    {"id": 1, "name": "机械键盘", "category": "电脑外设", "price": 599.00, "stock": 120, "sku": "KB-001"},
    {"id": 2, "name": "无线鼠标", "category": "电脑外设", "price": 159.00, "stock": 300, "sku": "MS-002"},
    {"id": 3, "name": "27寸4K显示器", "category": "电脑外设", "price": 2199.00, "stock": 45, "sku": "MN-003"},
    {"id": 4, "name": "Python编程:从入门到实践", "category": "图书", "price": 89.00, "stock": 500, "sku": "BK-004"},
    {"id": 5, "name": "设计模式", "category": "图书", "price": 75.50, "stock": 200, "sku": "BK-005"},
    {"id": 6, "name": "降噪耳机", "category": "影音设备", "price": 1299.00, "stock": 80, "sku": "HP-006"},
    {"id": 7, "name": "蓝牙音箱", "category": "影音设备", "price": 399.00, "stock": 150, "sku": "SP-007"},
    {"id": 8, "name": "USB-C扩展坞", "category": "电脑外设", "price": 269.00, "stock": 220, "sku": "DK-008"},
    {"id": 9, "name": "智能水杯", "category": "生活用品", "price": 199.00, "stock": 0, "sku": "CP-009"},
    {"id": 10, "name": "人体工学椅", "category": "生活用品", "price": 1599.00, "stock": 30, "sku": "CH-010"},
]


# TODO(①):在下一行 def 的【上一行】加装饰器 @lru_cache(maxsize=None)
def query_product(sku: str) -> dict:
    """
    【lru_cache · §9.7】大促高频调用:按 sku 查商品详情。

    模拟「昂贵查询」(真实系统是 DB/RPC,这里遍历 PRODUCT_CATALOG 全表扫描)。
    同一个 sku 一秒被查几千次,加 @lru_cache 后相同入参直接命中缓存,不重查。

    示例:
        query_product("KB-001")["name"]   -> "机械键盘"
        query_product("KB-001")["price"]  -> 599.0
        query_product("XX-000")           -> 抛 KeyError(异常不会被缓存,下次照抛)

        验证缓存生效:
        query_product.cache_clear()
        query_product("MS-002"); query_product("MS-002")
        query_product.cache_info()  -> CacheInfo(hits=1, misses=1, ...)

    提示:① @lru_cache(maxsize=None) 加在 def 上一行(None = 不限容量);
         ② 函数体就是普通遍历:遍历 PRODUCT_CATALOG,sku 匹配就 return 该 dict,
           循环结束还没找到 raise KeyError(sku)。
    """
    # TODO(②):遍历查找,命中 return,未命中 raise KeyError(sku)。
    #          别忘了上面的 TODO(①):加 @lru_cache 装饰器,否则缓存测试过不了。
    ...


# ========== §9.8 functools.partial:偏函数 ==========


def make_discounter(rate: float):
    """
    【partial · §9.8】大促定价器:固定折扣率,生成「原价 → 折后价」的函数。

    普通会员 9 折、VIP 8 折、SVIP 5 折——同一套「原价 × rate」逻辑,
    只是乘数不同。partial 把乘数【预先固定】进新函数。

    示例:
        vip8 = make_discounter(0.8)
        vip8(100)      -> 80.0
        vip8(599.0)    -> 479.2   (浮点乘法,测试用 pytest.approx 断言)
        svip5 = make_discounter(0.5)
        svip5(100)     -> 50.0    (和 vip8 互不影响,各自固化自己的 rate)

    提示:operator.mul(a, b) 就是 a*b。partial(mul, rate) 固定第一个参数,
         得到的新函数只收第二个参数(原价)。函数体一行。
    """
    # TODO: return partial(mul, rate)
    ...


# ========== §9.9 综合:类目盘点报告 ==========


def category_report(products: list[dict]) -> dict[str, dict]:
    """
    【综合 · §9.9】大促盘点报告:每个类目的商品数 / 总库存 / 库存总价值 / 最高单价。
    这是 §9.2(groupby)+ §9.5(reduce)的合奏——每段你都单独写过,现在组合起来。

    返回 dict 的 schema(键名固定,测试逐个验):
        {类目: {"count": 商品数, "total_stock": 总库存,
                "total_value": Σ单价×库存, "max_price": 最高单价}}

    示例(products.json 实际结果):
        r = category_report(products)
        list(r.keys())   -> ["图书", "影音设备", "生活用品", "电脑外设"]  (排序后分组)
        r["电脑外设"]    -> {"count": 4, "total_stock": 685,
                            "total_value": 277715.0, "max_price": 2199.0}
        r["图书"]        -> {"count": 2, "total_stock": 700,
                            "total_value": 59600.0, "max_price": 89.0}
        category_report([]) -> {}

    提示:sorted + groupby 分组(§9.2 两段式,g 记得 list 物化);
         每组内:len 算 count、sum 生成器算 total_stock、
         reduce(add, (p["price"]*p["stock"] for ...), 0.0) 算 total_value(§9.5)、
         max 生成器算 max_price。【内联实现,别调前面的函数】——web 端单题跑时它们还是骨架。
    """
    # TODO: sorted + groupby,组内 len / sum / reduce / max 组装 4 键 dict
    ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     uv run python 02_stdlib/ch09/ch09_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    from conftest import load_mock_json

    products = load_mock_json("products.json")

    print("===== 大促盘点 =====")
    print("合并批次:", [p["sku"] for p in merge_batches(products[:2], products[2:4])])
    print("类目分组:", {k: len(v) for k, v in group_by_category(products).items()})
    print("搭配套餐数:", len(bundle_pairs(products)))
    print("促销矩阵:", promo_matrix(["图书", "影音设备"], [0.9, 0.8]))
    print("库存总值:", inventory_value(products))

    from itertools import count
    print("事件流取样:", take_first((f"order-{i}" for i in count(1)), 3))

    print("查询 KB-001:", query_product("KB-001")["name"])
    query_product("KB-001")
    print("缓存信息:", query_product.cache_info())

    vip8 = make_discounter(0.8)
    print("VIP 价(599 原价):", vip8(599.0))

    print("盘点报告:", category_report(products))
