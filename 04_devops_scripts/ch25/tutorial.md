# Ch25 · CLI 工具开发:Typer + Rich

> **预计**:1 天 ｜ **前置**:Ch08(Counter)、Ch02(解包)、Ch07(类型注解)｜ **M4 第 3 章**
> **目标**:把脚本变成**漂亮的命令行工具**——`Typer` 用类型注解定义命令/参数/选项(= Java Picocli,FastAPI 同作者 Sebastián Ramírez),`Rich` 渲染彩色表格/面板/进度条。本章把 Ch08 的日志分析器改造成 `loganalyzer analyze access.json --top 3` 这种正经 CLI。

> 📐 **本教程的契约**:§25.3–§25.5 对应作业(3 个纯/渲染函数 + 1 个 Typer 命令体)。

---

## 🗺️ 本章地图

**作业 ↔ 教程对应表**:

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `summarize_status` | §25.3 | Counter 统计(复用 Ch08) |
| `top_ips` | §25.3 | Counter.most_common(top-N) |
| `make_table` | §25.4 | Rich Table: add_column / add_row(*解包) |
| `analyze` 命令 | §25.5 | Typer: Argument / Option / 子命令 |

---

## ⏱️ 学习路径:费曼五步(约 60 分钟)

① 预览猜 → ② 写 assignment(4 处填空)→ ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## ① 预览猜

1. Java 写命令行工具用 Picocli(`@Command`/`@Option` 注解)。Python 的 Typer 用什么「声明」参数?(提示:你一直在用)
2. 为什么本章要**把纯逻辑(summarize_status)和渲染(make_table)分开**?混在一起写会怎样?
3. `Rich` 的 `Table` 怎么用?为什么建议「构造」和「打印」分两步?
4. Typer 里「位置参数」和「选项」怎么区分声明?(`--top 3` vs 直接给文件名)
5. `table.add_row(*row)` 里的 `*` 是什么?(Ch01 学过)

---

## §25.1 Typer:类型注解驱动的 CLI 🟡

Typer 的核心理念和 FastAPI 一模一样——**类型注解驱动一切**。你写函数签名,Typer 自动生成 CLI。

```python
import typer

app = typer.Typer()

@app.command()
def greet(name: str, loud: bool = False):
    """打招呼。"""
    msg = f"HELLO {name.upper()}!" if loud else f"Hello, {name}"
    print(msg)

if __name__ == "__main__":
    app()
```

跑起来:
```bash
$ python greet.py John
Hello, John
$ python greet.py John --loud
HELLO JOHN!
$ python greet.py --help        # ← 自动生成!
```

Typer 看到 `name: str`(必填,无默认)→ 位置参数;`loud: bool = False`(有默认)→ `--loud` 开关。**你写的类型注解就是 CLI 的定义**。

> 🟡 **Java 对比**:= Picocli 的 `@Command` + `@Parameters` + `@Option`,但 Typer **不用注解**,直接读类型注解——更少样板。FastAPI 同作者,思路完全一致(请求参数 = CLI 参数)。

---

## §25.2 Argument / Option / 单命令坑(对应周边知识)🔴

Typer 区分两种参数,显式用 `typer.Argument` / `typer.Option` 声明:

```python
@app.command()
def analyze(
    path: Path = typer.Argument(..., help="日志文件路径"),      # 位置参数(...)
    top: int = typer.Option(5, "--top", "-n", help="Top N"),   # 选项(有默认)
    fmt: str = typer.Option("table", "--format", "-f"),
):
    ...
```

| 声明 | 含义 | 调用 |
|------|------|------|
| `typer.Argument(...)` | 必填位置参数(`...` 表示无默认) | `analyze access.json` |
| `typer.Option(5, "--top", "-n")` | 选项(默认 5,长/短名) | `analyze --top 3` 或 `-n 3` |
| `name: str`(裸) | 必填位置参数 | 同 Argument |

### ⚠️ 单命令坑(本章踩到过)🔴

Typer 有个**反直觉行为**:如果一个 `Typer()` app **只注册了一个命令**,它会把这个命令**折叠成根命令**——命令名变成程序名本身,**不再作为子命令**。

```python
app = typer.Typer()

@app.command()
def analyze(path): ...       # 唯一一个命令

# 调用:analyze 变成了程序名!
$ python app.py access.json          # ✅ 直接给 path
$ python app.py analyze access.json  # ❌ "analyze" 被当成 path 了!
```

**解法**:加一个空的 `@app.callback()`,强制 app 成为「命令组」,analyze 就是正经子命令:

```python
app = typer.Typer()

@app.callback()
def _main():
    """CLI。"""     # 空回调,只为让 app 成为命令组

@app.command()
def analyze(path): ...

# 现在:
$ python app.py analyze access.json   # ✅ 子命令形式(我们想要的)
```

> 🔴 **Python 特有**:这是 Typer 的设计取舍(单命令 CLI 不需要多余的前缀)。Java Picocli 没这问题(总有 `@Command`)。本项目代码里已加 callback,你不用管,知道原因即可。

---

## §25.3 纯逻辑:Counter 统计(对应:`summarize_status`、`top_ips`)🟢

**关键设计原则**:把「算数据」和「画表格」分开。纯逻辑函数只算 dict/list,好测、好复用;渲染交给 Rich。

```python
from collections import Counter

def summarize_status(logs: list[dict]) -> dict[int, int]:
    return dict(Counter(log["status"] for log in logs))

def top_ips(logs: list[dict], n: int = 5) -> list[tuple[str, int]]:
    return Counter(log["ip"] for log in logs).most_common(n)
```

- `Counter(genexpr)` 数频次(Ch08 学过)。
- `dict(Counter(...))` 转回普通 dict(Counter 是 dict 子类,转一下更「干净」)。
- `Counter.most_common(n)` 自带 top-N 语义,= Java `stream.sorted().limit(n).toList()`,但更简洁。

> ✅ 做 `summarize_status`:`dict(Counter(log["status"] for log in logs))`。
> 做 `top_ips`:`Counter(log["ip"] for log in logs).most_common(n)`。

---

## §25.4 Rich:构造表格(对应:`make_table`)🟡

`Rich` 让终端输出变漂亮(表格/颜色/进度条/Markdown)。核心是 `Table`:

```python
from rich.table import Table
from rich.console import Console

table = Table(title="Top IP")
table.add_column("IP")
table.add_column("次数")
table.add_row("1.1.1.1", "5")
table.add_row("2.2.2.2", "3")

console = Console()
console.print(table)       # 这一步才真正渲染(带边框、对齐)
```

输出(终端里是彩色框):
```
        Top IP        
┏━━━━━━━━━┳━━━━━━┓
┃ IP      ┃ 次数 ┃
┡━━━━━━━━━╇━━━━━━┩
│ 1.1.1.1 │ 5    │
│ 2.2.2.2 │ 3    │
└─────────┴──────┘
```

### 设计:构造与打印分离

`make_table` **只构造 Table 对象,不打印**。为什么?
- **好测**:测试里能把 Table 渲染到 `io.StringIO()` 检查内容,不必抓真终端。
- **好复用**:调用方能决定「打印到屏幕」还是「再加工」。
- **关注点分离**:数据结构 vs 副作用(打印)。

```python
def make_table(title: str, columns: list[str], rows: list[list[str]]) -> Table:
    table = Table(title=title)
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*row)        # * 解包:list → 多个参数(Ch01)
    return table
```

`add_row(*row)`:row 是 `["1.1.1.1", "5"]`,`*` 解包成 `add_row("1.1.1.1", "5")`。

> 🟡 **Java 对比**:Rich ≈ 没有直接等价(Java 终端美化库少且弱)。这是 Python 运维脚本「看着专业」的杀手锏。

> ✅ 做 `make_table`:`Table(title=title)` → 循环 `add_column` → 循环 `add_row(*row)` → `return table`。

---

## §25.5 串起来:analyze 命令(对应:`analyze` 命令体)🟡

把读文件 + 纯逻辑 + 渲染串成完整命令:

```python
@app.command()
def analyze(
    path: Path = typer.Argument(..., help="日志 json 文件路径"),
    top: int = typer.Option(5, "--top", "-n", help="Top N 个 IP"),
    fmt: str = typer.Option("table", "--format", "-f", help="table | json"),
) -> None:
    logs = json.loads(Path(path).read_text(encoding="utf-8"))   # 读 + 解析
    status = summarize_status(logs)                              # §25.3
    ips = top_ips(logs, top)                                     # §25.3
    if fmt == "json":
        typer.echo(json.dumps({"status": status, "top_ips": ips}, ensure_ascii=False))
    else:
        rows = [[ip, str(cnt)] for ip, cnt in ips]
        console.print(make_table("Top IP", ["IP", "次数"], rows))  # §25.4
        typer.echo(f"状态码分布: {status}")
```

- `typer.echo(...)` = `print` 的 CLI 版(处理编码/管道更稳,= Java `System.out.println` 但更智能)。
- `--format json` 输出机器可读(管道给别的命令);`--format table` 输出给人看。**一个工具两种输出**是 CLI 好习惯。

> ✅ 做 `analyze` 命令:读 json → summarize_status + top_ips → 按 fmt 分支输出。

---

## §25.6 测试 CLI:CliRunner(讲透不出题)

CLI 怎么测?`typer.testing.CliRunner`(基于 click 的 runner)在**进程内**跑命令,不用起子进程:

```python
from typer.testing import CliRunner
runner = CliRunner()

result = runner.invoke(app, ["analyze", "logs.json", "--format", "json"])
assert result.exit_code == 0          # 退出码
assert "1.1.1.1" in result.stdout     # 输出
```

- `result.exit_code`:0 成功,非 0 失败(2 = 用法错,如参数不对)。
- `result.stdout`:合并后的输出。
- **不用真起子进程**,快且能在 CI 跑。

> 🟡 **Java 对比**:= Picocli 的 `CommandLine.execute(...)` + picocli 测试,或用 `SystemLambda` 抓 System.out。Python 这套开箱即用。

⚠️ **JSON 往返坑**(测试里踩到):`json.dumps({200: 2})` 的 key 会变字符串 `"200"`(JSON 规范 key 只能是 string),`json.loads` 回来就是 `{"200": 2}`;tuple 也会变 list。测试断言要按往返后的形态写。

---

## §25.7 Java 老手常踩的坑 ⚠️

1. **Typer 单命令折叠**:只注册一个命令时,命令名被当程序名,不作为子命令。要子命令形式加 `@app.callback()`。
2. **混逻辑与渲染**:把 print 散在业务函数里,没法测。纯逻辑返回数据,渲染单独做。
3. **忘 `console.print`**:Rich 对象(Table/Panel)构造后**不会自动显示**,要 `console.print(table)` 才渲染。
4. **`add_row` 不解包**:`add_row(row)` 传一个 list 进去 → 一整行变成一个单元格。要 `add_row(*row)` 解包。
5. **CLI 输出用 print 不用 typer.echo**:`typer.echo` 处理管道/编码更稳,生产 CLI 用它。
6. **不给 `--help`**:Typer 自动生成 help,但你得在 `typer.Option(..., help="...")` 和函数 docstring 里写清楚,否则 help 是空的。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `summarize_status` | Counter 统计 | 🟢 |
| `top_ips` | Counter.most_common | 🟢 |
| `make_table` | Rich Table + * 解包 | 🟡 |
| `analyze` 命令 | Typer Argument/Option + 串起来 | 🟡 |

```bash
uv run pytest 04_devops_scripts/ch25/test_ch25_assignment.py -v
```

跑起来看效果(可选):
```bash
uv run python 04_devops_scripts/ch25/ch25_assignment.py --help
uv run python 04_devops_scripts/ch25/ch25_assignment.py analyze assets/mock_data/access_logs.json --top 3
uv run python 04_devops_scripts/ch25/ch25_assignment.py analyze assets/mock_data/access_logs.json --format json
```

全绿 = 掌握 Ch25。

---

## ✅ 自测

- [ ] 能说清 Typer 为什么是「类型注解驱动」(对比 Picocli)
- [ ] 知道 Typer 单命令折叠坑 + callback 解法
- [ ] 能说清为什么纯逻辑和渲染要分开
- [ ] 会用 Rich Table(add_column / add_row(*row)),知道要 console.print 才显示
- [ ] 4 个作业全绿

## 🎓 费曼挑战

1. 「Typer 单命令折叠是什么坑?怎么让 analyze 成为正经子命令?」— 重读 §25.2
2. 「为什么 make_table 只构造不打印?这对测试有什么好处?」— 重读 §25.4
3. 「`json.dumps({200:2})` 再 `json.loads` 回来,键的类型怎么变了?」— 重读 §25.6

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步:Ch26 定时任务与日志分析

CLI 会写了,接下来学「**让脚本定时跑 + 日志异常检测**」——`schedule` 库(进程内定时)+ 按分钟聚合日志找 5xx 突增。监控告警的核心。
