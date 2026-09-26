/**
 * Markdown:marked(GFM) + highlight.js。```mermaid 交给 diagrams.js。
 * headingIds 按出现顺序标到 h2 上,给左侧目录跳转。
 */
(function (root) {
  "use strict";

  function highlightCodeBlock(codeEl) {
    var hljs = root.hljs;
    if (!hljs) return;
    var m = /language-([\w+-]+)/.exec(codeEl.className || "");
    var text = codeEl.textContent || "";
    if (m && m[1] === "mermaid") return;
    if (!m) {
      codeEl.innerHTML = hljs.highlightAuto(text).value;
      return;
    }
    if (!hljs.getLanguage(m[1])) return;
    codeEl.innerHTML = hljs.highlight(text, { language: m[1], ignoreIllegals: true }).value;
  }

  function renderMarkdown(container, mdText, headingIds) {
    container.className = "tutorial";
    container.innerHTML = root.marked.parse(mdText || "", { gfm: true, breaks: false });

    var mermaidJobs = [];
    Array.from(container.querySelectorAll("pre > code")).forEach(function (codeEl) {
      var m = /language-([\w+-]+)/.exec(codeEl.className || "");
      if (!m || m[1] !== "mermaid") return;
      var pre = codeEl.parentNode;
      var host = document.createElement("div");
      host.className = "mermaid-block";
      pre.parentNode.replaceChild(host, pre);
      mermaidJobs.push([host, codeEl.textContent || ""]);
    });

    Array.from(container.querySelectorAll("pre > code")).forEach(highlightCodeBlock);

    if (headingIds && headingIds.length) {
      var h2s = container.querySelectorAll("h2");
      headingIds.forEach(function (id, i) {
        if (h2s[i]) h2s[i].id = id;
      });
    }

    if (mermaidJobs.length && root.PYDiagrams) {
      mermaidJobs.forEach(function (job) {
        root.PYDiagrams.renderMermaid(job[0], job[1]);
      });
    }
  }

  root.PYMarkdown = { renderMarkdown: renderMarkdown };
})(typeof globalThis !== "undefined" ? globalThis : this);
