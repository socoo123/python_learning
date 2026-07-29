# Ch14 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | FastAPI「类型注解驱动一切」具体驱动了哪 4 件事? | ① 解析参数(路径/查询/请求体)② 校验数据 ③ 序列化响应成 JSON ④ 生成 OpenAPI 文档。一个类型注解全搞定 | ⬜ |
| 2 | Pydantic `BaseModel` 对应 Java 什么?比它多了什么? | = Java DTO + 自动校验 + 自动(反)序列化,三位一体。比 DTO 多了校验和序列化自动化 | ⬜ |
| 3 | Pydantic 校验失败(price=-1)返回什么状态码? | **422** Unprocessable Entity(不是 400)。FastAPI/Pydantic 的默认约定 | ⬜ |
| 4 | `Field(gt=0)` / `ge` / `min_length` 各什么? | gt=大于,ge=大于等于,lt/le=小于/小于等于,min_length=字符串最小长度。给字段加约束,校验失败自动 422 | ⬜ |
| 5 | Pydantic v2 模型转 dict 用什么?v1 呢? | v2 用 `model_dump()`;v1 用 `dict()`(已废弃)。本项目 v2。常配合 `**` 解包造另一模型 | ⬜ |
| 6 | `HTTPException(status_code=404, detail=...)` 干嘛?对应 Java? | 抛 HTTP 错误响应。= Spring `ResponseStatusException`。常用于资源不存在返 404 | ⬜ |
| 7 | 怎么不用启动服务测自己的 API?自动文档在哪? | `TestClient(app)` 直接对 app 发 HTTP 请求(基于 httpx,= Spring MockMvc)。自动文档在 `/docs`(Swagger)和 `/redoc` | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「类型注解驱动的 4 件事、Pydantic vs Java DTO」?
- [ ] 能说清「校验失败 422、Field 约束怎么加」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
