# Ch18 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | `async def f(): ...` 调用 `f()` 会立刻执行吗? | **不会**。返回【协程对象】,必须 `await`(async 上下文)或 `asyncio.run`(同步代码)才执行。否则「coroutine was never awaited」警告 | ⬜ |
| 2 | `async` 是多线程吗?和 Java 线程的本质差别? | **不是**,是【单线程协作式并发】。协程靠 `await` 主动让出;Java 线程是抢占式(OS/JVM 强制切)。纯 async 无 await 区段内共享变量不用锁,有 await 就要小心 | ⬜ |
| 3 | `await` 只能写在哪?在普通 `def` 里写会怎样? | 只能写在 `async def` 里;写在普通 `def` 是 **SyntaxError**。所以异步会「传染」整条调用链 | ⬜ |
| 4 | async 代码里模拟/等待 IO 该用什么?用 `time.sleep` 呢? | `await asyncio.sleep(n)`(等待期间让出线程)。`time.sleep` 死占线程 → 卡死整个事件循环,所有协程陪葬 | ⬜ |
| 5 | `asyncio.gather(a, b, c)` 做什么?结果顺序按什么?对应 Java? | 三个协程【同时启动】、等全部完成、按【传入顺序】返回结果列表(不是完成顺序)。总耗时 ≈ max(单个)。≈ Java `CompletableFuture.allOf(...)` | ⬜ |
| 6 | 为什么 `gather` 比串行 `await a; await b; await c` 快? | IO 等待【重叠】:a 的 await 让出线程期间,事件循环去启动并等 b、c,N 个 IO 并行计时。串行是等完一个再开始下一个,耗时相加。本章:3×50ms → 并发 50ms | ⬜ |
| 7 | 怎么并发跑「动态数量」的协程(如批量查 N 个商品)?空列表呢? | `await asyncio.gather(*[fetch(pid) for pid in ids])`——列表推导造协程 + `*` 解包。空列表不用特判,`gather()` 返回 `[]` | ⬜ |
| 8 | 批量接口里写 `for pid in ids: results.append(await fetch(pid))` 有什么问题? | 退回【串行】:每轮等 50ms,N 个就是 N×50ms。正确做法是先造全部协程再一次 gather(先全部启动,再统一等) | ⬜ |
| 9 | `asyncio.create_task(coro)` 和直接 `await coro` 的启动时机差别? | `create_task` 【立刻】排入事件循环后台跑,之后 `await task` 取结果;直接 `await` 要等执行到那行才开始。≈ Java `supplyAsync`(立即提交) | ⬜ |
| 10 | `create_task` 出来的 task 不 `await` 会怎样? | 结果拿不到,且函数返回后事件循环可能取消这个「孤儿任务」。每个 task 后面都要有人 await(或交给 gather) | ⬜ |
| 11 | FastAPI `def` 端点 vs `async def` 端点,何时用哪个? | `def`(调同步库/阻塞调用)→ FastAPI 丢【线程池】跑,不卡事件循环;`async def`(全程异步库)→ 不占线程池,吞吐高。**async 端点里绝不能调阻塞代码** | ⬜ |
| 12 | 为什么 `async def` 端点里调 `requests.get` 是严重错误,`def` 端点却没事? | async 端点跑在事件循环线程上,阻塞 = 所有请求陪葬;`def` 端点被丢线程池,阻塞只占池里一个线程 | ⬜ |
| 13 | CPU 密集任务该用 async 吗?为什么? | **不该**。CPU 计算不 await、不让出,gather 也只能串行算。CPU 密集用【多进程】`ProcessPoolExecutor` 或同步。async 只解决 IO 密集并发 | ⬜ |
| 14 | `asyncio.run(main())` 能在 FastAPI 端点里调吗? | **不能**——端点已在事件循环里,再调报错「cannot be called from a running event loop」。`asyncio.run` 只在普通同步代码(如测试)里用 | ⬜ |
| 15 | Python async vs Java 21 虚拟线程,本质差别? | 协作式 vs 抢占式:Python 协程靠显式 `await` 让出;虚拟线程由 JVM 在 IO 处自动挂起,写法仍是同步。Python 没有虚拟线程等价物 | ⬜ |
| 16 | 生产里 `fetch_price` 这类模拟函数怎么换成真调用? | 函数体把 `asyncio.sleep` 换成 `async with httpx.AsyncClient()` + `await client.get(...)`(§18.8);gather / 端点代码一行不用改 | ⬜ |

## 🎓 费曼自检

- [ ] 能讲清「为什么 `gather` 比串行 await 快」(IO 重叠 + 单线程交错)?
- [ ] 能讲清「为什么 async 端点里调 `requests` 会出事,而 `def` 端点没事」?
- [ ] 能讲清「Python async vs Java 21 虚拟线程」的协作式/抢占式差别?
- [ ] 能讲清「`gather(*列表)` 的结果顺序按什么排、空列表返回什么」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
