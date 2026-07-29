import type { RunMode } from "../types";

export default function RunModeBadge({ mode }: { mode: RunMode }) {
  if (mode === "pyodide") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-drac-green/30 bg-drac-green/10 px-2 py-0.5 text-xs font-medium text-drac-green">
        🟢 浏览器运行
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-drac-orange/30 bg-drac-orange/10 px-2 py-0.5 text-xs font-medium text-drac-orange">
      🔒 本地运行
    </span>
  );
}
