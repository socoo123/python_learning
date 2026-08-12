"""
Ch19 作业测试。运行:

    uv sync --extra web
    uv run pytest 03_web_framework/ch19/test_ch19_assignment.py -v

测试隔离:autouse fixture 在每个 test 前 drop_all + create_all 建空表(SQLite 内存库
+ StaticPool,和应用共用同一个 engine),test 结束再 drop_all → 测试间完全隔离。
准备前置数据用 SessionLocal 直接写库(绕过 HTTP);关键断言也直接查库,
验证「真的写进去了」而不是「接口返回得好看」。
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from ch19_assignment import Base, Order, Product, SessionLocal, User, app, engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    """每个 test 前建空表,yield 跑测试,之后 drop_all 清空 → 测试间完全隔离。"""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


# ---------- 测试辅助:直接写/查库(绕过 HTTP)----------


def seed_products(rows: list[dict]) -> None:
    with SessionLocal() as db:
        db.add_all([Product(**r) for r in rows])
        db.commit()


def seed_users(rows: list[dict]) -> None:
    with SessionLocal() as db:
        db.add_all([User(**r) for r in rows])
        db.commit()


def count_orders() -> int:
    with SessionLocal() as db:
        return len(db.execute(select(Order)).scalars().all())


def get_product_row(product_id: int) -> Product | None:
    with SessionLocal() as db:
        return db.get(Product, product_id)


PRODUCTS = [
    {"name": "机械键盘", "category": "电脑外设", "price": 599.0, "stock": 120},  # id 1
    {"name": "无线鼠标", "category": "电脑外设", "price": 159.0, "stock": 300},  # id 2
    {"name": "Python编程", "category": "图书", "price": 89.0, "stock": 500},  # id 3
    {"name": "设计模式", "category": "图书", "price": 75.5, "stock": 200},  # id 4
    {"name": "重构", "category": "图书", "price": 99.0, "stock": 150},  # id 5
    {"name": "降噪耳机", "category": "影音设备", "price": 1299.0, "stock": 80},  # id 6
]

USERS = [
    {"name": "张三", "email": "zhangsan@example.com"},  # id 1
    {"name": "李四", "email": "lisi@example.com"},  # id 2
]


# ============================================================
# ① list_products:多条件过滤 + 分页
# ============================================================


class TestListProducts:
    def test_empty_db_returns_empty_list(self):
        resp = client.get("/products")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_all_ordered_by_id(self):
        seed_products(PRODUCTS)
        data = client.get("/products").json()
        assert [p["id"] for p in data] == [1, 2, 3, 4, 5, 6]
        assert data[0]["name"] == "机械键盘"
        assert data[3]["price"] == 75.5

    def test_filter_by_category(self):
        seed_products(PRODUCTS)
        data = client.get("/products", params={"category": "图书"}).json()
        assert [p["id"] for p in data] == [3, 4, 5]
        assert all(p["category"] == "图书" for p in data)

    def test_filter_category_no_match_returns_empty(self):
        seed_products(PRODUCTS)
        resp = client.get("/products", params={"category": "不存在的类目"})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_filter_min_price(self):
        seed_products(PRODUCTS)
        data = client.get("/products", params={"min_price": 100}).json()
        assert [p["id"] for p in data] == [1, 2, 6]  # 599 / 159 / 1299

    def test_filter_price_range(self):
        seed_products(PRODUCTS)
        data = client.get("/products", params={"min_price": 80, "max_price": 100}).json()
        assert [p["name"] for p in data] == ["Python编程", "重构"]  # 89 / 99(75.5 被下限排除)

    def test_combined_category_and_price_range(self):
        seed_products(PRODUCTS)
        data = client.get(
            "/products", params={"category": "图书", "min_price": 80, "max_price": 100}
        ).json()
        assert [p["id"] for p in data] == [3, 5]

    def test_pagination_pages(self):
        seed_products(PRODUCTS)
        page1 = client.get("/products", params={"size": 2, "page": 1}).json()
        page2 = client.get("/products", params={"size": 2, "page": 2}).json()
        page3 = client.get("/products", params={"size": 2, "page": 3}).json()
        assert [p["id"] for p in page1] == [1, 2]
        assert [p["id"] for p in page2] == [3, 4]
        assert [p["id"] for p in page3] == [5, 6]

    def test_page_beyond_returns_empty(self):
        seed_products(PRODUCTS)
        resp = client.get("/products", params={"size": 2, "page": 4})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_filter_with_pagination(self):
        seed_products(PRODUCTS)
        data = client.get("/products", params={"category": "图书", "size": 2, "page": 2}).json()
        assert [p["id"] for p in data] == [5]  # 图书 3 本的第 2 页只剩「重构」

    def test_invalid_pagination_params_422(self):
        assert client.get("/products", params={"page": 0}).status_code == 422
        assert client.get("/products", params={"size": 0}).status_code == 422
        assert client.get("/products", params={"size": 101}).status_code == 422


# ============================================================
# ② get_product:按主键查 + 404
# ============================================================


class TestGetProduct:
    def test_get_existing(self):
        seed_products(PRODUCTS)
        resp = client.get("/products/4")
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "设计模式"
        assert body["stock"] == 200

    def test_get_not_found_returns_404(self):
        seed_products(PRODUCTS)
        resp = client.get("/products/999")
        assert resp.status_code == 404
        assert "不存在" in resp.json()["detail"]

    def test_get_on_empty_db_returns_404(self):
        assert client.get("/products/1").status_code == 404


# ============================================================
# ③ create_product:add → commit → refresh
# ============================================================


class TestCreateProduct:
    def test_create_returns_201_with_id(self):
        resp = client.post(
            "/products",
            json={"name": "蓝牙音箱", "category": "影音设备", "price": 399.0, "stock": 150},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["id"] == 1
        assert body["name"] == "蓝牙音箱"
        assert body["price"] == 399.0

    def test_create_persists_and_queryable(self):
        client.post(
            "/products",
            json={"name": "蓝牙音箱", "category": "影音设备", "price": 399.0, "stock": 150},
        )
        lst = client.get("/products").json()
        assert len(lst) == 1
        assert lst[0]["name"] == "蓝牙音箱"

    def test_create_multiple_autoincrement_ids(self):
        for r in PRODUCTS[:3]:
            client.post("/products", json=r)
        ids = [p["id"] for p in client.get("/products").json()]
        assert ids == [1, 2, 3]

    def test_missing_field_returns_422(self):
        resp = client.post("/products", json={"name": "x", "category": "y", "stock": 1})
        assert resp.status_code == 422

    def test_negative_price_returns_422(self):
        resp = client.post(
            "/products",
            json={"name": "x", "category": "y", "price": -1, "stock": 1},
        )
        assert resp.status_code == 422

    def test_negative_stock_returns_422(self):
        resp = client.post(
            "/products",
            json={"name": "x", "category": "y", "price": 1, "stock": -5},
        )
        assert resp.status_code == 422


# ============================================================
# ④ update_product:脏检查 + commit
# ============================================================


class TestUpdateProduct:
    def test_update_returns_new_values_id_unchanged(self):
        seed_products(PRODUCTS)
        resp = client.put(
            "/products/1",
            json={"name": "机械键盘 Pro", "category": "电脑外设", "price": 499.0, "stock": 100},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == 1
        assert body["name"] == "机械键盘 Pro"
        assert body["price"] == 499.0
        assert body["stock"] == 100

    def test_update_actually_persists(self):
        seed_products(PRODUCTS)
        client.put(
            "/products/1",
            json={"name": "机械键盘 Pro", "category": "电脑外设", "price": 499.0, "stock": 100},
        )
        assert client.get("/products/1").json()["price"] == 499.0
        # 直接查库再验证一次(防「只在内存里改了」)
        assert get_product_row(1).price == 499.0

    def test_update_not_found_returns_404(self):
        seed_products(PRODUCTS)
        resp = client.put(
            "/products/999",
            json={"name": "x", "category": "y", "price": 1, "stock": 1},
        )
        assert resp.status_code == 404

    def test_update_invalid_body_returns_422(self):
        seed_products(PRODUCTS)
        resp = client.put(
            "/products/1",
            json={"name": "x", "category": "y", "price": -5, "stock": 1},
        )
        assert resp.status_code == 422


# ============================================================
# ⑤ delete_product:delete + commit
# ============================================================


class TestDeleteProduct:
    def test_delete_existing(self):
        seed_products(PRODUCTS)
        resp = client.delete("/products/1")
        assert resp.status_code == 200
        assert resp.json() == {"deleted": 1}

    def test_delete_actually_removes_row(self):
        seed_products(PRODUCTS)
        client.delete("/products/2")
        lst = client.get("/products").json()
        assert len(lst) == 5
        assert all(p["id"] != 2 for p in lst)

    def test_delete_not_found_returns_404(self):
        seed_products(PRODUCTS)
        assert client.delete("/products/999").status_code == 404

    def test_delete_twice_second_returns_404(self):
        seed_products(PRODUCTS)
        assert client.delete("/products/1").status_code == 200
        assert client.delete("/products/1").status_code == 404


# ============================================================
# ⑥ register_user:唯一性检查 + 409
# ============================================================


class TestRegisterUser:
    def test_register_returns_201_with_id(self):
        resp = client.post("/users", json={"name": "张三", "email": "zhangsan@example.com"})
        assert resp.status_code == 201
        body = resp.json()
        assert body["id"] == 1
        assert body["name"] == "张三"
        assert body["email"] == "zhangsan@example.com"

    def test_register_actually_persists(self):
        client.post("/users", json={"name": "张三", "email": "zhangsan@example.com"})
        with SessionLocal() as db:
            u = db.get(User, 1)
            assert u is not None
            assert u.email == "zhangsan@example.com"

    def test_duplicate_email_returns_409(self):
        client.post("/users", json={"name": "张三", "email": "zhangsan@example.com"})
        resp = client.post("/users", json={"name": "张三丰", "email": "zhangsan@example.com"})
        assert resp.status_code == 409
        assert "邮箱" in resp.json()["detail"]

    def test_same_name_different_email_ok(self):
        client.post("/users", json={"name": "张三", "email": "zhangsan@example.com"})
        resp = client.post("/users", json={"name": "张三", "email": "zs@example.com"})
        assert resp.status_code == 201

    def test_missing_email_returns_422(self):
        assert client.post("/users", json={"name": "张三"}).status_code == 422


# ============================================================
# ⑦ place_order:校验 → 扣库存 → 写订单(事务原子性)
# ============================================================


class TestPlaceOrder:
    def test_place_order_returns_201_with_computed_total(self):
        seed_users(USERS)
        seed_products(PRODUCTS)
        resp = client.post("/orders", json={"user_id": 1, "product_id": 4, "quantity": 2})
        assert resp.status_code == 201
        body = resp.json()
        assert body["id"] == 1
        assert body["user_id"] == 1
        assert body["product_id"] == 4
        assert body["quantity"] == 2
        assert body["total_price"] == 151.0  # 75.5 × 2
        assert body["status"] == "created"

    def test_place_order_deducts_stock(self):
        seed_users(USERS)
        seed_products(PRODUCTS)
        client.post("/orders", json={"user_id": 1, "product_id": 4, "quantity": 2})
        assert client.get("/products/4").json()["stock"] == 198  # 200 - 2
        # 直接查库再验证一次
        assert get_product_row(4).stock == 198

    def test_place_order_persists_order_row(self):
        seed_users(USERS)
        seed_products(PRODUCTS)
        client.post("/orders", json={"user_id": 1, "product_id": 3, "quantity": 3})
        assert count_orders() == 1
        with SessionLocal() as db:
            o = db.get(Order, 1)
            assert o.total_price == 267.0  # 89.0 × 3
            assert o.user_id == 1

    def test_insufficient_stock_returns_400_and_writes_nothing(self):
        """原子性:库存不足 → 400,且库存不变、订单表无新行(commit 前抛异常 = 全没发生)。"""
        seed_users(USERS)
        seed_products(PRODUCTS)
        resp = client.post("/orders", json={"user_id": 1, "product_id": 6, "quantity": 81})
        assert resp.status_code == 400
        assert "库存" in resp.json()["detail"]
        assert get_product_row(6).stock == 80  # 库存没动
        assert count_orders() == 0  # 订单没写

    def test_user_not_found_returns_404(self):
        seed_products(PRODUCTS)
        resp = client.post("/orders", json={"user_id": 999, "product_id": 1, "quantity": 1})
        assert resp.status_code == 404

    def test_product_not_found_returns_404(self):
        seed_users(USERS)
        resp = client.post("/orders", json={"user_id": 1, "product_id": 999, "quantity": 1})
        assert resp.status_code == 404

    def test_zero_quantity_returns_422(self):
        seed_users(USERS)
        seed_products(PRODUCTS)
        resp = client.post("/orders", json={"user_id": 1, "product_id": 1, "quantity": 0})
        assert resp.status_code == 422


# ============================================================
# ⑧ list_user_orders:join 关联查询
# ============================================================


class TestListUserOrders:
    def test_returns_orders_with_product_name(self):
        seed_users(USERS)
        seed_products(PRODUCTS)
        client.post("/orders", json={"user_id": 1, "product_id": 4, "quantity": 2})
        client.post("/orders", json={"user_id": 1, "product_id": 3, "quantity": 1})
        resp = client.get("/users/1/orders")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        # 按订单 id 升序;商品名来自 join products 表(不是冗余存的)
        assert data[0] == {
            "order_id": 1,
            "product_id": 4,
            "product_name": "设计模式",
            "quantity": 2,
            "total_price": 151.0,
            "status": "created",
        }
        assert data[1]["product_name"] == "Python编程"
        assert data[1]["total_price"] == 89.0

    def test_orders_isolated_between_users(self):
        seed_users(USERS)
        seed_products(PRODUCTS)
        client.post("/orders", json={"user_id": 1, "product_id": 4, "quantity": 1})
        client.post("/orders", json={"user_id": 2, "product_id": 1, "quantity": 1})
        data1 = client.get("/users/1/orders").json()
        data2 = client.get("/users/2/orders").json()
        assert [o["product_name"] for o in data1] == ["设计模式"]
        assert [o["product_name"] for o in data2] == ["机械键盘"]

    def test_user_without_orders_returns_empty(self):
        seed_users(USERS)
        resp = client.get("/users/2/orders")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_user_not_found_returns_404(self):
        seed_users(USERS)
        resp = client.get("/users/999/orders")
        assert resp.status_code == 404
        assert "用户" in resp.json()["detail"]

    def test_reflects_stock_after_multiple_orders(self):
        """连续下单:库存连续扣减,两单都可见(验证事务各自完整提交)。"""
        seed_users(USERS)
        seed_products(PRODUCTS)
        client.post("/orders", json={"user_id": 1, "product_id": 4, "quantity": 50})
        client.post("/orders", json={"user_id": 2, "product_id": 4, "quantity": 50})
        assert get_product_row(4).stock == 100  # 200 - 50 - 50
        assert len(client.get("/users/1/orders").json()) == 1
        assert len(client.get("/users/2/orders").json()) == 1
