// Offline check of the content-plan flow with mocked Telegram, Workers AI and Apps Script.
// npx wrangler deploy --dry-run --outdir dist && node test/plan_sim.mjs $PWD/dist/index.js [long]
import { loadWorker, doNamespace } from "./load.mjs";
const mod = await loadWorker(process.argv[2]);
const LONG = process.argv[3] === "long";
const kv = new Map();
const PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==";
const TEXT = "🔥 HOT: ₹93,780 earned in one week\nMehul from Jodhpur works with 2 business bank accounts.\n\nTalk to our manager 👇\nhttps://g.ganeshapay.io/smmtg-mng\n\n#cases" + (LONG ? "\n" + "More details about the week. ".repeat(45) : "");
const LAYOUT = { headline: "HOT: ₹93,780 earned in one week", headline_emoji: "🔥", blocks: [{ type: "text", text: "***Mehul from Jodhpur*** works with **2** business bank accounts." + (LONG ? " " + "More details about the week. ".repeat(45) : "") }], cta: "Talk to our manager", hashtag: "terms", buttons: [{ link: "start", text: "ASK ABOUT PAYOUTS" }] };
const env = { BOT_TOKEN: "123:TEST", OWNER_ID: "726625635", CHANNEL_ID: "-1005659106771", MODEL: "@cf/qwen/qwen3.8-27b", PREMIUM_EMOJI: "off", PLAN_URL: "https://script.google.com/macros/s/X/exec", PLAN_KEY: "k",
  AI: { run: async () => ({ choices: [{ message: { content: JSON.stringify(LAYOUT) } }] }) },
  DRAFTS: { get: async (k, t) => kv.get(k)?.v ?? null, getWithMetadata: async (k) => ({ value: kv.get(k)?.v ?? null, metadata: kv.get(k)?.m }), put: async (k, v, o) => kv.set(k, { v, m: o?.metadata }), delete: async (k) => kv.delete(k) } };
let mid = 100; const sent = []; const planCalls = [];
globalThis.fetch = async (url, init) => {
  url = String(url);
  if (url.startsWith(env.PLAN_URL)) {
    const b = JSON.parse(init.body); planCalls.push(b.action + (b.date ? ":" + b.date : ""));
    const res = b.action === "list" ? { posts: [{ date: "27.11", status: "Posted", topic: "Ganesha Pay Academy", hasText: true }, { date: "29.11", status: "Choose", topic: "Недельный доход", hasText: true }] }
      : b.action === "post" ? (b.date === "29.11" ? { found: true, date: "29.11", status: "Choose", topic: "Недельный доход", text: TEXT, poll: "", file: { name: "dash.png", mime: "image/png", b64: PNG } } : { found: false })
      : { ok: true };
    return new Response(JSON.stringify(res));
  }
  const method = url.split("/").pop();
  let body = init.body instanceof FormData ? Object.fromEntries([...init.body.entries()].map(([k, v]) => [k, typeof v === "string" ? v : `<file ${v.size}b ${v.type}>`])) : JSON.parse(init.body);
  sent.push([method, body]);
  const result = { message_id: ++mid };
  if (method === "sendPhoto") result.photo = [{ file_id: "PHOTO_FILE_ID" }];
  return new Response(JSON.stringify({ ok: true, result }));
};
const secret = await (async () => { const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`whk:${env.BOT_TOKEN}`)); return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 48); })();
let uid = 0;
const post = async (u) => (await mod.default.fetch(new Request("https://bot.example.workers.dev/webhook", { method: "POST", headers: { "X-Telegram-Bot-Api-Secret-Token": secret }, body: JSON.stringify({ update_id: ++uid, ...u }) }), env, { waitUntil() {} })).text();
const me = { id: 726625635 }, chat = { id: 726625635, type: "private" };
await post({ message: { message_id: 1, chat, from: me, text: "📅 Контент-план" } });
const list = sent.find((s) => s[1].reply_markup?.inline_keyboard?.[0]?.[0]?.callback_data?.startsWith("plan:"));
console.log("list:", list[1].reply_markup.inline_keyboard.map((r) => r[0].text));
sent.length = 0;
await post({ callback_query: { id: "c", from: me, data: "plan:29.11", message: { message_id: 50, chat } } });
const prev = sent.find((s) => ["sendPhoto", "sendMessage"].includes(s[0]) && s[1].reply_markup && JSON.stringify(s[1].reply_markup).includes("pub:"));
console.log("preview via", prev[0], prev[0] === "sendPhoto" ? "photo=" + prev[1].photo : "preview=" + JSON.stringify(JSON.parse(JSON.stringify(prev[1].link_preview_options || {}))));
console.log((prev[1].caption || prev[1].text).slice(0, 400));
const kb = typeof prev[1].reply_markup === "string" ? JSON.parse(prev[1].reply_markup) : prev[1].reply_markup;
console.log("buttons:", JSON.stringify(kb.inline_keyboard.slice(0, 2)));
console.log("notes:", sent.filter((s) => s[1].text?.startsWith?.("📝")).map((s) => s[1].text));
const draftId = kb.inline_keyboard.flat().find((b) => b.callback_data?.startsWith("pub:")).callback_data.split(":")[1];
if (prev[0] === "sendMessage") { const imgUrl = new URL(prev[1].link_preview_options.url); const r = await mod.default.fetch(new Request(imgUrl), env, {}); console.log("img route:", r.status, r.headers.get("content-type"), (await r.arrayBuffer()).byteLength, "bytes"); }
sent.length = 0;
await post({ callback_query: { id: "c2", from: me, data: `pub:${draftId}`, message: { message_id: 103, chat } } });
const pub = sent.find((s) => s[1].chat_id === env.CHANNEL_ID || s[1].chat_id === "-1005659106771");
console.log("published:", pub[0], pub[0] === "sendPhoto" ? "photo=" + pub[1].photo : "", "| channel buttons:", JSON.stringify(pub[1].reply_markup));
console.log("confirm:", sent.find((s) => s[1].text?.startsWith?.("✅"))[1].text);
await post({ message: { message_id: 2, chat, from: me, text: "31.12" } });
console.log("missing date:", sent.slice(-2).map((s) => s[1].text).join(" | "));
console.log("plan calls:", planCalls.join(", "));
