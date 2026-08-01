# Python 全栈学习 · 交互式课程网站

把课程(`../01_python_core` 等章节)做成 React 深色静态网站:模块 → 章节 → 课程页,
教程 + 浏览器内代码编辑器 + 一键运行 pytest(Pyodide)。**全程 Bun**。

## 快速开始

```bash
cd web
bun install          # 装依赖
bun run dev          # 开发服务器(http://localhost:5188)
```

dev/build 时会自动调用 `build:content` 重新烘焙课程内容(只要 `../` 源仓库存在)。

## 常用命令

| 命令 | 作用 |
|------|------|
| `bun run dev` | 开发服务器(HMR),自动烘焙内容 |
| `bun run build` | 生产构建 → `dist/` |
| `bun run build:content` | 手动重新烘焙:`../` 源仓库 → `src/content/{index,shared,chapters}` |
| `bun run preview` | 预览生产构建 |

## 架构

- **内容烘焙**:`scripts/build-curriculum.ts`(Bun 原生跑 TS)扫描源仓库章节,产出:
  - `src/content/index.json` — 模块/章节轻量目录(首页用)
  - `src/content/shared.json` — conftest + mock 数据
  - `src/content/chapters/chXX.json` — 单章全文(教程/作业/测试/闪卡),**点进章节才懒加载**
  - 产物提交进 git,单独 clone `web/` 也能跑(可移植)
- **运行方式**:
  - 🟢 Pyodide 章节(M1、M2、Ch23、M6):浏览器内 Monaco 编辑器 + ▶ 运行(Pyodide 跑 pytest)+ 终端红绿。
  - 🔒 Local 章节(M3、M5、Ch24–27):只读教程 + 本地运行命令(代码仍写本地 .py)。

## 内容更新

源课程文件改动后:`bun run build:content` 重新烘焙 → 提交 `src/content/`。

新增可用模块:在 `scripts/build-curriculum.ts` 的 `MODULE_DEFS` 里把对应模块 `available` 改 `true`。

## 部署到 GitHub Pages(未来)

构建前在 `vite.config.ts` 设 `base: "/<仓库名>/"`,react-router 的 `BrowserRouter` 配 `basename`,
并加 `404.html` 做 SPA fallback。当前为本地开发态,未配 Pages。

## 技术栈

Bun · Vite · React 18 · TypeScript · Tailwind CSS · Monaco Editor · Pyodide · react-markdown
