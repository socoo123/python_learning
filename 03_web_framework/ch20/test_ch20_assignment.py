"""
Ch20 作业测试(答案校验,完整保留)。运行:

    uv sync --extra web
    uv run pytest 03_web_framework/ch20/test_ch20_assignment.py -v
    uv run pytest 03_web_framework/ch20/test_ch20_assignment.py --cov=ch20_assignment --cov-report=term-missing

fixture 接线:products_fixture / api_client / admin_client 定义在作业文件里,
本文件 import 后即在 pytest 命名空间里生效(= 迷你 conftest,见 §20.2)。
parametrize 数据源同理来自作业文件;骨架期它们返回 None,用 `or []` 降级为
空参数集(parametrize 收到空列表 → 该用例标记 skip),保证骨架期「能收集、
其余测试照常判红」。
"""
import pytest
from fastapi import HTTPException

from ch20_assignment import (
    PRODUCTS,
    SEED_PRODUCTS,
    admin_client,
    api_client,
    app,
    auth_headers,
    get_current_user,
    not_found_id_cases,
    override_auth,
    price_validation_cases,
    products_fixture,
)

# 骨架期数据源函数返回 None,`or []` 让 parametrize 退化为 skip,不炸收集
_PRICE_CASES = price_validation_cases() or []
_NOT_FOUND_CASES = not_found_id_cases() or []


# ---------- §20.1 auth_headers(构造 Bearer 请求头)----------
class TestAuthHeaders:
    def test_returns_dict_with_authorization_key(self):
        h = auth_headers("alice")
        assert isinstance(h, dict)
        assert "Authorization" in h

    def test_bearer_prefix_format(self):
        assert auth_headers("alice")["Authorization"] == "Bearer alice"
        assert auth_headers("token-abc-123")["Authorization"] == "Bearer token-abc-123"

    def test_real_request_with_headers_creates_product(self, api_client):
        """带 auth_headers 访问需鉴权端点 → 201(真走了一遍 get_current_user)。"""
        try:
            resp = api_client.post(
                "/products",
                json={"id": 100, "name": "测试商品", "price": 9.9, "stock": 10},
                headers=auth_headers("alice"),
            )
            assert resp.status_code == 201
            assert resp.json()["name"] == "测试商品"
        finally:
            PRODUCTS.clear()

    def test_missing_header_returns_401(self, api_client):
        """没带 Authorization → 401。"""
        resp = api_client.post(
            "/products",
            json={"id": 100, "name": "测试商品", "price": 9.9, "stock": 10},
        )
        assert resp.status_code == 401

    def test_wrong_scheme_returns_401(self, api_client):
        """scheme 不是 Bearer(如 Basic)→ 401。"""
        resp = api_client.post(
            "/products",
            json={"id": 100, "name": "测试商品", "price": 9.9, "stock": 10},
            headers={"Authorization": "Basic alice"},
        )
        assert resp.status_code == 401


# ---------- §20.2 products_fixture(fixture + yield + teardown)----------
class TestProductsFixture:
    def test_seeds_three_products(self, products_fixture):
        """setup 阶段把 3 个种子商品塞进了 PRODUCTS。"""
        assert len(PRODUCTS) == 3
        assert set(PRODUCTS.keys()) == {1, 2, 3}

    def test_yields_seeded_list(self, products_fixture):
        """yield 出来的是 3 个商品的列表,内容与 SEED_PRODUCTS 一致。"""
        assert isinstance(products_fixture, list)
        assert len(products_fixture) == 3
        assert [p.name for p in products_fixture] == [p.name for p in SEED_PRODUCTS]

    def test_products_match_seed_constant(self, products_fixture):
        keyboard = PRODUCTS[1]
        assert keyboard.name == "机械键盘"
        assert keyboard.price == 599.0
        assert keyboard.stock == 42

    def test_isolation_step1_pollutes(self, products_fixture):
        """故意删掉一个商品(污染全局状态);下一个测试证明 fixture 做了隔离。"""
        assert len(PRODUCTS) == 3
        del PRODUCTS[1]
        assert len(PRODUCTS) == 2

    def test_isolation_step2_recovers(self, products_fixture):
        """上一个测试删过数据;这里又看到 3 个 → teardown 清了 + setup 重塞了。"""
        assert len(PRODUCTS) == 3
        assert set(PRODUCTS.keys()) == {1, 2, 3}


# ---------- §20.2 api_client(fixture 管客户端 + 清全局状态)----------
class TestApiClient:
    def test_client_can_call_api(self, api_client):
        resp = api_client.get("/products")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_step1_pollute_overrides(self, api_client):
        """故意往 dependency_overrides 塞 mock(污染);下一个测试证明 teardown 清了它。"""
        app.dependency_overrides[get_current_user] = lambda: "hacker"
        assert get_current_user in app.dependency_overrides

    def test_step2_overrides_were_cleaned(self, api_client):
        """api_client 的 teardown 应清掉上个测试塞的覆盖;没清就是 teardown 没写。"""
        assert app.dependency_overrides == {}


# ---------- §20.3 override_auth(依赖覆盖)----------
class TestOverrideAuth:
    def test_registers_function_object_key(self):
        """键必须是 get_current_user 函数对象(不是字符串)。"""
        override_auth(app, username="someone")
        try:
            assert get_current_user in app.dependency_overrides
        finally:
            app.dependency_overrides.clear()

    def test_fake_returns_given_username(self):
        override_auth(app, username="someone")
        try:
            assert app.dependency_overrides[get_current_user]() == "someone"
        finally:
            app.dependency_overrides.clear()

    def test_default_username_is_testuser(self):
        """不传 username 时默认 testuser。"""
        override_auth(app)
        try:
            assert app.dependency_overrides[get_current_user]() == "testuser"
        finally:
            app.dependency_overrides.clear()

    def test_bypasses_auth_on_endpoint(self, api_client):
        """覆盖后不带 Authorization 头也能 POST → 201。"""
        override_auth(app, username="mocked_admin")
        try:
            resp = api_client.post(
                "/products",
                json={"id": 200, "name": "覆盖鉴权", "price": 1.0, "stock": 1},
            )
            assert resp.status_code == 201
        finally:
            PRODUCTS.clear()


# ---------- §20.4 price_validation_cases(parametrize 数据源:价格边界)----------
class TestPriceValidationCases:
    def test_returns_list_of_price_status_pairs(self):
        cases = price_validation_cases()
        assert isinstance(cases, list)
        assert len(cases) >= 3
        for case in cases:
            assert isinstance(case, tuple) and len(case) == 2
            price, expected = case
            assert isinstance(price, (int, float))
            assert isinstance(expected, int)

    def test_covers_valid_and_invalid(self):
        """防蒙对:必须同时覆盖 ≥2 组合法(201)和 ≥1 组 0/负价(422)。"""
        cases = price_validation_cases()
        valid = [c for c in cases if c[1] == 201]
        invalid = [c for c in cases if c[1] == 422 and c[0] <= 0]
        assert len(valid) >= 2, "至少 2 组合法价格(201)"
        assert len(invalid) >= 1, "至少 1 组 0 或负价(422)"

    @pytest.mark.parametrize("price, expected_status", _PRICE_CASES)
    def test_price_boundary(self, price, expected_status, admin_client, products_fixture):
        """每组数据展开成一个独立测试,ID 形如 test_price_boundary[0.01-201]。"""
        resp = admin_client.post(
            "/products",
            json={"id": 99, "name": "边界商品", "price": price, "stock": 5},
        )
        assert resp.status_code == expected_status


# ---------- §20.4 not_found_id_cases(parametrize 数据源:404)----------
class TestNotFoundIdCases:
    def test_returns_nonempty_list_of_ints(self):
        cases = not_found_id_cases()
        assert isinstance(cases, list) and len(cases) >= 2
        assert all(isinstance(pid, int) for pid in cases)

    def test_cases_are_truly_unknown(self, products_fixture):
        """防蒙对:每个 case id 都必须【真的不在】种子数据里。"""
        for pid in not_found_id_cases():
            assert pid not in PRODUCTS, f"{pid} 在种子数据里,测不出 404"

    @pytest.mark.parametrize("pid", _NOT_FOUND_CASES)
    def test_get_unknown_returns_404(self, pid, products_fixture, api_client):
        assert api_client.get(f"/products/{pid}").status_code == 404

    @pytest.mark.parametrize("pid", _NOT_FOUND_CASES)
    def test_update_unknown_returns_404(self, pid, products_fixture, admin_client):
        resp = admin_client.put(
            f"/products/{pid}",
            json={"id": pid, "name": "幽灵商品", "price": 1.0, "stock": 1},
        )
        assert resp.status_code == 404

    @pytest.mark.parametrize("pid", _NOT_FOUND_CASES)
    def test_delete_unknown_returns_404(self, pid, products_fixture, admin_client):
        assert admin_client.delete(f"/products/{pid}").status_code == 404


# ---------- §20.3 admin_client(fixture 组合,本章综合)----------
class TestAdminClient:
    def test_post_without_headers_succeeds(self, admin_client, products_fixture):
        """admin_client = 免鉴权客户端:不带 Authorization 也能 201。"""
        resp = admin_client.post(
            "/products",
            json={"id": 9, "name": "鼠标垫", "price": 29.9, "stock": 50},
        )
        assert resp.status_code == 201
        assert resp.json()["id"] == 9

    def test_full_crud_flow_as_admin(self, admin_client, products_fixture):
        """PUT 改名 → DELETE 删一个 → GET 列表数量正确。"""
        resp = admin_client.put(
            "/products/1",
            json={"id": 1, "name": "改名键盘", "price": 699.0, "stock": 100},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "改名键盘"

        assert admin_client.delete("/products/2").status_code == 204

        remaining = admin_client.get("/products").json()
        assert len(remaining) == 2
        assert {p["id"] for p in remaining} == {1, 3}

    def test_plain_client_still_requires_auth(self, api_client, products_fixture):
        """对照:没做 override 的 api_client 依然被 401 拦下(证明覆盖没乱泄漏)。"""
        resp = api_client.post(
            "/products",
            json={"id": 9, "name": "鼠标垫", "price": 29.9, "stock": 50},
        )
        assert resp.status_code == 401


# ---------- §20.5 示范:绕过 HTTP 直接单测依赖函数(完整给出,不用填)----------
class TestGetCurrentUserDirect:
    def test_valid_bearer_returns_username(self):
        assert get_current_user("Bearer alice") == "alice"

    def test_missing_header_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(None)
        assert exc_info.value.status_code == 401

    def test_wrong_scheme_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user("Basic alice")
        assert exc_info.value.status_code == 401

    def test_empty_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user("Bearer ")
        assert exc_info.value.status_code == 401
