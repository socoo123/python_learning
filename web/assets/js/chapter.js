/**
 * 章节页:只读教程、目录、作业路径、闪卡、已学完勾选。
 * 正文来自页面内嵌的 #chapter-data,不发额外请求,双击 html 也能开。
 */
(function (root) {
  "use strict";

  function copyText(text, btn) {
    function done() {
      btn.textContent = "已复制 ✓";
      setTimeout(function () {
        btn.textContent = "复制";
      }, 1500);
    }
    function fallback() {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand("copy");
        done();
      } catch (e) {
        /* 放弃 */
      }
      document.body.removeChild(ta);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, fallback);
    } else {
      fallback();
    }
  }

  function assignmentCard(chapter, h) {
    var file = chapter.moduleDir + "/ch" + chapter.num + "/ch" + chapter.num + "_assignment.py";
    var cmd = "uv run pytest " + chapter.moduleDir + "/ch" + chapter.num + "/test_ch" + chapter.num + "_assignment.py -v";
    var copyBtn = h("button", {
      type: "button",
      class: "copy-btn",
      text: "复制",
      onclick: function () {
        copyText(cmd, copyBtn);
      },
    });
    var extra =
      chapter.runMode === "local" ? " 本章依赖系统或网络库，先按模块说明做 uv sync --extra。" : "";
    return h("div", { class: "local-notice" }, [
      h("div", { class: "ln-title", text: "作业在仓库里写" }),
      h("p", { text: "网页只读教程。实现写在五件套的 assignment 文件里，用 pytest 验证。" + extra }),
      h("p", {}, [document.createTextNode("打开 "), h("code", { text: file })]),
      h("div", { class: "ln-cmd" }, [h("code", { text: cmd }), copyBtn]),
    ]);
  }

  function completeToggle(chapterId, state, h) {
    var card = h("div", { class: "complete-card" });
    var title = h("span", { class: "cc-title" });
    var sub = h("span", { class: "cc-sub" });
    var input = h("input", { type: "checkbox" });
    input.addEventListener("change", function () {
      state.setChapterComplete(chapterId, input.checked);
    });
    card.appendChild(
      h("label", {}, [
        input,
        h("span", {}, [
          title,
          sub,
          h("span", { class: "cc-note", text: "进度存在本机浏览器（localStorage），刷新不会丢。" }),
        ]),
      ]),
    );
    function paint() {
      var done = state.isComplete(chapterId);
      card.classList.toggle("done", done);
      input.checked = done;
      title.textContent = done ? "已学完本章" : "我已学完本章";
      sub.textContent = done ? "进度已勾选，可在首页和模块列表里看到。" : "学完教程和作业后勾选，外面的进度条会跟着更新。";
    }
    state.subscribeProgress(paint);
    paint();
    return card;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var mount = document.getElementById("page-root");
    var h = root.PYDom && root.PYDom.h;
    var state = root.PYLearnState;
    var dataEl = document.getElementById("chapter-data");
    var navEl = document.getElementById("chapter-nav");
    if (!mount || !h || !dataEl || !state || !root.PYMarkdown) return;

    var chapter;
    try {
      chapter = JSON.parse(dataEl.textContent || "");
    } catch (e) {
      mount.appendChild(h("div", { class: "notice-card", text: "章节数据解析失败。" }));
      return;
    }
    var nav = {};
    try {
      nav = JSON.parse((navEl && navEl.textContent) || "{}");
    } catch (e) {
      nav = {};
    }

    var site = root.SITE_ROOT || "../";
    var tocItems = (chapter.toc || []).filter(function (s) {
      return s.heading && String(s.heading).trim();
    });
    var showToc = tocItems.length >= 3;

    var badge = h("span", { class: "status-pill done", text: "已学完" });
    badge.hidden = true;

    var column = h("div", { class: "page-stack" }, [
      h("nav", { class: "breadcrumb" }, [
        h("a", { href: site + "index.html", text: "课程地图" }),
        h("span", { class: "sep", text: "/" }),
        h("a", { href: site + "modules/" + chapter.moduleId + ".html", text: chapter.moduleTitle || "" }),
        h("span", { class: "sep", text: "/" }),
        h("span", { text: "Ch" + chapter.num }),
      ]),
      h("header", { class: "chapter-header" }, [
        h("div", {}, [
          h("div", { class: "chapter-kicker", text: "第 " + chapter.num + " 课" }),
          h("h1", { text: chapter.title }),
        ]),
        badge,
      ]),
    ]);

    var tutorial = h("div", {});
    root.PYMarkdown.renderMarkdown(
      tutorial,
      chapter.tutorialMd,
      tocItems.map(function (s) {
        return s.id;
      }),
    );
    column.appendChild(h("section", {}, [tutorial]));
    column.appendChild(assignmentCard(chapter, h));
    column.appendChild(completeToggle(chapter.id, state, h));

    if (chapter.reviewMd && String(chapter.reviewMd).trim()) {
      var fcBody = h("div", { class: "fc-body" });
      root.PYMarkdown.renderMarkdown(fcBody, chapter.reviewMd);
      column.appendChild(
        h("details", { class: "flashcards" }, [
          h("summary", {}, [document.createTextNode("记忆闪卡"), h("span", { class: "fc-hint", text: "点开复习" })]),
          fcBody,
        ]),
      );
    }

    if (nav.prev || nav.next) {
      var pn = h("div", { class: "prevnext" });
      if (nav.prev) {
        pn.appendChild(
          h("a", { href: nav.prev.id + ".html" }, [
            h("div", { class: "pn-label", text: "← 上一章 Ch" + nav.prev.num }),
            h("span", { class: "pn-title", text: nav.prev.title }),
          ]),
        );
      } else {
        pn.appendChild(h("span", {}));
      }
      if (nav.next) {
        pn.appendChild(
          h("a", { class: "pn-next", href: nav.next.id + ".html" }, [
            h("div", { class: "pn-label", text: "下一章 Ch" + nav.next.num + " →" }),
            h("span", { class: "pn-title", text: nav.next.title }),
          ]),
        );
      }
      column.appendChild(pn);
    }

    var layout = h("div", { class: showToc ? "chapter-layout has-toc" : "chapter-layout" });
    if (showToc) {
      var toc = h("nav", { class: "chapter-toc", "aria-label": "目录" }, [
        h("div", { class: "chapter-toc-label", text: "目录" }),
        h(
          "ol",
          {},
          tocItems.map(function (s) {
            var label = String(s.heading).replace(/^#+\s*/, "");
            return h("li", {}, [
              h("a", {
                href: "#" + s.id,
                text: label,
                onclick: function (e) {
                  var target = document.getElementById(s.id);
                  if (!target) return;
                  e.preventDefault();
                  target.scrollIntoView({ behavior: "smooth", block: "start" });
                  if (history.replaceState) history.replaceState(null, "", "#" + s.id);
                },
              }),
            ]);
          }),
        ),
      ]);
      layout.appendChild(toc);
    }
    layout.appendChild(column);
    mount.appendChild(layout);

    function paintBadge() {
      badge.hidden = !state.isComplete(chapter.id);
    }
    state.subscribeProgress(paintBadge);
    paintBadge();
  });
})(typeof globalThis !== "undefined" ? globalThis : this);
