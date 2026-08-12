"""
Ch13 作业测试。运行: uv run pytest 03_web_framework/ch13/test_ch13_assignment.py -v

测试技巧:用 httpx.MockTransport 注入假响应,不需要真服务(tutorial §13.9)。
商品数据来自共享 mock:assets/mock_data/products.json(商品中心的示例数据)。
"""
import json

import httpx
import pytest

from conftest import load_mock_json
from ch13_assignment import (
    fetch_products,
    search_products,
    create_product,
    get_product_or_none,
    fetch_with_auth,
    update_stock,
    fetch_with_retry,
    aggregate_by_category,
)

PRODUCTS = load_mock_json("products.json")   # 10 条商品,商品中心文档示例数据


def make_client(handler):
    """构造带 MockTransport 的 client:handler 决定如何响应每个请求。"""
    return httpx.Client(transport=httpx.MockTransport(handler))


# ---------- fetch_products:GET + raise_for_status ----------
class TestFetchProducts:
    def test_ok_returns_full_list(self):
        def handler(req):
            return httpx.Response(200, json=PRODUCTS)
        result = fetch_products(make_client(handler), "http://x/api/products")
        assert result == PRODUCTS
        assert len(result) == 10

    def test_ok_empty_list(self):
        def handler(req):
            return httpx.Response(200, json=[])
        assert fetch_products(make_client(handler), "http://x/api/products") == []

    def test_500_raises(self):
        def handler(req):
            return httpx.Response(500)
        with pytest.raises(httpx.HTTPStatusError):
            fetch_products(make_client(handler), "http://x/api/products")

    def test_404_also_raises(self):
        # 列表接口的 404 不是「查单个不存在」,照样要抛(和 get_product_or_none 区分)
        def handler(req):
            return httpx.Response(404)
        with pytest.raises(httpx.HTTPStatusError):
            fetch_products(make_client(handler), "http://x/api/products")

    def test_send_correct_url(self):
        seen = {}

        def handler(req):
            seen["url"] = str(req.url)
            return httpx.Response(200, json=[])
        fetch_products(make_client(handler), "http://x/api/products")
        assert seen["url"] == "http://x/api/products"


# ---------- search_products:params 查询参数 ----------
class TestSearchProducts:
    def test_both_params_sent(self):
        seen = {}

        def handler(req):
            seen["params"] = req.url.params
            return httpx.Response(200, json=[PRODUCTS[0]])
        result = search_products(
            make_client(handler), "http://x/api/products/search",
            keyword="键盘", max_price=600,
        )
        assert seen["params"].get("keyword") == "键盘"
        assert seen["params"].get("max_price") == "600"
        assert result == [PRODUCTS[0]]

    def test_none_params_omitted(self):
        seen = {}

        def handler(req):
            seen["params"] = req.url.params
            return httpx.Response(200, json=PRODUCTS)
        search_products(make_client(handler), "http://x/api/products/search")
        # 两个条件都是 None:query 里一个参数都不能有(不能出现 keyword=None)
        assert seen["params"].get("keyword") is None
        assert seen["params"].get("max_price") is None
        assert len(seen["params"]) == 0

    def test_partial_params(self):
        seen = {}

        def handler(req):
            seen["params"] = req.url.params
            return httpx.Response(200, json=[])
        search_products(make_client(handler), "http://x/api/products/search", max_price=200)
        assert seen["params"].get("max_price") == "200"
        assert seen["params"].get("keyword") is None

    def test_chinese_keyword_url_encoded(self):
        # f-string 拼 URL 不会编码中文;params= 必须自动编码成 %XX
        seen = {}

        def handler(req):
            seen["raw_url"] = str(req.url)
            return httpx.Response(200, json=[])
        search_products(make_client(handler), "http://x/api/products/search", keyword="键盘")
        assert "%E9%94%AE%E7%9B%98" in seen["raw_url"]

    def test_500_raises(self):
        def handler(req):
            return httpx.Response(500)
        with pytest.raises(httpx.HTTPStatusError):
            search_products(make_client(handler), "http://x/api/products/search", keyword="x")


# ---------- create_product:POST + json body ----------
class TestCreateProduct:
    def test_ok_returns_created(self):
        def handler(req):
            return httpx.Response(201, json={"id": 11, "name": "机械键盘", "price": 599.0})
        result = create_product(
            make_client(handler), "http://x/api/products",
            {"name": "机械键盘", "price": 599.0},
        )
        assert result == {"id": 11, "name": "机械键盘", "price": 599.0}
        assert result["id"] == 11

    def test_sends_json_body_and_content_type(self):
        captured = {}

        def handler(req):
            captured["method"] = req.method
            captured["body"] = req.read()
            captured["content_type"] = req.headers.get("content-type")
            return httpx.Response(201, json={})
        create_product(
            make_client(handler), "http://x/api/products",
            {"name": "机械键盘", "price": 599.0},
        )
        assert captured["method"] == "POST"
        assert b'"name"' in captured["body"]
        assert b"599" in captured["body"]
        assert "application/json" in captured["content_type"]

    def test_400_raises(self):
        def handler(req):
            return httpx.Response(400, json={"detail": "price must be positive"})
        with pytest.raises(httpx.HTTPStatusError):
            create_product(make_client(handler), "http://x/api/products", {"price": -1})


# ---------- get_product_or_none:404 精细处理 ----------
class TestGetProductOrNone:
    def test_ok_returns_product(self):
        def handler(req):
            return httpx.Response(200, json=PRODUCTS[0])
        result = get_product_or_none(make_client(handler), "http://x/api/products/1")
        assert result == PRODUCTS[0]
        assert result["name"] == "机械键盘"

    def test_404_returns_none(self):
        calls = {"n": 0}

        def handler(req):
            calls["n"] += 1
            return httpx.Response(404)
        assert get_product_or_none(make_client(handler), "http://x/api/products/999") is None
        assert calls["n"] == 1     # 必须真的发了请求(拦住「直接 return None」的蒙对)

    def test_500_raises(self):
        def handler(req):
            return httpx.Response(500)
        with pytest.raises(httpx.HTTPStatusError):
            get_product_or_none(make_client(handler), "http://x/api/products/1")

    def test_400_raises_not_none(self):
        # 400 不是 404:参数错误必须抛,不能吞成 None(拦住「一律返回 None」的蒙对实现)
        def handler(req):
            return httpx.Response(400)
        with pytest.raises(httpx.HTTPStatusError):
            get_product_or_none(make_client(handler), "http://x/api/products/abc")


# ---------- fetch_with_auth:headers Bearer 认证 ----------
class TestFetchWithAuth:
    @staticmethod
    def _auth_handler(req):
        # 模拟商品中心:头对了给数据,错了 401
        if req.headers.get("authorization") == "Bearer token-abc":
            return httpx.Response(200, json=PRODUCTS[0])
        return httpx.Response(401, json={"detail": "invalid token"})

    def test_ok_with_valid_token(self):
        result = fetch_with_auth(make_client(self._auth_handler), "http://x/api/products/1", "token-abc")
        assert result == PRODUCTS[0]

    def test_wrong_token_raises_401(self):
        with pytest.raises(httpx.HTTPStatusError):
            fetch_with_auth(make_client(self._auth_handler), "http://x/api/products/1", "wrong")

    def test_header_format_exact(self):
        # 必须是 "Bearer <token>"(空格 + 大小写),不是 "token-abc" 也不是 "bearer ..."
        seen = {}

        def handler(req):
            seen["auth"] = req.headers.get("authorization")
            return httpx.Response(200, json={})
        fetch_with_auth(make_client(handler), "http://x/api/products/1", "tk123")
        assert seen["auth"] == "Bearer tk123"


# ---------- update_stock:PUT + json body ----------
class TestUpdateStock:
    def test_ok_returns_updated(self):
        def handler(req):
            return httpx.Response(200, json={**PRODUCTS[0], "stock": 118})
        result = update_stock(make_client(handler), "http://x/api/products/1/stock", -2)
        assert result["stock"] == 118
        assert result["id"] == 1

    def test_sends_put_with_delta_body(self):
        captured = {}

        def handler(req):
            captured["method"] = req.method
            captured["url"] = str(req.url)
            captured["body"] = req.read()
            return httpx.Response(200, json={})
        update_stock(make_client(handler), "http://x/api/products/1/stock", -2)
        assert captured["method"] == "PUT"
        assert captured["url"] == "http://x/api/products/1/stock"
        assert json.loads(captured["body"]) == {"delta": -2}

    def test_positive_delta_restock(self):
        captured = {}

        def handler(req):
            captured["body"] = req.read()
            return httpx.Response(200, json={})
        update_stock(make_client(handler), "http://x/api/products/1/stock", 50)
        assert json.loads(captured["body"]) == {"delta": 50}

    def test_404_raises(self):
        def handler(req):
            return httpx.Response(404)
        with pytest.raises(httpx.HTTPStatusError):
            update_stock(make_client(handler), "http://x/api/products/999/stock", -1)


# ---------- fetch_with_retry:异常分类 + 重试 ----------
class TestFetchWithRetry:
    def test_success_first_try(self):
        calls = {"n": 0}

        def handler(req):
            calls["n"] += 1
            return httpx.Response(200, json=PRODUCTS)
        result = fetch_with_retry(make_client(handler), "http://x/api/products", retries=3)
        assert result == PRODUCTS
        assert calls["n"] == 1

    def test_retry_on_503_then_success(self):
        calls = {"n": 0}

        def handler(req):
            calls["n"] += 1
            if calls["n"] < 3:
                return httpx.Response(503)
            return httpx.Response(200, json=PRODUCTS)
        result = fetch_with_retry(make_client(handler), "http://x/api/products", retries=3)
        assert result == PRODUCTS
        assert calls["n"] == 3     # 恰好 3 次:多一次少一次都是错

    def test_gives_up_after_retries(self):
        calls = {"n": 0}

        def handler(req):
            calls["n"] += 1
            return httpx.Response(503)
        with pytest.raises(httpx.HTTPStatusError):
            fetch_with_retry(make_client(handler), "http://x/api/products", retries=3)
        assert calls["n"] == 3     # 试满 retries 次才放弃

    def test_4xx_no_retry(self):
        # 400 是请求本身有错:第 1 次就抛,重发无意义(拦住「所有错误都重试」的实现)
        calls = {"n": 0}

        def handler(req):
            calls["n"] += 1
            return httpx.Response(400)
        with pytest.raises(httpx.HTTPStatusError):
            fetch_with_retry(make_client(handler), "http://x/api/products", retries=3)
        assert calls["n"] == 1

    def test_timeout_retried(self):
        # 网络错误(超时)也要重试:handler 直接抛 TransportError 模拟
        calls = {"n": 0}

        def handler(req):
            calls["n"] += 1
            if calls["n"] == 1:
                raise httpx.ConnectTimeout("connect timeout")
            return httpx.Response(200, json=PRODUCTS)
        result = fetch_with_retry(make_client(handler), "http://x/api/products", retries=3)
        assert result == PRODUCTS
        assert calls["n"] == 2

    def test_timeout_gives_up(self):
        def handler(req):
            raise httpx.ReadTimeout("read timeout")
        with pytest.raises(httpx.TransportError):
            fetch_with_retry(make_client(handler), "http://x/api/products", retries=2)


# ---------- aggregate_by_category:综合 ----------
class TestAggregateByCategory:
    def test_aggregates_products_json(self):
        # 断言值按 assets/mock_data/products.json 手工验算:
        # 电脑外设 599+159+2199+269=3226.0(4 个) / 生活用品 199+1599=1798.0
        # 影音设备 1299+399=1698.0 / 图书 89+75.5=164.5
        def handler(req):
            return httpx.Response(200, json=PRODUCTS)
        result = aggregate_by_category(make_client(handler), "http://x/api/products")
        assert result == [
            {"category": "电脑外设", "count": 4, "total_price": 3226.0},
            {"category": "生活用品", "count": 2, "total_price": 1798.0},
            {"category": "影音设备", "count": 2, "total_price": 1698.0},
            {"category": "图书", "count": 2, "total_price": 164.5},
        ]

    def test_empty_returns_empty(self):
        def handler(req):
            return httpx.Response(200, json=[])
        assert aggregate_by_category(make_client(handler), "http://x/api/products") == []

    def test_single_category(self):
        def handler(req):
            return httpx.Response(200, json=[
                {"id": 1, "name": "A", "category": "图书", "price": 100.0},
                {"id": 2, "name": "B", "category": "图书", "price": 50.5},
            ])
        result = aggregate_by_category(make_client(handler), "http://x/api/products")
        assert result == [{"category": "图书", "count": 2, "total_price": 150.5}]

    def test_500_raises(self):
        # 复用了 fetch_products:错误处理必须一并生效(拦住「自己重写一遍忘了 raise」的实现)
        def handler(req):
            return httpx.Response(500)
        with pytest.raises(httpx.HTTPStatusError):
            aggregate_by_category(make_client(handler), "http://x/api/products")
