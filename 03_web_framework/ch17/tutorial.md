# Ch17 · 中间件、CORS、异常处理

> **预计**:0.5 天 ｜ **前置**:Ch16 ｜ **M3 第一批(Ch13–17)收尾**
> **目标**:掌握 FastAPI 的三类工程化能力——**中间件**(= Servlet Filter)、**全局异常处理**(= `@ControllerAdvice`)、**CORS** 跨域。这是 API 上生产的基础。

> 📐 **本教程的契约**:§17.1–§17.3 对应作业三处填空。

---

## 🗺️ 本章地图

**作业 ↔ 教程对应表**:

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `log_requests`(中间件) | §17.1 | @app.middleware + call_next(洋葱模型) |
| `handle_not_found`(异常处理器) | §17.2 | @app.exception_handler → 统一错误格式 |
| `get_product`(抛业务异常) | §17.3 | raise 自定义异常 → 被处理器映射 |

---

## ⏱️ 学习路径:费曼五步(约 45-60 分钟)

① 预览猜 → ② 填三处实现 → ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## ① 预览猜

1. Spring 用 `Filter` / `HandlerInterceptor` 在请求前后做横切(日志/鉴权/计时)。FastAPI 对应什么?
2. Spring 用 `@ControllerAdvice` + `@ExceptionHandler` 统一处理异常。FastAPI 怎么注册异常处理器?
3. 前端跨域报 CORS 错,后端怎么放行?
4. 中间件在请求进/出各执行一次,这个「套娃」结构叫什么模型?

---

## §17.1 中间件:洋葱模型(对应:`log_requests`)🔴

中间件在**每个请求**前后执行,用于横切关注点(日志、计时、鉴权、CORS)。结构是**洋葱**——请求层层进入、响应层层出来:

```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # —— 请求进来时执行(call_next 之前)——
    start = time.time()
    response = await call_next(request)     # 放行:交给下一层中间件/路由
    # —— 响应出来时执行(call_next 之后)——
    duration_ms = (time.time() - start) * 1000
    response.headers["X-Process-Time-ms"] = f"{duration_ms:.2f}"
    return response
```

**三个关键点**:
- `call_next(request)` 是「放行」——把请求交给下一层(最终到路由)。`call_next` 是 async,必须 `await`(Ch18 异步详讲)。
- `call_next` 返回 `response`,你可以在返回前**修改它**(这里加了个响应头)。
- `call_next` **之前**的代码 = 请求进入时跑;**之后**的代码 = 响应出来时跑。这就是洋葱。

> 🟡 **Java 对比**:= Servlet `Filter` / Spring `HandlerInterceptor`。`doFilter`/`proceed` 对应 `call_next`。FastAPI 一个装饰器 + 函数搞定,比 Java 的 Filter 接口简洁。

### 多个中间件的顺序

注册多个中间件时,**后注册的先执行**(洋葱最外层)。中间件包着中间件,最里面是路由。

> ✅ 做 `log_requests` 题:`start` → `await call_next` → 算耗时 → 加 header → `return response`。

---

## §17.2 全局异常处理:统一错误格式(对应:`handle_not_found`)🔴

**问题**:业务代码里 `raise NotFoundError(...)`,你希望它自动变成「404 + 统一 JSON 格式」,而不是让用户看到 500 或 FastAPI 默认错误体。

**解法**:`@app.exception_handler(异常类型)` 注册处理器:

```python
from fastapi.responses import JSONResponse

@app.exception_handler(NotFoundError)
def handle_not_found(request: Request, exc: NotFoundError):
    # exc 是抛出的异常实例;request 是请求对象
    return JSONResponse(
        status_code=404,
        content={"error": "NotFound", "message": f"{exc.resource} {exc.id} 不存在"},
    )

# 业务代码里
@app.get("/products/{id}")
def get_product(id: int):
    if id not in PRODUCTS:
        raise NotFoundError("Product", id)   # 抛出 → 被上面的处理器接住 → 返 404
    return PRODUCTS[id]
```

**好处**:
- 业务代码只管 `raise`(干净),不用每处手写 `JSONResponse(404)`。
- 错误格式**统一**(所有 NotFoundError 都返 `{"error":"NotFound","message":...}`),前端好处理。

> 🤯 **Java 对比**:= `@ControllerAdvice` + `@ExceptionHandler(NotFoundError.class)`。FastAPI 一个装饰器搞定。这是生产 API 的标配——所有业务异常统一格式,前端只认一套错误结构。

> ✅ 做 `handle_not_found` 题:返回 `JSONResponse(404, {"error":"NotFound","message":...})`。

---

## §17.3 自定义业务异常(对应:`get_product`)

定义业务异常(继承 Exception),在端点里 raise,处理器自动映射:

```python
class NotFoundError(Exception):
    def __init__(self, resource, id):
        self.resource = resource
        self.id = id

@app.get("/products/{id}")
def get_product(id: int):
    if id not in PRODUCTS:
        raise NotFoundError("Product", id)   # 自动被 §17.2 的处理器映射成 404
    return PRODUCTS[id]
```

> 业务异常是「**业务规则违反**」(资源不存在、库存不足、权限不够),和「**程序 bug**」(ValueError、KeyError)区分开。前者映射成 4xx,后者是 500。

> ✅ 做 `get_product` 题:不存在 `raise NotFoundError(...)`,否则返回。

---

## §17.4 CORS:跨域资源共享

浏览器有同源策略:前端 `http://localhost:3000` 调后端 `http://localhost:8000` 会被拦。后端配 CORS 放行:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],   # 允许的前端域名(生产别用 *)
    allow_methods=["*"],                        # 允许的 HTTP 方法
    allow_headers=["*"],                        # 允许的请求头
    allow_credentials=True,                     # 允许带 cookie
)
```

> 🟡 **Java 对比**:= Spring `@CrossOrigin` / `CorsFilter` / WebMvcConfigurer。FastAPI 一个 add_middleware 搞定。
>
> ⚠️ `allow_origins=["*"]` + `allow_credentials=True` 不能同时用(浏览器拒绝)。生产环境一定要限定具体域名,别用 `*`。

---

## §17.5 未处理的异常 = 500

业务代码抛了**没注册处理器**的异常(如 `ValueError`),FastAPI 返 **500 Internal Server Error**。生产环境应该:
- 注册一个兜底的 `Exception` 处理器,把 500 也格式化、记日志(不暴露堆栈给用户)。
- 用 Ch12 的 logging 记录完整异常栈。

```python
@app.exception_handler(Exception)         # 兜底所有异常
def handle_all(request, exc):
    logger.exception("未处理异常")         # 记日志
    return JSONResponse(500, {"error": "InternalServerError", "message": "服务内部错误"})
```

---

## §17.6 速查:Java 横切机制对照

| FastAPI | Java 对应 | 用途 |
|---------|-----------|------|
| `@app.middleware("http")` | Servlet Filter / Interceptor | 请求前后横切(日志/计时) |
| `@app.exception_handler(X)` | @ControllerAdvice + @ExceptionHandler | 异常 → HTTP 响应 |
| `add_middleware(CORSMiddleware)` | @CrossOrigin / CorsFilter | 跨域 |
| `Depends`(Ch16) | @Autowired | 依赖注入 |

---

## §17.7 Java 老手常踩的坑 ⚠️

1. **`call_next` 必须 `await`**:它是 async,忘 await 会得到协程对象而非响应。
2. **中间件顺序**:后注册先执行(洋葱外层)。顺序错了可能影响行为(如鉴权要在日志前)。
3. **CORS `*` + credentials 冲突**:浏览器不允许,二选一。生产限定域名。
4. **业务异常 vs 程序异常**:业务异常(4xx)用自定义异常 + 处理器;程序异常(500)兜底处理 + 记日志。
5. **异常处理器没注册就 raise**:NotFoundError 没 handler 就是 500(被当普通异常)。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `log_requests` | 中间件(洋葱模型) | 🟡 |
| `handle_not_found` | 全局异常处理 | 🟡 |
| `get_product` | 抛业务异常 | 🟢 |

```bash
uv run pytest 03_web_framework/ch17/test_ch17_assignment.py -v
```

---

## ✅ 自测

- [ ] 能说清中间件的「洋葱模型」(call_next 前后各执行一次)
- [ ] 能用 `@app.exception_handler` 把业务异常映射成统一格式的 HTTP 响应
- [ ] 知道 CORS 怎么配,以及 `*` + credentials 的坑
- [ ] 3 个作业全绿

## 🎓 费曼挑战

1. 「中间件的洋葱模型是什么?call_next 前后的代码分别在何时执行?」— 重读 §17.1
2. 「为什么用自定义异常 + 全局处理器,而不是每处手写 JSONResponse(404)?」— 重读 §17.2/§17.3

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步:M3 第一批(Ch13–17)收尾

Ch13–17 学完,你掌握了 FastAPI 的**基础全貌**:调 API(httpx)→ 写 API(FastAPI + Pydantic)→ 参数(路由/查询/分页)→ 依赖注入 → 中间件/异常/CORS。

下一批 **Ch18–22**(你说一声我就写):
- **Ch18** 异步 async/await(Ch18 重点,Python 和 Java 最大差异之一)
- **Ch19** SQLAlchemy 数据库 ORM(接真 DB,告别内存存储)
- **Ch20** 测试 API(TestClient 进阶 + fixtures + 覆盖率)
- **Ch21** JWT 认证授权
- **Ch22** 部署(uvicorn/gunicorn/Docker)+ Flask/Django 对比

学完 Ch18–22,你就能做**考试系统 lab** 了。
