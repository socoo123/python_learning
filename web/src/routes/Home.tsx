import ModuleCard from "../components/ModuleCard";
import ProgressBar from "../components/ProgressBar";
import { modules } from "../data/curriculum";
import { useLearnerProgress } from "../hooks/useLearnerProgress";
import { LEARNER_FILE_HINT } from "../lib/learnerState";

export default function Home() {
  const available = modules.filter((m) => m.available).length;
  const { completedCount, totalChapters, persistence } = useLearnerProgress();

  return (
    <div className="space-y-12">
      <section className="relative overflow-hidden rounded-2xl border border-border-subtle bg-gradient-to-b from-bg-card to-bg-base p-8 sm:p-12">
        <div className="absolute right-6 top-6 select-none text-7xl opacity-10">🐍</div>
        <p className="text-sm font-medium text-accent">Python 全栈课程</p>
        <h1 className="mt-2 max-w-2xl text-3xl font-bold leading-tight text-drac-fg sm:text-4xl">
          从 Java 老手到 Python 全栈
          <span className="text-accent"> · 网页读教程，仓库写作业</span>
        </h1>
        <p className="mt-4 max-w-2xl text-drac-comment">
          40 章 / 6 大模块。网页只展示教程和闪卡；作业在仓库五件套里写，用 uv pytest 验证。
        </p>
        <div className="mt-6 flex flex-wrap gap-6 text-sm">
          <Stat label="模块" value={`${available} / ${modules.length}`} />
          <Stat label="已学章节" value={`${completedCount} / ${totalChapters}`} />
          <Stat label="作业" value="本地 pytest" />
        </div>
        <div className="mt-6 max-w-xl">
          <ProgressBar
            value={completedCount}
            max={totalChapters}
            label="总进度"
          />
          <p className="mt-2 text-xs text-drac-comment">
            {persistence === "file"
              ? `学习进度写入 ${LEARNER_FILE_HINT}，刷新不会丢。`
              : "进度存在本机浏览器；用 bun run dev 打开时会额外写入本地文件。"}
          </p>
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-lg font-semibold text-drac-fg">课程地图</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {modules.map((m, i) => (
            <ModuleCard key={m.id} module={m} index={i} />
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-lg font-semibold text-drac-fg">怎么学</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <Step n="1" title="读教程" desc="每节教程对比 Java 讲透,讲过的才考。" />
          <Step n="2" title="写作业" desc="在仓库 assignment 文件里填实现,不要在网页里写。" />
          <Step n="3" title="跑测试" desc="uv run pytest 全绿即掌握,再勾选「已学完」。" />
        </div>
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xl font-bold text-drac-fg">{value}</div>
      <div className="text-xs text-drac-comment">{label}</div>
    </div>
  );
}

function Step({ n, title, desc }: { n: string; title: string; desc: string }) {
  return (
    <div className="rounded-xl border border-border-subtle bg-bg-card p-5">
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent/15 text-sm font-bold text-accent">
        {n}
      </div>
      <h3 className="mt-3 font-semibold text-drac-fg">{title}</h3>
      <p className="mt-1 text-sm text-drac-comment">{desc}</p>
    </div>
  );
}
