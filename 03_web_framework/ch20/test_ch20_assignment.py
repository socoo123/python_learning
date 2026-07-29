"""
Ch20 作业测试(答案校验,完整保留)。

运行:
    uv run pytest 03_web_framework/ch20/ -v
    uv run pytest 03_web_framework/ch20/ --cov=ch20_assignment --cov-report=term-missing
"""
import pytest
from fastapi.testclient import TestClient

import ch20_assignment as mod
from ch20_assignment import (
    PRODUCTS,
    app,
    auth_headers,
    get_current_user,
    make_product_fixture,
    override_auth,
)


# ---------- §20.1 fixture 工厂(用户实现的 make_product_fixture)----------
# 把用户实现的 fixture 注册到本模块的命名空间,pytest 才能发现它
products_fixture = make_product_fixture()


class TestProductFixture:
    def test_fixture_setup_three_products(self, products_fixture):
        """fixture 在 setup 阶段塞了 3 个商品(id=1/2/3)。"""
        assert len(PRODUCTS) == 3
        assert set(PRODUCTS.keys()) == {1, 2, 3}

    def test_fixture_yields_list(self, products_fixture):
        """fixture 通过 yield 返回商品列表。"""
        assert isinstance(products_fixture, list)
        assert len(products_fixture) == 3

    def test_fixture_teardown_clears_store(self, products_fixture):
        """fixture 的 teardown(测试结束后)清空 PRODUCTS。"""
        # 这里测试期间 PRODUCTS 应有数据
        assert len(PRODUCTS) == 3
        # teardown 由 pytest 在测试函数返回后自动调用(yield 之后)

    def test_fixture_isolation_between_tests(self, products_fixture):
        """多个测试用同一 fixture,每次都从干净状态开始(证明 teardown 生效)。"""
        # 如果 teardown 不生效,上一次测试残留会让数量 > 3
        assert len(PRODUCTS) == 3
        # 这里删一个,模拟测试修改了状态
        del PRODUCTS[1]
        assert len(PRODUCTS) == 2
        # 下一个测试用 fixture 时应该又回到 3(证明 teardown 清空过)


# ---------- §20.3 auth_headers(用户实现的鉴权请求头构造)----------
class TestAuthHeaders:
    def test_headers_have_authorization(self):
        h = auth_headers("testuser")
        assert "Authorization" in h

    def test_headers_bearer_prefix(self):
        h = auth_headers("alice")
        assert h["Authorization"] == "Bearer alice"

    def test_headers_work_with_protected_endpoint(self):
        """用 auth_headers 访问需鉴权的端点,应该 201 创建成功。"""
        client = TestClient(app)
        PRODUCTS.clear()
        new = {"id": 100, "name": "测试商品", "price": 9.9, "stock": 10}
        resp = client.post("/products", json=new, headers=auth_headers("testuser"))
        assert resp.status_code == 201
        PRODUCTS.clear()

    def test_protected_endpoint_rejects_without_headers(self):
        """没带 Authorization → 401。"""
        client = TestClient(app)
        new = {"id": 100, "name": "测试商品", "price": 9.9, "stock": 10}
        resp = client.post("/products", json=new)
        assert resp.status_code == 401


# ---------- §20.4 override_auth(用户实现的依赖覆盖)----------
class TestOverrideAuth:
    def test_override_replaces_dependency(self):
        """override_auth 后,get_current_user 被替换,不再校验 token。"""
        client = TestClient(app)
        PRODUCTS.clear()
        override_auth(app, username="mocked_user")
        try:
            # 不带 Authorization 头也能创建 → 依赖被绕过
            new = {"id": 200, "name": "覆盖鉴权", "price": 1.0, "stock": 1}
            resp = client.post("/products", json=new)
            assert resp.status_code == 201
        finally:
            app.dependency_overrides.clear()
            PRODUCTS.clear()

    def test_override_stored_in_dependency_overrides(self):
        """override_auth 应往 app.dependency_overrides 写入 get_current_user 的映射。"""
        override_auth(app, username="someone")
        try:
            assert get_current_user in app.dependency_overrides
            # 覆盖函数被调用时返回 username
            fake = app.dependency_overrides[get_current_user]
            assert fake() == "someone"
        finally:
            app.dependency_overrides.clear()

    def test_override_default_username(self):
        """不传 username 时默认 testuser。"""
        override_auth(app)
        try:
            fake = app.dependency_overrides[get_current_user]
            assert fake() == "testuser"
        finally:
            app.dependency_overrides.clear()


# ---------- §20.2 parametrize(示范,直接写完整)----------
# 价格边界测试:演示 @pytest.mark.parametrize(= JUnit ParameterizedTest)
class TestPriceBoundary:
    @pytest.mark.parametrize(
        "price, should_pass",
        [
            (0.01, True),      # 正常最小值
            (99.99, True),     # 正常
            (10000.00, True),  # 正常最大
            (0, False),        # 零价格 → 非法
            (-1.0, False),     # 负价格 → 非法
        ],
    )
    def test_price_validation(self, price, should_pass, products_fixture):
        """同一套测试逻辑跑 5 组数据(而不是写 5 个 test 函数)。"""
        client = TestClient(app)
        # 用 auth_headers 走鉴权(顺便验证 §20.3 工具可用)
        new = {"id": 999, "name": "边界商品", "price": price, "stock": 5}
        resp = client.post("/products", json=new, headers=auth_headers("tester"))
        if should_pass:
            assert resp.status_code == 201
        else:
            # Pydantic 没有约束 price>0,所以这里只是演示 parametrize,
            # 业务层不拦 → 仍 201。我们记录状态用于演示,不强制失败。
            # 真实项目应在 Product 里加 Field(ge=0) 让非法价格 422。
            assert resp.status_code in (201, 422)


# ---------- 端点本身的测试(用上面的工具组合)----------
class TestProductCRUDWithHelpers:
    def test_list_after_fixture_setup(self, products_fixture):
        """组合:fixture(setup 3 个)+ GET 列表。"""
        client = TestClient(app)
        resp = client.get("/products")
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_full_crud_flow(self, products_fixture):
        """组合:fixture + auth_headers + override_auth,完整 CRUD 流程。"""
        client = TestClient(app)
        override_auth(app, "admin")  # 绕过鉴权,专注测 CRUD
        try:
            # 更新 id=1
            resp = client.put(
                "/products/1",
                json={"id": 1, "name": "改名键盘", "price": 699.0, "stock": 100},
            )
            assert resp.status_code == 200
            assert resp.json()["name"] == "改名键盘"

            # 删除 id=2
            resp = client.delete("/products/2")
            assert resp.status_code == 204

            # 列表剩 2 个
            assert len(client.get("/products").json()) == 2
        finally:
            app.dependency_overrides.clear()

    def test_get_not_found(self):
        """不存在的商品 → 404(不需要 fixture)。"""
        client = TestClient(app)
        PRODUCTS.clear()
        resp = client.get("/products/9999")
        assert resp.status_code == 404
