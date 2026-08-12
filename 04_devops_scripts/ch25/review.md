# Ch25 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | Typer 对应 Java 什么?它怎么定义 CLI 参数? | = Picocli,但【类型注解驱动】零注解。函数签名:`name: str`(无默认)= 位置参数;`opt: bool=False` = `--opt` 开关。同 FastAPI 作者 | ⬜ |
| 2 | `typer.Argument(...)` 和 `typer.Option(5,"--top","-n")` 区别? | Argument(...)= 必填位置参数(`...` 表示无默认);Option(默认,长名,短名)= 选项,可带默认值和长短名 | ⬜ |
| 3 | Typer「单命令折叠」坑是什么?怎么解? | app 只注册 1 个命令时,命令名被折叠成程序名,不作子命令。解法:加空 `@app.callback()`(或注册 ≥2 个命令)让 app 成命令组 | ⬜ |
| 4 | 为什么纯逻辑(summarize_status)和渲染(make_table)要分开? | 纯逻辑返回数据,好测、好复用;渲染有副作用(打印)难测。分开后 make_table 可渲染到 StringIO 测,report 能直接复用 | ⬜ |
| 5 | Rich Table 三步骤?为什么 `add_row(*row)` 不是 `add_row(row)`? | `Table(title)` → `add_column` 加表头 → `add_row(*row)`。`*` 解包:`["1.1.1.1","5"]` → 两个参数各进一列;不解包则整行塞进一个单元格 | ⬜ |
| 6 | Table 和 Panel 分别适合什么数据? | Table = 规整行列(Top N 列表),`add_column`/`add_row`;Panel = 一段文字/摘要(统计/告警横幅),`Panel(文本, title=...)`。两者都要 `console.print` 才显示 | ⬜ |
| 7 | 怎么构造一个 Panel(状态码摘要)? | `"\n".join(f"{k}: {v} 次" for k,v in sorted(d.items()))` 得到正文 → `Panel(body, title=...)`。只构造不打印,返回对象 | ⬜ |
| 8 | CLI 输出用 `print` 还是 `typer.echo`?为什么? | `typer.echo`。它处理编码/管道/颜色剥离更稳(Windows 尤其),是 print 的 CLI 版。生产 CLI 用它 | ⬜ |
| 9 | 为什么一个 CLI 要同时给 `--format table` 和 `--format json`? | table 给人看(Rich 美化),json 给机器/管道(jq、别的命令)。「一个工具两种输出」是 CLI 好习惯 | ⬜ |
| 10 | 怎么加第 2 个子命令?为什么 report 不用新写纯逻辑? | 再写一个 `@app.command()` 函数即可(自动成命令组)。report 全是复用 summarize_status/top_ips/error_logs/make_table/make_summary_panel 的组合 | ⬜ |
| 11 | CliRunner 怎么测 CLI? | `runner.invoke(app, [参数列表])` 进程内跑,不起子进程。看 `result.exit_code`(0 成功,2 用法错)和 `result.stdout` | ⬜ |
| 12 | `json.dumps({200:2})` 往返后键的类型? | 变字符串!JSON key 只能是 string,loads 回来是 `{"200":2}`;tuple 也变 list。测试断言按往返后形态写 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「Typer 类型注解驱动 + 单命令折叠坑 + callback 解法」?
- [ ] 能说清「纯逻辑与渲染分离」如何让 report 零新逻辑?
- [ ] 能说清「`add_row` 为什么要 `*row` 解包」?
- [ ] 能说清「JSON 往返 key 变 str、tuple 变 list」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
