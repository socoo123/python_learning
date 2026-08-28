import { useEffect, useId, useRef, useState } from "react";

type MermaidApi = {
  initialize: (config: Record<string, unknown>) => void;
  render: (id: string, chart: string) => Promise<{ svg: string }>;
};

let mermaidPromise: Promise<MermaidApi> | null = null;

function loadMermaid(): Promise<MermaidApi> {
  if (!mermaidPromise) {
    mermaidPromise = import("mermaid/dist/mermaid.esm.min.mjs").then((mod) => {
      const mermaid = (mod.default ?? mod) as MermaidApi;
      mermaid.initialize({
        startOnLoad: false,
        securityLevel: "loose",
        theme: "base",
        fontFamily: "ui-sans-serif, system-ui, sans-serif",
        fontSize: 13,
        flowchart: {
          htmlLabels: true,
          useMaxWidth: true,
          nodeSpacing: 22,
          rankSpacing: 28,
          padding: 6,
          wrappingWidth: 220,
        },
        sequence: {
          useMaxWidth: true,
          actorMargin: 28,
          boxMargin: 6,
          messageMargin: 24,
          noteMargin: 8,
          actorFontSize: 13,
          messageFontSize: 13,
          noteFontSize: 12,
        },
        themeVariables: {
          fontSize: "13px",
          background: "transparent",
          primaryTextColor: "#1f1f1f",
          secondaryTextColor: "#1f1f1f",
          tertiaryTextColor: "#1f1f1f",
          lineColor: "#6b7280",
          actorBorder: "#0097A7",
          actorBkg: "#E0F7FA",
          actorTextColor: "#1f1f1f",
          signalColor: "#374151",
          signalTextColor: "#1f1f1f",
          labelBoxBkgColor: "#FFF8E1",
          labelTextColor: "#1f1f1f",
          noteBkgColor: "#FFF8E1",
          noteTextColor: "#1f1f1f",
        },
        themeCSS: [
          ".nodeLabel,.edgeLabel,.label,.actor{font-size:13px}",
          ".nodeLabel p,.edgeLabel p,.label p,.noteText p{margin:0!important;line-height:1.25!important}",
          "foreignObject{overflow:visible}",
        ].join(""),
      });
      return mermaid;
    });
  }
  return mermaidPromise;
}

export default function MermaidBlock({ chart }: { chart: string }) {
  const reactId = useId().replace(/[^a-zA-Z0-9]/g, "");
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const renderId = `mmd${reactId}${Math.random().toString(36).slice(2, 8)}`;

    loadMermaid()
      .then((mermaid) => mermaid.render(renderId, chart))
      .then(({ svg }) => {
        if (cancelled || !containerRef.current) return;
        setError(null);
        containerRef.current.innerHTML = svg;
        const svgEl = containerRef.current.querySelector("svg");
        if (svgEl) {
          svgEl.setAttribute("role", "img");
          svgEl.removeAttribute("height");
          svgEl.removeAttribute("width");
          svgEl.setAttribute("preserveAspectRatio", "xMidYMid meet");
          svgEl.style.maxWidth = "100%";
          svgEl.style.height = "auto";
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "图表渲染失败");
      });

    return () => {
      cancelled = true;
    };
  }, [chart, reactId]);

  if (error) {
    return (
      <div className="mermaid-wrap mermaid-wrap--error" role="alert">
        <p className="mermaid-error">图表渲染失败：{error}</p>
        <pre>
          <code>{chart}</code>
        </pre>
      </div>
    );
  }

  return <div ref={containerRef} className="mermaid-wrap not-prose" />;
}
