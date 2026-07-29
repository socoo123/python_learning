import { Routes, Route, Link, NavLink } from "react-router-dom";
import Home from "./routes/Home";
import ModulePage from "./routes/ModulePage";
import ChapterPage from "./routes/ChapterPage";

export default function App() {
  return (
    <div className="min-h-screen bg-bg-base text-zinc-200">
      <header className="sticky top-0 z-20 border-b border-border-subtle/70 bg-bg-base/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-4 px-6 py-3">
          <Link to="/" className="flex items-center gap-2 font-semibold text-zinc-100">
            <span className="text-accent">🐍</span>
            <span>Python 全栈学习</span>
          </Link>
          <nav className="ml-auto flex items-center gap-1 text-sm">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `rounded-md px-3 py-1.5 ${isActive ? "bg-bg-elev text-zinc-100" : "text-zinc-400 hover:text-zinc-200"}`
              }
            >
              课程地图
            </NavLink>
            <a
              href="https://docs.python.org/3/"
              target="_blank"
              rel="noreferrer"
              className="rounded-md px-3 py-1.5 text-zinc-400 hover:text-zinc-200"
            >
              Python 文档 ↗
            </a>
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

      <footer className="mx-auto max-w-6xl px-6 py-10 text-center text-xs text-zinc-600">
        Python 全栈学习 · 交互式课程 · 浏览器内运行(Pyodide)
      </footer>
    </div>
  );
}
