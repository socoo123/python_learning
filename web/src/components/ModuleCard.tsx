import { Link } from "react-router-dom";
import type { Module } from "../types";

export default function ModuleCard({ module, index }: { module: Module; index: number }) {
  const enabled = module.available;
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
            enabled ? "bg-emerald-500/15 text-emerald-400" : "bg-bg-elev text-zinc-500"
          }`}
        >
          {enabled ? "可学习" : "待生成"}
        </span>
      </div>
      <h3 className="mt-4 text-lg font-semibold text-zinc-100">{module.title}</h3>
      <p className="mt-1 text-sm text-zinc-400">{module.subtitle}</p>
      <div className="mt-4 flex items-center gap-2 text-xs text-zinc-500">
        <span>{module.chapters.length} 章</span>
        {enabled && (
          <span className="ml-auto text-accent opacity-0 transition group-hover:opacity-100">进入 →</span>
        )}
      </div>
    </div>
  );

  if (!enabled) return <div className="cursor-not-allowed">{inner}</div>;
  return <Link to={`/m/${module.id}`} className="block h-full">{inner}</Link>;
}
