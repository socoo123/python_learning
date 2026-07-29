"""
Ch16 作业:依赖注入(Depends)—— FastAPI 最强大的设计之一。

三种依赖都已定义好(读代码理解三种模式):① 分页(类依赖)② 当前用户(Header 鉴权)
③ DB session(yield 依赖)。你填两个端点的实现,用 Depends() 注入的依赖。

    uv run pytest 03_web_framework/ch16/test_ch16_assignment.py -v

每题【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="依赖注入演示")


class Product(BaseModel):
    id: int
    name: str
    price: float


PRODUCTS: list[Product] = [
    Product(id=1, name="机械键盘", price=599.0),
    Product(id=2, name="无线鼠标", price=159.0),
    Product(id=3, name="设计模式", price=75.5),
    Product(id=4, name="Python编程", price=89.0),
    Product(id=5, name="降噪耳机", price=1299.0),
]


# ---------- 依赖 1:分页参数(类依赖,见 §16.3)----------


class Pagination:
    """把 page/size 打包,多端点复用。"""
    def __init__(self, page: int = 1, size: int = 10):
        self.page = page
        self.size = size


def get_pagination(page: int = 1, size: int = 10) -> Pagination:
    """依赖函数:FastAPI 先解析 page/size(查询参数),再构造 Pagination 返回。"""
    return Pagination(page=page, size=size)


# ---------- 依赖 2:当前用户(Header 鉴权,见 §16.5)----------


def get_current_user(x_token: str | None = Header(default=None)) -> str:
    """从 X-Token 头解析用户(模拟鉴权)。无效/缺失 → 401;有效 → 返回用户名。"""
    if not x_token or x_token == "invalid":
        raise HTTPException(status_code=401, detail="未授权")
    if x_token.startswith("user-"):
        return x_token[5:]
    raise HTTPException(status_code=401, detail="token 无效")


# ---------- 依赖 3:DB session(yield 依赖,见 §16.4)----------


def get_db():
    """模拟 DB session(Ch19 接真 DB)。
    yield 前=获取资源;yield 值=端点拿到的 session;yield 后=清理(总执行)。"""
    session = {"query_count": 0}
    try:
        yield session
    finally:
        pass                            # 模拟 session.close()


# ---------- 端点:用 Depends 注入 ----------


@app.get("/products")
def list_products(
    pagination: Pagination = Depends(get_pagination),
    user: str = Depends(get_current_user),
    db: dict = Depends(get_db),
):
    """
    【用 Depends 注入 · §16.2】签名里三个参数都用 Depends(),FastAPI 自动解析并注入。
    你直接用 pagination / user / db 当普通对象。

    思路:
        db["query_count"] += 1                                   # 用 db 依赖(模拟查询)
        start = (pagination.page - 1) * pagination.size          # 用 pagination 依赖
        return {
            "items": [p.model_dump() for p in PRODUCTS[start:start + pagination.size]],
            "page": pagination.page, "size": pagination.size, "user": user,
        }
    """
    # TODO: 用 pagination 分页、db 计数、user 返回。返回 dict(items/page/size/user)
    ...


@app.get("/me")
def who_am_i(user: str = Depends(get_current_user)):
    """
    【复用依赖 · §16.2】/me 只依赖当前用户(复用同一个 get_current_user)。
    同一个依赖函数可在多个端点复用,鉴权逻辑只写一处。

    思路:return {"user": user}
    """
    # TODO: 返回 {"user": user}
    ...
