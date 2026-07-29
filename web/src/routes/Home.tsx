import ModuleCard from "../components/ModuleCard";
import { modules } from "../data/curriculum";

export default function Home() {
  const available = modules.filter((m) => m.available).length;
  const totalChapters = modules.reduce((n, m) => n + m.chapters.length, 0);

  return (
    <div className="space-y-12">
      <section className="relative overflow-hidden rounded-2xl border border-border-subtle bg-gradient-to-b from-bg-card to-bg-base p-8 sm:p-12">
        <div className="absolute right-6 top-6 select-none text-7xl opacity-10">🐍</div>
        <p className="text-sm font-medium text-accent">交互式 Python 课程</p>
        <h1 className="mt-2 max-w-2xl text-3xl font-bold leading-tight text-zinc-50 sm:text-4xl">
          从 Java 老手到 Python 全栈
          <span className="text-accent"> · 浏览器内写代码、跑测试</span>
        </h1>
        <p className="mt-4 max-w-2xl text-zinc-400">
          40 章 / 6 大模块。点开模块看每节课的教程,直接在网页里写作业、点运行看 pytest 红绿。
          纯 Python 章节浏览器内即时跑;依赖系统的章节给出本地运行命令。
        </p>
        <div className="mt-6 flex flex-wrap gap-6 text-sm">
          <Stat label="模块" value={`${available} / ${modules.length}`} />
          <Stat label="已就绪章节" value={`${totalChapters}`} />
          <Stat label="运行方式" value="Pyodide · 浏览器内" />
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-lg font-semibold text-zinc-200">课程地图</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {modules.map((m, i) => (
            <ModuleCard key={m.id} module={m} index={i} />
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-lg font-semibold text-zinc-200">怎么学</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <Step n="1" title="读教程" desc="每节教程对比 Java 讲透,讲过的才考。" />
          <Step n="2" title="写作业" desc="网页编辑器里填实现,点「运行测试」。" />
          <Step n="3" title="看红绿" desc="pytest 即时反馈,全绿即掌握,存闪卡。" />
        </div>
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xl font-bold text-zinc-100">{value}</div>
      <div className="text-xs text-zinc-500">{label}</div>
    </div>
  );
}

function Step({ n, title, desc }: { n: string; title: string; desc: string }) {
  return (
    <div className="rounded-xl border border-border-subtle bg-bg-card p-5">
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent/15 text-sm font-bold text-accent">
        {n}
      </div>
      <h3 className="mt-3 font-semibold text-zinc-100">{title}</h3>
      <p className="mt-1 text-sm text-zinc-400">{desc}</p>
    </div>
  );
}
