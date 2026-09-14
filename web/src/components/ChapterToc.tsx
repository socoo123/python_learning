import type { Section } from "../types";

/**
 * 课程页左侧目录(参照 system_design_web 的 ChapterToc)。
 * 注意:本站是 HashRouter,`href="#id"` 会打断路由,锚点跳转用 JS 平滑滚动实现。
 */
export default function ChapterToc({ sections }: { sections: Section[] }) {
  const items = sections.filter((s) => s.heading.trim());
  if (items.length < 3) return null;

  const jump = (e: React.MouseEvent<HTMLAnchorElement>, id: string) => {
    e.preventDefault();
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <nav
      aria-label="目录"
      className="hidden lg:block lg:sticky lg:top-24 lg:max-h-[calc(100vh-8rem)] lg:overflow-y-auto lg:pr-2"
    >
      <div className="text-xs font-semibold uppercase tracking-wide text-drac-comment">目录</div>
      <ol className="mt-4 space-y-2.5 border-r border-border-subtle pr-4 text-[15px]">
        {items.map((s) => (
          <li key={s.id}>
            <a
              href={`#${s.id}`}
              onClick={(e) => jump(e, s.id)}
              className="block leading-relaxed text-drac-comment transition-colors hover:text-accent"
            >
              {s.heading.replace(/^#+\s*/, "")}
            </a>
          </li>
        ))}
      </ol>
    </nav>
  );
}
