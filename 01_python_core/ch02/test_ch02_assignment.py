"""
Ch02 作业测试。运行: pytest 01_python_core/ch02/test_ch02_assignment.py -v

products fixture 来自项目根 conftest.py,加载 assets/mock_data/products.json(10 个商品)。
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


# ---------- get_top_products_by_price:list + 切片 + 排序 ----------
class TestGetTopProductsByPrice:
    def test_top3(self, products):
        assert get_top_products_by_price(products, n=3) == [
            "27寸4K显示器",
            "人体工学椅",
            "降噪耳机",
        ]

    def test_default_n_is_3(self, products):
        assert len(get_top_products_by_price(products)) == 3

    def test_n_more_than_total_returns_all(self, products):
        # n 超过总数应安全返回全部 10 个
        assert len(get_top_products_by_price(products, n=100)) == 10

    def test_descending_order(self, products):
        result = get_top_products_by_price(products, n=5)
        # 第一个必须是最贵的
        assert result[0] == "27寸4K显示器"


# ---------- price_range:tuple 多返回值 ----------
class TestPriceRange:
    def test_min_max(self, products):
        assert price_range(products) == (75.5, 2199.0)

    def test_returns_tuple(self, products):
        assert isinstance(price_range(products), tuple)

    def test_low_less_than_high(self, products):
        low, high = price_range(products)
        assert low < high


# ---------- build_price_map:dict 推导 ----------
class TestBuildPriceMap:
    def test_contains_all(self, products):
        m = build_price_map(products)
        assert len(m) == 10

    def test_lookup(self, products):
        m = build_price_map(products)
        assert m["机械键盘"] == 599.0
        assert m["设计模式"] == 75.5

    def test_is_dict(self, products):
        assert isinstance(build_price_map(products), dict)


# ---------- group_by_category:setdefault 分组 ----------
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


# ---------- category_inventory_value:defaultdict 聚合 ----------
class TestCategoryInventoryValue:
    def test_values(self, products):
        v = category_inventory_value(products)
        # 电脑外设: 599*120 + 159*300 + 2199*45 + 269*220 = 277715
        assert v["电脑外设"] == pytest.approx(277715)
        # 生活用品: 199*0(水杯缺货) + 1599*30 = 47970
        assert v["生活用品"] == pytest.approx(47970)

    def test_all_categories_present(self, products):
        assert len(category_inventory_value(products)) == 4

    def test_zero_stock_contributes_zero(self, products):
        # 智能水杯 stock=0,不影响生活用品总值
        v = category_inventory_value(products)
        assert v["生活用品"] == pytest.approx(1599 * 30)


# ---------- all_categories:set 去重 ----------
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

    def test_deduped_to_4(self, products):
        # 10 个商品,但只有 4 个类目
        assert len(all_categories(products)) == 4


# ---------- find_cheapest_per_category:综合 ----------
class TestFindCheapestPerCategory:
    def test_cheapest_names(self, products):
        c = find_cheapest_per_category(products)
        assert c["电脑外设"] == "无线鼠标"      # 159
        assert c["图书"] == "设计模式"          # 75.5
        assert c["影音设备"] == "蓝牙音箱"      # 399
        assert c["生活用品"] == "智能水杯"      # 199(stock=0 但价格最低)


# ---------- filter_products:综合 + 可变默认参数 ----------
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
        result = filter_products(products, min_price=89, category="图书")
        names = [p["name"] for p in result]
        assert "Python编程:从入门到实践" in names  # 89
        assert "设计模式" not in names              # 75.5 < 89

    def test_sorted_ascending(self, products):
        result = filter_products(products, min_price=200)
        prices = [p["price"] for p in result]
        assert prices == sorted(prices)
