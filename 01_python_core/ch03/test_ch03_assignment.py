"""
Ch03 作业测试。
运行: uv run pytest 01_python_core/ch03/test_ch03_assignment.py -v

测试用例按函数分组(class)。
products fixture 来自项目根 conftest.py(10 个商品,function 级隔离,每测重新加载)。
log_lines fixture 加载 assets/mock_data/logs.json(20 行:INFO 10 / WARN 5 / ERROR 5)。
断言期望值均已对照 mock 数据手工验算;自建小数据用例用于防硬编码蒙对。
"""
import pytest

from ch03_assignment import (
    cheap_product_names,
    find_first_error,
    indexed_summary,
    merge_product_lists,
    champion_and_rest,
    top_n_by_price,
    iter_error_lines,
    count_error_logs,
)
from conftest import load_mock_json


@pytest.fixture
def log_lines():
    return load_mock_json("logs.json")


# ---------- §3.1 cheap_product_names:列表推导式(带条件)----------
class TestCheapProductNames:
    def test_under_200(self, products):
        # <200: 无线鼠标159 / Python编程89 / 设计模式75.5 / 智能水杯199
        result = cheap_product_names(products, max_price=200)
        assert result == ["无线鼠标", "Python编程:从入门到实践", "设计模式", "智能水杯"]

    def test_default_max_price_is_200(self, products):
        assert len(cheap_product_names(products)) == 4

    def test_boundary_price_excluded(self):
        # 拦住 <= 的错误实现:价格恰好等于 max_price 必须排除
        items = [{"name": "刚好200", "price": 200.0}, {"name": "便宜1分", "price": 199.99}]
        assert cheap_product_names(items, max_price=200) == ["便宜1分"]

    def test_custom_data(self):
        # 防硬编码:与 fixture 不同的数据
        items = [
            {"name": "甲", "price": 50.0},
            {"name": "乙", "price": 500.0},
            {"name": "丙", "price": 99.0},
        ]
        assert cheap_product_names(items, max_price=100) == ["甲", "丙"]

    def test_preserves_original_order(self, products):
        # 原顺序里 无线鼠标(id=2) 在 Python编程(id=4) 之前
        result = cheap_product_names(products, max_price=200)
        assert result[0] == "无线鼠标"

    def test_none_qualify(self, products):
        assert cheap_product_names(products, max_price=10) == []

    def test_empty_list(self):
        assert cheap_product_names([], max_price=200) == []


# ---------- §3.2 find_first_error:for-else ----------
class TestFindFirstError:
    def test_first_error_line(self, log_lines):
        # logs.json 第一条 ERROR 在第 4 行(redis 连接失败)
        assert find_first_error(log_lines) == (
            "2026-07-18 09:00:03 ERROR Failed to connect to redis at localhost:6379"
        )

    def test_returns_none_when_clean(self):
        assert find_first_error(["INFO ok", "WARN meh", "DEBUG x"]) is None

    def test_returns_first_not_last(self):
        # 拦住「返回最后一条匹配」的错误实现
        logs = ["INFO a", "ERROR first", "ERROR second"]
        assert find_first_error(logs) == "ERROR first"

    def test_empty_list(self):
        # 空循环直接进 else → None
        assert find_first_error([]) is None

    def test_accepts_generator(self, log_lines):
        # 生成器(只能遍历一次)同样适用:for-else 不挑可迭代对象
        gen = (line for line in log_lines)
        assert "redis" in find_first_error(gen)


# ---------- §3.3 indexed_summary:enumerate ----------
class TestIndexedSummary:
    def test_format_first(self, products):
        assert indexed_summary(products)[0] == "1. 机械键盘 (¥599.0)"

    def test_format_third(self, products):
        assert indexed_summary(products)[2] == "3. 27寸4K显示器 (¥2199.0)"

    def test_numbering_starts_at_1(self, products):
        # 拦住 enumerate 忘传 start=1 的实现
        assert indexed_summary(products)[0].startswith("1. ")

    def test_count(self, products):
        assert len(indexed_summary(products)) == 10

    def test_custom_data(self):
        # 防硬编码:自建小列表
        items = [{"name": "甲", "price": 10.0}, {"name": "乙", "price": 20.5}]
        assert indexed_summary(items) == ["1. 甲 (¥10.0)", "2. 乙 (¥20.5)"]

    def test_empty_list(self):
        assert indexed_summary([]) == []


# ---------- §3.3 merge_product_lists:zip ----------
class TestMergeProductLists:
    def test_pairs(self):
        result = merge_product_lists(["键盘", "鼠标"], [599.0, 159.0])
        assert result == [("键盘", 599.0), ("鼠标", 159.0)]

    def test_with_fixture_data(self, products):
        names = [p["name"] for p in products]
        prices = [p["price"] for p in products]
        result = merge_product_lists(names, prices)
        assert result[0] == ("机械键盘", 599.0)
        assert result[4] == ("设计模式", 75.5)
        assert len(result) == 10

    def test_truncates_to_shorter(self):
        # zip 语义:按最短的截断,多出来的静默丢弃
        result = merge_product_lists(["a", "b", "c"], [1.0, 2.0])
        assert result == [("a", 1.0), ("b", 2.0)]

    def test_each_is_2tuple(self):
        result = merge_product_lists(["x", "y"], [1.0, 2.0])
        assert all(isinstance(t, tuple) and len(t) == 2 for t in result)

    def test_empty(self):
        assert merge_product_lists([], []) == []
        assert merge_product_lists(["a"], []) == []


# ---------- §3.4 champion_and_rest:星号解包 ----------
class TestChampionAndRest:
    def test_basic(self):
        result = champion_and_rest(["机械键盘", "无线鼠标", "27寸4K显示器"])
        assert result == ("机械键盘", ["无线鼠标", "27寸4K显示器"])

    def test_single_element(self):
        assert champion_and_rest(["机械键盘"]) == ("机械键盘", [])

    def test_empty_returns_none_and_empty(self):
        # 空序列星号解包会 ValueError,必须先判空
        assert champion_and_rest([]) == (None, [])

    def test_rest_is_list(self):
        champion, rest = champion_and_rest(["A", "B", "C"])
        assert champion == "A"
        assert isinstance(rest, list) and rest == ["B", "C"]

    def test_does_not_mutate_input(self):
        names = ["A", "B", "C"]
        champion_and_rest(names)
        assert names == ["A", "B", "C"]

    def test_real_scene_top3(self, products):
        # 真实场景:热销榜第 1 名大卡 + 其余小字
        top3 = top_n_by_price(iter(products), n=3)
        champion, others = champion_and_rest(top3)
        assert champion == "27寸4K显示器"
        assert others == ["人体工学椅", "降噪耳机"]


# ---------- §3.5 top_n_by_price:迭代器消费 ----------
class TestTopNByPrice:
    def test_top3_descending(self, products):
        result = top_n_by_price(iter(products), n=3)
        assert result == ["27寸4K显示器", "人体工学椅", "降噪耳机"]

    def test_exhausts_the_iterator(self, products):
        it = iter(products)
        top_n_by_price(it, n=2)
        # 迭代器已被消费殆尽:再 list 就是 []
        assert list(it) == []

    def test_custom_data(self):
        # 防硬编码:自建小列表
        items = iter([
            {"name": "甲", "price": 10.0},
            {"name": "乙", "price": 30.0},
            {"name": "丙", "price": 20.0},
        ])
        assert top_n_by_price(items, n=2) == ["乙", "丙"]

    def test_n_more_than_total_returns_all(self, products):
        assert len(top_n_by_price(iter(products), n=100)) == 10

    def test_default_n_is_3(self, products):
        assert len(top_n_by_price(iter(products))) == 3

    def test_accepts_generator_expression(self, products):
        gen = (p for p in products)
        assert top_n_by_price(gen, n=1) == ["27寸4K显示器"]

    def test_empty_iterator(self):
        assert top_n_by_price(iter([]), n=3) == []


# ---------- §3.6 iter_error_lines:生成器 yield ----------
class TestIterErrorLines:
    def test_filters_only_error(self, log_lines):
        result = list(iter_error_lines(log_lines))
        assert len(result) == 5
        assert all("ERROR" in line for line in result)

    def test_is_a_generator(self, log_lines):
        # 拦住「用 list 收集再 return」的实现:返回值必须是生成器
        gen = iter_error_lines(log_lines)
        assert hasattr(gen, "__next__")

    def test_lazy_one_at_a_time(self):
        # 惰性:每次 next 只产出一个,产出顺序 = 原顺序
        gen = iter_error_lines(["INFO a", "ERROR boom", "ERROR crash"])
        assert next(gen) == "ERROR boom"
        assert next(gen) == "ERROR crash"
        with pytest.raises(StopIteration):
            next(gen)

    def test_calling_does_not_execute(self):
        # 调用生成器函数不执行函数体(只是造机器)
        executed = []

        def spy_lines():
            for line in ["INFO a", "ERROR b"]:
                executed.append(line)
                yield line

        gen = iter_error_lines(spy_lines())
        assert executed == []          # 一个都还没消费
        assert next(gen) == "ERROR b"  # 第一次 next 才真正驱动
        assert executed == ["INFO a", "ERROR b"]

    def test_empty_when_no_error(self):
        assert list(iter_error_lines(["INFO a", "WARN b", "DEBUG c"])) == []

    def test_empty_input(self):
        assert list(iter_error_lines([])) == []


# ---------- §3.7 count_error_logs:生成器表达式 ----------
class TestCountErrorLogs:
    def test_count_errors_default(self, log_lines):
        assert count_error_logs(log_lines) == 5

    def test_count_warn(self, log_lines):
        # 拦住硬编码 "ERROR" 的实现:keyword 必须真的用上
        assert count_error_logs(log_lines, keyword="WARN") == 5

    def test_count_info(self, log_lines):
        assert count_error_logs(log_lines, keyword="INFO") == 10

    def test_zero_when_absent(self, log_lines):
        assert count_error_logs(log_lines, keyword="FATAL") == 0

    def test_accepts_generator(self, log_lines):
        # 流式来源(生成器)也能直接统计
        gen = (line for line in log_lines)
        assert count_error_logs(gen) == 5

    def test_empty_input(self):
        assert count_error_logs([]) == 0
