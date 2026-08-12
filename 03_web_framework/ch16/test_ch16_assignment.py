"""
Ch16 作业测试。运行:

    uv sync --extra web
    uv run pytest 03_web_framework/ch16/test_ch16_assignment.py -v

依赖函数直接单测(它们就是普通函数);端点用 TestClient 发真 HTTP 语义请求。
每例前重置订单 / 自增 id / DB 审计日志,避免用例互相污染。
"""
import copy
import inspect

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import ch16_assignment as m
from ch16_assignment import (
    app,
    get_current_user,
    get_db,
    get_pagination,
    require_admin,
)

client = TestClient(app)

SEED_ORDERS = [
    {"id": 1, "username": "alice", "item": "机械键盘", "amount": 599.0, "status": "paid"},
    {"id": 2, "username": "alice", "item": "无线鼠标", "amount": 159.0, "status": "shipped"},
    {"id": 3, "username": "bob", "item": "设计模式", "amount": 75.5, "status": "paid"},
    {"id": 4, "username": "bob", "item": "降噪耳机", "amount": 1299.0, "status": "pending"},
    {"id": 5, "username": "alice", "item": "Python编程", "amount": 89.0, "status": "paid"},
]


@pytest.fixture(autouse=True)
def reset_state():
    """每个用例开始前恢复种子订单、自增 id 与审计日志。"""
    m.ORDERS.clear()
    m.ORDERS.extend(copy.deepcopy(SEED_ORDERS))
    m._next_order_id = 6
    m.DB_AUDIT.clear()
    yield


def auth(token: str = "tok-alice") -> dict:
    """构造带合法 X-Token 的请求头。"""
    return {"X-Token": token}


# ---------- get_db(yield 依赖)----------
class TestGetDb:
    def test_session_opened_and_closed_per_request(self):
        client.get("/orders", headers=auth())
        assert m.DB_AUDIT == ["open", "close"]

    def test_close_runs_even_when_endpoint_raises_404(self):
        # yield 依赖的核心卖点:端点抛异常,finally 清理照样执行(§16.2)
        client.get("/orders/99999", headers=auth())
        assert m.DB_AUDIT == ["open", "close"]

    def test_new_session_per_request_not_singleton(self):
        client.get("/orders", headers=auth())
        client.get("/orders", headers=auth())
        assert m.DB_AUDIT == ["open", "close", "open", "close"]

    def test_dependency_is_generator_function(self):
        # 写成 return 而不是 yield:值能用但没清理钩子,这里直接拦住
        assert inspect.isgeneratorfunction(get_db)


# ---------- get_current_user(Header 鉴权依赖)----------
class TestGetCurrentUser:
    def test_valid_token_returns_user_dict(self):
        assert get_current_user(x_token="tok-alice") == {"username": "alice", "role": "user"}
        assert get_current_user(x_token="tok-bob") == {"username": "bob", "role": "user"}

    def test_admin_token_returns_admin_role(self):
        assert get_current_user(x_token="tok-admin") == {"username": "admin", "role": "admin"}

    def test_missing_token_raises_401(self):
        with pytest.raises(HTTPException) as exc:
            get_current_user(x_token=None)
        assert exc.value.status_code == 401

    def test_unknown_token_raises_401(self):
        with pytest.raises(HTTPException) as exc:
            get_current_user(x_token="garbage")
        assert exc.value.status_code == 401

    def test_short_circuits_endpoint(self):
        # 依赖抛 401 → 端点函数体不执行(§16.3 短路)
        assert client.get("/orders").status_code == 401
        assert client.get("/orders", headers={"X-Token": "garbage"}).status_code == 401


# ---------- get_pagination(类依赖)----------
class TestGetPagination:
    def test_builds_pagination_object(self):
        p = get_pagination(page=2, size=3)
        assert (p.page, p.size, p.offset) == (2, 3, 3)

    def test_first_page_offset_is_zero(self):
        p = get_pagination(page=1, size=10)
        assert p.offset == 0

    def test_page_zero_rejected_422(self):
        # 签名里的 Query(ge=1) 校验:非法分页框架直接 422
        assert client.get("/orders", params={"page": 0}, headers=auth()).status_code == 422

    def test_size_over_100_rejected_422(self):
        assert client.get("/orders", params={"size": 101}, headers=auth()).status_code == 422

    def test_negative_size_rejected_422(self):
        assert client.get("/orders", params={"size": -5}, headers=auth()).status_code == 422


# ---------- require_admin(嵌套依赖)----------
class TestRequireAdmin:
    def test_admin_passes_and_returns_user(self):
        user = {"username": "admin", "role": "admin"}
        assert require_admin(user=user) == user

    def test_normal_user_raises_403(self):
        with pytest.raises(HTTPException) as exc:
            require_admin(user={"username": "alice", "role": "user"})
        assert exc.value.status_code == 403

    def test_via_endpoint_admin_200(self):
        assert client.get("/admin/stats", headers=auth("tok-admin")).status_code == 200

    def test_via_endpoint_user_403(self):
        assert client.get("/admin/stats", headers=auth("tok-alice")).status_code == 403

    def test_via_endpoint_no_token_401_not_403(self):
        # 嵌套链:上游 get_current_user 先短路 → 401 而非 403(§16.5)
        assert client.get("/admin/stats").status_code == 401


# ---------- list_orders(注入三依赖:过滤 + 分页)----------
class TestListOrders:
    def test_alice_sees_only_her_orders(self):
        data = client.get("/orders", headers=auth("tok-alice")).json()
        assert data["total"] == 3
        assert {o["id"] for o in data["items"]} == {1, 2, 5}

    def test_bob_sees_only_his_orders(self):
        # 拦住「不过滤直接返回全部」的水平越权实现
        data = client.get("/orders", headers=auth("tok-bob")).json()
        assert data["total"] == 2
        assert {o["id"] for o in data["items"]} == {3, 4}

    def test_pagination_first_page(self):
        data = client.get("/orders", params={"page": 1, "size": 2}, headers=auth()).json()
        assert [o["id"] for o in data["items"]] == [1, 2]
        assert data["page"] == 1
        assert data["size"] == 2
        assert data["total"] == 3  # total 是过滤后总数,不是本页条数

    def test_pagination_second_page(self):
        data = client.get("/orders", params={"page": 2, "size": 2}, headers=auth()).json()
        assert [o["id"] for o in data["items"]] == [5]

    def test_page_beyond_range_returns_empty_items(self):
        data = client.get("/orders", params={"page": 99, "size": 10}, headers=auth()).json()
        assert data["items"] == []
        assert data["total"] == 3

    def test_no_token_401(self):
        assert client.get("/orders").status_code == 401


# ---------- get_order(404 vs 403)----------
class TestGetOrder:
    def test_get_own_order(self):
        resp = client.get("/orders/1", headers=auth("tok-alice"))
        assert resp.status_code == 200
        assert resp.json()["item"] == "机械键盘"
        assert resp.json()["amount"] == 599.0

    def test_get_own_order_bob(self):
        resp = client.get("/orders/4", headers=auth("tok-bob"))
        assert resp.status_code == 200
        assert resp.json()["item"] == "降噪耳机"

    def test_others_order_403(self):
        # 订单存在但属于别人 → 403(不是 404,也不是 200)
        resp = client.get("/orders/1", headers=auth("tok-bob"))
        assert resp.status_code == 403

    def test_missing_order_404(self):
        resp = client.get("/orders/99999", headers=auth())
        assert resp.status_code == 404
        assert resp.json()["detail"] == "订单不存在"

    def test_no_token_401(self):
        assert client.get("/orders/1").status_code == 401


# ---------- create_order(POST + session 写入)----------
class TestCreateOrder:
    def test_create_returns_201_and_body(self):
        resp = client.post("/orders", json={"item": "显示器", "amount": 899}, headers=auth("tok-bob"))
        assert resp.status_code == 201
        assert resp.json() == {
            "id": 6,
            "username": "bob",
            "item": "显示器",
            "amount": 899.0,
            "status": "pending",
        }

    def test_created_appears_in_my_list(self):
        client.post("/orders", json={"item": "显示器", "amount": 899}, headers=auth("tok-bob"))
        data = client.get("/orders", headers=auth("tok-bob")).json()
        assert data["total"] == 3
        assert any(o["item"] == "显示器" for o in data["items"])

    def test_created_not_visible_to_others(self):
        client.post("/orders", json={"item": "显示器", "amount": 899}, headers=auth("tok-bob"))
        data = client.get("/orders", headers=auth("tok-alice")).json()
        assert data["total"] == 3  # alice 还是自己的 3 单

    def test_ids_increment(self):
        a = client.post("/orders", json={"item": "A", "amount": 1}, headers=auth()).json()["id"]
        b = client.post("/orders", json={"item": "B", "amount": 2}, headers=auth()).json()["id"]
        assert b == a + 1

    def test_invalid_amount_422(self):
        resp = client.post("/orders", json={"item": "X", "amount": -1}, headers=auth())
        assert resp.status_code == 422

    def test_empty_item_422(self):
        resp = client.post("/orders", json={"item": "", "amount": 10}, headers=auth())
        assert resp.status_code == 422

    def test_no_token_401_and_nothing_written(self):
        resp = client.post("/orders", json={"item": "X", "amount": 10})
        assert resp.status_code == 401
        assert len(m.ORDERS) == 5  # 依赖短路:没有写入


# ---------- admin_stats(综合:admin 依赖 + 全站统计)----------
class TestAdminStats:
    def test_seed_stats(self):
        resp = client.get("/admin/stats", headers=auth("tok-admin"))
        assert resp.status_code == 200
        assert resp.json() == {
            "total_orders": 5,
            "total_amount": 2221.5,
            "by_status": {"paid": 3, "shipped": 1, "pending": 1},
        }

    def test_stats_change_after_new_order(self):
        client.post("/orders", json={"item": "显示器", "amount": 899}, headers=auth("tok-bob"))
        stats = client.get("/admin/stats", headers=auth("tok-admin")).json()
        assert stats["total_orders"] == 6
        assert stats["total_amount"] == 3120.5
        assert stats["by_status"]["pending"] == 2

    def test_user_forbidden_403(self):
        assert client.get("/admin/stats", headers=auth("tok-alice")).status_code == 403

    def test_no_token_401(self):
        assert client.get("/admin/stats").status_code == 401
