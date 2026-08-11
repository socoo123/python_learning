"""
Ch02 作业测试。
运行: uv run pytest 01_python_core/ch02/test_ch02_assignment.py -v

测试用例按函数分组(class)。products fixture 来自项目根 conftest.py,
加载 assets/mock_data/products.json(10 个商品,function 级隔离,每测重新加载)。
断言期望值均已对照 mock 数据手工验算;自定义小列表用例用于防硬编码蒙对。
"""
import pytest

from ch02_assignment import (
    get_top_products_by_price,
    price_range,
    build_price_map,
    group_by_category,
    category_inventory_value,
    all_categories,
    find_cheapest_per_category,
    filter_products,
)


# ---------- §2.1 get_top_products_by_price:list 切片 + sorted ----------
class TestGetTopProductsByPrice:
    def test_top3(self, products):
        assert get_top_products_by_price(products, n=3) == [
            "27寸4K显示器",   # 2199
            "人体工学椅",     # 1599
            "降噪耳机",       # 1299
        ]

    def test_custom_list(self):
        # 防硬编码:自建小列表
        items = [
            {"name": "甲", "price": 10.0},
            {"name": "乙", "price": 30.0},
            {"name": "丙", "price": 20.0},
        ]
        assert get_top_products_by_price(items, n=2) == ["乙", "丙"]

    def test_ties_keep_original_order(self):
        # sorted 是稳定排序:同价保持原先后顺序
        items = [
            {"name": "A", "price": 100.0},
            {"name": "B", "price": 100.0},
            {"name": "C", "price": 50.0},
        ]
        assert get_top_products_by_price(items, n=2) == ["A", "B"]

    def test_n_more_than_total_returns_all(self, products):
        # 切片越界不报错:n 超过总数返回全部 10 个
        assert len(get_top_products_by_price(products, n=100)) == 10

    def test_n_zero_returns_empty(self, products):
        assert get_top_products_by_price(products, n=0) == []

    def test_empty_list(self):
        assert get_top_products_by_price([], n=3) == []

    def test_does_not_mutate_input(self, products):
        # 拦住 products.sort() 原地排序的实现:调用后原列表顺序必须不变
        ids_before = [p["id"] for p in products]
        get_top_products_by_price(products, n=3)
        assert [p["id"] for p in products] == ids_before


# ---------- §2.2 price_range:tuple 多返回值 ----------
class TestPriceRange:
    def test_min_max(self, products):
        assert price_range(products) == (75.5, 2199.0)

    def test_returns_tuple(self, products):
        assert isinstance(price_range(products), tuple)

    def test_single_product(self):
        items = [{"name": "智能水杯", "price": 199.0}]
        assert price_range(items) == (199.0, 199.0)

    def test_custom_two_products(self):
        # 防硬编码:与 fixture 不同的数据
        items = [{"name": "甲", "price": 89.0}, {"name": "乙", "price": 75.5}]
        assert price_range(items) == (75.5, 89.0)

    def test_can_unpack(self, products):
        low, high = price_range(products)
        assert low < high


# ---------- §2.3 build_price_map:dict 推导式 ----------
class TestBuildPriceMap:
    def test_lookup(self, products):
        m = build_price_map(products)
        assert m["机械键盘"] == 599.0
        assert m["设计模式"] == 75.5

    def test_contains_all(self, products):
        assert len(build_price_map(products)) == 10

    def test_empty_list(self):
        assert build_price_map([]) == {}

    def test_duplicate_name_last_wins(self):
        # dict 键重复:后出现的覆盖先出现的
        items = [
            {"name": "重名商品", "price": 100.0},
            {"name": "重名商品", "price": 200.0},
        ]
        assert build_price_map(items) == {"重名商品": 200.0}


# ---------- §2.4 group_by_category:setdefault 分组 ----------
class TestGroupByCategory:
    def test_category_keys(self, products):
        g = group_by_category(products)
        assert set(g.keys()) == {"电脑外设", "图书", "影音设备", "生活用品"}

    def test_group_counts(self, products):
        g = group_by_category(products)
        assert len(g["电脑外设"]) == 4
        assert len(g["图书"]) == 2
        assert len(g["影音设备"]) == 2
        assert len(g["生活用品"]) == 2

    def test_no_products_lost(self, products):
        g = group_by_category(products)
        assert sum(len(v) for v in g.values()) == 10

    def test_empty_list(self):
        assert group_by_category([]) == {}

    def test_custom_groups_preserve_order(self):
        # 防硬编码 + 组内保持原顺序
        items = [
            {"name": "A", "category": "x"},
            {"name": "B", "category": "y"},
            {"name": "C", "category": "x"},
        ]
        g = group_by_category(items)
        assert [p["name"] for p in g["x"]] == ["A", "C"]
        assert [p["name"] for p in g["y"]] == ["B"]


# ---------- §2.4 category_inventory_value:defaultdict 聚合 ----------
class TestCategoryInventoryValue:
    def test_values(self, products):
        v = category_inventory_value(products)
        # 电脑外设: 599*120 + 159*300 + 2199*45 + 269*220 = 277715
        assert v["电脑外设"] == pytest.approx(277715.0)
        # 图书: 89*500 + 75.5*200 = 59600
        assert v["图书"] == pytest.approx(59600.0)
        # 影音设备: 1299*80 + 399*150 = 163770
        assert v["影音设备"] == pytest.approx(163770.0)

    def test_zero_stock_contributes_zero(self, products):
        # 生活用品: 199*0(智能水杯缺货) + 1599*30(工学椅) = 47970
        assert category_inventory_value(products)["生活用品"] == pytest.approx(47970.0)

    def test_empty_list(self):
        assert category_inventory_value([]) == {}

    def test_custom_list(self):
        items = [
            {"category": "x", "price": 10.0, "stock": 3},
            {"category": "x", "price": 2.5, "stock": 4},
            {"category": "y", "price": 100.0, "stock": 1},
        ]
        v = category_inventory_value(items)
        assert v["x"] == pytest.approx(40.0)
        assert v["y"] == pytest.approx(100.0)

    def test_returns_plain_dict(self, products):
        # 要求 dict(...) 转换,不把 defaultdict 的自动造键副作用泄漏给调用方
        assert type(category_inventory_value(products)) is dict


# ---------- §2.5 all_categories:set 推导式去重 ----------
class TestAllCategories:
    def test_returns_set(self, products):
        assert isinstance(all_categories(products), set)

    def test_contents(self, products):
        assert all_categories(products) == {
            "电脑外设",
            "图书",
            "影音设备",
            "生活用品",
        }

    def test_empty_list(self):
        assert all_categories([]) == set()

    def test_custom_dedup(self):
        items = [{"category": "x"}, {"category": "y"}, {"category": "x"}]
        assert all_categories(items) == {"x", "y"}


# ---------- §2.6 find_cheapest_per_category:min + key 综合 ----------
class TestFindCheapestPerCategory:
    def test_cheapest_names(self, products):
        c = find_cheapest_per_category(products)
        assert c["电脑外设"] == "无线鼠标"      # 159
        assert c["图书"] == "设计模式"          # 75.5
        assert c["影音设备"] == "蓝牙音箱"      # 399
        assert c["生活用品"] == "智能水杯"      # 199(stock=0 但价格最低)

    def test_custom_list(self):
        items = [
            {"name": "甲", "category": "x", "price": 10.0},
            {"name": "乙", "category": "x", "price": 5.0},
            {"name": "丙", "category": "y", "price": 99.0},
        ]
        assert find_cheapest_per_category(items) == {"x": "乙", "y": "丙"}

    def test_tie_takes_first(self):
        # min 的特性:并列最小返回先出现的
        items = [
            {"name": "A", "category": "x", "price": 100.0},
            {"name": "B", "category": "x", "price": 100.0},
        ]
        assert find_cheapest_per_category(items) == {"x": "A"}

    def test_empty_list(self):
        assert find_cheapest_per_category([]) == {}


# ---------- §2.7 filter_products:可变默认参数 + 组合过滤 ----------
class TestFilterProducts:
    def test_no_filter_returns_all_ascending(self, products):
        result = filter_products(products)
        assert len(result) == 10
        assert result[0]["name"] == "设计模式"        # 最便宜 75.5
        assert result[-1]["name"] == "27寸4K显示器"   # 最贵 2199

    def test_min_price(self, products):
        names = [p["name"] for p in filter_products(products, min_price=1000)]
        # >=1000: 耳机1299 / 工学椅1599 / 显示器2199,升序
        assert names == ["降噪耳机", "人体工学椅", "27寸4K显示器"]

    def test_category(self, products):
        names = [p["name"] for p in filter_products(products, category="图书")]
        assert names == ["设计模式", "Python编程:从入门到实践"]

    def test_in_stock_only_excludes_zero_stock(self, products):
        result = filter_products(products, in_stock_only=True)
        assert len(result) == 9  # 排除智能水杯(stock=0)
        assert all(p["stock"] > 0 for p in result)

    def test_combined_filters(self, products):
        names = [p["name"] for p in filter_products(products, min_price=500, category="电脑外设")]
        # 电脑外设 >=500: 键盘599 / 显示器2199,升序
        assert names == ["机械键盘", "27寸4K显示器"]

    def test_min_price_boundary_inclusive(self, products):
        # 边界:>=89 应包含 89,不包含 75.5
        names = [p["name"] for p in filter_products(products, min_price=89, category="图书")]
        assert names == ["Python编程:从入门到实践"]

    def test_no_match_returns_empty(self, products):
        assert filter_products(products, category="食品") == []

    def test_empty_list(self):
        assert filter_products([]) == []

    def test_does_not_mutate_input(self, products):
        # 拦住 .sort() 原地排序的实现:调用后原列表顺序必须不变
        ids_before = [p["id"] for p in products]
        filter_products(products)
        assert [p["id"] for p in products] == ids_before
