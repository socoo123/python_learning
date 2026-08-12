# Ch16 · 依赖注入系统(Depends)

> **预计**:1 天 ｜ **前置**:Ch15(路由参数 / Query 校验)｜ **M3 第四章 · 重点**
> **目标**:理解 FastAPI 最强大的设计——**依赖注入**(Depends,对比 Spring `@Autowired` / 构造注入)。把鉴权、分页、DB session、权限校验这些「跨端点共享的横切逻辑」抽成可复用的**依赖**;端点只声明「我需要 X」,FastAPI 自动解析并注入。
> 本章主线:你是「极客商城」后端。Ch15 的筛选/分页/排序上线后,架构组做 Code Review 时拍了桌子:**每个端点都在手写 `if not token: 401`、`offset = (page-1)*size`、开关 DB session**——这些横切关注点必须抽成依赖。你的任务:亲手写 4 个依赖(yield session / token 鉴权 / 分页打包 / admin 嵌套权限),再把它们注入订单 API 的 4 个端点。

> 📐 **本教程的契约**:§16.2–§16.5 每节对应一个「你写的依赖」,§16.6–§16.8 每节对应「用依赖组装的端点」。§16.1 是开胃、§16.9/§16.10 是坑与速查。卡住时按对应表回查小节。

---

## 🗺️ 本章地图(元学习 · 原则一)

读完这章 + 完成作业,你将能够:
- 说清 Depends 的工作机制:**声明 → 框架调用依赖 → 返回值注入参数**,以及与 Spring DI 的异同
- 写 **yield 依赖**管理 DB session:setup / yield / teardown 三段,端点抛异常也保证清理(= Ch06 `@contextmanager`)
- 写 **Header 依赖**做 token 鉴权:依赖里 `raise HTTPException(401)` 会**短路**,端点根本不执行
- 写**类依赖**把 page/size 打包成 `Pagination`,`offset` 计算一处定义
- 写**嵌套依赖**(依赖的依赖)实现角色权限,分清 **401(没认证)vs 403(没权限)**
- 在端点里同时注入多个依赖,让「当前用户」参与业务(按用户过滤订单,杜绝水平越权)
- 分清 404(资源不存在)与 403(存在但越权)的分工

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业题 | 对应小节 | 核心知识点 |
|--------|----------|-----------|
| `get_db` | §16.2 | yield 依赖:setup / yield / finally 清理 |
| `get_current_user` | §16.3 | Header 依赖 + 401 短路 |
| `get_pagination` | §16.4 | 类依赖打包参数 + 依赖内声明 Query 校验 |
| `require_admin` | §16.5 | 嵌套依赖 + 401 vs 403 |
| `list_orders` | §16.6 | 注入三依赖:按用户过滤 + 分页 |
| `get_order` | §16.6 | 404(不存在)vs 403(越权) |
| `create_order` | §16.7 | POST + 用注入的 session 写入 + 201 |
| `admin_stats` | §16.8 | 综合:复用 admin 依赖 + 全站统计 |

---

## ⏱️ 学习路径:费曼五步(约 60-90 分钟)

| 步 | 你要做 | 在哪做 |
|----|--------|--------|
| ① 预览猜(2分钟) | 下面 5 个 Spring 场景,猜 FastAPI 怎么写 | 本页 ① |
| ② 先动手 | 打开 `ch16_assignment.py`,**先试着写**(别通读) | assignment |
| ③ 提取+反馈 | 凭记忆写完 → `uv run pytest` 红绿 | test |
| ④ 费曼(2分钟) | 大白话讲清「Depends 机制、yield 清理、401 vs 403」 | 本页 ④ |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡标复习日期 | review.md |

> 💡 **直接性原则**:别通读!先猜 ① → 去 ② 写作业 → **哪题卡了,回对应 § 查** → 改 → 再跑。
> 本章作业形态:`填依赖函数体 + 填端点函数体`。测试用 `TestClient` 发真 HTTP 语义请求,依赖函数也被直接单测(它们就是普通函数)。

---

## ① 预览猜(2 分钟 · 激活你的 Java 直觉)

先别看答案,凭 Spring 经验猜:
1. Spring 用 `@Autowired` / 构造注入拿到 service。FastAPI 没有 IoC 容器,端点怎么「声明我需要某个依赖」?
2. 20 个端点都要鉴权,你希望 token 校验只写一处。Spring 里你用拦截器/Filter,FastAPI 的对应物是什么?
3. 端点需要 DB session 且**用完必须关闭(即使端点抛异常)**。Python 哪个语法结构天生适合「获取资源 → 给调用方用 → 保证清理」?(提示:Ch06)
4. 依赖 A 想复用依赖 B 的结果(B 解析 token,A 检查角色),能不能「依赖套依赖」?
5. 「没带 token」和「带了 token 但不是管理员」,HTTP 状态码应该各是多少?

> 猜完带着验证心态进正文。第 3 题的 **yield 依赖**和第 5 题的 **401 vs 403** 是本章最高频考点。

---

## §16.1 为什么需要依赖注入(开胃 · 不出题)🟢

订单 API 的每个端点都长这样——业务只有 1 行,横切逻辑 5 行:

```python
@app.get("/orders")
def list_orders(x_token: str | None = Header(default=None), page: int = 1, size: int = 10):
    if not x_token or x_token not in TOKENS:        # 鉴权(每个端点抄一遍)
        raise HTTPException(401, "未授权")
    session = open_session()                        # 拿 session
    try:
        offset = (page - 1) * size                  # 分页计算(每个端点抄一遍)
        return session.query(...)[offset:offset+size]   # ← 业务只有这 1 行
    finally:
        session.close()
```

问题:鉴权 / session 管理 / 分页计算是**横切关注点**,抄 N 遍,改一处要改 N 处。依赖注入的思路:**把共享逻辑写成「依赖」,端点声明「我需要它」,框架自动调用并把返回值注入进来**。

### Java 对照最小例

```java
// Spring:IoC 容器 + 构造注入,注入的是容器管理的单例 bean
@RestController
public class OrderController {
    private final OrderService orders;
    public OrderController(OrderService orders) { this.orders = orders; }   // 构造注入
}
```

```python
# FastAPI:无容器、无组件扫描,函数级声明;默认每次请求重新调用依赖
@app.get("/orders")
def list_orders(user: dict = Depends(get_current_user)):   # 声明 → 框架调用 → 注入返回值
    return {"user": user["username"]}
```

| | Spring DI | FastAPI Depends |
|---|---|---|
| 声明位置 | 字段 / 构造器(`@Autowired`) | 参数默认值(`= Depends(f)`) |
| 容器 | IoC 容器 + `@Component` 扫描 | 无容器,直接引用函数 |
| 生命周期 | 默认单例 bean | **默认每次请求重新调用**(适合 DB session) |
| 粒度 | 类级 | 函数/端点级,可逐端点组合 |

> 🟡 **Java 对比**:Depends ≈ 「方法参数级的 `@Autowired` + `HandlerInterceptor` + `try-with-resources` 三合一」。更轻是因为没有容器——依赖就是普通函数,框架替你调。

❌ **错误心智**(把 Depends 当成「调用函数」):

```python
user: dict = Depends(get_current_user())   # 加括号 = 你立刻调了一次,返回啥注入啥,错!
```

✅ **正确心智**:`Depends(get_current_user)` 传的是**函数本身**,调用是 FastAPI 的事。

---

## §16.2 yield 依赖:get_db(对应:`get_db`)🔴

DB session、文件句柄这类资源要「用完关闭,即使异常」。FastAPI 的解法是 **yield 依赖**:把依赖函数写成生成器,`yield` 把它切成三段。

### Java 对照最小例

```java
// Spring 里你要么 try-with-resources,要么靠 AOP/@Transactional 替你管 session
try (Session session = sessionFactory.openSession()) {
    return session.createQuery("from Order", Order.class).list();
}   // 出作用域自动 close
```

```python
# FastAPI:依赖函数写成生成器,框架保证 yield 后的清理一定执行
def get_db():
    DB_AUDIT.append("open")          # ① yield 前:获取资源(setup)
    session = {"queries": 0}
    try:
        yield session                # ② yield 的值:注入给端点的对象
    finally:
        DB_AUDIT.append("close")     # ③ yield 后:清理(端点正常/异常都执行)

@app.get("/orders")
def list_orders(db: dict = Depends(get_db)):   # db 就是 yield 出来的 session
    db["queries"] += 1
    ...
# 端点结束后(即使抛 HTTPException),finally 里的 "close" 一定会追加
```

> 🔴 **这就是 Ch06 `@contextmanager` 的三段套路**(yield 前 setup / yield 值 / yield 后 teardown),FastAPI 内部正是用 `contextlib` 包装你的生成器。Ch19 接 SQLAlchemy 时,`get_db` 里 `yield` 的就是真 session。

### 真实场景例(商城 DB 审计)

运维要求「每次请求的连接必须闭环」。本章用模块级 `DB_AUDIT: list[str]` 模拟连接日志,测试直接断言它:

```text
GET /orders(带 token)→ DB_AUDIT 增加 ["open", "close"]
GET /orders/99999(端点抛 404)→ DB_AUDIT 依然增加 ["open", "close"]   ← 关键!
GET /orders 连发两次 → ["open", "close", "open", "close"]            ← 每请求新建,不是单例
```

❌ **错误写法 1**(清理不放在 finally):

```python
def get_db():
    session = open_session()
    yield session
    DB_AUDIT.append("close")   # 端点抛异常时,生成器在 yield 处被 close() 掉,这行执行不到!
```

✅ **正确写法**:`try: yield ... finally: 清理`。

❌ **错误写法 2**(用 `return` 而不是 `yield`):

```python
def get_db():
    return {"queries": 0}   # 普通依赖:值能用,但你永远没机会清理(没有 teardown 钩子)
```

✅ 需要清理的资源才用 yield 依赖;纯计算/解析用普通函数依赖即可(§16.3/§16.4)。

> ✅ 做 `get_db`:三段式——`DB_AUDIT.append("open")` → `try: yield {"queries": 0}` → `finally: DB_AUDIT.append("close")`。测试会验证「404 时 close 也执行」。

---

## §16.3 Header 依赖:get_current_user(对应:`get_current_user`)🔴

鉴权是 DI 最经典的场景:**token 解析 + 校验 + 401 全包在依赖里**,端点只管用 `user`。

### Java 对照最小例

```java
// Spring:@RequestHeader + 拦截器里校验,或在每个方法第一行手写
@GetMapping("/orders")
public List<Order> list(@RequestHeader("X-Token") String token) {
    var user = tokenStore.get(token);
    if (user == null) throw new ResponseStatusException(UNAUTHORIZED, "未授权");
    ...
}
```

```python
from fastapi import Header

def get_current_user(x_token: str | None = Header(default=None)) -> dict:
    #                    ↑ 参数名 x_token → 自动找请求头 X-Token(下划线转连字符)
    if not x_token or x_token not in TOKENS:
        raise HTTPException(status_code=401, detail="未授权")   # 短路:端点不执行
    return TOKENS[x_token]        # {"username": "alice", "role": "user"} → 注入端点
```

### 真实场景例(商城 token 表)

本章用模块级 `TOKENS` 模拟 token → 用户的映射(`tok-alice` → 普通用户 alice,`tok-admin` → 管理员):

```python
get_current_user(x_token="tok-alice")   # → {"username": "alice", "role": "user"}
get_current_user(x_token=None)          # → 抛 HTTPException(401)
# HTTP 层:curl -H "X-Token: tok-bob" /orders → 端点拿到 bob 的 user dict
```

三个关键点:
1. **依赖函数自己也能声明参数**(`Header`/`Query`/路径参数),FastAPI 一并解析——依赖不是「无参工厂」。
2. **依赖里抛 `HTTPException` 会短路**:端点函数体根本不执行,直接返回 401。这就是「鉴权逻辑写一处,20 个端点复用」的原理。
3. **返回值注入**:依赖 return 什么,端点参数就是什么(这里是 user dict;Ch21 会换成 JWT 解析出的 `User` 模型)。

❌ **错误写法**(在端点里继续手写鉴权,依赖白注入):

```python
@app.get("/orders")
def list_orders(user: dict = Depends(get_current_user), x_token: str | None = Header(default=None)):
    if not x_token: ...   # 重复!依赖已经校验过,端点里再写就是没理解 DI
```

✅ **正确写法**:端点签名只留 `user: dict = Depends(get_current_user)`,直接用 `user["username"]`。

> ✅ 做 `get_current_user`:缺失/未知 token → `raise HTTPException(status_code=401, detail="未授权")`;有效 → `return TOKENS[x_token]`。

---

## §16.4 类依赖:Pagination(对应:`get_pagination`)🟡

依赖不只能返回简单值,还能返回**对象**——把一组相关参数打包,端点签名更干净。

### Java 对照最小例

```java
// Spring:用 @ModelAttribute / 参数对象把 page、size 收进一个 POJO
@GetMapping("/orders")
public Page<Order> list(PageQuery q) { ... }   // PageQuery 有 page/size/getOffset()
```

```python
class Pagination:
    def __init__(self, page: int, size: int):
        self.page = page
        self.size = size

    @property
    def offset(self) -> int:          # offset 计算一处定义,20 个端点共享
        return (self.page - 1) * self.size

def get_pagination(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
) -> Pagination:
    return Pagination(page=page, size=size)
```

### 真实场景例(订单列表分页)

```python
get_pagination(page=2, size=3)   # → Pagination(page=2, size=3),.offset == 3
# HTTP 层:GET /orders?page=2&size=3  → 依赖拿到 page=2, size=3
#         GET /orders?page=0         → 422(Query(ge=1) 校验,依赖函数体不执行)
```

注意:**依赖函数签名里的 `Query(...)` 校验照常生效**——Ch15 学的参数校验原样搬进依赖,非法分页直接 422,你的代码不背锅。

❌ **错误写法**(每个端点签名散落 page/size,offset 到处重算):

```python
@app.get("/orders")
def list_orders(page: int = 1, size: int = 10):
    offset = (page - 1) * size   # 第 1 份拷贝;改分页规则要改 N 处
```

✅ **正确写法**:`pagination: Pagination = Depends(get_pagination)`,用 `pagination.offset` / `pagination.size`。

> ✅ 做 `get_pagination`:函数体只有一行——`return Pagination(page=page, size=size)`。`Pagination` 类和 `Query` 校验已给定,体会「声明即解析」。

---

## §16.5 嵌套依赖 + 401 vs 403:require_admin(对应:`require_admin`)🔴

依赖可以**依赖别的依赖**——FastAPI 自动解析整条链:

```python
def require_admin(user: dict = Depends(get_current_user)) -> dict:
    #                          ↑ 这个依赖自己又声明了对 get_current_user 的依赖
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user

@app.get("/admin/stats")
def admin_stats(admin: dict = Depends(require_admin)): ...
# 请求进来:FastAPI 先解析 get_current_user(可能 401)→ 再解析 require_admin(可能 403)→ 才进端点
```

> 🟡 **Java 对比** ≈ Spring Security 的 `@PreAuthorize("hasRole('ADMIN')")`,同样构建在「认证(Authentication)之上再做授权(Authorization)」。

### 401 vs 403:Java 老手也常混

| 状态码 | 含义 | 本章场景 |
|--------|------|----------|
| **401** Unauthorized | **没认证**(我不知道你是谁) | 无 `X-Token` / token 不在 `TOKENS` 表 |
| **403** Forbidden | **已认证但没权限**(我知道你是谁,但你不够格) | alice 访问 `/admin/stats`;bob 查 alice 的订单 |

记忆法:**401 先发生(链条上游),403 后发生(上游已通过)**。所以 `/admin/stats` 无 token 时是 401 而不是 403——`require_admin` 根本没机会执行。

❌ **错误写法 1**(权限不够也抛 401):

```python
raise HTTPException(401, "需要管理员")   # 401 会让客户端以为「重新登录就行」,误导!
```

✅ **正确写法**:权限不够抛 **403**。

❌ **错误写法 2**(在 admin 端点里重新校验 token,不走嵌套依赖):

```python
@app.get("/admin/stats")
def admin_stats(x_token: str | None = Header(default=None)):
    user = TOKENS.get(x_token)   # 鉴权逻辑第 2 份拷贝;require_admin 白写了
```

✅ **正确写法**:`admin: dict = Depends(require_admin)`,链条自动串联。

> ✅ 做 `require_admin`:签名已给定(`user: dict = Depends(get_current_user)`),函数体:`role != "admin"` → 403,否则 `return user`。

---

## §16.6 注入依赖组装端点:list_orders / get_order(对应两题)🟡

依赖注入端点后,**拿到的就是普通对象**,直接用。三个依赖可以同时注入:

```python
@app.get("/orders")
def list_orders(
    pagination: Pagination = Depends(get_pagination),   # §16.4 的类依赖
    user: dict = Depends(get_current_user),             # §16.3 的鉴权依赖
    db: dict = Depends(get_db),                         # §16.2 的 yield session
):
    db["queries"] += 1                                  # 用 session(模拟查询)
    mine = [o for o in ORDERS if o["username"] == user["username"]]   # 鉴权参与业务!
    items = mine[pagination.offset : pagination.offset + pagination.size]
    return {"items": items, "total": len(mine), "page": pagination.page, "size": pagination.size}
```

### 真实场景例(种子数据手算)

种子订单 5 单:alice 有 id=1/2/5,bob 有 id=3/4。

```text
GET /orders(X-Token: tok-alice)         → total=3,items 全是 alice 的(id 1/2/5)
GET /orders?page=2&size=2(tok-alice)    → items 只有 [id=5];total 仍是 3(过滤后的总数)
GET /orders(tok-bob)                    → total=2(id 3/4)——看不到 alice 的单
GET /orders(无 token)                   → 401,端点体没执行
```

**鉴权不是摆设**:注入 `user` 后必须参与过滤,否则 bob 能看到 alice 的订单——这就是 OWASP 头号漏洞「水平越权 / IDOR」。

### get_order:404 vs 403 的分工

```python
@app.get("/orders/{order_id}")
def get_order(order_id: int, user: dict = Depends(get_current_user), db: dict = Depends(get_db)):
    db["queries"] += 1
    order = next((o for o in ORDERS if o["id"] == order_id), None)
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")       # 不存在
    if order["username"] != user["username"]:
        raise HTTPException(status_code=403, detail="无权查看他人订单") # 存在但越权
    return order
```

```text
GET /orders/1(tok-alice)   → 200
GET /orders/1(tok-bob)     → 403(订单存在,但是 alice 的)
GET /orders/99999(tok-alice)→ 404
GET /orders/1(无 token)    → 401(依赖链上游短路,端点体没执行)
```

**先 404 再 403**:不存在的订单不暴露归属;存在才谈权限。

❌ **错误写法**(注入了 user 却不过滤,或越权返回 404):

```python
return next(o for o in ORDERS if o["id"] == order_id)   # 不过滤 owner → 水平越权!
if order["username"] != user["username"]:
    raise HTTPException(404)   # 用 404 掩盖存在性是一种流派,但本章契约要求显式 403
```

✅ **正确写法**:按契约——不存在 404、越权 403,两个分支分开写。

> 🟡 **use_cache**:同一请求内,同一个依赖(同函数同参数)默认只解析一次,结果缓存复用(`Depends(f, use_cache=True)` 是默认值)。所以一个端点里两次声明 `Depends(get_current_user)` 也只查一次 token。每请求一次 DB session 也靠这个保证。

> ✅ 做 `list_orders`:`db["queries"] += 1` → 按 `user["username"]` 过滤 → `pagination.offset` 切片 → 返回四键 dict。做 `get_order`:404 守卫 → 403 守卫 → 返回。

---

## §16.7 POST + 用注入的 session 写入:create_order(对应:`create_order`)🟡

写操作同样走注入的 session——读和写共用一套 `get_db`,这正是 Ch19 接 SQLAlchemy 时的标准形态。

```python
@app.post("/orders", status_code=201)
def create_order(
    body: OrderCreate,                            # 请求体模型(Ch14):item/amount,框架自动 422
    user: dict = Depends(get_current_user),
    db: dict = Depends(get_db),
):
    global _next_order_id
    db["queries"] += 1                            # 写入也走 session
    order = {"id": _next_order_id, "username": user["username"],
             "item": body.item, "amount": body.amount, "status": "pending"}
    ORDERS.append(order)
    _next_order_id += 1
    return order
```

### 真实场景例

```text
POST /orders(tok-bob){"item": "显示器", "amount": 899}
    → 201 {"id": 6, "username": "bob", "item": "显示器", "amount": 899.0, "status": "pending"}
    → 再 GET /orders(tok-bob):total 从 2 变 3
    → alice 的列表不受影响(她的 total 仍是 3)
POST /orders 无 token           → 401(依赖短路,不会写入)
POST amount=-1                  → 422(OrderCreate 的 Field(gt=0),函数体不执行)
```

下单人是谁?**从注入的 `user` 取**,绝不信客户端传的 username——这是「服务端身份」与「客户端输入」的分界线。

❌ **错误写法**(body 里收 username,客户端说谁就是谁):

```python
class OrderCreate(BaseModel):
    username: str   # 恶意客户端可以冒充任何人下单!
```

✅ **正确写法**:`OrderCreate` 只有 `item`/`amount`;`username` 来自 `user["username"]`(依赖解析出的服务端身份)。

> ✅ 做 `create_order`:`global _next_order_id` → `db["queries"] += 1` → 造 dict → append → 自增 → 返回。装饰器已写好 `status_code=201`。

---

## §16.8 综合:admin_stats + 全局依赖(对应:`admin_stats`)🔴

最后一题把前面全部串起来:**复用 §16.5 的 `require_admin`**,给运营一个全站统计端点(所有用户的订单,不再按用户过滤——这正是 admin 的特权):

```python
@app.get("/admin/stats")
def admin_stats(admin: dict = Depends(require_admin)):
    by_status: dict[str, int] = {}
    for o in ORDERS:
        by_status[o["status"]] = by_status.get(o["status"], 0) + 1
    return {
        "total_orders": len(ORDERS),
        "total_amount": round(sum(o["amount"] for o in ORDERS), 2),
        "by_status": by_status,
    }
```

### 真实场景例(种子数据手算)

5 单:599 + 159 + 75.5 + 1299 + 89。

```text
GET /admin/stats(tok-admin)
    → {"total_orders": 5, "total_amount": 2221.5,
       "by_status": {"paid": 3, "shipped": 1, "pending": 1}}
GET /admin/stats(tok-alice)  → 403
GET /admin/stats(无 token)   → 401(链条上游短路)
```

注意参数 `admin` 在函数体里没用——**注入它就是为了它的「副作用」(鉴权)**。这是 DI 的常见用法:要的是依赖执行过程,不是返回值。

### 延伸:全局依赖与路由级依赖(了解,不出题)

```python
app = FastAPI(dependencies=[Depends(verify_api_key)])      # 全局:每个端点都先跑
router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])   # 整组路由
@app.get("/x", dependencies=[Depends(log_request)])        # 单个端点,不接收返回值
```

`dependencies=[...]` 列表里的依赖只执行、不注入参数——适合「整个 admin 分组都要管理员」这类批量挂载,等价于 Spring 里给 `/admin/**` 配一条 Security 拦截规则。本章作业用参数注入式(要拿返回值),列表式了解即可。

> ✅ 做 `admin_stats`:三键都算对;`total_amount` 用 `round(..., 2)` 防浮点尾巴;`by_status` 逐单累计。

---

## §16.9 Java 老手常踩的坑 ⚠️

1. **`Depends(f)` 不是 `Depends(f())`**——传函数本身,调用是框架的事。加了括号,注入的是「你那次调用的返回值」。
2. **yield 依赖的清理必须放 `finally`**——只写在 `yield` 后面,端点异常时清理代码执行不到。
3. **依赖默认每请求重新解析,不是单例**——这正是 DB session 想要的;同请求内同依赖有 `use_cache` 只解析一次。
4. **依赖里抛 `HTTPException` = 短路**——端点体不执行。鉴权失败 401、权限不足 403,都靠它。
5. **401 ≠ 403**:401 没认证(无/坏 token),403 已认证没权限。权限不够抛 401 会误导客户端「重新登录」。
6. **Header 参数名自动转换**:`x_token` → `X-Token`(下划线转连字符);要别名用 `Header(alias="...")`。
7. **注入了 `user` 就要用它过滤**——只鉴权不过滤 = 水平越权(IDOR)。
8. **身份只信服务端**:`username` 从注入的 `user` 取,别放进请求体让客户端自报家门。
9. **依赖函数也能声明 `Query`/`Header`/路径参数**,校验照常 422——别把解析逻辑抄进端点。

---

## §16.10 速查:四种依赖形态

| 形态 | 写法 | 用途 | 本章例子 |
|------|------|------|----------|
| 函数依赖 | `def f() -> X` + `Depends(f)` | 解析/计算并注入返回值 | `get_current_user` |
| yield 依赖 | `def f(): setup; yield x; finally: clean` | 需清理的资源(DB/文件) | `get_db` |
| 类依赖 | `def f() -> SomeClass` | 打包一组参数 | `get_pagination` → `Pagination` |
| 嵌套依赖 | `def g(x = Depends(f))` | 在已有依赖上叠加规则 | `require_admin` |

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `get_db` | yield 依赖三段式 + finally 清理 | 🔴 |
| `get_current_user` | Header 解析 + 401 短路 | 🔴 |
| `get_pagination` | 类依赖 + 依赖内 Query 校验 | 🟡 |
| `require_admin` | 嵌套依赖 + 403 | 🔴 |
| `list_orders` | 注入三依赖 + 按用户过滤 + 分页 | 🟡 |
| `get_order` | 404 vs 403 | 🟡 |
| `create_order` | POST + session 写入 + 201 | 🟡 |
| `admin_stats` | 综合:admin 依赖 + 全站统计 | 🔴 |

```bash
uv sync --extra web
uv run pytest 03_web_framework/ch16/test_ch16_assignment.py -v
```

---

## ✅ 自测

- [ ] 能说清「Depends 怎么工作:声明 → 框架调用 → 注入返回值」,以及与 Spring DI 的三个差异
- [ ] 能手写 yield 依赖三段式,并解释为什么端点 404 时 `close` 也会执行(对应 Ch06 @contextmanager)
- [ ] 能说清鉴权依赖的「短路」:依赖里 raise 401,端点体为什么不执行
- [ ] 能不查资料分清 401 / 403 / 404 的分工
- [ ] 知道为什么「注入了 user 还要按 user 过滤」(水平越权)
- [ ] 8 个作业全绿

## 🎓 费曼挑战

1. 「FastAPI 的 Depends 和 Spring @Autowired 有什么异同?为什么说它更轻?」— 重读 §16.1
2. 「yield 依赖怎么保证 DB session 一定被关闭?画出 setup/yield/teardown 三段。」— 重读 §16.2
3. 「`/admin/stats` 无 token 为什么是 401 而不是 403?`require_admin` 的依赖链是怎么解析的?」— 重读 §16.5
4. 「为什么下单接口不能把 `username` 放进请求体?」— 重读 §16.7

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步

Ch16 掌握后,进 **Ch17 · 中间件、CORS、异常处理**——给 API 加请求日志中间件(= Servlet Filter)、统一异常处理(把 `HTTPException` 之外的异常也变成结构化响应)、跨域 CORS。
