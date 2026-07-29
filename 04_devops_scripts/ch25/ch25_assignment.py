"""
Ch25 作业:CLI 工具开发 —— Typer + Rich。

把脚本变成漂亮的命令行工具:Typer 用【类型注解】定义命令/参数/选项(= Java Picocli,
FastAPI 同作者);Rich 渲染彩色表格/面板。本作业把 Ch08 的日志分析器改造成 CLI。

设计要点(重要):把【纯逻辑】和【渲染】分开——纯逻辑函数好测,渲染用 Rich。
4 个填空:3 个纯函数 + 1 个 Typer 命令体。在每处 TODO 写实现,然后:

    uv run pytest 04_devops_scripts/ch25/test_ch25_assignment.py -v

全绿 = 你掌握了 Ch25。

每题顶部的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。

约定:logs 是 list[dict],每条形如:
    {"ip": "192.168.1.1", "method": "GET", "path": "/api/products", "status": 200}
"""
import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="访问日志分析 CLI:状态码分布 + Top IP。")
console = Console()


@app.callback()
def _main() -> None:
    """访问日志分析 CLI。callback 让 app 成为「命令组」,analyze 作为子命令。"""


# ========== §25.3 纯逻辑:summarize_status ==========


def summarize_status(logs: list[dict]) -> dict[int, int]:
    """
    【纯逻辑 · §25.3】统计状态码分布,返回 {状态码: 次数}。

    示例(2 个 200、1 个 500):
        summarize_status(logs) -> {200: 2, 500: 1}

    思路(collections.Counter,Ch08 学过;这里手写也行):
        from collections import Counter
        return dict(Counter(log["status"] for log in logs))
        - Counter 数 status;dict() 转回普通 dict(Counter 是 dict 子类)
    """
    # TODO: Counter 数 status(或手写循环),返回 dict
    ...


# ========== §25.3 纯逻辑:top_ips ==========


def top_ips(logs: list[dict], n: int = 5) -> list[tuple[str, int]]:
    """
    【纯逻辑 · §25.3】返回访问次数最多的前 n 个 IP,降序。
    每项是 (ip, 次数)。n 超过 IP 总数时返回全部。

    示例(1.1.1.1 访问 5 次、2.2.2.2 访问 3 次):
        top_ips(logs, n=2) -> [("1.1.1.1", 5), ("2.2.2.2", 3)]

    思路(Counter.most_common = Java stream sorted + limit):
        from collections import Counter
        return Counter(log["ip"] for log in logs).most_common(n)
        - most_common(n) 返回 [(key, count), ...] 降序,自带 top-N 语义
    """
    # TODO: Counter(ip).most_common(n)
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
            table.add_row(*row)        # *row 把 list 拆成多个参数
        return table
        - add_column 加表头;add_row 加一行(* 解包,Ch01 学过)
    """
    # TODO: Table(title=title) + add_column 循环 + add_row(*row) 循环
    ...


# ========== §25.5 Typer:analyze 命令 ==========


@app.command()
def analyze(
    path: Path = typer.Argument(..., help="日志 json 文件路径"),
    top: int = typer.Option(5, "--top", "-n", help="Top N 个 IP"),
    fmt: str = typer.Option("table", "--format", "-f", help="输出格式: table | json"),
) -> None:
    """
    【Typer · §25.5】分析日志文件:读 json → 算状态码分布 + Top IP → 输出。
    支持两种格式:table(Rich 表格)/ json(机器可读)。

    用法:
        uv run python -m typer ch25_assignment.py run analyze access.json --top 3
        # 或装好后:loganalyzer analyze access.json --top 3 --format json

    思路:
        logs = json.loads(Path(path).read_text(encoding="utf-8"))   # 读+解析
        status = summarize_status(logs)                              # §25.3
        ips = top_ips(logs, top)                                      # §25.3
        if fmt == "json":
            typer.echo(json.dumps({"status": status, "top_ips": ips}, ensure_ascii=False))
        else:
            rows = [[ip, str(cnt)] for ip, cnt in ips]
            console.print(make_table("Top IP", ["IP", "次数"], rows))  # §25.4
            typer.echo(f"状态码分布: {status}")
    """
    # TODO: 读 json → summarize_status + top_ips → 按 fmt 输出
    ...


# ---------------------------------------------------------------------
# 开发模式下直接跑(不是测试):
#     uv run python 04_devops_scripts/ch25/ch25_assignment.py --help
#     uv run python 04_devops_scripts/ch25/ch25_assignment.py analyze <file> --top 3
# ---------------------------------------------------------------------
if __name__ == "__main__":
    app()
