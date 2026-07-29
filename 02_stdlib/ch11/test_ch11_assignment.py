"""
Ch11 作业测试。运行: uv run pytest 02_stdlib/ch11/test_ch11_assignment.py -v
"""
import json
from datetime import date, datetime

import pytest

from ch11_assignment import (
    parse_products_json,
    to_pretty_json,
    parse_iso_datetime,
    days_between,
    to_json_with_datetime,
)


# ---------- parse_products_json:json.loads ----------
class TestParseProductsJson:
    def test_list_of_products(self):
        s = '[{"name":"键盘","price":599}]'
        r = parse_products_json(s)
        assert r[0]["name"] == "键盘"
        assert r[0]["price"] == 599

    def test_dict(self):
        assert parse_products_json('{"a":1}') == {"a": 1}

    def test_invalid_raises(self):
        with pytest.raises(json.JSONDecodeError):
            parse_products_json("not json")


# ---------- to_pretty_json:json.dumps ----------
class TestToPrettyJson:
    def test_indented(self):
        s = to_pretty_json({"a": 1})
        assert '"a": 1' in s   # indent=2 产生换行 + 缩进

    def test_chinese_not_escaped(self):
        s = to_pretty_json({"name": "键盘"})
        assert "键盘" in s     # ensure_ascii=False,中文原样输出

    def test_roundtrip(self):
        obj = {"x": [1, 2], "y": "hi"}
        assert parse_products_json(to_pretty_json(obj)) == obj


# ---------- parse_iso_datetime:datetime ----------
class TestParseIsoDatetime:
    def test_full_datetime(self):
        dt = parse_iso_datetime("2026-07-21T10:30:00")
        assert dt.year == 2026
        assert dt.hour == 10
        assert dt.minute == 30

    def test_date_only(self):
        dt = parse_iso_datetime("2026-07-21")
        assert dt.month == 7
        assert dt.day == 21

    def test_returns_datetime(self):
        assert isinstance(parse_iso_datetime("2026-01-01"), datetime)


# ---------- days_between:date + timedelta ----------
class TestDaysBetween:
    def test_same_day_zero(self):
        assert days_between("2026-07-21", "2026-07-21") == 0

    def test_twenty_days(self):
        assert days_between("2026-07-01", "2026-07-21") == 20

    def test_order_independent(self):
        # abs:参数顺序不影响结果
        assert days_between("2026-07-21", "2026-07-01") == 20

    def test_across_month(self):
        assert days_between("2026-01-31", "2026-03-01") == 29   # 2026 非闰年,2月28天


# ---------- to_json_with_datetime:自定义序列化 ----------
class TestToJsonWithDatetime:
    def test_serializes_datetime(self):
        dt = datetime(2026, 7, 21, 10, 30, 0)
        s = to_json_with_datetime({"created_at": dt})
        assert "2026-07-21T10:30:00" in s

    def test_serializes_date(self):
        d = date(2026, 7, 21)
        s = to_json_with_datetime({"d": d})
        assert "2026-07-21" in s

    def test_normal_data_still_works(self):
        s = to_json_with_datetime({"name": "x", "price": 10})
        assert "x" in s and "10" in s

    def test_unsupported_type_raises(self):
        # 没法序列化的类型,default 也救不了 → 抛 TypeError
        with pytest.raises(TypeError):
            to_json_with_datetime({"obj": object()})
