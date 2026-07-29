import curriculumData from "../content/curriculum.json";
import type { Curriculum, Module, Chapter } from "../types";

export const curriculum = curriculumData as unknown as Curriculum;

export const modules: Module[] = curriculum.modules;
export const shared = curriculum.shared;

export function getModule(moduleId: string): Module | undefined {
  return modules.find((m) => m.id === moduleId);
}

export function getChapter(moduleId: string, chapterId: string): Chapter | undefined {
  return getModule(moduleId)?.chapters.find((c) => c.id === chapterId);
}
