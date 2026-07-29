"""
Ch10 作业:正则表达式与字符串处理。

4 个任务。在每处 TODO 写实现,然后:

    uv run pytest 02_stdlib/ch10/test_ch10_assignment.py -v

全绿 = 你掌握了 Ch10。

每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
(正则语法看 §10.1 速查表;nginx 日志正则的逐段拆解看 §10.5。)
"""
import re


# ========== 预编译正则(模块级,复用高效)==========

# TODO: 预编译 nginx 日志正则(命名分组)。结构提示见 parse_nginx_log 的 docstring。
LOG_RE = None   # ← 换成 re.compile(r"...")

# TODO: 预编译 IP 地址正则
IP_RE = None    # ← 换成 re.compile(r"...")


# ========== §10.3/§10.5 re + 命名分组 ==========


def parse_nginx_log(line: str) -> dict | None:
    """
    【命名分组 · §10.5】解析一行 nginx 日志,提取 ip/time/method/path/status。
    合法行返回 dict(status 转 int);非法行返回 None。

    示例行:
        '192.168.1.1 - - [10/Oct/2023:13:55:36 +0000] "GET /api/products HTTP/1.1" 200 1234'
        -> {"ip":"192.168.1.1", "time":"...", "method":"GET", "path":"/api/products", "status":200}

    正则结构(LOG_RE 用这个,命名分组):
        (?P<ip>\d+\.\d+\.\d+\.\d+)           4 段数字用点连
         - - \[(?P<time>[^\]]+)\]             " - - [时间]"  时间是 ] 前的任意字符([^\]]+)
        "(?P<method>[A-Z]+) (?P<path>\S+) HTTP/[\d.]+"    "方法 路径 HTTP/x.x"
         (?P<status>\d+)                      状态码

    思路:m = LOG_RE.search(line);m 为 None 返回 None;否则 d = m.groupdict(),
         把 d["status"] 转成 int 后返回 d。
    """
    # TODO: search + 判空 + groupdict + status 转 int
    ...


# ========== §10.2 re.findall ==========


def extract_ips(text: str) -> list[str]:
    """
    【findall · §10.2】提取文本里所有 IP 地址。

    示例:
        extract_ips("from 1.2.3.4 to 10.0.0.5")  -> ["1.2.3.4", "10.0.0.5"]

    思路:IP 正则 \b\d{1,3}(?:\.\d{1,3}){3}\b(单词边界 + 4 段 1~3 位数字)。
         用预编译的 IP_RE.findall(text)。
    """
    # TODO: IP_RE.findall(text)
    ...


# ========== §10.2 re.sub ==========


def redact_phones(text: str) -> str:
    """
    【sub · §10.2】把手机号(1 开头 11 位)替换成 ***。

    示例:
        redact_phones("call 13812345678")  -> "call ***"

    思路:手机号正则 1[3-9]\d{9}(1 开头、第二位 3-9、再 9 位数字 = 11 位)。
         re.sub(正则, '***', text)。
    """
    # TODO: re.sub(r'1[3-9]\d{9}', '***', text)
    ...


# ========== §10.2 re.split ==========


def split_on(text: str, seps: str = r'[,;]') -> list[str]:
    """
    【split · §10.2】按【多种分隔符】(默认逗号或分号)拆分字符串。

    示例:
        split_on("a,b;c")  -> ["a", "b", "c"]

    思路:re.split(seps, text)。seps 本身是正则,默认 r'[,;]' 表示「逗号或分号」。
    """
    # TODO: re.split(seps, text)
    ...


# ---------------------------------------------------------------------
if __name__ == "__main__":
    from conftest import load_mock_json

    logs = load_mock_json("nginx_logs.json")
    for line in logs:
        print(parse_nginx_log(line))
    print("ips:", extract_ips("from 1.2.3.4 to 10.0.0.5"))
    print("redact:", redact_phones("call 13812345678"))
    print("split:", split_on("a,b;c"))
