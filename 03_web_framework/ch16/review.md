# Ch16 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | `Depends(f)` 怎么工作?和 Spring @Autowired 三个差异? | 端点声明 `param = Depends(f)`,FastAPI 调 f 把返回值注入 param。差异:① 无 IoC 容器/组件扫描 ② 函数级声明 ③ 默认每请求重新调用(适合 DB session),Spring 注入单例 bean | ⬜ |
| 2 | 写 `Depends(get_current_user())`(加括号)会怎样? | 错!括号 = 你立刻调了一次,注入的是那次调用的返回值。Depends 接收**函数本身**,调用是框架的事 | ⬜ |
| 3 | yield 依赖的三段式?对应 Ch06 什么? | ① yield 前 setup(获取资源)② yield 值(注入端点)③ finally 清理(总执行)。= Ch06 `@contextmanager` 的套路,FastAPI 内部就是用 contextlib 包装生成器 | ⬜ |
| 4 | 为什么 yield 依赖的清理必须放 finally?只写在 yield 后面呢? | 端点抛异常时,生成器在 yield 处被关闭,yield 后的普通代码执行不到;finally 保证正常/异常都清理 | ⬜ |
| 5 | 怎么验证 yield 依赖「异常也清理」?(本章测试手法) | 模块级 `DB_AUDIT` 日志:请求一个会 404 的端点,断言日志仍是 `["open", "close"]` | ⬜ |
| 6 | 依赖里 `raise HTTPException(401)` 会发生什么? | **短路**:端点函数体根本不执行,直接返回 401。鉴权依赖能「写一处,N 端点复用」就靠这个 | ⬜ |
| 7 | `x_token: str \| None = Header(default=None)` 怎么映射请求头? | 参数名 `x_token` → 自动找 `X-Token` 头(下划线转连字符);`default=None` 表示可选。要别名用 `Header(alias="...")` | ⬜ |
| 8 | 依赖函数能声明 Query/Header 参数吗?校验生效吗? | 能!FastAPI 一并解析,`Query(ge=1)` 等校验照常 422——解析+校验+打包全在端点之外 | ⬜ |
| 9 | 类依赖解决什么问题?本章怎么打包分页? | 把一组相关参数打包成对象,端点签名干净。`Pagination(page, size)` + `offset` property 一处定义,N 个端点共享 | ⬜ |
| 10 | 嵌套依赖怎么写?`/admin/stats` 无 token 为什么是 401 不是 403? | `def require_admin(user = Depends(get_current_user))`,FastAPI 自动解析整条链。无 token 时上游 get_current_user 先短路 401,require_admin 没机会执行 | ⬜ |
| 11 | 401 vs 403 vs 404 分工? | 401 = 没认证(无/坏 token);403 = 已认证但没权限(非 admin、看别人订单);404 = 资源不存在。权限不够抛 401 会误导客户端「重新登录」 | ⬜ |
| 12 | 查单个订单为什么「先 404 再 403」? | 不存在的订单不暴露归属;确认存在后才谈权限(存在但越权 → 403) | ⬜ |
| 13 | 注入了 `user` 为什么还要按 `user` 过滤订单? | 只鉴权不过滤 = 水平越权(IDOR):bob 能看到 alice 的订单。鉴权不是摆设,user 必须参与业务过滤 | ⬜ |
| 14 | 下单接口为什么不能把 `username` 放进请求体? | 客户端会自报家门冒充任何人。身份只信服务端:从注入的 `user["username"]` 取 | ⬜ |
| 15 | 同一请求内同一依赖会被解析几次?依赖默认是单例吗? | 同请求内同依赖默认只解析一次(`use_cache=True` 缓存);跨请求**不是单例**,每请求重新调用(正是 DB session 想要的) | ⬜ |
| 16 | 只想让依赖执行、不接收返回值(如整组路由鉴权)怎么写? | `dependencies=[Depends(f)]` 列表式:可挂在 `FastAPI(...)`(全局)/ `APIRouter(...)`(整组)/ 单个端点上 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「Depends 机制 + vs Spring DI 的三个差异」?
- [ ] 能手写 yield 依赖三段式,并解释 404 时 close 为什么也执行?
- [ ] 能说清「401 短路、401 vs 403、嵌套依赖链的解析顺序」?
- [ ] 能说清「水平越权、服务端身份」两个安全点?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
