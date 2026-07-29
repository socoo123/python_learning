"""
Ch20 作业:测试 API 进阶(TestClient + fixtures + 覆盖率)。

本章特殊:【你写的是测试代码】,不是业务实现。下面分两块——

  ① 被测 app(完整实现,不擦):
     - 商品内存 CRUD(POST/GET/PUT/DELETE)
     - get_current_user 依赖(从 Authorization 头解析 token → 用户名;测它=麻烦)
  ② 三个【测试工具函数 / fixture 工厂】(你填):
     - make_product_fixture()      → §20.1 fixture(= @BeforeEach 升级)
     - auth_headers(token)         → §20.3 构造鉴权请求头
     - override_auth(app)          → §20.4 依赖覆盖(绕过鉴权,= Spring @MockBean)

运行:
    uv run pytest 03_web_framework/ch20/ -v
    uv run pytest 03_web_framework/ch20/ --cov=ch20_assignment --cov-report=term-missing

每题【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI, HTTPException, Header, status
from fastapi.testclient import TestClient
from pydantic import BaseModel


# =====================================================================
# ① 被测 app(完整实现,不擦)——商品内存 CRUD + 鉴权依赖
# =====================================================================

app = FastAPI(title="Ch20 测试练习 - 商品 CRUD")


class Product(BaseModel):
    id: int
    name: str
    price: float
    stock: int


# 内存存储(全局 dict)。测试用 fixture 在 setup 前清空、teardown 后清空。
PRODUCTS: dict[int, Product] = {}


def get_current_user(authorization: str | None = Header(default=None)) -> str:
    """
    从 Authorization 头解析 token,返回用户名。

    真实场景这里要解 JWT、查 DB、验过期……非常麻烦。测试时我们用
    dependency_overrides 直接把它替换掉,跳过所有鉴权逻辑。见 §20.4。
    """
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少或非法的 Authorization 头",
        )
    token = authorization.removeprefix("Bearer ")
    # 演示用:token 直接当用户名(真实项目这里要解 JWT)
    if not token:
        raise HTTPException(status_code=401, detail="空 token")
    return token


@app.get("/products")
def list_products() -> list[Product]:
    """列出所有商品(无需鉴权)。"""
    return list(PRODUCTS.values())


@app.get("/products/{product_id}")
def get_product(product_id: int) -> Product:
    """单个商品(无需鉴权)。"""
    if product_id not in PRODUCTS:
        raise HTTPException(status_code=404, detail="商品不存在")
    return PRODUCTS[product_id]


@app.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(product: Product, user: str = Depends(get_current_user)) -> Product:
    """新建商品(需鉴权)。"""
    PRODUCTS[product.id] = product
    return product


@app.put("/products/{product_id}")
def update_product(
    product_id: int, product: Product, user: str = Depends(get_current_user)
) -> Product:
    """更新商品(需鉴权)。"""
    if product_id not in PRODUCTS:
        raise HTTPException(status_code=404, detail="商品不存在")
    PRODUCTS[product_id] = product
    return product


@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, user: str = Depends(get_current_user)) -> None:
    """删除商品(需鉴权)。"""
    if product_id not in PRODUCTS:
        raise HTTPException(status_code=404, detail="商品不存在")
    del PRODUCTS[product_id]


# =====================================================================
# ② 三个测试工具(你填)——这才是本章作业
# =====================================================================

def make_product_fixture():
    """
    【fixture 工厂 · §20.1】返回一个 pytest fixture 函数。

    功能(= JUnit @BeforeEach 的升级版,带 teardown):
      - setup:往 PRODUCTS 里塞 3 个商品(id=1/2/3)
      - yield 把控制权交回测试(测试期间这 3 个商品可用)
      - teardown:测试结束清空 PRODUCTS(用 .clear())

    关键写法(必须 yield,不能用 return):
        @pytest.fixture
        def _products_fixture():
            PRODUCTS.update({1: Product(...), 2: Product(...), 3: Product(...)})
            yield list(PRODUCTS.values())   # 测试期间的「返回值」
            PRODUCTS.clear()                # teardown
        return _products_fixture

    提示:
      - 用 @pytest.fixture 装饰器
      - fixture 是「带 setup + yield + teardown 的函数」
      - 这里要 return 这个 fixture 函数本身(不是调用它)
    """
    @pytest.fixture
    def _products_fixture():
        # TODO: setup —— PRODUCTS.update({1: Product(...), 2: ..., 3: ...})
        # TODO: yield list(PRODUCTS.values())   # 测试期间的返回值
        # TODO: teardown —— PRODUCTS.clear()
        ...

    return _products_fixture


def auth_headers(token: str) -> dict[str, str]:
    """
    【鉴权请求头 · §20.3】构造带 Authorization 的 headers dict。

    get_current_user 期望形如 "Bearer <token>" 的头。测试带鉴权的端点
    (POST/PUT/DELETE)时,用 client.post(..., headers=auth_headers("testuser"))。

    思路:返回 {"Authorization": f"Bearer {token}"}

    Java 对比:= 测试 RestTemplate 时手动塞 HttpHeaders.set("Authorization", ...)。
    """
    # TODO: return {"Authorization": f"Bearer {token}"}
    ...


def override_auth(test_app: FastAPI, username: str = "testuser") -> None:
    """
    【依赖覆盖 · §20.4】用 app.dependency_overrides 把 get_current_user 替换掉,
    绕过鉴权。= Spring @MockBean / @WithMockUser。

    关键 API(必背):
        test_app.dependency_overrides[get_current_user] = lambda: username

    思路:对 test_app 的 dependency_overrides 字典,把键 get_current_user 映射到
          一个返回 username 的可调用对象。

    注意:测试结束要还原(test 里用 try/finally 或 monkeypatch 清掉)。
    """
    # TODO: test_app.dependency_overrides[get_current_user] = lambda: username
    ...
