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

/** 首页 / 模块列表用的轻量元数据(不含教程正文) */
export interface ChapterSummary {
  id: string;
  num: string;
  title: string;
  runMode: RunMode;
}

/** 课程页用的完整章节内容 */
export interface Chapter extends ChapterSummary {
  tutorialMd: string;
  assignment: string;
  testName: string;
  testSource: string;
  reviewMd: string;
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
  chapters: ChapterSummary[];
}

export interface CurriculumIndex {
  modules: Module[];
}

export interface SharedContent {
  conftest: string;
  mocks: Record<string, string>;
}

/** @deprecated 单体 curriculum 已拆分;保留别名方便旧引用 */
export type Curriculum = {
  modules: Module[];
  shared: SharedContent;
};
