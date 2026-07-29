export type RunMode = "pyodide" | "local";

export interface FuncDef {
  name: string;
  testClass: string;
  skeleton: string;
}

export interface Section {
  id: string;
  heading: string;
  secNum: string | null;
  body: string;
  exerciseFunctions: string[];
}

export interface Chapter {
  id: string;
  num: string;
  title: string;
  runMode: RunMode;
  tutorialMd: string;
  assignment: string;
  testName: string;
  testSource: string;
  reviewMd: string;
  // 交错式:
  interleaved: boolean;
  sections: Section[];
  functions: FuncDef[];
  preamble: string;
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
