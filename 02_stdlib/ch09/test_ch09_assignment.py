"""
Ch09 作业测试。运行: uv run pytest 02_stdlib/ch09/test_ch09_assignment.py -v

每个函数一个 TestXxx 类(命名 = Test + 函数名 PascalCase,web 端按类名单跑)。
覆盖:正常 case ≥ 2 + 边界 case(空输入 / 乱序输入 / 无限流 / 缓存命中)≥ 1,
另配「手工小数据」用例防止对着 mock 数据硬编码。

注意:query_product 的缓存测试用 cache_clear() 重置,不依赖测试执行顺序。
"""
from itertools import count

import pytest

from ch09_assignment import (
    PRODUCT_CATALOG,
    bundle_pairs,
    category_report,
    group_by_category,
    inventory_value,
    make_discounter,
    merge_batches,
    promo_matrix,
    query_product,
    take_first,
)


# ---------- merge_batches:itertools.chain ----------
class TestMergeBatches:
    def test_two_batches(self):
        b1 = [{"sku": "KB-001"}, {"sku": "MS-002"}]
        b2 = [{"sku": "MN-003"}]
        assert merge_batches(b1, b2) == [
            {"sku": "KB-001"}, {"sku": "MS-002"}, {"sku": "MN-003"},
        ]

    def test_preserves_batch_order(self, products):
        # 按批次顺序首尾相接:前 2 个 + 第 3、4 个 = 前 4 个
        merged = merge_batches(products[:2], products[2:4])
        assert [p["id"] for p in merged] == [1, 2, 3, 4]

    def test_three_warehouse_batches(self):
        east = [{"sku": "KB-001"}]
        north = [{"sku": "MN-003"}, {"sku": "DK-008"}]
        south = [{"sku": "HP-006"}]
        merged = merge_batches(east, north, south)
        assert [p["sku"] for p in merged] == ["KB-001", "MN-003", "DK-008", "HP-006"]

    def test_accepts_any_iterable(self):
        # chain 不挑输入类型:tuple / 生成器都能拼
        assert merge_batches((1, 2), [3], (x for x in [4, 5])) == [1, 2, 3, 4, 5]

    def test_empty_inputs(self):
        assert merge_batches([], []) == []
        assert merge_batches() == []   # 一批都没到

    def test_does_not_mutate_inputs(self):
        b1 = [{"sku": "A"}]
        b2 = [{"sku": "B"}]
        merge_batches(b1, b2)
        assert b1 == [{"sku": "A"}]
        assert b2 == [{"sku": "B"}]


# ---------- group_by_category:itertools.groupby(先排序) ----------
class TestGroupByCategory:
    def test_keys_sorted(self, products):
        # sorted 后分组 → key 按字典序(Unicode)有序
        assert list(group_by_category(products).keys()) == [
            "图书", "影音设备", "生活用品", "电脑外设",
        ]

    def test_group_sizes(self, products):
        g = group_by_category(products)
        assert len(g["电脑外设"]) == 4
        assert len(g["图书"]) == 2
        assert len(g["影音设备"]) == 2
        assert len(g["生活用品"]) == 2

    def test_group_content(self, products):
        g = group_by_category(products)
        assert [p["sku"] for p in g["图书"]] == ["BK-004", "BK-005"]
        assert [p["sku"] for p in g["影音设备"]] == ["HP-006", "SP-007"]

    def test_no_products_lost(self, products):
        assert sum(len(v) for v in group_by_category(products).values()) == 10

    def test_unsorted_input_merged_correctly(self):
        # 乱序输入也必须正确合并:拦住「只 groupby 不 sorted」的实现
        items = [
            {"name": "a", "category": "数码"},
            {"name": "b", "category": "图书"},
            {"name": "c", "category": "数码"},
        ]
        g = group_by_category(items)
        assert set(g.keys()) == {"数码", "图书"}
        assert [p["name"] for p in g["数码"]] == ["a", "c"]
        assert [p["name"] for p in g["图书"]] == ["b"]

    def test_returns_plain_dict(self, products):
        assert type(group_by_category(products)) is dict

    def test_empty(self):
        assert group_by_category([]) == {}


# ---------- bundle_pairs:itertools.combinations ----------
class TestBundlePairs:
    def test_three_products(self, products):
        assert bundle_pairs(products[:3]) == [
            ("机械键盘", "无线鼠标"),
            ("机械键盘", "27寸4K显示器"),
            ("无线鼠标", "27寸4K显示器"),
        ]

    def test_count_is_n_choose_2(self, products):
        assert len(bundle_pairs(products)) == 45   # C(10,2)

    def test_no_duplicates_no_self_pairs(self, products):
        pairs = bundle_pairs(products)
        assert len(set(pairs)) == 45               # 无重复对
        assert all(a != b for a, b in pairs)       # 不和自己配对

    def test_returns_list_of_2tuples(self, products):
        assert all(isinstance(t, tuple) and len(t) == 2 for t in bundle_pairs(products))

    def test_less_than_two_returns_empty(self):
        assert bundle_pairs([{"name": "独角商品"}]) == []
        assert bundle_pairs([]) == []


# ---------- promo_matrix:itertools.product ----------
class TestPromoMatrix:
    def test_two_by_two_order(self):
        # 顺序 = 双重 for:外层类目,内层折扣(右边跑最快)
        assert promo_matrix(["图书", "影音设备"], [0.9, 0.8]) == [
            ("图书", 0.9), ("图书", 0.8),
            ("影音设备", 0.9), ("影音设备", 0.8),
        ]

    def test_full_matrix_4x3(self):
        cats = ["图书", "影音设备", "生活用品", "电脑外设"]
        matrix = promo_matrix(cats, [0.95, 0.9, 0.8])
        assert len(matrix) == 12
        assert matrix[0] == ("图书", 0.95)
        assert matrix[-1] == ("电脑外设", 0.8)

    def test_single_cell(self):
        assert promo_matrix(["图书"], [0.5]) == [("图书", 0.5)]

    def test_empty_side_gives_empty(self):
        assert promo_matrix([], [0.9]) == []
        assert promo_matrix(["图书"], []) == []


# ---------- inventory_value:functools.reduce ----------
class TestInventoryValue:
    def test_real_total(self, products):
        # 手算:71880+47700+98955+44500+15100+103920+59850+59180+0+47970
        assert inventory_value(products) == 549055.0

    def test_returns_float(self, products):
        assert isinstance(inventory_value(products), float)

    def test_empty_returns_zero(self):
        assert inventory_value([]) == 0.0   # 初始值兜底,不写初始值会 TypeError

    def test_handmade(self):
        # 手工小数据,防止对着 mock 答案硬编码
        assert inventory_value([
            {"price": 10.0, "stock": 2},
            {"price": 3.0, "stock": 1},
        ]) == 23.0

    def test_zero_stock_contributes_nothing(self):
        # 智能水杯 CP-009 库存 0:价值 0
        assert inventory_value([{"price": 199.0, "stock": 0}]) == 0.0


# ---------- take_first:itertools.islice ----------
class TestTakeFirst:
    def test_basic(self):
        assert take_first(iter(["a", "b", "c"]), 2) == ["a", "b"]

    def test_infinite_stream_safe(self):
        # count(10) 是无限迭代器——list(stream) 或推导式会卡死,只有 islice 能过
        assert take_first(count(10), 4) == [10, 11, 12, 13]

    def test_infinite_event_stream(self):
        events = (f"order-{i}" for i in count(1))
        assert take_first(events, 3) == ["order-1", "order-2", "order-3"]

    def test_n_more_than_available(self):
        assert take_first([1, 2], 10) == [1, 2]

    def test_n_zero(self):
        assert take_first([1, 2, 3], 0) == []

    def test_empty_stream(self):
        assert take_first([], 5) == []


# ---------- query_product:functools.lru_cache(PRODUCT_CATALOG 为脚手架) ----------
class TestQueryProduct:
    def test_found(self):
        assert query_product("KB-001")["name"] == "机械键盘"
        assert query_product("KB-001")["price"] == 599.0

    def test_returns_catalog_dict(self):
        # 返回的就是目录里那条完整记录
        expected = next(p for p in PRODUCT_CATALOG if p["sku"] == "BK-005")
        assert query_product("BK-005") == expected

    def test_unknown_sku_raises_keyerror(self):
        with pytest.raises(KeyError):
            query_product("XX-000")

    def test_cache_hit_recorded(self):
        # 先清缓存保证不依赖其他测试;同 sku 第二次调用应命中缓存
        query_product.cache_clear()
        query_product("MS-002")
        query_product("MS-002")
        info = query_product.cache_info()
        assert info.hits == 1
        assert info.misses == 1
        assert info.currsize == 1

    def test_distinct_skus_cached_separately(self):
        query_product.cache_clear()
        query_product("KB-001")
        query_product("HP-006")
        info = query_product.cache_info()
        assert info.misses == 2
        assert info.currsize == 2

    def test_has_cache_api(self):
        # 没加 @lru_cache 装饰器的话这两个属性不存在 → 测试失败
        assert hasattr(query_product, "cache_info")
        assert hasattr(query_product, "cache_clear")
        assert query_product.cache_info().maxsize is None


# ---------- make_discounter:functools.partial ----------
class TestMakeDiscounter:
    def test_vip8(self):
        vip8 = make_discounter(0.8)
        assert vip8(100) == 80.0

    def test_real_price(self):
        vip8 = make_discounter(0.8)
        assert vip8(599.0) == pytest.approx(479.2)   # 浮点乘法用 approx

    def test_svip5(self):
        assert make_discounter(0.5)(100) == 50.0

    def test_instances_independent(self):
        # 两个折扣器各自固化 rate,互不影响
        vip8 = make_discounter(0.8)
        svip5 = make_discounter(0.5)
        assert vip8(100) == 80.0
        assert svip5(100) == 50.0
        assert vip8(200) == pytest.approx(160.0)   # svip5 的创建没污染 vip8

    def test_apply_to_price_list(self, products):
        vip8 = make_discounter(0.8)
        discounted = [vip8(p["price"]) for p in products[:2]]
        assert discounted == pytest.approx([479.2, 127.2])


# ---------- category_report:综合 ----------
class TestCategoryReport:
    def test_keys_sorted(self, products):
        assert list(category_report(products).keys()) == [
            "图书", "影音设备", "生活用品", "电脑外设",
        ]

    def test_peripherals(self, products):
        # 电脑外设:4 个;库存 120+300+45+220=685;
        # 价值 599×120+159×300+2199×45+269×220=277715;最高单价 2199
        assert category_report(products)["电脑外设"] == {
            "count": 4,
            "total_stock": 685,
            "total_value": 277715.0,
            "max_price": 2199.0,
        }

    def test_books(self, products):
        assert category_report(products)["图书"] == {
            "count": 2,
            "total_stock": 700,
            "total_value": 59600.0,
            "max_price": 89.0,
        }

    def test_all_categories(self, products):
        r = category_report(products)
        assert r["影音设备"] == {
            "count": 2, "total_stock": 230,
            "total_value": 163770.0, "max_price": 1299.0,
        }
        assert r["生活用品"] == {
            "count": 2, "total_stock": 30,
            "total_value": 47970.0, "max_price": 1599.0,
        }

    def test_values_sum_to_total(self, products):
        # 各类目价值之和 = 库存总值(和 inventory_value 交叉验证)
        r = category_report(products)
        assert sum(v["total_value"] for v in r.values()) == 549055.0
        assert sum(v["total_stock"] for v in r.values()) == 1645

    def test_handmade_unsorted(self):
        # 乱序手工小数据:防硬编码 + 防「只 groupby 不 sorted」
        items = [
            {"name": "a", "category": "数码", "price": 100.0, "stock": 2},
            {"name": "b", "category": "图书", "price": 50.0, "stock": 10},
            {"name": "c", "category": "数码", "price": 300.0, "stock": 1},
        ]
        assert category_report(items) == {
            "图书": {"count": 1, "total_stock": 10,
                     "total_value": 500.0, "max_price": 50.0},
            "数码": {"count": 2, "total_stock": 3,
                     "total_value": 500.0, "max_price": 300.0},
        }

    def test_empty(self):
        assert category_report([]) == {}
