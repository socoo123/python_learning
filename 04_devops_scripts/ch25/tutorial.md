# Ch25 · CLI 工具开发:Typer + Rich

> **预计**:1 天 ｜ **前置**:Ch08(Counter)、Ch02(解包/推导式)、Ch07(类型注解)｜ **M4 第 3 章**
> **目标**:把脚本变成**漂亮的命令行工具**——`Typer` 用类型注解定义命令/参数/选项(= Java Picocli,FastAPI 同作者 Sebastián Ramírez),`Rich` 渲染彩色表格/面板/进度条。本章把 Ch08 的日志分析器改造成 `loganalyzer analyze access.json --top 3` 这种**正经 CLI**。

> 📐 **本教程的契约**:§25.3–§25.7 对应作业(4 个纯/渲染函数 + 2 个 Typer 命令体)。

---

## 🗺️ 本章地图

**作业 ↔ 教程对应表**:

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `summarize_status` | §25.3 | Counter 统计(复用 Ch08) |
| `top_ips` | §25.3 | Counter.most_common(top-N) |
| `error_logs` | §25.3 | 列表推导过滤(复用 Ch03) |
| `make_table` | §25.4 | Rich Table: add_column / add_row(*解包) |
| `make_summary_panel` | §25.5 | Rich Panel + 多组件组合 |
| `analyze` 命令 | §25.6 | Typer: Argument / Option / 串起纯逻辑+渲染 |
| `report` 命令 | §25.7 | 第 2 个子命令:复用所有函数做综合报告 |

---

## ⏱️ 学习路径:费曼五步(约 60 分钟)

① 预览猜 → ② 写 assignment(7 处填空)→ ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## ① 预览猜

1. Java 写命令行工具用 Picocli(`@Command`/`@Option` 注解)。Python 的 Typer 用什么「声明」参数?(提示:你一直在用)
2. 为什么本章要**把纯逻辑(summarize_status)和渲染(make_table)分开**?混在一起写会怎样?
3. `table.add_row(*row)` 里的 `*` 是什么?(Ch01 学过)如果写成 `add_row(row)` 会发生什么?
4. Typer 里「位置参数」和「选项」怎么区分声明?(`--top 3` vs 直接给文件名)
5. 为什么生产 CLI 用 `typer.echo` 而不是 `print`?

---

## §25.1 Typer:类型注解驱动的 CLI 🟡

Typer 的核心理念和 FastAPI 一模一样——**类型注解驱动一切**。你写函数签名,Typer 自动生成 CLI、解析参数、生成 `--help`。

**Java 对照最小例**(Picocli):

```java
@Command(name = "greet")
class Greet implements Runnable {
    @Parameters(index = "0") String name;          // 位置参数
    @Option(names = "--loud") boolean loud;         // 选项
    public void run() { System.out.println("Hello " + name); }
}
```

**Python(Typer)等价物**——不用注解,直接读类型注解:

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
$ python greet.py --help        # ← 自动生成,不用手写!
```

**Typer 的推断规则**(看签名就够了):

| 你写的 | Typer 推断为 | 调用方式 |
|--------|-------------|----------|
| `name: str`(无默认) | **必填位置参数** | `greet John` |
| `loud: bool = False`(有默认) | **`--loud` 开关** | `greet John --loud` |

> 🟡 **Java 对比**:= Picocli 的 `@Command` + `@Parameters` + `@Option`,但 Typer **零注解**,直接读类型注解——更少样板。FastAPI 同作者,思路完全一致(请求参数 = CLI 参数)。

---

## §25.2 Argument / Option / 单命令坑 🔴

Typer 区分两种参数,可显式用 `typer.Argument` / `typer.Option` 声明(加帮助文案、短名):

```python
from pathlib import Path

@app.command()
def analyze(
    path: Path = typer.Argument(..., help="日志文件路径"),      # 位置参数(...=无默认)
    top: int = typer.Option(5, "--top", "-n", help="Top N"),    # 选项(默认 5,长/短名)
    fmt: str = typer.Option("table", "--format", "-f"),
):
    ...
```

| 声明 | 含义 | 调用 |
|------|------|------|
| `typer.Argument(...)` | 必填位置参数(`...` 表示无默认) | `analyze access.json` |
| `typer.Option(5, "--top", "-n")` | 选项(默认 5,长名 `--top`/短名 `-n`) | `analyze --top 3` 或 `-n 3` |
| `name: str`(裸写) | 必填位置参数(同 Argument,但无 help) | 同 Argument |

### ⚠️ 单命令坑(本章踩到过)🔴

Typer 有个**反直觉行为**:如果一个 `Typer()` app **只注册了一个命令**,它会把这个命令**折叠成根命令**——命令名变成程序名本身,**不再作为子命令**。

```python
app = typer.Typer()

@app.command()
def analyze(path): ...       # 唯一一个命令

# 调用:analyze 被折叠了!
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

> 🔴 **Python 特有**:这是 Typer 的设计取舍(单命令 CLI 不需要多余前缀)。Java Picocli 没这问题(总有 `@Command`)。本章作业里有**两个**命令(`analyze` + `report`),所以天然是命令组,但知道单命令坑能帮你调试别人的脚本。

---

## §25.3 纯逻辑:Counter 统计与过滤(对应:`summarize_status`、`top_ips`、`error_logs`)🟢

**关键设计原则**:把「算数据」和「画表格」分开。纯逻辑函数只返回 dict/list,**好测、好复用**;渲染交给 Rich。

**真实场景例**(本章主线:运维分析 access_logs.json):

```python
from collections import Counter

# logs 是 list[dict],每条形如:
# {"ip": "192.168.1.1", "method": "GET", "path": "/api/products", "status": 200}

def summarize_status(logs: list[dict]) -> dict[int, int]:
    """状态码分布:{200: 13, 500: 3, ...}"""
    return dict(Counter(log["status"] for log in logs))

def top_ips(logs: list[dict], n: int = 5) -> list[tuple[str, int]]:
    """访问次数最多的前 n 个 IP:[("192.168.1.1", 5), ...]"""
    return Counter(log["ip"] for log in logs).most_common(n)

def error_logs(logs: list[dict], threshold: int = 500) -> list[dict]:
    """过滤出 status >= threshold 的日志(默认 5xx)。"""
    return [log for log in logs if log["status"] >= threshold]
```

- `Counter(genexpr)` 数频次(Ch08 学过)。
- `dict(Counter(...))` 转回普通 dict(Counter 是 dict 子类,转一下更「干净」,测试里 `type(x) is dict` 才过)。
- `Counter.most_common(n)` 自带 top-N 语义,= Java `stream.sorted(降序).limit(n).toList()`,但更简洁。
- `error_logs` 就是 Ch03 的**列表推导过滤**——Python 里过滤不需要 `stream().filter().collect()`,一行 `[x for x in xs if 条件]` 搞定。

> 🟢 **秒懂**:这三题都是 M1/M2 知识点的复用,没有新东西。重点是体会「**纯逻辑层**」的设计——它们不知道 Rich 的存在,也不打印任何东西。

---

## §25.4 Rich Table:构造表格(对应:`make_table`)🟡

`Rich` 让终端输出变漂亮(表格/颜色/进度条/Markdown)。核心是 `Table`——先**构造**,再 `console.print` 才渲染。

**真实场景例**(把 top_ips 的结果画成表格):

```python
from rich.table import Table
from rich.console import Console

table = Table(title="Top IP")
table.add_column("IP")
table.add_column("次数")
table.add_row("192.168.1.1", "5")      # 一行 = 多个字符串参数
table.add_row("10.0.0.5", "3")

console = Console()
console.print(table)       # ← 这一步才真正渲染(带边框、对齐、颜色)
```

输出(终端里是彩色框):

```
        Top IP
┏━━━━━━━━━━━━━┳━━━━━━┓
┃ IP          ┃ 次数 ┃
┡━━━━━━━━━━━━━╇━━━━━━┩
│ 192.168.1.1 │ 5    │
│ 10.0.0.5    │ 3    │
└─────────────┴──────┘
```

### ❌→✅ 易错对照:`add_row` 要解包

作业里 `rows` 是 `list[list[str]]`(每个内层 list 是一行)。直接传 list 会**把整行塞进一个单元格**:

```python
row = ["192.168.1.1", "5"]

table.add_row(row)     # ❌ 错:把 ["192.168.1.1","5"] 当成 1 个单元格 → 列数对不上
table.add_row(*row)    # ✅ 对:* 解包成 add_row("192.168.1.1", "5"),两列各归各位
```

`*row` 是 Ch01 的**星号解包**:`f(*[a, b])` ≡ `f(a, b)`。

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
        table.add_row(*row)        # * 解包:list → 多个参数
    return table                    # 返回对象,不 print
```

> 🟡 **Java 对比**:Rich ≈ 没有直接等价(Java 终端美化库少且弱)。这是 Python 运维脚本「看着专业」的杀手锏。

---

## §25.5 Rich Panel:面板与组件组合(对应:`make_summary_panel`)🟡

Rich 不止有 Table。`Panel` 能把任意内容装进一个带边框、标题的「卡片」里,常用来做摘要/告警横幅。

**真实场景例**(把状态码分布做成一个「摘要面板」):

```python
from rich.panel import Panel

status = {200: 13, 201: 2, 500: 3}
lines = [f"{code}: {cnt} 次" for code, cnt in sorted(status.items())]
body = "\n".join(lines)              # "200: 13 次\n201: 2 次\n500: 3 次"

panel = Panel(body, title="状态码摘要", border_style="green")
console.print(panel)
```

输出:

```
╭─ 状态码摘要 ─╮
│ 200: 13 次   │
│ 201: 2 次    │
│ 500: 3 次    │
╰──────────────╯
```

### Panel vs Table:什么时候用哪个

| 组件 | 适合 | 构造 |
|------|------|------|
| `Table` | **规整的行列数据**(Top N 列表) | `add_column` + `add_row` |
| `Panel` | **一段文字/摘要**(统计、告警横幅) | `Panel(文本, title=...)` |

`make_summary_panel` 和 `make_table` 一样**只构造不打印**——返回 `Panel` 对象,测试渲染到 StringIO 验证。

> ✅ 做 `make_summary_panel`:`"\n".join(f"{k}: {v} 次" ...)` → `Panel(body, title=title)` → `return`。

---

## §25.6 串起来:analyze 命令(对应:`analyze` 命令体)🟡

把「读文件 + 纯逻辑 + 渲染」串成完整命令。**一个工具两种输出**(给人看的 table / 给机器看的 json)是 CLI 好习惯:

```python
@app.command()
def analyze(
    path: Path = typer.Argument(..., help="日志 json 文件路径"),
    top: int = typer.Option(5, "--top", "-n", help="Top N 个 IP"),
    fmt: str = typer.Option("table", "--format", "-f", help="table | json"),
) -> None:
    logs = json.loads(Path(path).read_text(encoding="utf-8"))   # 读 + 解析
    status = summarize_status(logs)                              # §25.3 纯逻辑
    ips = top_ips(logs, top)                                     # §25.3 纯逻辑
    if fmt == "json":
        typer.echo(json.dumps({"status": status, "top_ips": ips}, ensure_ascii=False))
    else:
        rows = [[ip, str(cnt)] for ip, cnt in ips]               # tuple → list[str]
        console.print(make_table("Top IP", ["IP", "次数"], rows))  # §25.4 渲染
        typer.echo(f"状态码分布: {status}")
```

### ❌→✅ 易错对照:CLI 输出用 `typer.echo` 不用 `print`

```python
print(json.dumps(...))        # ❌ 管道/重定向时编码可能炸(Windows 尤其)
typer.echo(json.dumps(...))   # ✅ typer.echo 处理编码/管道/颜色剥离更稳
```

`typer.echo` = `print` 的 CLI 版,= Java `System.out.println` 但更智能。生产 CLI 用它。

> ✅ 做 `analyze` 命令:读 json → summarize_status + top_ips → 按 fmt 分支输出。**注意 json 分支里 dict/tuple 会自动序列化,table 分支要把 tuple 转成 list[str]**。

---

## §25.7 第 2 个子命令:report(对应:`report` 命令体)🔴

一个真实 CLI 通常有多个子命令(想想 `git commit` / `git push`)。`report` 命令复用前面**所有**函数,生成一份「完整巡检报告」——状态码面板 + Top IP 表格 + 错误日志表。

```python
@app.command()
def report(
    path: Path = typer.Argument(..., help="日志 json 文件路径"),
    top: int = typer.Option(5, "--top", "-n", help="Top N 个 IP"),
    threshold: int = typer.Option(500, "--threshold", "-t", help="错误状态码阈值"),
) -> None:
    logs = json.loads(Path(path).read_text(encoding="utf-8"))
    # ① 状态码摘要面板(§25.5)
    console.print(make_summary_panel(summarize_status(logs), title="状态码摘要"))
    # ② Top IP 表格(§25.4)
    ip_rows = [[ip, str(cnt)] for ip, cnt in top_ips(logs, top)]
    console.print(make_table("Top IP", ["IP", "次数"], ip_rows))
    # ③ 错误日志表格(§25.3 过滤 + §25.4 渲染)
    err_rows = [[l["ip"], l["path"], str(l["status"])] for l in error_logs(logs, threshold)]
    console.print(make_table("错误日志", ["IP", "路径", "状态码"], err_rows))
```

- 注册**第二个** `@app.command()` 后,app 自动成为命令组(两个子命令并存):
  ```bash
  $ loganalyzer analyze access.json --top 3      # 子命令 1
  $ loganalyzer report  access.json --threshold 500  # 子命令 2
  ```
- 体会**复用的威力**:`report` 一个纯逻辑都没新写,全是前面函数的组合——这正是「纯逻辑/渲染分离」的回报。

> ✅ 做 `report` 命令:依次 print 三个组件(panel + 两个 table),全部复用已有函数。

---

## §25.8 测试 CLI:CliRunner(讲透不出题)

CLI 怎么测?`typer.testing.CliRunner`(基于 click 的 runner)在**进程内**跑命令,不用起子进程:

```python
from typer.testing import CliRunner
runner = CliRunner()

result = runner.invoke(app, ["analyze", "logs.json", "--format", "json"])
assert result.exit_code == 0          # 退出码:0 成功,2 用法错
assert "192.168.1.1" in result.stdout # 输出
```

- `result.exit_code`:`0` 成功,非 0 失败(`2` = 用法错,如缺参数/文件不存在)。
- `result.stdout`:合并后的标准输出。
- **不用真起子进程**,快且能在 CI 跑。

> 🟡 **Java 对比**:≈ Picocli 的 `CommandLine.execute(...)` + 抓 System.out,但 Python 这套开箱即用、不用 mock 静态流。

⚠️ **JSON 往返坑**(测试里踩到):`json.dumps({200: 2})` 的 key 会变字符串 `"200"`(JSON 规范 key 只能是 string),`json.loads` 回来就是 `{"200": 2}`;tuple 也会变 list。**测试断言要按往返后的形态写**:

```python
payload = json.loads(result.stdout)
assert payload["status"] == {"200": 2}        # 不是 {200: 2},key 变 str 了
assert payload["top_ips"] == [["1.1.1.1", 2]] # 不是 [("1.1.1.1", 2)],tuple 变 list
```

---

## §25.9 Java 老手常踩的坑 ⚠️

1. **Typer 单命令折叠**:只注册一个命令时,命令名被当程序名,不作子命令。要子命令形式加 `@app.callback()`(或再注册一个命令)。
2. **混逻辑与渲染**:把 print 散在业务函数里,没法测。纯逻辑返回数据,渲染单独做。
3. **忘 `console.print`**:Rich 对象(Table/Panel)构造后**不会自动显示**,要 `console.print(table)` 才渲染。
4. **`add_row` 不解包**:`add_row(row)` 传一个 list → 整行变一个单元格,列数对不上。要 `add_row(*row)`。
5. **CLI 输出用 print 不用 typer.echo**:`typer.echo` 处理管道/编码更稳,生产 CLI 用它。
6. **不给 `--help` 文案**:Typer 自动生成 help,但你得在 `typer.Option(..., help="...")` 和函数 docstring 里写清楚,否则 help 是空的。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `summarize_status` | Counter 统计 | 🟢 |
| `top_ips` | Counter.most_common | 🟢 |
| `error_logs` | 列表推导过滤 | 🟢 |
| `make_table` | Rich Table + * 解包 | 🟡 |
| `make_summary_panel` | Rich Panel + 多组件 | 🟡 |
| `analyze` 命令 | Typer Argument/Option + 串起来 | 🟡 |
| `report` 命令 | 复用所有函数 + 第 2 子命令 | 🔴 |

```bash
uv run pytest 04_devops_scripts/ch25/test_ch25_assignment.py -v
```

跑起来看效果(可选):

```bash
uv run python 04_devops_scripts/ch25/ch25_assignment.py --help
uv run python 04_devops_scripts/ch25/ch25_assignment.py analyze assets/mock_data/access_logs.json --top 3
uv run python 04_devops_scripts/ch25/ch25_assignment.py analyze assets/mock_data/access_logs.json --format json
uv run python 04_devops_scripts/ch25/ch25_assignment.py report  assets/mock_data/access_logs.json --threshold 500
```

全绿 = 掌握 Ch25。

---

## ✅ 自测

- [ ] 能说清 Typer 为什么是「类型注解驱动」(对比 Picocli)
- [ ] 知道 Typer 单命令折叠坑 + callback 解法
- [ ] 能说清为什么纯逻辑和渲染要分开
- [ ] 会用 Rich Table(add_column / add_row(*row))和 Panel,知道要 console.print 才显示
- [ ] 能解释 `report` 为什么一行纯逻辑都不用新写
- [ ] 7 个作业全绿

## 🎓 费曼挑战

1. 「Typer 单命令折叠是什么坑?怎么让 analyze 成为正经子命令?」— 重读 §25.2
2. 「为什么 make_table 只构造不打印?这对测试有什么好处?」— 重读 §25.4
3. 「`json.dumps({200:2})` 再 `json.loads` 回来,键的类型怎么变了?」— 重读 §25.8
4. 「Table 和 Panel 分别适合展示什么数据?」— 重读 §25.5

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步:Ch26 定时任务与日志分析

CLI 会写了,接下来学「**让脚本定时跑 + 日志异常检测**」——`schedule` 库(进程内定时)+ 按分钟聚合日志找 5xx 突增。监控告警的核心。
