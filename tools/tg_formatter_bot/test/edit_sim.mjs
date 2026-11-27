// Offline check: plan post without a visual -> bot asks -> owner sends a photo; button editor (text, link, colour, add, delete).
// npx wrangler deploy --dry-run --outdir dist && node test/edit_sim.mjs $PWD/dist/index.js
const mod = await import(process.argv[2]);
const kv = new Map();
const LAYOUT = { headline: "5 months and 1 new bike", headline_emoji: "🏍️", blocks: [{ type: "text", text: "***Rahul from Nagpur*** sent his manager this photo today." }], cta: "Talk to Arnold today", hashtag: "cases", buttons: [{ link: "manager", text: "TALK TO ARNOLD" }] };
const env = { BOT_TOKEN: "123:TEST", OWNER_ID: "726625635", CHANNEL_ID: "-1005659106771", PREMIUM_EMOJI: "off", PLAN_URL: "https://script.google.com/x", PLAN_KEY: "k", PLAN_STATUS: "on",
  AI: { run: async () => ({ choices: [{ message: { content: JSON.stringify(LAYOUT) } }] }) },
  DRAFTS: { get: async (k) => kv.get(k)?.v ?? null, getWithMetadata: async (k) => ({ value: kv.get(k)?.v ?? null, metadata: kv.get(k)?.m }), put: async (k, v, o) => kv.set(k, { v, m: o?.metadata }), delete: async (k) => kv.delete(k) } };
let mid = 100; const sent = [];
globalThis.fetch = async (url, init) => {
  url = String(url);
  if (url.startsWith(env.PLAN_URL)) {
    const b = JSON.parse(init.body);
    return new Response(JSON.stringify(b.action === "post" ? { found: true, date: "07.12", status: "Choose", topic: "Мотоцикл", text: "5 months with Ganesha Pay and 1 new bike\nRahul from Nagpur sent his manager this photo today.\nTalk to Arnold today 👇\n#cases", visualNote: "Фото трейдера или дашборд", file: null } : { ok: true }));
  }
  if (url.includes("/file/bot")) return new Response(new Uint8Array([1, 2, 3, 4]));
  const method = url.split("/").pop();
  const body = init.body instanceof FormData ? Object.fromEntries(init.body.entries()) : JSON.parse(init.body);
  sent.push([method, body]);
  const result = method === "getFile" ? { file_path: "photos/x.jpg" } : { message_id: ++mid, ...(method === "sendPhoto" ? { photo: [{ file_id: body.photo }] } : {}) };
  return new Response(JSON.stringify({ ok: true, result }));
};
const secret = await (async () => { const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`whk:${env.BOT_TOKEN}`)); return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 48); })();
let uid = 0;
const post = (u) => mod.default.fetch(new Request("https://bot.example.workers.dev/webhook", { method: "POST", headers: { "X-Telegram-Bot-Api-Secret-Token": secret }, body: JSON.stringify({ update_id: ++uid, ...u }) }), env, { waitUntil() {} });
const me = { id: 726625635 }, chat = { id: 726625635, type: "private" };
const kbOf = (m) => (typeof m.reply_markup === "string" ? JSON.parse(m.reply_markup) : m.reply_markup)?.inline_keyboard || [];
const lastKb = () => kbOf([...sent].reverse().find((s) => s[0] === "editMessageReplyMarkup")[1]);
const show = (rows) => rows.map((r) => r.map((b) => b.text + (b.style ? `[${b.style}]` : "") + (b.url ? `→${b.url.split("/").pop()}` : "")).join(" | ")).join("\n   ");
const click = (data) => post({ callback_query: { id: "c" + uid, from: me, data, message: { message_id: 999, chat } } });
const say = (text) => post({ message: { message_id: 500 + uid, chat, from: me, text } });

await say("07.12");
const prev = sent.find((s) => s[0] === "sendMessage" && kbOf(s[1]).flat().some((b) => b.callback_data?.startsWith("pub:")));
const id = kbOf(prev[1]).flat().find((b) => b.callback_data?.startsWith("pub:")).callback_data.split(":")[1];
console.log("preview (no visual) via", prev[0], "\n   " + show(kbOf(prev[1])));
console.log("bot asks:", sent.find((s) => s[1].text?.startsWith?.("🖼"))[1].text);
sent.length = 0;
await post({ message: { message_id: 700, chat, from: me, photo: [{ file_id: "small" }, { file_id: "BIG_PHOTO" }] } });
const p2 = sent.find((s) => s[0] === "sendPhoto");
console.log("after photo: deleted old preview:", sent.some((s) => s[0] === "deleteMessage"), "| new preview via", p2[0], "photo=" + p2[1].photo, "| kv copy:", [...kv.keys()].some((k) => k.startsWith("img:")));
console.log("   " + show(kbOf(p2[1])));
await click(`bm:${id}`); console.log("editor:\n   " + show(lastKb()));
await click(`bc:${id}:0`); await click(`bc:${id}:0`); console.log("after 2× colour:\n   " + show(lastKb()).split("\n")[0]);
await click(`bt:${id}:0`); await say("WRITE TO ARNOLD"); console.log("text changed:", show(lastKb()).split("\n")[0]);
await click(`bl:${id}:0`); console.log("link menu:\n   " + show(lastKb()));
await click(`bs:${id}:0:start`); console.log("link -> start:", show(lastKb()).split("\n")[0]);
await click(`bl:${id}:0`); await click(`bu:${id}:0`); await say("not a link"); console.log("bad url reply:", sent.at(-1)[1].text);
await say("t.me/ganeshapay"); console.log("custom url:", show(lastKb()).split("\n")[0]);
await click(`ba:${id}`); console.log("added:\n   " + show(lastKb()));
await click(`bd:${id}:1`); await click(`bk:${id}`); console.log("deleted 2nd, done:\n   " + show(lastKb()));
sent.length = 0;
await click(`pub:${id}`);
const pub = sent.find((s) => s[1].chat_id === "-1005659106771");
console.log("published:", pub[0], "photo=" + pub[1].photo, "buttons:", JSON.stringify(kbOf(pub[1])));
