# Ch20 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | pytest fixture 和 JUnit `@BeforeEach`/`@AfterEach` 的关系?优势? | fixture = setup+teardown **一个函数**:`yield` 前 = setup、后 = teardown;按**参数名声明式注入**,不用继承基类。资源跟着 fixture 走,测试「按需点菜」而非类级全员共享 | ⬜ |
| 2 | fixture 里 `yield` 和 `return` 的区别?用错会怎样? | `yield` 把函数切两半:暂停交值给测试,**测试结束后**继续跑 teardown。用 `return`:后面的 teardown 是死代码,**永不执行**。fixture 本质是「只生成一次值的生成器」 | ⬜ |
| 3 | fixture 怎么被 pytest 发现和注入? | **按参数名匹配**注入(差一个字母就 `fixture not found`)。发现:定义在 test 模块 / conftest.py,或 **import 进 test 模块命名空间**(本章的接线方式) | ⬜ |
| 4 | fixture 三种 scope 各跑几次? | `function`(默认,每测试一次)/ `module`(每 .py 一次)/ `session`(整个进程一次)。测 Web API 默认 function;连真 DB 常 session 建表 + function 事务回滚 | ⬜ |
| 5 | `app.dependency_overrides[dep] = fake` 干嘛?键和值各是什么? | 把 FastAPI 依赖(如 `get_current_user`)整个换成假实现,绕过鉴权/DB。= Spring `@MockBean` / `@WithMockUser`。键是**函数对象**(写字符串**静默无效**),值是零参可调用 | ⬜ |
| 6 | `dependency_overrides` 用完必须做什么?怎么还最优雅? | **还原**,否则全局可变状态泄漏,下个测试鉴权被静默绕过。推荐:让 `api_client` fixture 的 teardown 统一 `clear()`;一次性场景用 try/finally;或 `monkeypatch.setitem` 自动还原 | ⬜ |
| 7 | fixture 组合怎么写?清理职责放哪? | 一个 fixture 把另一个**声明为参数**:`admin_client(api_client)` 里先 `override_auth(...)` 再 `yield api_client`。清理职责放**最下层 fixture**(api_client 的 teardown 清 override),上层不用写 | ⬜ |
| 8 | `@pytest.mark.parametrize` 对应 Java 什么?参数名怎么写?数据能来自函数吗? | = `@ParameterizedTest`;数据写在装饰器里 ≈ `@CsvSource`,**来自函数** ≈ `@MethodSource`(装饰器直接吃函数返回值)。参数名是**逗号分隔的字符串** `"a, b"`,不加引号 NameError | ⬜ |
| 9 | parametrize 展开后的测试 ID 长什么样?有什么用? | 形如 `test_price_boundary[0.01-201]`——每组数据一个独立用例,ID 自带参数值,哪组挂了直接知道数据 | ⬜ |
| 10 | 为什么断言非法价格 422 必须配 `Field(gt=0)`? | 没约束时业务层不拦,非法价格也 201,断言只能写 `in (201, 422)`(等于没断言)。模型里加 `Field(gt=0)` → Pydantic 校验失败自动 422,边界测试才有**硬预期**。校验写模型里,别在端点手写 if | ⬜ |
| 11 | 怎么直接单测 `get_current_user` 这类依赖函数(不过 HTTP)? | 普通函数直接调:`with pytest.raises(HTTPException) as exc_info:` 后断言 `exc_info.value.status_code == 401`。= JUnit `assertThrows`。单元测依赖 + TestClient 集成测端点,两层都要 | ⬜ |
| 12 | `auth_headers`(真带 token)和 `override_auth`(替换依赖)各解决什么? | 前者:真走鉴权逻辑,顺带验 401/201,适合「测鉴权本身」;后者:整替依赖跳过鉴权,专注测业务逻辑。测「401 是否正确返回」用前者,只测 CRUD 用后者 | ⬜ |
| 13 | 为什么覆盖率是下限不是目标?本章达标线? | 100% 行覆盖 ≠ 没 bug(断言可能没断关键值)。当门禁用(本章 ≥90%,实际 98%),别当奖杯 | ⬜ |

## 🎓 费曼自检

- [ ] 能讲清「fixture 的 `yield` 为何比 `@BeforeEach`+`@AfterEach` 优雅」?
- [ ] 能讲清「`dependency_overrides` 键为何是函数对象、用完为何必须还原」?
- [ ] 能讲清「`admin_client` 组合了什么、清理职责为何在最下层 fixture」?
- [ ] 能讲清「parametrize 数据源函数 ↔ JUnit `@MethodSource`」以及 422 硬断言为什么依赖 `Field(gt=0)`?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。

---

### 覆盖率命令速记

```bash
uv run pytest 03_web_framework/ch20/test_ch20_assignment.py --cov=ch20_assignment --cov-report=term-missing
# HTML 报告(可点):
uv run pytest 03_web_framework/ch20/test_ch20_assignment.py --cov=ch20_assignment --cov-report=html
# → 打开 htmlcov/index.html
```

本章参考实现跑出来:**42 passed,覆盖率 98%**(65 语句仅 1 行未覆盖)。
