import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // 语义 token(加深背景 + 粉色主强调,去雾用实色不用半透明)
        bg: { base: "#191a21", card: "#21222c", elev: "#2a2c36" },
        border: { subtle: "#44475a", strong: "#7d83a8" },
        accent: { DEFAULT: "#ff79c6", muted: "#ff79c6" }, // 粉(主强调)
        // Dracula 原色
        drac: {
          bg: "#191a21",
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
