"""
Ch17 作业:中间件、CORS、全局异常处理。

CORS 配置 + NotFoundError 定义已给。你填三处:① 计时中间件 ② 异常处理器 ③ 端点抛业务异常。

    uv run pytest 03_web_framework/ch17/test_ch17_assignment.py -v

每题【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="中间件与异常演示")


# ---------- CORS 中间件(已配好,了解即可)----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- 自定义业务异常(已定义)----------
class NotFoundError(Exception):
    """资源不存在的业务异常。会被全局处理器映射成 404。"""
    def __init__(self, resource: str, id: int):
        self.resource = resource
        self.id = id


# ---------- 全局异常处理器(你填)----------


# TODO: 注册 NotFoundError 的异常处理器,返回统一格式的 404 JSON
@app.exception_handler(NotFoundError)
def handle_not_found(request: Request, exc: NotFoundError):
    """
    【全局异常处理 · §17.2】把 NotFoundError 映射成 404 + 统一错误格式。

    思路:return JSONResponse(
        status_code=404,
        content={"error": "NotFound", "message": f"{exc.resource} {exc.id} 不存在"},
    )
    """
    # TODO: 返回 JSONResponse(404, {"error":"NotFound", "message":...})
    ...


# ---------- 计时中间件(你填)----------


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    【中间件 · §17.1】给每个请求计时,在响应头加 X-Process-Time-ms。

    思路(洋葱模型:进来记时 → call_next 放行 → 出来算耗时 → 改响应头):
        start = time.time()
        response = await call_next(request)              # 放行(call_next 是 async,要 await)
        duration_ms = (time.time() - start) * 1000
        response.headers["X-Process-Time-ms"] = f"{duration_ms:.2f}"
        return response
    """
    # TODO: 记时 → await call_next → 算耗时 → 加响应头 → return response
    ...


# ---------- 数据 + 端点 ----------
class Product(BaseModel):
    id: int
    name: str


PRODUCTS: dict[int, Product] = {
    1: Product(id=1, name="机械键盘"),
    2: Product(id=2, name="无线鼠标"),
}


@app.get("/products/{product_id}")
def get_product(product_id: int):
    """
    【端点抛业务异常 · §17.3】不存在时 raise NotFoundError(被全局处理器接住,映射 404)。

    思路:if product_id not in PRODUCTS: raise NotFoundError("Product", product_id)
         return PRODUCTS[product_id]
    """
    # TODO: 不存在 raise NotFoundError;否则返回
    ...


@app.get("/error")
def trigger_error():
    raise ValueError("故意出错")          # 未注册处理器的异常 → 500


@app.get("/health")
def health():
    return {"status": "ok"}
