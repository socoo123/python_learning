"""
Ch17 作业:中间件、CORS、全局异常处理。

场景:「极客商城」商品 API 上生产前的最后一道关卡。架构组 checklist:
  ① 可观测性 —— 每个请求记访问日志 + 响应头带耗时(中间件,= Servlet Filter)
  ② 维护模式 —— 运维开关一开,全站 503,但 /health 必须保活(中间件短路)
  ③ 统一错误格式 —— 业务异常(404/403/409)和程序 bug(500)都返回同一套
     {"error": 机器码, "message": 人话} 结构(全局异常处理器,= @ControllerAdvice)
  ④ 前端联调 —— CORS 已配好(脚手架),只允许 http://localhost:5173

你要填 9 处:2 个中间件 + 4 个异常处理器 + 3 个端点。

    uv sync --extra web
    uv run pytest 03_web_framework/ch17/test_ch17_assignment.py -v

每题【对应小节】指向 tutorial.md。卡住 → 回查对应 §。
"""
import logging
import time

from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger("ch17")

app = FastAPI(title="极客商城 · 商品 API(生产化)")


# ---------- CORS(脚手架,已配好 · §17.7)----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 前端联调域名;生产别用 *
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- 自定义业务异常体系(脚手架,已定义 · §17.4)----------
class NotFoundError(Exception):
    """资源不存在 → 404。"""

    def __init__(self, resource: str, id: int):
        self.resource = resource
        self.id = id


class PermissionDeniedError(Exception):
    """已认证但没权限 → 403。命名刻意避开内置 PermissionError(§17.4)。"""

    def __init__(self, username: str, action: str):
        self.username = username
        self.action = action


class ConflictError(Exception):
    """资源冲突(id 已存在)→ 409。"""

    def __init__(self, resource: str, id: int):
        self.resource = resource
        self.id = id


# ---------- 数据与可观测状态(脚手架,直接用)----------
PRODUCTS: dict[int, dict] = {
    1: {"id": 1, "name": "机械键盘", "price": 599.0, "owner": "alice"},
    2: {"id": 2, "name": "无线鼠标", "price": 159.0, "owner": "alice"},
    3: {"id": 3, "name": "降噪耳机", "price": 1299.0, "owner": "bob"},
}

REQUEST_LOG: list[str] = []  # 访问日志:log_requests 每处理完一个请求追加一行(§17.2)
MAINTENANCE_MODE = False     # 运维开关:True = 全站维护,测试会改它(§17.3)


class ProductCreate(BaseModel):
    """上架请求体。id 由商家后台指定(冲突 → 409),框架自动校验 422。"""

    id: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=50)
    price: float = Field(gt=0)
    owner: str = Field(min_length=1)


# ---------- 中间件 1:访问日志 + 计时(你填)----------


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    【计时/日志中间件 · §17.2】洋葱模型:每个请求记一行访问日志,响应头加耗时。

    任务:
      ① call_next 之前:start = time.perf_counter()(单调钟,计时专用)
      ② response = await call_next(request)(放行,必须 await)
      ③ 算耗时 duration_ms = (time.perf_counter() - start) * 1000
      ④ response.headers["X-Process-Time-ms"] = f"{duration_ms:.2f}"
      ⑤ REQUEST_LOG.append(f"{request.method} {request.url.path} -> {response.status_code}")
      ⑥ return response

    示例:
        GET /health 一次       -> 响应头含 X-Process-Time-ms;
                                  REQUEST_LOG == ["GET /health -> 200"]
        GET /products/999(404) -> 依然有耗时头;
                                  REQUEST_LOG 记 "GET /products/999 -> 404"

    提示:call_next 是 async,忘 await 拿到的是协程不是响应;
         计时用 perf_counter(= Java System.nanoTime),别用 time.time()(墙钟,会被校时影响)。
    """
    # TODO: 记时 → await call_next → 算耗时 → 加响应头 → 记访问日志 → return response
    ...


# ---------- 中间件 2:维护模式短路(你填)----------


@app.middleware("http")
async def maintenance_guard(request: Request, call_next):
    """
    【短路中间件 · §17.3】维护模式:MAINTENANCE_MODE 为 True 时,除 /health 外一律 503。

    任务:
      ① 若 MAINTENANCE_MODE 且 request.url.path != "/health":
            直接 return JSONResponse(
                status_code=503,
                content={"error": "Maintenance", "message": "系统维护中,请稍后重试"},
            )
            —— 不调 call_next = 短路,内层所有中间件和路由都不执行
      ② 否则 return await call_next(request)

    示例(测试会改 MAINTENANCE_MODE):
        维护中 GET /products/1 -> 503 {"error": "Maintenance", ...};
                                  REQUEST_LOG 不增加、响应无 X-Process-Time-ms
        维护中 GET /health     -> 200(保活,负载均衡器靠它探活)
        非维护 GET /products/1 -> 200

    提示:本中间件在 log_requests 之后注册 = 洋葱更外层,短路时 log_requests 都轮不到跑;
         只读 MAINTENANCE_MODE 不用 global(只有赋值才需要声明)。
    """
    # TODO: 维护中且非 /health → 直接 return JSONResponse(status_code=503, content={...});否则 return await call_next(request)
    ...


# ---------- 全局异常处理器:业务异常 → 统一错误格式(你填 4 个)----------


@app.exception_handler(NotFoundError)
def handle_not_found(request: Request, exc: NotFoundError):
    """
    【全局异常处理 · §17.4】NotFoundError → 404 + 统一错误格式。

    任务:return JSONResponse(
        status_code=404,
        content={"error": "NotFound", "message": f"{exc.resource} {exc.id} 不存在"},
    )

    示例:
        端点 raise NotFoundError("商品", 999)
            -> 404 {"error": "NotFound", "message": "商品 999 不存在"}
        直接调用 handle_not_found(None, NotFoundError("商品", 9))
            -> JSONResponse,status_code == 404,body == {"error": "NotFound", "message": "商品 9 不存在"}

    提示:exc 就是端点抛出的异常实例,属性 resource/id 直接用;
         统一格式 = 所有错误响应都是 {"error": 机器码, "message": 人话} 两键,前端只认这一套。
    """
    # TODO: return JSONResponse(status_code=404, content={"error": "NotFound", "message": ...})
    ...


@app.exception_handler(PermissionDeniedError)
def handle_permission_denied(request: Request, exc: PermissionDeniedError):
    """
    【全局异常处理 · §17.4】PermissionDeniedError → 403 + 统一错误格式。

    任务:return JSONResponse(
        status_code=403,
        content={"error": "PermissionDenied",
                 "message": f"用户 {exc.username} 无权{exc.action}"},
    )

    示例:
        端点 raise PermissionDeniedError("bob", "删除商品 1")
            -> 403 {"error": "PermissionDenied", "message": "用户 bob 无权删除商品 1"}
        端点 raise PermissionDeniedError("匿名", "删除商品 1")
            -> 403 {"error": "PermissionDenied", "message": "用户 匿名 无权删除商品 1"}

    提示:403 = 已认证但没权限(Ch16 讲过 401 vs 403);message 直接拼 exc 的两个属性。
    """
    # TODO: return JSONResponse(status_code=403, content={"error": "PermissionDenied", "message": ...})
    ...


@app.exception_handler(ConflictError)
def handle_conflict(request: Request, exc: ConflictError):
    """
    【全局异常处理 · §17.4】ConflictError → 409 + 统一错误格式。

    任务:return JSONResponse(
        status_code=409,
        content={"error": "Conflict", "message": f"{exc.resource} {exc.id} 已存在"},
    )

    示例:
        端点 raise ConflictError("商品", 1)
            -> 409 {"error": "Conflict", "message": "商品 1 已存在"}

    提示:409 Conflict = 请求本身合法,但和服务器现有资源冲突(如 id 撞了),
         比笼统的 400 更精确——REST 里创建冲突的标准码。
    """
    # TODO: return JSONResponse(status_code=409, content={"error": "Conflict", "message": ...})
    ...


@app.exception_handler(Exception)
def handle_unexpected(request: Request, exc: Exception):
    """
    【兜底异常处理 · §17.5】所有没注册处理器的异常 → 500 + 统一格式,绝不泄露内部细节。

    任务:
      ① logger.error("未处理异常: %s %s", request.method, request.url.path, exc_info=exc)
         —— 服务端记完整堆栈(exc_info=exc 会带上 traceback)
      ② return JSONResponse(
             status_code=500,
             content={"error": "InternalServerError",
                      "message": "服务内部错误,请稍后重试"},
         )
         —— 给用户的只有通用话术,别把 str(exc) 放进去(泄露内部信息)

    示例:
        GET /boom(脚手架端点 raise RuntimeError("磁盘满了"))
            -> 500 {"error": "InternalServerError", "message": "服务内部错误,请稍后重试"}
            -> 响应文本里绝不含 "磁盘";日志里有 "未处理异常" + 完整 Traceback

    提示:测试用 TestClient(app, raise_server_exceptions=False) 才能看到 500 响应
         (默认 TestClient 会把服务端异常重新抛出,方便调试)。
    """
    # TODO: logger.error(..., exc_info=exc) → return JSONResponse(status_code=500, content=通用话术)
    ...


# ---------- 端点:抛业务异常,响应长什么样交给处理器(你填 3 个)----------


@app.get("/products/{product_id}")
def get_product(product_id: int):
    """
    【抛业务异常 · §17.6】查商品:不存在 raise NotFoundError,被 handle_not_found 映射成 404。

    任务:product_id 不在 PRODUCTS -> raise NotFoundError("商品", product_id);
         否则 return PRODUCTS[product_id]。

    示例:
        GET /products/1   -> 200 {"id": 1, "name": "机械键盘", "price": 599.0, "owner": "alice"}
        GET /products/999 -> 404 {"error": "NotFound", "message": "商品 999 不存在"}
        GET /products/abc -> 422(路径参数类型校验,Ch15,不走业务异常)

    提示:端点只管 raise,HTTP 响应长什么样是处理器的事——这就是「统一」的意义。
    """
    # TODO: 不存在 → raise NotFoundError("商品", product_id);否则 return 商品
    ...


@app.delete("/products/{product_id}")
def delete_product(product_id: int, x_username: str | None = Header(default=None)):
    """
    【404 vs 403 · §17.6】删商品:不存在 404;是别人的 403;是自己的删掉并返回确认。

    任务:
      ① 商品不存在 -> raise NotFoundError("商品", product_id)
      ② 商品 owner != x_username
            -> raise PermissionDeniedError(x_username or "匿名", f"删除商品 {product_id}")
      ③ del PRODUCTS[product_id],return {"deleted": product_id, "name": 商品名}

    示例(种子:1/2 是 alice 的,3 是 bob 的):
        DELETE /products/3(X-Username: bob)   -> 200 {"deleted": 3, "name": "降噪耳机"}
        DELETE /products/1(X-Username: bob)   -> 403 "用户 bob 无权删除商品 1"
        DELETE /products/1(不带 header)       -> 403 "用户 匿名 无权删除商品 1"
        DELETE /products/999(X-Username: bob) -> 404 "商品 999 不存在"

    提示:先 404 再 403(不存在的商品不暴露归属,Ch16 同款分工);
         参数名 x_username 自动映射请求头 X-Username(下划线转连字符);
         真实项目身份用 Ch16 的 Depends 注入,本章为聚焦异常处理简化为直接读 header。
    """
    # TODO: 404 守卫 → 403 守卫 → del + return {"deleted": ..., "name": ...}
    ...


@app.post("/products", status_code=201)
def create_product(body: ProductCreate):
    """
    【409 冲突 · §17.6】上架商品:id 已存在 → 409,否则上架并 201 返回新商品。

    任务:
      ① body.id 已在 PRODUCTS -> raise ConflictError("商品", body.id)
      ② 否则 PRODUCTS[body.id] = {"id": body.id, "name": body.name,
                                  "price": body.price, "owner": body.owner}
      ③ return 新商品 dict

    示例:
        POST /products {"id": 4, "name": "显示器", "price": 899, "owner": "alice"}
            -> 201 {"id": 4, "name": "显示器", "price": 899.0, "owner": "alice"}
        再 POST 同 id      -> 409 {"error": "Conflict", "message": "商品 4 已存在"}
        POST price=-1      -> 422(ProductCreate 的 Field(gt=0),函数体不执行)

    提示:body 是 Pydantic 模型,用 body.id / body.name 取值;
         装饰器已写好 status_code=201,你只管用 dict 构造商品。
    """
    # TODO: id 撞了 → raise ConflictError;否则构造 dict 存入 PRODUCTS 并 return
    if body.id in PRODUCTS:
        raise ConflictError("商品", body.id)
    product = {"id": body.id, "name": body.name, "price": body.price, "owner": body.owner}
    PRODUCTS[body.id] = product
    return product


# ---------- 脚手架端点(已写好,供测试/演示)----------


@app.get("/health")
def health():
    """健康检查。维护模式下也必须可用(§17.3)。"""
    return {"status": "ok"}


@app.get("/boom")
def boom():
    """故意模拟程序 bug:未注册处理器的 RuntimeError → 兜底处理器 → 500(§17.5)。"""
    raise RuntimeError("磁盘满了")
