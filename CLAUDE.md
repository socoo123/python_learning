# CLAUDE.md — 项目指南

本文件是本项目的权威指南,每次会话自动加载。分两部分:**A. 学习项目本身**;**B. Web 网站子项目(规划中,待实施)**。

---

# A. Python 学习项目(已有内容)

面向 15 年 Java 经验开发者的 Python 全栈学习项目,40 章 / 6 模块,逐章「五件套」交付。
- 大纲:`SYLLABUS.md` ｜ 学习指南:`README.md` ｜ 闪卡索引:`REVIEW.md` ｜ 内容优化计划:`OPTIMIZATION_PLAN.md`(用户说「重新优化 chNN」时**必读**并严格按其 SOP 执行) ｜ 教材加图:`DIAGRAM_PLAN.md`(用户说「第一批 / 第二批 / 下一批 / 加图 batch N」时**必读**；内容批**最多 4 个 agent、每 agent 只改一章**)
- 已生成内容:M1(Ch01-07)、M2(Ch08-12)、M3(Ch13-22)、M4(Ch23-27)、M5(Ch28-33)、M6(Ch34-40)——**40 章全齐**
- 五件套约定:`ch{NN}/tutorial.md` + `ch{NN}_assignment.py`(作业,擦成 `...` 交付)+ `test_ch{NN}_assignment.py` + `review.md` + mock 数据
- 工作流:写完整实现 → pytest 全绿 → 擦成 `...` → 写 tutorial/review。质量标准见 memory(`tutorial-coverage-standard`)。
- 运行测试:`uv run pytest <path> -v`;各模块依赖:`uv sync --extra web|devops|ai`(extras 互斥,会卸其他组)

> Web 网站子项目(下文 B 部分)**不改动**这些已有课程文件,构建时只**读取+烘焙**它们。

---

# B. Web 网站子项目(预渲染静态页,可上 GitHub Pages)

> 状态:**2026-09-26 起改为预渲染 HTML,不再使用 Vite / React。** 网页只读教程;作业在仓库五件套里写,`uv run pytest` 验证。
> 目标:相对路径的静态站,推到 `main` 后由 GitHub Actions 发布到 Pages。双击 `web/index.html` 也能看。

## B.1 已拍板的决策

1. **独立、可移植**:站点文件就是 `web/index.html`、`web/modules/`、`web/chapters/`、`web/assets/`。相对路径,不写死仓库名。内容 JSON 在 `web/src/content/`,提交 git。
2. **网页只读,作业走仓库**:课程页渲染 tutorial Markdown + 闪卡 + 本地作业路径。不提供 Monaco / Pyodide / 交错小练习。实现写在 `chNN_assignment.py`。
3. **看站不需要构建**:`python3 -m http.server 5188`,或双击 `web/启动学习站.command` / `web/index.html`。只有课程内容变了才跑 `bun run build:content`(烘焙 JSON 并重新生成 HTML)。

## B.3 技术栈明细

| 关注点 | 选型 | 理由 |
|--------|------|------|
| 页面 | **预渲染 HTML** | `index.html` + `modules/mN.html` + `chapters/chNN.html`,相对路径,Pages 直接托管 |
| 脚本 | **经典 JS**(marked / highlight.js / mermaid) | 无打包步骤;mermaid 按需加载 |
| 样式 | **手写 CSS** | 护眼米色 / 德古拉,`assets/css/style.css` |
| 内容 | **Bun 脚本** | `build-curriculum.ts` 烘焙 JSON,`render-pages.ts` 生成 HTML |
| 进度持久化 | **localStorage** | 键 `py-learn:learner-state:v1`。Pages 与本地打开同一把钥匙 |

## B.4 内容管线(自包含、可移植的核心)

- `scripts/build-curriculum.ts`(Bun 原生跑,无需编译):从源仓库(默认 `../`,即 python_learning)扫描各章,烘焙出 `web/src/content/`:
  - `index.json`:模块/章节轻量目录 `{ id, title, runMode, ... }`(首页用)
  - `shared.json`:`conftest` + mock 数据
  - `chapters/chXX.json`:单章全文(tutorial / assignment / test / review / sections),**课程页懒加载**
- **`src/content/` 提交进 git** → 网站运行时只读它,**不依赖源仓库** → web/ 可独立 clone 运行 / 独立上传 GitHub。
- 源课程更新 → 跑 `bun run build:content`(烘焙 JSON **并** `render-pages` 刷新 HTML) → 提交 `src/content/` 和生成的 HTML。
- 判断 runMode:扫 `assignment.py` / `test_*.py` 的 import —— 出现 `fastapi`/`sqlalchemy`/`httpx`/`psutil`/`typer`/`rich`/`schedule`/`anthropic`/`openai` 等(见烘焙脚本 `LOCAL_IMPORTS`) → `local`;否则 `pyodide`。M5 目录强制 `local`。Ch24–27 因 subprocess/psutil/typer/schedule 均为 Local;Ch23 仅 pathlib 故仍为 Pyodide。

## B.5 课程页

教程 Markdown 全文只读。左侧 sticky 目录(≥3 节、宽屏时显示)。页底给出仓库 assignment 路径和 `uv run pytest` 命令。闪卡可展开。无编辑器、不跑 Pyodide。

**界面缩放**:CSS zoom 作用在 `<html>`。⌘/Ctrl±、⌘0、触控板捏合、页头 −/%/+ ;75%–175%,持久化 localStorage `py-learn:ui-zoom:v1`。教程正文 18px。

## B.6 目录结构(自包含 `web/`)

```
web/
├── index.html                    # 首页,相对路径
├── modules/                      # m1.html …
├── chapters/                     # ch01.html … 内嵌教程
├── assets/                       # css / js / vendor
├── .nojekyll
├── scripts/build-curriculum.ts   # 源五件套 → src/content
├── scripts/render-pages.ts       # src/content → 上面的 HTML
└── src/content/                  # 烘焙 JSON,提交 git
```

## B.7 主题

护眼米色默认 / 德古拉深色可切换。教程正文按主题提高对比度。

## B.8 实施阶段

- [x] **P0 脚手架**(2026-07-28):Vite+React+TS+Tailwind 深色 shell;首页 6 模块卡片。
- [x] **P1 内容烘焙**(2026-07-28):`build-curriculum.ts` 摄取源仓库 → `src/content/curriculum.json`;课程页渲染 tutorial.md。已烘焙 M1-M4 共 27 章。
- [x] **开放 M1–M4**(2026-07-29):M1/M2/M3/M4 `available=true`(首页可点);M3 与多数 M4 章为 Local 只读+本地 uv 命令。
- [x] **开放 M5–M6**(2026-08-01):五件套已生成并烘焙;M5 全 Local、M6 全 Pyodide;`available=true`。40 章进 web。
- [x] **P2 编辑器 + Pyodide**(2026-07-28):Monaco 接入;Pyodide 运行 pytest;终端红绿。
- [x] **去掉网页练习**(2026-08-23):按用户要求移除交错编辑器 / Monaco / Pyodide。课程页只读教程;作业在仓库五件套完成。
- [x] **静态页 + GitHub Pages**(2026-09-26):去掉 Vite/React,预渲染 HTML。`.github/workflows/pages.yml` 发布 `web/` 里的静态文件。
- [x] **进度勾选**(2026-08-22):章节页「已学完」;首页/模块卡/顶栏进度条。`bun run dev` 写入 `web/.learner-state.json` + localStorage。
- [x] **桌面版 DMG / Tauri**(2026-09-14):`web/src-tauri/` 壳。2026-09-26 起加载同一份静态 HTML(`desktop-dist/`)。更新流程:改课程 → `build:content` → `build:dmg`。详见 B.12。

> 顺序:P0→P1 先让全站教程可看;P2 给 Pyodide 章节加交互;P3 收尾。早期即有可用产物。

## B.9 关键风险与决策点

1. **GitHub Pages 子路径**:项目站地址是 `https://<user>.github.io/python_learning/`。页面只用相对路径(`./`、`../`),不要写以 `/` 开头的资源地址。
2. **Jekyll**:发布目录必须带 `.nojekyll`,否则 Pages 会吞掉下划线开头的文件。
3. **章节 HTML 内嵌教程**:`chapters/chNN.html` 把教程 JSON 写进页面,这样 `file://` 双击也能开,不必再发请求。改教程后要重新 `render-pages`。
4. **内容同步**:源课程改动 → `bun run build:content`(JSON + HTML) → 提交。

## B.10 常用命令

```bash
cd web
python3 -m http.server 5188   # 本地看站;或双击 启动学习站.command
bun run build:content         # 源仓库 → src/content/ → 静态 HTML
bun run render                # 只根据现有 JSON 重刷 HTML
bun run build:dmg             # Mac 桌面版(Tauri;先拷到 desktop-dist/)
```

GitHub Pages:推到 `main` 触发 `.github/workflows/pages.yml`。仓库 Settings → Pages → Source 选 **GitHub Actions**。发布的只有 `index.html`、`.nojekyll`、`chapters/`、`modules/`、`assets/`。

---

## B.11 内容与生成策略(2026-07-28 用户澄清,务必遵守)

1. **网页不放练习编辑器**:课程页是 `教程 → 本地作业提示 → 闪卡`。作业在仓库 assignment 文件里写。
2. **不要再加交错式网页练习**:用户已明确改回在 markdown/py 五件套里做题。
3. **教程内容不必照搬 .md**:用户已编辑过原始 .md。web 端可自由重组/精简/改写呈现,已生成的 .md/.py 可直接拿来用但不必逐字一致。
4. **后续未生成章节(M5/M6 等)直接生成 web 端内容**:不再先建 .md/.py 五件套再烘焙;直接写进 web 的内容数据(curriculum 结构)。省去中间步骤。
5. **web 跑不了的代码 → 放仓库对应模块目录**:如 M5 的 LLM 代码进 `05_ai_framework/chXX/`(本地 uv 跑);web 页只放教程 + 本地运行指引(LocalNotice 模式),代码在仓库里供单独运行。
6. **课程文件仍是源**:`01_python_core` 等已生成目录,web 只读不写;但「新章节」可跳过 .md/.py 直接产 web 内容。



- 实施 Web 子项目时,**只在 `web/` 目录内操作**;构建脚本**只读**源仓库章节文件,**绝不修改** `tutorial.md`/`assignment.py`/test 等课程文件。

## B.12 桌面版打包(Tauri,2026-09-14)

- 结构:`web/src-tauri/`(tauri.conf.json / Cargo.toml / src/main.rs / capabilities / .cargo/config.toml / icons)。devUrl 端口 5188(静态文件服务,目录是 `web/`)。productName 用 ASCII `PythonLearning`(避免打包脚本非 ASCII 问题),窗口标题中文「Python 学习」。
- **前置**:rustup 装的 Rust(minimal profile,`~/.cargo/bin`;新终端自动生效,旧终端 `source ~/.cargo/env`)+ Xcode CLT。升级用 `rustup update`。
- **打包**:`cd web && bun run build:dmg`(= `tauri build`,先 `prepare-desktop.ts` 把静态页拷到 `desktop-dist/`)。产物:`src-tauri/target/release/bundle/macos/PythonLearning.app` 与 `bundle/dmg/PythonLearning_<ver>_aarch64.dmg`。改版本号:tauri.conf.json 的 `version`。
- **代理坑**:cargo 会回退读 git 全局 `http.proxy`(本机指向 127.0.0.1:8118,常不开)→ 已在 `web/src-tauri/.cargo/config.toml` 设 `http.proxy = ""` 项目级绕过(布尔 false 这版 cargo 不收,必须空字符串)。
- 前端是多页静态 HTML(相对路径),`tauri://` 下不用 history 路由。进度勾选走 WebView 自带 localStorage。
- 保留已有「五件套 + uv pytest」本地学习工作流,网站是叠加的浏览器学习入口,不替代本地流程(Local 章节仍走本地)。
- 每个实施阶段(P0-P3)完成后,在本文件 B.8 勾选进度,并更新 memory `python-learning-project`。
