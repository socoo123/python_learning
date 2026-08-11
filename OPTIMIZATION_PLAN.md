# OPTIMIZATION_PLAN.md — 课程内容优化计划（40 章逐章重制）

> **这份文件是给「清空上下文后的新会话」看的。**
> 用户说「**重新优化 chNN**」（如「重新优化 ch01」）时：
> ① 先读本文件全文 → ② 读 `CLAUDE.md` 和 `SYLLABUS.md` 中该章定位 → ③ 按下方 SOP 执行。
> 全部章节优化完成后，本文件可归档删除。

---

## 1. 背景：为什么要优化

学习者（15 年 Java 后端）反馈两个核心痛点：

1. **例子太少**：教程小节里常常一个知识点只有 1 个示例，没有「错误写法 → 正确写法」对照，没有真实数据场景，看完还是不会用。
2. **题目莫名其妙**：作业题是为语法点硬造的玩具题（如 `add(a,b)` 返回 `a+b`、`describe` 拼字符串），缺业务语境，不知道学它干嘛；部分题目预期行为模糊。

**优化目标**：每一章做到「教程例子管够、作业题有真实业务感、测试能真正验证掌握」。质量标准见 §3，验收不过关不交付。

---

## 2. 每章优化 SOP（严格按序执行）

以「重新优化 ch01」为例，`{NN}` = `01`，`{M}` = 模块目录（如 `01_python_core`）。

### Step 0 · 定位与诊断（先输出，再动手）

1. 读 `SYLLABUS.md` 确认该章大纲定位（**不扩纲、不缩纲**）。
2. 读该章五件套：`{M}/ch{NN}/tutorial.md`、`ch{NN}_assignment.py`、`test_ch{NN}_assignment.py`、`review.md`，以及共享 `conftest.py` 和 `assets/mock_data/` 可用数据源。
3. 在对话中输出**简短诊断**（≤10 行）：例子缺口在哪、哪些题是玩具题、哪些知识点考了但没讲 / 讲了但没考、骨架是否擦干净。然后**直接开始重写**，不等用户确认（用户指令「重新优化」即授权）。

### Step 1 · 重写 tutorial.md

按 §3.1 质量标准重写。保留该章大纲范围，可自由增删小节，但必须满足格式红线（§4）。

### Step 2 · 重写 ch{NN}_assignment.py

按 §3.2 重写。先写**完整实现**（每个函数都真正实现），此时尚不擦除。

### Step 3 · 重写 test_ch{NN}_assignment.py

按 §3.3 重写。测试类命名必须是 `Test` + 函数名的 PascalCase（格式红线 §4.5）。

### Step 4 · 跑通测试

```bash
uv run pytest {M}/ch{NN}/test_ch{NN}_assignment.py -v
```

必须**全绿**。若该章属于 web/devops/ai extras 模块，先 `uv sync --extra web|devops|ai`（extras 互斥）。

### Step 5 · 擦除骨架 + 更新 review.md

1. 把 assignment 中每个函数体擦成 `...`：**保留签名、装饰器、完整 docstring（含任务/示例/提示）、`# TODO` 注释**，只把实现替换为 `...`。模块级 docstring 和必要 import 保留。
2. 擦完后**再跑一次 pytest 确认全红但可收集**（能 import、能跑、断言失败而不是语法错误）。
3. 重写 `review.md`：闪卡与新知识点一一对应，删掉已不存在知识点的旧卡。

### Step 6 · 同步 web 内容

```bash
cd web && bun run build:content
```

- 重烘焙后检查 `web/src/content/chapters/ch{NN}.json`：`sections` 里每节 `exerciseFunctions` 非空（交错式生效）；若整章只有 1 个 section 说明格式红线被破坏（§4），回 Step 1 修。
- Pyodide 章（清单见 §5）：确认 `runMode` 仍为 `"pyodide"`，即 assignment/test 中没有引入 `fastapi|sqlalchemy|httpx|psutil|subprocess|urllib|anthropic|openai`。
- `web/src/content/` 的 diff 是烘焙产物，**提示用户可提交，但用户没说就不 commit**。
- 如改动可能影响前端构建，可选跑 `cd web && bun run build` 验证。

### Step 7 · 收尾汇报

输出：改了什么、新增了多少例子/题目、测试全绿截图式摘要、进度表更新（把 §6 表中该章标为 ✅）。**不主动 git commit**（红线）。

---

## 3. 内容质量标准（验收清单）

### 3.1 tutorial.md

- [ ] **例子密度**：每个知识点 ≥ 2 个例子 = 1 个「Java 对照最小例」+ 1 个「真实场景例」（用本章主线的 mock 数据 / 运维场景 / API 场景，不用 foo/bar）。
- [ ] **错误对照**：Java 老手易错点给出「❌ 错误写法 → ✅ 正确写法」成对示例。
- [ ] **跳读标记**：🟢 秒懂 / 🟡 注意差异 / 🔴 Python 特有，标在每个小节或知识点上。
- [ ] **对应表**：文件前部有「作业 ↔ 教程对应表」，**每道作业题一行**，格式 `| \`func_name\` | §N.M | 知识点 |`（格式红线 §4.3）。
- [ ] **不超纲**：作业用到的每个知识点，教程必须有专节讲透（质量铁律）；教程不讲作业用不到的东西（可放「延伸阅读」明确标注）。
- [ ] 保留学习路径结构（本章地图 / 预览猜 / 费曼五步 / 闪卡指引），风格与现有章节一致。

### 3.2 ch{NN}_assignment.py

- [ ] **业务语境**：每题有明确的场景动机（「电商后台要过滤商品」「日志聚合要按级别计数」），禁止 `add`/`foo` 式纯语法玩具题。整章尽量围绕**一条主线场景**（如 ch02 围绕 products.json）。
- [ ] **题量与梯度**：6–10 个函数，从单知识点 → 综合题递进；最后一题尽量是「复用前面函数」的小综合。
- [ ] **docstring 自解释**：每题 docstring 含【场景】任务描述、≥ 2 个「输入 → 预期输出」示例（预期值必须是真实算出来的）、提示（点出用哪个知识点，不直接给答案）。
- [ ] **可判性**：返回确定值，避免依赖随机/时间/环境（除非该章就是教这个）。

### 3.3 test_ch{NN}_assignment.py

- [ ] 每个函数一个 `class TestXxx`（命名红线 §4.5），覆盖：正常 case ≥ 2、边界 case（空输入/极值/None）≥ 1。
- [ ] 断言值必须**手工验算过**；涉及 mock 数据的断言与 `assets/mock_data/` 实际内容一致。
- [ ] 测试要「能区分蒙对」：边界 case 能拦住错误实现（如硬编码返回值）。

### 3.4 review.md

- [ ] 闪卡覆盖本章全部 🔴/🟡 知识点；卡面问题具体（「Python 里 `dict` 为什么 3.7+ 有序？」），背面答案 ≤ 3 行。

---

## 4. 格式红线（web 烘焙脚本 `web/scripts/build-curriculum.ts` 的硬依赖，破坏 = 网站解析失败/回退）

1. **目录与文件名**：`{M}/ch{NN}/tutorial.md`、`ch{NN}_assignment.py`、`test_ch{NN}_assignment.py`、`review.md`，章节目录必须形如 `ch01`（`/^ch\d+$/`）。
2. **H1 标题**：`# Ch{NN} · 标题`——必须含 `·`（或 `•`/`・`/`-`），否则章节标题提取失败。
3. **分节**：教程以 `## `（H2）为分节边界；需要挂练习的小节标题必须含 `§N.M`（如 `## §2.3 dict 分组聚合`）。不要用 H2 干别的而不想要分节。
4. **对应表行**：`` `func_name` | §N.M ``——函数名用反引号、§ 号紧跟节号，正则 ` \`([a-z_][a-z0-9_]*)\`\s*\|\s*§(\d+\.\d+) `。**每个作业函数都必须出现在表里**，否则 web 交错式里该题丢失。
5. **测试类名**：`Test` + 函数名 PascalCase（`load_product_names` → `TestLoadProductNames`）。web 端单题运行是 `pytest test_file.py::TestXxx`，类名对不上 = 该题在网页上跑不了。
6. **函数定义**：作业函数必须**顶格** `def name(...)`（烘焙脚本按行首 `^def ` 切分）；装饰器紧贴 def；docstring 用 `"""` 且紧跟 def 行。
7. **骨架交付**：源仓库里的 assignment 永远是擦好的骨架（实现 = `...`，docstring/TODO 保留）。烘焙脚本会二次兜底擦除，但源文件必须自己擦净——本地 uv 工作流是主要学习入口。
8. **Pyodide 章的 import 红线**：见 §5，一旦 import 了本地依赖，该章会被自动降级为 Local 只读。

---

## 5. Pyodide / Local 章节清单（决定 Step 6 检查项）

| runMode | 章节 | web 呈现 |
|---|---|---|
| **Pyodide**（浏览器可跑） | M1 全（Ch01–07）、M2 全（Ch08–12）、Ch23、Ch25、Ch26、M6 全（Ch34–40） | 交错式：教程分节 + 每节嵌编辑器 + 单跑 `pytest path::TestXxx` |
| **Local**（只读） | M3 全（Ch13–22）、M5 全（Ch28–33，强制）、Ch24、Ch27 | 只读教程 + 🔒 徽章 + `uv run pytest` 指引 |

- Pyodide 章的 assignment/test **禁止** import：`fastapi`、`sqlalchemy`、`httpx`、`psutil`、`subprocess`、`urllib`、`anthropic`、`openai`（任一出现 → 自动判为 local）。
- Local 章也要重烘焙（教程/题目展示仍来自源文件），只是没有在线编辑器。

---

## 6. 40 章进度表（优化一章勾一章）

> 状态：⬜ 待优化 ｜ ✅ 已优化（日期）

### M1 语言核心（`01_python_core/`，Pyodide）

| 章 | 标题 | 状态 |
|---|---|---|
| Ch01 | 环境工具链 & 从 Java 到 Python 的思维转换 | ✅ 2026-08-11 |
| Ch02 | 数据结构：list / tuple / dict / set | ✅ 2026-08-11 |
| Ch03 | 控制流、迭代器、生成器、推导式 | ✅ 2026-08-11 |
| Ch04 | 函数：一等公民、闭包、装饰器 | ✅ 2026-08-11 |
| Ch05 | OOP：魔术方法、继承、dataclass | ✅ 2026-08-11 |
| Ch06 | 异常、上下文管理器、文件 IO | ✅ 2026-08-11 |
| Ch07 | 类型注解与 Pythonic 风格 | ✅ 2026-08-11 |

### M2 标准库（`02_stdlib/`，Pyodide）

| 章 | 标题 | 状态 |
|---|---|---|
| Ch08 | collections：Counter / defaultdict / deque / namedtuple | ✅ 2026-08-11 |
| Ch09 | itertools + functools：函数式利器 | ✅ 2026-08-11 |
| Ch10 | 正则表达式与字符串处理 | ✅ 2026-08-11 |
| Ch11 | 数据交换：json / csv / datetime | ✅ 2026-08-11 |
| Ch12 | 现代工具链：logging / 配置 / 项目结构 | ✅ 2026-08-12 |

### M3 FastAPI（`03_web_framework/`，Local）

| 章 | 标题 | 状态 |
|---|---|---|
| Ch13 | HTTP 客户端：httpx 调用 API | ⬜ |
| Ch14 | FastAPI 入门：第一个 API + Pydantic 模型 | ⬜ |
| Ch15 | 路由参数：路径参数 / 查询参数 / 分页 | ⬜ |
| Ch16 | 依赖注入系统（Depends） | ⬜ |
| Ch17 | 中间件、CORS、异常处理 | ⬜ |
| Ch18 | 异步编程 async/await | ⬜ |
| Ch19 | 数据库 ORM：SQLAlchemy 2.0 | ⬜ |
| Ch20 | 测试 API 进阶（TestClient + fixtures + 覆盖率） | ⬜ |
| Ch21 | 认证授权 JWT | ⬜ |
| Ch22 | 部署：uvicorn / gunicorn / Docker + 框架对比 | ⬜ |

### M4 运维脚本（`04_devops_scripts/`，Ch23/25/26 Pyodide；Ch24/27 Local）

| 章 | 标题 | 状态 |
|---|---|---|
| Ch23 | 文件系统批量操作：pathlib / shutil | ⬜ |
| Ch24 | 进程与子进程管理：subprocess / psutil | ⬜ |
| Ch25 | CLI 工具开发：Typer + Rich | ⬜ |
| Ch26 | 定时任务与日志分析：schedule + 聚合告警 | ⬜ |
| Ch27 | 配置管理与系统监控：psutil 巡检 + webhook 告警 | ⬜ |

### M5 AI 框架（`05_ai_framework/`，全 Local）

| 章 | 标题 | 状态 |
|---|---|---|
| Ch28 | LLM SDK 调用：Anthropic / OpenAI | ⬜ |
| Ch29 | Prompt 工程与结构化输出 | ⬜ |
| Ch30 | LangChain 基础：LCEL | ⬜ |
| Ch31 | RAG 实战：向量检索 | ⬜ |
| Ch32 | Agent 开发：Tool Use / ReAct | ⬜ |
| Ch33 | 用 FastAPI 封装 AI 服务 | ⬜ |

### M6 LeetCode（`06_leetcode/`，Pyodide）

| 章 | 标题 | 状态 |
|---|---|---|
| Ch34 | Python 刷题利器总览（stdlib 五件套） | ⬜ |
| Ch35 | 双指针 / 滑动窗口 | ⬜ |
| Ch36 | 哈希表 / 前缀和 | ⬜ |
| Ch37 | 栈 / 队列 / 单调栈 | ⬜ |
| Ch38 | 二叉树 / DFS / BFS | ⬜ |
| Ch39 | 动态规划 | ⬜ |
| Ch40 | 回溯 / 贪心 + 综合 | ⬜ |

---

## 7. 操作红线（继承 CLAUDE.md，再强调）

1. **源课程与 web 的边界**：改课程内容只动 `{M}/ch{NN}/` 五件套；web 侧只跑 `bun run build:content` 重烘焙，**绝不手改** `web/src/content/*.json`（烘焙产物），**绝不改** `web/scripts/build-curriculum.ts` 去迁就内容（内容迁就格式，不是反过来）。
2. **不主动 commit**：所有改动（含烘焙产物）完成后汇报，由用户决定何时提交。不改 git config。
3. **不破坏本地工作流**：五件套 + `uv run pytest` 始终可用，这是根本，web 只是叠加入口。
4. **M6 特殊**：LeetCode 章的题目是算法题，「业务场景」标准放宽，但每题仍需：题意讲清、示例输入输出、提示指向本章讲过的套路；教程例子可用 LeetCode 真题变体。
