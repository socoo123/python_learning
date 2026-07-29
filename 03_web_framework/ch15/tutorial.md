# Ch15 · 路由参数:路径参数 / 查询参数 / 分页

> **预计**:0.5 天 ｜ **前置**:Ch14
> **目标**:搞清 FastAPI 的「参数三来源」——**路径参数 / 查询参数 / 请求体**——FastAPI 怎么靠类型注解自动区分。给商品 API 加筛选和分页。

> 📐 **本教程的契约**:§15.1–§15.4 对应作业。

---

## 🗺️ 本章地图

**作业 ↔ 教程对应表**:

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `list_products`(筛选) | §15.2 | 查询参数(可选 + 默认) |
| `list_products`(分页) | §15.4 | Query 校验 + 切片分页 |
| `get_product` | §15.1 | 路径参数 + 422 |

---

## ⏱️ 学习路径:费曼五步(约 45 分钟)

① 预览猜 → ② 写 assignment → ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## ① 预览猜

1. Spring `@PathVariable("id")` 和 `@RequestParam("category")` 区分路径/查询参数。FastAPI 怎么区分(不写注解)?
2. 查询参数「可选,不传就不过滤」怎么写类型?
3. 分页参数 page 不能 ≤ 0、size 不能超过 100,怎么用一行注解约束?
4. `/products/abc`(id 应是 int)FastAPI 返回什么?

---

## §15.1 路径参数 vs 查询参数:FastAPI 怎么区分 🔴

FastAPI 靠**两个规则**自动判断参数来源(不用 `@PathVariable`/`@RequestParam`):

| 参数特征 | 来源 | 示例 |
|----------|------|------|
| 名字在路径 `{xxx}` 里 | **路径参数** | `/products/{product_id}` + `product_id: int` |
| 简单类型(int/str/float)且名字不在路径里 | **查询参数** | `category: str` → `?category=book` |
| Pydantic 模型类型 | **请求体** | `p: ProductCreate`(Ch14) |

```python
@app.get("/products/{product_id}")        # 路径里有 {product_id}
def get_product(product_id: int):          # product_id → 路径参数(从 URL 提取)
    ...

@app.get("/products")
def list_products(category: str = "all"):  # category 不在路径里 → 查询参数 ?category=xxx
    ...
```

> 🤯 **Java 老手震惊点**:Spring 要写 `@PathVariable` / `@RequestParam` / `@RequestBody` 显式标注。FastAPI 一个类型注解 + 是否在路径里,自动判断。少写一半样板。

### 路径参数的类型校验

```python
@app.get("/products/{product_id}")
def get_product(product_id: int):    # int 注解:URL "1"→1;非数字如 "abc"→422
    ...
```
`/products/abc` 会返回 **422**(路径参数类型校验失败),不是 404。

> ✅ 做 `get_product` 题:遍历找 id 匹配,找不到 `HTTPException(404)`。

---

## §15.2 查询参数:可选 + 默认值(对应:`list_products` 筛选)🟡

```python
@app.get("/products")
def list_products(
    category: str | None = None,       # 可选:不传是 None
    min_price: float | None = None,    # 可选
):
    result = PRODUCTS
    if category is not None:            # 只过滤「传了的」参数
        result = [p for p in result if p.category == category]
    if min_price is not None:
        result = [p for p in result if p.price >= min_price]
    return result
```

**关键模式**:`str | None = None` 表示「可选查询参数,不传时是 None」。函数内用 `if xxx is not None` 判断要不要过滤——这样「不传 = 不过滤」。

> 🟡 **Java 对比**:= `@RequestParam(required = false) String category`。Python 用 `str | None = None` 表达「可空 + 默认 None」。

调用:`GET /products?category=图书&min_price=50` → category="图书", min_price=50.0。

---

## §15.3 Query 校验:约束查询参数(对应:分页参数)

`Query(默认值, 约束)` 给查询参数加约束(类似 Ch14 的 Field,但用于简单类型参数):

```python
from fastapi import Query

@app.get("/products")
def list_products(
    page: int = Query(1, ge=1),             # 默认1,必须 >=1
    size: int = Query(10, ge=1, le=100),    # 默认10,范围 1~100
):
    ...
```

| 约束 | 含义 |
|------|------|
| `ge=1` | >= 1 |
| `le=100` | <= 100 |
| `gt=0` | > 0 |
| `lt=1000` | < 1000 |

`page=0` 或 `size=200` 会被拒绝 → **422**。

> ✅ 分页参数用 `Query(默认, ge=, le=)` 约束。

---

## §15.4 分页:切片(对应:`list_products` 分页)🟡

```python
start = (page - 1) * size       # 第 page 页 → 跳过 (page-1)*size 个
return result[start:start + size]
```

page 从 1 开始(对前端友好),转换成 0-based 切片:
- page=1, size=2 → `[0:2]`(第 1、2 个)
- page=2, size=2 → `[2:4]`(第 3、4 个)
- 超出范围 → `[]`(空列表,不是错误)

> 🟡 这是标准分页公式,记住:`start = (page-1) * size`。Ch19 接数据库后会换成 SQL 的 `offset/limit`,但公式一样。

> ✅ 做 `list_products` 题:筛选(两个可选参数)+ 分页切片组合。

---

## §15.5 速查:参数三来源判定(背下来)

```
def endpoint(
    path_param: int,            # 名字在路径 {path_param} 里 → 路径参数
    query_required: str,        # 简单类型,不在路径里,无默认 → 必填查询参数
    query_optional: int = 10,   # 简单类型,有默认 → 可选查询参数
    body: ProductCreate,        # Pydantic 模型 → 请求体
):
```

---

## §15.6 Java 老手常踩的坑 ⚠️

1. **路径参数和函数参数同名才匹配**:`/products/{product_id}` 要参数叫 `product_id`。名字不一致取不到。
2. **可选查询参数用 `X | None = None`**:不是 `Optional[X]` 也行,但 `= None` 必须有(否则变必填)。
3. **分页 page 从 1 开始**:别用 0-based page,前端约定俗成是 1-based。切片时 `(page-1)*size`。
4. **超出范围的页返 `[]` 不是 404**:分页越界是空列表,正常业务结果。
5. **路径参数类型错是 422 不是 404**:`/products/abc` 返 422(类型校验),不是 404。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| 筛选(category/min_price) | 可选查询参数 | 🟡 |
| 分页(page/size) | Query 校验 + 切片 | 🟡 |
| `get_product` | 路径参数 + 422 | 🟢 |

```bash
uv run pytest 03_web_framework/ch15/test_ch15_assignment.py -v
```

---

## ✅ 自测

- [ ] 能说清 FastAPI 如何靠「路径里有没有 + 类型」自动区分路径参数/查询参数/请求体
- [ ] 会写可选查询参数(`X | None = None`)并用 `is not None` 判断过滤
- [ ] 会用 `Query(默认, ge=, le=)` 约束分页参数,知道越界返 422
- [ ] 3 个作业全绿

## 🎓 费曼挑战

1. 「FastAPI 不写 @PathVariable/@RequestParam,怎么知道哪个参数从哪来?」— 重读 §15.1/§15.5
2. 「可选查询参数怎么写?为什么用 `is not None` 判断而不是 `if category:`?」— 重读 §15.2

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步

Ch15 掌握后,进 **Ch16 · 依赖注入**——FastAPI 最强大的设计之一(`Depends`,对比 Spring `@Autowired`)。把分页参数、当前用户、DB session 等公共逻辑抽成可复用的依赖。
