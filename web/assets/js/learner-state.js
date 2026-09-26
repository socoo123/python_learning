/**
 * 学习进度。存在本机 localStorage,刷新不丢。
 * 键名 py-learn:learner-state:v1 与原先 React 站一致,同一浏览器里的勾选会延续。
 * GitHub Pages / 双击打开都没有本地文件接口,不再写 web/.learner-state.json。
 */
(function (root) {
  "use strict";

  var LEARNER_STORAGE_KEY = "py-learn:learner-state:v1";

  function emptyState() {
    return { version: 1, updatedAt: "", completedChapters: [], drafts: {} };
  }

  function normalizeState(raw) {
    if (!raw || typeof raw !== "object") return null;
    if (raw.version !== 1) return null;
    var completed = Array.isArray(raw.completedChapters)
      ? raw.completedChapters.filter(function (id) {
          return typeof id === "string";
        })
      : [];
    var drafts = {};
    if (raw.drafts && typeof raw.drafts === "object") {
      Object.keys(raw.drafts).forEach(function (k) {
        var v = raw.drafts[k];
        if (!v || typeof v !== "object") return;
        var functions;
        if (v.functions && typeof v.functions === "object") {
          functions = {};
          Object.keys(v.functions).forEach(function (name) {
            if (typeof v.functions[name] === "string") functions[name] = v.functions[name];
          });
        }
        drafts[k] = {
          assignment: typeof v.assignment === "string" ? v.assignment : undefined,
          functions: functions,
        };
      });
    }
    return {
      version: 1,
      updatedAt: typeof raw.updatedAt === "string" ? raw.updatedAt : "",
      completedChapters: Array.from(new Set(completed)),
      drafts: drafts,
    };
  }

  function loadLocal() {
    try {
      var raw = localStorage.getItem(LEARNER_STORAGE_KEY);
      if (!raw) return emptyState();
      return normalizeState(JSON.parse(raw)) || emptyState();
    } catch (e) {
      return emptyState();
    }
  }

  function writeLocal(state) {
    try {
      localStorage.setItem(LEARNER_STORAGE_KEY, JSON.stringify(state));
    } catch (e) {
      /* quota / 隐私模式 */
    }
  }

  var progressListeners = new Set();
  var snapshot = { state: loadLocal() };

  function emit(next) {
    snapshot = { state: next };
    progressListeners.forEach(function (l) {
      l();
    });
  }

  function mutate(updater, notifyProgress) {
    var next = Object.assign({}, updater(snapshot.state), {
      version: 1,
      updatedAt: new Date().toISOString(),
    });
    writeLocal(next);
    if (notifyProgress) emit(next);
    else snapshot = { state: next };
  }

  var api = {
    subscribeProgress: function (listener) {
      progressListeners.add(listener);
      return function () {
        progressListeners.delete(listener);
      };
    },
    getProgressSnapshot: function () {
      return snapshot;
    },
    isComplete: function (chapterId) {
      return snapshot.state.completedChapters.indexOf(chapterId) !== -1;
    },
    setChapterComplete: function (chapterId, complete) {
      mutate(function (s) {
        var set = new Set(s.completedChapters);
        if (complete) set.add(chapterId);
        else set.delete(chapterId);
        return Object.assign({}, s, { completedChapters: Array.from(set) });
      }, true);
    },
    toggleChapterComplete: function (chapterId) {
      api.setChapterComplete(chapterId, !api.isComplete(chapterId));
    },
  };

  root.PYLearnState = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
