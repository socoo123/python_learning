"""
Ch18 作业测试。运行: uv run pytest 03_web_framework/ch18/test_ch18_assignment.py -v

纯 async 函数用 asyncio.run 跑(同步测试里驱动协程);
FastAPI async 端点用 TestClient 测(TestClient 内部跑事件循环,API 同步)。
"""
import time

from fastapi.testclient import TestClient

import asyncio

from ch18_assignment import (
    aggregate,
    aggregate_serial,
    fetch_orders,
    fetch_user,
    health,
    profile,
    app,
    IO_DELAY,
)

client = TestClient(app)


# ---------- ① 单个 async IO 任务 ----------
class TestFetchTasks:
    def test_fetch_user_returns_dict(self):
        """fetch_user 返回带 id 和 name 的 dict。"""
        result = asyncio.run(fetch_user(7))
        assert result == {"id": 7, "name": "用户7"}

    def test_fetch_user_is_coroutine(self):
        """fetch_user() 返回协程对象(不是直接执行)—— async def 的标志。"""
        coro = fetch_user(3)
        assert asyncio.iscoroutine(coro)
        # 必须跑掉,否则协程未关闭会告警
        asyncio.run(coro)

    def test_fetch_orders_returns_list(self):
        """fetch_orders 返回订单列表,每条带 order_id 和 amount。"""
        orders = asyncio.run(fetch_orders(5))
        assert isinstance(orders, list)
        assert len(orders) == 2
        for o in orders:
            assert "order_id" in o and "amount" in o
        # order_id = uid*10 + 序号
        assert orders[0]["order_id"] == 51
        assert orders[1]["order_id"] == 52


# ---------- ② gather 并发:正确性 ----------
class TestAggregate:
    def test_aggregate_combines_user_and_orders(self):
        """aggregate 用 gather 并发,返回 {user, orders} 结构正确。"""
        result = asyncio.run(aggregate(4))
        assert result["user"] == {"id": 4, "name": "用户4"}
        assert isinstance(result["orders"], list)
        assert result["orders"][0]["order_id"] == 41

    def test_aggregate_returns_dict_with_two_keys(self):
        """结构:顶层只有 user / orders 两个 key。"""
        result = asyncio.run(aggregate(1))
        assert set(result.keys()) == {"user", "orders"}


# ---------- ③ 重点:gather 并发 vs 串行,计时断言 ----------
class TestConcurrencySpeedup:
    def test_gather_faster_than_serial(self):
        """
        【并发演示】gather 版耗时 ≈ 1 个 IO_DELAY;串行版 ≈ 2 个 IO_DELAY。
        阈值取中点(IO_DELAY * 1.5),宽松,CI 抖动也能过。
        """
        threshold = IO_DELAY * 1.5  # 介于并发(1x)和串行(2x)之间

        t0 = time.perf_counter()
        asyncio.run(aggregate(9))
        concurrent_time = time.perf_counter() - t0
        assert concurrent_time < threshold, (
            f"并发版应在 {threshold:.3f}s 内完成,实际 {concurrent_time:.3f}s"
        )

        t1 = time.perf_counter()
        asyncio.run(aggregate_serial(9))
        serial_time = time.perf_counter() - t1
        assert serial_time > threshold, (
            f"串行版应超过 {threshold:.3f}s,实际 {serial_time:.3f}s"
        )

    def test_concurrent_time_about_one_delay(self):
        """gather 版耗时接近单个任务(允许一定调度开销)。"""
        overhead = IO_DELAY * 0.8  # 宽松:并发应明显快于串行(2x)
        t0 = time.perf_counter()
        asyncio.run(aggregate(2))
        elapsed = time.perf_counter() - t0
        # 并发版应远小于 2 个 IO_DELAY
        assert elapsed < IO_DELAY + overhead


# ---------- ④ FastAPI 异步端点 ----------
class TestAsyncEndpoint:
    def test_profile_endpoint(self):
        """async 端点 /profile/{uid} 返回聚合结果(TestClient 同步测 async 端点)。"""
        resp = client.get("/profile/8")
        assert resp.status_code == 200
        body = resp.json()
        assert body["user"] == {"id": 8, "name": "用户8"}
        assert body["orders"][0]["order_id"] == 81

    def test_profile_path_param_parsing(self):
        """路径参数 uid 自动解析成 int。"""
        resp = client.get("/profile/12")
        assert resp.status_code == 200
        assert resp.json()["user"]["id"] == 12

    def test_profile_invalid_uid_returns_422(self):
        """非整数 uid → FastAPI 路径参数校验 422。"""
        resp = client.get("/profile/abc")
        assert resp.status_code == 422

    def test_health(self):
        """health 也是 async 端点,正常返回。"""
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ---------- ⑤ create_task:在协程内调度(对应 §18.5)----------
class TestCreateTask:
    def test_create_task_schedules_concurrently(self):
        """
        asyncio.create_task 把协程包装成 Task 立即调度(不等 await)。
        对比直接 await 协程(它不会立刻跑,要等真正 await 它)。
        """

        async def main():
            # create_task 立即把 fetch_user 排入事件循环
            task = asyncio.create_task(fetch_user(6))
            # 此时 task 已在并发跑;await 等它出结果
            return await task

        assert asyncio.run(main()) == {"id": 6, "name": "用户6"}

    def test_create_task_overlap_two_tasks(self):
        """两个 create_task 几乎同时启动 → 总耗时 ≈ 1 个 IO_DELAY(并发)。"""
        threshold = IO_DELAY * 1.5

        async def main():
            t1 = asyncio.create_task(fetch_user(1))
            t2 = asyncio.create_task(fetch_orders(1))
            u, o = await asyncio.gather(t1, t2)
            return u, o

        t0 = time.perf_counter()
        asyncio.run(main())
        elapsed = time.perf_counter() - t0
        assert elapsed < threshold
