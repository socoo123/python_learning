"""
Ch25 作业:CLI 工具开发 —— Typer + Rich。

把脚本变成漂亮的命令行工具:Typer 用【类型注解】定义命令/参数/选项(= Java Picocli,
FastAPI 同作者);Rich 渲染彩色表格/面板。本作业把 Ch08 的日志分析器改造成 CLI。

设计要点(重要):把【纯逻辑】和【渲染】分开——纯逻辑函数返回数据好测,渲染用 Rich。
7 个填空:4 个纯/渲染函数 + 2 个 Typer 命令体 + 1 个复用综合。在每处 TODO 写实现,然后:

    uv run pytest 04_devops_scripts/ch25/test_ch25_assignment.py -v

全绿 = 你掌握了 Ch25。

每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。

约定:logs 是 list[dict],每条形如:
    {"ip": "192.168.1.1", "method": "GET", "path": "/api/products", "status": 200}
"""
import json
from collections import Counter
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(help="访问日志分析 CLI:状态码分布 + Top IP + 错误日志报告。")
console = Console()


@app.callback()
def _main() -> None:
    """访问日志分析 CLI。callback 让 app 成为「命令组」,analyze/report 作为子命令。"""


# ========== §25.3 纯逻辑:summarize_status ==========


def summarize_status(logs: list[dict]) -> dict[int, int]:
    """
    【纯逻辑 · §25.3】统计状态码分布,返回 {状态码: 次数}。

    示例(2 个 200、1 个 500):
        summarize_status(logs) -> {200: 2, 500: 1}

    思路(collections.Counter,Ch08 学过):
        return dict(Counter(log["status"] for log in logs))
        - Counter 数 status;dict() 转回普通 dict(Counter 是 dict 子类)
    """
    # TODO: Counter 数 status,dict() 转普通 dict
    ...


# ========== §25.3 纯逻辑:top_ips ==========


def top_ips(logs: list[dict], n: int = 5) -> list[tuple[str, int]]:
    """
    【纯逻辑 · §25.3】返回访问次数最多的前 n 个 IP,降序。
    每项是 (ip, 次数)。n 超过 IP 总数时返回全部。

    示例(1.1.1.1 访问 2 次、2.2.2.2 访问 1 次):
        top_ips(logs, n=2) -> [("1.1.1.1", 2), ("2.2.2.2", 1)]

    思路(Counter.most_common = Java stream sorted 降序 + limit):
        return Counter(log["ip"] for log in logs).most_common(n)
        - most_common(n) 返回 [(key, count), ...] 降序,自带 top-N 语义
    """
    # TODO: Counter(ip).most_common(n)
    ...


# ========== §25.3 纯逻辑:error_logs ==========


def error_logs(logs: list[dict], threshold: int = 500) -> list[dict]:
    """
    【纯逻辑 · §25.3】过滤出 status >= threshold 的日志(默认 5xx 错误)。
    保持原有顺序,返回新的 list(不改原列表)。

    示例(logs 里有 status 200/500/502):
        error_logs(logs)            -> [status=500 那条, status=502 那条]
        error_logs(logs, 400)       -> [status 400 及以上的所有]

    思路(Ch03 列表推导过滤):
        return [log for log in logs if log["status"] >= threshold]
        - Python 过滤不用 stream().filter(),一行推导式搞定
    """
    # TODO: 列表推导过滤 status >= threshold
    ...


# ========== §25.4 Rich:make_table ==========


def make_table(title: str, columns: list[str], rows: list[list[str]]) -> Table:
    """
    【Rich · §25.4】构造一个 Rich 表格对象(标题 + 表头 + 数据行)。
    注意:本函数只【构造】不【打印】——打印交给调用方(便于测试)。

    示例:
        t = make_table("Top IP", ["IP", "次数"], [["1.1.1.1", "5"]])
        # 之后:console.print(t) 才真正渲染到屏幕

    思路:
        table = Table(title=title)
        for col in columns:
            table.add_column(col)
        for row in rows:
            table.add_row(*row)        # *row 把 list 拆成多个参数(Ch01)
        return table
        - ⚠️ add_row(row) 会把整行塞进一个单元格;必须 add_row(*row) 解包
    """
    # TODO: Table(title=title) + add_column 循环 + add_row(*row) 循环
    ...


# ========== §25.5 Rich:make_summary_panel ==========


def make_summary_panel(status: dict[int, int], title: str = "状态码摘要") -> Panel:
    """
    【Rich · §25.5】把状态码分布做成一个 Panel(带边框标题的卡片)。
    每行一个状态码:`200: 13 次`,按键升序排列。只构造不打印。

    示例:
        make_summary_panel({200: 2, 500: 1})
        # 面板正文是:  "200: 2 次\n500: 1 次"

    思路:
        lines = [f"{code}: {cnt} 次" for code, cnt in sorted(status.items())]
        body = "\\n".join(lines)
        return Panel(body, title=title, border_style="green")
        - Panel(文本, title=...) 把一段文字装进卡片;sorted 保证顺序确定
    """
    # TODO: "\\n".join(f"{k}: {v} 次" for 升序) → Panel(body, title=title)
    ...


# ========== §25.6 Typer:analyze 命令 ==========


@app.command()
def analyze(
    path: Path = typer.Argument(..., help="日志 json 文件路径"),
    top: int = typer.Option(5, "--top", "-n", help="Top N 个 IP"),
    fmt: str = typer.Option("table", "--format", "-f", help="输出格式: table | json"),
) -> None:
    """
    【Typer · §25.6】分析日志文件:读 json → 算状态码分布 + Top IP → 输出。
    支持两种格式:table(Rich 表格)/ json(机器可读)。

    用法:
        uv run python 04_devops_scripts/ch25/ch25_assignment.py analyze access.json --top 3
        uv run python 04_devops_scripts/ch25/ch25_assignment.py analyze access.json -f json

    思路:
        logs = json.loads(Path(path).read_text(encoding="utf-8"))   # 读+解析
        status = summarize_status(logs)                              # §25.3
        ips = top_ips(logs, top)                                     # §25.3
        if fmt == "json":
            typer.echo(json.dumps({"status": status, "top_ips": ips}, ensure_ascii=False))
        else:
            rows = [[ip, str(cnt)] for ip, cnt in ips]
            console.print(make_table("Top IP", ["IP", "次数"], rows))  # §25.4
            typer.echo(f"状态码分布: {status}")
    """
    # TODO: 读 json → summarize_status + top_ips → 按 fmt 分支输出
    ...


# ========== §25.7 Typer:report 命令(复用综合) ==========


@app.command()
def report(
    path: Path = typer.Argument(..., help="日志 json 文件路径"),
    top: int = typer.Option(5, "--top", "-n", help="Top N 个 IP"),
    threshold: int = typer.Option(500, "--threshold", "-t", help="错误状态码阈值"),
) -> None:
    """
    【Typer · §25.7】生成完整巡检报告:状态码面板 + Top IP 表 + 错误日志表。
    复用前面所有函数——一个纯逻辑都不用新写,这正是「分离」的回报。

    用法:
        uv run python 04_devops_scripts/ch25/ch25_assignment.py report access.json --threshold 500

    思路:
        logs = json.loads(Path(path).read_text(encoding="utf-8"))
        console.print(make_summary_panel(summarize_status(logs)))          # ① 面板
        ip_rows = [[ip, str(c)] for ip, c in top_ips(logs, top)]
        console.print(make_table("Top IP", ["IP", "次数"], ip_rows))        # ② IP 表
        err_rows = [[l["ip"], l["path"], str(l["status"])] for l in error_logs(logs, threshold)]
        console.print(make_table("错误日志", ["IP", "路径", "状态码"], err_rows))  # ③ 错误表
    """
    # TODO: 依次 print 三个组件(make_summary_panel + 两个 make_table)
    ...


# ---------------------------------------------------------------------
# 开发模式下直接跑(不是测试):
#     uv run python 04_devops_scripts/ch25/ch25_assignment.py --help
#     uv run python 04_devops_scripts/ch25/ch25_assignment.py analyze <file> --top 3
#     uv run python 04_devops_scripts/ch25/ch25_assignment.py report  <file> --threshold 500
# ---------------------------------------------------------------------
if __name__ == "__main__":
    app()
