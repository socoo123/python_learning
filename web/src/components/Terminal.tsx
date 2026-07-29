type Status = "idle" | "loading" | "running" | "passed" | "failed" | "error";

const BORDER: Record<Status, string> = {
  idle: "border-border-subtle",
  loading: "border-drac-orange/40",
  running: "border-drac-orange/40",
  passed: "border-drac-green/40",
  failed: "border-drac-red/40",
  error: "border-drac-red/40",
};

const PILL: Record<Status, { text: string; cls: string }> = {
  idle: { text: "待运行", cls: "bg-bg-elev text-zinc-400" },
  loading: { text: "加载 Pyodide…", cls: "bg-drac-orange/15 text-drac-orange" },
  running: { text: "运行中…", cls: "bg-drac-orange/15 text-drac-orange" },
  passed: { text: "✅ 全绿", cls: "bg-drac-green/15 text-drac-green" },
  failed: { text: "❌ 有失败", cls: "bg-drac-red/15 text-drac-red" },
  error: { text: "⚠️ 出错", cls: "bg-drac-red/15 text-drac-red" },
};

export default function Terminal({ output, status }: { output: string; status: Status }) {
  const pill = PILL[status];
  return (
    <div className={`overflow-hidden rounded-lg border ${BORDER[status]} bg-[#21222c]`}>
      <div className="flex items-center gap-2 border-b border-border-subtle px-4 py-2">
        <span className="h-2.5 w-2.5 rounded-full bg-drac-red/80" />
        <span className="h-2.5 w-2.5 rounded-full bg-drac-orange/80" />
        <span className="h-2.5 w-2.5 rounded-full bg-drac-green/80" />
        <span className="ml-2 text-xs text-zinc-500">pytest 输出</span>
        <span className={`ml-auto rounded-full px-2 py-0.5 text-xs font-medium ${pill.cls}`}>{pill.text}</span>
      </div>
      <pre className="terminal-output max-h-80 overflow-auto p-4 text-drac-fg">
        {output || "点击「▶ 运行测试」查看结果。"}
      </pre>
    </div>
  );
}
