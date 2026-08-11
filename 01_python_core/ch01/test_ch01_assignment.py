"""
Ch01 作业测试。
运行: uv run pytest 01_python_core/ch01/test_ch01_assignment.py -v

测试用例按函数分组(class)。你写完 ch01_assignment.py 后,这里应该全绿。
断言期望值均已对照 assets/mock_data/products.json 实际数据验算。
"""
from conftest import load_mock_json
from ch01_assignment import (
    calc_line_total,
    parse_sku,
    format_price_tag,
    render_price_list,
    first_in_stock_name,
    debug_repr,
    load_out_of_stock_skus,
    inventory_summary,
)

PRODUCTS = load_mock_json("products.json")


# ---------- §1.1 calc_line_total:动态类型 + 类型注解 ----------
class TestCalcLineTotal:
    def test_float_price(self):
        assert calc_line_total(599.0, 2) == 1198.0

    def test_int_price_also_works(self):
        # 注解写 float,传 int 也能算——运行时不强制
        assert calc_line_total(89, 3) == 267

    def test_zero_quantity(self):
        assert calc_line_total(599.0, 0) == 0

    def test_large_numbers_no_overflow(self):
        # Python int 无溢出(对比 Java int/long 会溢出)
        assert calc_line_total(10**18, 10**18) == 10**36


# ---------- §1.2 parse_sku:元组打包/解包 ----------
class TestParseSku:
    def test_keyboard(self):
        assert parse_sku("KB-001") == ("KB", 1)

    def test_book(self):
        assert parse_sku("BK-005") == ("BK", 5)

    def test_returns_tuple(self):
        assert isinstance(parse_sku("KB-001"), tuple)

    def test_leading_zeros_stripped(self):
        # int("003") == 3,前导零必须去掉
        assert parse_sku("MN-003")[1] == 3


# ---------- §1.3 format_price_tag:默认参数 + f-string ----------
class TestFormatPriceTag:
    def test_default_currency(self):
        assert format_price_tag("机械键盘", 599.0) == "机械键盘 ¥599.00"

    def test_custom_currency_keyword(self):
        assert format_price_tag("无线鼠标", 159.0, currency="$") == "无线鼠标 $159.00"

    def test_half_price_padded_to_two_decimals(self):
        # 75.5 必须格式化成 "75.50"——拦住不做 :.2f 的实现
        assert format_price_tag("设计模式", 75.5) == "设计模式 ¥75.50"

    def test_int_price_formatted(self):
        assert format_price_tag("Python编程:从入门到实践", 89) == "Python编程:从入门到实践 ¥89.00"


# ---------- §1.3 render_price_list:join + 列表推导式 ----------
class TestRenderPriceList:
    def test_two_items_newline_joined(self):
        items = [
            {"name": "无线鼠标", "price": 159.0},
            {"name": "设计模式", "price": 75.5},
        ]
        assert render_price_list(items) == "无线鼠标 ¥159.00\n设计模式 ¥75.50"

    def test_single_item_no_trailing_newline(self):
        items = [{"name": "机械键盘", "price": 599.0}]
        assert render_price_list(items) == "机械键盘 ¥599.00"

    def test_empty_list_returns_empty_string(self):
        assert render_price_list([]) == ""

    def test_custom_currency(self):
        items = [{"name": "降噪耳机", "price": 1299.0}]
        assert render_price_list(items, currency="$") == "降噪耳机 $1299.00"


# ---------- §1.4 first_in_stock_name:truthiness ----------
class TestFirstInStockName:
    def test_first_product_in_stock(self):
        assert first_in_stock_name(PRODUCTS) == "机械键盘"

    def test_skips_out_of_stock(self):
        # 拦住「不看 stock 直接返回第一个」的错误实现
        items = [
            {"name": "智能水杯", "stock": 0},
            {"name": "机械键盘", "stock": 120},
        ]
        assert first_in_stock_name(items) == "机械键盘"

    def test_all_out_of_stock_returns_none(self):
        items = [{"name": "智能水杯", "stock": 0}]
        assert first_in_stock_name(items) is None

    def test_empty_list_returns_none(self):
        assert first_in_stock_name([]) is None


# ---------- §1.5 debug_repr:一切皆对象 + repr vs str ----------
class TestDebugRepr:
    def test_int(self):
        assert debug_repr(42) == "42 (int)"

    def test_str_is_quoted(self):
        # repr("hi") 带引号——本题核心考点
        assert debug_repr("hi") == "'hi' (str)"

    def test_list(self):
        assert debug_repr([1, 2]) == "[1, 2] (list)"

    def test_float(self):
        assert debug_repr(3.14) == "3.14 (float)"


# ---------- §1.6 load_out_of_stock_skus:import + dict + 推导式 ----------
class TestLoadOutOfStockSkus:
    def test_exact_skus(self):
        # 精确等值:拦住「返回全部 sku」「返回 name 而不是 sku」的错误实现
        assert load_out_of_stock_skus() == ["CP-009"]

    def test_returns_list(self):
        assert isinstance(load_out_of_stock_skus(), list)

    def test_all_elements_are_strings(self):
        assert all(isinstance(s, str) for s in load_out_of_stock_skus())


# ---------- §1.6 inventory_summary:综合(len/min/max/sum + dict) ----------
class TestInventorySummary:
    def test_count(self):
        assert inventory_summary(PRODUCTS)["count"] == 10

    def test_price_range(self):
        summary = inventory_summary(PRODUCTS)
        assert summary["min_price"] == 75.5
        assert summary["max_price"] == 2199.0

    def test_total_value(self):
        # sum(price * stock) = 71880+47700+98955+44500+15100+103920+59850+59180+0+47970
        assert inventory_summary(PRODUCTS)["total_value"] == 549055.0

    def test_full_dict_exact(self):
        assert inventory_summary(PRODUCTS) == {
            "count": 10,
            "min_price": 75.5,
            "max_price": 2199.0,
            "total_value": 549055.0,
        }
