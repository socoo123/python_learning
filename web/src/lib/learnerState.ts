/**
 * 学习进度 + 网页作业草稿。
 * - 始终写入 localStorage（刷新不丢）
 * - bun run dev 时同步到 web/.learner-state.json（换浏览器 / 重启 dev 也能读到）
 */

export const LEARNER_STORAGE_KEY = "py-learn:learner-state:v1";
export const LEARNER_API = "/api/learner-state";
export const LEARNER_FILE_HINT = "web/.learner-state.json";

export interface ChapterDraft {
  assignment?: string;
  functions?: Record<string, string>;
}

export interface LearnerState {
  version: 1;
  updatedAt: string;
  completedChapters: string[];
  drafts: Record<string, ChapterDraft>;
}

export type Persistence = "pending" | "file" | "browser";

export interface LearnerSnapshot {
  state: LearnerState;
  ready: boolean;
  persistence: Persistence;
}

export function emptyState(): LearnerState {
  return { version: 1, updatedAt: "", completedChapters: [], drafts: {} };
}

export function normalizeState(raw: unknown): LearnerState | null {
  if (!raw || typeof raw !== "object") return null;
  const o = raw as Record<string, unknown>;
  if (o.version !== 1) return null;
  const completed = Array.isArray(o.completedChapters)
    ? o.completedChapters.filter((id): id is string => typeof id === "string")
    : [];
  const drafts: Record<string, ChapterDraft> = {};
  if (o.drafts && typeof o.drafts === "object") {
    for (const [k, v] of Object.entries(o.drafts as Record<string, unknown>)) {
      if (!v || typeof v !== "object") continue;
      const d = v as ChapterDraft;
      drafts[k] = {
        assignment: typeof d.assignment === "string" ? d.assignment : undefined,
        functions:
          d.functions && typeof d.functions === "object"
            ? Object.fromEntries(
                Object.entries(d.functions).filter(([, code]) => typeof code === "string"),
              )
            : undefined,
      };
    }
  }
  return {
    version: 1,
    updatedAt: typeof o.updatedAt === "string" ? o.updatedAt : "",
    completedChapters: [...new Set(completed)],
    drafts,
  };
}

function loadLocal(): LearnerState {
  try {
    const raw = localStorage.getItem(LEARNER_STORAGE_KEY);
    if (!raw) return emptyState();
    return normalizeState(JSON.parse(raw)) ?? emptyState();
  } catch {
    return emptyState();
  }
}

function writeLocal(state: LearnerState) {
  try {
    localStorage.setItem(LEARNER_STORAGE_KEY, JSON.stringify(state));
  } catch {
    // quota / 隐私模式：忽略，文件通道仍可能成功
  }
}

async function fetchFileState(): Promise<LearnerState | null> {
  try {
    const res = await fetch(LEARNER_API, { cache: "no-store" });
    if (!res.ok) return null;
    const ct = res.headers.get("content-type") ?? "";
    if (!ct.includes("application/json")) return null;
    return normalizeState(await res.json());
  } catch {
    return null;
  }
}

async function putFileState(state: LearnerState): Promise<boolean> {
  try {
    const res = await fetch(LEARNER_API, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state),
      keepalive: true,
    });
    const ct = res.headers.get("content-type") ?? "";
    return res.ok && ct.includes("application/json");
  } catch {
    return false;
  }
}

type Listener = () => void;

const progressListeners = new Set<Listener>();

let snapshot: LearnerSnapshot = {
  state: typeof localStorage !== "undefined" ? loadLocal() : emptyState(),
  ready: false,
  persistence: "pending",
};

let fileTimer: ReturnType<typeof setTimeout> | null = null;
let hydrateStarted = false;

function emit(patch: Partial<LearnerSnapshot>) {
  snapshot = { ...snapshot, ...patch };
  progressListeners.forEach((l) => l());
}

function persist(next: LearnerState, notifyProgress: boolean) {
  writeLocal(next);
  if (notifyProgress) emit({ state: next });
  else snapshot = { ...snapshot, state: next };

  if (fileTimer) clearTimeout(fileTimer);
  fileTimer = setTimeout(() => {
    void putFileState(snapshot.state).then((ok) => {
      const persistence: Persistence = ok ? "file" : "browser";
      if (snapshot.persistence !== persistence) emit({ persistence });
    });
  }, 450);
}

function mutate(updater: (s: LearnerState) => LearnerState, notifyProgress: boolean) {
  const next: LearnerState = {
    ...updater(snapshot.state),
    version: 1,
    updatedAt: new Date().toISOString(),
  };
  persist(next, notifyProgress);
}

export function subscribeProgress(listener: Listener): () => void {
  progressListeners.add(listener);
  return () => progressListeners.delete(listener);
}

export function getProgressSnapshot(): LearnerSnapshot {
  return snapshot;
}

export function isComplete(chapterId: string): boolean {
  return snapshot.state.completedChapters.includes(chapterId);
}

export function setChapterComplete(chapterId: string, complete: boolean) {
  mutate((s) => {
    const set = new Set(s.completedChapters);
    if (complete) set.add(chapterId);
    else set.delete(chapterId);
    return { ...s, completedChapters: [...set] };
  }, true);
}

export function toggleChapterComplete(chapterId: string) {
  setChapterComplete(chapterId, !isComplete(chapterId));
}

export function getAssignmentDraft(chapterId: string): string | undefined {
  return snapshot.state.drafts[chapterId]?.assignment;
}

export function getFunctionDraft(chapterId: string, funcName: string): string | undefined {
  return snapshot.state.drafts[chapterId]?.functions?.[funcName];
}

function pruneDraft(draft: ChapterDraft | undefined): ChapterDraft | undefined {
  if (!draft) return undefined;
  const functions = draft.functions
    ? Object.fromEntries(Object.entries(draft.functions).filter(([, v]) => v.length > 0))
    : undefined;
  const next: ChapterDraft = {};
  if (draft.assignment) next.assignment = draft.assignment;
  if (functions && Object.keys(functions).length) next.functions = functions;
  return next.assignment || next.functions ? next : undefined;
}

export function saveAssignmentDraft(chapterId: string, code: string, skeleton: string) {
  mutate((s) => {
    const prev = s.drafts[chapterId] ?? {};
    const assignment = code === skeleton ? undefined : code;
    const draft = pruneDraft({ ...prev, assignment });
    const drafts = { ...s.drafts };
    if (draft) drafts[chapterId] = draft;
    else delete drafts[chapterId];
    return { ...s, drafts };
  }, false);
}

export function saveFunctionDraft(chapterId: string, funcName: string, code: string, skeleton: string) {
  mutate((s) => {
    const prev = s.drafts[chapterId] ?? {};
    const functions = { ...(prev.functions ?? {}) };
    if (!code || code === skeleton) delete functions[funcName];
    else functions[funcName] = code;
    const draft = pruneDraft({ ...prev, functions });
    const drafts = { ...s.drafts };
    if (draft) drafts[chapterId] = draft;
    else delete drafts[chapterId];
    return { ...s, drafts };
  }, false);
}

export async function hydrateLearnerState(): Promise<void> {
  if (hydrateStarted) return;
  hydrateStarted = true;

  const filePromise = fetchFileState();
  let timeoutId: ReturnType<typeof setTimeout> | undefined;
  const timeout = new Promise<"timeout">((r) => {
    timeoutId = setTimeout(() => r("timeout"), 800);
  });
  const first = await Promise.race([filePromise.then((f) => f ?? "none"), timeout]);
  if (timeoutId) clearTimeout(timeoutId);

  if (first === "timeout") {
    // 先让 UI 用 localStorage 起来；文件结果稍后仍会合并，绝不超时写空覆盖。
    emit({ ready: true, persistence: "browser" });
  }

  const file = first === "timeout" || first === "none" ? await filePromise : first;
  const local = snapshot.state;

  if (file) {
    const useFile = (file.updatedAt || "") > (local.updatedAt || "");
    const next = useFile ? file : local;
    writeLocal(next);
    emit({ state: next, ready: true, persistence: "file" });
    if (!useFile && local.updatedAt) void putFileState(local);
    return;
  }

  const ok = await putFileState(local);
  emit({ ready: true, persistence: ok ? "file" : "browser" });
}

if (typeof window !== "undefined") {
  window.addEventListener("pagehide", () => {
    if (fileTimer) {
      clearTimeout(fileTimer);
      fileTimer = null;
    }
    void putFileState(snapshot.state);
  });
}
