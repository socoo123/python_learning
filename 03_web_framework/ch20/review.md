# Ch20 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | pytest fixture 和 JUnit `@BeforeEach`/`@AfterEach` 的关系?优势在哪? | fixture = setup+teardown 合体。优势:一个函数,`yield` 前 = setup、后 = teardown,不用拆两个方法;按**参数名注入**(声明式),不用继承基类 | ⬜ |
| 2 | fixture 里 `yield` 和 `return` 的区别?用错会怎样? | `yield` 把函数切两半:前=setup、后=teardown(测试后执行)。用 `return`:teardown 代码**永不执行**。fixture 本质是「生成一次值的生成器」 | ⬜ |
| 3 | fixture 怎么注入到测试函数? | **按名字匹配**。测试函数声明参数名 = fixture 名,pytest 自动调用 fixture 并把 `yield` 的值传进来。名字差一个字母就 `fixture not found` | ⬜ |
| 4 | `@pytest.mark.parametrize` 对应 Java 什么?参数名怎么写? | = JUnit5 `@ParameterizedTest`。参数名是**逗号分隔的字符串** `"a, b"`,不是裸变量(忘引号会报错)。每行数据展开成一个独立测试,ID 用参数值拼 | ⬜ |
| 5 | `app.dependency_overrides[dep] = fake` 干嘛?对应 Java? | 把 FastAPI 依赖(如 `get_current_user`)替换成假函数,绕过真实逻辑(鉴权/DB)。= Spring `@MockBean` / `@WithMockUser`。键是**函数对象**,不是字符串 | ⬜ |
| 6 | `dependency_overrides` 用完必须做什么?为什么? | **还原**(clear/pop),否则全局可变状态泄漏到下个测试,鉴权被静默绕过。还原:`app.dependency_overrides.clear()`(try/finally)或用 `monkeypatch.setitem`(自动还原) | ⬜ |
| 7 | `auth_headers(token)` 和 `override_auth(app)` 各解决什么? | `auth_headers`:真带合法 token,既测鉴权又测业务(401 也会触发)。`override_auth`:整替依赖、跳过鉴权,专注测业务逻辑。测「401 正确返回」用前者;只测 CRUD 用后者 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「fixture 的 `yield` 为何比 `@BeforeEach`+`@AfterEach` 优雅」?
- [ ] 能说清「`dependency_overrides` 键为何是函数对象,值为何要兼容原返回类型」?
- [ ] 能说清「三种测鉴权端点的方式(带头/替换依赖/两者都测)的取舍」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。

---

### 覆盖率命令速记

```bash
uv run pytest 03_web_framework/ch20/ --cov=ch20_assignment --cov-report=term-missing
# HTML 报告(可点):
uv run pytest 03_web_framework/ch20/ --cov=ch20_assignment --cov-report=html
# → 打开 htmlcov/index.html
```

覆盖率是**下限**(低报警),不是目标——100% 行覆盖 ≠ 没 bug(assert 可能没断关键值)。
