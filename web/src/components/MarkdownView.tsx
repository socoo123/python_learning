import { Children, isValidElement, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import MermaidBlock from "./MermaidBlock";

function mermaidSource(children: ReactNode): string | null {
  for (const child of Children.toArray(children)) {
    if (!isValidElement<{ className?: string; children?: ReactNode }>(child)) continue;
    const cls = child.props.className ?? "";
    if (!cls.includes("language-mermaid")) continue;
    return String(child.props.children ?? "").replace(/\n$/, "");
  }
  return null;
}

export default function MarkdownView({
  children,
  headingIds,
}: {
  children: string;
  /** 与正文 `## ` 标题一一对应的锚点 id(按出现顺序);h2 依次取用,配左侧目录跳转 */
  headingIds?: string[];
}) {
  // 每次渲染重建 components → 计数器从 0 开始,与标题顺序对齐
  let headingIdx = 0;
  return (
    <div className="tutorial">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[[rehypeHighlight, { detect: true, ignoreMissing: true }]]}
        components={{
          h2({ children: hChildren, ...props }) {
            const id = headingIds?.[headingIdx++];
            return id ? (
              <h2 id={id} className="scroll-mt-24" {...props}>
                {hChildren}
              </h2>
            ) : (
              <h2 {...props}>{hChildren}</h2>
            );
          },
          pre({ children: preChildren }) {
            const chart = mermaidSource(preChildren);
            if (chart !== null) return <MermaidBlock chart={chart} />;
            return <pre>{preChildren}</pre>;
          },
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
