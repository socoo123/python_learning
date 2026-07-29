"""
Ch11 作业:json / csv / datetime。

5 个任务。在每处 TODO 写实现,然后:

    uv run pytest 02_stdlib/ch11/test_ch11_assignment.py -v

全绿 = 你掌握了 Ch11。

每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
import json
from datetime import date, datetime


# ========== §11.1 json.loads ==========


def parse_products_json(text: str):
    """
    【json.loads · §11.1】把 JSON 字符串解析成 Python 对象。

    示例:
        parse_products_json('[{"name":"键盘","price":599}]')[0]["name"]  -> "键盘"

    思路:json.loads(字符串)。
    """
    # TODO: json.loads(text)
    ...


# ========== §11.2 json.dumps(格式化)==========


def to_pretty_json(obj) -> str:
    """
    【json.dumps · §11.2】把对象序列化成【美观的】JSON 字符串:带缩进 + 中文原样输出。

    示例:
        to_pretty_json({"name":"键盘"})  -> 含 "键盘"(中文不被转义)

    思路:json.dumps(obj, indent=2, ensure_ascii=False)。
         indent=2 → 缩进美观;ensure_ascii=False → 中文不转义。
    """
    # TODO: json.dumps(obj, indent=2, ensure_ascii=False)
    ...


# ========== §11.3 datetime 解析 ==========


def parse_iso_datetime(s: str) -> datetime:
    """
    【datetime · §11.3】把 ISO 格式字符串解析成 datetime 对象。

    示例:
        dt = parse_iso_datetime("2026-07-21T10:30:00")
        dt.year   -> 2026
        dt.hour   -> 10

    思路:datetime.fromisoformat(s)(3.7+ 内置,直接解析 ISO 字符串)。
    """
    # TODO: datetime.fromisoformat(s)
    ...


# ========== §11.4 date + timedelta ==========


def days_between(s1: str, s2: str) -> int:
    """
    【date + timedelta · §11.4】两个日期字符串之间的天数差(绝对值,顺序无关)。

    示例:
        days_between("2026-07-01", "2026-07-21")  -> 20

    思路:
        d1 = date.fromisoformat(s1); d2 = date.fromisoformat(s2)
        两个 date 相减得到 timedelta,取 .days,再 abs() 取绝对值。
    """
    # TODO: date.fromisoformat + 相减 + .days + abs
    ...


# ========== §11.5 自定义序列化(处理 datetime)==========


def _datetime_default(o):
    """
    【default 钩子 · §11.5】json.dumps 遇到【不认识的对象】时调用的兜底函数。
    把 datetime/date 转成 ISO 字符串,其他类型抛 TypeError。

    思路:
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        raise TypeError(...)
    """
    # TODO: isinstance 判断 + isoformat / raise TypeError
    ...


def to_json_with_datetime(obj) -> str:
    """
    【default 钩子 · §11.5】序列化含 datetime 的对象。
    json.dumps 默认不认识 datetime(会报错),用 default=_datetime_default 教它。

    示例:
        to_json_with_datetime({"created_at": datetime(2026,7,21,10,30)})
        -> 含 "2026-07-21T10:30:00"

    思路:json.dumps(obj, default=_datetime_default)。
    """
    # TODO: json.dumps(obj, default=_datetime_default)
    ...


# ---------------------------------------------------------------------
if __name__ == "__main__":
    print(parse_products_json('[{"name":"键盘","price":599}]'))
    print(to_pretty_json({"name": "键盘", "price": 599}))
    print(parse_iso_datetime("2026-07-21T10:30:00"))
    print("days:", days_between("2026-07-01", "2026-07-21"))
    print(to_json_with_datetime({"created_at": datetime(2026, 7, 21, 10, 30)}))
