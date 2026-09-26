# Python 全栈学习 · 静态课程站

模块 → 章节 → **只读教程**。作业仍在仓库五件套里写，用 `uv run pytest` 验证。

页面是事先生成的 HTML（`index.html`、`modules/`、`chapters/`），相对路径，不依赖 Vite。GitHub Pages 直接托管这一份；双击 `index.html` 或 `启动学习站.command` 也能在本机看。

## 本地看站

```bash
cd web
python3 -m http.server 5188   # http://localhost:5188
```

也可以双击 `启动学习站.command`，或直接双击 `index.html`（`file://`）。

## 内容更新

源课程（`../01_python_core` 等）改动后：

```bash
cd web
bun run build:content
```

这一步会先烘焙 `src/content/`，再生成静态 HTML。只改了 JSON、想重刷页面时：`bun run render`。

生成物要提交 git：`index.html`、`modules/`、`chapters/`、`assets/js/data.js`，以及 `src/content/`。

## GitHub Pages

仓库里的 `.github/workflows/pages.yml` 会在推到 `main` 后，把下面这些文件发布出去：

- `index.html`、`.nojekyll`
- `chapters/`、`modules/`、`assets/`

仓库 **Settings → Pages → Source** 选 **GitHub Actions**。站点地址是 `https://<用户名>.github.io/python_learning/`。页面之间用相对路径，不写死仓库名。

## 桌面版

`bun run build:dmg` 仍走 Tauri。打包前会把静态页拷到 `desktop-dist/`（不进 git），避免把源码目录打进安装包。

## 学习进度

「已学完」存在浏览器 `localStorage`（键 `py-learn:learner-state:v1`），和以前的网页是同一把钥匙。GitHub Pages 上没有本地文件可写。
