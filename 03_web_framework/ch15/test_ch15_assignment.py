"""
Ch15 作业测试。运行:

    uv sync --extra web
    uv run pytest 03_web_framework/ch15/test_ch15_assignment.py -v

用 FastAPI TestClient 测 API;每例前重置订单数据与自增 id,避免用例互相污染。
"""
import pytest
from fastapi.testclient import TestClient

import ch15_assignment as m
from ch15_assignment import app, register_system_router

client = TestClient(app)

SEED_ORDERS = [o.model_copy(deep=True) for o in m.ORDERS]


@pytest.fixture(autouse=True)
def reset_orders():
    """每个用例开始前恢复 12 条种子订单与自增 id(create_order 会改状态)。"""
    m.ORDERS[:] = [o.model_copy(deep=True) for o in SEED_ORDERS]
    m._next_order_id = 13
    yield


# ---------- list_products:可选查询参数筛选 ----------
class TestListProducts:
    def test_no_filter_returns_all(self):
        resp = client.get("/products")
        assert resp.status_code == 200
        assert len(resp.json()) == 10

    def test_filter_by_category(self):
        data = client.get("/products", params={"category": "电脑外设"}).json()
        assert len(data) == 4
        assert {p["name"] for p in data} == {"机械键盘", "无线鼠标", "27寸4K显示器", "USB-C扩展坞"}

    def test_filter_by_min_price(self):
        data = client.get("/products", params={"min_price": 500}).json()
        assert {p["name"] for p in data} == {"机械键盘", "27寸4K显示器", "降噪耳机", "人体工学椅"}

    def test_filter_by_max_price(self):
        data = client.get("/products", params={"max_price": 200}).json()
        assert {p["name"] for p in data} == {"无线鼠标", "Python编程:从入门到实践", "设计模式", "智能水杯"}

    def test_filter_combined_price_band(self):
        # 电脑外设 且 500~1500:只剩机械键盘 599(显示器 2199 超上限,鼠标/扩展坞低于下限)
        data = client.get(
            "/products", params={"category": "电脑外设", "min_price": 500, "max_price": 1500}
        ).json()
        assert [p["name"] for p in data] == ["机械键盘"]

    def test_min_price_boundary_inclusive(self):
        # min_price=159 必须包含无线鼠标 159(>= 语义);共 8 件 >= 159
        data = client.get("/products", params={"min_price": 159}).json()
        assert len(data) == 8
        assert "无线鼠标" in {p["name"] for p in data}

    def test_max_price_boundary_inclusive(self):
        # max_price=75.5 只含设计模式(<= 语义)
        data = client.get("/products", params={"max_price": 75.5}).json()
        assert [p["name"] for p in data] == ["设计模式"]

    def test_no_match_returns_empty(self):
        assert client.get("/products", params={"category": "不存在"}).json() == []


# ---------- search_products:Query 校验 ----------
class TestSearchProducts:
    def test_search_by_name(self):
        data = client.get("/products/search", params={"q": "键盘"}).json()
        assert [p["name"] for p in data] == ["机械键盘"]

    def test_search_by_category_keyword(self):
        # 「影音」命中类目「影音设备」:降噪耳机 + 蓝牙音箱
        data = client.get("/products/search", params={"q": "影音"}).json()
        assert {p["name"] for p in data} == {"降噪耳机", "蓝牙音箱"}

    def test_limit_truncates_results(self):
        # 「电脑外设」命中 4 件,limit=2 截断到 2 件
        data = client.get("/products/search", params={"q": "电脑外设", "limit": 2}).json()
        assert len(data) == 2

    def test_query_too_short_rejected(self):
        # 「机」只有 1 个字符,过不了 min_length=2
        assert client.get("/products/search", params={"q": "机"}).status_code == 422

    def test_missing_query_rejected(self):
        assert client.get("/products/search").status_code == 422

    def test_limit_out_of_range_rejected(self):
        assert client.get("/products/search", params={"q": "键盘", "limit": 0}).status_code == 422
        assert client.get("/products/search", params={"q": "键盘", "limit": 51}).status_code == 422

    def test_no_match_returns_empty(self):
        assert client.get("/products/search", params={"q": "冰箱"}).json() == []


# ---------- list_product_ranking:Literal 白名单排序 ----------
class TestListProductRanking:
    def test_default_price_asc_top5(self):
        data = client.get("/products/ranking").json()
        assert [p["id"] for p in data] == [5, 4, 2, 9, 8]  # 75.5/89/159/199/269

    def test_price_desc_top3(self):
        data = client.get(
            "/products/ranking", params={"sort_by": "price", "order": "desc", "limit": 3}
        ).json()
        assert [p["id"] for p in data] == [3, 10, 6]  # 2199/1599/1299

    def test_stock_desc_top1(self):
        data = client.get(
            "/products/ranking", params={"sort_by": "stock", "order": "desc", "limit": 1}
        ).json()
        assert [p["name"] for p in data] == ["Python编程:从入门到实践"]  # stock=500

    def test_stock_asc_top1_is_out_of_stock_item(self):
        data = client.get(
            "/products/ranking", params={"sort_by": "stock", "order": "asc", "limit": 1}
        ).json()
        assert [p["name"] for p in data] == ["智能水杯"]  # stock=0

    def test_invalid_sort_by_rejected(self):
        assert client.get("/products/ranking", params={"sort_by": "name"}).status_code == 422

    def test_invalid_order_rejected(self):
        assert client.get("/products/ranking", params={"order": "up"}).status_code == 422

    def test_limit_out_of_range_rejected(self):
        assert client.get("/products/ranking", params={"limit": 0}).status_code == 422
        assert client.get("/products/ranking", params={"limit": 21}).status_code == 422


# ---------- get_product:路径参数 + Path 校验 ----------
class TestGetProduct:
    def test_get_existing(self):
        resp = client.get("/products/1")
        assert resp.status_code == 200
        assert resp.json()["name"] == "机械键盘"
        assert resp.json()["sku"] == "KB-001"

    def test_get_last_product(self):
        resp = client.get("/products/10")
        assert resp.status_code == 200
        assert resp.json()["name"] == "人体工学椅"

    def test_missing_returns_404(self):
        resp = client.get("/products/999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "商品不存在"

    def test_non_int_id_rejected(self):
        assert client.get("/products/abc").status_code == 422

    def test_zero_id_rejected_by_path_constraint(self):
        assert client.get("/products/0").status_code == 422

    def test_negative_id_rejected_by_path_constraint(self):
        assert client.get("/products/-1").status_code == 422


# ---------- list_orders:分页 + 元信息 ----------
class TestListOrders:
    def test_default_first_page(self):
        resp = client.get("/orders")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 10
        assert body["items"][0]["id"] == 1
        assert body["total"] == 12
        assert body["page"] == 1
        assert body["size"] == 10
        assert body["pages"] == 2

    def test_second_page_has_remaining_two(self):
        body = client.get("/orders", params={"page": 2}).json()
        assert [o["id"] for o in body["items"]] == [11, 12]
        assert body["pages"] == 2

    def test_beyond_last_page_returns_empty_items(self):
        body = client.get("/orders", params={"page": 99}).json()
        assert body["items"] == []
        assert body["total"] == 12  # 越界是空页,不是 404,元信息照常

    def test_custom_page_size(self):
        body = client.get("/orders", params={"size": 5, "page": 3}).json()
        assert [o["id"] for o in body["items"]] == [11, 12]
        assert body["pages"] == 3  # 12 条 / 每页 5 → 3 页

    def test_page_zero_rejected(self):
        assert client.get("/orders", params={"page": 0}).status_code == 422

    def test_size_zero_rejected(self):
        assert client.get("/orders", params={"size": 0}).status_code == 422

    def test_size_too_large_rejected(self):
        assert client.get("/orders", params={"size": 101}).status_code == 422


# ---------- create_order:嵌套请求体 + 业务校验 ----------
class TestCreateOrder:
    def test_create_returns_201_with_snapshot(self):
        resp = client.post(
            "/orders",
            json={
                "customer": "张三",
                "items": [
                    {"product_id": 1, "quantity": 2},
                    {"product_id": 4, "quantity": 1},
                ],
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["id"] == 13
        assert body["customer"] == "张三"
        assert body["status"] == "pending"
        assert body["total"] == 1287.0  # 599*2 + 89
        assert body["items"][0]["name"] == "机械键盘"
        assert body["items"][0]["unit_price"] == 599.0
        assert body["items"][0]["subtotal"] == 1198.0
        assert body["items"][1]["subtotal"] == 89.0

    def test_created_order_appears_in_list(self):
        client.post(
            "/orders",
            json={"customer": "李四", "items": [{"product_id": 2, "quantity": 1}]},
        )
        body = client.get("/orders").json()
        assert body["total"] == 13
        assert body["pages"] == 2

    def test_ids_increment(self):
        a = client.post(
            "/orders", json={"customer": "A", "items": [{"product_id": 2, "quantity": 1}]}
        ).json()["id"]
        b = client.post(
            "/orders", json={"customer": "B", "items": [{"product_id": 2, "quantity": 1}]}
        ).json()["id"]
        assert (a, b) == (13, 14)

    def test_unknown_product_returns_404(self):
        resp = client.post(
            "/orders",
            json={"customer": "李四", "items": [{"product_id": 999, "quantity": 1}]},
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "商品不存在: 999"

    def test_insufficient_stock_returns_400(self):
        # 智能水杯 stock=0,买 1 件也不够
        resp = client.post(
            "/orders",
            json={"customer": "李四", "items": [{"product_id": 9, "quantity": 1}]},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "库存不足: 智能水杯"

    def test_stock_exactly_enough_allowed(self):
        # 人体工学椅 stock=30,买 30 件:边界允许(stock < quantity 才拒绝)
        resp = client.post(
            "/orders",
            json={"customer": "王五", "items": [{"product_id": 10, "quantity": 30}]},
        )
        assert resp.status_code == 201
        assert resp.json()["total"] == 1599.0 * 30

    def test_stock_one_short_returns_400(self):
        # 人体工学椅 stock=30,买 31 件:越界拒绝
        resp = client.post(
            "/orders",
            json={"customer": "王五", "items": [{"product_id": 10, "quantity": 31}]},
        )
        assert resp.status_code == 400

    def test_zero_quantity_rejected_by_framework(self):
        resp = client.post(
            "/orders",
            json={"customer": "李四", "items": [{"product_id": 1, "quantity": 0}]},
        )
        assert resp.status_code == 422

    def test_empty_items_rejected_by_framework(self):
        resp = client.post("/orders", json={"customer": "李四", "items": []})
        assert resp.status_code == 422

    def test_blank_customer_rejected_by_framework(self):
        resp = client.post(
            "/orders",
            json={"customer": "", "items": [{"product_id": 1, "quantity": 1}]},
        )
        assert resp.status_code == 422


# ---------- register_system_router:APIRouter 分组 ----------
class TestRegisterSystemRouter:
    def test_not_registered_by_default(self):
        # 注意:本用例必须跑在类内其他用例之前(它们会真正注册)
        assert client.get("/system/health").status_code == 404

    def test_health_available_after_register(self):
        register_system_router()
        resp = client.get("/system/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_info_available_after_register(self):
        register_system_router()
        resp = client.get("/system/info")
        assert resp.status_code == 200
        assert resp.json() == {"service": "极客商城", "version": "2.0"}
