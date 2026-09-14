import { useEffect, useState } from "react";
import {
  getUiZoom,
  resetUiZoom,
  setUiZoom,
  subscribeUiZoom,
  zoomIn,
  zoomOut,
} from "../lib/uiZoom";

/** WebKit 的触控板捏合事件(Chromium 无此事件,走各自的原生缩放) */
interface GestureEventLike {
  scale: number;
  preventDefault?: () => void;
}

/**
 * 缩放状态 + 全局快捷键:
 * - ⌘/Ctrl + = 放大、⌘/Ctrl + - 缩小、⌘/Ctrl + 0 重置
 * - macOS 触控板双指捏合(WebKit gesture 事件)
 */
export function useUiZoom() {
  const [zoom, setZoomState] = useState(getUiZoom);

  useEffect(() => {
    const unsubscribe = subscribeUiZoom(setZoomState);

    const onKeyDown = (e: KeyboardEvent) => {
      if (!(e.metaKey || e.ctrlKey)) return;
      if (e.key === "=" || e.key === "+") {
        e.preventDefault();
        zoomIn();
      } else if (e.key === "-" || e.key === "_") {
        e.preventDefault();
        zoomOut();
      } else if (e.key === "0") {
        e.preventDefault();
        resetUiZoom();
      }
    };

    let gestureBase: number | null = null;
    const onGestureStart = () => {
      gestureBase = getUiZoom();
    };
    const onGestureChange = (e: Event) => {
      const ge = e as unknown as GestureEventLike;
      if (gestureBase == null) gestureBase = getUiZoom();
      ge.preventDefault?.();
      // 捏合是连续手势,scale 相对手势起点;lib 里会 clamp + 持久化
      setUiZoom(gestureBase * ge.scale);
    };

    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("gesturestart", onGestureStart);
    window.addEventListener("gesturechange", onGestureChange);
    return () => {
      unsubscribe();
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("gesturestart", onGestureStart);
      window.removeEventListener("gesturechange", onGestureChange);
    };
  }, []);

  return { zoom, zoomIn, zoomOut, reset: resetUiZoom };
}
