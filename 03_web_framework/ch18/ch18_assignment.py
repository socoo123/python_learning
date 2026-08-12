"""
Ch18 作业:异步编程 async/await —— Python 与 Java 并发模型差异最大的一章。

场景:「极客商城」商品详情页要同时展示「基本信息 + 价格 + 库存」,数据在 3 个
下游微服务里,每次调用 IO 耗时 50ms(IO_DELAY)。串行调用让详情页接口超过 150ms,
你要用 asyncio.gather 并发把接口压回 50ms 级,并包装成 FastAPI 异步端点。

你填七处:
  ① fetch_product            —— 商品服务:async def + await sleep + 查表
  ② fetch_price              —— 价格服务:同上
  ③ fetch_stock              —— 库存服务:同上
  ④ aggregate_product_info   —— 重点:gather 并发 3 个下游,耗时 ≈ max 而非相加
  ⑤ fetch_products_batch     —— gather(*列表) 并发动态数量,结果按传入顺序
  ⑥ aggregate_with_tasks     —— create_task 先启动、后等待
  ⑦ get_product_aggregate    —— FastAPI async 端点,LookupError → 404

    uv sync --extra web
    uv run pytest 03_web_framework/ch18/test_ch18_assignment.py -v

每题【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
import asyncio

from fastapi import FastAPI, HTTPException

app = FastAPI(title="极客商城 · 商品详情聚合")

# 每个下游微服务的模拟 IO 耗时(秒)。3 个服务串行 ≈ 3x,并发 ≈ 1x,差距稳定。
IO_DELAY = 0.05

# ---------- 种子数据:三个下游微服务的「数据库」(脚手架,直接用)----------

PRODUCTS: list[dict] = [
    {"id": 1, "name": "机械键盘", "category": "外设"},
    {"id": 2, "name": "无线鼠标", "category": "外设"},
    {"id": 3, "name": "设计模式", "category": "图书"},
    {"id": 4, "name": "降噪耳机", "category": "音频"},
    {"id": 5, "name": "Python编程", "category": "图书"},
]

PRICES: dict[int, dict] = {
    1: {"price": 599.0, "discount": 0.9},
    2: {"price": 159.0, "discount": 1.0},
    3: {"price": 75.5, "discount": 0.8},
    4: {"price": 1299.0, "discount": 0.85},
    5: {"price": 89.0, "discount": 1.0},
}

STOCKS: dict[int, dict] = {
    1: {"stock": 42, "warehouse": "华东仓"},
    2: {"stock": 0, "warehouse": "华东仓"},
    3: {"stock": 128, "warehouse": "华北仓"},
    4: {"stock": 7, "warehouse": "华南仓"},
    5: {"stock": 233, "warehouse": "华北仓"},
}


# ---------- ① 商品服务:取基本信息 ----------


async def fetch_product(product_id: int) -> dict:
    """
    【async def + await · §18.2】模拟调用「商品服务」:一次网络 IO。

    任务:
      ① await asyncio.sleep(IO_DELAY)  —— 模拟 50ms 网络 IO(等待期间让出线程)
      ② 在 PRODUCTS 里按 id 查找,找到就返回该商品 dict
      ③ 找不到 → raise LookupError(f"商品 {product_id} 不存在")(模拟下游 404)

    示例:
        await fetch_product(3)   -> {"id": 3, "name": "设计模式", "category": "图书"}
        await fetch_product(1)   -> {"id": 1, "name": "机械键盘", "category": "外设"}
        await fetch_product(999) -> 抛 LookupError

    提示:查找用 next((p for p in PRODUCTS if p["id"] == product_id), None);
         别用 time.sleep——它会死占线程,卡死整个事件循环(§18.2)。
    """
    # TODO: await asyncio.sleep(IO_DELAY) → 查 PRODUCTS → 返回 / 未找到 raise LookupError
    ...


# ---------- ② 价格服务:取价格与折扣 ----------


async def fetch_price(product_id: int) -> dict:
    """
    【async def + await · §18.2】模拟调用「价格服务」。

    任务:
      ① await asyncio.sleep(IO_DELAY)
      ② 在 PRICES 里查到 → 返回 {"product_id": product_id, "price": ..., "discount": ...}
      ③ 查不到 → raise LookupError(f"商品 {product_id} 不存在")

    示例:
        await fetch_price(3) -> {"product_id": 3, "price": 75.5, "discount": 0.8}
        await fetch_price(4) -> {"product_id": 4, "price": 1299.0, "discount": 0.85}
        await fetch_price(999) -> 抛 LookupError

    提示:PRICES 是 dict,用 product_id in PRICES 判断存在性;
         返回的 dict 要带上 product_id 键(下游响应的常规做法)。
    """
    # TODO: await asyncio.sleep(IO_DELAY) → 查 PRICES → 返回带 product_id 的 dict / raise LookupError
    ...


# ---------- ③ 库存服务:取库存与仓库 ----------


async def fetch_stock(product_id: int) -> dict:
    """
    【async def + await · §18.2】模拟调用「库存服务」。

    任务:
      ① await asyncio.sleep(IO_DELAY)
      ② 在 STOCKS 里查到 → 返回 {"product_id": product_id, "stock": ..., "warehouse": ...}
      ③ 查不到 → raise LookupError(f"商品 {product_id} 不存在")

    示例:
        await fetch_stock(3) -> {"product_id": 3, "stock": 128, "warehouse": "华北仓"}
        await fetch_stock(2) -> {"product_id": 2, "stock": 0, "warehouse": "华东仓"}
        await fetch_stock(999) -> 抛 LookupError

    提示:结构与 fetch_price 完全对称——写完 ①② 后这题是熟练度练习。
    """
    # TODO: await asyncio.sleep(IO_DELAY) → 查 STOCKS → 返回带 product_id 的 dict / raise LookupError
    ...


# ---------- ④ 重点:aggregate_product_info 用 gather 并发 ----------


async def aggregate_product_info(product_id: int) -> dict:
    """
    【asyncio.gather 并发 · §18.3 —— 本章重点】并发调用 3 个下游,聚合详情页数据。

    任务:
      ① await asyncio.gather(fetch_product(...), fetch_price(...), fetch_stock(...))
         —— 三个协程同时启动,IO 等待重叠,总耗时 ≈ 1 个 IO_DELAY(不是 3 个)
      ② 解包成 product, price, stock(结果顺序 = 传入顺序)
      ③ 返回 {"product": product, "price": price, "stock": stock}

    示例:
        await aggregate_product_info(3)
            -> {"product": {"id": 3, "name": "设计模式", "category": "图书"},
                "price":   {"product_id": 3, "price": 75.5, "discount": 0.8},
                "stock":   {"product_id": 3, "stock": 128, "warehouse": "华北仓"}}
        耗时 ≈ 0.05s(串行版 aggregate_serial 要 ≈ 0.15s,测试会计时对比)
        await aggregate_product_info(999) -> 抛 LookupError(gather 会传播异常)

    提示:千万别写成 await 三次的串行版——功能对但计时测试会挂;
         对比下方脚手架 aggregate_serial,体会差距。
    """
    # TODO: await asyncio.gather(三个协程) → 解包 → 返回 {"product":..., "price":..., "stock":...}
    ...


# ---------- ⑤ 批量:fetch_products_batch 并发动态数量 ----------


async def fetch_products_batch(product_ids: list[int]) -> list[dict]:
    """
    【gather(*列表) · §18.3】运营批量查商品:一次并发查 N 个,N 运行时才知道。

    任务:
      ① 列表推导造出 N 个协程:[fetch_product(pid) for pid in product_ids]
      ② await asyncio.gather(*那个列表)  —— * 把列表解包成 N 个位置参数
      ③ 直接返回结果列表(顺序 = product_ids 的传入顺序)

    示例:
        await fetch_products_batch([3, 1, 5])
            -> [{"id": 3, ...}, {"id": 1, ...}, {"id": 5, ...}]   # 按传入顺序,不是按 id 排序
        await fetch_products_batch([])  -> []   # gather 无参数返回空列表,天然处理边界
        5 个商品耗时仍 ≈ 1 个 IO_DELAY(N 个 IO 等待全部重叠)

    提示:别写 for 循环里逐个 await——那又退回串行(N×50ms),计时测试会挂;
         空列表不用特判,gather() 本身就是 []。
    """
    # TODO: return await asyncio.gather(*[fetch_product(pid) for pid in product_ids])
    ...


# ---------- ⑥ create_task:aggregate_with_tasks 先启动后等待 ----------


async def aggregate_with_tasks(product_id: int) -> dict:
    """
    【asyncio.create_task · §18.5】用 create_task 实现与 ④ 相同的聚合。

    任务:
      ① t_product = asyncio.create_task(fetch_product(product_id))  —— 立刻排入事件循环
         t_price、t_stock 同理(三个任务此刻已在后台并发跑)
      ② await t_product / await t_price / await t_stock 取结果
      ③ 返回 {"product": ..., "price": ..., "stock": ...}(与 ④ 结构相同)

    示例:
        await aggregate_with_tasks(4)
            -> {"product": {"id": 4, "name": "降噪耳机", "category": "音频"},
                "price":   {"product_id": 4, "price": 1299.0, "discount": 0.85},
                "stock":   {"product_id": 4, "stock": 7, "warehouse": "华南仓"}}
        耗时 ≈ 1 个 IO_DELAY(三个任务 create_task 时就已并发启动)

    提示:create_task 与直接 await 的区别在「启动时机」——create_task 立刻跑,
         await 协程要等执行到那行才跑;每个 task 后面都要有人 await,别成孤儿。
    """
    # TODO: 三个 create_task → 逐个 await → 返回 {"product":..., "price":..., "stock":...}
    ...


# ---------- 脚手架:串行对照版(不用填,测试用它证明 gather 更快)----------


async def aggregate_serial(product_id: int) -> dict:
    """
    【串行 await 三次 · §18.4】先取商品、再取价格、再取库存,总耗时 ≈ 3 个 IO_DELAY。
    和 aggregate_product_info(并发)对比,体会 gather 的价值。
    """
    product = await fetch_product(product_id)   # 等 50ms
    price = await fetch_price(product_id)       # 又等 50ms
    stock = await fetch_stock(product_id)       # 又等 50ms → 共 ≈ 150ms
    return {"product": product, "price": price, "stock": stock}


# ---------- ⑦ FastAPI 异步端点 ----------


@app.get("/products/{product_id}/aggregate")
async def get_product_aggregate(product_id: int):
    """
    【FastAPI 异步路由 · §18.6】商品详情聚合端点:async def + await ④。

    任务:
      ① try: return await aggregate_product_info(product_id)
      ② except LookupError → raise HTTPException(status_code=404, detail="商品不存在")

    示例:
        GET /products/3/aggregate   -> 200,body 是 {"product":..., "price":..., "stock":...}
        GET /products/999/aggregate -> 404(LookupError 转 HTTP 404)
        GET /products/abc/aggregate -> 422(路径参数校验,框架自动)

    提示:端点里 await 期间,事件循环去处理别的请求——这是 async 端点的高并发优势;
         千万别在 async 端点里调 requests.get 这类同步阻塞代码(§18.6 纪律)。
    """
    # TODO: try: return await aggregate_product_info(product_id) / except LookupError → 404
    ...


@app.get("/health")
async def health():
    """健康检查(脚手架)。"""
    return {"status": "ok"}
