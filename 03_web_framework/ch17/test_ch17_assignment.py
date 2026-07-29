"""
Ch17 作业测试。运行: uv run pytest 03_web_framework/ch17/test_ch17_assignment.py -v
"""
from fastapi.testclient import TestClient

from ch17_assignment import app

client = TestClient(app)


# ---------- 全局异常处理 ----------
class TestExceptionHandling:
    def test_not_found_mapped_to_404(self):
        # NotFoundError 被全局处理器映射成 404 + 统一格式
        resp = client.get("/products/999")
        assert resp.status_code == 404
        body = resp.json()
        assert body["error"] == "NotFound"
        assert "999" in body["message"]

    def test_existing_product_ok(self):
        resp = client.get("/products/1")
        assert resp.status_code == 200
        assert resp.json()["name"] == "机械键盘"

    def test_unhandled_exception_returns_500(self):
        # ValueError 没注册处理器 → 500。需关闭 TestClient 的「服务端异常重抛」
        c = TestClient(app, raise_server_exceptions=False)
        assert c.get("/error").status_code == 500


# ---------- 中间件 ----------
class TestMiddleware:
    def test_process_time_header_added(self):
        # log_requests 中间件给每个响应加 X-Process-Time-ms
        resp = client.get("/health")
        assert resp.status_code == 200
        # headers 大小写不敏感
        assert "x-process-time-ms" in resp.headers

    def test_middleware_runs_for_all_routes(self):
        resp1 = client.get("/health")
        resp2 = client.get("/products/1")
        assert "x-process-time-ms" in resp1.headers
        assert "x-process-time-ms" in resp2.headers


# ---------- CORS ----------
class TestCORS:
    def test_allow_origin_header(self):
        # 带 Origin 请求 → CORS 中间件加 Access-Control-Allow-Origin
        resp = client.get("/health", headers={"Origin": "http://example.com"})
        assert resp.headers.get("access-control-allow-origin") == "*"

    def test_cors_preflight(self):
        # 预检请求(OPTIONS)
        resp = client.options(
            "/health",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == "*"


# ---------- health ----------
class TestHealth:
    def test_health_ok(self):
        assert client.get("/health").json() == {"status": "ok"}
