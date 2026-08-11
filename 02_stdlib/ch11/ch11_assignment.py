"""
Ch11 作业:数据交换 —— json / csv / datetime。

场景:你是电商中台工程师,负责「订单数据交换」模块——收款事件从 MQ 以 JSONL 进来,
要解析事件 → 给前端发回执 → 解析事件时间 → 推算送达日 → UTC 换算北京时间 →
读运营调价 CSV → 给财务导出对账 CSV → 给下游发订单快照 → 汇总每日对账报表。

9 个任务围绕 assets/mock_data/order_events.json(7 条混合时区的收款事件)展开。
在每处 TODO 写实现,然后:

    uv run pytest 02_stdlib/ch11/test_ch11_assignment.py -v

全绿 = 你掌握了 Ch11。

约定:
- 收款事件 dict 形如
    {"order_id": "ORD-1001", "amount": 599.0, "occurred_at": "2026-07-21T09:15:00+08:00"}
- occurred_at 是 ISO 8601 字符串,可能带 +08:00 / Z / +00:00 等任意时区后缀。
- JSONL = 每行一个 JSON 对象(MQ 导出/日志收集的常见格式)。
- 每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
  (提示只给思路和关键语法,不给完整代码——自己组合才有掌握感。)
"""
import csv
import io
import json
from datetime import date, datetime, timedelta, timezone


# ========== §11.1 json.loads:解析订单事件 ==========


def parse_order_event(text: str) -> dict:
    """
    【json.loads · §11.1】MQ 消费端:把一条收款事件(JSON 字符串)解析成 dict。

    示例:
        parse_order_event('{"order_id":"ORD-1001","amount":599.0}')
            -> {"order_id": "ORD-1001", "amount": 599.0}
        parse_order_event('{"qty":2,"paid":true,"coupon":null}')
            -> {"qty": 2, "paid": True, "coupon": None}   (true→True, null→None)
        parse_order_event("not json")  -> 抛 json.JSONDecodeError

    提示:json.loads(text) 一行。不要 try/except 吞异常——脏事件该让
         JSONDecodeError(ValueError 子类)抛给上层,消费框架捕到后进死信队列。
    """
    # TODO: return json.loads(text)
    ...


# ========== §11.2 json.dumps:序列化与格式化 ==========


def order_receipt_json(order: dict) -> str:
    """
    【json.dumps · §11.2】订单支付成功,生成给前端/财务看的回执 JSON 字符串。
    要求三合一:缩进美观 + 中文不转义 + 键按字典序排序(两次输出可 diff 对账)。

    示例(逐字符精确):
        order_receipt_json({"b": 1, "a": 2})
            -> '{\\n  "a": 2,\\n  "b": 1\\n}'   (即打印出来是多行,a 排在 b 前)
        order_receipt_json({"buyer": "张三"})
            -> 输出里含 "张三" 二字,不含 \\u 转义

    提示:json.dumps(order, indent=2, ensure_ascii=False, sort_keys=True),
         三个参数缺一不可。ensure_ascii=False 让中文原样输出(默认会转义成 \\uXXXX)。
    """
    # TODO: json.dumps + indent / ensure_ascii / sort_keys 三参数
    ...


# ========== §11.3 datetime:解析与格式化 ==========


def parse_event_time(s: str) -> datetime:
    """
    【fromisoformat · §11.3】把事件时间戳(ISO 8601 字符串)解析成 datetime 对象。
    输入可能带 +08:00 / Z(UTC)后缀,也可能不带时区,fromisoformat 通吃。

    示例:
        parse_event_time("2026-07-21T10:30:00").hour          -> 10
        parse_event_time("2026-07-21T02:30:00Z").utcoffset()  -> timedelta(0)  (Z = UTC)
        parse_event_time("2026-07-21").day                    -> 21  (纯日期 → 当天 00:00)
        parse_event_time("昨天")  -> 抛 ValueError

    提示:datetime.fromisoformat(s) 一行(3.11+ 直接认 "Z",不用 replace)。
         别用 strptime 手写格式串——那是给非 ISO 格式准备的。
    """
    # TODO: datetime.fromisoformat(s)
    ...


# ========== §11.4 timedelta:日期推算 ==========


def delivery_date(order_date_s: str, days: int) -> str:
    """
    【timedelta · §11.4】下单页展示「预计送达日」:下单日期 + 承诺天数,返回 ISO 日期串。

    示例:
        delivery_date("2026-07-21", 3)   -> "2026-07-24"
        delivery_date("2026-01-31", 1)   -> "2026-02-01"   (自动跨月)
        delivery_date("2026-12-31", 1)   -> "2027-01-01"   (自动跨年)
        delivery_date("2026-07-21", 0)   -> "2026-07-21"
        delivery_date("2026-07-21", -1)  -> "2026-07-20"   (负值往前,查「昨天下的单」)

    提示:date.fromisoformat(order_date_s) + timedelta(days=days),返回 .isoformat()。
         千万别自己算每月几天——timedelta 管闰年大小月。
    """
    # TODO: date.fromisoformat + timedelta(days=days) + .isoformat()
    ...


# ========== §11.5 时区:astimezone 换算 ==========


def utc_to_beijing(s: str) -> str:
    """
    【astimezone · §11.5】WMS 回传的时间带任意时区后缀(Z / +00:00 / +02:00...),
    统一换算成北京时间(UTC+8),返回 ISO 字符串。

    示例(逐个手算验证过):
        utc_to_beijing("2026-07-21T02:30:00+00:00")  -> "2026-07-21T10:30:00+08:00"
        utc_to_beijing("2026-07-21T02:30:00Z")       -> "2026-07-21T10:30:00+08:00"
        utc_to_beijing("2026-07-21T20:00:00Z")       -> "2026-07-22T04:00:00+08:00"  (跨日!)
        utc_to_beijing("2026-07-21T12:30:00+02:00")  -> "2026-07-21T18:30:00+08:00"

    提示:datetime.fromisoformat(s).astimezone(timezone(timedelta(hours=8))).isoformat()。
         astimezone 按「同一时刻」换算,跨日自动处理。
         ⚠️ 别手动 +timedelta(hours=8):数值对但丢掉时区信息,后续比较全靠脑记。
    """
    # TODO: fromisoformat → astimezone(+08:00) → isoformat
    ...


# ========== §11.6 csv 读取:DictReader ==========


def parse_price_csv(text: str) -> list[dict]:
    """
    【DictReader · §11.6】运营发来调价单 CSV(Excel 导出),读成
    [{"sku": 原样字符串, "price": float 数值}, ...]。

    示例:
        parse_price_csv("sku,price\\nKB-001,549.00\\nMS-002,139.00\\n")
            -> [{"sku": "KB-001", "price": 549.0}, {"sku": "MS-002", "price": 139.0}]
        parse_price_csv("sku,price\\r\\nKB-001,549.00\\r\\n")   (\\r\\n 是 Excel 常态)
            -> [{"sku": "KB-001", "price": 549.0}]
        parse_price_csv('sku,price\\nKB-001,"549.00"\\n')       (引号保护逗号/空格)
            -> [{"sku": "KB-001", "price": 549.0}]
        parse_price_csv("sku,price\\n")  -> []   (只有表头)

    提示:csv.DictReader(io.StringIO(text)) —— StringIO 把字符串包装成内存文件。
         两个细节:① DictReader 读出的【所有值都是 str】,price 要 float() 转;
         ② 千万别 line.split(",")——引号字段会裂开。
    """
    # TODO: DictReader 逐行读,组装 {"sku": row["sku"], "price": float(row["price"])}
    ...


# ========== §11.7 csv 写出:DictWriter ==========


def export_reconcile_csv(rows: list[dict]) -> str:
    """
    【DictWriter · §11.7】给财务导出对账 CSV 字符串(内存写出,直接回 HTTP 响应)。
    列固定:order_id,amount,status(按此顺序),先写表头再写数据。

    示例(逐字符精确,注意 csv 标准行尾是 \\r\\n):
        export_reconcile_csv([{"order_id": "ORD-1001", "amount": 599.0, "status": "PAID"}])
            -> "order_id,amount,status\\r\\nORD-1001,599.0,PAID\\r\\n"
        export_reconcile_csv([])   -> "order_id,amount,status\\r\\n"   (空表也有表头)
        export_reconcile_csv([{"order_id": "A", "amount": "1,299.00", "status": "PAID"}])
            -> 'order_id,amount,status\\r\\nA,"1,299.00",PAID\\r\\n'   (含逗号自动加引号)

    提示:buf = io.StringIO();csv.DictWriter(buf, fieldnames=[三列]);
         writeheader() 写表头,writerows(rows) 写数据,最后 buf.getvalue()。
         别用 f-string 拼——值里有逗号时列就错位了。
    """
    # TODO: StringIO + DictWriter(fieldnames=...) + writeheader + writerows + getvalue
    ...


# ========== §11.8 序列化陷阱:datetime default 钩子 ==========


def snapshot_to_json(obj) -> str:
    """
    【default 钩子 · §11.8】给下游发订单快照:对象里嵌着 datetime/date,
    json.dumps 默认不认识(TypeError),用 default 钩子教它转成 ISO 字符串。
    快照可能含中文买家名,顺手保证中文不转义。

    示例:
        snapshot_to_json({"order_id": "ORD-1001", "paid_at": datetime(2026, 7, 21, 10, 30)})
            -> 含 '"paid_at": "2026-07-21T10:30:00"'
        snapshot_to_json({"day": date(2026, 7, 21)})     -> 含 '"day": "2026-07-21"'
        snapshot_to_json({"buyer": "张三"})               -> 含 "张三"(不转义)
        snapshot_to_json({"tags": {"a", "b"}})            -> 抛 TypeError(set 救不了)

    提示:在函数内部定义钩子(用完即弃):
            def _default(o):
                if isinstance(o, (datetime, date)):
                    return o.isoformat()
                raise TypeError(...)   ← 不认识的类型必须 raise,别返回 None 静默放走
         然后 json.dumps(obj, default=_default, ensure_ascii=False)。钩子对嵌套递归生效。
    """
    # TODO: 内部定义 _default 钩子 + json.dumps(obj, default=..., ensure_ascii=False)
    ...


# ========== §11.9 综合:每日对账报表 ==========


def daily_reconcile_report(events_text: str, day: str) -> str:
    """
    【综合 · §11.9】财务每日对账:从 MQ 导出的 JSONL 文本里,挑出【北京时间】
    落在 day 的收款事件,按发生时刻升序,导出 CSV。

    输入 events_text 每行一个 JSON(末尾可能有空行,跳过):
        {"order_id": "ORD-1001", "amount": 599.0, "occurred_at": "2026-07-21T09:15:00+08:00"}
    occurred_at 带任意时区——必须先 astimezone 换算成北京时间,再按【日期】过滤
    (看字符串前缀会算错:"2026-07-20T17:00:00Z" 北京时间是 21 号 01:00!)。

    输出 CSV(csv.writer 写,行尾 \\r\\n):
        表头 date,order_id,amount
        数据行:date 用 %Y/%m/%d 斜杠格式,amount 用 f"{...:.2f}" 保留两位小数

    示例:
        text = (
            '{"order_id":"A","amount":10.0,"occurred_at":"2026-07-21T08:00:00+08:00"}\\n'
            '{"order_id":"B","amount":20.0,"occurred_at":"2026-07-20T17:00:00Z"}\\n'
        )
        daily_reconcile_report(text, "2026-07-21")
            -> "date,order_id,amount\\r\\n2026/07/21,B,20.00\\r\\n2026/07/21,A,10.00\\r\\n"
            (B 是 UTC 17:00 = 北京 01:00,排在 A 的 08:00 前)
        daily_reconcile_report(text, "2026-07-22")  -> "date,order_id,amount\\r\\n"

    提示:步骤 = 逐行 strip/跳过空行 → json.loads → fromisoformat →
         astimezone(timezone(timedelta(hours=8))) → .date() == date.fromisoformat(day) 过滤 →
         收 (dt, event) 进列表 → sorted(key=lambda t: t[0])(aware datetime 可直接比)→
         io.StringIO + csv.writer:writerow 表头,再逐行 writerow([strftime, id, f-string])。
         【内联实现,别调前面的函数】——web 端单题跑时它们还是骨架。
    """
    # TODO: JSONL 解析 → astimezone 过滤 → sorted → csv.writer 导出
    ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     uv run python 02_stdlib/ch11/ch11_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # 仓库根,好导 conftest
    from conftest import load_mock_json

    events = load_mock_json("order_events.json")
    jsonl = "\n".join(json.dumps(e) for e in events)

    print("===== 订单数据交换 =====")
    first = parse_order_event(jsonl.splitlines()[0])
    print("解析首条事件:", first["order_id"], first["amount"])
    print("回执 JSON:", order_receipt_json({"buyer": "张三", "amount": 599.0}))
    print("事件时间:", parse_event_time(first["occurred_at"]))
    print("送达日(+3天):", delivery_date("2026-07-21", 3))
    print("UTC→北京:", utc_to_beijing("2026-07-20T17:00:00Z"))
    print("调价 CSV:", parse_price_csv("sku,price\nKB-001,549.00\n"))
    print("对账 CSV:", repr(export_reconcile_csv(
        [{"order_id": "ORD-1001", "amount": 599.0, "status": "PAID"}]
    )))
    print("快照 JSON:", snapshot_to_json({"order_id": "ORD-1001", "paid_at": datetime(2026, 7, 21, 10, 30)}))
    print("--- 07-21 对账报表 ---")
    print(daily_reconcile_report(jsonl, "2026-07-21"))
