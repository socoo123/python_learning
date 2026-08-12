# Ch20 · 测试 API 进阶(TestClient + fixtures + 覆盖率)

> **预计**:0.5 天 ｜ **前置**:Ch14(Pydantic `Field` 校验、TestClient 初见)、Ch16(Depends 依赖注入)、Ch06(pytest 基础)
> **目标**:能给一套真实 API 搭出**可维护的 pytest 测试套件**——fixture 管数据与客户端、parametrize 打边界、`dependency_overrides` 绕过鉴权、覆盖率验收。这是后面所有 Web 测试的地基。
> 本章主线:你是「极客商城」新接盘的后端。离职的前同事留下一套**能跑但零测试**的商品 CRUD API(内存存储 + Bearer 鉴权 + Pydantic 校验)。老板的规定:合并新代码前,测试套件必须全绿、核心逻辑覆盖率 ≥ 90%。你的任务:为这套 API 从零搭测试。

> 📐 **本教程的契约**:讲过的才考,考的必讲过。§20.1–§20.4 对应 7 个作业函数;§20.5 起是示范与进阶,不出题。卡住时按对应表回查小节。

---

## 🗺️ 本章地图

读完这章 + 完成作业,你将能够:
- 用 `@pytest.fixture` + `yield` 一个函数搞定 setup/teardown,讲清为何优于 `@BeforeEach`+`@AfterEach` 拆分
- 用 fixture 管理两类资源——「测试数据」和「TestClient」——并**清理全局可变状态**(PRODUCTS、dependency_overrides)
- 用 `app.dependency_overrides` 把鉴权依赖整个换成假实现(= Spring `@MockBean`),并知道**用完必须还原**
- 用 **fixture 组合**拼出「已登录管理员客户端」(`admin_client` ← `api_client`)
- 用 `@pytest.mark.parametrize` + **数据源函数**(= JUnit `@MethodSource`)打边界值
- 用 `pytest.raises` 绕过 HTTP 直接单测依赖函数;用 `pytest-cov` 出覆盖率报告

**作业 ↔ 教程对应表**(学哪节,就去做哪题):

| 作业题 | 对应小节 | 核心知识点 | Java 对应 |
|--------|----------|-----------|-----------|
| `auth_headers` | §20.1 | 构造 Bearer 请求头喂给 TestClient | 手动塞 `HttpHeaders` |
| `products_fixture` | §20.2 | `@pytest.fixture` + `yield`(setup/teardown) | `@BeforeEach`+`@AfterEach` 合体 |
| `api_client` | §20.2 | fixture 管理 TestClient + 清全局状态 | MockMvc + `@AfterEach` 清理 |
| `override_auth` | §20.3 | `app.dependency_overrides[dep] = fake` | `@MockBean` / `@WithMockUser` |
| `admin_client` | §20.3 | **fixture 组合**(复用 api_client + override_auth) | 自定义测试切片注解 |
| `price_validation_cases` | §20.4 | parametrize 数据源函数(价格边界 → 422) | `@MethodSource` |
| `not_found_id_cases` | §20.4 | parametrize 数据源(404 边界) | `@MethodSource` |

**脚手架**(完整给出,不用填):商品 CRUD 五个端点、`get_current_user` 鉴权依赖、`Product` 模型(`Field(gt=0)` 校验)、`SEED_PRODUCTS` 种子数据。§20.5 的 `TestGetCurrentUserDirect` 是完整示范,也不用填。

---

## ⏱️ 学习路径:费曼五步(约 50-70 分钟)

| 步 | 动作 | 预计 |
|----|------|------|
| ① 预览猜 | 回答下方 4 个激发 Java 直觉的问题 | 5 min |
| ② 先动手 | 打开 `ch20_assignment.py`,按顺序填 7 个函数(别通读教程) | 25 min |
| ③ pytest 红绿 | `uv run pytest 03_web_framework/ch20/test_ch20_assignment.py -v` 从红到绿 | 15 min |
| ④ 费曼 | 不看教程,讲清「yield 为何优于 @BeforeEach」「override 为何要还原」 | 10 min |
| ⑤ 存闪卡 | 把 [`review.md`](./review.md) 的卡过一遍,登记复习日期 | 5 min |

> 💡 **直接性原则**:先猜 ① → 去 ② 写作业 → 哪题卡了,回对应 § 查 → 改 → 再跑。

---

## ① 预览猜

先别看答案,凭 15 年 Java 测试经验猜:

1. Spring 里 `@BeforeEach`/`@AfterEach` 拆成两个方法。pytest 有没有「一个函数搞定 setup+teardown」的写法?靠什么语法?
2. JUnit 5 的 `@MethodSource` 让一个普通方法提供参数化数据。pytest 的 `@pytest.mark.parametrize` 的数据能来自函数吗?
3. Spring Test 用 `@MockBean` 把真实 Bean 换成 mock。FastAPI 的 `Depends(get_current_user)` 怎么在测试时被「替换」掉?
4. 测试改了你 app 的**模块级全局存储**(`PRODUCTS` dict)和 `app.dependency_overrides`,下一个测试会受影响吗?怎么防?

> 猜完带着验证心态进正文。第 3、4 题是本章最高频的实战价值点。

---

## §20.1 测试心智 + 鉴权请求头(对应:`auth_headers`)🟢

本章特殊:**你写的是测试代码,不是业务实现**。被测 app 已完整给出,你的作业是给它搭「测试工具箱」。第一箱工具:鉴权请求头。

app 里 POST/PUT/DELETE 都 `Depends(get_current_user)`,它要求请求头形如 `Authorization: Bearer <token>`。`TestClient`(Ch14 见过,基于 httpx,不用起服务)用 `headers=` 传:

### Java 对照最小例

```java
// MockMvc:手动拼头
mockMvc.perform(post("/products")
        .header("Authorization", "Bearer " + token)
        .content(json))
```

```python
# TestClient:headers 就是一个 dict
client.post("/products", json=payload, headers={"Authorization": "Bearer alice"})   # 201
```

每个测试都手写这串 dict 太啰嗦,封装成一行函数:

```python
def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

client.post("/products", json=payload, headers=auth_headers("alice"))   # 201
```

> 🟢 **Java 对比**:= `HttpHeaders headers = new HttpHeaders(); headers.setBearerAuth(token);`。Python 里 headers 就是个 dict,不用专门的 HttpHeaders 对象。

### 真实场景例:测鉴权本身(负路径)也是工作的一部分

```python
client.post("/products", json=payload)                                   # 401 缺头
client.post("/products", json=payload, headers={"Authorization": "Basic alice"})  # 401 scheme 错
client.post("/products", json=payload, headers=auth_headers("alice"))     # 201 放行
```

### ❌ → ✅ 对照

❌ **错误写法**(f-string 之外手拼,漏了空格):

```python
{"Authorization": "Bearer" + token}     # "Beareralice" → 401,排查半天
```

✅ **正确写法**:`{"Authorization": f"Bearer {token}"}`——f-string 模板里空格看得见。

> ✅ 做 `auth_headers`:一行返回 `{"Authorization": f"Bearer {token}"}`。热身题,重点是后面的 fixture。

---

## §20.2 fixture:一个函数搞定 setup+teardown(对应:`products_fixture` / `api_client`)🔴

### Java 对照最小例

```java
@BeforeEach
void setUp() { products.save(键盘); products.save(鼠标); products.save(书); }
@AfterEach
void tearDown() { products.deleteAll(); }
```

pytest 的 **fixture** 把两件事合进**一个函数**,用 `yield` 切成两半——yield 之前 = setup,yield 之后 = teardown:

```python
import pytest

@pytest.fixture
def products_fixture():
    PRODUCTS.update({p.id: p for p in SEED_PRODUCTS})   # —— setup(@BeforeEach 的活)——
    yield list(PRODUCTS.values())                        # 把值交给测试
    PRODUCTS.clear()                                     # —— teardown(@AfterEach 的活)——
```

测试函数**把 fixture 名当参数**,pytest 自动注入(声明式,不用继承基类、不用注解字段):

```python
def test_seeds_three_products(products_fixture):   # 参数名 = fixture 名 → 注入
    assert len(products_fixture) == 3               # 拿到的是 yield 出来的值
```

> 🔴 **Python 特有**:`yield` 不是 `return`。函数执行到 `yield` **暂停**、把值给测试;**测试结束后**从 yield 下一行继续跑 teardown。fixture 本质是「只生成一次值的生成器」(Ch03 的生成器在这里发光)。

### ❌ → ✅ 对照:teardown 写在 return 后面(永不执行)

❌ **错误写法**:

```python
@pytest.fixture
def products_fixture():
    PRODUCTS.update({p.id: p for p in SEED_PRODUCTS})
    return list(PRODUCTS.values())
    PRODUCTS.clear()      # return 之后 → 死代码,永不执行 → 数据泄漏到下个测试
```

✅ **正确写法**:用 `yield`,teardown 写在 yield 后。

### 真实场景例:fixture 管理 TestClient 与全局状态

本章第二件资源是 **TestClient + 全局状态**。`app` 是模块级单例,`app.dependency_overrides` 是它身上的全局可变 dict——一个测试往里塞了 mock 不清掉,**下一个测试的鉴权就被静默绕过**(最阴的测试 bug:单独跑绿、一起跑红)。用 fixture 把清理绑在资源上:

```python
@pytest.fixture
def api_client():
    client = TestClient(app)          # setup:造客户端
    yield client
    app.dependency_overrides.clear()  # teardown:清掉本测试塞的所有依赖覆盖
```

> 🟡 **这就是 fixture 比 @BeforeEach 强的地方**:资源跟着 fixture 走,测试在参数里「点菜」——要数据就声明 `products_fixture`,要客户端就声明 `api_client`,不声明就干干净净。Java 是「类级 setup 全员共享」,pytest 是「按需注入」。

### fixture 放哪:本章的接线方式

真实项目 fixture 写在 `conftest.py`(pytest 自动发现)。本章为了「作业在 assignment、测试在 test 文件」的五件套结构,fixture 定义在 `ch20_assignment.py` 里,test 文件 `from ch20_assignment import products_fixture` 导入——**fixture 只要出现在 test 模块的命名空间(定义的或导入的),pytest 就能发现**。

### fixture 作用域速查

| scope | 执行频率 | Java 类比 |
|-------|----------|-----------|
| `function`(默认) | 每个测试函数 setup+teardown 各一次 | `@BeforeEach` |
| `module` | 每个 .py 文件一次 | `@BeforeAll` |
| `session` | 整个 pytest 进程一次 | 全局一次(如建表) |

测 Web API 默认 `function`:每个测试独立干净状态。连真 DB 常见组合:session 级建表 + function 级事务回滚(§20.6)。

> ✅ 做 `products_fixture`:`@pytest.fixture` 装饰 → `PRODUCTS.update({p.id: p for p in SEED_PRODUCTS})` → `yield list(PRODUCTS.values())` → `PRODUCTS.clear()`。
> ✅ 做 `api_client`:`yield TestClient(app)` → teardown `app.dependency_overrides.clear()`。
> 测试会用「故意污染 → 下一个测试验证已清理」来检查你的 teardown 写没写。

---

## §20.3 依赖覆盖 + fixture 组合(对应:`override_auth` / `admin_client`)🔴

### dependency_overrides:把依赖整个换掉

`get_current_user` 的真实实现要解 JWT、查 DB、验过期(Ch21 的活)。测「创建商品」时你**根本不想**碰鉴权——用 `app.dependency_overrides` 把它整个换成假实现:

```python
app.dependency_overrides[get_current_user] = lambda: "admin"
#                       ^^^^^^^^^^^^^^^^^^^     ^^^^^^^^^^^^^^^^
#                       键:要替换的【函数对象】   值:返回固定用户的零参可调用
```

之后所有 `Depends(get_current_user)` 直接拿到 `"admin"`,不再校验请求头。

> 🤯 **Java 对比**:= Spring Test 的 **`@MockBean`**(把 Bean 换成 mock)+ Spring Security 的 **`@WithMockUser("admin")`**(跳过鉴权)。FastAPI 这套更轻——一次字典赋值搞定,不用 Mockito。

### ❌ → ✅ 对照:键用字符串(静默无效!)

❌ **错误写法**:

```python
app.dependency_overrides["get_current_user"] = lambda: "admin"   # ❌ 不报错,但也不生效!
```

✅ **正确写法**:`app.dependency_overrides[get_current_user] = lambda: "admin"`——键是**函数对象本身**。

### 用完必须还原(全局可变状态)

`dependency_overrides` 是 app 上的全局 dict,塞了不清 → 下个测试鉴权还被绕过。三种还原料:

```python
# 1. try/finally 手动清(直白,适合一次性脚本)
override_auth(app)
try:
    ...测试...
finally:
    app.dependency_overrides.clear()

# 2. 交给 fixture teardown —— 本章推荐,§20.2 的 api_client 就是这么干的
# 3. monkeypatch fixture(自动还原,了解即可)
def test_xxx(monkeypatch):
    monkeypatch.setitem(app.dependency_overrides, get_current_user, lambda: "u")
```

### 真实场景例:fixture 组合出「管理员客户端」(本章综合)

测试套件里 90% 的用例是「**已登录用户干业务**」。把 §20.2 的 `api_client` 和上面的 override 拼起来,一次声明、直接可用:

```python
@pytest.fixture
def admin_client(api_client):                # ← 参数是另一个 fixture:fixture 组合
    override_auth(app, username="admin")     # 复用你写的 override_auth
    yield api_client
    # 清理不用写:下层 api_client 的 teardown 会自动清掉 override
```

测试里一句话拿到「免鉴权客户端」,还能和别的 fixture 随意叠加:

```python
def test_create_product(admin_client, products_fixture):   # 免鉴权 + 已播种
    resp = admin_client.post("/products",
                             json={"id": 9, "name": "鼠标垫", "price": 29.9, "stock": 50})
    assert resp.status_code == 201
```

> 🤯 **Java 对比**:≈ 自定义测试切片注解(`@WithMockUser` + `@AutoConfigureMockMvc` 的组合)。pytest 用「fixture 依赖 fixture」表达组合,不用元注解。**组合时清理职责放在最下层 fixture**——admin_client 不用写 teardown。

> ✅ 做 `override_auth`:`test_app.dependency_overrides[get_current_user] = lambda: username`(一行;键是函数对象)。
> ✅ 做 `admin_client`:参数声明 `api_client` → 调 `override_auth(app, username="admin")` → `yield api_client`。

---

## §20.4 参数化:parametrize + 数据源函数(对应:`price_validation_cases` / `not_found_id_cases`)🟡

### Java 对照最小例

JUnit 5 打边界值:

```java
@ParameterizedTest
@MethodSource("priceCases")
void testPrice(double price, int expectedStatus) { ... }

static Stream<Arguments> priceCases() {
    return Stream.of(Arguments.of(0.01, 201), Arguments.of(0, 422), Arguments.of(-1.0, 422));
}
```

pytest 对应物——`@pytest.mark.parametrize`,数据可以写在装饰器里,**也可以来自一个普通函数**(和 `@MethodSource` 一模一样的思路):

```python
# assignment 里(你写):数据源函数
def price_validation_cases() -> list[tuple[float, int]]:
    return [
        (0.01, 201),      # 最小合法价
        (599.0, 201),     # 正常价
        (0.0, 422),       # 0 违反 Field(gt=0) → 422
        (-1.0, 422),      # 负价 → 422
    ]

# test 文件里(已接好):装饰器直接吃函数返回值
@pytest.mark.parametrize("price, expected_status", price_validation_cases())
def test_price_boundary(self, price, expected_status, admin_client, products_fixture):
    resp = admin_client.post("/products",
                             json={"id": 99, "name": "边界商品", "price": price, "stock": 5})
    assert resp.status_code == expected_status
```

每组数据展开成一个独立测试,pytest 输出里能看到 `test_price_boundary[0.01-201]` 这样的 ID——哪组挂了,ID 直接告诉你数据。

> 🟢 **为什么非法价格能断言 422**:脚手架的 `Product` 用了 Ch14 的 `price: float = Field(gt=0)`、`stock: int = Field(ge=0)`(= Bean Validation 的 `@Positive`)。Pydantic 校验失败 → FastAPI 自动 422。**这就是「校验约束 + 参数化边界」的连击**:没有约束时,非法数据只能断言「201 或 422」(等于没断言);加上约束,边界测试才有硬预期。校验要写在模型里,别在端点里手写 if。

### ❌ → ✅ 对照:parametrize 两个新手坑

❌ **错误写法 1**(参数名忘加引号):

```python
@pytest.mark.parametrize(price, expected_status, [...])   # NameError:price 未定义
```

✅ 参数名必须是**逗号分隔的字符串**:`"price, expected_status"`。

❌ **错误写法 2**(参数个数对不上):参数名 2 个、数据行给 3 元组 → 收集期报错。每行「格子数」= 参数名个数。

### 真实场景例:404 边界,一个数据源喂三个端点

运营问:「删不存在的商品返回什么?」——答:404。把「确定不存在的 id」集中成一个数据源,GET/PUT/DELETE 复用:

```python
def not_found_id_cases() -> list[int]:
    return [999, -1, 123456]     # 都不在种子数据 {1, 2, 3} 里

@pytest.mark.parametrize("pid", not_found_id_cases())
def test_delete_unknown_returns_404(self, pid, admin_client, products_fixture):
    assert admin_client.delete(f"/products/{pid}").status_code == 404
```

3 个 id × 3 个端点 = 9 个边界测试,数据只在一处维护。

> ✅ 做 `price_validation_cases`:返回 ≥2 组合法价(201)+ ≥1 组 0 或负价(422)。做 `not_found_id_cases`:返回 ≥2 个**确实不在种子里**的 int id。测试里有「防蒙对」元测试:只返回 happy path、或返回已存在的 id,都过不了。

---

## §20.5 示范:pytest.raises 直接单测依赖函数(不出题)🟢

依赖函数本身也是代码,可以**绕过 HTTP 直接单测**。test 文件里的 `TestGetCurrentUserDirect` 是完整示范:

```python
def test_missing_header_raises_401(self):
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(None)
    assert exc_info.value.status_code == 401
```

`pytest.raises(Exc)` = JUnit 的 `assertThrows`;`exc_info.value` 拿到异常对象继续断言。**单元测依赖 + 集成测端点,两层都要有**:依赖逻辑的边界(空 token、错 scheme)用单元测试打,端点的状态码用 TestClient 打。

---

## §20.6 测试数据隔离:连真 DB 时怎么办(了解)🟡

本章 `PRODUCTS` 是内存 dict,fixture 里 `clear()` 就够隔离。连真 DB(Ch19)时手段升级:

| 手段 | 做法 | 代价 |
|------|------|------|
| 事务回滚 | setup `BEGIN` / teardown `ROLLBACK` | 最快,首选 |
| 独立测试库 | SQLite 内存库 / testcontainers 起一次性 PG | 彻底但慢 |
| truncate 表 | 每个测试前清空所有表 | 慢,兜底 |

`get_db` 依赖照样用 `dependency_overrides` 换成测试 session——§20.3 的套路原样复用。思想不变:**每个测试从已知状态开始,结束不留痕迹**。

---

## §20.7 覆盖率:pytest-cov(验收工具)🟢

```bash
# 终端报告:列出未覆盖的行号
uv run pytest 03_web_framework/ch20/test_ch20_assignment.py --cov=ch20_assignment --cov-report=term-missing

# HTML 报告:htmlcov/index.html 可点开,红行 = 没跑到
uv run pytest 03_web_framework/ch20/test_ch20_assignment.py --cov=ch20_assignment --cov-report=html
```

> ⚠️ **覆盖率是下限,不是目标**:100% 行覆盖 ≠ 没 bug(断言可能没断在关键值上——比如旧版价格测试的 `in (201, 422)`)。把覆盖率当门禁(低于 90% 报警),别当奖杯。本章全绿后,被测代码覆盖率应达 **98%**(65 语句仅 1 行未覆盖)。

---

## §20.8 Java 老手常踩的坑 ⚠️

1. **teardown 写在 `return` 后** → 永不执行;fixture 必须用 `yield`。🔴
2. **fixture 名与测试参数名差一个字母** → `fixture 'xxx' not found`。pytest 按**名字**注入。
3. **`dependency_overrides` 键用字符串** → 不报错但也不生效(静默无效)。键是**函数对象**。🔴
4. **塞了 override 不还原** → 下个测试鉴权被静默绕过。让 `api_client` 的 teardown 兜底。
5. **parametrize 参数名不加引号 / 格子数不匹配** → NameError 或收集期报错。
6. **全局 `PRODUCTS` 不清理** → 测试顺序相关(单跑绿、全跑红)。数据归 `products_fixture` 管。
7. **以为 TestClient 每次是新 app** → 不是,测的是同一个模块级单例,所有全局状态都靠 fixture 隔离。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `auth_headers` | 构造 Bearer 头 | 🟢 |
| `products_fixture` | `@pytest.fixture` + `yield` + teardown | 🔴 |
| `api_client` | fixture 管客户端 + 清全局状态 | 🟡 |
| `override_auth` | `dependency_overrides`(键是函数对象) | 🟡 |
| `admin_client` | **fixture 组合**(综合) | 🔴 |
| `price_validation_cases` | parametrize 数据源 + 422 硬断言 | 🟡 |
| `not_found_id_cases` | parametrize 数据源 + 404 | 🟢 |

```bash
uv sync --extra web
uv run pytest 03_web_framework/ch20/test_ch20_assignment.py -v
uv run pytest 03_web_framework/ch20/test_ch20_assignment.py --cov=ch20_assignment --cov-report=term-missing
```

期望:42 个测试全绿(骨架期是「22 failed + 4 skipped」;parametrize 数据源没写时,参数化用例先按 skip 处理,由元测试判红)。其中 `TestApiClient` 用「故意污染 → 下个测试验证」确认你的 teardown 真的写了。

---

## ✅ 自测清单

- [ ] 能写 `@pytest.fixture` + `yield` 的 setup/teardown,并说清为何优于 `@BeforeEach` 拆分
- [ ] 知道 fixture 按「参数名」注入;定义或导入进 test 模块命名空间即可被发现
- [ ] 能用 `dependency_overrides` 绕过鉴权(键是函数对象),并知道用完必须还原
- [ ] 能用 fixture 组合(`admin_client` ← `api_client`)拼「已登录客户端」,清理职责放下层
- [ ] 能用 parametrize + 数据源函数打边界,数据与硬断言一一对应
- [ ] 知道 `pytest.raises` 单测依赖函数、TestClient 集成测端点的分层
- [ ] 42 个测试全绿,覆盖率 ≥ 90%

---

## 🎓 费曼挑战

1. **「fixture 为什么用 `yield` 不用 `return`?用 `return` 的话 teardown 会怎样?」**— 卡壳重读 §20.2
2. **「`dependency_overrides` 的键为什么是函数对象?为什么用完必须还原?」**— 卡壳重读 §20.3
3. **「`admin_client` 组合了哪两个东西?清理职责为什么放在 `api_client` 层?」**— 卡壳重读 §20.3
4. **「parametrize 的数据从函数返回有什么好处?和 JUnit `@MethodSource` 怎么对?为什么非法价格必须配 `Field(gt=0)` 才能硬断言 422?」**— 卡壳重读 §20.4

---

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步

Ch20 学完,你握住了**测 Web API 的三件套**:fixture / parametrize / dependency_overrides。后面:

- **Ch21** JWT 认证授权——`get_current_user` 会换成真 JWT 解析,然后你**反过来用 §20.3** 把它 mock 掉测业务。
- **Ch22** 部署——CI 流水线里跑 `pytest --cov`,覆盖率卡门禁。

fixture + dependency_overrides 是后面所有集成测试的地基,务必练熟。
