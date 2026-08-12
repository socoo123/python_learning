"""
Ch20 作业:测试 API 进阶(TestClient + fixtures + 覆盖率)。

主线场景:你是「极客商城」新接盘的后端。前同事留下一套能跑的商品 CRUD API
(内存存储 + Bearer 鉴权 + Pydantic 校验),但一行测试都没写。老板规定:
合并新代码前,测试套件必须全绿、核心逻辑覆盖率 ≥ 90%。你的任务:给这套
API 从零搭 pytest 测试套件。

本章特殊:【你写的是测试代码】,不是业务实现。文件分两块——

  ① 被测 app(完整实现,不擦):
     - Product 模型(Field(gt=0) 校验,Ch14 的套路)
     - 商品内存 CRUD 五个端点(GET 列表 / GET 单个 / POST / PUT / DELETE)
     - get_current_user 依赖(解析 Authorization: Bearer <token>)
     - SEED_PRODUCTS 种子数据(products_fixture 用)
  ② 七个测试工具函数 / fixture(你填):
     - auth_headers(token)            → §20.1 构造 Bearer 请求头
     - products_fixture()             → §20.2 fixture:seed 3 商品 + yield + clear
     - api_client()                   → §20.2 fixture:TestClient + 清 dependency_overrides
     - override_auth(test_app, ...)   → §20.3 依赖覆盖(= Spring @MockBean)
     - admin_client(api_client)       → §20.3 fixture 组合:免鉴权客户端(综合)
     - price_validation_cases()       → §20.4 parametrize 数据源:价格边界 → 201/422
     - not_found_id_cases()           → §20.4 parametrize 数据源:404 的 id

运行:
    uv sync --extra web
    uv run pytest 03_web_framework/ch20/test_ch20_assignment.py -v
    uv run pytest 03_web_framework/ch20/test_ch20_assignment.py --cov=ch20_assignment --cov-report=term-missing

每题【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field


# =====================================================================
# ① 被测 app(完整实现,不擦)——商品 CRUD + 鉴权依赖 + 种子数据
# =====================================================================

app = FastAPI(title="Ch20 测试练习 · 极客商城商品 API")


class Product(BaseModel):
    """商品模型。Field 约束(Ch14):价格必须 > 0、库存不能为负,违反 → 422。"""

    id: int
    name: str = Field(min_length=1, max_length=50)
    price: float = Field(gt=0)
    stock: int = Field(ge=0)


# 内存存储(全局 dict)。测试隔离手段 = fixture 的 setup/teardown(§20.2)。
PRODUCTS: dict[int, Product] = {}

# 种子数据:products_fixture 往 PRODUCTS 里塞的就是这三个。
SEED_PRODUCTS: list[Product] = [
    Product(id=1, name="机械键盘", price=599.0, stock=42),
    Product(id=2, name="无线鼠标", price=159.0, stock=0),
    Product(id=3, name="设计模式", price=75.5, stock=128),
]


def get_current_user(authorization: str | None = Header(default=None)) -> str:
    """
    从 Authorization 头解析 token,返回用户名。

    真实项目这里要解 JWT、查 DB、验过期(Ch21 的活)。测试时我们用
    dependency_overrides 直接把它替换掉,跳过所有鉴权逻辑(§20.3)。
    """
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少或非法的 Authorization 头",
        )
    token = authorization.removeprefix("Bearer ")
    # 演示用:token 直接当用户名(真实项目这里要解 JWT)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="空 token"
        )
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
# ② 七个测试工具(你填)——这才是本章作业
# =====================================================================


def auth_headers(token: str) -> dict[str, str]:
    """
    【构造鉴权请求头 · §20.1】返回带 Authorization 的 headers dict。

    场景:POST/PUT/DELETE 都要 `Authorization: Bearer <token>` 头,
    每个测试手写太啰嗦,封装成一行函数,测试里这样用:
    client.post("/products", json=payload, headers=auth_headers("alice"))。

    任务:返回 {"Authorization": f"Bearer {token}"}

    示例:
        auth_headers("alice")         -> {"Authorization": "Bearer alice"}
        auth_headers("token-abc-123") -> {"Authorization": "Bearer token-abc-123"}

    提示:就是一行 f-string;别手写 "Bearer" + token——漏空格就是 401(§20.1 ❌→✅)。
         Java 里是 headers.setBearerAuth(token),这里 dict 就是头。
    """
    # TODO: return {"Authorization": f"Bearer {token}"}
    ...


@pytest.fixture
def products_fixture():
    """
    【fixture:测试数据 · §20.2】每个测试前塞 3 个种子商品,测试后清空。

    场景:商品接口的每个测试都要「库里有已知数据」且「互不污染」
    (= JUnit @BeforeEach + @AfterEach,pytest 用一个函数搞定)。

    任务:
      ① PRODUCTS.update({p.id: p for p in SEED_PRODUCTS})   # setup
      ② yield list(PRODUCTS.values())                        # 测试拿到的值
      ③ PRODUCTS.clear()                                     # teardown(必须!)

    示例(测试侧视角):
        def test_a(products_fixture): len(PRODUCTS) == 3;products_fixture[0].name == "机械键盘"
        某测试删了 PRODUCTS[1] → 下一个用 fixture 的测试仍看到 3 个(隔离生效)

    提示:teardown 只能写在 yield 后;写在 return 后是死代码(§20.2 ❌→✅)。
         别忘了头顶的 @pytest.fixture。
    """
    # TODO: setup —— PRODUCTS.update({p.id: p for p in SEED_PRODUCTS})
    # TODO: yield list(PRODUCTS.values())   # 测试期间拿到的值
    # TODO: teardown —— PRODUCTS.clear()
    ...


@pytest.fixture
def api_client():
    """
    【fixture:客户端 + 全局状态清理 · §20.2】产出 TestClient,测试后清空依赖覆盖。

    场景:app 是模块级单例,dependency_overrides 是它身上的全局可变 dict——
    测试塞了 mock 不清,下个测试的鉴权就被静默绕过(单跑绿、全跑红的经典 bug)。

    任务:
      ① yield TestClient(app)
      ② teardown:app.dependency_overrides.clear()

    示例:
        def test_list(api_client): api_client.get("/products").status_code == 200
        某测试往 app.dependency_overrides 塞了 mock → 下一个用 api_client 的测试看到 {}

    提示:结构和 products_fixture 一模一样——yield 之前 setup、之后 teardown。
    """
    # TODO: yield TestClient(app)
    # TODO: teardown —— app.dependency_overrides.clear()
    ...


def override_auth(test_app: FastAPI, username: str = "testuser") -> None:
    """
    【依赖覆盖 · §20.3】把 get_current_user 换成返回固定用户的假函数,绕过鉴权。
    = Spring 的 @MockBean / @WithMockUser。

    场景:测「创建商品」时不想碰鉴权(真实实现要解 JWT、查 DB),
    把整个依赖换成假实现,让 Depends(get_current_user) 直接拿到 username。

    任务:test_app.dependency_overrides[get_current_user] = lambda: username

    示例:
        override_auth(app)                -> 之后不带 Authorization 的 POST 也 201
        override_auth(app, "someone")     -> app.dependency_overrides[get_current_user]() == "someone"

    提示:键是【函数对象】get_current_user,不是字符串 "get_current_user"(§20.3 ❌→✅);
         值是零参可调用。还原由 api_client 的 teardown 负责,你不用管。
    """
    # TODO: test_app.dependency_overrides[get_current_user] = lambda: username
    ...


@pytest.fixture
def admin_client(api_client):
    """
    【fixture 组合(本章综合)· §20.3】「已登录管理员客户端」:api_client + override_auth。

    场景:测试套件里 90% 的用例是「已登录用户干业务」,不该每个测试都手写
    override。把两个你已写好的东西组合起来,一次声明、直接可用。

    任务:
      ① 参数声明 api_client(fixture 依赖 fixture)
      ② override_auth(app, username="admin")
      ③ yield api_client

    示例:
        def test_create(admin_client):   # 不带 Authorization
            admin_client.post("/products", json={...}).status_code == 201

    提示:清理不用你写——下层 api_client 的 teardown 会自动清掉 override。
         组合时,清理职责放在最下层 fixture。
    """
    # TODO: override_auth(app, username="admin") → yield api_client
    ...


def price_validation_cases() -> list[tuple[float, int]]:
    """
    【parametrize 数据源:价格边界 · §20.4】返回 [(价格, 期望状态码), ...]。

    场景:Product 有 Field(gt=0) 约束(Ch14)——0 和负价该被 422 拦下。
    老板要求边界都有测试,你提供数据,@pytest.mark.parametrize 负责展开成
    独立用例(= JUnit @MethodSource 的数据方法)。

    任务:返回 tuple 列表,≥2 组合法价(201)+ ≥1 组 0 或负价(422)。

    示例数据(可直接用):
        (0.01, 201)    # 最小合法价
        (599.0, 201)   # 正常价
        (0.0, 422)     # 违反 gt=0
        (-1.0, 422)    # 负价

    提示:别只返回合法数据——元测试会检查你确实覆盖了非法分支(防蒙对)。
    """
    # TODO: return [(0.01, 201), (599.0, 201), ..., (0.0, 422), (-1.0, 422)]
    ...


def not_found_id_cases() -> list[int]:
    """
    【parametrize 数据源:404 边界 · §20.4】返回「确定不存在」的商品 id 列表。

    场景:运营问「删不存在的商品返回什么?」——答:404。把不存在的 id
    集中成一个数据源,GET / PUT / DELETE 三个端点复用。

    任务:返回 ≥2 个 int id,且都不能在 SEED_PRODUCTS 的 {1, 2, 3} 里。

    示例:
        [999, -1, 123456]

    提示:元测试会把每个 id 和种子数据对账——返回已存在的 id 算蒙对,过不了。
    """
    # TODO: return [999, -1, 123456](或任何 ≥2 个不在 {1,2,3} 里的 int)
    ...
