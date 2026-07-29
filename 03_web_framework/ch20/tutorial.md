# Ch20 · 测试 API 进阶(TestClient + fixtures + 覆盖率)

> **预计**:0.5 天 ｜ **前置**:Ch16(依赖注入)、Ch17(中间件/异常)、Ch13(TestClient 基础)
> **目标**:掌握 pytest 测试 Web API 的「三件套」——**fixtures**(= `@BeforeEach` 升级)、**parametrize**(= `ParameterizedTest`)、**dependency_overrides**(= `@MockBean`)。这是后面所有 Web 测试的基础。

> 📐 **本教程的契约**:讲过的才考,考的必讲过。§20.1–§20.4 对应作业三处填空,§20.2 是 parametrize 示范(test 文件里已写完整)。

---

## 🗺️ 本章地图

**作业 ↔ 教程对应表**:

| 作业(你填) | 对应小节 | 核心知识点 | Java 对应 |
|------------|----------|-----------|-----------|
| `make_product_fixture` | §20.1 | `@pytest.fixture` + `yield`(setup/teardown) | `@BeforeEach` + `@AfterEach` |
| (parametrize 示范) | §20.2 | `@pytest.mark.parametrize` 参数化 | `@ParameterizedTest` |
| `auth_headers` | §20.3 | 构造鉴权请求头,塞给 `TestClient` | 手动塞 `HttpHeaders` |
| `override_auth` | §20.4 | `app.dependency_overrides[dep] = fake` 覆盖依赖 | `@MockBean` / `@WithMockUser` |

**本章特殊**:作业是「写测试代码」本身。被测 app(商品 CRUD + 鉴权)已完整给你,你要写的是**让测试更省力的三个工具**。

---

## ⏱️ 学习路径:费曼五步(约 45-60 分钟)

| 步 | 动作 | 预计 |
|----|------|------|
| ① 预览猜 | 回答下方 4 个激发 Java 直觉的问题 | 5 min |
| ② 先动手 | 填三处 `...`(make_product_fixture / auth_headers / override_auth) | 20 min |
| ③ pytest 红绿 | `uv run pytest 03_web_framework/ch20/ -v` 从红到绿 | 10 min |
| ④ 费曼 | 不看教程,讲清「fixture 的 yield 为何比 @BeforeEach 强」 | 10 min |
| ⑤ 存闪卡 | 把 7 张闪卡过一遍,登记复习日期 | 5 min |

---

## ① 预览猜

1. Spring 里 `@BeforeEach`/`@AfterEach` 拆成两个方法。pytest 有没有「一个方法搞定 setup+teardown」的写法?
2. JUnit 5 的 `@ParameterizedTest` 让一组数据跑 N 次同一个 test。pytest 怎么写?
3. Spring Test 用 `@MockBean` 把真实 Bean 换成 mock。FastAPI 的 `Depends` 怎么在测试时被「替换」掉?
4. 你要测一个**需要登录**的端点,但不想真去解 JWT。最小代价是什么?

---

## §20.1 fixture:带 setup/teardown 的测试准备函数(对应:`make_product_fixture`)🟡

**fixture** = pytest 里「为测试准备数据/状态,并在测试后清理」的函数。你可以把它当成「**升级版的 @BeforeEach + @AfterEach 合体**」。

最简 fixture(只准备,不清理):

```python
import pytest

@pytest.fixture
def sample_product():
    return {"id": 1, "name": "键盘", "price": 599}
```

测试函数**把 fixture 名当参数**,pytest 自动注入:

```python
def test_name(sample_product):          # 名字匹配 → 自动注入
    assert sample_product["name"] == "键盘"
```

> 🟢 **Java 对比**:= `@BeforeEach`。区别:pytest fixture 是**按参数名注入**的(声明式),不用继承基类、不用注解字段。Java 是「方法级」,fixture 是「依赖级」。

### setup + teardown:用 `yield`(关键)

`yield` 把函数切成两半——**yield 之前 = setup,yield 之后 = teardown**。这是比 `@BeforeEach`+`@AfterEach` 优雅的地方:一个函数,前后呼应,不用拆两个方法:

```python
@pytest.fixture
def db_session():
    session = open_db()          # —— setup(@BeforeEach 的活)——
    yield session                # 把值交给测试;测试结束后从这里继续
    session.close()              # —— teardown(@AfterEach 的活)——
```

> 🔴 **Python 特有**:`yield` 不是 `return`。`yield` 后的代码**在测试结束后**才执行。这是「生成器」语义——fixture 本质是个「生成一次值的生成器」。用 `return` 写 teardown 代码**永远不会执行**。

### fixture 的作用域(scope)

```python
@pytest.fixture(scope="function")  # 默认:每个测试函数都跑一次 setup+teardown
@pytest.fixture(scope="module")    # 整个 .py 文件只跑一次
@pytest.fixture(scope="session")   # 整个 pytest 进程只跑一次
```

测 Web API 时默认 `function` 就够(每个 test 独立干净状态)。连真 DB 时常用 `session`(建表一次)+ `function`(每个 test 开事务回滚)。

### 本章作业的「fixture 工厂」

你的 `make_product_fixture()` 不是 fixture 本身,而是**返回一个 fixture 函数**。这是「工厂模式」——因为 fixture 必须在模块顶层用名字注册,test 文件才认得它:

```python
# assignment 里(你写)
def make_product_fixture():
    @pytest.fixture
    def _products_fixture():
        PRODUCTS.update({1: Product(...), ...})   # setup
        yield list(PRODUCTS.values())             # 交给测试
        PRODUCTS.clear()                          # teardown
    return _products_fixture                      # 返回函数本身(不是调用)

# test 文件里(已写好)
products_fixture = make_product_fixture()         # 在模块顶层「注册」
def test_xxx(self, products_fixture):             # 名字匹配 → pytest 注入
    ...
```

> ✅ 做 `make_product_fixture` 题:`@pytest.fixture` 装饰 + `PRODUCTS.update(...)` setup + `yield` + `PRODUCTS.clear()` teardown + `return _products_fixture`。

---

## §20.2 参数化:`@pytest.mark.parametrize`(对应:test 文件示范)🟢

同一个测试逻辑想跑 N 组数据。Java 用 `@ParameterizedTest` + `@CsvSource`,pytest 用 `@pytest.mark.parametrize`:

```python
@pytest.mark.parametrize(
    "price, should_pass",                       # 参数名(逗号分隔的字符串)
    [                                           # 数据列表
        (0.01, True),
        (99.99, True),
        (0, False),
        (-1.0, False),
    ],
)
def test_price_validation(self, price, should_pass, products_fixture):
    # pytest 会把每行数据展开成一个独立测试:test_price_validation[0.01-True] 等
    ...
```

test 文件里 `TestPriceBoundary::test_price_validation` 就是完整示范,会生成 5 个测试用例(看 pytest 输出 ID `[0.01-True]`、`[-1.0-False]`…)。

> 🟢 **Java 对比**:= JUnit 5 `@ParameterizedTest` + `@MethodSource`/`@CsvSource`。pytest 的 ID 自动用参数值拼。

> ⚠️ parametrize 的「参数名」是**字符串**(不是变量),这是新手坑。写成 `@pytest.mark.parametrize(price, should_pass, [...])`(没引号)会报错。

### parametrize vs 多个 test:何时用?

- **边界值/等价类**(价格 0/负数/正常)→ parametrize,一组数据一行。
- **完全不同的逻辑**(测登录、测下单、测退款)→ 拆成多个 test 函数,别硬塞 parametrize。

---

## §20.3 构造鉴权请求头(对应:`auth_headers`)🟢

带鉴权的端点(`POST/PUT/DELETE` 都 `Depends(get_current_user)`)需要 `Authorization: Bearer <token>` 头。`TestClient` 用 `headers=` 传:

```python
client.post("/products", json={...}, headers={"Authorization": "Bearer testuser"})
```

每次手写这串头太啰嗦。封装一个小函数,测试里 `headers=auth_headers("testuser")` 一行搞定:

```python
def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
```

> 🟢 **Java 对比**:= `RestTemplate`/`MockMvc` 测试时手动 `HttpHeaders headers = new HttpHeaders(); headers.set("Authorization", "Bearer " + token);`。Python 一个 dict 就行,不用 HttpHeaders 对象。

> ✅ 做 `auth_headers` 题:返回 `{"Authorization": f"Bearer {token}"}`。一行。

---

## §20.4 依赖覆盖:`app.dependency_overrides`(对应:`override_auth`)🔴

**本章最重要的 API**。`get_current_user` 真实实现要解 JWT、查 DB、验过期……测业务端点时你**根本不想**碰这些。用 `dependency_overrides` 把它整个替换掉:

```python
app.dependency_overrides[get_current_user] = lambda: "testuser"
#                       ^^^^^^^^^^^^^^^^^^^     ^^^^^^^^^^^^^^^^^^^
#                       要替换的真实依赖         替换成的假函数(返回固定用户)
```

替换后,所有 `Depends(get_current_user)` 都不再走真实逻辑,直接拿到 `"testuser"`。= 你「mock」掉了鉴权。

> 🤯 **Java 对比**:= Spring Test 的 **`@MockBean`** 把 Bean 换成 Mockito mock;也像 Spring Security 的 **`@WithMockUser("testuser")`** 跳过鉴权。FastAPI 这套更轻——一个字典赋值搞定,不用 Mockito 框架。

### 替换函数的签名约定

替换函数**没有参数**(或只声明子依赖),返回值要**兼容**原依赖的返回类型。`get_current_user -> str`,所以 lambda 返回 str。

### 测试结束必须还原(关键!)

`dependency_overrides` 是 `app` 上的**全局可变状态**。不清掉会**污染下一个测试**(鉴权一直被绕过)。还原方式:

```python
# 方式 1:try/finally(本作业用的)
override_auth(app)
try:
    ...测试...
finally:
    app.dependency_overrides.clear()    # 或 pop(get_current_user)

# 方式 2:monkeypatch fixture(自动还原,更优雅)
def test_xxx(monkeypatch):
    monkeypatch.setitem(app.dependency_overrides, get_current_user, lambda: "u")
    # 测试结束 monkeypatch 自动还原
```

> ✅ 做 `override_auth` 题:`test_app.dependency_overrides[get_current_user] = lambda: username`。一行。**注意键是函数对象本身**(`get_current_user`),不是字符串。

### 三种「测鉴权端点」的方式对比

| 方式 | 做法 | 适用场景 |
|------|------|----------|
| §20.3 `auth_headers` | 真带一个合法 token | 测「鉴权通过后的业务逻辑」+ 顺带验鉴权 |
| §20.4 `dependency_overrides` | 整个替换依赖,跳过鉴权 | 只关心业务逻辑,鉴权单测(不混进来) |
| 两个都测 | 一组带合法头、一组不带 | 测「401 是否正确返回」(鉴权本身的测试) |

---

## §20.5 测试 DB 隔离(进阶,了解)

本项目用内存 `dict`(PRODUCTS)存储,fixture 用 `clear()` 就能隔离。连真 DB 时,隔离手段升级:

- **每个测试一个事务,结束回滚**(transaction rollback):setup 开 `BEGIN`,teardown `ROLLBACK`,数据不落地。这是最快的方式。
- **每个测试一个独立 schema/数据库**(SQLite in-memory 或 testcontainers):彻底隔离,但慢。
- **Truncate 表**(慢,生产慎用):每个测试前清空所有表。

FastAPI 的 `get_db` 依赖也能用 `dependency_overrides` 替换成测试 session——和 §20.4 一模一样的套路。本章用内存 dict,先掌握思想,Ch19/Ch21 连真 DB 时再实战。

---

## §20.6 覆盖率:`pytest-cov`

```bash
uv run pytest 03_web_framework/ch20/ --cov=ch20_assignment --cov-report=term-missing
```

输出每个文件的语句数、覆盖数、未覆盖行号。目标:核心业务逻辑 90%+。本作业完整实现跑出来约 **92%**。

> ⚠️ 覆盖率**只看行没看逻辑**。100% 覆盖率 ≠ 没 bug(可能你的 assert 根本没断言关键值)。把覆盖率当「下限」(低于 70% 报警),不当「目标」。

`--cov-report=html` 生成可点击的 HTML 报告(`htmlcov/index.html`),红行=没跑到,直观。

---

## §20.7 Java 老手常踩的坑 ⚠️

1. **fixture 用 `return` 写 teardown**:`yield` 后的代码才是 teardown,`return` 后的代码**永远不执行**。🔴
2. **fixture 名 vs 参数名不匹配**:pytest 靠**名字**注入。fixture 叫 `products_fixture`,测试参数也得叫 `products_fixture`,差一个字母就注入失败(`fixture not found`)。
3. **fixture 注册位置**:fixture 必须在**模块顶层**赋值(如 `products_fixture = make_product_fixture()`),写在 test 函数里 pytest 发现不了。本章用「工厂」就是因为这点。
4. **`dependency_overrides` 不还原**:全局可变状态泄漏到下个测试,鉴权被静默绕过。一定 `try/finally` 或 `monkeypatch`。🔴
5. **覆盖键用字符串**:`dependency_overrides["get_current_user"]` ❌。键是**函数对象**:`dependency_overrides[get_current_user]` ✅。
6. **parametrize 参数名忘加引号**:`@pytest.mark.parametrize(a, b, [...])` 报错。要写 `"a, b"`(字符串)。
7. **TestClient 的 `app` 是单例**:多个 test 共用同一个 `app`,`dependency_overrides`、全局 `PRODUCTS` 都会串。靠 fixture teardown 清理。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `make_product_fixture` | `@pytest.fixture` + `yield`(setup/teardown) | 🟡 |
| `auth_headers` | 构造鉴权请求头 | 🟢 |
| `override_auth` | `app.dependency_overrides` 依赖覆盖 | 🟡 |

```bash
# 跑测试
uv run pytest 03_web_framework/ch20/ -v

# 看覆盖率
uv run pytest 03_web_framework/ch20/ --cov=ch20_assignment --cov-report=term-missing
```

填完后应从「17 failed」变「19 passed」。

---

## ✅ 自测清单

- [ ] 能说清 fixture 的 `yield` 为何比 `@BeforeEach`+`@AfterEach` 优雅
- [ ] 能用 `@pytest.mark.parametrize` 把一组边界数据跑成一个测试
- [ ] 能用 `app.dependency_overrides[dep] = fake` 绕过鉴权,并知道结束后要还原
- [ ] 知道 `auth_headers`(真带 token)和 `override_auth`(替换依赖)的取舍
- [ ] 3 个作业全绿,覆盖率 ≥ 90%

---

## 🎓 费曼挑战

1. 「为什么 fixture 必须用 `yield` 而不是 `return`?如果用 `return`,teardown 会怎样?」— 卡壳重读 §20.1
2. 「`dependency_overrides` 为什么键必须是函数对象?替换函数为什么要返回和原依赖兼容的类型?」— 卡壳重读 §20.4
3. 「测一个需鉴权的端点,`auth_headers` 和 `override_auth` 各解决什么不同的问题?什么场景用哪个?」— 卡壳重读 §20.4 末尾对照表

---

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步

Ch20 学完,你掌握了**测 Web API 的三件套**(fixture / parametrize / dependency_overrides)。后面:

- **Ch21** JWT 认证授权——本章的 `get_current_user` 会换成真 JWT 解析,然后你**反过来用 §20.4** 把它 mock 掉测业务。
- **Ch22** 部署——CI 里跑 `pytest --cov`,覆盖率卡门槛。

fixture + dependency_overrides 是后面所有集成测试的地基,务必练熟。
