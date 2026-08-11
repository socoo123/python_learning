# Ch06 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | `with` 语句做了什么?`__enter__`/`__exit__` 何时被调? | 自动管理资源。进入 with 调 `__enter__`(返回值给 as);退出 with 调 `__exit__`(无论是否异常,负责清理)。= Java try-with-resources / AutoCloseable | ⬜ |
| 2 | `__exit__` 返回 True 和 False 的区别? | 返回 True=**吞掉异常**(不向上抛);返回 False/None=让异常继续传播。99% 情况返回 False | ⬜ |
| 3 | `try/except/else/finally` 的 `else` 何时执行?为什么要有它? | try【没抛异常】时执行。意义:把「成功后的逻辑」挪出 try 块,避免 try 块太大误捕自己代码的异常。Java 的 try/catch 没有 else | ⬜ |
| 4 | EAFP 和 LBYL 是什么?Python 推荐哪个? | EAFP=直接操作、出错再捕获(Python 推荐);LBYL=先检查再操作(Java 习惯)。EAFP 让代码表达「想做什么」而非「怕什么」,且检查项与真实逻辑不脱节 | ⬜ |
| 5 | `raise LogParseError(...) from e` 的 `from e` 干嘛?不用会怎样? | 把原始异常挂到新异常的 `__cause__`,保留完整异常链(= Java `throw new XxxException(msg, e)`)。不用则 `__cause__` 丢失,排查时看不到根源 | ⬜ |
| 6 | 自定义异常怎么写?要写构造器吗? | `class XxxError(Exception): pass`。继承 Exception 即可,不需要写构造器(message 直接传给 `Exception.__init__`,`str(e)` 可拿到) | ⬜ |
| 7 | Python 有 Java 那种 checked exception 吗? | **没有**。所有异常都非受检,不强制 try/catch、不用在签名声明。哲学:该抛就抛,调用方决定要不要处理 | ⬜ |
| 8 | 批量处理文件时,某一行解析失败怎么办?try 该放哪? | try 放 `for` **里面**,粒度是单行——坏行记下行号跳过,后面的好数据继续处理。❌ 把整个 for 包在一个 try 里,一行坏全批丢 | ⬜ |
| 9 | `@contextmanager` 版用 yield 切几段?各对应什么? | 三段:yield 之前=`__enter__`;yield 的值=as 拿到的对象;yield 之后(正常)=`__exit__` 成功路径。with 块抛异常时在 yield 处复苏,进 `except` 分支 | ⬜ |
| 10 | 用 `@contextmanager` 写事务(commit/rollback)的骨架? | `yield` 前初始化;`yield db` 后(正常)`committed.extend(pending)`;`except Exception` 设 `rolled_back=True` 并 `raise`;`finally` 清空 `pending` | ⬜ |
| 11 | 读 GB 级日志文件,为什么不能用 `read_text()`?该怎么读? | `read_text()` 一次全读进内存会 OOM。用 `with open() as f: for line in f:` 逐行惰性迭代,内存只占一行 | ⬜ |
| 12 | `open()` / `Path.open()` 写文件时,哪两个参数必须显式给? | `mode="w"`(覆盖,或 `"a"` 追加)和 `encoding="utf-8"`(Windows 默认 GBK,不写会乱码)。且必须用 `with` 保证关闭 | ⬜ |
| 13 | 为什么不能裸 `except:`?该写什么? | 裸 `except:` 会捕 `KeyboardInterrupt`/`SystemExit`(继承自 BaseException 而非 Exception)。至少写 `except Exception:` | ⬜ |

## 🎓 费曼自检(复习时口头说一遍)

- [ ] 能说清「with 做了什么、__enter__/__exit__ 何时调、返回 True 会怎样」?
- [ ] 能说清「@contextmanager 的 yield 三段对应什么、with 块抛异常时生成器里发生什么」?
- [ ] 能说清「else 何时执行、EAFP 为什么优于 LBYL」?
- [ ] 能徒手写出「读文件→逐行解析(坏行跳过)→聚合→写报告」的完整流程?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 复习日期到了,把这一行登记到根 [`REVIEW.md`](../../REVIEW.md) 的「复习日程」表。
