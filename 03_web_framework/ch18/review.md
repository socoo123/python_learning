# Ch18 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | `async def f(): ...` 调用 `f()` 会立刻执行吗? | **不会**。返回【协程对象】(coroutine),必须 `await`(async 上下文)或 `asyncio.run`(同步代码)才执行。否则「coroutine was never awaited」警告 | ⬜ |
| 2 | `async` 是多线程吗?和 Java 线程的本质差别? | **不是**,是【单线程协作式并发】。协程靠 `await` 主动让出;Java 线程是抢占式(OS/JVM 强制切)。共享状态:纯 async 无 await 区段内不用锁,有 await 就要小心 | ⬜ |
| 3 | `asyncio.gather(a, b)` 做什么?对应 Java? | 并发启动 a、b,等全部完成,按【传入顺序】返回结果列表。总耗时 ≈ max(单个)。≈ Java `CompletableFuture.allOf(fa, fb)` | ⬜ |
| 4 | 为什么 `gather` 比串行 `await a; await b` 快? | IO 等待【重叠】:a 的 `await`(让出)期间,事件循环去启动并等 b。两个 IO 并行计时。串行是等完 a 再开始 b,耗时相加 | ⬜ |
| 5 | async 代码里能用 `time.sleep` / `requests.get` 吗? | **绝对不行**。它们阻塞线程 → 卡死整个事件循环(所有协程陪葬)。要用 `asyncio.sleep` / `httpx.AsyncClient` | ⬜ |
| 6 | FastAPI `def` 端点 vs `async def` 端点,何时用哪个? | `def`(同步库/阻塞调用)→ FastAPI 丢【线程池】跑,不卡事件循环;`async def`(全程异步库)→ 不占线程池,吞吐高。**async 端点里绝不能阻塞** | ⬜ |
| 7 | CPU 密集任务该用 async 吗?为什么? | **不该**。CPU 计算不 `await`、不让出,gather 也只能串行算。CPU 密集用【多进程】`ProcessPoolExecutor` 或同步。async 只解决 IO 密集并发 | ⬜ |

## 🎓 费曼自检

- [ ] 能讲清「为什么 `gather` 比串行 await 快」(IO 重叠 + 单线程交错)?
- [ ] 能讲清「为什么 async 端点里调 `requests` 会出事,而 `def` 端点没事」?
- [ ] 能讲清「Python async vs Java 21 虚拟线程」的协作式/抢占式差别?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
