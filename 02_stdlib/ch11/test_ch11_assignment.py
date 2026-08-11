"""
Ch11 作业测试。运行: uv run pytest 02_stdlib/ch11/test_ch11_assignment.py -v

每个函数一个 TestXxx 类(命名 = Test + 函数名 PascalCase,web 端按类名单跑)。
覆盖:正常 case ≥ 2 + 边界 case(非法 JSON / 空输入 / 跨月跨年 / 跨时区跨日 /
引号字段 / CRLF 换行)≥ 1;CSV 断言精确到 \\r\\n,所有预期值手工验算过。

mock 数据:assets/mock_data/order_events.json(7 条混合时区收款事件,
其中 ORD-1005 / ORD-1007 是「字符串前缀是 20 号、北京时间是 21 号」的跨日陷阱)。
"""
import json
from datetime import date, datetime, timedelta

import pytest

from ch11_assignment import (
    daily_reconcile_report,
    delivery_date,
    export_reconcile_csv,
    order_receipt_json,
    parse_event_time,
    parse_order_event,
    parse_price_csv,
    snapshot_to_json,
    utc_to_beijing,
)
from conftest import load_mock_json


@pytest.fixture
def order_events():
    return load_mock_json("order_events.json")


@pytest.fixture
def events_jsonl(order_events):
    """把 mock 事件拼成 MQ 导出的 JSONL 文本(每行一个 JSON)。"""
    return "\n".join(json.dumps(e) for e in order_events)


# ---------- parse_order_event:json.loads ----------
class TestParseOrderEvent:
    def test_parses_event(self):
        s = '{"order_id":"ORD-1001","amount":599.0,"occurred_at":"2026-07-21T09:15:00+08:00"}'
        r = parse_order_event(s)
        assert r["order_id"] == "ORD-1001"
        assert r["amount"] == 599.0

    def test_type_mapping(self):
        # JSON → Python 类型映射:true→True,null→None,整数→int,小数→float
        r = parse_order_event('{"qty": 2, "amount": 59.9, "paid": true, "coupon": null}')
        assert r == {"qty": 2, "amount": 59.9, "paid": True, "coupon": None}
        assert isinstance(r["qty"], int)
        assert isinstance(r["amount"], float)

    def test_mock_event_roundtrip(self, order_events):
        r = parse_order_event(json.dumps(order_events[0]))
        assert r == order_events[0]

    def test_invalid_raises(self):
        # 脏事件不吞:抛 JSONDecodeError(ValueError 子类),上层进死信队列
        with pytest.raises(json.JSONDecodeError):
            parse_order_event("not json")

    def test_invalid_is_value_error(self):
        with pytest.raises(ValueError):
            parse_order_event("{broken")


# ---------- order_receipt_json:json.dumps 三参数 ----------
class TestOrderReceiptJson:
    def test_exact_output_sorted_indented(self):
        # 手工验算:indent=2 → 每键一行两空格缩进;sort_keys → a 在 b 前
        assert order_receipt_json({"b": 1, "a": 2}) == '{\n  "a": 2,\n  "b": 1\n}'

    def test_chinese_not_escaped(self):
        s = order_receipt_json({"buyer": "张三"})
        assert "张三" in s
        assert "\\u" not in s   # ensure_ascii=False,不出现转义

    def test_keys_sorted_with_mock(self, order_events):
        s = order_receipt_json(order_events[0])
        # amount < occurred_at < order_id(字典序)
        assert s.index('"amount"') < s.index('"occurred_at"') < s.index('"order_id"')

    def test_roundtrip(self, order_events):
        for e in order_events:
            assert json.loads(order_receipt_json(e)) == e


# ---------- parse_event_time:datetime.fromisoformat ----------
class TestParseEventTime:
    def test_naive_datetime(self):
        dt = parse_event_time("2026-07-21T10:30:00")
        assert (dt.year, dt.month, dt.day, dt.hour, dt.minute) == (2026, 7, 21, 10, 30)
        assert dt.utcoffset() is None   # 无时区后缀 → naive

    def test_with_offset(self):
        dt = parse_event_time("2026-07-21T10:30:00+08:00")
        assert dt.utcoffset() == timedelta(hours=8)

    def test_zulu_suffix(self):
        # 3.11+ fromisoformat 直接认 Z(UTC)
        dt = parse_event_time("2026-07-21T02:30:00Z")
        assert dt.utcoffset() == timedelta(0)
        assert dt.hour == 2

    def test_date_only(self):
        assert parse_event_time("2026-07-21") == datetime(2026, 7, 21, 0, 0)

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            parse_event_time("昨天")


# ---------- delivery_date:date + timedelta ----------
class TestDeliveryDate:
    def test_simple_add(self):
        assert delivery_date("2026-07-21", 3) == "2026-07-24"

    def test_cross_month(self):
        assert delivery_date("2026-01-31", 1) == "2026-02-01"   # 1 月 31 日 +1 → 2 月 1 日

    def test_cross_year(self):
        assert delivery_date("2026-12-31", 1) == "2027-01-01"

    def test_zero_and_negative(self):
        assert delivery_date("2026-07-21", 0) == "2026-07-21"
        assert delivery_date("2026-07-21", -1) == "2026-07-20"


# ---------- utc_to_beijing:timezone + astimezone ----------
class TestUtcToBeijing:
    def test_plus_zero_offset(self):
        assert utc_to_beijing("2026-07-21T02:30:00+00:00") == "2026-07-21T10:30:00+08:00"

    def test_zulu_suffix(self):
        assert utc_to_beijing("2026-07-21T02:30:00Z") == "2026-07-21T10:30:00+08:00"

    def test_cross_day(self):
        # UTC 20:00 + 8h = 次日 04:00,跨日自动处理
        assert utc_to_beijing("2026-07-21T20:00:00Z") == "2026-07-22T04:00:00+08:00"

    def test_other_offset(self):
        # 12:30+02:00 = 10:30 UTC → 18:30+08:00
        assert utc_to_beijing("2026-07-21T12:30:00+02:00") == "2026-07-21T18:30:00+08:00"


# ---------- parse_price_csv:csv.DictReader ----------
class TestParsePriceCsv:
    def test_two_rows(self):
        text = "sku,price\nKB-001,549.00\nMS-002,139.00\n"
        assert parse_price_csv(text) == [
            {"sku": "KB-001", "price": 549.0},
            {"sku": "MS-002", "price": 139.0},
        ]

    def test_price_is_float(self):
        r = parse_price_csv("sku,price\nKB-001,549.00\n")
        assert isinstance(r[0]["price"], float)   # DictReader 读出是 str,必须转

    def test_crlf_line_ending(self):
        # Excel/Windows 导出的 \r\n 一样能解
        assert parse_price_csv("sku,price\r\nKB-001,549.00\r\n") == [
            {"sku": "KB-001", "price": 549.0},
        ]

    def test_quoted_value(self):
        # 引号保护的值:手写 split(",") 在这里会裂(逗号/引号场景)
        assert parse_price_csv('sku,price\nKB-001,"549.00"\n') == [
            {"sku": "KB-001", "price": 549.0},
        ]

    def test_header_only(self):
        assert parse_price_csv("sku,price\n") == []


# ---------- export_reconcile_csv:csv.DictWriter ----------
class TestExportReconcileCsv:
    def test_exact_output(self):
        # 手工验算:表头 + 一行,csv 标准行尾 \r\n;599.0 str 化是 "599.0"
        rows = [{"order_id": "ORD-1001", "amount": 599.0, "status": "PAID"}]
        assert export_reconcile_csv(rows) == "order_id,amount,status\r\nORD-1001,599.0,PAID\r\n"

    def test_row_order_preserved(self):
        rows = [
            {"order_id": "ORD-1002", "amount": 159.0, "status": "PAID"},
            {"order_id": "ORD-1001", "amount": 599.0, "status": "REFUND"},
        ]
        s = export_reconcile_csv(rows)
        assert s == (
            "order_id,amount,status\r\n"
            "ORD-1002,159.0,PAID\r\n"
            "ORD-1001,599.0,REFUND\r\n"
        )

    def test_empty_still_has_header(self):
        assert export_reconcile_csv([]) == "order_id,amount,status\r\n"

    def test_value_with_comma_quoted(self):
        # 千分位金额字符串含逗号 → csv 自动加引号;f-string 拼接在这里会裂
        rows = [{"order_id": "A", "amount": "1,299.00", "status": "PAID"}]
        assert export_reconcile_csv(rows) == 'order_id,amount,status\r\nA,"1,299.00",PAID\r\n'


# ---------- snapshot_to_json:default 钩子 ----------
class TestSnapshotToJson:
    def test_serializes_datetime(self):
        s = snapshot_to_json({"order_id": "ORD-1001", "paid_at": datetime(2026, 7, 21, 10, 30)})
        assert json.loads(s)["paid_at"] == "2026-07-21T10:30:00"

    def test_serializes_date(self):
        s = snapshot_to_json({"day": date(2026, 7, 21)})
        assert json.loads(s)["day"] == "2026-07-21"

    def test_nested_datetime(self):
        # default 钩子对嵌套结构递归生效
        s = snapshot_to_json({"items": [{"at": datetime(2026, 7, 21, 8, 0)}]})
        assert json.loads(s)["items"][0]["at"] == "2026-07-21T08:00:00"

    def test_chinese_not_escaped(self):
        s = snapshot_to_json({"buyer": "张三", "paid_at": datetime(2026, 7, 21)})
        assert "张三" in s

    def test_unsupported_type_raises(self):
        # set 连钩子也救不了 → 必须 raise TypeError,不能静默返回 None
        with pytest.raises(TypeError):
            snapshot_to_json({"tags": {"a", "b"}})


# ---------- daily_reconcile_report:综合 ----------
class TestDailyReconcileReport:
    # mock 数据验算(北京时间):
    #   ORD-1001 09:15+08 → 21 号 09:15 ｜ ORD-1002 11:02+08 → 21 号 11:02
    #   ORD-1003 22:30+08 → 20 号 22:30(20 号的款)
    #   ORD-1004 02:30Z   → 21 号 10:30
    #   ORD-1005 17:00Z(20 号)→ 21 号 01:00  ← 跨日陷阱
    #   ORD-1006 15:40+08 → 21 号 15:40
    #   ORD-1007 16:30Z(20 号)→ 21 号 00:30  ← 跨日陷阱
    def test_day_21_full_report(self, events_jsonl):
        assert daily_reconcile_report(events_jsonl, "2026-07-21") == (
            "date,order_id,amount\r\n"
            "2026/07/21,ORD-1007,399.00\r\n"   # 00:30(UTC 20 号 16:30)
            "2026/07/21,ORD-1005,75.50\r\n"    # 01:00(UTC 20 号 17:00)
            "2026/07/21,ORD-1001,599.00\r\n"   # 09:15
            "2026/07/21,ORD-1004,89.00\r\n"    # 10:30(UTC 21 号 02:30)
            "2026/07/21,ORD-1002,159.00\r\n"   # 11:02
            "2026/07/21,ORD-1006,1299.00\r\n"  # 15:40
        )

    def test_day_20_single_row(self, events_jsonl):
        assert daily_reconcile_report(events_jsonl, "2026-07-20") == (
            "date,order_id,amount\r\n"
            "2026/07/20,ORD-1003,2199.00\r\n"
        )

    def test_day_without_events(self, events_jsonl):
        assert daily_reconcile_report(events_jsonl, "2026-07-22") == "date,order_id,amount\r\n"

    def test_trailing_blank_lines_tolerated(self, events_jsonl):
        # MQ 导出文件末尾常带空行,不能炸
        assert daily_reconcile_report(events_jsonl + "\n\n", "2026-07-20") == (
            "date,order_id,amount\r\n"
            "2026/07/20,ORD-1003,2199.00\r\n"
        )

    def test_handmade_mixed_zones(self):
        # 手工小数据,防对着 mock 硬编码;B 是 UTC 17:00 = 北京 01:00,排在 A 前
        text = (
            '{"order_id":"A","amount":10.0,"occurred_at":"2026-07-21T08:00:00+08:00"}\n'
            '{"order_id":"B","amount":20.0,"occurred_at":"2026-07-20T17:00:00Z"}\n'
        )
        assert daily_reconcile_report(text, "2026-07-21") == (
            "date,order_id,amount\r\n"
            "2026/07/21,B,20.00\r\n"
            "2026/07/21,A,10.00\r\n"
        )
