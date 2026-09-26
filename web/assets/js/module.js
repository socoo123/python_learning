/**
 * 模块页:本章列表 + 进度勾选。模块 id 写在 #page-root[data-module-id]。
 */
(function (root) {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    var mount = document.getElementById("page-root");
    var h = root.PYDom && root.PYDom.h;
    var data = root.PY_LEARN;
    var state = root.PYLearnState;
    if (!mount || !h || !data || !state) return;

    var moduleId = mount.getAttribute("data-module-id");
    var module = null;
    data.index.modules.forEach(function (m) {
      if (m.id === moduleId) module = m;
    });
    var site = root.SITE_ROOT || "../";
    if (!module) {
      mount.appendChild(
        h("div", { class: "notice-card" }, [
          document.createTextNode("模块不存在。"),
          h("a", { href: site + "index.html", text: "返回首页" }),
        ]),
      );
      return;
    }

    var generated = new Set(data.generated);
    var progressHost = h("div", {});
    var rows = [];
    var list = h("div", { class: "chapter-list" });

    module.chapters.forEach(function (ch) {
      var ready = generated.has(ch.id);
      var meta = h("div", { class: "chapter-meta", text: "" });
      var toggle = h("button", {
        type: "button",
        class: "complete-toggle-btn",
        title: "标为已学完",
        disabled: ready ? null : "disabled",
        onclick: function () {
          state.toggleChapterComplete(ch.id);
        },
      });
      var content = [
        h("span", { class: "chapter-num", text: ch.num }),
        h("div", { class: "chapter-info" }, [h("div", { class: "chapter-title", text: ch.title }), meta]),
      ];
      var row = h("div", { class: "chapter-row" }, [toggle]);
      if (ready) {
        row.classList.add("ready");
        row.appendChild(
          h("a", { class: "chapter-link", href: site + "chapters/" + ch.id + ".html" }, content.concat([h("span", { class: "chapter-arrow", text: "→" })])),
        );
      } else {
        row.classList.add("not-ready");
        row.appendChild(h("div", { class: "chapter-link" }, content));
      }
      rows.push({ id: ch.id, row: row, toggle: toggle, meta: meta, ready: ready });
      list.appendChild(row);
    });

    if (module.chapters.length === 0) {
      list.appendChild(h("div", { class: "notice-card", text: "本模块内容待生成。" }));
    }

    mount.appendChild(
      h("div", { class: "page-stack" }, [
        h("nav", { class: "breadcrumb" }, [
          h("a", { href: site + "index.html", text: "课程地图" }),
          h("span", { class: "sep", text: "/" }),
          h("span", { text: module.title }),
        ]),
        h("header", { class: "chapter-header" }, [
          h("div", {}, [h("h1", { text: module.title }), h("p", { class: "hero-sub", text: module.subtitle })]),
        ]),
        progressHost,
        list,
      ]),
    );

    function refresh() {
      var doneIds = new Set(state.getProgressSnapshot().state.completedChapters);
      var done = 0;
      rows.forEach(function (r) {
        var learned = doneIds.has(r.id);
        if (learned) done += 1;
        r.row.classList.toggle("learned", learned);
        r.toggle.classList.toggle("on", learned);
        r.toggle.title = learned ? "取消已学完" : "标为已学完";
        r.toggle.setAttribute("aria-pressed", learned ? "true" : "false");
        r.toggle.textContent = learned ? "✓" : "";
        if (!r.ready) r.meta.textContent = "内容待生成";
        else r.meta.textContent = learned ? "已学完" : "";
        r.meta.classList.toggle("done", learned && r.ready);
      });
      progressHost.textContent = "";
      if (module.chapters.length > 0) {
        progressHost.appendChild(root.PYDom.progressBarLabeled(done, module.chapters.length, "本模块进度"));
      }
    }

    state.subscribeProgress(refresh);
    refresh();
  });
})(typeof globalThis !== "undefined" ? globalThis : this);
