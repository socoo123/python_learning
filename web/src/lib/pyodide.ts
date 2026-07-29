/**
 * Pyodide 运行器:浏览器内跑 pytest。
 *
 * 流程:懒加载 Pyodide(CDN)→ 把 assignment + test + conftest + mock 数据写进
 * 虚拟 FS 的 /work → redirect_stdout 跑 pytest.main → 回传 {output, returncode}。
 */
const PYODIDE_VERSION = "0.26.2";
const INDEX_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;

let pyodidePromise: Promise<any> | null = null;

declare global {
  interface Window {
    loadPyodide?: (cfg: { indexURL: string }) => Promise<any>;
  }
}

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (window.loadPyodide) return resolve();
    const existing = document.querySelector(`script[src="${src}"]`);
    if (existing) {
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () => reject(new Error("Pyodide 脚本加载失败(检查网络)")));
      return;
    }
    const s = document.createElement("script");
    s.src = src;
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("Pyodide 脚本加载失败(检查网络)"));
    document.head.appendChild(s);
  });
}

/** 加载 Pyodide 单例(首次拉 ~10MB,后续复用)。 */
export async function getPyodide(): Promise<any> {
  if (!pyodidePromise) {
    pyodidePromise = (async () => {
      await loadScript(INDEX_URL + "pyodide.js");
      const py = await window.loadPyodide!({ indexURL: INDEX_URL });
      await py.loadPackage(["pytest"]);
      return py;
    })();
  }
  return pyodidePromise;
}

export interface RunResult {
  returncode: number; // 0=全绿, 非0=有失败或错误
  output: string;
}

export interface RunOptions {
  assignmentCode: string;
  testName: string; // 如 "ch01_assignment"
  testSource: string;
  conftestSource: string;
  mocks: Record<string, string>;
}

/** 把代码写进虚拟 FS 并跑 pytest。 */
export async function runChapterTests(opts: RunOptions): Promise<RunResult> {
  const py = await getPyodide();
  const FS = py.FS;
  const mkdir = (p: string) => {
    try {
      FS.mkdir(p);
    } catch {
      /* 已存在 */
    }
  };

  mkdir("/work");
  mkdir("/work/assets");
  mkdir("/work/assets/mock_data");

  FS.writeFile("/work/conftest.py", opts.conftestSource);
  FS.writeFile(`/work/${opts.testName}.py`, opts.assignmentCode);
  FS.writeFile(`/work/test_${opts.testName}.py`, opts.testSource);
  for (const [name, content] of Object.entries(opts.mocks)) {
    FS.writeFile(`/work/assets/mock_data/${name}`, content);
  }

  // redirect_stdout/stderr 把 pytest 输出收进 buf;最后返回 dict 给 JS。
  const script = `
import io, contextlib, sys
sys.path.insert(0, "/work")
import pytest
buf = io.StringIO()
with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
    rc = pytest.main([
        "/work/test_${opts.testName}.py",
        "-v", "--tb=short", "--color=no",
        "-p", "no:cacheprovider",
        "--rootdir=/work",
    ])
{"output": buf.getvalue(), "returncode": int(rc)}
`;

  const proxy = await py.runPythonAsync(script);
  const result = proxy.toJs({ dict_converter: Object.fromEntries });
  if (typeof proxy.destroy === "function") proxy.destroy();
  return { returncode: result.returncode, output: result.output || "" };
}

export interface FuncDefLite {
  name: string;
  skeleton: string;
}

export interface FunctionRunOptions {
  testName: string; // "ch01_assignment"
  testSource: string;
  conftestSource: string;
  mocks: Record<string, string>;
  preamble: string;
  functions: FuncDefLite[]; // 全部函数(取其余的骨架)
  activeFunction: string; // 当前在练的函数名
  userCode: string; // 用户为该函数写的代码
  testClass: string; // "TestAdd"
}

/** 单函数练习:把用户代码 + 其余函数骨架组装成完整模块,只跑该函数的测试类。 */
export async function runFunctionTest(opts: FunctionRunOptions): Promise<RunResult> {
  const py = await getPyodide();
  const FS = py.FS;
  const mkdir = (p: string) => {
    try {
      FS.mkdir(p);
    } catch {
      /* 已存在 */
    }
  };
  mkdir("/work");
  mkdir("/work/assets");
  mkdir("/work/assets/mock_data");

  // 组装完整模块:前言 + 用户当前函数 + 其余函数骨架(保证 import 不缺名)
  const others = opts.functions
    .filter((f) => f.name !== opts.activeFunction)
    .map((f) => f.skeleton)
    .join("\n\n\n");
  const moduleSource = `${opts.preamble}\n\n\n${opts.userCode}\n\n\n${others}\n`;

  FS.writeFile("/work/conftest.py", opts.conftestSource);
  FS.writeFile(`/work/${opts.testName}.py`, moduleSource);
  FS.writeFile(`/work/test_${opts.testName}.py`, opts.testSource);
  for (const [name, content] of Object.entries(opts.mocks)) {
    FS.writeFile(`/work/assets/mock_data/${name}`, content);
  }

  // 只跑该测试类:pytest path::TestClass
  const script = `
import io, contextlib, sys
sys.path.insert(0, "/work")
import pytest
buf = io.StringIO()
with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
    rc = pytest.main([
        "/work/test_${opts.testName}.py::${opts.testClass}",
        "-v", "--tb=short", "--color=no",
        "-p", "no:cacheprovider",
        "--rootdir=/work",
    ])
{"output": buf.getvalue(), "returncode": int(rc)}
`;
  const proxy = await py.runPythonAsync(script);
  const result = proxy.toJs({ dict_converter: Object.fromEntries });
  if (typeof proxy.destroy === "function") proxy.destroy();
  return { returncode: result.returncode, output: result.output || "" };
}
