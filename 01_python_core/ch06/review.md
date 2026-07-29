# Ch06 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | `with` 语句做了什么?`__enter__`/`__exit__` 何时被调? | 自动管理资源。进入 with 调 `__enter__`(返回值给 as);退出 with 调 `__exit__`(无论是否异常,负责清理)。= Java try-with-resources / AutoCloseable | ⬜ |
| 2 | `try/except/else/finally` 的 `else` 何时执行?Java 为什么没有? | try【没抛异常】时执行(类似 for-else 的 nobreak)。把"成功后逻辑"挪出 try,避免误捕自己代码的异常。Java 的 try/catch 没有 else | ⬜ |
| 3 | `raise DataLoadError(...) from e` 的 `from e` 干嘛? | 把原始异常挂到新异常的 `__cause__`,保留完整异常链。= Java `throw new XxxException(msg, e)` 把 e 当 cause | ⬜ |
| 4 | `@contextmanager` 版用 yield 切几段?各对应什么? | 切三段:yield 之前=`__enter__`;yield 的值=as 拿到的对象;yield 之后(放 finally)=`__exit__`。with 块抛异常时在 yield 处复苏 | ⬜ |
| 5 | 自定义异常怎么写? | `class XxxError(Exception): pass`。继承 Exception 即可,不需要写构造器(message 直接传)。= Java `class XxxException extends Exception` | ⬜ |
| 6 | Python 有 Java 那种 checked exception 吗? | **没有**。所有异常都是非受检的,不强制 try/catch 或声明 throws。哲学:该抛就抛,调用方决定处理 | ⬜ |
| 7 | `__exit__` 返回 True 和 False 的区别? | 返回 True=**吞掉异常**(不向上抛);返回 False/None=让异常继续传播。99% 情况返回 False | ⬜ |

## 🎓 费曼自检(复习时口头说一遍)

- [ ] 能说清「with 做了什么、__enter__/__exit__ 何时调」?
- [ ] 能说清「@contextmanager 的 yield 三段对应 __enter__/值/__exit__」?
- [ ] 能说清「else 何时执行、为什么 Python 有而 Java 没有」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 复习日期到了,把这一行登记到根 [`REVIEW.md`](../../REVIEW.md) 的「复习日程」表。
