# Ch18 · 异步编程 async/await

> **预计**:1 天 ｜ **前置**:Ch13(httpx 同步客户端)、Ch16(Depends)、Ch17(中间件里见过 `await call_next`)
> **目标**:吃透 Python 的 `async/await`——**单线程协作式并发**。能用 `asyncio.gather` 把多个 IO 任务并发跑(比串行快),写出 FastAPI 异步路由,并知道**何时该用同步、何时该用异步**。

> 📐 **本教程的契约**:讲过的才考,考的必讲过。作业四处填空(`fetch_user` / `fetch_orders` / `aggregate` / `profile`)分别对应 §18.2 / §18.2 / §18.3 / §18.6。`asyncio.create_task` 在 §18.5 讲,测试里有覆盖。

---

## 🗺️ 本章地图

**作业 ↔ 教程对应表**:

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `fetch_user`(①) | §18.2 | `async def` + `await asyncio.sleep` 模拟 IO |
| `fetch_orders`(②) | §18.2 | 同上,返回 list |
| `aggregate`(③ 重点) | §18.3 | `asyncio.gather(...)` 并发,总耗时 ≈ max 而非相加 |
| `profile`(④) | §18.6 | FastAPI `async def` 端点 + `await` |

**辅助代码**(不用填,读它理解):
- `aggregate_serial`(§18.4):串行 `await` 两次的对照版,用来在测试里**证明 gather 更快**。
- 测试里 `asyncio.create_task`(§18.5):另一种并发调度方式。

---

## ⏱️ 费曼五步路径(约 60-90 分钟)

| 步 | 动作 | 产出 |
|----|------|------|
| ① 预览猜 | 回答下面的「Java 直觉」问题,先不翻答案 | 脑里的猜测 |
| ② 先动手 | 直接去 `ch18_assignment.py` 填四处(签名 + docstring 已给) | 你的实现 |
| ③ pytest 红绿 | `uv run pytest 03_web_framework/ch18/ -v`,红→查对应 §→改→绿 | 13 个全绿 |
| ④ 费曼 | 合上教程,对着 `test_gather_faster_than_serial` 解释「为什么并发快」 | 你能讲清 |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的 7 张卡过一遍 | 勾选掌握 |

---

## ① 预览猜(先想,再往下看)

> 用你 15 年 Java 的直觉猜,不求对,求「有立场」。

1. Java 里你要并发调两个 HTTP 接口,会用 `CompletableFuture` / `CompletionStage` / 线程池。Python 的 `async` 是**多开线程**吗?
2. `async def f(): ...` 调一下 `f()`——它**立刻执行**并返回结果吗?还是返回一个「能执行的东西」?
3. Spring 控制器方法里 `Thread.sleep(100)` 会阻塞 Tomcat 的请求线程。FastAPI 端点里 `await asyncio.sleep(0.1)` 会阻塞整个进程吗?
4. 同一个协程,`await a(); await b()`(串行)和 `await asyncio.gather(a(), b())`(并发),哪个快?为什么?
5. 一个 CPU 密集任务(算圆周率、压缩大文件),放进 `async def` 里跑会怎样?能提升并发吗?

(带着猜测往下读,看对了几条。)

---

## §18.1 为什么需要异步:IO 是瓶颈,线程是奢侈品 🟢

一个 Web 后端 90% 的时间在**等 IO**:等数据库、等下游 HTTP、等 Redis。等待期间 CPU 是闲的。

Java 的解法:**线程池**。Tomcat 默认 200 个线程,一个请求占一个线程,等 IO 时这个线程**整个阻塞**着(干等)。想扛更多并发?加线程。但线程是操作系统资源,开几千个就开始扛不住(每个线程栈 1MB、上下文切换贵)。Java 21 的**虚拟线程**正是为了解决「线程太贵」。

**异步的解法**:**一个线程,同时等很多个 IO**。等 IO 时不占着线程,让线程去服务别的请求;IO 回来了再**回来继续**。这样 1 个线程能撑住上万并发连接。

> 🟢 **关键认知**:`async` 不是「多线程并发」,而是「**单线程 + IO 期间不让线程干等**」。它解决的是 **IO 密集**场景的并发,**不是** CPU 密集场景。

**一张图说清串行 vs 并发**(本作业的模型):

```
串行(await a; await b):    总耗时 = a + b
  线程 |--等a--|--等b--|

并发(gather(a, b)):       总耗时 = max(a, b)
  线程 |--同时等 a 和 b--|   ← 同一个线程,在 a 的 IO 等待期去启动 b
```

> 本作业里 `a`、`b` 各 0.05s,串行 ≈ 0.1s,并发 ≈ 0.05s。测试会断言这个差距。

---

## §18.2 async def + await:协程的基础(对应:`fetch_user` / `fetch_orders`)🔴

### 定义:async def 返回的是「协程」,不是结果

```python
import asyncio

async def fetch_user(uid: int) -> dict:        # async def = 定义协程函数
    await asyncio.sleep(0.05)                   # await = 等一个异步操作(这里模拟 IO)
    return {"id": uid, "name": f"用户{uid}"}

# 关键:调用协程函数,得到的不是结果,而是【协程对象】
coro = fetch_user(7)
# coro 现在还没执行!它是个「待跑的任务」
result = asyncio.run(coro)     # 这才真正跑,拿到 {"id": 7, ...}
```

**两个最易踩的点**(Java 老手几乎必踩):

1. **`async def` 的函数,直接调用不会执行**。`fetch_user(7)` 只给你一个协程对象,你必须 `await` 它(在 async 上下文里)或 `asyncio.run` 它(在普通同步代码里)。否则啥也没发生,还会报警告「coroutine was never awaited」。
2. **`await` 只能写在 `async def` 里**。在普通函数里写 `await` 是语法错误。

> 🟡 **Java 对比**:协程函数调用 ≠ 执行,这点像 Java 的 `Supplier`/`CompletionStage`——你拿到的是「未执行的计算」,要 `.get()` / `.thenApply` 才推进。但 Python 更直接:`f()` 给协程,`await coro` 推进。

### await 的语义:让出事件循环

`await x` 做两件事:
- 等 `x` 这个异步操作完成;
- 在等待期间,**把控制权交还给事件循环**(event loop),让循环去跑别的协程。

`asyncio.sleep(n)` 是「异步版的 `time.sleep`」——它在等待的 n 秒里**不阻塞线程**,而是让出去;`time.sleep(n)` 会**死占**线程 n 秒(async 代码里绝对别用)。

> 🤔 **为什么这么设计**:整个异步模型建立在「大家都很自觉、遇到等待就让出」上,这叫**协作式**(cooperative)调度。谁阻塞不让出(比如写了 `time.sleep` 或同步 HTTP 调用),整个事件循环就被卡死,所有协程都跟着卡。这点和 Java 线程的**抢占式**(preemptive,OS 强制切换)截然不同。

> ✅ 做 `fetch_user` / `fetch_orders`:`await asyncio.sleep(IO_DELAY)` 模拟 IO → `return` 结果。

---

## §18.3 asyncio.gather:并发(对应:`aggregate` —— 本章重点)🔴

`aggregate` 要「同时」取用户和订单。串行写法:

```python
async def aggregate_serial(uid):
    user   = await fetch_user(uid)      # 先等用户取完
    orders = await fetch_orders(uid)    # 再开始取订单 —— 总耗时 ≈ 相加
    return {"user": user, "orders": orders}
```

`gather` 把多个协程**同时**启动,等它们都完成,按顺序返回结果列表:

```python
async def aggregate(uid):
    user, orders = await asyncio.gather(     # 同时启动两个
        fetch_user(uid),
        fetch_orders(uid),
    )
    return {"user": user, "orders": orders}  # 总耗时 ≈ max(单个)
```

`gather` 干的事:
- 把传入的协程**立刻排进**事件循环(它们开始并发跑);
- 自己 `await` 直到**全部**完成;
- 返回**结果列表**(顺序 = 你传的顺序),所以可以用 `user, orders = ...` 解包。

> 🤯 **Java 对比**:`asyncio.gather(a, b)` ≈ `CompletableFuture.allOf(fa, fb).thenApply(...)`——并发跑多个、等全部完成。区别:Python 是**单线程**跑这两个(在 IO 等待期交错),CompletableFuture 默认跑在 ForkJoinPool(真线程)。结果上都是「并发 + 等全部 + 按序返回」。

> ⚠️ **结果顺序 = 传入顺序**,不是完成顺序。`gather(fast(), slow())` 返回 `[fast结果, slow结果]`,即使 slow 先启动后完成。

> ✅ 做 `aggregate` 题:`await asyncio.gather(fetch_user(uid), fetch_orders(uid))` → 解包成 `user, orders` → `return {"user":..., "orders":...}`。

---

## §18.4 串行 vs 并发:为什么 gather 省(对应:`aggregate_serial`)🟡

本作业保留了一个 `aggregate_serial` 对照版,测试里**计时断言**证明 gather 更快:

```python
# 两个任务各 0.05s
串行  ≈ 0.10s    (await a; await b)
并发  ≈ 0.05s    (await gather(a, b))
```

**省在哪?** 省在「等 a 的 IO 期间,线程去启动并等 b」。a 的 `asyncio.sleep` 让出线程 → 循环发现 b 没跑就跑 b → b 也 sleep 让出 → 两个 sleep 并行计时 → 谁先到先回来。整个过程**一个线程**搞定。

> 🟡 **这是 async 的全部价值**:把 IO 等待时间重叠起来。如果 a、b 都是 CPU 计算(没有 await 让出),gather **不会**让它们并发——还是一个算完再算另一个(因为单线程)。

**`aggregate_serial` 不用你填**,它是「反面教材」+ 测试对照。读懂即可:它的两行 `await` 是顺序的,中间没有重叠。

---

## §18.5 asyncio.create_task:手动调度(测试里有覆盖)🟡

`gather` 之外,另一种让协程「立刻开跑」的方式是 `create_task`:

```python
async def main():
    task = asyncio.create_task(fetch_user(6))   # 立刻排入循环,开始跑
    # ... 这里可以干别的事,task 在后台并发跑 ...
    return await task                            # 要结果时再 await
```

`create_task` vs 直接 `await` 协程:

| 写法 | 何时开始跑 |
|------|-----------|
| `await fetch_user(6)` | **等到这行才**开始跑 |
| `task = asyncio.create_task(fetch_user(6))` | **立刻**开始跑(后台),之后 `await task` 取结果 |

`gather` 内部其实就是「把协程包成 task 再等」。日常并发多个任务,**优先用 `gather`**(简洁);需要「先启动、稍后再等」的精细控制,才用 `create_task`。

> 🟡 **Java 对比**:`create_task` ≈ `CompletableFuture.supplyAsync(...)`(提交到池,立刻开始)。直接 `await` 协程则像同步调用。

---

## §18.6 FastAPI 异步路由(对应:`profile`)🔴

FastAPI 端点可以是 `def`(同步)或 `async def`(异步):

```python
@app.get("/profile/{uid}")
async def profile(uid: int):
    return await aggregate(uid)        # 端点体里 await IO
```

**为什么用 async 端点**:端点体内一旦 `await`(等 DB、等下游 API),事件循环就在等待期间**去处理别的请求**。单进程能扛的并发连接数大幅提升。这是 async Web 框架(FastAPI / Starlette / aiohttp)的核心卖点。

**关键纪律**:**async 端点里绝对不能调阻塞的同步代码**。一旦阻塞,整个事件循环(及其上所有请求)卡死。

> 🟡 **Java 对比**:Tomcat 是「一个请求一个线程」,同步阻塞没问题(只卡自己那个线程)。FastAPI 是「一个线程跑所有请求」,谁的代码阻塞,全员陪葬。这就是 async 的代价——**要求整个调用链都是异步的**(叫「async 全家桶」,DB 驱动要用 asyncpg、HTTP 用 httpx.AsyncClient)。

> ✅ 做 `profile` 题:`return await aggregate(uid)`。一行。

---

## §18.7 同步 vs 异步:何时用哪个(关键取舍)🟡

**FastAPI 对同步端点 `def` 的处理**(Ch16 的端点都是 `def`):它会把同步端点**丢到一个线程池**里跑(`run_in_threadpool`),这样它阻塞只占线程池的一个线程,不会卡事件循环。所以:

| 端点类型 | 适合的场景 | 阻塞时的代价 |
|---------|-----------|--------------|
| `def`(同步) | 调**同步**库(如 SQLAlchemy 同步 session、`requests`)、CPU 密集 | 占线程池一个线程,但**不卡事件循环** |
| `async def`(异步) | 调**异步**库(httpx.AsyncClient、asyncpg),全程不阻塞 | 不占线程池,吞吐高 |

**取舍口诀**:
- 你的代码里**有阻塞的同步调用**(`requests.get`、同步 DB、`time.sleep`)→ **别用 async**,用普通 `def`,让 FastAPI 丢线程池。
- 你的代码**全程异步**(await httpx、await asyncpg)→ 用 `async def`,享受高并发。
- **千万别**在 `async def` 里混用阻塞同步代码——这是性能杀手。

> 🤯 **Java 对比**:这就像 Spring WebFlux(全程 Reactor/异步,不能调阻塞 JDBC)vs Spring MVC(一请求一线程,同步 JDBC 没事)。FastAPI 同时支持两种,你按端点选。**Java 21 虚拟线程**让「同步写法 + 高并发」成为可能(虚拟线程等 IO 时不占平台线程),某种程度上是「同步写法的 async」——但 Python 目前没有等价物,Python 的 async 就是显式 `async/await`。

---

## §18.8 httpx.AsyncClient:异步 HTTP(Ch13 的 httpx 是同步版)🟢

Ch13 用 `httpx.get(...)`(同步)。异步版用 `AsyncClient`:

```python
import httpx

async def call_downstream():
    async with httpx.AsyncClient() as client:      # 异步上下文管理
        resp = await client.get("https://api.example.com/users/1")
        return resp.json()
```

`AsyncClient` 的 API 和同步 `Client` 几乎一样,只是方法是 `async`、要 `await`。本作业用 `asyncio.sleep` 模拟 IO,没真发请求,但**生产里**取用户/取订单就是用 `AsyncClient` 调下游。

> 🟢 **Java 对比**:同步 httpx ≈ `HttpClient`(Java 11)/ RestTemplate;AsyncClient ≈ 异步 `HttpClient.sendAsync` 或 WebClient。

---

## §18.9 Java 老手常踩的坑 ⚠️

1. **调用协程不 await**:`fetch_user(7)` 得到协程对象,**不执行**。必须 `await` 或 `asyncio.run`。否则「coroutine was never awaited」警告 + 啥也没干。
2. **`await` 写在普通 `def` 里**:语法错误。`await` 只能在 `async def` 里。
3. **async 代码里用 `time.sleep` / `requests.get`**:阻塞线程 → 卡死整个事件循环。要用 `asyncio.sleep` / `httpx.AsyncClient`。
4. **`asyncio.run` 在已经有事件循环时再调**:报错「asyncio.run() cannot be called from a running event loop」。在 FastAPI 端点里(已经在循环里)不能再 `asyncio.run`,要直接 `await`。`asyncio.run` 只在**普通同步测试代码**里用。
5. **把 CPU 密集任务塞进 async**:以为加个 `async` 就并发了——并没有。CPU 计算不 `await`,不会让出,一个算完才下一个。CPU 密集要用**多进程**(`ProcessPoolExecutor`)或干脆同步,不是 async。
6. **同步/异步混用**:端点是 `async def`,里面却调了同步阻塞的 DB 驱动——直接卡住。要么换异步驱动,要么端点改回 `def`。
7. **以为 `async` = 多线程**:不是。全程单线程。共享变量不需要锁(在纯 async、无 `await` 中断的区段内)。一旦 `await`,可能被切走,共享状态就要小心。

---

## §18.10 速查:Python async ↔ Java 并发对照

| Python async | Java 对应 | 说明 |
|--------------|-----------|------|
| `async def` | `CompletableFuture.supplyAsync` | 定义异步计算(协程) |
| `await coro` | `future.get()` / `.join()` | 等结果(等期间让出) |
| `asyncio.gather(a,b)` | `CompletableFuture.allOf(fa,fb)` | 并发跑多个、等全部 |
| `asyncio.create_task(c)` | `CompletableFuture.supplyAsync`(立即提交) | 立刻调度,后台跑 |
| `asyncio.run(main)` | (Java 无等价:Java 进程自带线程) | 同步代码里启动事件循环跑一个协程 |
| 事件循环(event loop) | (线程池/调度器) | 单线程调度协程 |
| 单线程协作式 | Java 虚拟线程(抢占式,JVM 调度) | 谁让出 / 谁被切走的差别 |
| `asyncio.sleep`(不阻塞) | `Thread.sleep`(阻塞)/ `CompletableFuture.delayedExecutor` | 等待 vs 阻塞等待 |

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `fetch_user`(①) | async def + await asyncio.sleep | 🟡 |
| `fetch_orders`(②) | 同上,返回 list | 🟡 |
| `aggregate`(③) | **asyncio.gather 并发**(重点) | 🟡 |
| `profile`(④) | FastAPI async 端点 | 🟢 |

```bash
uv run pytest 03_web_framework/ch18/test_ch18_assignment.py -v
```

期望:13 个全绿。其中 `test_gather_faster_than_serial` 会**计时断言**——并发版 < `0.075s`,串行版 > `0.075s`(阈值取两个 IO_DELAY 的中点),用宽松阈值保证 CI 不抖动。

---

## ✅ 自测清单

- [ ] 能说清「`async` 不是多线程,是单线程协作式并发」
- [ ] 知道调用 `async def` 函数得到的是**协程对象**,必须 `await` 或 `asyncio.run` 才执行
- [ ] 能用 `asyncio.gather` 并发跑多个协程,知道结果顺序 = 传入顺序
- [ ] 能解释为什么 `gather(a, b)` 比 `await a; await b` 快(IO 重叠)
- [ ] 知道 async 代码里不能用 `time.sleep` / `requests`(要用 asyncio 版)
- [ ] 知道 FastAPI `def` 端点会被丢线程池、`async def` 端点不能阻塞
- [ ] 知道 CPU 密集任务不该用 async
- [ ] 13 个测试全绿

---

## 🎓 费曼挑战(合上教程讲清「为什么」)

1. **「为什么 `gather(fetch_user, fetch_orders)` 比 `await fetch_user; await fetch_orders` 快?同一个线程怎么可能同时干两件事?」**
   — 卡壳重读 §18.1 的图 + §18.4。(关键词:IO 等待重叠、await 让出、事件循环交错)

2. **「为什么在 `async def` 端点里调 `requests.get`(同步 HTTP)是个严重错误?FastAPI 的 `def` 端点调 `requests` 却没事?」**
   — 卡壳重读 §18.6 + §18.7。(关键词:事件循环被卡死 vs 丢线程池)

3. **「Python 的 async 和 Java 21 虚拟线程,都能用同步/异步写法扛高并发,本质差别是什么?」**
   — 卡壳重读 §18.7。(关键词:协作式 vs 抢占式、显式 await vs JVM 自动挂起)

---

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步

Ch18 学完,你掌握了 FastAPI 的**异步能力**:并发 IO、async 端点、何时用同步何时用异步。

下一批 **Ch19–22**(你说一声我就写):
- **Ch19** SQLAlchemy 数据库 ORM(接真 DB,告别内存存储;同步 session 用 `def` 端点 + 线程池)
- **Ch20** 测试 API(TestClient 进阶 + fixtures + 覆盖率)
- **Ch21** JWT 认证授权
- **Ch22** 部署(uvicorn/gunicorn/Docker)+ 异步部署取舍

> 提示:Ch19 接真 DB 时,你会再次面对「同步 SQLAlchemy session 配 `def` 端点」还是「异步 SQLAlchemy(asyncpg)配 `async def` 端点」的取舍——本章 §18.7 的结论直接用。
