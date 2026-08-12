"""
Ch18 作业测试。运行:

    uv sync --extra web
    uv run pytest 03_web_framework/ch18/test_ch18_assignment.py -v

纯 async 函数用 asyncio.run 在同步测试里驱动(不需要 pytest-asyncio);
FastAPI async 端点用 TestClient 测(内部跑事件循环,API 同步)。
计时断言:3 个下游并发 ≈ 1×IO_DELAY,串行 ≈ 3×IO_DELAY,阈值取 2×IO_DELAY。
"""
import asyncio
import time

import pytest
from fastapi.testclient import TestClient

from ch18_assignment import (
    IO_DELAY,
    aggregate_product_info,
    aggregate_serial,
    aggregate_with_tasks,
    app,
    fetch_price,
    fetch_product,
    fetch_products_batch,
    fetch_stock,
)

client = TestClient(app)

# 计时阈值:介于并发(1×IO_DELAY)与串行(3×IO_DELAY)之间,宽松不抖动
THRESHOLD = IO_DELAY * 2


# ---------- ① fetch_product(商品服务)----------
class TestFetchProduct:
    def test_returns_book_product(self):
        result = asyncio.run(fetch_product(3))
        assert result == {"id": 3, "name": "设计模式", "category": "图书"}

    def test_returns_electronics_product(self):
        result = asyncio.run(fetch_product(1))
        assert result == {"id": 1, "name": "机械键盘", "category": "外设"}

    def test_calling_returns_coroutine_not_result(self):
        # async def 的标志:调用得到协程对象,必须 await/run 才执行(§18.2)
        coro = fetch_product(3)
        assert asyncio.iscoroutine(coro)
        asyncio.run(coro)  # 跑掉,避免「never awaited」警告

    def test_unknown_id_raises_lookup_error(self):
        with pytest.raises(LookupError):
            asyncio.run(fetch_product(999))


# ---------- ② fetch_price(价格服务)----------
class TestFetchPrice:
    def test_returns_price_with_discount(self):
        result = asyncio.run(fetch_price(3))
        assert result == {"product_id": 3, "price": 75.5, "discount": 0.8}

    def test_returns_full_price_when_no_discount(self):
        result = asyncio.run(fetch_price(2))
        assert result == {"product_id": 2, "price": 159.0, "discount": 1.0}

    def test_unknown_id_raises_lookup_error(self):
        with pytest.raises(LookupError):
            asyncio.run(fetch_price(999))


# ---------- ③ fetch_stock(库存服务)----------
class TestFetchStock:
    def test_returns_stock_and_warehouse(self):
        result = asyncio.run(fetch_stock(3))
        assert result == {"product_id": 3, "stock": 128, "warehouse": "华北仓"}

    def test_returns_zero_stock(self):
        # 边界:库存为 0 也是合法结果(别写成 falsy 就当不存在)
        result = asyncio.run(fetch_stock(2))
        assert result == {"product_id": 2, "stock": 0, "warehouse": "华东仓"}

    def test_unknown_id_raises_lookup_error(self):
        with pytest.raises(LookupError):
            asyncio.run(fetch_stock(999))


# ---------- ④ aggregate_product_info(gather 并发,本章重点)----------
class TestAggregateProductInfo:
    def test_returns_three_sections(self):
        result = asyncio.run(aggregate_product_info(3))
        assert set(result.keys()) == {"product", "price", "stock"}
        assert result["product"] == {"id": 3, "name": "设计模式", "category": "图书"}
        assert result["price"] == {"product_id": 3, "price": 75.5, "discount": 0.8}
        assert result["stock"] == {"product_id": 3, "stock": 128, "warehouse": "华北仓"}

    def test_values_for_another_product(self):
        result = asyncio.run(aggregate_product_info(4))
        assert result["product"]["name"] == "降噪耳机"
        assert result["price"]["price"] == 1299.0
        assert result["stock"]["warehouse"] == "华南仓"

    def test_unknown_id_raises_lookup_error(self):
        with pytest.raises(LookupError):
            asyncio.run(aggregate_product_info(999))

    def test_concurrent_faster_than_threshold(self):
        # 并发版 ≈ 1×IO_DELAY,应远低于阈值 2×IO_DELAY(§18.4)
        t0 = time.perf_counter()
        asyncio.run(aggregate_product_info(1))
        elapsed = time.perf_counter() - t0
        assert elapsed < THRESHOLD, (
            f"并发版应在 {THRESHOLD:.3f}s 内,实际 {elapsed:.3f}s——是不是写成了串行 await?"
        )

    def test_serial_version_is_slower(self):
        # 串行对照版 ≈ 3×IO_DELAY,应超过阈值——证明 gather 的提速是真的
        t0 = time.perf_counter()
        asyncio.run(aggregate_serial(1))
        elapsed = time.perf_counter() - t0
        assert elapsed > THRESHOLD, (
            f"串行版应超过 {THRESHOLD:.3f}s,实际 {elapsed:.3f}s"
        )


# ---------- ⑤ fetch_products_batch(gather(*列表) 动态并发)----------
class TestFetchProductsBatch:
    def test_results_follow_input_order(self):
        # 结果顺序 = 传入顺序,不是 id 排序(§18.3)
        result = asyncio.run(fetch_products_batch([3, 1, 5]))
        assert [p["id"] for p in result] == [3, 1, 5]
        assert result[0]["name"] == "设计模式"
        assert result[1]["name"] == "机械键盘"
        assert result[2]["name"] == "Python编程"

    def test_all_five_products(self):
        result = asyncio.run(fetch_products_batch([1, 2, 3, 4, 5]))
        assert [p["id"] for p in result] == [1, 2, 3, 4, 5]

    def test_empty_list_returns_empty(self):
        # 边界:gather() 无参数返回空列表,不用特判
        assert asyncio.run(fetch_products_batch([])) == []

    def test_any_unknown_id_raises_lookup_error(self):
        with pytest.raises(LookupError):
            asyncio.run(fetch_products_batch([1, 999, 3]))

    def test_batch_is_concurrent(self):
        # 5 个商品串行要 5×IO_DELAY,并发仍 ≈ 1×——拦住 for 循环逐个 await 的实现
        t0 = time.perf_counter()
        asyncio.run(fetch_products_batch([1, 2, 3, 4, 5]))
        elapsed = time.perf_counter() - t0
        assert elapsed < THRESHOLD, (
            f"批量并发应在 {THRESHOLD:.3f}s 内,实际 {elapsed:.3f}s——是不是 for 里逐个 await 了?"
        )


# ---------- ⑥ aggregate_with_tasks(create_task 先启动后等待)----------
class TestAggregateWithTasks:
    def test_returns_same_shape_as_gather_version(self):
        result = asyncio.run(aggregate_with_tasks(4))
        assert result == {
            "product": {"id": 4, "name": "降噪耳机", "category": "音频"},
            "price": {"product_id": 4, "price": 1299.0, "discount": 0.85},
            "stock": {"product_id": 4, "stock": 7, "warehouse": "华南仓"},
        }

    def test_values_for_another_product(self):
        result = asyncio.run(aggregate_with_tasks(5))
        assert result["product"]["name"] == "Python编程"
        assert result["price"]["discount"] == 1.0
        assert result["stock"]["stock"] == 233

    def test_tasks_run_concurrently(self):
        # create_task 立刻启动 → 总耗时 ≈ 1×IO_DELAY(§18.5)
        t0 = time.perf_counter()
        asyncio.run(aggregate_with_tasks(1))
        elapsed = time.perf_counter() - t0
        assert elapsed < THRESHOLD, (
            f"create_task 版应在 {THRESHOLD:.3f}s 内,实际 {elapsed:.3f}s"
        )


# ---------- ⑦ get_product_aggregate(FastAPI 异步端点)----------
class TestGetProductAggregate:
    def test_aggregate_endpoint_200(self):
        resp = client.get("/products/3/aggregate")
        assert resp.status_code == 200
        body = resp.json()
        assert body["product"] == {"id": 3, "name": "设计模式", "category": "图书"}
        assert body["price"]["price"] == 75.5
        assert body["stock"]["warehouse"] == "华北仓"

    def test_aggregate_endpoint_another_product(self):
        resp = client.get("/products/1/aggregate")
        assert resp.status_code == 200
        assert resp.json()["product"]["name"] == "机械键盘"

    def test_unknown_product_returns_404(self):
        # LookupError → HTTP 404(§18.6)
        resp = client.get("/products/999/aggregate")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "商品不存在"

    def test_invalid_id_returns_422(self):
        resp = client.get("/products/abc/aggregate")
        assert resp.status_code == 422

    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
