"""
Ch16 作业测试。运行: uv run pytest 03_web_framework/ch16/test_ch16_assignment.py -v
"""
from fastapi.testclient import TestClient

from ch16_assignment import app

client = TestClient(app)


def auth(user: str = "alice") -> dict:
    """构造带合法 X-Token 的请求头。"""
    return {"X-Token": f"user-{user}"}


# ---------- 依赖 1:分页(类依赖)----------
class TestPaginationDep:
    def test_list_with_auth(self):
        resp = client.get("/products", headers=auth())
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["page"] == 1

    def test_pagination_size(self):
        resp = client.get("/products", params={"page": 1, "size": 2}, headers=auth())
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["size"] == 2

    def test_page2(self):
        resp = client.get("/products", params={"page": 2, "size": 2}, headers=auth())
        assert resp.json()["items"][0]["id"] == 3


# ---------- 依赖 2:当前用户(鉴权)----------
class TestAuthDep:
    def test_no_token_401(self):
        # 没有 X-Token 头 → 依赖抛 401
        assert client.get("/products").status_code == 401

    def test_invalid_token_401(self):
        resp = client.get("/products", headers={"X-Token": "invalid"})
        assert resp.status_code == 401

    def test_garbage_token_401(self):
        resp = client.get("/products", headers={"X-Token": "garbage"})
        assert resp.status_code == 401

    def test_user_injected_into_response(self):
        # 依赖返回的 user 被端点使用并返回
        resp = client.get("/products", headers=auth("bob"))
        assert resp.json()["user"] == "bob"

    def test_me_endpoint(self):
        assert client.get("/me", headers=auth("alice")).json() == {"user": "alice"}

    def test_me_no_token_401(self):
        # /me 也依赖 get_current_user,复用同一鉴权逻辑
        assert client.get("/me").status_code == 401


# ---------- 依赖 3:DB session(yield 依赖)----------
class TestYieldDep:
    def test_db_injected_and_usable(self):
        # 端点里 db["query_count"] += 1,说明 yield 依赖注入的 db 被正常使用
        resp = client.get("/products", headers=auth())
        assert resp.status_code == 200

    def test_yield_dep_runs_per_request(self):
        # 每次请求都重新跑 get_db(新 session,query_count 从 0 开始)
        client.get("/products", headers=auth())
        resp2 = client.get("/products", headers=auth())
        assert resp2.status_code == 200
