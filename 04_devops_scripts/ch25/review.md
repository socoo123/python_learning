# Ch25 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | Typer 对应 Java 什么?它怎么定义 CLI 参数? | = Picocli,但【类型注解驱动】不用注解。函数签名:name: str(无默认)= 位置参数;opt: bool=False = --opt 选项。同 FastAPI 作者 | ⬜ |
| 2 | typer.Argument 和 typer.Option 区别? | Argument(...)= 必填位置参数(... 表示无默认);Option(默认,"--name","-n")= 选项(带默认和长短名) | ⬜ |
| 3 | Typer 单命令折叠坑是什么?怎么解? | app 只注册一个命令时,命令名被当程序名,不作子命令。要子命令形式(如 app analyze ...):加空的 @app.callback() 让 app 成为命令组 | ⬜ |
| 4 | 为什么纯逻辑(summarize_status)和渲染(make_table)要分开? | 纯逻辑返回数据,好测、好复用;渲染有副作用(打印)难测。分开后 make_table 可渲染到 StringIO 测 | ⬜ |
| 5 | Rich Table 怎么用?为什么 add_row(*row)? | Table(title) → add_column 加表头 → add_row(*row) 加行。* 解包:list["1.1.1.1","5"] → 两个参数。构造完要 console.print(table) 才显示 | ⬜ |
| 6 | Counter.most_common(n) 等价 Java 什么? | stream.sorted(降序).limit(n)。自带 top-N 语义,返回 [(key,count),...]。summarize_status 用 Counter + dict() 转普通 dict | ⬜ |
| 7 | CLI 输出用 print 还是 typer.echo? | typer.echo。它处理管道/编码更稳,是 print 的 CLI 版。生产 CLI 用它 | ⬜ |
| 8 | CliRunner 怎么测 CLI? | runner.invoke(app, [参数列表]) 在进程内跑,不用起子进程。看 result.exit_code(0=成功,2=用法错)和 result.stdout | ⬜ |
| 9 | json.dumps({200:2}) 往返后键的类型? | 变字符串!JSON key 只能是 string。loads 回来是 {"200":2}。tuple 也会变 list。测试断言要按往返后形态写 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「Typer 类型注解驱动 + 单命令折叠坑」?
- [ ] 能说清「纯逻辑与渲染分离的好处」?
- [ ] 能说清「JSON 往返 key 变 str、tuple 变 list」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
