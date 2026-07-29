"""
Ch15 作业测试。运行: uv run pytest 03_web_framework/ch15/test_ch15_assignment.py -v
"""
from fastapi.testclient import TestClient

from ch15_assignment import app

client = TestClient(app)


# ---------- list_products:筛选 ----------
class TestFilter:
    def test_all_no_filter(self):
        assert len(client.get("/products").json()) == 5

    def test_filter_by_category(self):
        data = client.get("/products", params={"category": "图书"}).json()
        assert len(data) == 2
        assert all(p["category"] == "图书" for p in data)

    def test_filter_min_price(self):
        data = client.get("/products", params={"min_price": 500}).json()
        assert len(data) == 2          # 键盘599、耳机1299
        names = {p["name"] for p in data}
        assert names == {"机械键盘", "降噪耳机"}

    def test_filter_combined(self):
        data = client.get("/products", params={"category": "电脑外设", "min_price": 200}).json()
        assert len(data) == 1          # 只有键盘599 >=200(鼠标159被滤掉)
        assert data[0]["name"] == "机械键盘"

    def test_filter_no_match(self):
        data = client.get("/products", params={"category": "不存在"}).json()
        assert data == []

    def test_min_price_boundary_inclusive(self):
        # >= 599 应包含键盘599
        data = client.get("/products", params={"min_price": 599}).json()
        names = {p["name"] for p in data}
        assert "机械键盘" in names


# ---------- list_products:分页 ----------
class TestPagination:
    def test_default_returns_all(self):
        # 默认 size=10,共 5 个 → 全返回
        assert len(client.get("/products").json()) == 5

    def test_page1_size2(self):
        data = client.get("/products", params={"page": 1, "size": 2}).json()
        assert len(data) == 2
        assert data[0]["id"] == 1

    def test_page2_size2(self):
        data = client.get("/products", params={"page": 2, "size": 2}).json()
        assert len(data) == 2
        assert data[0]["id"] == 3

    def test_last_page_partial(self):
        # 第 3 页(每页2):只剩 id=5 一个
        data = client.get("/products", params={"page": 3, "size": 2}).json()
        assert len(data) == 1

    def test_beyond_last_page_empty(self):
        data = client.get("/products", params={"page": 99, "size": 2}).json()
        assert data == []

    def test_page_zero_rejected(self):
        # page 必须 >=1(ge=1)
        assert client.get("/products", params={"page": 0}).status_code == 422

    def test_size_too_large_rejected(self):
        # size 上限 100(le=100)
        assert client.get("/products", params={"size": 200}).status_code == 422


# ---------- get_product:路径参数 ----------
class TestGetProduct:
    def test_existing(self):
        assert client.get("/products/1").json()["name"] == "机械键盘"

    def test_missing_404(self):
        assert client.get("/products/999").status_code == 404

    def test_non_int_id_rejected(self):
        # /products/abc → 路径参数类型校验失败 422
        assert client.get("/products/abc").status_code == 422
