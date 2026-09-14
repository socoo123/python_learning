import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getChapterSummary, getModule, loadChapter } from "../data/curriculum";
import type { Chapter } from "../types";
import MarkdownView from "../components/MarkdownView";
import Flashcards from "../components/Flashcards";
import ChapterCompleteToggle from "../components/ChapterCompleteToggle";
import ChapterToc from "../components/ChapterToc";
import { useLearnerProgress } from "../hooks/useLearnerProgress";

export default function ChapterPage() {
  const { moduleId, chapterId } = useParams();
  const module = moduleId ? getModule(moduleId) : undefined;
  const summary = moduleId && chapterId ? getChapterSummary(moduleId, chapterId) : undefined;
  const { isComplete } = useLearnerProgress();
  const [chapter, setChapter] = useState<Chapter | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setChapter(null);
    setLoadError(false);

    if (!summary || !chapterId) {
      setLoading(false);
      return;
    }

    setLoading(true);
    loadChapter(chapterId)
      .then((ch) => {
        if (cancelled) return;
        if (!ch) setLoadError(true);
        else setChapter(ch);
      })
      .catch(() => {
        if (!cancelled) setLoadError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [chapterId, summary]);

  if (!module || !summary) {
    return (
      <div className="rounded-lg border border-border-subtle bg-bg-card p-8 text-center text-drac-comment">
        章节不存在。<Link to="/" className="text-accent">返回首页</Link>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="rounded-lg border border-border-subtle bg-bg-card p-8 text-center text-drac-comment">
        加载章节内容…
      </div>
    );
  }

  if (loadError || !chapter) {
    return (
      <div className="rounded-lg border border-border-subtle bg-bg-card p-8 text-center text-drac-comment">
        章节内容加载失败。<Link to={`/m/${module.id}`} className="text-accent">返回模块</Link>
      </div>
    );
  }

  const tocItems = chapter.sections.filter((s) => s.heading.trim());
  const showToc = tocItems.length >= 3;

  return (
    <div className={showToc ? "lg:grid lg:grid-cols-[18rem_minmax(0,1fr)] lg:gap-10" : undefined}>
      {showToc && <ChapterToc sections={chapter.sections} />}
      <div className="min-w-0 space-y-8">
      <nav className="text-sm text-drac-comment">
        <Link to="/" className="hover:text-drac-fg">课程地图</Link>
        <span className="mx-2">/</span>
        <Link to={`/m/${module.id}`} className="hover:text-drac-fg">{module.title}</Link>
        <span className="mx-2">/</span>
        <span className="text-drac-fg">Ch{chapter.num}</span>
      </nav>

      <header className="flex flex-wrap items-start justify-between gap-3 border-b border-border-subtle pb-5">
        <div>
          <div className="font-mono text-sm text-accent">第 {chapter.num} 课</div>
          <h1 className="mt-1 text-2xl font-bold text-drac-fg">{chapter.title}</h1>
        </div>
        {isComplete(chapter.id) && (
          <span className="rounded-full bg-drac-green/15 px-2.5 py-0.5 text-xs font-medium text-drac-green">
            ✓ 已学完
          </span>
        )}
      </header>

      <section className="space-y-3">
        <MarkdownView headingIds={tocItems.map((s) => s.id)}>{chapter.tutorialMd}</MarkdownView>
      </section>

      <AssignmentHint chapterNum={chapter.num} moduleDir={module.dir} runMode={chapter.runMode} />

      <ChapterCompleteToggle chapterId={chapter.id} />

      {chapter.reviewMd.trim() && (
        <details className="group rounded-lg border border-border-subtle bg-bg-card p-5">
          <summary className="cursor-pointer list-none text-lg font-semibold text-drac-fg">
            🧠 记忆闪卡 <span className="ml-2 text-xs font-normal text-drac-comment group-open:hidden">点开复习</span>
          </summary>
          <div className="mt-4">
            <Flashcards reviewMd={chapter.reviewMd} />
          </div>
        </details>
      )}
      </div>
    </div>
  );
}

function AssignmentHint({
  chapterNum,
  moduleDir,
  runMode,
}: {
  chapterNum: string;
  moduleDir: string;
  runMode: "pyodide" | "local";
}) {
  const file = `${moduleDir}/ch${chapterNum}/ch${chapterNum}_assignment.py`;
  const cmd = `uv run pytest ${moduleDir}/ch${chapterNum}/test_ch${chapterNum}_assignment.py -v`;
  return (
    <div className="rounded-lg border border-border-subtle bg-bg-card p-5">
      <div className="font-semibold text-drac-fg">✏️ 作业在仓库里写</div>
      <p className="mt-2 text-sm text-drac-comment">
        网页只读教程。实现写在五件套的 assignment 文件里，用 pytest 验证。
        {runMode === "local" ? " 本章依赖系统/网络库，先按模块 README 做 uv sync --extra。" : ""}
      </p>
      <p className="mt-3 text-sm text-drac-fg">
        打开 <code className="rounded bg-bg-elev px-1.5 py-0.5 text-accent">{file}</code>
      </p>
      <div className="mt-2 flex items-center gap-2 rounded-md border border-border-subtle bg-bg-base p-3">
        <code className="flex-1 font-mono text-xs text-drac-fg">{cmd}</code>
        <CopyButton text={cmd} />
      </div>
    </div>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      onClick={() =>
        navigator.clipboard?.writeText(text).then(() => {
          setCopied(true);
          setTimeout(() => setCopied(false), 1500);
        })
      }
      className="rounded border border-border-subtle px-2 py-1 text-xs text-drac-fg hover:bg-bg-elev"
    >
      {copied ? "已复制 ✓" : "复制"}
    </button>
  );
}
