# Ch16 · 依赖注入系统(Depends)

> **预计**:1 天 ｜ **前置**:Ch15 ｜ **重点**
> **目标**:理解 FastAPI 最强大的设计——**依赖注入**(Depends,对比 Spring `@Autowired`)。把鉴权、分页、DB session 等「跨端点共享的逻辑」抽成可复用的依赖,端点声明「我需要 X」,FastAPI 自动解析注入。

> 📐 **本教程的契约**:三种依赖模式(§16.2–§16.5)都已定义好,你填端点体练习「用 Depends 注入」。

---

## 🗺️ 本章地图

**作业 ↔ 教程对应表**:

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `list_products` | §16.2 | 用 Depends 注入三种依赖 |
| `who_am_i` | §16.2 | 复用同一个依赖 |

（三种依赖的定义见 §16.3–§16.5,读代码理解模式）

---

## ⏱️ 学习路径:费曼五步(约 60-90 分钟)

① 预览猜 → ② 写端点实现 → ③ pytest 红绿 → ④ 费曼 → ⑤ 存闪卡。

---

## ① 预览猜

1. Spring 用 `@Autowired` 注入 service。FastAPI 怎么「声明我需要某个依赖」?
2. 多个端点都要鉴权,你希望鉴权逻辑只写一处。怎么做?
3. 端点需要 DB session 且用完要关闭(即使异常)。FastAPI 哪种依赖能保证清理?
4. 怎么从请求头 `X-Token` 提取值并做成依赖?

---

## §16.1 为什么需要依赖注入

问题:很多端点共享同样的「前置逻辑」——鉴权、分页解析、获取 DB session。如果每个端点都抄一遍,重复且难维护。

依赖注入的思路:**把共享逻辑写成「依赖」,端点声明「我需要它」,框架自动调用并注入结果**。

```python
@app.get("/products")
def list_products(user: str = Depends(get_current_user)):   # 声明依赖
    # user 已经是 get_current_user() 的返回值,FastAPI 自动调用注入
    return {"user": user}
```

> 🟡 **Java 对比**:= Spring `@Autowired` / 构造注入。但 FastAPI 的 Depends 更轻——不用 IoC 容器、不用 @Component 扫描,直接函数级声明。Spring 注入的是「单例 bean」,FastAPI 默认「每次请求新建」(适合 DB session 这种)。

---

## §16.2 Depends 基础(对应:`list_products`、`who_am_i`)🔴

`Depends(依赖函数)` 放在参数默认值位置。FastAPI 在调用端点前,**先调用依赖函数**,把返回值注入到参数。

```python
def get_current_user(x_token: str | None = Header(default=None)) -> str:
    # 这是个普通函数,内部还能自己声明查询参数/Header(会被 FastAPI 解析)
    if not x_token:
        raise HTTPException(401, "未授权")
    return x_token[5:]   # 返回值就是注入给端点的值

@app.get("/me")
def who_am_i(user: str = Depends(get_current_user)):   # user = get_current_user() 的返回值
    return {"user": user}
```

**三个关键点**:
1. `Depends(get_current_user)` ——声明依赖,不用调 `get_current_user()`(FastAPI 调)。
2. 依赖函数的返回值 → 注入端点参数。
3. 依赖函数自己也可以有参数(查询参数/Header),FastAPI 一并解析。
4. **同一依赖多端点复用**——鉴权逻辑写一处(`/me` 和 `/products` 都用 `get_current_user`)。

> ✅ 做 `list_products`/`who_am_i` 题:签名已给(含 Depends),直接用 `pagination`/`user`/`db`。

---

## §16.3 类依赖(本作业 `Pagination`)

依赖不只返回简单值,也能返回**对象**(把多个相关参数打包):

```python
class Pagination:
    def __init__(self, page: int = 1, size: int = 10):
        self.page = page
        self.size = size

def get_pagination(page: int = 1, size: int = 10) -> Pagination:
    return Pagination(page=page, size=size)

@app.get("/products")
def list_products(pagination: Pagination = Depends(get_pagination)):
    pagination.page    # 用打包后的对象
```

类依赖好处:把 page/size 等一组参数封装,端点签名更干净(一个 `pagination` 而非散落的 page/size)。

---

## §16.4 yield 依赖:带清理的依赖(本作业 `get_db`)🔴

DB session、文件句柄等资源要「用完关闭」。**yield 依赖** = 生成器写法(Ch06 @contextmanager 学过),保证清理:

```python
def get_db():
    session = create_session()      # ① yield 前:获取资源(setup)
    try:
        yield session               # ② yield 值:端点拿到的 session
    finally:
        session.close()             # ③ yield 后:清理(无论端点是否异常都执行)

@app.get("/products")
def list_products(db = Depends(get_db)):   # db 就是 yield 的 session
    db.query(...)    # 用 session
# 端点结束后(即使抛异常),session.close() 一定会被调
```

> 🤯 **这正是 Ch06 `@contextmanager` 的思路**(yield 切三段:setup/值/teardown)。FastAPI 把它用在依赖上,资源管理极优雅。Ch19 接 SQLAlchemy 时,`get_db` 就是真 DB session。

---

## §16.5 Header 依赖(本作业 `get_current_user`)

`Header(default=None)` 从请求头提取值(`x_token` → `X-Token`,下划线自动转连字符):

```python
from fastapi import Header

def get_current_user(x_token: str | None = Header(default=None)) -> str:
    #                    ↑ 参数名 x_token → 自动找请求头 X-Token
    if not x_token:
        raise HTTPException(401, "未授权")
    return decode_token(x_token)
```

鉴权是依赖注入的经典场景:**把 token 解析 + 校验 + 401 全包在依赖里**,端点只管用 `user`。Ch21 用 JWT 真做。

---

## §16.6 嵌套依赖(了解)

依赖可以**依赖别的依赖**(链式):

```python
def get_token(x_token: str = Header(...)): return x_token
def get_current_user(token: str = Depends(get_token)):  # 这个依赖又依赖 get_token
    return decode(token)
@app.get("/x")
def x(user: str = Depends(get_current_user)): ...       # FastAPI 自动解析整条链
```

---

## §16.7 全局依赖 vs 路由级(了解)

```python
app = FastAPI(dependencies=[Depends(verify_api_key)])    # 全局:每个端点都跑
@app.get("/x", dependencies=[Depends(log_request)])      # 路由级:只这个端点
```
全局依赖常用于「整个 app 都要鉴权」。本章不深入。

---

## §16.8 速查:三种依赖模式

| 模式 | 写法 | 用途 |
|------|------|------|
| 函数依赖 | `def f() -> X` + `Depends(f)` | 返回值注入(最常见) |
| 类依赖 | `def f() -> SomeClass` | 打包多个参数 |
| yield 依赖 | `def f(): ... yield x ...` | 需要清理的资源(DB/file) |

---

## §16.9 Java 老手常踩的坑 ⚠️

1. **`Depends(f)` 不调 f**:写 `Depends(get_current_user)`,不是 `Depends(get_current_user())`。FastAPI 负责调。
2. **yield 依赖忘加 try/finally**:清理代码放 finally,否则端点异常时清理漏执行。
3. **Header 参数名 vs 头名**:`x_token` → `X-Token`(下划线转连字符)。要别名用 `Header(alias="...")`。
4. **依赖默认每次请求新建**:不是单例(除非用 `Depends(use_cache=True)`)。DB session 就是要每请求新建。
5. **依赖抛 HTTPException 会短路**:依赖里 `raise HTTPException(401)`,端点不会执行,直接返 401。这是鉴权依赖的原理。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `list_products` | 用 3 个 Depends | 🟡 |
| `who_am_i` | 复用依赖 | 🟢 |

（读懂三种依赖定义 §16.3–§16.5 是前提）

```bash
uv run pytest 03_web_framework/ch16/test_ch16_assignment.py -v
```

---

## ✅ 自测

- [ ] 能说清「Depends 怎么工作:声明 → 框架调用 → 注入返回值」
- [ ] 能解释 yield 依赖如何保证资源清理(对应 @contextmanager)
- [ ] 知道鉴权依赖(get_current_user)为什么能在多端点复用、抛 401 如何短路
- [ ] 2 个作业全绿

## 🎓 费曼挑战

1. 「FastAPI 的 Depends 和 Spring @Autowired 有什么异同?为什么说它更轻?」— 重读 §16.1/§16.2
2. 「yield 依赖怎么保证 DB session 一定被关闭?它和 Ch06 的 @contextmanager 什么关系?」— 重读 §16.4

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步

Ch16 掌握后,进 **Ch17 · 中间件、CORS、异常处理**——给 API 加请求日志中间件(= Servlet Filter)、统一异常处理、跨域 CORS。M3 第一批(Ch13-17)收尾。
