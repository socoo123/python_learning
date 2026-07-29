# CLAUDE.md — 项目指南

本文件是本项目的权威指南,每次会话自动加载。分两部分:**A. 学习项目本身**;**B. Web 网站子项目(规划中,待实施)**。

---

# A. Python 学习项目(已有内容)

面向 15 年 Java 经验开发者的 Python 全栈学习项目,40 章 / 6 模块,逐章「五件套」交付。
- 大纲:`SYLLABUS.md` ｜ 学习指南:`README.md` ｜ 闪卡索引:`REVIEW.md`
- 已生成内容:M1(Ch01-07)、M2(Ch08-12)、M3(Ch13-22)、M4(Ch23-27);M5/M6 待生成
- 五件套约定:`ch{NN}/tutorial.md` + `ch{NN}_assignment.py`(作业,擦成 `...` 交付)+ `test_ch{NN}_assignment.py` + `review.md` + mock 数据
- 工作流:写完整实现 → pytest 全绿 → 擦成 `...` → 写 tutorial/review。质量标准见 memory(`tutorial-coverage-standard`)。
- 运行测试:`uv run pytest <path> -v`;各模块依赖:`uv sync --extra web|devops|ai`(extras 互斥,会卸其他组)

> Web 网站子项目(下文 B 部分)**不改动**这些已有课程文件,构建时只**读取+烘焙**它们。

---

# B. Web 网站子项目(Bun + React 静态站 · 设计文档 v2)

> 状态:**设计已定,待实施**。本节是实施蓝图,动手前再读一遍。
> 目标:做一个**独立、可移植**的 React 深色静态网站,模块→章节→课程页。Pyodide 能跑的章节在浏览器内编辑+运行 pytest;本地章节只读展示。

## B.1 已拍板的决策

1. **独立、可移植**:web 是自包含项目。课程内容在**构建时烘焙**进 `web/src/content/` 并提交 git → 单独 clone `web/` + `bun install` + `bun run dev` 就能跑,可独立上传 GitHub 在别处运行。
2. **运行方式 = 浏览器内运行(Pyodide)**:只有 Pyodide 能跑的章节才有「编辑+运行」交互。依赖系统/网络的章节**代码不进网页编辑器**,继续走本地 uv 文件工作流。
3. **全程 Bun**:`bun install` / `bun run dev` / `bun run build` 全部经 Bun。Bun 原生跑 TS(内容烘焙脚本无需编译)。React 打包用 **Vite(跑在 Bun 上)**,HMR 成熟稳。Pyodide 走浏览器端 CDN,与 Bun 无关。

## B.2 章节在网站上的呈现(关键简化)

| 章节 | 网站呈现 |
|------|---------|
| **Pyodide 章节**:M1 全(Ch01-07)、M2 全(Ch08-12)、Ch23、Ch25、Ch26、M6 全(Ch34-40) | **完整交互**:教程 + Monaco 编辑器(预填 `...` 骨架)+ ▶ 运行(Pyodide 跑 pytest)+ 终端输出(红绿) |
| **Local 章节**:M3 全(Ch13-22)、M5 全(Ch28-33)、Ch24、Ch27 | **只读教程** + 「🔒 本章在本地运行」徽章 + 仓库路径 + `uv run pytest ...` 命令;**无编辑器**(代码仍在本地 .py 文件里写) |

> 可调:若希望 Local 章节完全不进网页(只保留 Pyodide 章节),砍掉即可——说一声。

## B.3 技术栈明细

| 关注点 | 选型 | 理由 |
|--------|------|------|
| 运行时+包管理 | **Bun** | 全程统一;装包快;原生跑 TS |
| 构建/HMR | **Vite**(跑在 Bun 上) | React SPA 生态最成熟,HMR 好 |
| 框架 | **React 18 + TypeScript** | 用户指定 React |
| 样式 | **Tailwind CSS + shadcn/ui** | 深色主题好做,组件省心 |
| 路由 | **react-router-dom v6** | `/`、`/module/:id`、`/chapter/:id` |
| 代码编辑器 | **Monaco**(`@monaco-editor/react`) | VS Code 同款,Java 老手熟悉;备选 CodeMirror 6(更轻) |
| 浏览器跑 Python | **Pyodide**(CDN 懒加载) | 真 CPython,能跑 pytest |
| Markdown 渲染 | **react-markdown + remark-gfm + rehype-highlight** | 渲染 tutorial.md |
| 进度持久化 | **localStorage** | 无后端,记每章全绿 + 闪卡掌握 |

## B.4 内容管线(自包含、可移植的核心)

- `scripts/build-curriculum.ts`(Bun 原生跑,无需编译):从源仓库(默认 `../`,即 python_learning)扫描各章,烘焙出 `web/src/content/`:
  - `curriculum.json`:每章元数据 `{ id, module, title, runMode, tutorialMd, assignmentSkeleton, testSource, reviewCards, mocks }`
  - 把 `tutorial.md` 正文、`assignment.py`(`...` 骨架)、`test_*.py`、`review.md` 闪卡、`assets/mock_data/*` 全部嵌入
- **`src/content/` 提交进 git** → 网站运行时只读它,**不依赖源仓库** → web/ 可独立 clone 运行 / 独立上传 GitHub。
- 源课程更新 → 跑 `bun run build:content` 重新烘焙 → 提交 diff。
- 判断 runMode:扫 `assignment.py` / `test_*.py` 的 import —— 出现 `fastapi`/`sqlalchemy`/`httpx`/`psutil`/`subprocess`/`urllib`/`anthropic`/`openai` → `local`;否则 `pyodide`。

## B.5 运行流程(Pyodide 章节)

1. Monaco 编辑器预填 `...` 骨架,用户写实现。
2. 点 ▶ 运行 → 首次懒加载 Pyodide(CDN ~10MB,spinner);后续复用单例。
3. 把「用户编辑后的 assignment 代码」+ test 源码 + mock 数据 + `conftest.py` 写入 Pyodide 虚拟 FS,设 sys.path,让 `from ch{NN}_assignment import ...` / `from conftest import ...` 能跑。
4. Pyodide 内跑 `pytest.main(['test_xxx.py','-v','--tb=short'])`,捕获 stdout/stderr/退出码。
5. 终端区显示 `N passed`/`M failed` + 失败详情。全绿 → localStorage 标本章完成。

## B.6 目录结构(自包含 `web/`)

```
web/                              ← 自包含,可独立成 repo / 上传 GitHub
├── package.json                  # 包管理用 bun;scripts: dev/build/build:content
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── index.html
├── scripts/
│   └── build-curriculum.ts       # bun 原生跑;读 ../ 源仓库 → 烘焙 src/content/
├── src/
│   ├── content/                  # ★ 烘焙产物,提交 git(网站唯一数据源)
│   │   └── curriculum.json
│   ├── main.tsx
│   ├── App.tsx                   # 路由
│   ├── routes/
│   │   ├── Home.tsx              # 6 模块卡片
│   │   ├── ModulePage.tsx        # 章节列表
│   │   └── ChapterPage.tsx       # 教程 + 编辑器(Pyodide)/ 只读(Local)
│   ├── components/
│   │   ├── ModuleCard.tsx
│   │   ├── CodeRunner.tsx        # Pyodide 章节:Monaco + 运行 + 终端
│   │   ├── LocalBadge.tsx        # Local 章节:🔒 徽章 + 仓库路径 + uv 命令
│   │   ├── MarkdownView.tsx      # 渲染 tutorial.md
│   │   ├── Flashcards.tsx        # 闪卡交互
│   │   └── Terminal.tsx          # 终端样式输出
│   ├── hooks/
│   │   └── usePyodide.ts         # Pyodide 单例 + 懒加载
│   ├── lib/
│   │   ├── pyodideRunner.ts      # 写虚拟 FS + 跑 pytest
│   │   └── progress.ts           # localStorage 进度
│   └── styles/globals.css        # Tailwind + 深色变量
└── README.md                     # 怎么 bun install / dev / build / 部署 GitHub Pages
```

## B.7 深色主题

背景 zinc/slate 深(`zinc-950`/`slate-900`),卡片 `zinc-900` 带细边框;强调色 emerald(全绿)/ indigo(主操作);报错 `red-500`;代码与终端区近黑 + 等宽;Monaco 用 `vs-dark`。整体 IDE/终端风。

## B.8 实施阶段

- [x] **P0 脚手架**(2026-07-28):Vite+React+TS+Tailwind 深色 shell;首页 6 模块卡片。
- [x] **P1 内容烘焙**(2026-07-28):`build-curriculum.ts` 摄取源仓库 → `src/content/curriculum.json`;课程页渲染 tutorial.md。已烘焙 M1-M4 共 27 章(M2-M4 available=false,仅 M1 可点)。
- [x] **P2 编辑器 + Pyodide**(2026-07-28):Monaco 接入;Pyodide 运行 pytest;终端红绿。
- [x] **交错式 + Dracula 主题**(2026-07-28):课程页改为「讲一节练一节」——教程按 § 切分,每节后嵌该函数的小编辑器 + 单跑该函数测试(`pytest path::TestClass`,其余函数用骨架占位保证 import)。烘焙脚本解析 tutorial 的 §小节 + 对应表 + 函数骨架。解析不到的章(Ch02/Ch05)自动回退「整章教程+末尾作业」。配色全换 Dracula(含 Monaco 自定义主题)。dev 端口 5188。
- [ ] **P3 打磨**:Local 章节只读页;进度 localStorage;闪卡可交互;Ch01 骨架还原;GitHub Pages 部署。

> 顺序:P0→P1 先让全站教程可看;P2 给 Pyodide 章节加交互;P3 收尾。早期即有可用产物。

## B.9 关键风险与决策点

1. **Pyodide 体积**(~10MB):懒加载,只在首次点运行时拉,首页不阻塞。
2. **pytest in Pyodide**:验证 `micropip install pytest` 能跑现有测试;现有测试依赖 `from conftest import load_mock_json` + mock 数据,需一并写入虚拟 FS 并设 sys.path。
3. **可移植性**:`src/content/` 必须自包含(嵌入 mock 数据 + test 源码),否则单独 clone web/ 跑不起来。
4. **Bun + Vite 兼容**:Vite 在 Bun 下运行良好;若遇问题回退 `node`/`npm`(影响很小)。
5. **Monaco vs CodeMirror**:默认 Monaco;嫌包大换 CodeMirror 6。
6. **内容同步**:源课程改动 → `bun run build:content` 重烘焙 → 提交。

## B.10 常用命令(实施后)

```bash
cd web
bun install                 # 装前端依赖(bun)
bun run dev                 # 开发服务器(HMR)
bun run build               # 生产构建 → web/dist(纯静态,部署 GitHub Pages)
bun run build:content       # 重新烘焙课程内容(源仓库 → src/content/)
```

---

## B.11 内容与生成策略(2026-07-28 用户澄清,务必遵守)

1. **作业位置 = 教程之后(靠后)**:课程页布局是 `教程 → 作业 → 闪卡`。作业绝不放最前、绝不藏 Tab。当前已实现「教程在前 + 作业在后」。
2. **(可选升级)交错式**:每讲完一节(§X.Y),紧跟该节对应的那道练习(独立小编辑器 + 单跑该函数的测试,`pytest -k`)。利用各章 tutorial 已有的「作业↔知识点对应表」。是否上交错式,待用户定(见下)。
3. **教程内容不必照搬 .md**:用户已编辑过原始 .md。web 端可自由重组/精简/改写呈现,已生成的 .md/.py 可直接拿来用但不必逐字一致。
4. **后续未生成章节(M5/M6 等)直接生成 web 端内容**:不再先建 .md/.py 五件套再烘焙;直接写进 web 的内容数据(curriculum 结构)。省去中间步骤。
5. **web 跑不了的代码 → 放仓库对应模块目录**:如 M5 的 LLM 代码进 `05_ai_framework/chXX/`(本地 uv 跑);web 页只放教程 + 本地运行指引(LocalNotice 模式),代码在仓库里供单独运行。
6. **课程文件仍是源**:`01_python_core` 等已生成目录,web 只读不写;但「新章节」可跳过 .md/.py 直接产 web 内容。



- 实施 Web 子项目时,**只在 `web/` 目录内操作**;构建脚本**只读**源仓库章节文件,**绝不修改** `tutorial.md`/`assignment.py`/test 等课程文件。
- 保留已有「五件套 + uv pytest」本地学习工作流,网站是叠加的浏览器学习入口,不替代本地流程(Local 章节仍走本地)。
- 每个实施阶段(P0-P3)完成后,在本文件 B.8 勾选进度,并更新 memory `python-learning-project`。
