import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { buildCurriculum } from "./scripts/build-curriculum";

// 启动 dev / build 前自动重新烘焙课程内容(若源仓库存在)。
// 源仓库不在(独立 clone web/)时静默跳过,保留已提交的 src/content。
function curriculumIngestPlugin() {
  return {
    name: "curriculum-ingest",
    configureServer() {
      buildCurriculum();
    },
    buildStart() {
      buildCurriculum();
    },
  };
}

export default defineConfig({
  plugins: [react(), curriculumIngestPlugin()],
  server: { port: 5188, open: true },
});
