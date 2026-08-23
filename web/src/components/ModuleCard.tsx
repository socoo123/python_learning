import { Link } from "react-router-dom";
import type { Module } from "../types";
import { useLearnerProgress } from "../hooks/useLearnerProgress";
import ProgressBar from "./ProgressBar";

export default function ModuleCard({ module, index }: { module: Module; index: number }) {
  const enabled = module.available;
  const { moduleDone } = useLearnerProgress();
  const { done, total } = moduleDone(module.id);

  const inner = (
    <div
      className={`group relative h-full overflow-hidden rounded-xl border p-5 transition ${
        enabled
          ? "border-border-subtle bg-bg-card hover:border-accent/50 hover:bg-bg-elev"
          : "border-border-subtle/50 bg-bg-card/40 opacity-60"
      }`}
    >
      <div className="flex items-start justify-between">
        <span className="text-3xl font-bold text-border-strong">{String(index + 1).padStart(2, "0")}</span>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${
            !enabled
              ? "bg-bg-elev text-drac-comment"
              : done === total && total > 0
                ? "bg-drac-green/15 text-drac-green"
                : "bg-accent/15 text-accent"
          }`}
        >
          {!enabled ? "待生成" : done === total && total > 0 ? "已学完" : "可学习"}
        </span>
      </div>
      <h3 className="mt-4 text-lg font-semibold text-drac-fg">{module.title}</h3>
      <p className="mt-1 text-sm text-drac-comment">{module.subtitle}</p>
      <div className="mt-4 space-y-2">
        {enabled && total > 0 && (
          <ProgressBar value={done} max={total} size="sm" label="已学" />
        )}
        <div className="flex items-center gap-2 text-xs text-drac-comment">
          {!enabled && <span>{module.chapters.length} 章</span>}
          {enabled && (
            <span className="ml-auto text-accent opacity-0 transition group-hover:opacity-100">进入 →</span>
          )}
        </div>
      </div>
    </div>
  );

  if (!enabled) return <div className="cursor-not-allowed">{inner}</div>;
  return <Link to={`/m/${module.id}`} className="block h-full">{inner}</Link>;
}
