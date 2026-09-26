/**
 * 静态页生成器:src/content/*.json → index.html + modules/*.html + chapters/chNN.html + assets/js/data.js
 *
 * 运行:bun scripts/render-pages.ts [--chapter ch07]
 * 幂等:输出与磁盘一致时不写盘。
 * 日常看站直接开 index.html,或双击 启动学习站.command。内容 JSON 变了才需要重跑。
 * bun run build:content 结束时会自动调用本脚本。
 */
import { existsSync, mkdirSync, readFileSync, readdirSync, unlinkSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";

const ROOT = resolve(import.meta.dir, "..");
const CONTENT_DIR = join(ROOT, "src", "content");
const CHAPTERS_DIR = join(CONTENT_DIR, "chapters");

type ChapterSummary = { id: string; num: string; title: string; runMode: string };
type Module = {
  id: string;
  title: string;
  subtitle: string;
  dir: string;
  available: boolean;
  chapters: ChapterSummary[];
};
type Section = { id: string; heading: string };

function embedJson(value: unknown): string {
  return JSON.stringify(value).replace(/</g, "\\u003c");
}

function writeIfChanged(path: string, content: string, emitted: string[]): void {
  if (existsSync(path) && readFileSync(path, "utf8") === content) return;
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, content, "utf8");
  emitted.push(path.slice(ROOT.length + 1));
}

function parseChapterArg(): string | undefined {
  const argv = process.argv.slice(2);
  const i = argv.indexOf("--chapter");
  if (i !== -1) return argv[i + 1];
  const eq = argv.find((a) => a.startsWith("--chapter="));
  return eq ? eq.split("=")[1] : undefined;
}

function bootScripts(): string {
  return `    <script>
      try {
        var t = localStorage.getItem("py-theme");
        document.documentElement.setAttribute("data-theme", t === "dracula" ? "dracula" : "parchment");
        var z = parseFloat(localStorage.getItem("py-learn:ui-zoom:v1") || "");
        if (z >= 0.75 && z <= 1.75) document.documentElement.style.zoom = String(z);
      } catch (e) {
        document.documentElement.setAttribute("data-theme", "parchment");
      }
    </script>`;
}

function chrome(siteRoot: string, navActive: boolean): string {
  const mapClass = navActive ? "nav-link active" : "nav-link";
  return `    <header class="topbar">
      <div class="topbar-inner">
        <a class="brand" href="${siteRoot}index.html"><span class="brand-logo">🐍</span><span>Python 全栈学习</span></a>
        <div data-header-progress></div>
        <nav class="topnav">
          <a class="${mapClass}" href="${siteRoot}index.html">课程地图</a>
          <a class="nav-link" href="https://docs.python.org/3/" target="_blank" rel="noreferrer">Python 文档 ↗</a>
          <div class="theme-toggle" data-theme-toggle role="group" aria-label="主题切换">
            <button type="button" data-theme-value="parchment" title="护眼米色" aria-pressed="false">☀️<span class="tt-text">护眼</span></button>
            <button type="button" data-theme-value="dracula" title="德古拉深色" aria-pressed="false">🌙<span class="tt-text">德古拉</span></button>
          </div>
          <div class="zoom-control" role="group" aria-label="界面缩放">
            <button type="button" data-zoom="out" title="缩小 (⌘− / 触控板捏合)" aria-label="缩小界面">−</button>
            <button type="button" data-zoom="reset" data-zoom-label title="重置 (⌘0)" aria-label="重置缩放">100%</button>
            <button type="button" data-zoom="in" title="放大 (⌘+ / 触控板张开)" aria-label="放大界面">+</button>
          </div>
        </nav>
      </div>
    </header>`;
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function page(opts: {
  title: string;
  siteRoot: string;
  navActive: boolean;
  main: string;
  headExtra?: string;
  bodyScripts: string;
}): string {
  return `<!doctype html>
<html lang="zh-CN" data-theme="parchment">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>${escapeHtml(opts.title)}</title>
    <link rel="stylesheet" href="${opts.siteRoot}assets/css/style.css" />
${bootScripts()}
${opts.headExtra ?? ""}
  </head>
  <body>
${chrome(opts.siteRoot, opts.navActive)}

    <main class="wrap">
${opts.main}
    </main>

    <footer class="site-footer">Python 全栈学习 · 教程只读 · 作业在仓库里写</footer>

    <script>window.SITE_ROOT = "${opts.siteRoot}";</script>
${opts.bodyScripts}
  </body>
</html>
`;
}

const SHELL_SCRIPTS = [
  "assets/js/data.js",
  "assets/js/dom.js",
  "assets/js/learner-state.js",
  "assets/js/app-common.js",
];

const CHAPTER_SCRIPTS = [
  ...SHELL_SCRIPTS.slice(0, 1),
  "assets/js/vendor/marked.umd.js",
  "assets/js/vendor/hljs.common.min.js",
  ...SHELL_SCRIPTS.slice(1),
  "assets/js/diagrams.js",
  "assets/js/markdown.js",
  "assets/js/chapter.js",
];

function scriptTags(siteRoot: string, srcs: string[]): string {
  return srcs.map((src) => `    <script src="${siteRoot}${src}"></script>`).join("\n");
}

function removeStale(dir: string, keep: Set<string>): string[] {
  if (!existsSync(dir)) return [];
  const removed: string[] = [];
  for (const name of readdirSync(dir)) {
    if (!name.endsWith(".html")) continue;
    if (keep.has(name)) continue;
    unlinkSync(join(dir, name));
    removed.push(name);
  }
  return removed;
}

function main(): void {
  const onlyChapter = parseChapterArg();
  const index = JSON.parse(readFileSync(join(CONTENT_DIR, "index.json"), "utf8")) as { modules: Module[] };
  const generatedIds = readdirSync(CHAPTERS_DIR)
    .filter((f) => /^ch\d+\.json$/.test(f))
    .map((f) => f.replace(/\.json$/, ""))
    .sort();
  const generatedSet = new Set(generatedIds);
  const flat: Array<ChapterSummary & { module: Module }> = index.modules.flatMap((m) =>
    m.chapters.map((c) => ({ ...c, module: m })),
  );
  const emitted: string[] = [];

  if (!onlyChapter) {
    const dataJs =
      "/* 由 scripts/render-pages.ts 生成;课程索引 + 已生成章节清单 */\n" +
      `window.PY_LEARN = { index: ${embedJson(index)}, generated: ${embedJson(generatedIds)} };\n`;
    writeIfChanged(join(ROOT, "assets", "js", "data.js"), dataJs, emitted);

    writeIfChanged(
      join(ROOT, "index.html"),
      page({
        title: "Python 全栈学习",
        siteRoot: "./",
        navActive: true,
        main: `      <div id="page-root"></div>`,
        bodyScripts: scriptTags("./", [...SHELL_SCRIPTS, "assets/js/index.js"]),
      }),
      emitted,
    );

    const moduleKeep = new Set<string>();
    for (const mod of index.modules) {
      moduleKeep.add(`${mod.id}.html`);
      writeIfChanged(
        join(ROOT, "modules", `${mod.id}.html`),
        page({
          title: `${mod.title} — Python 全栈学习`,
          siteRoot: "../",
          navActive: false,
          main: `      <div id="page-root" data-module-id="${mod.id}"></div>`,
          bodyScripts: scriptTags("../", [...SHELL_SCRIPTS, "assets/js/module.js"]),
        }),
        emitted,
      );
    }
    for (const name of removeStale(join(ROOT, "modules"), moduleKeep)) {
      emitted.push(`modules/${name} (删除)`);
    }
  }

  const chapterKeep = new Set(flat.filter((c) => generatedSet.has(c.id)).map((c) => `${c.id}.html`));
  for (const summary of flat) {
    if (!generatedSet.has(summary.id)) continue;
    if (onlyChapter && summary.id !== onlyChapter) continue;

    const full = JSON.parse(readFileSync(join(CHAPTERS_DIR, `${summary.id}.json`), "utf8")) as {
      id: string;
      num: string;
      title: string;
      runMode: string;
      tutorialMd: string;
      reviewMd: string;
      sections: Section[];
    };
    const pos = flat.findIndex((c) => c.id === summary.id);
    const prev = pos > 0 ? flat[pos - 1] : null;
    const next = pos >= 0 && pos < flat.length - 1 ? flat[pos + 1] : null;
    const payload = {
      id: full.id,
      num: full.num,
      title: full.title,
      runMode: full.runMode,
      moduleId: summary.module.id,
      moduleTitle: summary.module.title,
      moduleDir: summary.module.dir,
      tutorialMd: full.tutorialMd,
      reviewMd: full.reviewMd,
      toc: (full.sections || [])
        .filter((s) => s.heading && s.heading.trim())
        .map((s) => ({ id: s.id, heading: s.heading })),
    };
    const nav = {
      prev: prev ? { id: prev.id, num: prev.num, title: prev.title } : null,
      next: next ? { id: next.id, num: next.num, title: next.title } : null,
    };

    writeIfChanged(
      join(ROOT, "chapters", `${summary.id}.html`),
      page({
        title: `Ch${full.num} · ${full.title} — Python 全栈学习`,
        siteRoot: "../",
        navActive: false,
        main: `      <div id="page-root"></div>`,
        headExtra: "",
        bodyScripts:
          `    <script type="application/json" id="chapter-data">${embedJson(payload)}</script>\n` +
          `    <script type="application/json" id="chapter-nav">${embedJson(nav)}</script>\n` +
          scriptTags("../", CHAPTER_SCRIPTS),
      }),
      emitted,
    );
  }

  if (!onlyChapter) {
    for (const name of removeStale(join(ROOT, "chapters"), chapterKeep)) {
      emitted.push(`chapters/${name} (删除)`);
    }
  }

  const target = onlyChapter ? ` (仅 ${onlyChapter})` : "";
  if (emitted.length) {
    console.log(`render-pages: 写出 ${emitted.length} 个文件${target}`);
    for (const f of emitted) console.log(`  ${f}`);
  } else {
    console.log(`render-pages: 全部最新,无需写盘${target}`);
  }
}

main();
