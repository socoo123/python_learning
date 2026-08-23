import { Link, useParams } from "react-router-dom";
import { getModule } from "../data/curriculum";
import ProgressBar from "../components/ProgressBar";
import { useLearnerProgress } from "../hooks/useLearnerProgress";

export default function ModulePage() {
  const { moduleId } = useParams();
  const module = moduleId ? getModule(moduleId) : undefined;
  const { moduleDone, isComplete, toggleComplete } = useLearnerProgress();

  if (!module) {
    return (
      <div className="rounded-lg border border-border-subtle bg-bg-card p-8 text-center text-drac-comment">
        模块不存在。<Link to="/" className="text-accent">返回首页</Link>
      </div>
    );
  }

  const { done, total } = moduleDone(module.id);

  return (
    <div className="space-y-6">
      <nav className="text-sm text-drac-comment">
        <Link to="/" className="hover:text-drac-fg">课程地图</Link>
        <span className="mx-2">/</span>
        <span className="text-drac-fg">{module.title}</span>
      </nav>

      <header className="border-b border-border-subtle pb-5">
        <h1 className="text-2xl font-bold text-drac-fg">{module.title}</h1>
        <p className="mt-1 text-drac-comment">{module.subtitle}</p>
        {total > 0 && (
          <div className="mt-4 max-w-md">
            <ProgressBar value={done} max={total} label="本模块进度" />
          </div>
        )}
      </header>

      <div className="space-y-2">
        {module.chapters.map((ch) => {
          const learned = isComplete(ch.id);
          return (
            <div
              key={ch.id}
              className={`flex items-center gap-3 rounded-lg border bg-bg-card p-3 transition hover:border-accent/50 hover:bg-bg-elev ${
                learned ? "border-drac-green/30" : "border-border-subtle"
              }`}
            >
              <button
                type="button"
                title={learned ? "取消已学完" : "标为已学完"}
                aria-pressed={learned}
                onClick={() => toggleComplete(ch.id)}
                className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-md border text-sm transition ${
                  learned
                    ? "border-drac-green/50 bg-drac-green/15 text-drac-green"
                    : "border-border-subtle bg-bg-elev text-drac-comment hover:border-drac-green/40 hover:text-drac-green"
                }`}
              >
                {learned ? "✓" : ""}
              </button>
              <Link
                to={`/m/${module.id}/${ch.id}`}
                className="group flex min-w-0 flex-1 items-center gap-4 py-1"
              >
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-bg-elev font-mono text-sm font-semibold text-drac-comment group-hover:text-accent">
                  {ch.num}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="font-medium text-drac-fg">{ch.title}</div>
                  {learned && <div className="text-xs text-drac-green">已学完</div>}
                </div>
                <span className="text-border-strong transition group-hover:translate-x-0.5 group-hover:text-accent">→</span>
              </Link>
            </div>
          );
        })}
        {module.chapters.length === 0 && (
          <div className="rounded-lg border border-dashed border-border-subtle p-8 text-center text-sm text-drac-comment">
            本模块内容待生成。
          </div>
        )}
      </div>
    </div>
  );
}
