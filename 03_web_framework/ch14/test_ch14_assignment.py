"""
Ch14 作业测试。运行:

    uv sync --extra web
    uv run pytest 03_web_framework/ch14/test_ch14_assignment.py -v

用 FastAPI TestClient 测 API;每例前重置内存仓库,避免用例互相污染。
"""
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

import ch14_assignment as m
from ch14_assignment import Product, ProductCreate, app, build_product_from_create

client = TestClient(app)

SEED = {
    1: Product(id=1, name="机械键盘", category="电脑外设", price=599.0, stock=120, sku="KB-001"),
    2: Product(id=2, name="无线鼠标", category="电脑外设", price=159.0, stock=300, sku="MS-002"),
    3: Product(id=3, name="设计模式", category="图书", price=75.5, stock=200, sku="BK-005"),
    4: Product(id=4, name="智能水杯", category="生活用品", price=199.0, stock=0, sku="CP-009"),
}


@pytest.fixture(autouse=True)
def reset_store():
    """每个用例开始前恢复种子数据与自增 id(端点会改全局状态,不重置会互相污染)。"""
    m.PRODUCTS.clear()
    m.PRODUCTS.update({k: v.model_copy() for k, v in SEED.items()})
    m._next_id = 5
    yield


# ---------- ProductCreate 模型(字段约束)----------
class TestProductCreate:
    def test_accepts_valid_payload(self):
        p = ProductCreate(name="机械键盘", category="电脑外设", price=599.0, stock=120, sku="KB-001")
        assert p.name == "机械键盘"
        assert p.category == "电脑外设"
        assert p.price == 599.0
        assert p.stock == 120
        assert p.sku == "KB-001"

    def test_stock_defaults_to_zero(self):
        p = ProductCreate(name="试用装", category="生活用品", price=1.0, sku="TS-001")
        assert p.stock == 0

    def test_string_price_is_coerced(self):
        # lax 模式:字符串 "599" 会被强转成 float(§14.2 coercion)
        p = ProductCreate(name="X", category="图书", price="599", sku="KB-001")
        assert p.price == 599.0
        assert isinstance(p.price, float)

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            ProductCreate(name="", category="图书", price=10, sku="KB-001")

    def test_too_long_name_rejected(self):
        with pytest.raises(ValidationError):
            ProductCreate(name="好" * 51, category="图书", price=10, sku="KB-001")

    def test_zero_price_rejected(self):
        with pytest.raises(ValidationError):
            ProductCreate(name="X", category="图书", price=0, sku="KB-001")

    def test_negative_stock_rejected(self):
        with pytest.raises(ValidationError):
            ProductCreate(name="X", category="图书", price=10, stock=-1, sku="KB-001")

    def test_bad_sku_rejected(self):
        with pytest.raises(ValidationError):
            ProductCreate(name="X", category="图书", price=10, sku="kb-001")

    def test_missing_category_rejected(self):
        with pytest.raises(ValidationError):
            ProductCreate(name="X", price=10, sku="KB-001")

    def test_non_numeric_price_rejected(self):
        with pytest.raises(ValidationError):
            ProductCreate(name="X", category="图书", price="abc", sku="KB-001")


# ---------- build_product_from_create ----------
class TestBuildProductFromCreate:
    def test_copies_fields_and_sets_id(self):
        data = ProductCreate(name="键盘", category="电脑外设", price=599, stock=10, sku="KB-001")
        product = build_product_from_create(7, data)
        assert product == Product(id=7, name="键盘", category="电脑外设", price=599.0, stock=10, sku="KB-001")

    def test_does_not_mutate_request_model(self):
        data = ProductCreate(name="鼠标", category="电脑外设", price=159, stock=1, sku="MS-002")
        build_product_from_create(1, data)
        assert data.model_dump() == {
            "name": "鼠标",
            "category": "电脑外设",
            "price": 159.0,
            "stock": 1,
            "sku": "MS-002",
        }

    def test_zero_stock_allowed(self):
        data = ProductCreate(name="售罄杯", category="生活用品", price=199, stock=0, sku="CP-009")
        product = build_product_from_create(3, data)
        assert product.stock == 0


# ---------- list_products ----------
class TestListProducts:
    def test_returns_200_list(self):
        resp = client.get("/products")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 4

    def test_has_seed_names(self):
        names = {p["name"] for p in client.get("/products").json()}
        assert names == {"机械键盘", "无线鼠标", "设计模式", "智能水杯"}

    def test_product_has_expected_fields(self):
        first = client.get("/products").json()[0]
        assert {"id", "name", "category", "price", "stock", "sku"} <= set(first.keys())


# ---------- create_product ----------
class TestCreateProduct:
    def test_create_returns_201_and_body(self):
        resp = client.post(
            "/products",
            json={"name": "降噪耳机", "category": "影音设备", "price": 1299, "stock": 80, "sku": "HP-006"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "降噪耳机"
        assert body["category"] == "影音设备"
        assert body["price"] == 1299.0
        assert body["stock"] == 80
        assert body["sku"] == "HP-006"
        assert body["id"] == 5

    def test_created_appears_in_get(self):
        resp = client.post(
            "/products",
            json={"name": "蓝牙音箱", "category": "影音设备", "price": 399, "sku": "SP-007"},
        )
        new_id = resp.json()["id"]
        got = client.get(f"/products/{new_id}")
        assert got.status_code == 200
        assert got.json()["name"] == "蓝牙音箱"
        assert got.json()["stock"] == 0  # 默认库存

    def test_ids_increment(self):
        a = client.post(
            "/products", json={"name": "A", "category": "图书", "price": 1, "sku": "AA-001"}
        ).json()["id"]
        b = client.post(
            "/products", json={"name": "B", "category": "图书", "price": 2, "sku": "BB-002"}
        ).json()["id"]
        assert b == a + 1

    def test_invalid_price_rejected(self):
        resp = client.post(
            "/products", json={"name": "X", "category": "图书", "price": -10, "sku": "XX-001"}
        )
        assert resp.status_code == 422

    def test_zero_price_rejected(self):
        resp = client.post(
            "/products", json={"name": "X", "category": "图书", "price": 0, "sku": "XX-001"}
        )
        assert resp.status_code == 422

    def test_missing_name_rejected(self):
        resp = client.post("/products", json={"category": "图书", "price": 10, "sku": "XX-001"})
        assert resp.status_code == 422

    def test_bad_sku_rejected(self):
        resp = client.post(
            "/products", json={"name": "X", "category": "图书", "price": 10, "sku": "bad"}
        )
        assert resp.status_code == 422

    def test_missing_category_rejected(self):
        resp = client.post(
            "/products", json={"name": "X", "price": 10, "sku": "XX-001"}
        )
        assert resp.status_code == 422

    def test_422_body_locates_field(self):
        # 422 响应体是结构化的:detail[].loc 指出哪个字段违法(§14.2)
        resp = client.post(
            "/products", json={"name": "X", "category": "图书", "price": -1, "sku": "XX-001"}
        )
        detail = resp.json()["detail"]
        assert isinstance(detail, list)
        assert ["body", "price"] in [e["loc"] for e in detail]


# ---------- get_product ----------
class TestGetProduct:
    def test_get_existing(self):
        resp = client.get("/products/1")
        assert resp.status_code == 200
        assert resp.json()["name"] == "机械键盘"
        assert resp.json()["sku"] == "KB-001"

    def test_get_out_of_stock_item(self):
        resp = client.get("/products/4")
        assert resp.status_code == 200
        assert resp.json()["stock"] == 0

    def test_get_missing_returns_404(self):
        resp = client.get("/products/99999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "商品不存在"

    def test_get_non_int_id_returns_422(self):
        # 路径参数 int 转换失败 → 框架 422,函数体不执行
        resp = client.get("/products/abc")
        assert resp.status_code == 422


# ---------- update_product ----------
class TestUpdateProduct:
    def test_update_replaces_fields_keeps_id(self):
        resp = client.put(
            "/products/2",
            json={"name": "无线鼠标", "category": "电脑外设", "price": 169, "stock": 350, "sku": "MS-002"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == 2
        assert body["price"] == 169.0
        assert body["stock"] == 350

    def test_update_persisted(self):
        client.put(
            "/products/1",
            json={"name": "机械键盘 Pro", "category": "电脑外设", "price": 699, "stock": 50, "sku": "KB-001"},
        )
        got = client.get("/products/1").json()
        assert got["name"] == "机械键盘 Pro"
        assert got["price"] == 699.0

    def test_update_missing_returns_404(self):
        resp = client.put(
            "/products/99999",
            json={"name": "幽灵", "category": "图书", "price": 1, "sku": "GH-001"},
        )
        assert resp.status_code == 404

    def test_update_invalid_body_422(self):
        resp = client.put(
            "/products/1",
            json={"name": "机械键盘", "category": "电脑外设", "price": -1, "sku": "KB-001"},
        )
        assert resp.status_code == 422


# ---------- delete_product ----------
class TestDeleteProduct:
    def test_delete_returns_204(self):
        resp = client.delete("/products/4")
        assert resp.status_code == 204
        assert resp.content == b""
        # 必须真的删掉,不能只靠装饰器返回 204(骨架 ... 也会 204)
        assert 4 not in m.PRODUCTS
        assert len(client.get("/products").json()) == 3

    def test_deleted_no_longer_gettable(self):
        client.delete("/products/4")
        assert client.get("/products/4").status_code == 404
        assert len(client.get("/products").json()) == 3

    def test_delete_missing_returns_404(self):
        resp = client.delete("/products/99999")
        assert resp.status_code == 404


# ---------- inventory_report ----------
class TestInventoryReport:
    def test_seed_report(self):
        resp = client.get("/inventory/report")
        assert resp.status_code == 200
        assert resp.json() == {
            "total_skus": 4,
            "total_units": 620,
            "total_value": 134680.0,
            "out_of_stock": ["智能水杯"],
        }

    def test_report_after_create_and_restock(self):
        client.post(
            "/products",
            json={"name": "扩展坞", "category": "电脑外设", "price": 269, "stock": 0, "sku": "DK-008"},
        )
        client.put(
            "/products/4",
            json={"name": "智能水杯", "category": "生活用品", "price": 199, "stock": 5, "sku": "CP-009"},
        )
        report = client.get("/inventory/report").json()
        assert report["total_skus"] == 5
        assert report["total_units"] == 625
        assert report["total_value"] == 135675.0
        assert report["out_of_stock"] == ["扩展坞"]

    def test_report_after_delete_out_of_stock(self):
        client.delete("/products/4")
        report = client.get("/inventory/report").json()
        assert report["total_skus"] == 3
        assert report["total_units"] == 620
        assert report["total_value"] == 134680.0
        assert report["out_of_stock"] == []
