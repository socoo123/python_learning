# Ch18 · 异步编程 async/await

> **预计**:1 天 ｜ **前置**:Ch13(httpx 同步客户端)、Ch16(Depends)、Ch17(中间件里见过 `await call_next`)｜ **M3 第六章 · 重点**
> **目标**:吃透 Python 的 `async/await`——**单线程协作式并发**。能用 `asyncio.gather` 把多个 IO 调用并发跑(总耗时 ≈ max 而非相加),写出 FastAPI 异步端点,并讲清**何时用同步、何时用异步**。
> 本章主线:你是「极客商城」后端。商品详情页要同时展示「基本信息 + 价格 + 库存」,数据分别在 3 个下游微服务里,每次调用耗时 50ms。产品经理来投诉:串行调用让详情页接口 P99 超过 150ms。你的任务:用 `asyncio.gather` 把三次调用并发起来,把接口压回 50ms 级,并把它包装成一个 FastAPI 异步端点。

> 📐 **本教程的契约**:讲过的才考,考的必讲过。§18.2 对应三个「模拟下游」函数,§18.3 对应本章重点 `aggregate_product_info` 与批量版 `fetch_products_batch`,§18.5 对应 `aggregate_with_tasks`,§18.6 对应 FastAPI 端点。卡住时按对应表回查小节。

---

## 🗺️ 本章地图(元学习 · 原则一)

读完这章 + 完成作业,你将能够:
- 说清 `async` **不是多线程**,而是「单线程 + IO 等待期间不让线程干等」的协作式并发
- 知道调用 `async def` 函数得到的是**协程对象**,必须 `await` 或 `asyncio.run` 才真正执行
- 用 `asyncio.gather` 并发跑多个协程:结果顺序 = 传入顺序,总耗时 ≈ max(单个)
- 用 `asyncio.gather(*[...])` 并发跑**动态数量**的协程列表(批量场景)
- 用 `asyncio.create_task` 实现「先启动、稍后再等结果」
- 写 FastAPI `async def` 端点,并说清为什么端点里**绝不能调阻塞代码**
- 按「同步库 → `def` 端点 / 异步库 → `async def` 端点」做取舍;CPU 密集任务不用 async

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业题 | 对应小节 | 核心知识点 |
|--------|----------|-----------|
| `fetch_product` | §18.2 | `async def` + `await asyncio.sleep` 模拟下游 IO |
| `fetch_price` | §18.2 | 同上,返回价格 dict |
| `fetch_stock` | §18.2 | 同上,返回库存 dict |
| `aggregate_product_info` | §18.3 | **`asyncio.gather` 并发 3 个下游调用**(本章重点) |
| `fetch_products_batch` | §18.3 | `gather(*列表)` 并发动态数量 + 结果保序 |
| `aggregate_with_tasks` | §18.5 | `asyncio.create_task` 先启动、后等待 |
| `get_product_aggregate` | §18.6 | FastAPI `async def` 端点 + LookupError → 404 |

**脚手架**(不用填,读它理解):`aggregate_serial`(§18.4 的串行对照版,测试用它**证明 gather 更快**)、`health`(健康检查端点)。

---

## ⏱️ 学习路径:费曼五步(约 60-90 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 下面 5 个 Java 并发直觉题,猜 Python 怎么答 | 本页 ① |
| ② 先动手 | 打开 `ch18_assignment.py`,**先试着写**(别通读) | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清「为什么并发比串行快、为什么端点里不能阻塞」 | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性原则**:别通读!先猜 ① → 去 ② 写作业 → **哪题卡了,回对应 § 查** → 改 → 再跑。
> 本章作业形态:`填 async 函数体 + 填端点函数体`。纯异步函数用 `asyncio.run(...)` 在同步测试里驱动;端点用 `TestClient` 发真 HTTP 语义请求。

---

## ① 预览猜(2 分钟 · 激活你的 Java 直觉)

先别看答案,凭 15 年 Java 经验猜:
1. Java 里并发调两个 HTTP 接口,你会用 `CompletableFuture` / 线程池。Python 的 `async` 是**多开线程**吗?
2. `async def f(): ...` 调一下 `f()`——它**立刻执行**并返回结果吗?还是返回一个「能执行的东西」?
3. Spring 控制器里 `Thread.sleep(100)` 只阻塞当前请求线程。FastAPI 端点里 `await asyncio.sleep(0.1)` 会阻塞整个进程吗?
4. 同一个协程里,`await a(); await b()`(串行)和 `await asyncio.gather(a(), b())`(并发),哪个快?为什么?
5. 一个 CPU 密集任务(压缩大文件),放进 `async def` 里跑能提升并发吗?

> 猜完带着验证心态进正文。第 2 题的「**协程对象 ≠ 结果**」和第 4 题的「**IO 重叠**」是本章最高频考点。

---

## §18.1 为什么需要异步:IO 是瓶颈,线程是奢侈品(开胃 · 不出题)🟢

一个 Web 后端 90% 的时间在**等 IO**:等数据库、等下游 HTTP、等 Redis。等待期间 CPU 是闲的。

### Java 对照最小例

```java
// Tomcat 模型:一个请求占一个线程,等 IO 时线程整个阻塞(干等)
@GetMapping("/product/{id}")
public ProductDetail detail(@PathVariable long id) {
    Product p = productClient.get(id);   // 阻塞 50ms,线程干等
    Price pr = priceClient.get(id);      // 又阻塞 50ms
    Stock s = stockClient.get(id);       // 又阻塞 50ms → 共 150ms
    return new ProductDetail(p, pr, s);
}
// 想扛更多并发?加线程。但线程是 OS 资源:每个栈 1MB、上下文切换贵,几千个就扛不住。
// Java 21 的虚拟线程正是为解决「线程太贵」而生。
```

### Python 的解法:一个线程,同时等很多个 IO

```python
# async 模型:等 IO 时不占着线程,让线程去服务别的协程;IO 回来了再回来继续
async def aggregate_product_info(product_id: int) -> dict:
    product, price, stock = await asyncio.gather(   # 同一个线程,同时等 3 个 IO
        fetch_product(product_id),
        fetch_price(product_id),
        fetch_stock(product_id),
    )
    return {"product": product, "price": price, "stock": stock}
```

> 🟢 **关键认知**:`async` 不是「多线程并发」,而是「**单线程 + IO 期间不让线程干等**」。它解决的是 **IO 密集**场景的并发,**不是** CPU 密集场景。

### 本章主线的账:串行 vs 并发

```text
串行(await a; await b; await c):  总耗时 = a + b + c
  线程 |--等商品50ms--|--等价格50ms--|--等库存50ms--|   ≈ 150ms

并发(gather(a, b, c)):            总耗时 ≈ max(a, b, c)
  线程 |--同时等 商品/价格/库存--|                      ≈ 50ms
        ↑ 等商品的 50ms 里,线程去启动了价格和库存的等待
```

> 这就是产品经理要的结果:详情页接口从 150ms 压到 50ms,**没加一个线程**。测试会用计时断言证明这个差距(§18.4)。

---

## §18.2 async def + await:协程基础(对应:`fetch_product` / `fetch_price` / `fetch_stock`)🔴

### 定义:async def 调用后得到的是「协程」,不是结果

```python
import asyncio

async def fetch_product(product_id: int) -> dict:   # async def = 定义协程函数
    await asyncio.sleep(0.05)                        # await = 等一个异步操作(模拟 IO)
    return {"id": product_id, "name": "设计模式", "category": "图书"}

coro = fetch_product(3)        # 关键:此刻【什么都没执行】!coro 只是个「待跑的任务」
result = asyncio.run(coro)     # 这才真正跑 → {"id": 3, "name": "设计模式", ...}
```

> 🟡 **Java 对比**:协程函数调用 ≠ 执行,像 Java 的 `Supplier` / `CompletionStage`——你拿到的是「未执行的计算」,要 `.get()` 才推进。Python 更直接:`f()` 给协程对象,`await coro` 或 `asyncio.run(coro)` 才推进。

### await 的语义:让出事件循环

`await x` 做两件事:① 等 `x` 这个异步操作完成;② **等待期间把线程交还给事件循环**,让循环去跑别的协程。

`asyncio.sleep(n)` 是「异步版 `time.sleep`」:等待的 n 秒里**不阻塞线程**,而是让出;`time.sleep(n)` 会**死占**线程 n 秒——async 代码里绝对别用。

> 🤔 **为什么这么设计**:整个异步模型建立在「大家都很自觉、遇到等待就让出」上,这叫**协作式**(cooperative)调度。谁阻塞不让出(写了 `time.sleep` 或同步 HTTP 调用),整个事件循环就被卡死,所有协程陪葬。和 Java 线程的**抢占式**(OS 强制切换)截然不同。

### 真实场景例(商城三个下游服务)

本章用 `asyncio.sleep(IO_DELAY)` 模拟下游微服务的网络 IO,用种子表模拟返回数据:

```python
PRODUCTS = [{"id": 1, "name": "机械键盘", "category": "外设"},
            {"id": 3, "name": "设计模式", "category": "图书"}, ...]
PRICES   = {3: {"price": 75.5, "discount": 0.8}, ...}
STOCKS   = {3: {"stock": 128, "warehouse": "华北仓"}, ...}

# 三个「下游服务」函数,结构一模一样:sleep 模拟 IO → 查表 → 返回 dict
await fetch_product(3)   # → {"id": 3, "name": "设计模式", "category": "图书"}
await fetch_price(3)     # → {"product_id": 3, "price": 75.5, "discount": 0.8}
await fetch_stock(3)     # → {"product_id": 3, "stock": 128, "warehouse": "华北仓"}
await fetch_product(999) # → 抛 LookupError(模拟下游返回 404)
```

商品不存在时抛 `LookupError`——模拟真实下游的 404,§18.6 的端点会把它转成 HTTP 404。

### ❌ → ✅ 对照(Java 老手几乎必踩)

❌ **错误写法 1**(调了协程不 await,以为执行了):

```python
product = fetch_product(3)        # product 是个协程对象,不是 dict!
print(product["name"])            # TypeError: 'coroutine' object is not subscriptable
# 还会收到警告:RuntimeWarning: coroutine 'fetch_product' was never awaited
```

✅ **正确写法**:`product = await fetch_product(3)`(在 async 上下文里),或同步代码里 `asyncio.run(fetch_product(3))`。

❌ **错误写法 2**(用 `time.sleep` 模拟 IO):

```python
async def fetch_product(product_id: int):
    time.sleep(0.05)   # 死占线程 50ms!事件循环卡死,所有协程陪葬
```

✅ **正确写法**:`await asyncio.sleep(0.05)`——等待期间让出线程。

❌ **错误写法 3**(在普通 `def` 里写 `await`):

```python
def get_product(pid):              # 普通函数
    return await fetch_product(pid)  # SyntaxError!await 只能在 async def 里
```

✅ **正确写法**:要 `await`,函数就必须是 `async def`(异步会「传染」整条调用链)。

> ✅ 做 `fetch_product` / `fetch_price` / `fetch_stock`:`await asyncio.sleep(IO_DELAY)` → 查表 → `return` dict;查不到 → `raise LookupError(f"商品 {product_id} 不存在")`。三题结构一样,写完第一题后两题是「换个表」的熟练度练习。

---

## §18.3 asyncio.gather:并发聚合(对应:`aggregate_product_info` / `fetch_products_batch`)🔴

### gather:同时启动,等全部,按序返回

❌ **错误写法**(串行:等完一个再开始下一个,总耗时相加):

```python
async def aggregate_product_info(product_id: int) -> dict:
    product = await fetch_product(product_id)   # 等 50ms
    price   = await fetch_price(product_id)     # 又等 50ms
    stock   = await fetch_stock(product_id)     # 又等 50ms → 共 150ms
    return {"product": product, "price": price, "stock": stock}
```

✅ **正确写法**(`gather` 把多个协程**同时**排进事件循环):

```python
async def aggregate_product_info(product_id: int) -> dict:
    product, price, stock = await asyncio.gather(   # 三个一起启动,IO 等待重叠
        fetch_product(product_id),
        fetch_price(product_id),
        fetch_stock(product_id),
    )
    return {"product": product, "price": price, "stock": stock}   # 总耗时 ≈ 50ms
```

`gather` 干的事:① 把传入的协程**立刻排进**事件循环(开始并发跑);② 自己 `await` 直到**全部**完成;③ 返回**结果列表**,顺序 = 你传入的顺序,所以可以 `a, b, c = await gather(...)` 解包。

> 🤯 **Java 对比**:`asyncio.gather(a, b, c)` ≈ `CompletableFuture.allOf(fa, fb, fc)`——并发跑多个、等全部完成。区别:Python 是**单线程**跑这三个(IO 等待期交错),CompletableFuture 默认跑在 ForkJoinPool(真线程)。结果上都是「并发 + 等全部 + 按序返回」。

> ⚠️ **结果顺序 = 传入顺序,不是完成顺序**。`gather(fast(), slow())` 返回 `[fast结果, slow结果]`,即使 slow 先完成。

### 真实场景例(批量接口:`gather(*列表)` 并发动态数量)

运营要一个「批量查商品」接口,一次传 N 个 id。N 是运行时才知道的,不能写死三个参数——用**列表推导 + `*` 解包**:

```python
async def fetch_products_batch(product_ids: list[int]) -> list[dict]:
    return await asyncio.gather(*[fetch_product(pid) for pid in product_ids])
    #                          ↑ 列表推导造出 N 个协程,* 解包成 N 个位置参数

await fetch_products_batch([3, 1, 5])
# → [设计模式dict, 机械键盘dict, Python编程dict]   顺序 = 传入的 [3, 1, 5]
await fetch_products_batch([])   # → [](gather 无参数时返回空列表,天然处理边界)
```

5 个商品串行要 250ms,`gather` 并发仍然 ≈ 50ms——**N 个 IO 的等待全部重叠**,这是批量接口的杀手锏。

❌ **错误写法**(for 循环里逐个 await,又退回串行):

```python
results = []
for pid in product_ids:
    results.append(await fetch_product(pid))   # 每轮等 50ms,N 个就是 N×50ms
```

✅ **正确写法**:先用列表推导造出**全部协程**,再一次 `gather`——「先全部启动,再统一等」。

> ✅ 做 `aggregate_product_info`:`await asyncio.gather(fetch_product(pid), fetch_price(pid), fetch_stock(pid))` → 解包 → 返回三键 dict。做 `fetch_products_batch`:`gather(*[fetch_product(pid) for pid in ids])`,空列表不用特判。

---

## §18.4 串行 vs 并发:计时证据(对应:脚手架 `aggregate_serial`)🟡

作业里保留了一个**已写好的**串行版 `aggregate_serial`,测试里**计时断言**证明 gather 更快:

```python
# 3 个下游各 50ms(IO_DELAY = 0.05)
aggregate_serial(3)          # 串行:await 三次  → ≈ 0.15s
aggregate_product_info(3)    # 并发:gather      → ≈ 0.05s
# 测试阈值取 2× IO_DELAY = 0.10s:并发 < 0.10,串行 > 0.10,差距稳定不抖动
```

**省在哪?** 省在「等商品的 50ms 里,线程去启动并等价格、库存」。`fetch_product` 的 `asyncio.sleep` 让出线程 → 循环发现 `fetch_price` 没跑就跑它 → 三个 sleep **并行计时** → 差不多同时回来。全程**一个线程**。

> 🟡 **这是 async 的全部价值**:把 IO 等待时间重叠起来。反过来说——如果三个任务都是 CPU 计算(没有任何 `await` 让出),`gather` **不会**让它们并发:单线程还是一个算完再算另一个。

`aggregate_serial` 不用你填,它是「反面教材 + 测试对照」。读懂即可:三行 `await` 顺序执行,中间没有重叠。

---

## §18.5 asyncio.create_task:先启动、后等待(对应:`aggregate_with_tasks`)🟡

`gather` 之外,另一种让协程「立刻开跑」的方式是 `create_task`:

```python
async def aggregate_with_tasks(product_id: int) -> dict:
    t_product = asyncio.create_task(fetch_product(product_id))  # 立刻排入循环,后台开跑
    t_price   = asyncio.create_task(fetch_price(product_id))
    t_stock   = asyncio.create_task(fetch_stock(product_id))
    # ... 此刻三个任务已在并发跑,这里还能干别的 ...
    return {"product": await t_product,   # 要结果时再 await
            "price":   await t_price,
            "stock":   await t_stock}
```

| 写法 | 何时开始跑 |
|------|-----------|
| `await fetch_product(3)` | **等到这行才**开始跑 |
| `task = asyncio.create_task(fetch_product(3))` | **立刻**开始跑(后台),之后 `await task` 取结果 |

`gather` 内部其实就是「把每个协程包成 task 再统一等」。日常并发多个任务**优先用 `gather`**(一行搞定);需要「先启动、中途干别的、稍后再等」的精细控制才用 `create_task`。

> 🟡 **Java 对比**:`create_task` ≈ `CompletableFuture.supplyAsync(...)`(提交到池,立刻开始);直接 `await` 协程则像同步调用——「调用即阻塞等待」。

❌ **错误写法**(create_task 之后忘了 await,结果丢失):

```python
asyncio.create_task(fetch_product(3))   # 任务在后台跑,但没人等它 → 返回值拿不到
return {"product": ???}                 # 而且函数返回后,事件循环可能取消这个孤儿任务
```

✅ **正确写法**:每个 `create_task` 出来的 task,后面都要 `await`(或交给 `gather` 统一等)。

> ✅ 做 `aggregate_with_tasks`:三个 `create_task` → 逐个 `await` → 返回与 `aggregate_product_info` 相同的三键 dict。测试同样会计时:并发 ≈ 1× IO_DELAY。

---

## §18.6 FastAPI 异步路由(对应:`get_product_aggregate`)🔴

FastAPI 端点可以是 `def`(同步)或 `async def`(异步)。聚合要 `await` 协程,所以端点必须是 `async def`:

```python
@app.get("/products/{product_id}/aggregate")
async def get_product_aggregate(product_id: int):
    try:
        return await aggregate_product_info(product_id)   # 端点体里 await IO
    except LookupError:
        raise HTTPException(status_code=404, detail="商品不存在")
```

### 真实场景例(请求生命周期)

```text
GET /products/3/aggregate   → 200 {"product": {...}, "price": {...}, "stock": {...}}
                              等待 3 个下游的 50ms 里,事件循环去处理别人的请求
GET /products/999/aggregate → 404(LookupError → HTTPException,Ch06 的 try/except 复用)
GET /products/abc/aggregate → 422(路径参数校验,Ch15 的老朋友)
```

**为什么用 async 端点**:端点体内一旦 `await`(等 DB、等下游 API),事件循环就在等待期间**去处理别的请求**,单进程能扛的并发连接数大幅提升。这是 FastAPI / Starlette / aiohttp 的核心卖点。

**关键纪律**:**async 端点里绝对不能调阻塞的同步代码**。一旦阻塞,整个事件循环(及其上所有请求)卡死。

> 🟡 **Java 对比**:Tomcat 是「一个请求一个线程」,同步阻塞只卡自己那个线程;FastAPI 是「一个线程跑所有请求」,谁的代码阻塞,**全员陪葬**。这就是 async 的代价——要求整条调用链都是异步的(「async 全家桶」:DB 驱动用 asyncpg、HTTP 用 httpx.AsyncClient)。

❌ **错误写法**(async 端点里调同步阻塞库):

```python
@app.get("/products/{pid}/aggregate")
async def get_product_aggregate(pid: int):
    resp = requests.get(f"http://price-svc/{pid}")   # 同步阻塞!事件循环卡死
```

✅ **正确写法**:要么全链路异步(`httpx.AsyncClient`,§18.8),要么端点改回 `def` 让 FastAPI 丢线程池(§18.7)。

> ✅ 做 `get_product_aggregate`:`try: return await aggregate_product_info(product_id)` → `except LookupError: raise HTTPException(404, "商品不存在")`。

---

## §18.7 同步 vs 异步:何时用哪个(关键取舍)🟡

**FastAPI 对同步端点 `def` 的处理**(Ch14–17 的端点都是 `def`):它会把同步端点**丢到线程池**里跑(`run_in_threadpool`),阻塞只占线程池一个线程,**不卡事件循环**。所以两种端点不是「新的取代旧的」,而是按场景选:

| 端点类型 | 适合的场景 | 阻塞时的代价 |
|---------|-----------|--------------|
| `def`(同步) | 调**同步**库(同步 SQLAlchemy session、`requests`)、CPU 密集 | 占线程池一个线程,不卡事件循环 |
| `async def`(异步) | 调**异步**库(httpx.AsyncClient、asyncpg),全程不阻塞 | 不占线程池,吞吐高 |

**取舍口诀**:
- 代码里**有阻塞的同步调用**(`requests.get`、同步 DB、`time.sleep`)→ 别用 async,用普通 `def`。
- 代码**全程异步**(await httpx、await asyncpg)→ 用 `async def`,享受高并发。
- **千万别**在 `async def` 里混阻塞同步代码——性能杀手。

> 🤯 **Java 对比**:这就像 Spring WebFlux(全程 Reactor 异步,不能调阻塞 JDBC)vs Spring MVC(一请求一线程,同步 JDBC 没事)。FastAPI 同时支持两种,按端点选。**Java 21 虚拟线程**让「同步写法 + 高并发」成为可能(虚拟线程等 IO 时不占平台线程),某种程度上是「同步写法的 async」——但 Python 没有等价物,Python 的 async 就是显式 `async/await`。

---

## §18.8 httpx.AsyncClient:生产里的异步 HTTP(了解 · 不出题)🟢

Ch13 用 `httpx.get(...)`(同步)。异步版用 `AsyncClient`:

```python
import httpx

async def fetch_price_from_service(product_id: int) -> dict:
    async with httpx.AsyncClient(base_url="http://price-svc") as client:
        resp = await client.get(f"/prices/{product_id}")   # 真发异步 HTTP
        resp.raise_for_status()
        return resp.json()
```

`AsyncClient` 的 API 和同步 `Client` 几乎一样,只是方法是 async、要 `await`。本章作业用 `asyncio.sleep` 模拟 IO 没真发请求,但**生产里** `fetch_price` 的函数体就是上面这样——把 sleep 换成 `await client.get(...)` 即可,`gather` / 端点的代码一行不用改。

> 🟢 **Java 对比**:同步 httpx ≈ `HttpClient`(Java 11)/ RestTemplate;`AsyncClient` ≈ `HttpClient.sendAsync` 或 WebClient。

---

## §18.9 Java 老手常踩的坑 ⚠️

1. **调用协程不 await**:`fetch_product(3)` 得到协程对象,**不执行**。必须 `await` 或 `asyncio.run`,否则「coroutine was never awaited」警告 + 啥也没干。
2. **`await` 写在普通 `def` 里**:SyntaxError。`await` 只能在 `async def` 里——异步会「传染」整条调用链。
3. **async 代码里用 `time.sleep` / `requests.get`**:阻塞线程 → 卡死整个事件循环。要用 `asyncio.sleep` / `httpx.AsyncClient`。
4. **`asyncio.run` 在已有事件循环时再调**:报错「cannot be called from a running event loop」。FastAPI 端点里(已在循环里)不能再 `asyncio.run`,直接 `await`。`asyncio.run` 只在**普通同步代码**(如测试)里用。
5. **把 CPU 密集任务塞进 async**:以为加 `async` 就并发了——并没有。CPU 计算不 `await`、不让出,gather 也只能串行算。CPU 密集用**多进程**(`ProcessPoolExecutor`)或干脆同步。
6. **同步/异步混用**:端点是 `async def`,里面却调同步阻塞的 DB 驱动——直接卡死。要么换异步驱动,要么端点改回 `def`。
7. **以为 `async` = 多线程**:不是,全程单线程。纯 async、无 `await` 中断的区段内共享变量不需要锁;一旦 `await` 可能被切走,共享状态就要小心。
8. **`gather` 结果顺序 ≠ 完成顺序**:是**传入顺序**。批量场景靠这个保证「第 i 个结果对应第 i 个 id」。

---

## §18.10 速查:Python async ↔ Java 并发对照

| Python async | Java 对应 | 说明 |
|--------------|-----------|------|
| `async def` | `CompletableFuture.supplyAsync` | 定义异步计算(协程) |
| `await coro` | `future.get()` / `.join()` | 等结果(等期间让出线程) |
| `asyncio.gather(a,b)` | `CompletableFuture.allOf(fa,fb)` | 并发跑多个、等全部、按传入顺序返回 |
| `asyncio.gather(*列表)` | `allOf(list.toArray(...))` | 并发动态数量 |
| `asyncio.create_task(c)` | `CompletableFuture.supplyAsync`(立即提交) | 立刻调度,后台跑 |
| `asyncio.run(main)` | (Java 无等价:Java 进程自带线程) | 同步代码里启动事件循环跑一个协程 |
| 事件循环(event loop) | (线程池/调度器) | 单线程调度协程 |
| 单线程协作式 | Java 虚拟线程(抢占式,JVM 调度) | 谁让出 / 谁被切走的差别 |
| `asyncio.sleep`(不阻塞) | `Thread.sleep`(阻塞) | 让出等待 vs 死占线程 |
| `httpx.AsyncClient` | `HttpClient.sendAsync` / WebClient | 异步 HTTP |

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `fetch_product` | async def + await sleep + 查表 + LookupError | 🟡 |
| `fetch_price` | 同上,熟练度 | 🟢 |
| `fetch_stock` | 同上,熟练度 | 🟢 |
| `aggregate_product_info` | **asyncio.gather 并发**(重点) | 🔴 |
| `fetch_products_batch` | gather(*列表) + 保序 + 空列表 | 🟡 |
| `aggregate_with_tasks` | create_task 先启动后等待 | 🟡 |
| `get_product_aggregate` | FastAPI async 端点 + 404 | 🟡 |

```bash
uv sync --extra web
uv run pytest 03_web_framework/ch18/test_ch18_assignment.py -v
```

期望:28 个全绿。其中计时断言会验证:3 个下游并发版 < `2 × IO_DELAY`(0.10s),串行版 > 该阈值——阈值取在并发(1×)与串行(3×)之间,CI 抖动也能过。

---

## ✅ 自测清单

- [ ] 能说清「`async` 不是多线程,是单线程协作式并发」
- [ ] 知道调用 `async def` 函数得到的是**协程对象**,必须 `await` 或 `asyncio.run` 才执行
- [ ] 能用 `asyncio.gather` 并发跑多个协程,知道结果顺序 = 传入顺序
- [ ] 能用 `gather(*[...])` 并发动态数量的协程,知道空列表返回 `[]`
- [ ] 能解释为什么 `gather(a,b,c)` 比 `await a; await b; await c` 快(IO 重叠)
- [ ] 知道 `create_task` 与直接 `await` 的启动时机差别
- [ ] 知道 async 代码里不能用 `time.sleep` / `requests`(要用 asyncio 版)
- [ ] 知道 FastAPI `def` 端点会被丢线程池、`async def` 端点不能阻塞
- [ ] 知道 CPU 密集任务不该用 async
- [ ] 28 个测试全绿

---

## 🎓 费曼挑战(合上教程讲清「为什么」)

1. **「为什么 `gather(fetch_product, fetch_price, fetch_stock)` 比串行 await 三次快?同一个线程怎么可能同时干三件事?」**
   — 卡壳重读 §18.1 的图 + §18.4。(关键词:IO 等待重叠、await 让出、事件循环交错)

2. **「为什么在 `async def` 端点里调 `requests.get`(同步 HTTP)是严重错误,而 `def` 端点调 `requests` 却没事?」**
   — 卡壳重读 §18.6 + §18.7。(关键词:事件循环被卡死 vs 丢线程池)

3. **「Python 的 async 和 Java 21 虚拟线程都能扛高并发 IO,本质差别是什么?」**
   — 卡壳重读 §18.7。(关键词:协作式 vs 抢占式、显式 await vs JVM 自动挂起)

4. **「`fetch_products_batch([3,1,5])` 的结果顺序是按什么排的?如果改成 for 循环逐个 await,除了慢还有什么差别?」**
   — 卡壳重读 §18.3。(关键词:传入顺序、先全部启动再统一等)

---

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步

Ch18 学完,你掌握了 FastAPI 的**异步能力**:并发 IO、async 端点、同步/异步取舍。

下一章 **Ch19 · 数据库 ORM:SQLAlchemy 2.0**——接真数据库(对比 MyBatis/JPA),你会再次面对本章 §18.7 的取舍:同步 session 配 `def` 端点 + 线程池,还是异步 `AsyncSession`(asyncpg)配 `async def` 端点。
