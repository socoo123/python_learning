type Status = "idle" | "loading" | "running" | "passed" | "failed" | "error";

// 终端是固定深色「代码岛」,两套主题下都用 night 色板,保证输出可读性一致
const BORDER: Record<Status, string> = {
  idle: "border-night-line",
  loading: "border-night-orange/40",
  running: "border-night-orange/40",
  passed: "border-night-green/40",
  failed: "border-night-red/40",
  error: "border-night-red/40",
};

const PILL: Record<Status, { text: string; cls: string }> = {
  idle: { text: "待运行", cls: "bg-night-elev text-night-comment" },
  loading: { text: "加载 Pyodide…", cls: "bg-night-orange/15 text-night-orange" },
  running: { text: "运行中…", cls: "bg-night-orange/15 text-night-orange" },
  passed: { text: "✅ 全绿", cls: "bg-night-green/15 text-night-green" },
  failed: { text: "❌ 有失败", cls: "bg-night-red/15 text-night-red" },
  error: { text: "⚠️ 出错", cls: "bg-night-red/15 text-night-red" },
};

export default function Terminal({ output, status }: { output: string; status: Status }) {
  const pill = PILL[status];
  return (
    <div className={`overflow-hidden rounded-lg border ${BORDER[status]} bg-night-card`}>
      <div className="flex items-center gap-2 border-b border-night-line px-4 py-2">
        <span className="h-2.5 w-2.5 rounded-full bg-night-red/80" />
        <span className="h-2.5 w-2.5 rounded-full bg-night-orange/80" />
        <span className="h-2.5 w-2.5 rounded-full bg-night-green/80" />
        <span className="ml-2 text-xs text-night-comment">pytest 输出</span>
        <span className={`ml-auto rounded-full px-2 py-0.5 text-xs font-medium ${pill.cls}`}>{pill.text}</span>
      </div>
      <pre className="terminal-output max-h-80 overflow-auto p-4">
        {output || "点击「▶ 运行测试」查看结果。"}
      </pre>
    </div>
  );
}
