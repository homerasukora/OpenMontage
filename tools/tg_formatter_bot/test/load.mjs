// Loads the bundled worker in Node: "cloudflare:workers" is replaced by a tiny DurableObject base class.
import { readFileSync, writeFileSync } from "node:fs";
export async function loadWorker(path) {
  const src = readFileSync(path, "utf8").replace(/import\s*\{\s*DurableObject\s*\}\s*from\s*"cloudflare:workers";/, "class DurableObject { constructor(ctx, env) { this.ctx = ctx; this.env = env; } }");
  const out = path.replace(/\.js$/, ".node.mjs");
  writeFileSync(out, src);
  return import(out + "?t=" + Date.now());
}
// In-memory Durable Object namespace backed by node:sqlite, with alarms run on demand.
export async function doNamespace(Cls, envRef) {
  const { DatabaseSync } = await import("node:sqlite");
  const objs = new Map();
  return {
    idFromName: (n) => n,
    get(name) {
      if (!objs.has(name)) {
        const db = new DatabaseSync(":memory:");
        let alarm = null;
        const ctx = { storage: {
          sql: { exec: (q, ...p) => { const st = db.prepare(q); const rows = /^\s*select/i.test(q) ? st.all(...p) : (st.run(...p), []); return { toArray: () => rows }; } },
          getAlarm: async () => alarm, setAlarm: async (t) => { alarm = t; },
        } };
        const o = new Cls(ctx, envRef());
        o.runAlarm = async () => { if (alarm) { alarm = null; await o.alarm(); } };
        objs.set(name, o);
      }
      return objs.get(name);
    },
    all: () => [...objs.values()],
    names: () => [...objs.keys()],
  };
}
