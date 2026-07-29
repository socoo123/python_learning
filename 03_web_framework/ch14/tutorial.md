# Ch14 · FastAPI 入门:第一个 API + Pydantic 模型

> **预计**:1 天 ｜ **前置**:Ch13 ｜ **M3 第二章**
> **目标**:理解 FastAPI 的核心理念——「**类型注解驱动一切**」。写一个端点,类型注解就自动帮你:解析参数、校验数据、序列化 JSON、生成文档。对比 Spring Boot,样板代码少 80%。

> 📐 **本教程的契约**:§14.1–§14.5 对应作业。本章建商品管理 mini app,后续章节在此基础上加功能。

---

## 🗺️ 本章地图

**作业 ↔ 教程对应表**:

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `ProductCreate` 模型 | §14.2/§14.3 | Pydantic 模型 + Field 校验 |
| `list_products` | §14.1 | 路由 + 自动序列化 |
| `create_product` | §14.2 | 请求体模型(model_dump) |
| `get_product` | §14.5 | 路径参数 + HTTPException |

---

## ⏱️ 学习路径:费曼五步(约 60-90 分钟)

① 预览猜 → ② 写 assignment → ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

> 💡 本章开始,作业形态变了:不是填函数,而是**填 API 端点 + 模型**。测试用 TestClient 发 HTTP 请求验证。

---

## ① 预览猜

1. Spring 写 `@GetMapping("/products")` + 手动 `@RequestBody` + `@Valid` + Jackson 序列化。FastAPI 怎么用类型注解一次性搞定这些?
2. Java DTO 用 class + Lombok。FastAPI 用什么定义「请求/响应数据结构」并自动校验?
3. 参数校验失败(如 price=-1),Spring 返回 400,FastAPI 默认返回什么状态码?
4. Spring 启动后看接口文档要装 Swagger。FastAPI 自带文档在哪个路径?
5. 不启动服务怎么测自己的 API?

---

## §14.1 FastAPI 核心理念 + 第一个端点

FastAPI 的设计哲学:**你写类型注解,框架自动干活**。

```python
from fastapi import FastAPI

app = FastAPI(title="商品管理 API")

@app.get("/products")
def list_products():
    return list(PRODUCTS.values())
```

就这么几行,你得到了:
- 一个 GET `/products` 端点(= Spring `@GetMapping("/products")`)
- 返回值**自动序列化成 JSON**(Product 对象 → `{"id":1,"name":...}`),不用手动 json.dumps
- 自动生成 **OpenAPI 文档**(启动后访问 `/docs` 有 Swagger UI)
- 启动命令:`uvicorn ch14_assignment:app --reload`(Ch22 讲部署)

> 🟡 **Java 对比**:Spring 要 `@RestController` + `@GetMapping` + 返回值靠 Jackson 序列化。FastAPI 更简洁,且**类型注解参与业务**(不只是文档)。

### 启动看效果(可选,非作业必需)

```bash
uv run uvicorn 03_web_framework.ch14.ch14_assignment:app --reload
# 浏览器开 http://localhost:8000/docs 看 Swagger UI
# http://localhost:8000/products 看商品列表
```
> 作业用 TestClient 测,不需要手动启动。但建议至少跑一次看 `/docs` 的自动文档,体会「类型驱动」。

> ✅ 做 `list_products` 题:`return list(PRODUCTS.values())`。

---

## §14.2 Pydantic 模型:请求/响应数据结构(对应:`ProductCreate`、`create_product`)🔴

**Pydantic `BaseModel`** = Java DTO + 自动校验 + 自动(反)序列化,三位一体。

```python
from pydantic import BaseModel, Field

class ProductCreate(BaseModel):
    name: str
    price: float = Field(gt=0, description="价格必须大于 0")   # gt=0:必须 > 0
    stock: int = 0                                              # 默认值
```

### 用在端点参数 = 请求体

```python
@app.post("/products", status_code=201)
def create_product(p: ProductCreate):
    # p 已经是 ProductCreate 实例,FastAPI 自动做了:
    #   ① 解析请求 JSON body
    #   ② 按 ProductCreate 校验(类型 + Field 约束)
    #   ③ 校验失败自动返回 422(你不用写校验代码!)
    return ...
```

**FastAPI 看到 `p: ProductCreate` 这个类型注解**,就自动把请求体 JSON 解析成 `ProductCreate` 实例传给你。校验失败它自动返 422。你只管用 `p.name`、`p.price`。

> 🤯 **Java 老手震惊点**:Spring 要 `@RequestBody @Valid ProductCreate p` + DTO 上写 `@Positive` + 配 Bean Validation + 全局异常处理 422。FastAPI 一个类型注解全搞定。

### `model_dump()`:模型转 dict(Pydantic v2)

```python
p = ProductCreate(name="键盘", price=599)
p.model_dump()        # {"name":"键盘", "price":599.0, "stock":0}   ← v2 方法
# (Pydantic v1 是 p.dict(),已废弃)
```

本节作业用它把 ProductCreate 转成 dict,再 `**` 解包造 Product:
```python
product = Product(id=_next_id, **p.model_dump())
```

> ✅ 做 `ProductCreate` + `create_product`:模型加 `Field(gt=0)`;端点用 `p.model_dump()` 造 Product 存入。

---

## §14.3 自动校验:Field 约束

Pydantic 的 `Field` 给字段加约束。校验失败 FastAPI 自动返 **422 Unprocessable Entity**(不是 400):

| 约束 | 含义 | 示例 |
|------|------|------|
| `gt=0` | 大于 0 | price 必须 > 0 |
| `ge=0` | 大于等于 0 | |
| `lt=100` | 小于 | |
| `le=100` | 小于等于 | |
| `min_length=1` | 字符串最小长度 | name 非空 |
| `default=...` | 默认值 | stock=0 |

```python
class ProductCreate(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(gt=0)
    stock: int = 0
```

不写约束时,**类型本身就在校验**——传 `"price": "abc"` 会被拒(类型不符 → 422)。

---

## §14.4 自动序列化 + OpenAPI 文档

返回 Pydantic 模型(或 list/dict),FastAPI **自动转 JSON**:
```python
@app.get("/products")
def list_products():
    return list(PRODUCTS.values())   # [Product, Product] → JSON 数组
```

**自动文档**:启动后 `/docs` 有 Swagger UI,`/redoc` 有 ReDoc。这些文档是根据你的**类型注解**生成的——你改模型,文档自动更新。这是 FastAPI 最爽的特性之一。

> 🟡 **Java 对比**:Spring 要 springdoc/swagger 依赖 + 配置。FastAPI 内置,零配置。

---

## §14.5 路径参数 + HTTPException(对应:`get_product`)

```python
@app.get("/products/{product_id}")     # {product_id} 是路径参数
def get_product(product_id: int):       # int 注解:自动把 URL 的 "1" 转 int,非数字返 422
    if product_id not in PRODUCTS:
        raise HTTPException(status_code=404, detail="商品不存在")
    return PRODUCTS[product_id]
```

**两个关键点**:
- `{product_id}` 在路径里,同名参数自动从 URL 提取。`int` 注解做类型转换+校验。
- `HTTPException(status_code, detail)` 抛出 HTTP 错误响应。= Spring 的 `ResponseStatusException`。

> ✅ 做 `get_product` 题:判存在性,不存在 `raise HTTPException(404, ...)`,否则返回。

---

## §14.6 TestClient:测自己的 API

不用启动服务,`TestClient` 直接对 app 发请求(基于 httpx,Ch13 学过):

```python
from fastapi.testclient import TestClient
from ch14_assignment import app

client = TestClient(app)

resp = client.get("/products")
resp.status_code       # 200
resp.json()            # [{"id":1,...}, ...]

resp = client.post("/products", json={"name":"X","price":10})   # 发 JSON body
resp.status_code       # 201

client.post("/products", json={"name":"X","price":-1}).status_code   # 422(校验失败)
```

> 🟡 **Java 对比**:= Spring `MockMvc` / `WebMvcTest`。TestClient 更简洁,且能测完整 HTTP 语义。

---

## §14.7 速查:FastAPI 端点签名各部分

```python
@app.post("/products", status_code=201, response_model=Product)   # 装饰器:方法+路径+选项
def create_product(                                                # 函数名任意
    p: ProductCreate,                                              # Pydantic 类型 → 请求体
    product_id: int,                                               # 简单类型 + 路径里有同名 → 路径参数
    category: str = "all",                                         # 简单类型 + 路径里没有 → 查询参数
):                                                                #   (Ch15 详讲)
    return ...
```

---

## §14.8 Java 老手常踩的坑 ⚠️

1. **Pydantic v1 vs v2**:v2 用 `model_dump()`,v1 用 `dict()`(已废弃)。本项目是 v2。
2. **校验失败是 422 不是 400**:FastAPI 的 Pydantic 校验失败默认 422 Unprocessable Entity。
3. **路径参数 vs 查询参数**:同名在路径里 `{x}` → 路径参数;不在 → 查询参数(Ch15 详讲)。
4. **`@app.post` 的 `status_code`**:默认 200,创建资源通常设 201。
5. **改全局变量要 `global`**:`create_product` 改 `_next_id` 要 `global _next_id`(Ch01 §1.10 坑6 相关)。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `ProductCreate` 模型 | Pydantic + Field 校验 | 🟡 |
| `list_products` | 路由 + 自动序列化 | 🟢 |
| `create_product` | 请求体模型 + model_dump | 🟡 |
| `get_product` | 路径参数 + HTTPException | 🟡 |

```bash
uv run pytest 03_web_framework/ch14/test_ch14_assignment.py -v
```

---

## ✅ 自测

- [ ] 能说清「FastAPI 的类型注解驱动了哪几件事」(解析/校验/序列化/文档)
- [ ] 会定义 Pydantic 模型 + Field 约束,知道校验失败返回 422
- [ ] 会用 TestClient 测 API
- [ ] 4 个作业全绿

## 🎓 费曼挑战

1. 「FastAPI 为什么说『类型注解驱动一切』?一个 `p: ProductCreate` 注解替你做了什么?」— 重读 §14.2
2. 「Pydantic 模型和 Java DTO 有什么不同?校验是怎么自动发生的?」— 重读 §14.2/§14.3

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步

Ch14 掌握后,进 **Ch15 · 路由参数**:路径参数 `/{id}`、查询参数 `?category=&min_price=`、分页 `?page=&size=`、`Query`/`Field` 校验——给商品 API 加上筛选和分页。
