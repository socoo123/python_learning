# Ch21 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | JWT 的三段结构?payload 能放密码吗? | `header.payload.signature`。header=算法/类型,payload=claims(sub/role/exp),signature=HMAC(前两段, SECRET_KEY)。payload 是 Base64 **明文**,谁都能解,**绝不放密码**——JWT 防篡改不防偷看 | ⬜ |
| 2 | JWT 为什么叫「无状态」?好处/代价? | 服务端不存 session,每次靠 SECRET_KEY 验签。好处:水平扩展不用共享 session,任意机器都能验。代价:token 到 exp 前无法主动作废(踢人得上黑名单,又变有状态) | ⬜ |
| 3 | 密码为什么用 bcrypt 不用 SHA-256?同密码两次哈希结果不同是 bug 吗? | SHA-256 太快,GPU 撞库秒破;bcrypt **故意慢**(cost 可调)+ **内置随机盐**。不是 bug 是特性——所以验证必须 `verify(明文, 哈希)`,不能「再哈希一次比对」 | ⬜ |
| 4 | passlib 为什么不推荐?替代方案? | passlib 1.7.4 自 2020 未更新,与 bcrypt ≥ 4.1 不兼容(抛 ValueError)。直接用官方 `bcrypt` 库,套个 `hash`/`verify` 薄封装,业务写法不变 | ⬜ |
| 5 | `jwt.encode` / `jwt.decode` 各自动做了什么?decode 失败抛什么? | encode:dict + SECRET_KEY → 带签名的 JWT 串。decode:解 Base64 + **验签名** + **自动查 exp 过期**。签名错/过期/格式错统一抛 `JWTError`(python-jose) | ⬜ |
| 6 | 算 `exp` 的正确写法?为什么 `datetime.now()` 是坑? | `datetime.now(timezone.utc) + timedelta(...)`。naive datetime 无时区,某些环境让 token 立刻过期或永不过期;永远用 aware UTC | ⬜ |
| 7 | `OAuth2PasswordBearer(tokenUrl="token")` 当依赖用的行为?tokenUrl 干嘛的? | 请求带 `Authorization: Bearer <token>` → 提取 token;没带 → 自动 401 + `WWW-Authenticate: Bearer` 头。tokenUrl 只是告诉 Swagger UI 登录入口(/docs 出现 Authorize 按钮) | ⬜ |
| 8 | 登录端点为什么失败不区分「用户不存在」和「密码错」? | 防用户名枚举:两种失败统一 401 + 同一句「用户名或密码错误」,否则攻击者能探出哪些用户名已注册 | ⬜ |
| 9 | 401 vs 403 区别?FastAPI 里 RBAC 怎么写? | 401=未认证(你是谁?);403=已认证没权限(你不够格)。RBAC=依赖嵌套:`require_admin(current_user=Depends(get_current_user))`,role 不对抛 403——≈ Spring `@PreAuthorize("hasRole('ADMIN')")` | ⬜ |
| 10 | 受保护端点为什么函数体只有一行?鉴权逻辑写端点里有什么问题? | 鉴权收敛进 `get_current_user` 依赖,端点 `Depends` 它即可;token 无效 → 依赖链中 raise 401 → FastAPI 短路,**端点函数根本不执行**。写端点里 = 重复 + 易漏,违背声明式模式 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「JWT 三段结构 + 为什么无状态 + 代价」?
- [ ] 能说清「为什么 bcrypt 而不是 SHA-256(慢为什么是优点)」?
- [ ] 能说清「依赖链如何短路 + 401/403 分工」(对照 Spring Filter 链 / @PreAuthorize)?
- [ ] 能讲一遍「注册 → 登录 → /me → /admin/stats」全链路每一跳谁来拦?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
