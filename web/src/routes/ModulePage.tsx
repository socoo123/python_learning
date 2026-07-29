import { Link, useParams } from "react-router-dom";
import { getModule } from "../data/curriculum";
import RunModeBadge from "../components/RunModeBadge";

export default function ModulePage() {
  const { moduleId } = useParams();
  const module = moduleId ? getModule(moduleId) : undefined;

  if (!module) {
    return (
      <div className="rounded-lg border border-border-subtle bg-bg-card p-8 text-center text-zinc-400">
        模块不存在。<Link to="/" className="text-accent">返回首页</Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <nav className="text-sm text-zinc-500">
        <Link to="/" className="hover:text-zinc-300">课程地图</Link>
        <span className="mx-2">/</span>
        <span className="text-zinc-300">{module.title}</span>
      </nav>

      <header className="border-b border-border-subtle pb-5">
        <h1 className="text-2xl font-bold text-zinc-50">{module.title}</h1>
        <p className="mt-1 text-zinc-400">{module.subtitle}</p>
      </header>

      <div className="space-y-2">
        {module.chapters.map((ch) => (
          <Link
            key={ch.id}
            to={`/m/${module.id}/${ch.id}`}
            className="group flex items-center gap-4 rounded-lg border border-border-subtle bg-bg-card p-4 transition hover:border-accent/50 hover:bg-bg-elev"
          >
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-bg-elev font-mono text-sm font-semibold text-zinc-400 group-hover:text-accent">
              {ch.num}
            </span>
            <div className="min-w-0 flex-1">
              <div className="font-medium text-zinc-100">{ch.title}</div>
            </div>
            <RunModeBadge mode={ch.runMode} />
            <span className="text-zinc-600 transition group-hover:translate-x-0.5 group-hover:text-accent">→</span>
          </Link>
        ))}
        {module.chapters.length === 0 && (
          <div className="rounded-lg border border-dashed border-border-subtle p-8 text-center text-sm text-zinc-500">
            本模块内容待生成。
          </div>
        )}
      </div>
    </div>
  );
}
