"""
Ch13 作业测试。运行: uv run pytest 03_web_framework/ch13/test_ch13_assignment.py -v

测试技巧:用 httpx.MockTransport 注入假响应,不需要真服务。
"""
import httpx
import pytest

from ch13_assignment import fetch_products, create_product, get_product_or_none


def make_client(handler):
    """构造带 MockTransport 的 client:handler 决定如何响应每个请求。"""
    return httpx.Client(transport=httpx.MockTransport(handler))


# ---------- fetch_products:GET ----------
class TestFetchProducts:
    def test_ok(self):
        def handler(req):
            return httpx.Response(200, json=[{"name": "键盘"}, {"name": "鼠标"}])
        result = fetch_products(make_client(handler), "http://x/api/products")
        assert result == [{"name": "键盘"}, {"name": "鼠标"}]

    def test_500_raises(self):
        def handler(req):
            return httpx.Response(500)
        with pytest.raises(httpx.HTTPStatusError):
            fetch_products(make_client(handler), "http://x/api/products")

    def test_send_correct_url(self):
        seen = {}

        def handler(req):
            seen["url"] = str(req.url)
            return httpx.Response(200, json=[])
        fetch_products(make_client(handler), "http://x/api/products")
        assert seen["url"] == "http://x/api/products"


# ---------- create_product:POST ----------
class TestCreateProduct:
    def test_ok_returns_response(self):
        def handler(req):
            return httpx.Response(201, json={"id": 1, "name": "键盘"})
        result = create_product(make_client(handler), "http://x/api/products", {"name": "键盘"})
        assert result == {"id": 1, "name": "键盘"}

    def test_sends_json_body(self):
        captured = {}

        def handler(req):
            captured["body"] = req.read()
            captured["content_type"] = req.headers.get("content-type")
            return httpx.Response(201, json={})
        create_product(make_client(handler), "http://x/api/products", {"name": "键盘", "price": 599})
        assert b'"name"' in captured["body"]
        assert b'599' in captured["body"]
        assert "application/json" in captured["content_type"]

    def test_400_raises(self):
        def handler(req):
            return httpx.Response(400)
        with pytest.raises(httpx.HTTPStatusError):
            create_product(make_client(handler), "http://x/api/products", {})


# ---------- get_product_or_none:GET + 404 处理 ----------
class TestGetProductOrNone:
    def test_ok(self):
        def handler(req):
            return httpx.Response(200, json={"id": 1, "name": "键盘"})
        assert get_product_or_none(make_client(handler), "http://x/api/products/1") == {
            "id": 1, "name": "键盘",
        }

    def test_404_returns_none(self):
        def handler(req):
            return httpx.Response(404)
        assert get_product_or_none(make_client(handler), "http://x/api/products/999") is None

    def test_500_raises(self):
        def handler(req):
            return httpx.Response(500)
        with pytest.raises(httpx.HTTPStatusError):
            get_product_or_none(make_client(handler), "http://x/api/products/1")
