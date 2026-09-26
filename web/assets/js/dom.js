/**
 * 小型 DOM 助手。静态页不用 React,各页脚本共用这一套。
 */
(function (root) {
  "use strict";

  function h(tag, attrs, children) {
    var el = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (attrs[k] == null) return;
        if (k === "class") el.className = attrs[k];
        else if (k === "text") el.textContent = attrs[k];
        else if (k.slice(0, 2) === "on") el.addEventListener(k.slice(2), attrs[k]);
        else el.setAttribute(k, attrs[k]);
      });
    }
    (children || []).forEach(function (c) {
      if (c) el.appendChild(c);
    });
    return el;
  }

  function progressBar(value, max, size) {
    var pct = Math.min(100, Math.round((value / Math.max(max, 1)) * 100));
    var track = h("div", {
      class: "progress-track " + (size || "md"),
      role: "progressbar",
      "aria-valuemin": "0",
      "aria-valuemax": String(max),
      "aria-valuenow": String(value),
    });
    var fill = h("div", { class: "progress-fill" });
    fill.style.width = pct + "%";
    track.appendChild(fill);
    return track;
  }

  function progressBarLabeled(value, max, label, size) {
    var pct = Math.min(100, Math.round((value / Math.max(max, 1)) * 100));
    var wrap = h("div", { class: "progress-wrap" });
    wrap.appendChild(
      h("div", { class: "progress-label" }, [
        h("span", { text: label || "" }),
        h("span", { text: value + "/" + max + " · " + pct + "%" }),
      ]),
    );
    wrap.appendChild(progressBar(value, max, size || "md"));
    return wrap;
  }

  root.PYDom = { h: h, progressBar: progressBar, progressBarLabeled: progressBarLabeled };
})(typeof globalThis !== "undefined" ? globalThis : this);
