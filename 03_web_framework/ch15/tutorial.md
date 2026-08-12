# Ch15 · 路由参数:路径参数 / 查询参数 / 分页排序

> **预计**:0.5 天 ｜ **前置**:Ch14 ｜ **M3 第三章**
> **目标**:搞清 FastAPI 的「参数三来源」——**路径参数 / 查询参数 / 请求体**——框架怎么靠类型注解自动区分,不用写 `@PathVariable` / `@RequestParam`。再给参数加上校验(`Path` / `Query` / `Literal`),并学会商城后台的三件套:**筛选、分页、排序**。
> 本章主线:你是「极客商城」后端。Ch14 的 CRUD 上线后,运营后台提了 2.0 需求:商品要按类目/价格带筛选、关键词搜索、价格/库存榜单;订单列表要分页;下单接口要收「一个订单含多个商品」的嵌套 JSON;路由文件大了,要用 `APIRouter` 分组管理。

> 📐 **本教程的契约**:§15.1–§15.7 每节精确对应一道作业。§15.8(Form/File)是延伸——讲透但不出题。卡住时按对应表回查小节。

---

## 🗺️ 本章地图(元学习 · 原则一)

读完这章 + 完成作业,你将能够:
- 说清 FastAPI 不靠注解,凭「名字在不在路径里 + 参数类型」判断参数来源
- 用 `Path(ge=1)` 校验路径参数,分清 **422(形状错)/ 404(资源无)/ 400(业务规则)** 的分工
- 用 `X | None = None` 写可选查询参数,并用 `is not None` 做「不传不过滤」
- 用 `Query(...)` 给查询参数加默认值与约束(必填、`min_length`、`ge/le`)
- 说清为什么 `/products/search` 必须比 `/products/{product_id}` **先注册**(路由顺序坑)
- 写出标准分页:`start = (page-1)*size` + 切片 + 分页元信息(`total/pages`)
- 用 `Literal["price","stock"]` 把排序参数变成「白名单枚举」,非法值自动 422
- 用 `list[ItemModel]` 收嵌套请求体,知道框架校验和业务校验各管什么
- 用 `APIRouter` + `include_router(prefix=..., tags=...)` 给路由分组

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业题 | 对应小节 | 核心知识点 |
|--------|----------|-----------|
| `get_product` | §15.1 | 路径参数 + `Path` 校验 + 404 |
| `list_products` | §15.2 | 可选查询参数(`X \| None = None`) |
| `search_products` | §15.3 | `Query` 校验 + 路由注册顺序 |
| `list_orders` | §15.4 | 分页切片 + 分页元信息 |
| `list_product_ranking` | §15.5 | `Literal` 枚举参数 + 排序 |
| `create_order` | §15.6 | 嵌套请求体 `list[Model]` + 业务校验 |
| `register_system_router` | §15.7 | `APIRouter` 分组 + `include_router` |

---

## ⏱️ 学习路径:费曼五步(约 45-60 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 下面 5 个 Spring 场景,猜 FastAPI 怎么写 | 本页 ① |
| ② 先动手 | 打开 `ch15_assignment.py`,**先试着写**(别通读) | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清「参数三来源、422/404/400、路由顺序」 | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性原则**:别通读!先猜 ① → 去 ② 写作业 → **哪题卡了,回对应 § 查** → 改 → 再跑。
> 本章作业形态:`填端点函数体`。测试用 `TestClient` 发真 HTTP 语义请求,不用你手动起 uvicorn。

---

## ① 预览猜(2 分钟 · 激活你的 Java 直觉)

先别看答案,凭 Spring 经验猜:
1. Spring 靠 `@PathVariable` / `@RequestParam` / `@RequestBody` 区分参数来源。FastAPI 一个注解不写,靠什么区分?
2. `@RequestParam(required = false) String category` 在 FastAPI 里怎么表达?过滤时为什么用 `if category is not None` 而不是 `if category:`?
3. `page` 必须 ≥ 1、`size` 不能超过 100,Spring 里 `@Min(1) @Max(100)`,FastAPI 一行怎么写?
4. `/products/search` 和 `/products/{product_id}` 两个路由都存在时,谁先注册?颠倒会发生什么?
5. 查询参数 `sort_by` 只允许 `price` / `stock` 两个值,怎么让框架自动拒绝其他值、还写进文档?

> 猜完带着验证心态进正文。第 4 题的**路由顺序**和第 5 题的 **Literal** 是 Java 老手最容易栽的两处。

---

## §15.1 路径参数 + Path 校验(对应:`get_product`)🟡

### Java 对照最小例

```java
@GetMapping("/products/{id}")
public Product get(@PathVariable @Min(1) int id) {
    Product p = store.get(id);
    if (p == null) throw new ResponseStatusException(NOT_FOUND, "商品不存在");
    return p;
}
```

```python
from fastapi import Path, HTTPException

@products_router.get("/products/{product_id}")
def get_product(product_id: int = Path(ge=1)):
    for p in PRODUCTS:
        if p.id == product_id:
            return p
    raise HTTPException(status_code=404, detail="商品不存在")
```

**两个规则,自动判断参数来源**(不用任何注解):

| 参数特征 | 来源 | Spring 对应 |
|----------|------|-------------|
| 名字出现在路径 `{xxx}` 里 | **路径参数** | `@PathVariable` |
| 简单类型(int/str/float/bool)且不在路径里 | **查询参数** | `@RequestParam` |
| Pydantic 模型类型 | **请求体** | `@RequestBody` |

### 真实场景例(极客商城商品详情)

- `GET /products/1` → 200,机械键盘
- `GET /products/999` → **404** `{"detail":"商品不存在"}`(类型对,但资源不存在 → 你的代码抛的)
- `GET /products/abc` → **422**(路径参数 `int` 转换失败,函数体根本不执行)
- `GET /products/0` → **422**(`Path(ge=1)` 约束失败——id 从 1 开始,0 是非法输入)

`Path(默认值或省略, 约束)` 给路径参数加校验,约束参数和 Ch14 的 `Field` 是同一套:`ge` / `le` / `gt` / `lt` / `min_length` / `pattern`。

❌ **错误写法**(找不到也回 200 + `null`,前端拿到 null 直接崩):

```python
return next((p for p in PRODUCTS if p.id == product_id), None)  # None → 200 + null
```

✅ **正确写法**:不存在就 `raise HTTPException(status_code=404, ...)`。

> 🤯 **Java 老手震惊点**:Spring 要写 `@PathVariable` + `@Min` 两个注解;FastAPI 靠「参数名在路径里 + `int` 注解」自动提取转换,`Path(ge=1)` 一行搞定约束。**422 是框架替你拒的,404 是你自己抛的**——分工别混。

> ✅ 做 `get_product`:`Path(ge=1)` 已在签名里写好,你实现「遍历查找 + 找不到 404」。

---

## §15.2 可选查询参数:不传不过滤(对应:`list_products`)🟡

### Java 对照最小例

```java
@GetMapping("/products")
public List<Product> list(@RequestParam(required = false) String category,
                          @RequestParam(required = false) BigDecimal minPrice) { ... }
```

```python
@products_router.get("/products")
def list_products(
    category: str | None = None,      # 可选:不传是 None
    min_price: float | None = None,
    max_price: float | None = None,
):
    result = PRODUCTS
    if category is not None:          # 只过滤「传了的」
        result = [p for p in result if p.category == category]
    if min_price is not None:
        result = [p for p in result if p.price >= min_price]
    if max_price is not None:
        result = [p for p in result if p.price <= max_price]
    return result
```

**关键模式**:`str | None = None` = 「可选查询参数,缺省 None」。函数体用 `if xxx is not None` 决定要不要过滤——**不传 = 不过滤**,三个条件可任意组合。

### 真实场景例(运营后台筛选器)

运营要查「电脑外设里 500~1500 元的商品」盘点库存:

```text
GET /products?category=电脑外设&min_price=500&max_price=1500
→ [机械键盘 599](显示器 2199 超上限,鼠标/扩展坞低于下限)
GET /products?max_price=200   → 无线鼠标159 / Python编程89 / 设计模式75.5 / 智能水杯199
```

❌ **错误写法**(用 truthiness 判断「传没传」):

```python
if category:        # category="" 时被当「没传」跳过过滤
if min_price:       # min_price=0 也被跳过!0 是合法输入(查免费品)
```

✅ **正确写法**:`if min_price is not None`——`None` 才是「没传」的唯一信号,`0` / `""` / `False` 都是「传了」。(Ch01 的 truthiness 坑在 Web 参数里复活了)

> 🟡 **Java 对比**:`X | None = None` ≈ `@RequestParam(required=false)` + 默认 null。区别:Python 里**写了 `| None` 就必须给 `= None` 默认值**,否则仍是必填(类型可空 ≠ 参数可选)。

> ✅ 做 `list_products`:三个筛选条件,`is not None` 守卫 + 列表推导逐级过滤。

---

## §15.3 Query 校验 + 路由注册顺序(对应:`search_products`)🔴

### Query:给查询参数加约束

`Query(...)` 之于查询参数,就像 `Field(...)` 之于模型字段、`Path(...)` 之于路径参数——同一套约束,三个战场:

```python
from fastapi import Query

@products_router.get("/products/search")
def search_products(
    q: str = Query(min_length=2),              # 无默认值 → 必填;至少 2 个字符
    limit: int = Query(10, ge=1, le=50),       # 默认 10,范围 1~50
):
    matched = [p for p in PRODUCTS if q in p.name or q in p.category]
    return matched[:limit]
```

| 写法 | 含义 | 违反时 |
|------|------|--------|
| `q: str = Query(min_length=2)` | **必填**(没给默认值),至少 2 字符 | 缺省或太短 → 422 |
| `limit: int = Query(10, ge=1, le=50)` | 可选,默认 10,1~50 | `limit=0` / `limit=51` → 422 |

### 真实场景例(商城搜索框)

搜索接口必须防「空关键词全表扫描」:运营后台的搜索框按**名称或类目**匹配,要求至少输入 2 个字符,一次最多返回 50 条:

```python
matched = [p for p in PRODUCTS if q in p.name or q in p.category]
return matched[:limit]
```

```text
GET /products/search?q=键盘          → [机械键盘](名称匹配)
GET /products/search?q=影音          → [降噪耳机, 蓝牙音箱](类目「影音设备」匹配)
GET /products/search?q=电脑外设&limit=2 → 4 条匹配截断到 2 条
GET /products/search?q=机            → 422(只有 1 个字符,min_length=2)
GET /products/search                 → 422(缺必填 q)
```

> ⚠️ 中文字符按 1 个字符计长度:`"机"` 的 `len` 是 1,过不了 `min_length=2`。

### 🔴 路由顺序坑(Java 里没有对应物)

FastAPI **按注册顺序匹配路由,先匹配先赢**。`/products/search` 和 `/products/{product_id}` 并存时:

❌ **错误顺序**(具体路径被参数路径「抢走」):

```python
@products_router.get("/products/{product_id}")   # 先注册
def get_product(product_id: int): ...

@products_router.get("/products/search")          # 后注册 → 永远轮不到!
def search_products(...): ...
# GET /products/search → 匹配到 {product_id}="search" → int 转换失败 → 422
```

✅ **正确顺序**:**具体路径在前,参数路径在后**:

```python
@products_router.get("/products/search")          # 先注册具体路径
@products_router.get("/products/{product_id}")    # 参数路径兜底
```

> 这就是为什么作业文件里 `get_product` 定义在 `search_products` / `list_product_ranking` **之后**——不是教学顺序乱,是路由注册顺序的硬约束。Spring 的路径匹配按「精确度优先」,FastAPI 是纯粹的「先来后到」。

> ✅ 做 `search_products`:`q in p.name or q in p.category` 过滤 + `[:limit]` 截断。签名已按正确顺序写好。

---

## §15.4 分页:切片 + 元信息(对应:`list_orders`)🟡

### Java 对照最小例

```java
@GetMapping("/orders")
public Page<Order> list(@RequestParam @Min(1) int page,
                        @RequestParam @Min(1) @Max(100) int size) {
    // Page<T> 自带 total / totalPages
}
```

```python
@orders_router.get("/orders")
def list_orders(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
):
    start = (page - 1) * size            # 第 page 页 → 跳过 (page-1)*size 条
    items = ORDERS[start:start + size]
    total = len(ORDERS)
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,   # 向上取整,不用 import math
    }
```

**分页公式**:`start = (page - 1) * size`,切片 `[start : start + size]`。page 从 **1** 开始(前端约定),切片是 0-based:

- page=1, size=10 → `[0:10]`(第 1~10 条)
- page=2, size=10 → `[10:20]`(第 11~20 条)
- 12 条数据,size=10 → 第 2 页只有 2 条;page=3 → `[]`

### 真实场景例(订单列表 12 条)

```text
GET /orders                 → items 10 条, total=12, pages=2
GET /orders?page=2          → items 2 条(id 11、12)
GET /orders?page=99         → items=[], total=12  ← 越界不是错误!
GET /orders?page=0          → 422(ge=1)
GET /orders?size=200        → 422(le=100)
```

❌ **错误写法**(越界页当 404 处理):

```python
if start >= len(ORDERS):
    raise HTTPException(404, "页码超出范围")   # 前端翻页到末尾会收到报错,体验差
```

✅ **正确写法**:越界返回 `items: []` + 正确元信息——**空页是正常业务结果,不是错误**。

**为什么要返回元信息而不只返回数组?** 前端分页组件需要 `total` / `pages` 渲染「共 12 条,2 页」。只返回当前页数组,前端只能盲猜。这就是 Spring `Page<T>` 里 `totalElements` / `totalPages` 的对应物。

> 🟡 Ch19 接数据库后,切片会换成 SQL 的 `OFFSET/LIMIT`,`total` 换成 `COUNT(*)`,但公式和响应结构一模一样。

> ✅ 做 `list_orders`:公式切片 + 五元组元信息,`pages` 用 `(total + size - 1) // size` 向上取整。

---

## §15.5 排序:Literal 白名单参数(对应:`list_product_ranking`)🔴

### Java 对照最小例

```java
@GetMapping("/products/ranking")
public List<Product> ranking(@RequestParam SortField sortBy,   // enum 白名单
                             @RequestParam(defaultValue = "asc") SortOrder order) { ... }
```

```python
from typing import Literal

@products_router.get("/products/ranking")
def list_product_ranking(
    sort_by: Literal["price", "stock"] = "price",
    order: Literal["asc", "desc"] = "asc",
    limit: int = Query(5, ge=1, le=20),
):
    ranked = sorted(PRODUCTS, key=lambda p: getattr(p, sort_by), reverse=order == "desc")
    return ranked[:limit]
```

**`Literal["price", "stock"]`** = 参数只能取这两个字面量,其他值框架直接 422,还会以「下拉枚举」的形式写进 `/docs`。等价于 Java 的 `enum` 参数,但不用定义枚举类。

### 真实场景例(商城首页「价格榜」组件)

首页要渲染「最低价 Top5」「库存积压 Top5」两个小组件:

```text
GET /products/ranking                          → 价格升序前 5:设计模式75.5 → Python编程89 → 无线鼠标159 → 智能水杯199 → 扩展坞269
GET /products/ranking?sort_by=price&order=desc&limit=3
    → [27寸4K显示器 2199, 人体工学椅 1599, 降噪耳机 1299]
GET /products/ranking?sort_by=stock&order=desc&limit=1
    → [Python编程 stock=500]
GET /products/ranking?sort_by=name             → 422(不在白名单)
```

❌ **错误写法**(不过滤直接拿用户输入当字段名):

```python
sort_by: str = "price"
sorted(PRODUCTS, key=lambda p: getattr(p, sort_by))   # sort_by=__class__ 之类 → 信息泄露/报错
```

✅ **正确写法**:`Literal` 白名单兜底,非法值根本进不了函数体——这和「SQL 排序字段绝不能拼用户输入」是同一个安全直觉。

> 🔴 **Python 特有**:`Literal` 来自 `typing`,运行时被 FastAPI/Pydantic 消费成真正的校验规则。Java 里你要 `enum` + 转换器;这里一行类型注解搞定,文档还自动出枚举下拉框。

> ✅ 做 `list_product_ranking`:`sorted(..., key=lambda p: getattr(p, sort_by), reverse=order == "desc")` + `[:limit]`。

---

## §15.6 嵌套请求体:list[Model](对应:`create_order`)🔴

### Java 对照最小例

```java
public record OrderCreate(@NotBlank String customer,
                          @NotEmpty List<@Valid OrderItemCreate> items) {}
```

```python
class OrderItemCreate(BaseModel):
    product_id: int = Field(ge=1)
    quantity: int = Field(gt=0, le=99)

class OrderCreate(BaseModel):
    customer: str = Field(min_length=1)
    items: list[OrderItemCreate] = Field(min_length=1)   # 嵌套:至少 1 项
```

`items: list[OrderItemCreate]` —— 请求体是「订单里套商品行」的嵌套 JSON。FastAPI 会**递归校验**:每一行的 `product_id` / `quantity` 不合法,整个请求 422。

### 真实场景例(商城下单)

```text
POST /orders
{"customer":"张三","items":[{"product_id":1,"quantity":2},{"product_id":4,"quantity":1}]}
→ 201
{"id":13,"customer":"张三","total":1287.0,"status":"pending",
 "items":[{"product_id":1,"name":"机械键盘","quantity":2,"unit_price":599.0,"subtotal":1198.0},
          {"product_id":4,"name":"Python编程:从入门到实践","quantity":1,"unit_price":89.0,"subtotal":89.0}]}
```

**两层校验,分工明确**:

| 层 | 谁干 | 例子 | 状态码 |
|----|------|------|--------|
| **形状校验** | 框架(Pydantic) | `quantity=0`、`items=[]`、缺 `customer` | 422 |
| **业务校验** | 你的代码 | 商品不存在、库存不足 | 404 / 400 |

```python
@orders_router.post("/orders", status_code=201)
def create_order(order: OrderCreate):
    items = []
    for item in order.items:
        product = next((p for p in PRODUCTS if p.id == item.product_id), None)
        if product is None:
            raise HTTPException(status_code=404, detail=f"商品不存在: {item.product_id}")
        if product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"库存不足: {product.name}")
        items.append(OrderItem(product_id=product.id, name=product.name,
                               quantity=item.quantity, unit_price=product.price,
                               subtotal=product.price * item.quantity))
    total = sum(i.subtotal for i in items)
    ...   # 分配 id、append 到 ORDERS、返回
```

❌ **错误写法**(把业务校验也丢给框架,或形状校验自己写):

```python
if not order.customer:            # 框架已用 min_length=1 拦了,轮不到你
    raise HTTPException(400, ...)
if item.quantity <= 0:            # 同上,Field(gt=0) 已拦
    raise HTTPException(422, ...)
```

✅ **正确写法**:形状约束写进 `Field`,函数体只管「商品存在吗、库存够吗」这类**要查数据才知道**的业务规则。

> 🤯 **Java 老手震惊点**:Spring 里嵌套校验要 `@Valid` 一路注解下去;FastAPI 看到 `list[OrderItemCreate]` 自动递归。你要做的只是声明类型。

> ✅ 做 `create_order`:遍历 `order.items` → 查商品(404)/ 验库存(400)→ 组装 `OrderItem`(含 `subtotal`)→ `sum` 出 `total` → 用 `_next_order_id`(记得 `global`)分配 id → append 到 `ORDERS` → 返回。装饰器已写 `status_code=201`。

---

## §15.7 APIRouter:路由分组(对应:`register_system_router`)🟡

### Java 对照最小例

```java
@RestController
@RequestMapping("/products")   // 类级前缀:该控制器所有路由共享
public class ProductController { ... }
```

```python
from fastapi import APIRouter

products_router = APIRouter(tags=["商品"])     # 一个资源一个 router
orders_router = APIRouter(tags=["订单"])

@products_router.get("/products")              # 端点挂在 router 上,而不是 app 上
def list_products(...): ...

app = FastAPI(title="极客商城 · 商品与订单 API")
app.include_router(products_router)            # 组装:把 router 挂进 app
app.include_router(orders_router)
```

`APIRouter` = 迷你版 FastAPI,可以先挂端点、最后统一 `include_router` 进 app。好处和 Spring 的「按控制器拆文件」一样:**路由按资源分组,可跨文件组织,统一加前缀和标签**。

### 真实场景例(商城 2.0 的路由文件)

本章作业文件就是这么组织的:`products_router`(商品 4 个端点)、`orders_router`(订单 2 个端点)已注册;另有一个 `system_router`(健康检查 / 服务信息)定义好了**但还没挂进 app**——运维等着用:

```python
system_router = APIRouter()

@system_router.get("/health")
def health():
    return {"status": "ok"}

# 你的任务:一行代码挂上,并统一加 /system 前缀
app.include_router(system_router, prefix="/system", tags=["系统"])
# GET /system/health → {"status": "ok"}
```

`include_router` 常用参数:

| 参数 | 作用 | 例子 |
|------|------|------|
| `prefix` | 给该 router 所有路径加统一前缀 | `prefix="/system"` → `/system/health` |
| `tags` | `/docs` 里的分组名 | `tags=["系统"]` |
| `dependencies` | 整组统一依赖(Ch16 讲) | 如统一鉴权 |

> 🟡 **Java 对比**:`prefix` ≈ 类级 `@RequestMapping("/system")`;`tags` ≈ Swagger 的 `@Tag`。区别:FastAPI 的前缀在**注册时**加,同一个 router 可以用不同前缀挂多次(如 `/v1` / `/v2` 并存)。

> ✅ 做 `register_system_router`:`app.include_router(system_router, prefix="/system", tags=["系统"])` 一行。测试会验证 `/system/health` 从 404 变 200。

---

## §15.8 延伸:Form 表单与 File 上传(不出题)🟢

大纲知识点,了解即可。需要 `python-multipart`(本项目 `uv sync --group web` 才装),所以本章不出题:

```python
from fastapi import Form, File, UploadFile

@app.post("/login")
def login(username: str = Form(), password: str = Form()): ...   # 表单字段,非 JSON

@app.post("/products/import")
async def import_products(file: UploadFile = File()):            # 文件上传
    content = await file.read()
```

| 参数来源 | 声明 | 前端 Content-Type |
|----------|------|-------------------|
| JSON 请求体 | `p: ProductCreate` | `application/json` |
| 表单字段 | `x: str = Form()` | `application/x-www-form-urlencoded` |
| 文件 | `f: UploadFile = File()` | `multipart/form-data` |

> 🟡 记住一句话:**声明了 `Form`/`File`,请求体就不再是 JSON**。Ch21 的 OAuth2 登录表单会真用到 `Form`。

---

## §15.9 Java 老手常踩的坑 ⚠️

1. **路径参数必须和 `{...}` 同名**:`/products/{product_id}` 配参数 `product_id`,名字不一致取不到值。
2. **可选查询参数 = `X | None = None` 两件套**:只写 `| None` 不给 `= None` 默认值,参数仍是必填。
3. **过滤判断用 `is not None`,不用 truthiness**:`if min_price:` 会把 `0` 当「没传」。
4. **具体路径先于参数路径注册**:`/products/search` 写在 `/products/{product_id}` 前面,否则被抢 → 422。
5. **422 / 404 / 400 分工**:形状/约束错 → 框架 422;资源不存在 → 你抛 404;业务规则(库存不足)→ 你抛 400。
6. **分页越界返空列表,不是 404**;元信息 `pages = (total + size - 1) // size`。
7. **排序字段用 `Literal` 白名单**,别把用户输入直接喂给 `getattr` / SQL。
8. **`Query` / `Path` / `Field` 是同一套约束参数**(`ge/le/gt/lt/min_length/pattern`),只是战场不同:查询参数 / 路径参数 / 模型字段。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `get_product` | 路径参数 + Path(ge=1) + 404 | 🟢 |
| `list_products` | 可选查询参数三条件筛选 | 🟡 |
| `search_products` | Query 必填/范围校验 + 路由顺序 | 🟡 |
| `list_orders` | 分页切片 + 元信息 | 🟡 |
| `list_product_ranking` | Literal 白名单 + sorted | 🟡 |
| `create_order` | 嵌套请求体 + 业务校验(综合) | 🔴 |
| `register_system_router` | APIRouter + include_router | 🟢 |

```bash
uv sync --extra web
uv run pytest 03_web_framework/ch15/test_ch15_assignment.py -v
```

---

## ✅ 自测

- [ ] 能说清 FastAPI 如何靠「路径里有没有 + 类型」自动区分路径参数/查询参数/请求体
- [ ] 会写可选查询参数(`X | None = None`)并用 `is not None` 判断过滤
- [ ] 会用 `Query` / `Path` 加约束,知道违反约束是 422
- [ ] 能解释 `/products/search` 为什么要先注册
- [ ] 会写分页公式 + 元信息,知道越界返 `[]`
- [ ] 会用 `Literal` 做排序白名单,知道为什么不能用裸 `str`
- [ ] 能分清形状校验(框架,422)和业务校验(自己,404/400)
- [ ] 7 个作业全绿

## 🎓 费曼挑战

1. 「FastAPI 不写 @PathVariable/@RequestParam,怎么知道参数从哪来?」— 重读 §15.1
2. 「为什么 `if category:` 是 bug,`if category is not None` 才对?」— 重读 §15.2
3. 「如果 `/products/{product_id}` 比 `/products/search` 先注册,访问 `/products/search?q=键盘` 会发生什么?为什么?」— 重读 §15.3
4. 「`quantity=0` 和「库存不够」都是拒绝,为什么一个 422 一个 400?」— 重读 §15.6

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步

Ch15 掌握后,进 **Ch16 · 依赖注入(`Depends`)**——FastAPI 最强大的设计之一,对比 Spring `@Autowired`。把本章的「分页参数」「当前用户」「DB session」等重复逻辑抽成可复用依赖。
