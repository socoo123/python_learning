"""
Ch03 作业测试。运行: uv run pytest 01_python_core/ch03/test_ch03_assignment.py -v

products fixture 来自项目根 conftest.py(10 个商品)。
error_lines fixture 加载 assets/mock_data/logs.json(20 行日志,含 5 条 ERROR)。
"""
import pytest

from ch03_assignment import (
    cheap_product_names,
    indexed_summary,
    names_and_prices_zipped,
    is_prime,
    iter_error_lines,
    top_n_by_price,
)
from conftest import load_mock_json


@pytest.fixture
def error_lines():
    return load_mock_json("logs.json")


# ---------- cheap_product_names:列表推导(带条件)----------
class TestCheapProductNames:
    def test_under_200(self, products):
        # <200: 无线鼠标159 / Python编程89 / 设计模式75.5 / 智能水杯199
        result = cheap_product_names(products, max_price=200)
        assert set(result) == {
            "无线鼠标",
            "Python编程:从入门到实践",
            "设计模式",
            "智能水杯",
        }
        assert len(result) == 4

    def test_default_max_price_is_200(self, products):
        assert len(cheap_product_names(products)) == 4

    def test_strict_under_100(self, products):
        result = cheap_product_names(products, max_price=100)
        assert set(result) == {"Python编程:从入门到实践", "设计模式"}

    def test_preserves_original_order(self, products):
        # 原顺序里 无线鼠标(id=2) 在 Python编程(id=4) 之前
        result = cheap_product_names(products, max_price=200)
        assert result[0] == "无线鼠标"

    def test_empty_when_none_qualify(self, products):
        assert cheap_product_names(products, max_price=10) == []


# ---------- indexed_summary:enumerate ----------
class TestIndexedSummary:
    def test_format_first(self, products):
        assert indexed_summary(products)[0] == "1. 机械键盘 (¥599.0)"

    def test_format_third(self, products):
        assert indexed_summary(products)[2] == "3. 27寸4K显示器 (¥2199.0)"

    def test_numbering_starts_at_1(self, products):
        assert indexed_summary(products)[0].startswith("1. ")

    def test_count(self, products):
        assert len(indexed_summary(products)) == 10


# ---------- names_and_prices_zipped:zip ----------
class TestNamesAndPricesZipped:
    def test_first_pair(self, products):
        assert names_and_prices_zipped(products)[0] == ("机械键盘", 599.0)

    def test_fifth_pair(self, products):
        assert names_and_prices_zipped(products)[4] == ("设计模式", 75.5)

    def test_all_ten_pairs(self, products):
        result = names_and_prices_zipped(products)
        assert len(result) == 10

    def test_each_is_2tuple(self, products):
        result = names_and_prices_zipped(products)
        assert all(isinstance(t, tuple) and len(t) == 2 for t in result)


# ---------- is_prime:for-else ----------
class TestIsPrime:
    @pytest.mark.parametrize("n", [2, 3, 5, 7, 11, 13, 97])
    def test_primes(self, n):
        assert is_prime(n) is True

    @pytest.mark.parametrize("n", [0, 1, 4, 6, 8, 9, 15, 100])
    def test_not_primes(self, n):
        assert is_prime(n) is False

    def test_two_is_prime_edge(self):
        # 2 是最小素数:range(2,2) 为空,循环不执行 → else 执行
        assert is_prime(2) is True


# ---------- iter_error_lines:生成器 yield ----------
class TestIterErrorLines:
    def test_filters_only_error(self, error_lines):
        result = list(iter_error_lines(error_lines))
        assert len(result) == 5
        assert all("ERROR" in line for line in result)

    def test_is_a_generator(self, error_lines):
        gen = iter_error_lines(error_lines)
        assert hasattr(gen, "__next__")  # 生成器对象有 __next__

    def test_empty_when_no_error(self):
        assert list(iter_error_lines(["INFO a", "WARN b", "DEBUG c"])) == []

    def test_lazy_one_at_a_time(self):
        # 生成器惰性:每次 next 只产出一个
        gen = iter_error_lines(["INFO a", "ERROR boom", "ERROR crash"])
        first = next(gen)
        assert first == "ERROR boom"
        second = next(gen)
        assert second == "ERROR crash"


# ---------- top_n_by_price:迭代器消费 ----------
class TestTopNByPrice:
    def test_top3_descending(self, products):
        result = top_n_by_price(iter(products), n=3)
        assert result == ["27寸4K显示器", "人体工学椅", "降噪耳机"]

    def test_exhausts_the_iterator(self, products):
        it = iter(products)
        top_n_by_price(it, n=2)
        # 迭代器已被消费殆尽
        assert list(it) == []

    def test_n_more_than_total_returns_all(self, products):
        assert len(top_n_by_price(iter(products), n=100)) == 10

    def test_default_n_is_3(self, products):
        assert len(top_n_by_price(iter(products))) == 3

    def test_accepts_generator_expression(self, products):
        gen = (p for p in products)
        assert top_n_by_price(gen, n=1) == ["27寸4K显示器"]
