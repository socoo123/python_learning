# Ch21 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | JWT 的三段结构分别是什么?payload 能放密码吗? | `header.payload.signature`。header=算法/类型,payload=业务 claims(sub/exp 等),signature=HMAC(前两段, SECRET_KEY)。payload 是 Base64 **明文**,谁都能解,**绝不放密码** | ⬜ |
| 2 | JWT 为什么叫「无状态(stateless)」?相比 Spring Session 的好处/代价? | 服务端不存 session,每次靠 SECRET_KEY 重算签名验证。好处:水平扩展不用共享 session。代价:token 发出去到 exp 前没法主动作废(退出登录只能客户端删 token 或上黑名单) | ⬜ |
| 3 | 密码为什么用 bcrypt 而不是 SHA-256? | SHA-256 太快,GPU 撞库秒破。bcrypt **故意慢**(可调 cost)+ **内置随机盐**(同密码每次哈希不同),让暴力破解成本爆炸 | ⬜ |
| 4 | `jwt.encode` 和 `jwt.decode` 各自动做了什么?decode 失败抛什么异常? | encode:把 dict + SECRET_KEY → JWT 字符串(自动加签名)。decode:解 Base64 + **验签名** + **查 exp 过期**。签名错/过期/格式错都抛 `JWTError`(python-jose) | ⬜ |
| 5 | `OAuth2PasswordBearer(tokenUrl="token")` 当依赖用时行为? | 带 `Authorization: Bearer <token>` → 提取 token 给你;没带 → 自动返 401 + 加 `WWW-Authenticate: Bearer` 头。tokenUrl 只是给 Swagger UI 的「登录入口」提示 | ⬜ |
| 6 | FastAPI 受保护端点为什么端点函数本身不写 if 鉴权?依赖链如何短路? | 鉴权写在依赖 `get_current_user` 里,端点用 `Depends(get_current_user)`。token 无效 → 依赖链中某层 raise 401 → FastAPI 自动短路,**端点函数根本不执行**。= Spring Security 的 Filter 链短路 | ⬜ |
| 7 | passlib 与新 bcrypt 的兼容坑?生产 SECRET_KEY 怎么管? | passlib 1.7.4(2020 起未更新)与 bcrypt ≥4.1 不兼容,直接抛 ValueError → 直接用官方 `bcrypt` 库(hash/verify 方法名一致)。SECRET_KEY **生产从环境变量读** `os.environ["SECRET_KEY"]`,绝不硬编码,key 泄露=认证体系崩溃 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「JWT 三段结构 + 为什么无状态 + 代价」?
- [ ] 能说清「为什么 bcrypt 而不是 SHA-256(bcrypt 慢为什么是优点)」?
- [ ] 能说清「依赖链如何让端点函数不用写 if 鉴权」(对照 Spring Security Filter 链)?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
