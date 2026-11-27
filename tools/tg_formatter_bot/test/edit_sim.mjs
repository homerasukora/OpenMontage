// Offline check: missing visual -> bot asks -> photo attached; button editor (links, reactions, colours); live reaction counters.
// npx wrangler deploy --dry-run --outdir dist && node test/edit_sim.mjs $PWD/dist/index.js
import { loadWorker, doNamespace } from "./load.mjs";
const mod = await loadWorker(process.argv[2]);
const kv = new Map();
const LAYOUT = { headline: "5 months and 1 new bike", headline_emoji: "🏍️", blocks: [{ type: "text", text: "***Rahul from Nagpur*** sent his manager this photo today." }], cta: "Talk to Arnold today", hashtag: "cases", buttons: [{ link: "manager", text: "TALK TO ARNOLD" }] };
const env = { BOT_TOKEN: "123:TEST", OWNER_ID: "726625635", CHANNEL_ID: "-1005659106771", PREMIUM_EMOJI: "off", PLAN_URL: "https://script.google.com/x", PLAN_KEY: "k", PLAN_STATUS: "on",
  AI: { run: async () => ({ choices: [{ message: { content: JSON.stringify(LAYOUT) } }] }) },
  DRAFTS: { get: async (k) => kv.get(k)?.v ?? null, getWithMetadata: async (k) => ({ value: kv.get(k)?.v ?? null, metadata: kv.get(k)?.m }), put: async (k, v, o) => kv.set(k, { v, m: o?.metadata }), delete: async (k) => kv.delete(k) } };
env.REACTIONS = await doNamespace(mod.Reactions, () => env);
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
const say = (text, entities) => post({ message: { message_id: 500 + uid, chat, from: me, text, entities } });

await say("07.12");
const prev = sent.find((s) => s[0] === "sendMessage" && kbOf(s[1]).flat().some((b) => b.callback_data?.startsWith("pub:")));
const id = kbOf(prev[1]).flat().find((b) => b.callback_data?.startsWith("pub:")).callback_data.split(":")[1];
console.log("bot asks:", sent.find((s) => s[1].text?.startsWith?.("🖼"))[1].text.split("\n")[0]);
await post({ message: { message_id: 700, chat, from: me, photo: [{ file_id: "small" }, { file_id: "BIG_PHOTO" }] } });
console.log("photo attached:", sent.filter((s) => s[0] === "sendPhoto").length === 1);
await click(`bm:${id}`); console.log("editor:\n   " + show(lastKb()));
await click(`be:${id}:u:0`); console.log("link button settings:\n   " + show(lastKb()));
await click(`bc:${id}:u:0`); console.log("colour ->", lastKb()[0][0].style);
await click(`bl:${id}:0`); console.log("link menu:\n   " + show(lastKb()));
await click(`bs:${id}:0:start`); console.log("after preset:", show(lastKb()).split("\n")[0]);
await click(`bt:${id}:0`); await say("START WITH ARNOLD"); console.log("after text:", show(lastKb()).split("\n")[0]);
await click(`bm:${id}`);
await click(`ba:${id}:r`); console.log("asks:", sent.at(-1)[1].text.split("\n")[0]);
const txt = "❤️🔥 x👍🇮🇳";   // the 🔥 pretends to be a premium emoji
await say(txt, [{ type: "custom_emoji", offset: 2, length: 2, custom_emoji_id: "5368324170671202286" }]);
console.log("bot:", sent.at(-1)[1].text.replace(/\n/g, " / "));
console.log("editor with reactions:\n   " + show(lastKb()));
await click(`be:${id}:r:1`); console.log("reaction settings:\n   " + show(lastKb()));
await click(`bc:${id}:r:1`); await click(`bd:${id}:r:3`); await click(`bk:${id}`);
console.log("main keyboard:\n   " + show(lastKb()));
sent.length = 0;
await click(`pub:${id}`);
const pub = sent.find((s) => s[1].chat_id === "-1005659106771");
console.log("published:", pub[0], "\n   " + show(kbOf(pub[1])));
// subscribers tap reactions in the channel
const chMsg = Number(env.REACTIONS.names()[0].split(":").pop());
const tap = (user, data) => post({ callback_query: { id: "x" + uid, from: { id: user }, data, message: { message_id: chMsg, chat: { id: -1005659106771, type: "channel" } } } });
await tap(1, "r:0"); await tap(2, "r:0"); await tap(3, "r:1"); await tap(2, "r:1"); await tap(4, "r:2"); await tap(4, "r:2");
console.log("answers:", sent.filter((s) => s[0] === "answerCallbackQuery" && s[1].callback_query_id.startsWith("x")).map((s) => s[1].text).join(", "));
for (const o of env.REACTIONS.all()) await o.runAlarm();
const upd = [...sent].reverse().find((s) => s[0] === "editMessageReplyMarkup" && s[1].chat_id === "-1005659106771");
console.log("channel keyboard after taps (msg " + upd[1].message_id + "):\n   " + show(kbOf(upd[1])));
await post({ callback_query: { id: "y1", from: { id: 5 }, data: `pub:${id}`, message: { message_id: 999, chat: { id: 5 } } } });
console.log("stranger presses pub:", sent.at(-1)[1].text);
