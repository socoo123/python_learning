"""
Ch19 作业测试。运行: uv run pytest 03_web_framework/ch19/test_ch19_assignment.py -v

测试隔离方案:用全局内存 engine(和 app 里同一个)。autouse fixture 在【每个 test 前】
create_all 建空表 → 在 test 里(或 seed fixture)插数据 → test 结束 drop_all 清空。
这样每个 test 看到的都是干净的表,互不影响。
"""
import pytest
from fastapi.testclient import TestClient

from ch19_assignment import Base, Product, SessionLocal, app, engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    """每个 test 前建空表,yield 跑测试,之后 drop_all 清空 → 测试间完全隔离。"""
    Base.metadata.drop_all(engine)     # 先清干净(防上个 test 残留)
    Base.metadata.create_all(engine)   # 建表
    yield
    Base.metadata.drop_all(engine)     # 收尾清空


def seed_products(rows: list[dict]) -> None:
    """直接用 SessionLocal 往库里塞数据(绕过 HTTP,准备测试前置数据)。"""
    with SessionLocal() as db:
        db.add_all([Product(**r) for r in rows])
        db.commit()


SAMPLE = [
    {"name": "机械键盘", "category": "电脑外设", "price": 599.0, "stock": 120},
    {"name": "无线鼠标", "category": "电脑外设", "price": 159.0, "stock": 300},
    {"name": "Python编程", "category": "图书", "price": 89.0, "stock": 500},
    {"name": "设计模式", "category": "图书", "price": 75.5, "stock": 200},
]


# ---------- 列表 + 过滤 ----------


class TestListProducts:
    def test_empty_when_no_data(self):
        resp = client.get("/products")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_all(self):
        seed_products(SAMPLE)
        resp = client.get("/products")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 4
        # 自增 id 从 1 开始
        assert data[0]["id"] == 1
        assert data[0]["name"] == "机械键盘"

    def test_filter_by_category(self):
        seed_products(SAMPLE)
        resp = client.get("/products", params={"category": "图书"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert all(p["category"] == "图书" for p in data)

    def test_filter_no_match_returns_empty(self):
        seed_products(SAMPLE)
        resp = client.get("/products", params={"category": "不存在的类目"})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_is_ordered_by_id(self):
        seed_products(SAMPLE)
        ids = [p["id"] for p in client.get("/products").json()]
        assert ids == sorted(ids)


# ---------- 创建 ----------


class TestCreateProduct:
    def test_create_returns_201_with_id(self):
        resp = client.post(
            "/products",
            json={"name": "降噪耳机", "category": "影音设备", "price": 1299.0, "stock": 80},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["id"] == 1
        assert body["name"] == "降噪耳机"

    def test_create_persists_and_queryable(self):
        client.post(
            "/products",
            json={"name": "蓝牙音箱", "category": "影音设备", "price": 399.0, "stock": 150},
        )
        lst = client.get("/products").json()
        assert len(lst) == 1
        assert lst[0]["name"] == "蓝牙音箱"

    def test_create_multiple_autoincrement(self):
        for r in SAMPLE:
            client.post("/products", json=r)
        ids = [p["id"] for p in client.get("/products").json()]
        assert ids == [1, 2, 3, 4]

    def test_create_missing_field_422(self):
        # Pydantic 校验:缺 price → 422
        resp = client.post("/products", json={"name": "x", "category": "y", "stock": 1})
        assert resp.status_code == 422


# ---------- 按主键查 + 404 ----------


class TestGetProduct:
    def test_get_existing(self):
        seed_products(SAMPLE)
        resp = client.get("/products/1")
        assert resp.status_code == 200
        assert resp.json()["name"] == "机械键盘"

    def test_get_not_found_returns_404(self):
        seed_products(SAMPLE)
        resp = client.get("/products/999")
        assert resp.status_code == 404
        assert "不存在" in resp.json()["detail"]

    def test_get_empty_db_404(self):
        resp = client.get("/products/1")
        assert resp.status_code == 404


# ---------- 删除 ----------


class TestDeleteProduct:
    def test_delete_existing(self):
        seed_products(SAMPLE)
        resp = client.delete("/products/1")
        assert resp.status_code == 200
        assert resp.json() == {"deleted": 1}

    def test_delete_actually_removes_row(self):
        seed_products(SAMPLE)
        client.delete("/products/2")
        lst = client.get("/products").json()
        assert len(lst) == 3
        assert all(p["id"] != 2 for p in lst)

    def test_delete_not_found_404(self):
        seed_products(SAMPLE)
        resp = client.delete("/products/999")
        assert resp.status_code == 404

    def test_delete_twice_second_404(self):
        seed_products(SAMPLE)
        assert client.delete("/products/1").status_code == 200
        assert client.delete("/products/1").status_code == 404
