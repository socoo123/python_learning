/**
 * build-curriculum.ts —— 把源仓库课程烘焙成 web 可消费 JSON。
 * 运行:`bun run build:content`(dev/build 时 vite 插件自动调用)。
 * 只读源文件,绝不修改。源仓库不在(独立 clone web/)时静默跳过。
 */
import { readFileSync, readdirSync, existsSync, writeFileSync, mkdirSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const WEB_DIR = path.resolve(__dirname, "..");
const REPO_ROOT = path.resolve(WEB_DIR, "..");
const OUT_DIR = path.join(WEB_DIR, "src", "content");
const OUT_FILE = path.join(OUT_DIR, "curriculum.json");

export interface FuncDef {
  name: string;
  testClass: string; // "TestAdd"
  skeleton: string; // 编辑器初始内容(单函数,已骨架化)
}
export interface Section {
  id: string;
  heading: string; // 不含 "## "
  secNum: string | null; // "1.1" 或 null
  body: string; // 该节 markdown 正文(不含标题行)
  exerciseFunctions: string[]; // 该节对应的函数名
}
export interface Chapter {
  id: string;
  num: string;
  title: string;
  runMode: "pyodide" | "local";
  tutorialMd: string; // 原始完整教程(layout A 回退用)
  assignment: string; // 完整作业文件(layout A / 本地用)
  testName: string;
  testSource: string;
  reviewMd: string;
  // 交错式:
  interleaved: boolean;
  sections: Section[];
  functions: FuncDef[];
  preamble: string; // 作业文件里函数之外的全局代码(import/模块docstring)
}
export interface Module {
  id: string;
  title: string;
  subtitle: string;
  dir: string;
  available: boolean;
  chapters: Chapter[];
}
export interface Curriculum {
  modules: Module[];
  shared: { conftest: string; mocks: Record<string, string> };
}

const MODULE_DEFS: Omit<Module, "chapters">[] = [
  { id: "m1", title: "Python 语言核心", subtitle: "思维转换 · 数据结构 · OOP · 类型", dir: "01_python_core", available: true },
  { id: "m2", title: "标准库 & 三方库", subtitle: "collections · itertools · 正则 · json", dir: "02_stdlib", available: true },
  { id: "m3", title: "Web 框架 FastAPI", subtitle: "API · ORM · 认证 · 部署", dir: "03_web_framework", available: true },
  { id: "m4", title: "运维脚本", subtitle: "pathlib · subprocess · CLI · 监控", dir: "04_devops_scripts", available: true },
  { id: "m5", title: "AI 框架", subtitle: "LLM · Prompt · RAG · Agent", dir: "05_ai_framework", available: true },
  { id: "m6", title: "LeetCode 实战", subtitle: "Pythonic 刷题", dir: "06_leetcode", available: true },
];

/** 整模块强制 Local(设计约定:M5 全章本地跑,即便作业本身可离线测) */
const FORCE_LOCAL_DIRS = new Set(["05_ai_framework"]);

const LOCAL_IMPORTS = new Set([
  "fastapi", "uvicorn", "httpx", "sqlalchemy", "alembic", "jose", "passlib",
  "pydantic", "psutil", "schedule", "typer", "rich", "anthropic", "openai",
  "langchain", "langchain_core", "langchain_community", "chromadb",
  "sentence_transformers", "multipart", "dotenv",
  "starlette", "requests", "pydantic_settings",
]);

function readText(p: string): string {
  return readFileSync(p, "utf-8");
}
function safeRead(p: string): string {
  return existsSync(p) ? readText(p) : "";
}
function detectRunMode(texts: string[]): "pyodide" | "local" {
  const re = /^\s*(?:from|import)\s+([a-zA-Z0-9_]+)/gm;
  for (const t of texts) {
    let m: RegExpExecArray | null;
    while ((m = re.exec(t))) if (LOCAL_IMPORTS.has(m[1])) return "local";
  }
  return "pyodide";
}
function extractTitle(tutorialMd: string, fallback: string): string {
  const m = tutorialMd.match(/^#\s+.*?(?:·|•|・|-)\s*(.+)$/m);
  return m ? m[1].trim() : fallback;
}

// ---------- 函数解析 ----------
function pascalCase(name: string): string {
  return name.split("_").map((p) => p.charAt(0).toUpperCase() + p.slice(1)).join("");
}

function skeletonize(blockLines: string[]): string {
  const defIdx = blockLines.findIndex((l) => /^def\s/.test(l));
  if (defIdx < 0) return blockLines.join("\n");
  const decorators = blockLines.slice(0, defIdx);
  const defLine = blockLines[defIdx];
  const body = blockLines.slice(defIdx + 1);

  // 找 docstring(紧跟 def 的缩进 """ ... """)
  let i = 0;
  const lead: string[] = [];
  while (i < body.length && body[i].trim() === "") { lead.push(body[i]); i++; }
  let docLines: string[] = [];
  if (i < body.length && /^\s*("""|''')/.test(body[i])) {
    const q = body[i].trim().slice(0, 3);
    docLines.push(...lead, body[i]);
    i++;
    const singleLine = new RegExp(`^\\s*${q}.+${q}\\s*$`).test(body[i - 1]);
    if (!singleLine) {
      while (i < body.length && !body[i].includes(q)) { docLines.push(body[i]); i++; }
      if (i < body.length) { docLines.push(body[i]); i++; }
    }
  }
  const rest = body.slice(i);
  const isSkeleton = rest.every((l) => {
    const t = l.trim();
    return t === "" || t.startsWith("#") || t === "..." || t === "pass";
  });
  if (isSkeleton) return blockLines.join("\n"); // 已是骨架(保留 TODO 提示)
  return [...decorators, defLine, ...docLines, "    ..."].join("\n");
}

function parseAssignment(source: string): { preamble: string; functions: FuncDef[] } {
  const lines = source.split("\n");
  const functions: FuncDef[] = [];
  const preamble: string[] = [];
  let pendingDeco: string[] = [];
  let idx = 0;
  while (idx < lines.length) {
    const line = lines[idx];
    if (/^@/.test(line)) { pendingDeco.push(line); idx++; continue; }
    const defM = line.match(/^def\s+([A-Za-z_]\w*)\s*\(/);
    if (defM) {
      const name = defM[1];
      const block = [...pendingDeco, line];
      pendingDeco = [];
      idx++;
      while (idx < lines.length) {
        const l = lines[idx];
        if (l === "" || /^\s/.test(l)) { block.push(l); idx++; continue; }
        break;
      }
      while (block.length && block[block.length - 1] === "") block.pop();
      functions.push({ name, testClass: "Test" + pascalCase(name), skeleton: skeletonize(block) });
      continue;
    }
    preamble.push(line);
    pendingDeco = [];
    idx++;
  }
  return { preamble: preamble.join("\n").trim(), functions };
}

// ---------- 教程分节 + 函数映射 ----------
function parseMappingTable(tutorialMd: string): Map<string, string[]> {
  const map = new Map<string, string[]>();
  const re = /`([a-z_][a-z0-9_]*)`\s*\|\s*§(\d+\.\d+)/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(tutorialMd))) {
    const [, fn, sec] = m;
    if (!map.has(sec)) map.set(sec, []);
    if (!map.get(sec)!.includes(fn)) map.get(sec)!.push(fn);
  }
  return map;
}

function slug(s: string): string {
  return s.replace(/[^\w一-龥]+/g, "-").replace(/^-|-$/g, "").slice(0, 40) || "sec";
}

function parseSections(tutorialMd: string, mapping: Map<string, string[]>): Section[] {
  const lines = tutorialMd.split("\n");
  const sections: Section[] = [];
  let intro: string[] = [];
  let cur: { heading: string; secNum: string | null; body: string[] } | null = null;
  const pushCur = () => {
    if (!cur) return;
    const fns = cur.secNum ? mapping.get(cur.secNum) || [] : [];
    sections.push({
      id: cur.secNum ? `sec-${cur.secNum}` : `sec-${slug(cur.heading)}`,
      heading: cur.heading,
      secNum: cur.secNum,
      body: cur.body.join("\n").trim(),
      exerciseFunctions: fns,
    });
    cur = null;
  };
  for (const line of lines) {
    if (/^##\s+/.test(line)) {
      pushCur();
      const heading = line.replace(/^##\s+/, "").trim();
      const sn = heading.match(/§(\d+\.\d+)/);
      cur = { heading, secNum: sn ? sn[1] : null, body: [] };
    } else {
      if (cur) cur.body.push(line);
      else intro.push(line);
    }
  }
  pushCur();
  // intro(首标题 # 之后到第一个 ##),去掉 H1 行避免与页面标题重复
  const introBody = intro.join("\n").replace(/^#\s+.*/, "").trim();
  if (introBody) sections.unshift({ id: "intro", heading: "", secNum: null, body: introBody, exerciseFunctions: [] });
  return sections;
}

function buildModule(def: Omit<Module, "chapters">): Module {
  const moduleDir = path.join(REPO_ROOT, def.dir);
  const chapters: Chapter[] = [];
  if (existsSync(moduleDir) && statSync(moduleDir).isDirectory()) {
    const dirs = readdirSync(moduleDir).filter((d) => /^ch\d+$/.test(d)).sort();
    for (const d of dirs) {
      const chDir = path.join(moduleDir, d);
      const num = d.replace("ch", "");
      const testName = `${d}_assignment`;
      const tutorial = safeRead(path.join(chDir, "tutorial.md"));
      const assignment = safeRead(path.join(chDir, `${testName}.py`));
      const testSource = safeRead(path.join(chDir, `test_${testName}.py`));
      const reviewMd = safeRead(path.join(chDir, "review.md"));
      if (!tutorial && !assignment) continue;

      let runMode = detectRunMode([assignment, testSource]);
      if (FORCE_LOCAL_DIRS.has(def.dir)) runMode = "local";
      const { preamble, functions } = parseAssignment(assignment);
      const mapping = parseMappingTable(tutorial);
      const sections = parseSections(tutorial, mapping);
      const funcNames = new Set(functions.map((f) => f.name));
      const hasExercises = sections.some((s) => s.exerciseFunctions.some((f) => funcNames.has(f)));
      const interleaved = hasExercises && functions.length > 0 && runMode === "pyodide";

      chapters.push({
        id: d,
        num,
        title: extractTitle(tutorial, `第 ${num} 课`),
        runMode,
        tutorialMd: tutorial,
        assignment,
        testName,
        testSource,
        reviewMd,
        interleaved,
        sections,
        functions,
        preamble,
      });
    }
  }
  return { ...def, chapters };
}

export function buildCurriculum(): Curriculum | null {
  if (!existsSync(path.join(REPO_ROOT, "01_python_core"))) {
    console.log("[content] 源仓库不存在(独立运行 web/),跳过烘焙,使用已提交内容。");
    return null;
  }
  const modules = MODULE_DEFS.map(buildModule);
  const mockDir = path.join(REPO_ROOT, "assets", "mock_data");
  const mocks: Record<string, string> = {};
  if (existsSync(mockDir)) for (const f of readdirSync(mockDir).sort()) mocks[f] = readText(path.join(mockDir, f));
  const conftest = safeRead(path.join(REPO_ROOT, "conftest.py"));
  const curriculum: Curriculum = { modules, shared: { conftest, mocks } };
  mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(OUT_FILE, JSON.stringify(curriculum, null, 2), "utf-8");

  let inter = 0, total = 0;
  for (const m of modules) for (const c of m.chapters) { total++; if (c.interleaved) inter++; }
  console.log(`[content] 烘焙完成:${total} 章,其中 ${inter} 章交错式 → src/content/curriculum.json`);
  return curriculum;
}

if ((import.meta as any).main) buildCurriculum();
