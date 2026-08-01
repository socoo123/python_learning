import { useState } from "react";
import Editor from "@monaco-editor/react";
import type { Chapter, SharedContent } from "../types";
import { getPyodide, runChapterTests, type RunResult } from "../lib/pyodide";
import { defineDracula } from "../lib/monaco";
import Terminal from "./Terminal";

type Status = "idle" | "loading" | "running" | "passed" | "failed" | "error";

interface Props {
  chapter: Chapter;
  shared: SharedContent;
}

export default function CodeRunner({ chapter, shared }: Props) {
  const [code, setCode] = useState(chapter.assignment);
  const [output, setOutput] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [pyReady, setPyReady] = useState(false);

  async function handleRun() {
    try {
      if (!pyReady) {
        setStatus("loading");
        setOutput("⏳ 正在加载 Pyodide(首次约 10MB,请稍候)…\n");
        await getPyodide();
        setPyReady(true);
      }
      setStatus("running");
      setOutput((o) => o + "▶ 运行测试中…\n\n");
      const res: RunResult = await runChapterTests({
        assignmentCode: code,
        testName: chapter.testName,
        testSource: chapter.testSource,
        conftestSource: shared.conftest,
        mocks: shared.mocks,
      });
      setOutput(res.output || "(无输出)");
      setStatus(res.returncode === 0 ? "passed" : "failed");
    } catch (e) {
      setOutput((o) => o + "\n❌ " + (e instanceof Error ? e.message : String(e)));
      setStatus("error");
    }
  }

  function handleReset() {
    setCode(chapter.assignment);
    setOutput("");
    setStatus("idle");
  }

  const busy = status === "loading" || status === "running";

  // 按内容行数自适应:整章作业通常较长,给足高度,超长才滚动
  const editorHeight = Math.min(680, Math.max(360, chapter.assignment.split("\n").length * 20 + 28));

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={handleRun}
          disabled={busy}
          className="inline-flex items-center gap-1.5 rounded-md bg-accent px-4 py-2 text-sm font-semibold text-bg-base shadow-sm transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {busy ? "运行中…" : "▶ 运行测试"}
        </button>
        <button
          onClick={handleReset}
          disabled={busy}
          className="inline-flex items-center gap-1.5 rounded-md border border-border-subtle bg-bg-card px-3 py-2 text-sm text-zinc-300 transition hover:bg-bg-elev disabled:opacity-50"
        >
          ↺ 重置
        </button>
        <span className="ml-auto font-mono text-xs text-zinc-500">{chapter.testName}.py</span>
      </div>

      <div className="overflow-hidden rounded-lg border border-border-subtle">
        <Editor
          height={editorHeight}
          defaultLanguage="python"
          theme="dracula"
          beforeMount={defineDracula}
          value={code}
          onChange={(v) => setCode(v ?? "")}
          options={{
            fontSize: 13.5,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            tabSize: 4,
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
            lineNumbers: "on",
            renderLineHighlight: "line",
            automaticLayout: true,
          }}
        />
      </div>

      <Terminal output={output} status={status} />
    </div>
  );
}
