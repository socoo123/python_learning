import { Routes, Route, Link, NavLink } from "react-router-dom";
import Home from "./routes/Home";
import ModulePage from "./routes/ModulePage";
import ChapterPage from "./routes/ChapterPage";
import { useTheme } from "./hooks/useTheme";
import { useLearnerProgress } from "./hooks/useLearnerProgress";
import { useUiZoom } from "./hooks/useUiZoom";
import { ZOOM_MAX, ZOOM_MIN } from "./lib/uiZoom";
import ProgressBar from "./components/ProgressBar";

function ZoomControl() {
  const { zoom, zoomIn, zoomOut, reset } = useUiZoom();
  const btn =
    "px-2 py-1 text-xs text-drac-comment hover:text-drac-fg disabled:cursor-default disabled:opacity-40";
  return (
    <div
      className="inline-flex items-center rounded-lg border border-border-subtle bg-bg-card p-0.5 font-mono"
      role="group"
      aria-label="界面缩放"
    >
      <button
        type="button"
        title="缩小 (⌘− / 触控板捏合)"
        aria-label="缩小界面"
        onClick={zoomOut}
        disabled={zoom <= ZOOM_MIN}
        className={btn}
      >
        −
      </button>
      <button
        type="button"
        title="重置 (⌘0)"
        aria-label="重置缩放"
        onClick={reset}
        className="w-11 text-center text-[11px] text-drac-comment hover:text-drac-fg"
      >
        {Math.round(zoom * 100)}%
      </button>
      <button
        type="button"
        title="放大 (⌘+ / 触控板张开)"
        aria-label="放大界面"
        onClick={zoomIn}
        disabled={zoom >= ZOOM_MAX}
        className={btn}
      >
        +
      </button>
    </div>
  );
}

function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const btn = (active: boolean) =>
    `inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs transition ${
      active ? "bg-accent/15 font-medium text-accent" : "text-drac-comment hover:text-drac-fg"
    }`;
  return (
    <div
      className="inline-flex items-center rounded-lg border border-border-subtle bg-bg-card p-0.5"
      role="group"
      aria-label="主题切换"
    >
      <button
        type="button"
        title="护眼米色"
        aria-pressed={theme === "parchment"}
        onClick={() => setTheme("parchment")}
        className={btn(theme === "parchment")}
      >
        ☀️<span className="hidden sm:inline">护眼</span>
      </button>
      <button
        type="button"
        title="德古拉深色"
        aria-pressed={theme === "dracula"}
        onClick={() => setTheme("dracula")}
        className={btn(theme === "dracula")}
      >
        🌙<span className="hidden sm:inline">德古拉</span>
      </button>
    </div>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-bg-base text-drac-fg">
      <header className="sticky top-0 z-20 border-b border-border-subtle bg-bg-base/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-4 px-6 py-3">
          <Link to="/" className="flex items-center gap-2 font-semibold text-drac-fg">
            <span className="text-accent">🐍</span>
            <span>Python 全栈学习</span>
          </Link>
          <HeaderProgress />
          <nav className="ml-auto flex items-center gap-1 text-sm">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `rounded-md px-3 py-1.5 ${isActive ? "bg-bg-elev text-drac-fg" : "text-drac-comment hover:text-drac-fg"}`
              }
            >
              课程地图
            </NavLink>
            <a
              href="https://docs.python.org/3/"
              target="_blank"
              rel="noreferrer"
              className="rounded-md px-3 py-1.5 text-drac-comment hover:text-drac-fg"
            >
              Python 文档 ↗
            </a>
            <ThemeToggle />
            <ZoomControl />
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/m/:moduleId" element={<ModulePage />} />
          <Route path="/m/:moduleId/:chapterId" element={<ChapterPage />} />
        </Routes>
      </main>

      <footer className="mx-auto max-w-6xl px-6 py-10 text-center text-xs text-drac-comment">
        Python 全栈学习 · 教程只读 · 作业在仓库里写
      </footer>
    </div>
  );
}

function HeaderProgress() {
  const { completedCount, totalChapters } = useLearnerProgress();
  if (totalChapters <= 0) return null;
  return (
    <Link
      to="/"
      className="hidden min-w-0 max-w-[14rem] flex-1 sm:block"
      title={`已学 ${completedCount} / ${totalChapters} 章`}
    >
      <div className="mb-1 font-mono text-[11px] text-drac-comment">
        进度 {completedCount}/{totalChapters}
      </div>
      <ProgressBar value={completedCount} max={totalChapters} size="sm" />
    </Link>
  );
}
