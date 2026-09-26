/**
 * mermaid 懒加载。mermaid.min.js 约 3.4MB,只在页面里真有图时才插入。
 */
(function (root) {
  "use strict";

  var SITE_ROOT = root.SITE_ROOT || "./";
  var mermaidPromise = null;
  var renderSeq = 0;
  var liveHosts = new Set();

  function ensureMermaid() {
    if (mermaidPromise) return mermaidPromise;
    mermaidPromise = new Promise(function (resolve, reject) {
      var s = document.createElement("script");
      s.src = SITE_ROOT + "assets/js/vendor/mermaid.min.js";
      s.onload = function () {
        resolve(root.mermaid);
      };
      s.onerror = function () {
        mermaidPromise = null;
        reject(new Error("mermaid.min.js 加载失败"));
      };
      document.head.appendChild(s);
    });
    return mermaidPromise;
  }

  function parseErrorMessage(err) {
    if (err instanceof Error && err.message) return err.message;
    if (typeof err === "string") return err;
    return "图表渲染失败";
  }

  function fitSvg(svgEl) {
    svgEl.setAttribute("role", "img");
    svgEl.removeAttribute("height");
    svgEl.removeAttribute("width");
    svgEl.setAttribute("preserveAspectRatio", "xMidYMid meet");
    svgEl.style.maxWidth = "100%";
    svgEl.style.height = "auto";
  }

  function renderMermaid(host, chart) {
    var source = String(chart).replace(/\n$/, "").trim();
    host.__pyChart = source;
    liveHosts.add(host);
    renderSeq += 1;
    var renderId = "mmd" + renderSeq + Math.random().toString(36).slice(2, 8);

    ensureMermaid()
      .then(function (mermaid) {
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
        return mermaid.render(renderId, source);
      })
      .then(function (result) {
        if (host.__pyChart !== source) return;
        host.innerHTML = result.svg;
        var svgEl = host.querySelector("svg");
        if (svgEl) fitSvg(svgEl);
      })
      .catch(function (err) {
        if (host.__pyChart !== source) return;
        liveHosts.delete(host);
        host.classList.add("mermaid-error");
        host.textContent = parseErrorMessage(err);
      });
  }

  document.addEventListener("py-theme-change", function () {
    Array.from(liveHosts).forEach(function (host) {
      if (!document.contains(host)) {
        liveHosts.delete(host);
        return;
      }
      renderMermaid(host, host.__pyChart);
    });
  });

  root.PYDiagrams = { renderMermaid: renderMermaid };
})(typeof globalThis !== "undefined" ? globalThis : this);
