/**
 * Tauri 打包前:先刷新静态页,再把网页文件拷到 desktop-dist/。
 * frontendDist 不能指到 web/ 根目录,否则会把 src-tauri 和 node_modules 打进安装包。
 */
import { spawnSync } from "node:child_process";
import { cpSync, mkdirSync, rmSync } from "node:fs";
import { join, resolve } from "node:path";

const WEB = resolve(import.meta.dir, "..");
const DEST = join(WEB, "desktop-dist");

const rendered = spawnSync("bun", ["scripts/render-pages.ts"], { cwd: WEB, stdio: "inherit" });
if (rendered.status !== 0) process.exit(rendered.status ?? 1);

rmSync(DEST, { recursive: true, force: true });
mkdirSync(DEST, { recursive: true });
for (const name of ["index.html", ".nojekyll", "chapters", "modules", "assets"]) {
  cpSync(join(WEB, name), join(DEST, name), { recursive: true });
}
console.log("prepare-desktop: 已写入 desktop-dist/");
