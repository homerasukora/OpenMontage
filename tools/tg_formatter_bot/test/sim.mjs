// Offline check of the worker with mocked Telegram + Workers AI.
// npx wrangler deploy --dry-run --outdir dist && node test/sim.mjs $PWD/dist/index.js
const mod = await import(process.argv[2]);
const kv = new Map();
const LAYOUT = { headline: "Free P2P course", headline_emoji: "👨‍🎓", blocks: [{ type: "text", text: "Not sure what ***PAYIN*** means?" }, { type: "quote", items: [{ emoji: "⏳", text: "Around **20** minutes a day" }] }, { type: "text", text: "Learn it free in the [Academy](academy). Join the free course today." }], cta: "", hashtag: "knowledge", buttons: ["academy"] };
const DRAFT = "Free P2P course\nNot sure what PAYIN means?\nAround 20 minutes a day\nLearn it free in the Academy. Join the free course today.";
let aiCalls = 0;
const env = { BOT_TOKEN: "123:TEST", OWNER_ID: "726625635", CHANNEL_ID: "-1005659106771", MODEL: "@cf/qwen/qwen3.8-27b", PREMIUM_EMOJI: process.argv[3] || "off",
  AI: { run: async (model, input) => { aiCalls++; if (process.env.AI_FAIL) throw new Error("boom"); return { choices: [{ message: { content: "```json\n" + JSON.stringify(LAYOUT) + "\n```" } }], usage: { neurons: 1 } }; } },
  DRAFTS: { get: async (k) => kv.get(k) ?? null, put: async (k, v) => kv.set(k, v), delete: async (k) => kv.delete(k) } };
let mid = 100; const sent = [];
globalThis.fetch = async (url, init) => {
  const method = String(url).split("/").pop(); const body = JSON.parse(init.body); sent.push([method, body]);
  return new Response(JSON.stringify({ ok: true, result: { message_id: ++mid } }), { headers: { "content-type": "application/json" } });
};
const secretOf = async () => { const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`whk:${env.BOT_TOKEN}`)); return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 48); };
const ctx = { waitUntil() {} };
const post = async (u) => (await mod.default.fetch(new Request("https://x.workers.dev/webhook", { method: "POST", headers: { "X-Telegram-Bot-Api-Secret-Token": await secretOf() }, body: JSON.stringify(u) }), env, ctx)).text();
console.log("1", await post({ update_id: 1, message: { message_id: 1, chat: { id: 726625635, type: "private" }, from: { id: 726625635 }, text: DRAFT } }), "ai calls", aiCalls);
const prev = sent.find((s) => s[0] === "sendMessage" && s[1].parse_mode === "HTML");
console.log("preview html:\n" + prev[1].text);
console.log("keyboard:", JSON.stringify(prev[1].reply_markup.inline_keyboard.map((r) => r.map((b) => b.text))));
const notes = sent.find((s) => s[0] === "sendMessage" && s[1].text?.startsWith("📝")); console.log("notes:", notes ? notes[1].text : "—");
const draftId = prev[1].reply_markup.inline_keyboard.flat().find((b) => b.callback_data?.startsWith("pub:")).callback_data.split(":")[1];
console.log("2", await post({ update_id: 2, callback_query: { id: "c1", from: { id: 726625635 }, data: `tag:${draftId}:cases`, message: { message_id: 103, chat: { id: 726625635 } } } }));
console.log("3", await post({ update_id: 3, callback_query: { id: "c2", from: { id: 726625635 }, data: `pub:${draftId}`, message: { message_id: 103, chat: { id: 726625635 } } } }));
const pub = sent.find((s) => s[0] === "sendMessage" && s[1].chat_id === "-1005659106771");
console.log("published to", pub[1].chat_id, "buttons", JSON.stringify(pub[1].reply_markup), "last line:", pub[1].text.split("\n").pop());
console.log("4 dup", await post({ update_id: 3, callback_query: { id: "c2", from: { id: 726625635 }, data: `pub:${draftId}`, message: { message_id: 103, chat: { id: 726625635 } } } }));
console.log("5 stranger", await post({ update_id: 5, message: { message_id: 9, chat: { id: 1, type: "private" }, from: { id: 1 }, text: "hi" } }), sent.slice(-1)[0][1].text);
console.log("6 bad secret", (await mod.default.fetch(new Request("https://x.workers.dev/webhook", { method: "POST", body: "{}" }), env, ctx)).status);
console.log("7 debug w/o TEST_KEY", await (await mod.default.fetch(new Request("https://x.workers.dev/debug", { method: "POST", body: "{}" }), env, ctx)).text());
