# Ch14 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | FastAPI「类型注解驱动一切」具体驱动哪 4 件事? | ① 解析参数(路径/查询/请求体) ② 校验数据 ③ 序列化响应 JSON ④ 生成 OpenAPI(`/docs`)。一个类型注解全搞定 | ⬜ |
| 2 | Pydantic `BaseModel` 对应 Java 什么?比 DTO 多了什么? | = Java DTO + 自动校验 + 自动(反)序列化。比纯 DTO 多了校验与序列化自动化 | ⬜ |
| 3 | `Field(gt=0)` / `ge=0` / `min_length` / `max_length` / `pattern=` 各管什么? | gt 严格大于;ge 大于等于;min/max_length 字符串长度;pattern 正则(如 SKU `^[A-Z]{2}-\d{3}$`) | ⬜ |
| 4 | `price: float = 0` 和 `price: float = Field(gt=0)` 区别? | 前者只是默认值,负数照过;后者才是校验,违反 → 422 | ⬜ |
| 5 | Pydantic 校验失败(price=-1)默认什么状态码?响应体结构? | **422** Unprocessable Entity;body 是 `{"detail": [{loc, msg, type, input}]}`,`loc` 指出违法字段 | ⬜ |
| 6 | 422 和 404 怎么分工? | 422 = 请求形状/约束不合法(框架自动,函数体不跑);404 = 资源不存在(业务代码主动 `HTTPException`) | ⬜ |
| 7 | 客户端传 `price="599"`(字符串)会怎样?`"abc"` 呢? | lax 模式强转 → `599.0` 不报错;转不了的 `"abc"` → 422。想严格用 `Field(strict=True)` | ⬜ |
| 8 | Pydantic v2 模型转 dict 用什么?怎么灌进另一个模型? | `model_dump()`(v1 的 `dict()` 已废弃)。`Product(id=n, **p.model_dump())` | ⬜ |
| 9 | `HTTPException(status_code=404, detail=...)` 对应 Spring 什么? | ≈ `ResponseStatusException`。查无商品时抛,响应 `{"detail": "..."}` | ⬜ |
| 10 | POST 创建为什么 `status_code=201`?DELETE 为什么 204? | 201=Created「新建成功」;204=No Content,删除成功且无响应体 | ⬜ |
| 11 | 端点里 `_next_id += 1` 为什么必须先 `global _next_id`? | 有赋值会被当成局部变量,不写 global 会 UnboundLocalError(Ch01 坑) | ⬜ |
| 12 | 路径参数 `{product_id}` 和函数参数名不一致会怎样? | FastAPI 把对不上的参数当必传查询参数 → 请求 422,`loc == ["query", "id"]` | ⬜ |
| 13 | 为什么不要 `return json.dumps(...)`? | 返回 str 会被再序列化一次,客户端收到 JSON 字符串而不是数组(双重编码) | ⬜ |
| 14 | `response_model=list[Product]` 除了写文档还有什么用? | 自动过滤响应多余字段(如内部成本价),防数据泄露 ≈ `@JsonIgnore` 但不改模型 | ⬜ |
| 15 | 怎么不启动 uvicorn 测自己的 FastAPI?文档在哪看? | `TestClient(app)`(基于 httpx,≈ MockMvc)。文档 `/docs`(Swagger)、`/redoc` | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「类型驱动 4 件事、Pydantic vs Java DTO」?
- [ ] 能说清「422 vs 404、201 vs 204、model_dump + global、lax 强转」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
