import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getChapter, getModule, shared } from "../data/curriculum";
import type { Chapter, FuncDef } from "../types";
import MarkdownView from "../components/MarkdownView";
import CodeRunner from "../components/CodeRunner";
import ExerciseRunner from "../components/ExerciseRunner";
import RunModeBadge from "../components/RunModeBadge";
import Flashcards from "../components/Flashcards";

type Block = { type: "md"; text: string } | { type: "exercise"; func: FuncDef };

/** 把分节合成渲染块:连续无练习的小节合并成一段 markdown,有练习的小节单独成块后跟练习。 */
function buildBlocks(chapter: Chapter): Block[] {
  const blocks: Block[] = [];
  let mdBuf = "";
  const flush = () => {
    if (mdBuf.trim()) blocks.push({ type: "md", text: mdBuf });
    mdBuf = "";
  };
  for (const s of chapter.sections) {
    const secMd = (s.heading ? `## ${s.heading}\n\n` : "") + s.body;
    if (s.exerciseFunctions.length) {
      flush();
      blocks.push({ type: "md", text: secMd });
      for (const fname of s.exerciseFunctions) {
        const f = chapter.functions.find((x) => x.name === fname);
        if (f) blocks.push({ type: "exercise", func: f });
      }
    } else {
      mdBuf += secMd + "\n\n";
    }
  }
  flush();
  return blocks;
}

export default function ChapterPage() {
  const { moduleId, chapterId } = useParams();
  const chapter = moduleId && chapterId ? getChapter(moduleId, chapterId) : undefined;
  const module = moduleId ? getModule(moduleId) : undefined;
  const [pyReady, setPyReady] = useState(false);

  if (!chapter || !module) {
    return (
      <div className="rounded-lg border border-border-subtle bg-bg-card p-8 text-center text-zinc-400">
        章节不存在。<Link to="/" className="text-accent">返回首页</Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <nav className="text-sm text-zinc-500">
        <Link to="/" className="hover:text-zinc-300">课程地图</Link>
        <span className="mx-2">/</span>
        <Link to={`/m/${module.id}`} className="hover:text-zinc-300">{module.title}</Link>
        <span className="mx-2">/</span>
        <span className="text-zinc-300">Ch{chapter.num}</span>
      </nav>

      <header className="flex flex-wrap items-start justify-between gap-3 border-b border-border-subtle pb-5">
        <div>
          <div className="font-mono text-sm text-accent">第 {chapter.num} 课</div>
          <h1 className="mt-1 text-2xl font-bold text-zinc-50">{chapter.title}</h1>
        </div>
        <RunModeBadge mode={chapter.runMode} />
      </header>

      {/* 正文:交错式 / 回退 / 本地 */}
      {chapter.interleaved ? (
        <div className="space-y-2">
          {buildBlocks(chapter).map((b, i) =>
            b.type === "md" ? (
              <MarkdownView key={i}>{b.text}</MarkdownView>
            ) : (
              <ExerciseRunner
                key={`ex-${b.func.name}`}
                chapter={chapter}
                shared={shared}
                func={b.func}
                pyReady={pyReady}
                onPyReady={() => setPyReady(true)}
              />
            )
          )}
        </div>
      ) : (
        <>
          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-zinc-100">📖 教程</h2>
            <MarkdownView>{chapter.tutorialMd}</MarkdownView>
          </section>
          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-zinc-100">✏️ 作业</h2>
            {chapter.runMode === "pyodide" ? (
              <CodeRunner key={chapter.id} chapter={chapter} shared={shared} />
            ) : (
              <LocalNotice chapter={chapter} moduleDir={module.dir} />
            )}
          </section>
        </>
      )}

      {chapter.reviewMd.trim() && (
        <details className="group rounded-lg border border-border-subtle bg-bg-card p-5">
          <summary className="cursor-pointer list-none text-lg font-semibold text-zinc-100">
            🧠 记忆闪卡 <span className="ml-2 text-xs font-normal text-zinc-500 group-open:hidden">点开复习</span>
          </summary>
          <div className="mt-4">
            <Flashcards reviewMd={chapter.reviewMd} />
          </div>
        </details>
      )}
    </div>
  );
}

function LocalNotice({ chapter, moduleDir }: { chapter: { num: string }; moduleDir: string }) {
  const cmd = `uv run pytest ${moduleDir}/ch${chapter.num}/test_ch${chapter.num}_assignment.py -v`;
  return (
    <div className="rounded-lg border border-drac-orange/30 bg-drac-orange/5 p-6">
      <div className="font-semibold text-drac-orange">🔒 本章在本地运行</div>
      <p className="mt-3 text-sm text-zinc-300">
        这章依赖系统/网络(FastAPI、数据库、subprocess、LLM API 等),浏览器内跑不了。
        请在本地仓库写实现,然后用下面命令跑测试。报错可在终端问 Claude。
      </p>
      <ol className="mt-4 space-y-2 text-sm text-zinc-400">
        <li>① 打开 <code className="rounded bg-bg-elev px-1.5 py-0.5 text-accent">{moduleDir}/ch{chapter.num}/ch{chapter.num}_assignment.py</code> 写实现</li>
        <li>② 终端运行:</li>
      </ol>
      <div className="mt-2 flex items-center gap-2 rounded-md border border-border-subtle bg-bg-card p-3">
        <code className="flex-1 font-mono text-xs text-zinc-300">{cmd}</code>
        <CopyButton text={cmd} />
      </div>
    </div>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => navigator.clipboard?.writeText(text).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      })}
      className="rounded border border-border-subtle px-2 py-1 text-xs text-zinc-300 hover:bg-bg-elev"
    >
      {copied ? "已复制 ✓" : "复制"}
    </button>
  );
}
