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

export default function MarkdownView({ children }: { children: string }) {
  return (
    <div className="tutorial">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[[rehypeHighlight, { detect: true, ignoreMissing: true }]]}
        components={{
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
