import indexData from "../content/index.json";
import sharedData from "../content/shared.json";
import type { Chapter, ChapterSummary, CurriculumIndex, Module, SharedContent } from "../types";

const index = indexData as CurriculumIndex;

export const modules: Module[] = index.modules;
export const shared: SharedContent = sharedData as SharedContent;

/** Vite 懒加载:只有点进某章才拉对应 JSON chunk */
const chapterLoaders = import.meta.glob("../content/chapters/*.json") as Record<
  string,
  () => Promise<{ default: Chapter }>
>;

const chapterCache = new Map<string, Chapter>();

export function getModule(moduleId: string): Module | undefined {
  return modules.find((m) => m.id === moduleId);
}

export function getChapterSummary(moduleId: string, chapterId: string): ChapterSummary | undefined {
  return getModule(moduleId)?.chapters.find((c) => c.id === chapterId);
}

export async function loadChapter(chapterId: string): Promise<Chapter | undefined> {
  const cached = chapterCache.get(chapterId);
  if (cached) return cached;

  const key = `../content/chapters/${chapterId}.json`;
  const loader = chapterLoaders[key];
  if (!loader) return undefined;

  const mod = await loader();
  const chapter = mod.default;
  chapterCache.set(chapterId, chapter);
  return chapter;
}
