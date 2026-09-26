/**
 * 首页:模块卡片 + 总进度。数据来自 data.js 的 window.PY_LEARN。
 */
(function (root) {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    var mount = document.getElementById("page-root");
    var h = root.PYDom && root.PYDom.h;
    var data = root.PY_LEARN;
    var state = root.PYLearnState;
    if (!mount || !h || !data || !state) return;

    var modules = data.index.modules;
    var generated = new Set(data.generated);
    var allChapters = [];
    modules.forEach(function (m) {
      allChapters = allChapters.concat(m.chapters);
    });
    var available = modules.filter(function (m) {
      return m.available;
    }).length;

    var statModules = h("div", { class: "stat-value", text: "" });
    var statDone = h("div", { class: "stat-value", text: "" });
    var heroProgress = h("div", { class: "hero-progress-wrap" });
    var hero = h("section", { class: "hero" }, [
      h("div", { class: "hero-watermark", text: "PY" }),
      h("p", { class: "hero-kicker", text: "Python 全栈课程" }),
      h("h1", {}, [
        document.createTextNode("从 Java 老手到 Python 全栈"),
        h("span", { class: "hero-accent", text: " · 网页读教程，仓库写作业" }),
      ]),
      h("p", {
        class: "hero-sub",
        text:
          allChapters.length +
          " 章 / " +
          modules.length +
          " 大模块。网页只展示教程和闪卡；作业在仓库五件套里写，用 uv pytest 验证。",
      }),
      h("div", { class: "hero-stats" }, [
        h("div", { class: "stat" }, [statModules, h("div", { class: "stat-label", text: "模块" })]),
        h("div", { class: "stat" }, [statDone, h("div", { class: "stat-label", text: "已学章节" })]),
        h("div", { class: "stat" }, [
          h("div", { class: "stat-value", text: "本地 pytest" }),
          h("div", { class: "stat-label", text: "作业" }),
        ]),
      ]),
      heroProgress,
    ]);

    var cards = [];
    modules.forEach(function (m, i) {
      var pill = h("span", { class: "status-pill", text: "" });
      var barHost = h("div", {});
      var foot = h("div", { class: "module-card-foot", text: "" });
      var inner = [
        h("div", { class: "module-card-top" }, [
          h("span", { class: "module-card-index", text: String(i + 1).padStart(2, "0") }),
          pill,
        ]),
        h("h3", { text: m.title }),
        h("p", { class: "module-card-sub", text: m.subtitle }),
        barHost,
        foot,
      ];
      var card;
      if (m.available) {
        card = h("a", { class: "module-card", href: "modules/" + m.id + ".html" }, inner);
      } else {
        card = h("div", { class: "module-card disabled" }, inner);
      }
      cards.push({
        module: m,
        card: card,
        pill: pill,
        barHost: barHost,
        foot: foot,
      });
    });

    var steps = [
      ["1", "读教程", "每节教程对比 Java 讲透，讲过的才考。"],
      ["2", "写作业", "在仓库 assignment 文件里填实现，不要在网页里写。"],
      ["3", "跑测试", "uv run pytest 全绿即掌握，再勾选「已学完」。"],
    ].map(function (s) {
      return h("div", { class: "step-card" }, [
        h("div", { class: "step-no", text: s[0] }),
        h("h3", { text: s[1] }),
        h("p", { text: s[2] }),
      ]);
    });

    mount.appendChild(
      h("div", { class: "page-stack" }, [
        hero,
        h("section", {}, [h("h2", { class: "section-title", text: "课程地图" }), h("div", { class: "module-grid" }, cards.map(function (c) { return c.card; }))]),
        h("section", {}, [h("h2", { class: "section-title", text: "怎么学" }), h("div", { class: "steps-grid" }, steps)]),
      ]),
    );

    function refresh() {
      var doneIds = new Set(state.getProgressSnapshot().state.completedChapters);
      var doneCount = allChapters.filter(function (c) {
        return doneIds.has(c.id);
      }).length;
      statModules.textContent = available + " / " + modules.length;
      statDone.textContent = doneCount + " / " + allChapters.length;
      heroProgress.textContent = "";
      heroProgress.appendChild(root.PYDom.progressBarLabeled(doneCount, allChapters.length, "总进度"));
      heroProgress.appendChild(
        h("p", {
          class: "hero-progress-note",
          text: "进度存在本机浏览器；学完一章后在章末勾选「已学完」。",
        }),
      );

      cards.forEach(function (c) {
        var total = c.module.chapters.length;
        var done = c.module.chapters.filter(function (ch) {
          return doneIds.has(ch.id);
        }).length;
        var readyChapters = c.module.chapters.filter(function (ch) {
          return generated.has(ch.id);
        }).length;
        c.barHost.textContent = "";
        if (!c.module.available) {
          pill.className = "status-pill wait";
          pill.textContent = "待生成";
          c.foot.textContent = total + " 章";
          return;
        }
        if (total > 0 && done === total) {
          pill.className = "status-pill done";
          pill.textContent = "已学完";
        } else {
          pill.className = "status-pill ready";
          pill.textContent = "可学习";
        }
        if (total > 0) c.barHost.appendChild(root.PYDom.progressBarLabeled(done, total, "已学", "sm"));
        c.foot.textContent = readyChapters + " 章 · 进入 →";
      });
    }

    state.subscribeProgress(refresh);
    refresh();
  });
})(typeof globalThis !== "undefined" ? globalThis : this);
