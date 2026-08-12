"""
Ch17 作业测试。运行:

    uv sync --extra web
    uv run pytest 03_web_framework/ch17/test_ch17_assignment.py -v

端点用 TestClient 发真 HTTP 语义请求;3 个业务异常处理器也可直接单测(普通函数)。
每例前重置商品 / 访问日志 / 维护开关,避免用例互相污染。
"""
import copy
import json
import logging

import pytest
from fastapi.testclient import TestClient

import ch17_assignment as m
from ch17_assignment import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    app,
    handle_conflict,
    handle_not_found,
    handle_permission_denied,
)

client = TestClient(app)

SEED_PRODUCTS = {
    1: {"id": 1, "name": "机械键盘", "price": 599.0, "owner": "alice"},
    2: {"id": 2, "name": "无线鼠标", "price": 159.0, "owner": "alice"},
    3: {"id": 3, "name": "降噪耳机", "price": 1299.0, "owner": "bob"},
}


@pytest.fixture(autouse=True)
def reset_state():
    """每个用例开始前恢复种子商品、清空访问日志、关闭维护模式。"""
    m.PRODUCTS.clear()
    m.PRODUCTS.update(copy.deepcopy(SEED_PRODUCTS))
    m.REQUEST_LOG.clear()
    m.MAINTENANCE_MODE = False
    yield


# ---------- log_requests(访问日志 + 计时中间件 · §17.2)----------
class TestLogRequests:
    def test_process_time_header_added(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert "x-process-time-ms" in resp.headers  # headers 大小写不敏感

    def test_process_time_is_numeric_milliseconds(self):
        resp = client.get("/health")
        assert float(resp.headers["x-process-time-ms"]) >= 0

    def test_access_log_line_recorded(self):
        client.get("/health")
        assert m.REQUEST_LOG == ["GET /health -> 200"]

    def test_header_and_log_present_even_on_404(self):
        # 异常处理器在更内层:404 响应出来时仍穿过中间件(洋葱模型 §17.2)
        resp = client.get("/products/999")
        assert resp.status_code == 404
        assert "x-process-time-ms" in resp.headers
        assert m.REQUEST_LOG[-1] == "GET /products/999 -> 404"

    def test_every_request_appends_one_line(self):
        client.get("/health")
        client.get("/products/1")
        assert m.REQUEST_LOG == ["GET /health -> 200", "GET /products/1 -> 200"]


# ---------- maintenance_guard(短路中间件 · §17.3)----------
class TestMaintenanceGuard:
    def test_normal_when_maintenance_off(self):
        assert client.get("/health").status_code == 200

    def test_503_when_maintenance_on(self):
        m.MAINTENANCE_MODE = True
        resp = client.get("/products/1")
        assert resp.status_code == 503
        assert resp.json() == {"error": "Maintenance", "message": "系统维护中,请稍后重试"}

    def test_health_exempt_during_maintenance(self):
        # /health 保活:负载均衡器探活不能被维护模式挡掉
        m.MAINTENANCE_MODE = True
        assert client.get("/health").status_code == 200

    def test_short_circuits_inner_layers(self):
        # guard 比 log_requests 更外层:短路时访问日志/计时头都没有(§17.3 注册顺序)
        m.MAINTENANCE_MODE = True
        resp = client.get("/products/1")
        assert m.REQUEST_LOG == []
        assert "x-process-time-ms" not in resp.headers

    def test_recovers_after_maintenance_off(self):
        m.MAINTENANCE_MODE = True
        assert client.get("/products/1").status_code == 503
        m.MAINTENANCE_MODE = False
        assert client.get("/products/1").status_code == 200


# ---------- handle_not_found(NotFoundError → 404 · §17.4)----------
class TestHandleNotFound:
    def test_handler_direct_call(self):
        # 处理器就是普通函数,可直接单测(request 用不到,传 None)
        resp = handle_not_found(None, NotFoundError("商品", 9))  # type: ignore[arg-type]
        assert resp.status_code == 404
        assert json.loads(resp.body) == {"error": "NotFound", "message": "商品 9 不存在"}

    def test_get_missing_product_404_unified_format(self):
        resp = client.get("/products/999")
        assert resp.status_code == 404
        assert resp.json() == {"error": "NotFound", "message": "商品 999 不存在"}

    def test_delete_missing_product_404(self):
        resp = client.delete("/products/999", headers={"X-Username": "bob"})
        assert resp.status_code == 404
        assert resp.json()["error"] == "NotFound"

    def test_message_contains_resource_and_id(self):
        # 拦住硬编码 message 的实现:id 必须来自异常实例
        resp = client.get("/products/42")
        assert resp.json()["message"] == "商品 42 不存在"


# ---------- handle_permission_denied(PermissionDeniedError → 403 · §17.4)----------
class TestHandlePermissionDenied:
    def test_handler_direct_call(self):
        resp = handle_permission_denied(None, PermissionDeniedError("bob", "删除商品 1"))  # type: ignore[arg-type]
        assert resp.status_code == 403
        assert json.loads(resp.body) == {
            "error": "PermissionDenied",
            "message": "用户 bob 无权删除商品 1",
        }

    def test_delete_others_product_403(self):
        resp = client.delete("/products/1", headers={"X-Username": "bob"})
        assert resp.status_code == 403
        assert resp.json() == {"error": "PermissionDenied", "message": "用户 bob 无权删除商品 1"}

    def test_anonymous_user_403(self):
        resp = client.delete("/products/1")
        assert resp.status_code == 403
        assert resp.json()["message"] == "用户 匿名 无权删除商品 1"

    def test_forbidden_delete_does_not_mutate(self):
        client.delete("/products/1", headers={"X-Username": "bob"})
        assert 1 in m.PRODUCTS  # 403 短路,商品没被删


# ---------- handle_conflict(ConflictError → 409 · §17.4)----------
class TestHandleConflict:
    def test_handler_direct_call(self):
        resp = handle_conflict(None, ConflictError("商品", 1))  # type: ignore[arg-type]
        assert resp.status_code == 409
        assert json.loads(resp.body) == {"error": "Conflict", "message": "商品 1 已存在"}

    def test_duplicate_id_409(self):
        resp = client.post(
            "/products",
            json={"id": 1, "name": "机械键盘Pro", "price": 699, "owner": "alice"},
        )
        assert resp.status_code == 409
        assert resp.json() == {"error": "Conflict", "message": "商品 1 已存在"}

    def test_conflict_does_not_overwrite(self):
        client.post("/products", json={"id": 1, "name": "机械键盘Pro", "price": 699, "owner": "alice"})
        assert m.PRODUCTS[1]["name"] == "机械键盘"  # 原商品没被覆盖


# ---------- handle_unexpected(兜底 500 · §17.5)----------
class TestHandleUnexpected:
    def test_unhandled_exception_500_unified_format(self):
        # raise_server_exceptions=False:别重抛服务端异常,我要看 500 响应
        c = TestClient(app, raise_server_exceptions=False)
        resp = c.get("/boom")
        assert resp.status_code == 500
        assert resp.json() == {"error": "InternalServerError", "message": "服务内部错误,请稍后重试"}

    def test_response_does_not_leak_internals(self):
        c = TestClient(app, raise_server_exceptions=False)
        resp = c.get("/boom")
        assert "磁盘" not in resp.text  # 内部错误细节不外泄(§17.5)

    def test_exception_logged_with_traceback(self, caplog):
        c = TestClient(app, raise_server_exceptions=False)
        with caplog.at_level(logging.ERROR, logger="ch17"):
            c.get("/boom")
        assert "未处理异常" in caplog.text
        assert "Traceback" in caplog.text  # 堆栈进日志(exc_info=exc),不进响应
        assert "磁盘满了" in caplog.text


# ---------- get_product(抛 NotFoundError · §17.6)----------
class TestGetProduct:
    def test_get_existing_product(self):
        resp = client.get("/products/1")
        assert resp.status_code == 200
        assert resp.json() == {"id": 1, "name": "机械键盘", "price": 599.0, "owner": "alice"}

    def test_get_another_product(self):
        resp = client.get("/products/3")
        assert resp.status_code == 200
        assert resp.json()["name"] == "降噪耳机"
        assert resp.json()["owner"] == "bob"

    def test_missing_product_404(self):
        assert client.get("/products/999").status_code == 404

    def test_non_integer_id_422(self):
        # 路径参数类型校验(Ch15)照常工作,不走业务异常体系
        assert client.get("/products/abc").status_code == 422


# ---------- delete_product(404 vs 403 · §17.6)----------
class TestDeleteProduct:
    def test_owner_deletes_own_product(self):
        resp = client.delete("/products/3", headers={"X-Username": "bob"})
        assert resp.status_code == 200
        assert resp.json() == {"deleted": 3, "name": "降噪耳机"}

    def test_deleted_product_gone(self):
        client.delete("/products/3", headers={"X-Username": "bob"})
        assert 3 not in m.PRODUCTS
        assert client.get("/products/3").status_code == 404

    def test_others_product_403(self):
        assert client.delete("/products/1", headers={"X-Username": "bob"}).status_code == 403

    def test_missing_product_404(self):
        # 先 404 再 403:不存在的商品不暴露归属
        assert client.delete("/products/999", headers={"X-Username": "bob"}).status_code == 404

    def test_anonymous_403(self):
        assert client.delete("/products/1").status_code == 403


# ---------- create_product(409 冲突 · §17.6)----------
class TestCreateProduct:
    def test_create_returns_201_and_body(self):
        resp = client.post(
            "/products",
            json={"id": 4, "name": "显示器", "price": 899, "owner": "alice"},
        )
        assert resp.status_code == 201
        assert resp.json() == {"id": 4, "name": "显示器", "price": 899.0, "owner": "alice"}

    def test_created_can_be_fetched(self):
        client.post("/products", json={"id": 4, "name": "显示器", "price": 899, "owner": "alice"})
        assert client.get("/products/4").json()["name"] == "显示器"

    def test_duplicate_id_409(self):
        resp = client.post("/products", json={"id": 1, "name": "X", "price": 1, "owner": "alice"})
        assert resp.status_code == 409

    def test_invalid_price_422(self):
        resp = client.post("/products", json={"id": 4, "name": "显示器", "price": -1, "owner": "alice"})
        assert resp.status_code == 422

    def test_missing_owner_422(self):
        resp = client.post("/products", json={"id": 4, "name": "显示器", "price": 899})
        assert resp.status_code == 422


# ---------- CORS(脚手架验证 · §17.7)----------
class TestCorsConfig:
    def test_allowed_origin_gets_header(self):
        resp = client.get("/health", headers={"Origin": "http://localhost:5173"})
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_disallowed_origin_gets_no_header(self):
        resp = client.get("/health", headers={"Origin": "http://evil.com"})
        assert "access-control-allow-origin" not in resp.headers

    def test_preflight_options(self):
        # 预检请求(OPTIONS):浏览器发问「这个域名允许跨域吗」
        resp = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"
