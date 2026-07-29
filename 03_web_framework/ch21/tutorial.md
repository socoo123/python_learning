# Ch21 · 认证授权 JWT

> **预计**:0.5–1 天 ｜ **前置**:Ch16(依赖注入)、Ch17(中间件/异常)
> **目标**:掌握 **JWT 无状态认证** 全流程——bcrypt 密码哈希、python-jose 编解码、OAuth2 密码流登录发 token、依赖注入鉴权受保护端点。学完你能给任何 API 加上登录。

> 📐 **本教程的契约**:讲过的才考,考的必讲过。§21.1–§21.5 对应作业五处填空。

---

## 🗺️ 本章地图

**作业 ↔ 教程对应表**:

| 作业填空 | 对应小节 | 核心知识点 |
|----------|----------|-----------|
| `hash_password` / `verify_password` | §21.2 | bcrypt 哈希(单向 + 随机盐) |
| `create_access_token` | §21.3 | jose.jwt.encode + exp 过期 claim |
| `login`(POST /token) | §21.4 | OAuth2PasswordRequestForm + 验密码发 token |
| `get_current_user` | §21.5 | Depends(oauth2_scheme) + jwt.decode 验签 |
| `read_current_user`(GET /me) | §21.5 | 依赖 get_current_user 鉴权 |

---

## ⏱️ 学习路径:费曼五步(约 60–90 分钟)

| 步骤 | 做什么 | 时间 |
|------|--------|------|
| ① 预览猜 | 先看下面 5 个问题,激活你的 Java/Spring Security 直觉 | 5 min |
| ② 先动手 | 打开 `ch21_assignment.py`,不看答案先试着填 | 15 min |
| ③ pytest 红绿 | 跑测试,红→对照对应 §→改→绿,逐个点亮 | 30 min |
| ④ 费曼 | 合上教程,用自己的话讲清 §21.1(为何无状态)、§21.2(bcrypt 为何慢) | 10 min |
| ⑤ 存闪卡 | 把 `review.md` 的 7 张卡过一遍,标记掌握度 | 10 min |

---

## ① 预览猜(先想,别急着翻答案)

1. Spring Security 一套 `WebSecurityConfigurerAdapter` + `UserDetailsService` + `AuthenticationProvider` + `JwtFilter` 配下来几十行。FastAPI 给 API 加登录,最少要几样东西?
2. 服务器**不存 session**,凭什么能「认出」第二次请求是同一个用户?
3. 一个 JWT 长这样 `xxx.yyy.zzz`(三段,点号分隔)。这三段分别是什么?为什么**不能**把密码放进去?
4. 数据库里存用户密码,为什么不能存明文?为什么连 SHA-256 都不够、非要用 bcrypt(它慢得多)?
5. 客户端登录拿到 token 后,后续请求怎么带?服务端在 FastAPI 里用什么机制(Ch16 学过)统一拦截并校验?

---

## §21.1 认证 vs 授权 + JWT 是什么(本节无填空,但贯穿全章)🟢

先厘清两个词(Java 老手别混淆):

- **认证(Authentication,AuthN)**:你是谁?——验证用户身份(账号密码、token)。对应 Spring Security 的 `AuthenticationManager`。
- **授权(Authorization,AuthZ)**:你能干什么?——检查权限(是不是 admin、能不能访问这个资源)。对应 `@PreAuthorize` / `AccessDecisionManager`。

**本章只做认证**(登录 + 验 token),授权(角色/权限)是下一步。但 JWT 里可以带角色信息,为授权铺路。

### JWT 三段结构

JWT(JSON Web Token)就是一个**带签名的字符串**,长这样:

```
eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhbGljZSIsImV4cCI6MTcwMDAwMDAwMH0.s8f3k2j...
└──── header ────┘└──────── payload ─────────────────────────┘└─ signature ─┘
```

用 `.` 分成三段,每段都是 Base64URL 编码:

| 段 | 内容 | 解码后 | 能改吗 |
|----|------|--------|--------|
| **header** | 算法 + 类型 | `{"alg":"HS256","typ":"JWT"}` | 改了签名就失效 |
| **payload** | 业务数据(叫 **claims**) | `{"sub":"alice","exp":1700000000}` | 改了签名就失效 |
| **signature** | `HMAC-SHA256(base64(header)+"."+base64(payload), SECRET_KEY)` | 一段二进制 | —— |

**关键认知**:
- payload 是**明文**(Base64 不等于加密!)。**绝不放密码、信用卡号**。JWT 解决的是「防篡改」不是「防偷看」。
- 签名用服务端的 `SECRET_KEY` 算。客户端拿不到 key,所以**改了 payload 算不出正确签名** → 服务端 `decode` 时验签失败 → 401。
- 这就是「**无状态(stateless)**」:服务端不存 session,每次只靠 `SECRET_KEY` 重新验签就能确认 token 真实性。

> 🟢 **Java 对比**:Spring Security 走 Session/JWT Filter 一套;Servlet 容器默认存 session(有状态),要无状态得配 `SessionCreationPolicy.STATELESS`。FastAPI 一开始就是无状态的——没有 session 这个概念,token 全靠你自己发/自己验。

> 🤯 **为什么无状态重要**:水平扩展时,有状态 session 要么粘性路由、要么共享 session 存储(Redis)。无状态 JWT **任何一台机器都能验**——加机器不用动 session。代价:token 没法主动作废(发出去就有效到 exp),退出登录只能靠客户端删 token 或上「黑名单」(又变有状态了)。这是 JWT 的根本权衡。

---

## §21.2 密码哈希:bcrypt(对应:`hash_password` / `verify_password`)🔴

### 为什么存哈希、为什么不存明文、为什么不用 SHA-256

| 方案 | 问题 |
|------|------|
| 存明文 | 数据库泄露 = 所有人密码泄露。绝对不行。 |
| 存 `SHA-256(password)` | SHA-256 太快,GPU 一秒能跑几亿次,撞库/彩虹表秒破。不行。 |
| 存 `bcrypt(password)` | **故意设计得很慢**(可调 cost),暴力破解成本爆炸。✅ |

bcrypt 还**内置随机盐(salt)**:同一密码每次哈希结果不同 → 攻击者没法用预算好的彩虹表。这就是为什么 `hash_password("x")` 调两次结果不一样。

### Python 写法

本教程直接用官方 `bcrypt` 库(原因见下方坑)。`pwd_context` 是个薄封装,对外两个方法 `hash` / `verify`:

```python
import bcrypt

# 哈希(注册时 / 模块加载时算一次,存库)
hashed = bcrypt.hashpw("alice123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
# → "$2b$12$...."   (bcrypt 哈希串,以 $2 开头)

# 验证(登录时)
ok = bcrypt.checkpw("alice123".encode("utf-8"), hashed.encode("utf-8"))   # True
```

> ⚠️ bcrypt 吃 **bytes** 不吃 str,所以 `encode("utf-8")` / `decode("utf-8")` 是固定动作。本教程的 `CryptContext` 封装把这步做掉了,你直接 `pwd_context.hash(p)` / `pwd_context.verify(plain, hashed)`。

> ✅ 做 `hash_password` / `verify_password` 题:一行 return 对应的 `pwd_context.hash(...)` / `pwd_context.verify(...)`。

> 🔴 **Java 老手常踩的坑 —— passlib 兼容问题**:网上 99% 的 FastAPI 教程让你用 `passlib.CryptContext(schemes=["bcrypt"])`。但 **passlib 1.7.4 自 2020 年起没更新过**,与新版 `bcrypt >= 4.1`(尤其 5.0)不兼容——passlib 内部探测代码会触发 bcrypt 5 的「密码不能超过 72 字节」检查,直接抛 `ValueError`。这就是为什么本教程**直接用 bcrypt 库**(2024+ FastAPI 官方文档也在往这个方向走)。`hash`/`verify` 两个方法名和 passlib 一致,记忆零负担。如果你接手的老项目用的 passlib 还能跑(bcrypt 没升级),把底层换掉即可,业务代码不用改。

---

## §21.3 生成 JWT(对应:`create_access_token`)🟡

用 `python-jose` 编码。核心一行:

```python
from jose import jwt
from datetime import datetime, timedelta, timezone

token = jwt.encode(
    {"sub": "alice", "exp": datetime.now(timezone.utc) + timedelta(minutes=30)},
    SECRET_KEY,
    algorithm="HS256",
)
```

**几个点**:

1. **`sub`(subject)** 是 JWT 标准 claim,放用户标识(用户名/user id)。你也可以自定义(如 `"role": "admin"`),但 `sub` 是约定俗成的「我是谁」。
2. **`exp`(expiration)** 也是标准 claim。`jwt.decode` 会**自动检查过期**——过了 exp 直接抛 `JWTError`,你不用自己判时间。
3. **`datetime.now(timezone.utc)`** 必须用**带时区**的 UTC。用 `datetime.now()`(naive,无时区)在某些环境会有偏差。Python 3.14 强烈建议永远用 aware datetime。
4. **`SECRET_KEY`**:HS256 是**对称**算法,签发和验证用同一个 key。**生产从环境变量读,绝不硬编码**——`SECRET_KEY = os.environ["SECRET_KEY"]`,key 泄露 = 任何人都能伪造 token。

> 🟡 **Java 对比**:= `io.jsonwebtoken (jjwt)` 的 `Jwts.builder().setSubject("alice").setExpiration(...).signWith(key).compact()`。python-jose 的 `jwt.encode` 就是它的对应。思路完全一样,语法更省。

> ✅ 做 `create_access_token` 题:`to_encode = data.copy()` → 算 `expire` → `to_encode.update({"exp": expire})` → `jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)`。

---

## §21.4 OAuth2 密码流 + 登录端点(对应:`login`)🔴

### OAuth2PasswordBearer 是什么

```python
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
```

`oauth2_scheme` 本身是个**依赖**(Ch16 学过)。把它放进 `Depends(...)`:
- 请求带 `Authorization: Bearer <token>` → 它把 token 提取出来给你。
- 请求没带 → 自动返 **401**(还帮你加 `WWW-Authenticate: Bearer` 响应头)。

`tokenUrl="token"` 只是告诉 Swagger UI:「登录去 POST /token 拿 token」,它会在 `/docs` 页面生成一个「Authorize」按钮。

### OAuth2PasswordRequestForm 是什么

```python
from fastapi.security import OAuth2PasswordRequestForm

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # form_data.username / form_data.password —— 从表单里取
```

OAuth2 密码流规定:客户端用 **`application/x-www-form-urlencoded` 表单**提交 `username` + `password`(不是 JSON!)。`OAuth2PasswordRequestForm` 就是帮你解析这个表单的依赖。`form_data.username` / `form_data.password` 直接拿到。

> ⚠️ **依赖 `python-multipart`**:`OAuth2PasswordRequestForm` 解析 form-data 需要 `python-multipart` 库。FastAPI 没装它会在启动时报错。本项目已装(`uv add python-multipart`)。

### 登录端点全流程

```
客户端 POST /token (form: username, password)
        │
        ▼
authenticate_user(username, password)  ← USERS.get + verify_password
        │
   ┌────┴────┐
  None     user
   │         │
   ▼         ▼
 401     create_access_token({"sub": username})
 (带 WWW-      │
  Authenticate) ▼
         {"access_token": token, "token_type": "bearer"}
```

**401 响应带 `WWW-Authenticate: Bearer` 头**是 OAuth2 规范要求,提示客户端「请用 Bearer token 方式重新认证」。

> ✅ 做 `login` 题:`user = authenticate_user(...)` → None 则 `raise HTTPException(401, ..., headers={"WWW-Authenticate": "Bearer"})` → 否则 `token = create_access_token({"sub": user["username"]})` → `return {"access_token": token, "token_type": "bearer"}`。

> 🤯 **Java 对比**:Spring Security 的密码流要配 `AuthenticationManager` + `AuthenticationProvider` + `UserDetailsService` + `PasswordEncoder` + `SecurityFilterChain` 一整套 bean。FastAPI **一个端点函数**搞定——验密码、发 token,全在你眼前。这就是 FastAPI 「依赖注入即一切」的哲学。

---

## §21.5 验 token + 受保护端点(对应:`get_current_user` / `read_current_user`)🔴

这是 JWT 认证的核心。两个东西配合:

### 1. 验 token 的依赖

```python
def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        if username is None or username not in USERS:
            raise HTTPException(401, ...)
        return username
    except JWTError:              # 过期 / 签名错 / 格式错 都抛这个
        raise HTTPException(401, ...)
```

`jwt.decode` **同时做三件事**:解 Base64、**验签名**(签名错抛 `JWTError`)、**查 exp 过期**(过期抛 `JWTError`)。所以你只要 try/except `JWTError` 就能兜住所有「坏 token」。

### 2. 受保护端点 = `Depends(get_current_user)`

```python
@app.get("/me")
def read_current_user(current_user: str = Depends(get_current_user)):
    return {"user": current_user}
```

**魔法在于依赖链**:`/me` 依赖 `get_current_user` → `get_current_user` 依赖 `oauth2_scheme`。

- token 有效 → `get_current_user` 返回用户名 → 端点正常跑。
- token 无效/缺失 → 链中某层 `raise HTTPException(401)` → FastAPI 自动短路,**端点函数根本不会执行**。

这就是 Ch16 依赖注入的威力:**鉴权逻辑写一次,任何端点加一个 `Depends(get_current_user)` 就受保护**。

> ✅ 做 `get_current_user` 题:`jwt.decode` → 取 `sub` → None 或不在 USERS → 401 → 否则 return 用户名;`except JWTError` → 401。
>
> ✅ 做 `read_current_user` 题:`return {"user": current_user}`(鉴权全靠依赖注入,端点函数本身极简)。

> 🟢 **Java 对比**:= Spring Security 的 `OncePerRequestFilter` + `SecurityContextHolder`。FastAPI 不用全局 ThreadLocal(那是 Java 的并发模型),而是用**依赖注入显式传参**——`current_user` 是函数参数,线程安全天然成立。这也是 FastAPI 鉴权代码比 Spring Security 短得多的根本原因。

### 鉴权(授权)预告

`get_current_user` 返回用户名。要加授权,再加一层依赖:

```python
def require_admin(user: str = Depends(get_current_user)) -> str:
    if user != "admin":
        raise HTTPException(403, "需要管理员权限")
    return user

@app.delete("/users/{id}")
def delete_user(id: int, _: str = Depends(require_admin)):   # 依赖嵌套依赖
    ...
```

依赖嵌套依赖,层层加码——这就是 FastAPI 的授权模式(本章不考,了解即可)。

---

## §21.6 整体流程串起来(对照图)

```
┌──────────┐   POST /token (alice/alice123)       ┌──────────────┐
│  客户端   │ ───────────────────────────────────▶ │   /token     │
│          │                                       │ verify_pwd   │
│          │ ◀──────────────────────────────────  │ create_token │
│          │   {"access_token":"eyJ...", "bearer"} └──────────────┘
│          │
│          │   GET /me  Authorization: Bearer eyJ...
│          │ ───────────────────────────────────▶ ┌──────────────┐
│          │                                       │ oauth2_scheme│ → 提取 token
│          │                                       │  get_current │ → decode 验签
│          │                                       │    _user     │ → 返 alice
│          │ ◀──────────────────────────────────  │   /me        │ → {"user":"alice"}
│          │   {"user":"alice"}                    └──────────────┘
└──────────┘
```

---

## §21.7 Java 老手常踩的坑 ⚠️

1. **passlib 与新 bcrypt 不兼容**:passlib 1.7.4 + bcrypt ≥4.1 直接挂。直接用 `bcrypt` 库,`hash`/`verify` 方法名一致。(§21.2 详述)
2. **payload 是明文不是加密**:`{"sub":"alice"}` 只是 Base64,谁都能解。**绝不放密码/敏感信息**。要加密用 JWE(不是 JWT,本教程不涉及)。
3. **`SECRET_KEY` 硬编码**:演示无所谓,**生产必须 `os.environ["SECRET_KEY"]`**。key 泄露 = 整个认证体系崩溃(任何人能伪造任意用户 token)。
4. **token 无法主动作废**:JWT 无状态,发出去到 `exp` 前一直有效。退出登录只能客户端删 token;要服务端能「踢人」得上 token 黑名单(变有状态)。这是 JWT vs Session 的核心权衡。
5. **`exp` 用 naive datetime**:必须 `datetime.now(timezone.utc)`,带时区。naive datetime 在某些环境会导致 token 立刻过期或永不过期。
6. **`OAuth2PasswordRequestForm` 要表单不是 JSON**:客户端要 `Content-Type: application/x-www-form-urlencoded` 发 `username=alice&password=...`。发 JSON 这个依赖拿不到数据。
7. **依赖链短路才安全**:`/me` 的鉴权**全靠 `Depends(get_current_user)`**。端点函数本身**没有**任何 if 判断——如果你把鉴权逻辑写进端点函数而非依赖,就违背了 FastAPI 的模式,容易漏。
8. **bcrypt 故意慢**:`hash_password` 跑几十毫秒是**正常的**(`cost=12` 约 250ms)。这是防暴力破解的设计。测试里哈希慢点别慌。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `hash_password` / `verify_password` | bcrypt 密码哈希 | 🟢 |
| `create_access_token` | jose.jwt.encode + exp | 🟡 |
| `authenticate_user`(辅助) | USERS.get + verify_password | 🟢 |
| `login`(POST /token) | OAuth2 密码流 + 验密码发 token | 🟡 |
| `get_current_user` | Depends(oauth2_scheme) + jwt.decode | 🔴 |
| `read_current_user`(GET /me) | Depends(get_current_user) | 🟢 |

```bash
uv run pytest 03_web_framework/ch21/test_ch21_assignment.py -v
```

16 个测试,全绿即通关。

---

## ✅ 自测清单

- [ ] 能说出 JWT 三段(header / payload / signature)各是什么,为什么 payload 不能放密码
- [ ] 能解释「无状态(stateless)」:服务端不存 session,靠 SECRET_KEY 验签
- [ ] 能说清为什么用 bcrypt 而不是 SHA-256(慢哈希 + 随机盐 → 防暴力/彩虹表)
- [ ] 能用 `Depends(oauth2_scheme)` + `jwt.decode` 写出鉴权依赖,并说清依赖链如何短路
- [ ] 知道 passlib 与新 bcrypt 的兼容坑,以及生产 SECRET_KEY 必须从环境变量读
- [ ] 16 个测试全绿

---

## 🎓 费曼挑战(合上教程讲,讲不清重读)

1. **「JWT 为什么叫无状态?相比 Spring Session 有什么好处和代价?」**
   —— 卡壳重读 §21.1(无状态段落)。
2. **「为什么密码要用 bcrypt 哈希而不是 SHA-256?bcrypt 慢为什么反而是优点?」**
   —— 卡壳重读 §21.2。
3. **「`get_current_user` 里 `jwt.decode` 自动做了哪几件事?为什么端点函数本身不需要写 if 判断鉴权?」**
   —— 卡壳重读 §21.5(验签名+exp + 依赖链短路)。

---

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步

学完 Ch21,你的 API 有了「门禁」。下一个自然的进阶:
- **授权(角色/权限)**:`get_current_user` 之上再叠 `require_admin` 依赖,区分 admin/普通用户。
- **Refresh Token**:access token 短期(15min)+ refresh token 长期(7天),access 过期用 refresh 换新的,避免用户频繁登录。
- **接数据库**:本章 USERS 是内存 dict,生产换成 SQLAlchemy(Ch19)+ users 表。
- **Ch22 部署**:uvicorn/gunicorn 多 worker 下,JWT 无状态的优势就体现出来了——不用共享 session。
