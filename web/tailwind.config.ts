import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // 语义 token:近黑背景 + 高对比 + 饱和粉主强调
        bg: { base: "#0d0e13", card: "#181a22", elev: "#23262f" },
        border: { subtle: "#363a48", strong: "#8b90b8" },
        accent: { DEFAULT: "#ff4fa3", muted: "#ff4fa3" }, // 饱和粉
        // Dracula 原色(提亮 fg)
        drac: {
          bg: "#0d0e13",
          line: "#44475a",
          fg: "#ffffff",
          comment: "#7d83a8",
          cyan: "#8be9fd",
          green: "#50fa7b",
          orange: "#ffb86c",
          pink: "#ff4fa3",
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
