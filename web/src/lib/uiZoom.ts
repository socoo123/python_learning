/**
 * 界面缩放:CSS zoom 作用在 <html> 上,等效浏览器 Cmd+缩放。
 * 桌面 App(WKWebView)没有原生页面缩放,这是「换大显示器要更大字体」的统一解法。
 * 持久化到 localStorage;订阅机制让页头百分比实时刷新。
 */
const KEY = "py-learn:ui-zoom:v1";

export const ZOOM_MIN = 0.75;
export const ZOOM_MAX = 1.75;
export const ZOOM_STEP = 0.05;

let current = 1;
const listeners = new Set<(z: number) => void>();

function clamp(v: number): number {
  return Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, Math.round(v * 100) / 100));
}

function apply() {
  document.documentElement.style.zoom = String(current);
  listeners.forEach((fn) => fn(current));
}

/** 在 React 渲染前调用,读取持久化缩放并立即生效(避免闪回 100%) */
export function initUiZoom() {
  try {
    const v = parseFloat(localStorage.getItem(KEY) ?? "");
    if (Number.isFinite(v)) current = clamp(v);
  } catch {
    /* localStorage 不可用时静默 */
  }
  apply();
}

export function getUiZoom(): number {
  return current;
}

export function setUiZoom(v: number) {
  current = clamp(v);
  try {
    localStorage.setItem(KEY, String(current));
  } catch {
    /* 持久化失败不影响当次会话 */
  }
  apply();
}

export function zoomIn() {
  setUiZoom(current + ZOOM_STEP);
}

export function zoomOut() {
  setUiZoom(current - ZOOM_STEP);
}

export function resetUiZoom() {
  setUiZoom(1);
}

export function subscribeUiZoom(fn: (z: number) => void): () => void {
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
}
