import { useState } from "react";
import Editor from "@monaco-editor/react";
import type { Chapter, FuncDef, SharedContent } from "../types";
import { getPyodide, runFunctionTest } from "../lib/pyodide";
import { defineDracula } from "../lib/monaco";
import Terminal from "./Terminal";

type Status = "idle" | "loading" | "running" | "passed" | "failed" | "error";

interface Props {
  chapter: Chapter;
  shared: SharedContent;
  func: FuncDef;
  pyReady: boolean;
  onPyReady: () => void;
}

export default function ExerciseRunner({ chapter, shared, func, pyReady, onPyReady }: Props) {
  const [code, setCode] = useState(func.skeleton);
  const [output, setOutput] = useState("");
  const [status, setStatus] = useState<Status>("idle");

  async function handleRun() {
    try {
      if (!pyReady) {
        setStatus("loading");
        setOutput("⏳ 正在加载 Pyodide(首次约 10MB,请稍候)…\n");
        await getPyodide();
        onPyReady();
      }
      setStatus("running");
      setOutput((o) => o + `▶ 运行 ${func.name} 的测试…\n\n`);
      const res = await runFunctionTest({
        testName: chapter.testName,
        testSource: chapter.testSource,
        conftestSource: shared.conftest,
        mocks: shared.mocks,
        preamble: chapter.preamble,
        functions: chapter.functions,
        activeFunction: func.name,
        userCode: code,
        testClass: func.testClass,
      });
      setOutput(res.output || "(无输出)");
      setStatus(res.returncode === 0 ? "passed" : "failed");
    } catch (e) {
      setOutput((o) => o + "\n❌ " + (e instanceof Error ? e.message : String(e)));
      setStatus("error");
    }
  }

  function handleReset() {
    setCode(func.skeleton);
    setOutput("");
    setStatus("idle");
  }

  const busy = status === "loading" || status === "running";

  // 按初始内容行数自适应高度:短题也给够空间,只有特别长的才滚动
  const editorHeight = Math.min(620, Math.max(300, func.skeleton.split("\n").length * 20 + 28));

  return (
    <div className="my-4 rounded-lg border border-border-subtle bg-bg-card p-3">
      <div className="mb-2 flex items-center gap-2">
        <span className="rounded bg-drac-pink/15 px-2 py-0.5 font-mono text-xs text-drac-pink">
          ✏️ {func.name}()
        </span>
        <button
          onClick={handleRun}
          disabled={busy}
          className="ml-auto rounded-md bg-accent px-3 py-1.5 text-xs font-semibold text-drac-bg transition hover:brightness-110 disabled:opacity-60"
        >
          {busy ? "运行中…" : "▶ 运行测试"}
        </button>
        <button
          onClick={handleReset}
          disabled={busy}
          className="rounded-md border border-border-subtle px-2 py-1.5 text-xs text-zinc-300 hover:bg-bg-elev disabled:opacity-50"
        >
          ↺ 重置
        </button>
      </div>
      <div className="overflow-hidden rounded-md border border-border-subtle">
        <Editor
          height={editorHeight}
          defaultLanguage="python"
          theme="dracula"
          beforeMount={defineDracula}
          value={code}
          onChange={(v) => setCode(v ?? "")}
          options={{
            fontSize: 13,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            tabSize: 4,
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
            lineNumbers: "on",
            automaticLayout: true,
          }}
        />
      </div>
      <div className="mt-2">
        <Terminal output={output} status={status} />
      </div>
    </div>
  );
}
