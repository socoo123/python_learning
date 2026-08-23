/**
 * 学习进度 + 作业草稿落盘。
 * bun run dev / vite preview 时提供 GET/PUT /api/learner-state，
 * 写入 web/.learner-state.json（gitignored，不进课程源文件）。
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { IncomingMessage, ServerResponse } from "node:http";
import type { Plugin, PreviewServer, ViteDevServer } from "vite";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const WEB_DIR = path.resolve(__dirname, "..");
export const LEARNER_STATE_FILE = path.join(WEB_DIR, ".learner-state.json");
const ROUTE = "/api/learner-state";
const MAX_BODY = 2_000_000;

const EMPTY = {
  version: 1,
  updatedAt: "",
  completedChapters: [] as string[],
  drafts: {} as Record<string, unknown>,
};

function readBody(req: IncomingMessage): Promise<string> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    let size = 0;
    req.on("data", (chunk: Buffer) => {
      size += chunk.length;
      if (size > MAX_BODY) {
        req.destroy();
        reject(new Error("body too large"));
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    req.on("error", reject);
  });
}

function json(res: ServerResponse, status: number, body: unknown) {
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("Cache-Control", "no-store");
  res.end(JSON.stringify(body));
}

async function handle(req: IncomingMessage, res: ServerResponse): Promise<void> {
  const method = req.method ?? "GET";

  if (method === "GET") {
    if (!fs.existsSync(LEARNER_STATE_FILE)) {
      json(res, 200, EMPTY);
      return;
    }
    const raw = fs.readFileSync(LEARNER_STATE_FILE, "utf8");
    res.statusCode = 200;
    res.setHeader("Content-Type", "application/json; charset=utf-8");
    res.setHeader("Cache-Control", "no-store");
    res.end(raw);
    return;
  }

  if (method === "PUT") {
    let body: string;
    try {
      body = await readBody(req);
    } catch {
      json(res, 413, { error: "body too large" });
      return;
    }
    let parsed: unknown;
    try {
      parsed = JSON.parse(body);
    } catch {
      json(res, 400, { error: "invalid json" });
      return;
    }
    if (!parsed || typeof parsed !== "object") {
      json(res, 400, { error: "invalid payload" });
      return;
    }
    fs.writeFileSync(LEARNER_STATE_FILE, JSON.stringify(parsed, null, 2) + "\n", "utf8");
    json(res, 200, { ok: true });
    return;
  }

  json(res, 405, { error: "method not allowed" });
}

function attach(server: ViteDevServer | PreviewServer) {
  server.middlewares.use((req, res, next) => {
    const url = req.url?.split("?")[0];
    if (url !== ROUTE) {
      next();
      return;
    }
    void handle(req, res).catch(() => {
      if (!res.headersSent) json(res, 500, { error: "internal error" });
    });
  });
}

export function learnerStatePlugin(): Plugin {
  return {
    name: "learner-state",
    configureServer(server) {
      attach(server);
    },
    configurePreviewServer(server) {
      attach(server);
    },
  };
}
