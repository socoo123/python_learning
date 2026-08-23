# Python 全栈学习 · 课程网站

把课程（`../01_python_core` 等章节）做成 React 静态网站：模块 → 章节 → **只读教程**。
作业在仓库五件套里写，用 `uv run pytest` 验证。**全程 Bun**。

## 快速开始

```bash
cd web
bun install          # 装依赖
bun run dev          # 开发服务器(http://localhost:5188)
```

dev/build 时会自动调用 `build:content` 重新烘焙课程内容（只要 `../` 源仓库存在）。

## 常用命令

| 命令 | 作用 |
|------|------|
| `bun run dev` | 开发服务器(HMR),自动烘焙内容 |
| `bun run build` | 生产构建 → `dist/` |
| `bun run build:content` | 手动重新烘焙:`../` 源仓库 → `src/content/{index,shared,chapters}` |
| `bun run preview` | 预览生产构建 |

## 学习进度

用 `bun run dev` 时，勾选「已学完」会写入 **`web/.learner-state.json`**（已 gitignore）。刷新、关标签、换浏览器再开同一个 dev 服务，进度还在。

静态部署（没有 dev API）时退化为浏览器 localStorage。

- **内容烘焙**:`scripts/build-curriculum.ts` 扫描源仓库章节,产出:
  - `src/content/index.json` — 模块/章节轻量目录(首页用)
  - `src/content/shared.json` — conftest + mock 数据
  - `src/content/chapters/chXX.json` — 单章全文(教程/作业/测试/闪卡),**点进章节才懒加载**
  - 产物提交进 git,单独 clone `web/` 也能跑(可移植)
- **网站呈现**:只读教程 + 闪卡 + 本地作业路径/`uv run pytest` 命令。不在浏览器里写代码、不跑 Pyodide。

## 内容更新

源课程文件改动后:`bun run build:content` 重新烘焙 → 提交 `src/content/`。

新增可用模块:在 `scripts/build-curriculum.ts` 的 `MODULE_DEFS` 里把对应模块 `available` 改 `true`。

## 技术栈

Bun · Vite · React 18 · TypeScript · Tailwind CSS · react-markdown
