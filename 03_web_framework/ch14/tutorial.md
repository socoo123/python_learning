# Ch14 · FastAPI 入门:第一个 API + Pydantic 模型

> **预计**:1 天 ｜ **前置**:Ch13(httpx 调 API)｜ **M3 第二章**
> **目标**:理解 FastAPI 的核心理念——「**类型注解驱动一切**」。你只声明类型,框架自动做完四件事:**解析参数、校验数据、序列化 JSON、生成 OpenAPI 文档**。对比 Spring Boot,样板代码少一大截。
> 本章主线:Ch13 你调用别人的商品 API;这章轮到**你来写**——你是「极客商城」后端,要上线第一版**商品管理 API**。数据先放内存字典(Ch19 再接 SQLAlchemy),种子数据与 Ch13 的 `products.json` 同源。客户端要:`GET` 列表、`POST` 创建(带校验)、`GET`/`PUT`/`DELETE` 单个,再给运营一个库存汇总报表。

> 📐 **本教程的契约**:§14.2–§14.8 每节精确对应一道作业。§14.1 是开胃、§14.9 自动文档 / §14.10 TestClient / §14.11 踩坑是配置类知识——讲透但不出独立 pytest 题。卡住时按对应表回查小节。

---

## 🗺️ 本章地图(元学习 · 原则一)

读完这章 + 完成作业,你将能够:
- 说清「类型注解驱动」的 4 件事(解析 / 校验 / 序列化 / 文档),并各举一个 Spring 对应物
- 用 Pydantic `BaseModel` + `Field` 定义请求模型:名称非空且 ≤50 字、价格 >0、库存 ≥0、SKU 正则
- 看懂 422 响应体的结构(`detail[].loc/msg/type`),知道 `"599"` 会被强转而 `"abc"` 会 422
- 用 `@app.get/post/put/delete` 写 CRUD:路径参数自动转 int,资源不存在抛 `HTTPException(404)`
- 用 `model_dump()` 把请求模型灌进响应模型,创建返回 201、删除返回 204
- 用 `TestClient` 不启服务测自己的 API,并知道 `/docs` 文档从哪来

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业题 | 对应小节 | 核心知识点 |
|--------|----------|-----------|
| `build_product_from_create` | §14.2 | Pydantic 模型 + `model_dump` 转响应 |
| `list_products` | §14.3 | `@app.get` + 自动 JSON 序列化 |
| `create_product` | §14.4 | 请求体模型 + `status_code=201` + Field 422 |
| `get_product` | §14.5 | 路径参数 + `HTTPException` |
| `update_product` | §14.6 | PUT 全量更新 + 404 |
| `delete_product` | §14.7 | DELETE + `204 No Content` |
| `inventory_report` | §14.8 | 综合:复用内存商品做运营汇总 |

> `ProductCreate` / `Product` 模型在 §14.2 定义;`ProductCreate` 的字段约束由 `TestProductCreate` + 创建接口的 422 用例一起验收(模型本身不是 `def`,不单独占对应表一行)。

---

## ⏱️ 学习路径:费曼五步(约 60-90 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 下面 5 个 Spring 场景,猜 FastAPI 怎么写 | 本页 ① |
| ② 先动手 | 打开 `ch14_assignment.py`,**先试着写**(别通读) | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清「类型驱动 4 件事、422 vs 404、model_dump、coercion」 | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性原则**:别通读!先猜 ① → 去 ② 写作业 → **哪题卡了,回对应 § 查** → 改 → 再跑。
> 本章作业形态:`填模型字段 + 填端点函数体`。测试用 `TestClient` 发真 HTTP 语义请求,不用你手动起 uvicorn。

---

## ① 预览猜(2 分钟 · 激活你的 Java 直觉)

先别看答案,凭 Spring 经验猜:
1. Spring:`@GetMapping` + `@RequestBody @Valid` + Jackson + springdoc。FastAPI 想一个机制搞定解析/校验/序列化/文档,靠的是什么?
2. Java DTO 常配 Lombok + Bean Validation(`@NotBlank @Positive`)。FastAPI 里对应的「请求/响应数据结构」基类叫什么?约束写在哪?
3. `price=-1` 校验失败,Spring 默认 400。FastAPI + Pydantic 默认回什么状态码?响应体长什么样?
4. 客户端把 `price` 传成字符串 `"599"`,你觉得 FastAPI 会拒绝还是悄悄转成数字?
5. 不启动 Tomcat/uvicorn,怎么对「自己的 app」发 HTTP 测接口?(提示:Ch13 的 httpx 亲戚)

> 猜完带着验证心态进正文。第 3 题的 **422**、第 4 题的**类型强转**是本章最高频考点 + 踩坑点。

---

## §14.1 为什么 FastAPI:类型注解驱动一切(开胃 · 不出题)🟢

FastAPI 的设计哲学:**你写类型注解,框架自动干活**。一个 Spring 商品 Controller 里你要写/配的东西,和 FastAPI 的对应关系:

| 你在 Spring 里写的 | FastAPI 里谁干 |
|--------------------|----------------|
| `@RequestBody` 反序列化 JSON | 参数类型是 `BaseModel` → 自动当请求体解析 |
| `@Valid` + `@Positive` 等约束 | `Field(gt=0)` → 失败自动 **422** |
| Jackson 把对象写成 JSON | 返回 `BaseModel` / `list` / `dict` → 自动序列化 |
| springdoc-openapi 依赖 + 注解 | 类型注解 → 内置 `/docs`、`/redoc`、`/openapi.json` |

**同一个「创建商品」端点,两家对比**:

```java
// Spring:注解是「给人和框架看的配置」,校验失败还要配 @ExceptionHandler 才能定制响应
@PostMapping("/products")
@ResponseStatus(HttpStatus.CREATED)
public Product create(@Valid @RequestBody ProductCreate body) { ... }
```

```python
# FastAPI:注解就是「运行时契约」,p: ProductCreate 一个注解 = 解析 + 校验 + 文档
@app.post("/products", status_code=201)
def create_product(p: ProductCreate):
    ...
```

❌ **错误心智**(把 FastAPI 当「薄路由」用,手动到处校验):

```python
@app.post("/products")
def create_product(payload: dict):          # 放弃类型 → 框架帮不了你
    if payload.get("price", 0) <= 0:        # 手写校验,文档也丢了
        return {"error": "bad price"}       # 还随手回了 200 + 错误 JSON
```

✅ **正确心智**(类型即契约,校验失败框架替你 422,函数体根本不执行):

```python
@app.post("/products", status_code=201)
def create_product(p: ProductCreate):
    return build_and_store(p)               # 你只写业务
```

> 🟡 **Java 对比**:FastAPI ≈ Spring Web + Bean Validation + Jackson + springdoc 的「类型驱动」子集。样板少,是因为**注解参与运行时**,不只是给人看的文档。

可选体验(非作业必需):

```bash
uv sync --extra web
uv run uvicorn 03_web_framework.ch14.ch14_assignment:app --reload
# 浏览器打开 http://localhost:8000/docs
```

作业全程用 `TestClient`,不必每次手动启动;但建议至少看一次 `/docs`,体会「改模型 → 文档自动变」。

---

## §14.2 Pydantic 模型 + Field 校验 + model_dump(对应:`build_product_from_create`)🔴

**Pydantic `BaseModel`** = Java DTO + 自动校验 + 自动(反)序列化,三位一体。

### Java 对照最小例

```java
public record ProductCreate(
    @NotBlank @Size(max = 50) String name,
    @NotBlank String category,
    @Positive double price,
    @Min(0) int stock,
    @Pattern(regexp = "^[A-Z]{2}-\\d{3}$") String sku
) {}
```

```python
from pydantic import BaseModel, Field

class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50, description="商品名称")
    category: str = Field(min_length=1, description="分类,如 电脑外设")
    price: float = Field(gt=0, description="价格必须 > 0")
    stock: int = Field(default=0, ge=0, description="库存不能为负")
    sku: str = Field(pattern=r"^[A-Z]{2}-\d{3}$", description="形如 KB-001")
```

### 约束速查表(本章用到的)

| 约束 | 含义 | 商城场景 |
|------|------|----------|
| `gt=0` | `>` | 价格必须大于 0(**0 也不行**) |
| `ge=0` | `≥` | 库存可为 0(售罄),不能为负 |
| `min_length=1` | 字符串最短 | 名称、分类不能是 `""` |
| `max_length=50` | 字符串最长 | 名称超长拒绝(对齐 DB `varchar(50)`) |
| `pattern=r"..."` | 正则 | SKU 必须「两大写字母 + 短横 + 三数字」 |
| `default=0` | 默认值 | 没传 `stock` 时当 0 |
| `description=` | 文档文案 | 自动出现在 `/docs` 的 schema 里 |

### 真实场景例(极客商城入库单)

运营 POST 上来的 JSON 必须先变成「合法入库单」,再由服务端分配 `id` 落成完整商品:

```python
class Product(BaseModel):          # 响应模型:含服务端分配的 id
    id: int
    name: str
    category: str
    price: float
    stock: int = 0
    sku: str

raw = ProductCreate(name="机械键盘", category="电脑外设", price=599.0, stock=120, sku="KB-001")
raw.model_dump()
# → {'name': '机械键盘', 'category': '电脑外设', 'price': 599.0, 'stock': 120, 'sku': 'KB-001'}

product = Product(id=1, **raw.model_dump())   # ** 解包:请求字段灌进响应模型
```

### 校验失败时客户端收到什么?(422 响应体)

`POST /products` 传 `price=-1`,FastAPI 回 **422 Unprocessable Entity**,body 是结构化数组:

```json
{
  "detail": [
    {
      "type": "greater_than",
      "loc": ["body", "price"],
      "msg": "Input should be greater than 0",
      "input": -1
    }
  ]
}
```

`loc` 告诉你错在哪个字段,`type` 是机器可读的规则名——前端可以据此做表单级报错。多个字段同时违法,`detail` 就有多条。

### 🤯 Java 老手震惊点:类型强转(coercion)

Pydantic 默认 **lax 模式**,会尽力把「长得像」的值转成声明类型:

```python
ProductCreate(name="X", category="图书", price="599", sku="KB-001").price
# → 599.0   字符串 "599" 被悄悄转成 float!JSON 里数字和字符串是两种类型,但 Pydantic 宽容

ProductCreate(name="X", category="图书", price="abc", sku="KB-001")
# → ValidationError → 接口 422   转不了才报错
```

> 🟡 对比 Java:Jackson 默认也做类似的字符串→数字转换,但 Bean Validation 的报错是 400。记住 FastAPI 的组合:**能转就转,转不了/违反约束就 422**。(想严格拒绝字符串,可用 `Field(strict=True)`,本章不要求。)

❌ **错误写法 1**(Pydantic v1 API,本项目是 v2):

```python
product = Product(id=1, **p.dict())     # v1 已废弃,会有弃用警告
```

✅ **正确写法**:

```python
product = Product(id=1, **p.model_dump())
```

❌ **错误写法 2**(约束写成默认值,校验完全失效):

```python
price: float = 0          # 这只是「默认 0」,负数照过!
```

✅ **正确写法**:

```python
price: float = Field(gt=0)   # 约束要写在 Field(...) 里
```

> ✅ 做 `build_product_from_create`:用 `Product(id=..., **data.model_dump())` 返回;`ProductCreate` 五个字段按速查表加 `Field`(name 多一个 `max_length=50`,category 只要 `min_length=1`)。

---

## §14.3 第一个 GET 端点(对应:`list_products`)🟢

### Java 对照最小例

```java
@GetMapping("/products")
public List<Product> list() {
    return new ArrayList<>(store.values());
}
```

```python
from fastapi import FastAPI

app = FastAPI(title="极客商城 · 商品 API")

@app.get("/products")
def list_products():
    return list(PRODUCTS.values())   # [Product, ...] → 自动变 JSON 数组
```

### 真实场景例

种子仓库里有 4 件商品(机械键盘 / 无线鼠标 / 设计模式 / 智能水杯)。`GET /products` 实际返回:

```json
[
  {"id": 1, "name": "机械键盘", "category": "电脑外设", "price": 599.0, "stock": 120, "sku": "KB-001"},
  {"id": 2, "name": "无线鼠标", "category": "电脑外设", "price": 159.0, "stock": 300, "sku": "MS-002"}
]
```

FastAPI 看到返回值是 Pydantic 模型列表,自动:① 逐个序列化成 JSON → ② 设 `Content-Type: application/json` → ③ 把响应 schema 写进 OpenAPI。

❌ **错误写法**(Java 老手手痒,自己序列化):

```python
import json

@app.get("/products")
def list_products():
    return json.dumps([p.model_dump() for p in PRODUCTS.values()])
    # 返回的是 str → 客户端收到一个「JSON 字符串」,不是数组!前端 JSON.parse 要调两次
```

✅ **正确写法**:直接返回 Python 对象,序列化是框架的事。

> 🟡 **Java 对比**:Spring 靠 Jackson + `@RestController`。FastAPI 无额外注解,`return` 的类型即契约。

> ✅ 做 `list_products`:`return list(PRODUCTS.values())`。

---

## §14.4 POST 创建 + 201 + Field 自动 422(对应:`create_product`)🟡

### Java 对照最小例

```java
@PostMapping("/products")
@ResponseStatus(HttpStatus.CREATED)
public Product create(@Valid @RequestBody ProductCreate body) { ... }
```

```python
@app.post("/products", status_code=201)
def create_product(p: ProductCreate):
    global _next_id
    product = build_product_from_create(_next_id, p)
    PRODUCTS[_next_id] = product
    _next_id += 1
    return product
```

**FastAPI 看见 `p: ProductCreate` 就自动**:① 读 JSON body → ② 按模型校验 → ③ 失败回 422。你只管业务。

### 真实场景例(合法入库 vs 脏数据)

```python
# 合法:运营录入降噪耳机
POST /products  {"name":"降噪耳机","category":"影音设备","price":1299,"stock":80,"sku":"HP-006"}
→ 201  {"id":5,"name":"降噪耳机","category":"影音设备","price":1299.0,"stock":80,"sku":"HP-006"}

# 脏数据:价格为 0 / 缺 name / SKU 写成小写 hp-006 / 名称 51 个字
→ 全部 422,你的函数体根本不会执行,PRODUCTS 不会被污染
```

❌ **错误写法**(改全局 id 忘了 `global`,抛 `UnboundLocalError`):

```python
def create_product(p: ProductCreate):
    product = build_product_from_create(_next_id, p)  # 只读还行
    _next_id += 1   # 有赋值 → Python 把 _next_id 当局部变量 → 读时炸(Ch01 的坑)
```

✅ **正确写法**:函数内要给模块级变量赋值,先声明 `global _next_id`。

> 🟡 **为什么 201 不是 200**:REST 语义里「新建资源成功」用 `201 Created`。FastAPI 默认 200,所以在装饰器里显式 `status_code=201`。

> ✅ 做 `create_product`:声明 `global _next_id` → 调 `build_product_from_create` → 写入 `PRODUCTS` → id 自增 → `return product`。装饰器已写好 `status_code=201`。

---

## §14.5 路径参数 + HTTPException(对应:`get_product`)🟡

### Java 对照最小例

```java
@GetMapping("/products/{id}")
public Product get(@PathVariable int id) {
    Product p = store.get(id);
    if (p == null) throw new ResponseStatusException(NOT_FOUND, "商品不存在");
    return p;
}
```

```python
from fastapi import HTTPException

@app.get("/products/{product_id}")
def get_product(product_id: int):
    if product_id not in PRODUCTS:
        raise HTTPException(status_code=404, detail="商品不存在")
    return PRODUCTS[product_id]
```

### 真实场景例

- `GET /products/1` → 200,机械键盘完整 JSON
- `GET /products/99999` → 404,`{"detail":"商品不存在"}`
- `GET /products/abc` → **422**(路径参数 `int` 转换失败,函数体不跑)——注意 422 不只属于请求体,路径/查询参数转换失败也是 422

两个关键点:
1. 路径里的 `{product_id}` 与函数参数**同名** → 自动提取;`int` 注解负责转换 + 类型校验。
2. `HTTPException` = Spring `ResponseStatusException`。**业务上「没有这个资源」用 404**;**请求形状不合法**留给框架 422——别混。

❌ **错误写法 1**(路径名和参数名不一致):

```python
@app.get("/products/{product_id}")
def get_product(id: int):   # 名字对不上!FastAPI 把 id 当成「必传查询参数」
    ...
# GET /products/1 → 422:detail[0].loc == ["query", "id"],一脸懵
```

✅ **正确写法**:`{product_id}` 和 `product_id: int` 严格同名。

❌ **错误写法 2**(找不到也回 200 + `null`,前端拿到 null 直接崩):

```python
return PRODUCTS.get(product_id)   # None → JSON null,状态码仍 200
```

✅ **正确写法**:不存在就 `raise HTTPException(status_code=404, detail="商品不存在")`。

> ✅ 做 `get_product`:先判 `product_id not in PRODUCTS`,再返回。

---

## §14.6 PUT 全量更新(对应:`update_product`)🟡

### Java 对照最小例

```java
@PutMapping("/products/{id}")
public Product update(@PathVariable int id, @Valid @RequestBody ProductCreate body) { ... }
```

```python
@app.put("/products/{product_id}")
def update_product(product_id: int, p: ProductCreate):
    if product_id not in PRODUCTS:
        raise HTTPException(status_code=404, detail="商品不存在")
    product = build_product_from_create(product_id, p)  # 保留原 id
    PRODUCTS[product_id] = product
    return product
```

### 真实场景例

无线鼠标涨价、补货:

```text
PUT /products/2
{"name":"无线鼠标","category":"电脑外设","price":169.0,"stock":350,"sku":"MS-002"}
→ 200  {"id":2,"name":"无线鼠标","category":"电脑外设","price":169.0,"stock":350,"sku":"MS-002"}
```

PUT = **全量替换**(请求体仍是 `ProductCreate`,不含 id)。id 只来自路径,避免客户端篡改主键。校验同样生效:body 里 `price=-1` → 422;路径里 id 不存在 → 404。先 422 还是先 404?FastAPI 先校验参数形状(422),再执行你的函数体(404)——和 Spring 一样,**校验永远先于业务**。

❌ **错误写法**(逐字段手拷,字段一多必漏):

```python
old = PRODUCTS[product_id]
old.name, old.category, old.price, old.stock, old.sku = p.name, p.category, p.price, p.stock, p.sku
# 原地修改 + 五连赋值,新增字段时这里必忘改
```

✅ **正确写法**:复用 `build_product_from_create(product_id, p)` 造新对象写回,一处定义处处生效。

> 🟡 **Java 对比**:和 Spring `@PutMapping` + `@PathVariable` + `@RequestBody` 同构。部分更新 PATCH / 可选字段放到 Ch15+;本章先掌握全量 PUT。

> ✅ 做 `update_product`:404 守卫 → `build_product_from_create(product_id, p)` → 写回字典 → 返回。

---

## §14.7 DELETE + 204(对应:`delete_product`)🟢

### Java 对照最小例

```java
@DeleteMapping("/products/{id}")
@ResponseStatus(HttpStatus.NO_CONTENT)
public void delete(@PathVariable int id) { ... }
```

```python
@app.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int) -> None:
    if product_id not in PRODUCTS:
        raise HTTPException(status_code=404, detail="商品不存在")
    del PRODUCTS[product_id]
```

### 真实场景例

下架 id=4 的智能水杯:`DELETE /products/4` → **204**,响应体为空;再 `GET /products/4` → 404。

❌ **错误写法**(删成功却回 200 + 整对象,或静默吞掉不存在):

```python
PRODUCTS.pop(product_id, None)   # 不存在也 204,调用方以为删过了(幂等≠静默,本章要求显式 404)
return PRODUCTS.get(product_id)  # 还试图返回 body,和 204 语义冲突
```

✅ **正确写法**:不存在 → 404;存在 → `del` → 隐式 `return None`(204 无 body)。

> 🟡 **204 vs 200**:删除成功且无内容要返回,用 `204 No Content` 是 REST 惯例;调用方看到 204 就知道「成了,别解析 body」。

> ✅ 做 `delete_product`:404 守卫 + `del PRODUCTS[product_id]`。`status_code=204` 已在装饰器里。

---

## §14.8 综合:库存运营报表(对应:`inventory_report`)🔴

复用前面的内存商品,给运营一个只读汇总——**不引新框架 API**,练的是组合已有数据 + M1/M2 的推导式基本功。

```python
@app.get("/inventory/report")
def inventory_report():
    items = list(PRODUCTS.values())
    return {
        "total_skus": len(items),
        "total_units": sum(p.stock for p in items),
        "total_value": round(sum(p.price * p.stock for p in items), 2),
        "out_of_stock": sorted(p.name for p in items if p.stock == 0),
    }
```

### 真实场景例(种子数据手算)

种子 4 件:机械键盘 599×120、无线鼠标 159×300、设计模式 75.5×200、智能水杯 199×0。

```text
GET /inventory/report
→ {
    "total_skus": 4,
    "total_units": 620,
    "total_value": 134680.0,
    "out_of_stock": ["智能水杯"]
  }
```

- `total_units` = 120+300+200+0 = **620**
- `total_value` = 71880 + 47700 + 15100 + 0 = **134680.0**(货值 = Σ 价格×库存,运营看板核心指标)
- `out_of_stock` 只列售罄品名,**排序**保证每次响应一致

创建/删除商品后再打这个接口,数字应跟着变——所以它是小综合,也能帮你发现「状态没写进 `PRODUCTS`」的 bug。

❌ **错误写法**(直接返回未排序的生成器结果 / 用 dict 顺序碰运气):

```python
"out_of_stock": [p.name for p in items if p.stock == 0]   # 依赖插入顺序,数据一变断言就飘
```

✅ **正确写法**:`sorted(...)`,输出稳定,前端和测试都好断言。

> ✅ 做 `inventory_report`:四字段都算对;`total_value` 用 `round(..., 2)` 防浮点尾巴;`out_of_stock` 用 `sorted`。

---

## §14.9 自动文档与 response_model(延伸 · 不出独立题)🟢

启动 app 后自带三件套:`/docs`(Swagger UI)、`/redoc`(ReDoc)、`/openapi.json`(机器可读 schema)。它们全部来自你的类型注解——改 `ProductCreate` 的 `Field(description=...)`,文档文案一起变。

返回值已经能进 `/docs`。若想**响应 schema 更严**,加 `response_model`:

```python
class ProductInternal(BaseModel):   # 内部模型:含成本价,绝不能给前端
    id: int
    name: str
    price: float
    cost: float

@app.get("/products", response_model=list[Product])   # Product 没有 cost 字段
def list_products():
    return list(PRODUCTS_INTERNAL.values())   # 返回内部模型,cost 被自动剥掉
```

`response_model` 两大价值:① **过滤多余字段**(防数据泄露,≈ Spring 的 `@JsonIgnore` 但不用改模型);② 文档里写明返回类型。

> 🟡 **Java 对比**:springdoc 要加依赖 + 注解;FastAPI 内置零配置。本章作业装饰器未强制 `response_model`,理解概念即可,后面章节会逐步加上。

---

## §14.10 TestClient:测自己的 API(测试基础设施 · 不出独立题)🟡

```python
from fastapi.testclient import TestClient
from ch14_assignment import app

client = TestClient(app)

client.get("/products").status_code                    # 200
client.post("/products", json={...}).status_code       # 201 或 422
client.get("/products/99999").status_code              # 404
client.delete("/products/1").status_code               # 204
```

> 🟡 **Java 对比** ≈ Spring `MockMvc` / `@WebMvcTest`。底层是 httpx(Ch13),所以 `resp.json()` / `status_code` 手感一致。

**为什么测试文件里有个 `autouse` fixture?** 端点会改全局 `PRODUCTS` / `_next_id`,用例执行顺序不同结果就不同(「先跑 create 再跑 list」互相污染)。所以每个用例前重置种子数据:

```python
@pytest.fixture(autouse=True)
def reset_store():
    m.PRODUCTS.clear()
    m.PRODUCTS.update({k: v.model_copy() for k, v in SEED.items()})
    m._next_id = 5
    yield
```

`model_copy()`(Pydantic v2,≈ Java 的 copy 构造器)避免用例间共享同一个模型实例。这个 fixture 已写好,你读测试时看懂即可。

---

## §14.11 Java 老手常踩的坑 ⚠️

1. **校验失败是 422 不是 400**——别在断言里写 `== 400`;422 的 body 是 `{"detail": [{loc, msg, type, ...}]}`。
2. **资源不存在是 404**——和 422(形状/约束错误)分工不同;路径参数 `/products/abc` 转换失败也是 422。
3. **lax 模式会强转**:`price="599"` → `599.0` 不报错;`price="abc"` → 422。别假设「类型不对一定炸」。
4. **Pydantic v2 用 `model_dump()`**,不要 `dict()`;复制模型用 `model_copy()`。
5. **约束写进 `Field(...)`**——`price: float = 0` 只是默认值,不是校验。
6. **创建资源用 `status_code=201`**;删除常用 **204** 且无 body。
7. **函数内修改 `_next_id` 必须 `global`**(Ch01 坑:有赋值就被当局部变量)。
8. **路径参数名与函数参数名必须一致**,否则被当成查询参数,报莫名其妙的 422。
9. **不要手动 `json.dumps` 再 return**——客户端会收到双重编码的字符串。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `ProductCreate` 字段 | Field:min_length / max_length / gt / ge / pattern | 🟡 |
| `build_product_from_create` | model_dump + 解包 | 🟢 |
| `list_products` | GET + 自动序列化 | 🟢 |
| `create_product` | POST 201 + global | 🟡 |
| `get_product` | 路径参数 + 404 | 🟡 |
| `update_product` | PUT 全量更新 | 🟡 |
| `delete_product` | DELETE 204 | 🟢 |
| `inventory_report` | 综合汇总(货值 + 售罄榜) | 🔴 |

```bash
uv sync --extra web
uv run pytest 03_web_framework/ch14/test_ch14_assignment.py -v
```

---

## ✅ 自测

- [ ] 能说清「类型注解驱动」的 4 件事,各举一个 Spring 对应物
- [ ] 会写 `Field(gt / ge / min_length / max_length / pattern)`,知道失败是 422 且看得懂 422 body
- [ ] 知道 `"599"` 会被 lax 模式强转、`"abc"` 才 422
- [ ] 会用 `model_dump()` 把请求模型变成响应模型
- [ ] CRUD + 库存报表全绿;404 / 422 / 201 / 204 不混用

## 🎓 费曼挑战

1. 「一个 `p: ProductCreate` 注解替你做了什么?和 Spring `@Valid @RequestBody` 怎么对应?」— 重读 §14.2 / §14.4
2. 「为什么 `price=0` 是 422,而 `product_id=99999` 是 404?`price="599"` 为什么不报错?」— 重读 §14.2 / §14.4 / §14.5
3. 「`response_model` 除了写文档还有什么实际价值?」— 重读 §14.9

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步

Ch14 掌握后,进 **Ch15 · 路由参数**:路径参数加深、`Query` 筛选 / 分页、`Field` 与 `Query` 配合——给商品 API 加上 `?category=&min_price=&page=`(正好用上本章模型里的 `category` 字段)。
