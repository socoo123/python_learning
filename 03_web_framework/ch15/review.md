# Ch15 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | FastAPI 不写注解,怎么区分路径参数/查询参数/请求体? | ① 名字在路径 `{x}` 里 → 路径参数 ② 简单类型且不在路径 → 查询参数 ③ Pydantic 模型 → 请求体。靠「位置 + 类型」自动判断 | ⬜ |
| 2 | `Path(ge=1)` 干嘛?`/products/0` 和 `/products/abc` 各返回什么? | 校验路径参数(id ≥ 1)。两个都 **422**:abc 是 int 转换失败,0 是 ge=1 约束失败,函数体都不执行 | ⬜ |
| 3 | 可选查询参数怎么写?为什么必须 `= None`? | `category: str \| None = None`。只写 `\| None` 不给默认值仍是**必填**——类型可空 ≠ 参数可选 | ⬜ |
| 4 | 过滤判断为什么用 `is not None` 不用 `if x:`? | `if x:` 会把 `0` / `""` / `False` 当「没传」跳过过滤(truthiness 坑);`None` 才是「没传」的唯一信号 | ⬜ |
| 5 | `Query(min_length=2)` 和 `Query(10, ge=1, le=50)` 区别? | 前者**必填**(没给默认值)+ 至少 2 字符;后者可选、默认 10、范围 1~50。违反都 422 | ⬜ |
| 6 | `/products/search` 和 `/products/{product_id}` 谁先注册?颠倒后果? | **具体路径先注册**。颠倒后 search 被 `{product_id}` 抢走 → "search" 转 int 失败 → 422。FastAPI 先匹配先赢,不像 Spring 精确度优先 | ⬜ |
| 7 | 分页公式?元信息 pages 怎么算?越界页返什么? | `start = (page-1)*size`,切 `[start:start+size]`;`pages = (total+size-1)//size`;越界返 `items: []`,**不是 404** | ⬜ |
| 8 | 排序参数 `sort_by` 怎么防止任意字段名? | `sort_by: Literal["price", "stock"] = "price"`——白名单外自动 422,文档出枚举下拉;之后 `getattr(p, sort_by)` 才安全 | ⬜ |
| 9 | 嵌套请求体怎么声明?两层校验怎么分工? | `items: list[OrderItemCreate] = Field(min_length=1)`,框架递归校验。形状错(quantity=0/空 items)→ 框架 422;业务错(商品不存在/库存不足)→ 你抛 404/400 | ⬜ |
| 10 | `APIRouter` + `include_router` 对应 Spring 什么?prefix 何时加? | ≈ 按 Controller 拆文件 + 类级 `@RequestMapping("/x")`。`app.include_router(router, prefix="/system", tags=["系统"])`——前缀在**注册时**加,同一 router 可不同前缀挂多次(/v1 /v2) | ⬜ |
| 11 | `Query` / `Path` / `Field` 什么关系? | 同一套约束参数(`ge/le/gt/lt/min_length/pattern`),三个战场:查询参数 / 路径参数 / 模型字段 | ⬜ |
| 12 | 422 / 404 / 400 怎么分工? | 422 = 请求形状/约束不合法(框架自动);404 = 资源不存在(你抛);400 = 业务规则拒绝,如库存不足(你抛) | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「参数三来源判定 + 路由注册顺序坑」?
- [ ] 能说清「可选参数两件套 + is not None + Literal 白名单」?
- [ ] 能说清「分页公式与元信息 + 越界返空」?
- [ ] 能说清「嵌套请求体的两层校验分工」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
