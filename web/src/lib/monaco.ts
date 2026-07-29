import type { Monaco } from "@monaco-editor/react";

/** 注册 Dracula 主题(在 Editor beforeMount 调用,幂等)。 */
export function defineDracula(monaco: Monaco) {
  monaco.editor.defineTheme("dracula", {
    base: "vs-dark",
    inherit: true,
    rules: [
      { token: "comment", foreground: "6272a4", fontStyle: "italic" },
      { token: "string", foreground: "f1fa8c" },
      { token: "keyword", foreground: "ff79c6" },
      { token: "number", foreground: "bd93f9" },
      { token: "type", foreground: "8be9fd" },
      { token: "function", foreground: "50fa7b" },
      { token: "variable", foreground: "f8f8f2" },
      { token: "constant", foreground: "bd93f9" },
      { token: "delimiter", foreground: "f8f8f2" },
      { token: "operator", foreground: "ff79c6" },
    ],
    colors: {
      "editor.background": "#0d0e13",
      "editor.foreground": "#f8f8f2",
      "editor.lineHighlightBackground": "#262833",
      "editor.selectionBackground": "#44475a",
      "editorCursor.foreground": "#ff79c6",
      "editorGutter.background": "#191a21",
      "editorLineNumber.foreground": "#6272a4",
      "editorLineNumber.activeForeground": "#f8f8f2",
      "editorWidget.background": "#21222c",
      "editor.border": "#44475a",
    },
  });
}
