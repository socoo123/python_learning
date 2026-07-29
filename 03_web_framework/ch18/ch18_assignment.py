"""
Ch18 作业:异步编程 async/await —— Python 与 Java 并发模型差异最大的一章。

核心演示:用 asyncio.gather 把两个 IO 任务【并发】跑(单线程协作式),
比【串行】await 两次快一倍。再包成一个 FastAPI async 端点。

你填四处:① fetch_user ② fetch_orders ③ aggregate(gather 并发)④ profile(async 端点)。

    uv run pytest 03_web_framework/ch18/test_ch18_assignment.py -v

每题【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
import asyncio

from fastapi import FastAPI

app = FastAPI(title="异步编程演示")

# 每个模拟 IO 任务的耗时(秒)。两个任务串行 ≈ 2x,并发 ≈ 1x,差距稳定。
IO_DELAY = 0.05


# ---------- ① 模拟单个 IO 任务:取用户 ----------


async def fetch_user(uid: int) -> dict:
    """
    【async def + await · §18.2】模拟一次「取用户」的网络/DB IO。
    await asyncio.sleep(IO_DELAY) 模拟阻塞 IO(让出事件循环)。

    思路:
        await asyncio.sleep(IO_DELAY)                 # 模拟 IO,这里让出(不阻塞线程)
        return {"id": uid, "name": f"用户{uid}"}
    """
    # TODO: await asyncio.sleep → return {"id": uid, "name": f"用户{uid}"}
    ...


# ---------- ② 模拟单个 IO 任务:取订单 ----------


async def fetch_orders(uid: int) -> list[dict]:
    """
    【async def + await · §18.2】模拟一次「取该用户订单」的 IO。

    思路:
        await asyncio.sleep(IO_DELAY)
        return [{"order_id": uid * 10 + 1, "amount": 99.0},
                {"order_id": uid * 10 + 2, "amount": 199.0}]
    """
    # TODO: await asyncio.sleep → return [两条订单 dict]
    ...


# ---------- ③ 重点:aggregate 用 gather 并发 ----------


async def aggregate(uid: int) -> dict:
    """
    【asyncio.gather 并发 · §18.3 —— 本章重点】并发取「用户 + 订单」。
    gather 同时启动两个协程,IO 期间互相等待,总耗时 ≈ max(单个) 而非相加。

    思路(对比 §18.4 串行版 aggregate_serial):
        user, orders = await asyncio.gather(           # 一次 await 拿两个结果
            fetch_user(uid),
            fetch_orders(uid),
        )
        return {"user": user, "orders": orders}
    """
    # TODO: await asyncio.gather(fetch_user(uid), fetch_orders(uid)) → 返回 {"user":..., "orders":...}
    ...


# ---------- ④ 串行版:用来对比 gather ----------


async def aggregate_serial(uid: int) -> dict:
    """
    【串行 await 两次 · §18.4】先取用户再取订单,顺序执行,总耗时 ≈ 相加。
    和 aggregate(并发)对比,体会 gather 的价值。
    """
    user = await fetch_user(uid)          # 先等这个完成
    orders = await fetch_orders(uid)      # 再等这个(加起来 = 2 * IO_DELAY)
    return {"user": user, "orders": orders}


# ---------- ⑤ FastAPI async 端点 ----------


@app.get("/profile/{uid}")
async def profile(uid: int):
    """
    【FastAPI 异步路由 · §18.6】async def 端点 + await aggregate。
    端点体内 await IO,事件循环就能在等 IO 时去处理别的请求(高并发优势)。

    思路:return await aggregate(uid)
    """
    # TODO: return await aggregate(uid)
    ...


@app.get("/health")
async def health():
    """健康检查。"""
    return {"status": "ok"}
