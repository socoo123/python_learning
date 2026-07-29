"""
Ch14 作业测试。运行: uv run pytest 03_web_framework/ch14/test_ch14_assignment.py -v

用 FastAPI 的 TestClient(基于 httpx)测自己的 API,不用起服务。
"""
from fastapi.testclient import TestClient

from ch14_assignment import app

client = TestClient(app)


# ---------- list_products:GET /products ----------
class TestListProducts:
    def test_returns_list(self):
        resp = client.get("/products")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2     # 初始有 2 个

    def test_has_initial_products(self):
        names = [p["name"] for p in client.get("/products").json()]
        assert "机械键盘" in names
        assert "无线鼠标" in names

    def test_product_has_fields(self):
        first = client.get("/products").json()[0]
        assert {"id", "name", "price", "stock"} <= set(first.keys())


# ---------- create_product:POST /products ----------
class TestCreateProduct:
    def test_create_returns_201(self):
        resp = client.post("/products", json={"name": "新商品", "price": 100})
        assert resp.status_code == 201
        assert resp.json()["name"] == "新商品"

    def test_create_assigns_id(self):
        resp = client.post("/products", json={"name": "X", "price": 50})
        assert "id" in resp.json()
        assert isinstance(resp.json()["id"], int)

    def test_created_appears_in_list(self):
        resp = client.post("/products", json={"name": "可查商品", "price": 88})
        new_id = resp.json()["id"]
        # 能通过 GET 单个查到
        assert client.get(f"/products/{new_id}").status_code == 200

    def test_invalid_price_rejected(self):
        # price <= 0 违反 Field(gt=0),Pydantic 拒绝 → 422
        resp = client.post("/products", json={"name": "X", "price": -10})
        assert resp.status_code == 422

    def test_zero_price_rejected(self):
        resp = client.post("/products", json={"name": "X", "price": 0})
        assert resp.status_code == 422     # gt=0 不含 0

    def test_missing_name_rejected(self):
        resp = client.post("/products", json={"price": 10})
        assert resp.status_code == 422     # name 必填

    def test_default_stock(self):
        resp = client.post("/products", json={"name": "Y", "price": 10})
        assert resp.json()["stock"] == 0   # stock 默认 0


# ---------- get_product:GET /products/{id} ----------
class TestGetProduct:
    def test_get_existing(self):
        resp = client.get("/products/1")
        assert resp.status_code == 200
        assert resp.json()["name"] == "机械键盘"

    def test_get_missing_returns_404(self):
        resp = client.get("/products/99999")
        assert resp.status_code == 404
