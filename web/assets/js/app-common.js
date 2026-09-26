/**
 * 顶栏行为:主题、界面缩放、头部进度。
 * 主题键 py-theme;缩放键 py-learn:ui-zoom:v1。都和原先 React 站一致。
 */
(function (root) {
  "use strict";

  var THEME_STORAGE_KEY = "py-theme";
  var ZOOM_KEY = "py-learn:ui-zoom:v1";
  var ZOOM_MIN = 0.75;
  var ZOOM_MAX = 1.75;
  var ZOOM_STEP = 0.05;
  var zoom = 1;

  function readStoredTheme() {
    try {
      var raw = localStorage.getItem(THEME_STORAGE_KEY);
      if (raw === "parchment" || raw === "dracula") return raw;
    } catch (e) {
      /* localStorage 不可用时静默回退 */
    }
    return "parchment";
  }

  function persistTheme(theme) {
    try {
      localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch (e) {
      /* 同上 */
    }
    document.documentElement.setAttribute("data-theme", theme);
    document.dispatchEvent(new CustomEvent("py-theme-change", { detail: { theme: theme } }));
  }

  function clampZoom(v) {
    return Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, Math.round(v * 100) / 100));
  }

  function readZoom() {
    try {
      var v = parseFloat(localStorage.getItem(ZOOM_KEY) || "");
      if (Number.isFinite(v)) return clampZoom(v);
    } catch (e) {
      /* 忽略 */
    }
    return 1;
  }

  function paintZoom() {
    document.documentElement.style.zoom = String(zoom);
    document.querySelectorAll("[data-zoom-label]").forEach(function (el) {
      el.textContent = Math.round(zoom * 100) + "%";
    });
    document.querySelectorAll("[data-zoom='out']").forEach(function (btn) {
      btn.disabled = zoom <= ZOOM_MIN;
    });
    document.querySelectorAll("[data-zoom='in']").forEach(function (btn) {
      btn.disabled = zoom >= ZOOM_MAX;
    });
  }

  function setZoom(v) {
    zoom = clampZoom(v);
    try {
      localStorage.setItem(ZOOM_KEY, String(zoom));
    } catch (e) {
      /* 持久化失败不影响当次 */
    }
    paintZoom();
  }

  function initHeaderProgress() {
    var host = document.querySelector("[data-header-progress]");
    var h = root.PYDom && root.PYDom.h;
    if (!host || !root.PYLearnState || !h || !root.PY_LEARN) return;
    var chapters = [];
    root.PY_LEARN.index.modules.forEach(function (m) {
      chapters = chapters.concat(m.chapters);
    });
    var total = chapters.length;
    if (total <= 0) return;

    var label = h("div", { class: "hp-label", text: "进度 0/" + total });
    var bar = root.PYDom.progressBar(0, total, "sm");
    var link = h("a", { class: "header-progress", href: (root.SITE_ROOT || "./") + "index.html" }, [label, bar]);
    host.appendChild(link);

    function refresh() {
      var doneIds = new Set(root.PYLearnState.getProgressSnapshot().state.completedChapters);
      var done = chapters.filter(function (c) {
        return doneIds.has(c.id);
      }).length;
      label.textContent = "进度 " + done + "/" + total;
      link.title = "已学 " + done + " / " + total + " 章";
      var fill = bar.querySelector(".progress-fill");
      if (fill) fill.style.width = Math.min(100, Math.round((done / total) * 100)) + "%";
    }
    root.PYLearnState.subscribeProgress(refresh);
    refresh();
  }

  document.addEventListener("DOMContentLoaded", function () {
    zoom = readZoom();
    paintZoom();

    document.querySelectorAll("[data-theme-toggle]").forEach(function (box) {
      function paint(current) {
        box.querySelectorAll("button").forEach(function (btn) {
          var on = btn.getAttribute("data-theme-value") === current;
          btn.classList.toggle("active", on);
          btn.setAttribute("aria-pressed", on ? "true" : "false");
        });
      }
      box.querySelectorAll("button").forEach(function (btn) {
        btn.addEventListener("click", function () {
          var theme = btn.getAttribute("data-theme-value");
          persistTheme(theme);
          paint(theme);
        });
      });
      paint(document.documentElement.getAttribute("data-theme") || readStoredTheme());
    });

    document.querySelectorAll("[data-zoom]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var kind = btn.getAttribute("data-zoom");
        if (kind === "in") setZoom(zoom + ZOOM_STEP);
        else if (kind === "out") setZoom(zoom - ZOOM_STEP);
        else setZoom(1);
      });
    });

    window.addEventListener("keydown", function (e) {
      if (!(e.metaKey || e.ctrlKey)) return;
      if (e.key === "=" || e.key === "+") {
        e.preventDefault();
        setZoom(zoom + ZOOM_STEP);
      } else if (e.key === "-" || e.key === "_") {
        e.preventDefault();
        setZoom(zoom - ZOOM_STEP);
      } else if (e.key === "0") {
        e.preventDefault();
        setZoom(1);
      }
    });

    var gestureBase = null;
    window.addEventListener("gesturestart", function () {
      gestureBase = zoom;
    });
    window.addEventListener("gesturechange", function (e) {
      var ge = e;
      if (gestureBase == null) gestureBase = zoom;
      if (typeof ge.preventDefault === "function") ge.preventDefault();
      if (typeof ge.scale === "number") setZoom(gestureBase * ge.scale);
    });

    initHeaderProgress();
  });
})(typeof globalThis !== "undefined" ? globalThis : this);
