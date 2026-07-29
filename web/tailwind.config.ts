import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // 语义 token(组件用这些,指向 Dracula 色)
        bg: { base: "#282a36", card: "#21222c", elev: "#343746" },
        border: { subtle: "#44475a", strong: "#6272a4" },
        accent: { DEFAULT: "#bd93f9", muted: "#bd93f9" }, // 紫
        // Dracula 原色
        drac: {
          bg: "#282a36",
          line: "#44475a",
          fg: "#f8f8f2",
          comment: "#6272a4",
          cyan: "#8be9fd",
          green: "#50fa7b",
          orange: "#ffb86c",
          pink: "#ff79c6",
          purple: "#bd93f9",
          red: "#ff5555",
          yellow: "#f1fa8c",
        },
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "monospace"],
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
} satisfies Config;
