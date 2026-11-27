// Offline check of PREMIUM_EMOJI="owner": premium emoji in the private preview, «🙋 Опубликую сам» copy,
// buttons added to the owner's forwarded channel post, bot publishing without premium emoji.
// npx wrangler deploy --dry-run --outdir dist && node test/owner_sim.mjs $PWD/dist/index.js
import { loadWorker, doNamespace } from "./load.mjs";
const mod = await loadWorker(process.argv[2]);
const kv = new Map();
const LAYOUT = { headline: "Free P2P course", headline_emoji: "👨‍🎓", blocks: [{ type: "quote", items: [{ emoji: "🔥", text: "Hot offer for new traders" }] }], cta: "Start today", hashtag: "terms", buttons: [{ link: "start", text: "START WORKING" }] };
const env = { BOT_TOKEN: "123:TEST", OWNER_ID: "726625635", CHANNEL_ID: "-1005659106771", PREMIUM_EMOJI: "owner",
  AI: { run: async () => ({ choices: [{ message: { content: JSON.stringify(LAYOUT) } }] }) },
  DRAFTS: { get: async (k) => kv.get(k)?.v ?? null, getWithMetadata: async (k) => ({ value: kv.get(k)?.v ?? null }), put: async (k, v) => kv.set(k, { v }), delete: async (k) => kv.delete(k) } };
env.REACTIONS = await doNamespace(mod.Reactions, () => env);
let mid = 100; const sent = [];
globalThis.fetch = async (url, init) => { sent.push([String(url).split("/").pop(), JSON.parse(init.body)]); return new Response(JSON.stringify({ ok: true, result: { message_id: ++mid } })); };
const secret = await (async () => { const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`whk:${env.BOT_TOKEN}`)); return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 48); })();
let uid = 0;
const post = (u) => mod.default.fetch(new Request("https://b.workers.dev/webhook", { method: "POST", headers: { "X-Telegram-Bot-Api-Secret-Token": secret }, body: JSON.stringify({ update_id: ++uid, ...u }) }), env, { waitUntil() {} });
const me = { id: 726625635 }, chat = { id: 726625635, type: "private" };
const click = (data) => post({ callback_query: { id: "c" + uid, from: me, data, message: { message_id: 999, chat } } });
await post({ message: { message_id: 1, chat, from: me, text: "Free P2P course. Hot offer for new traders. Start today" } });
const prev = sent.find((s) => s[0] === "sendMessage" && s[1].reply_markup?.inline_keyboard?.flat().some((b) => b.callback_data?.startsWith("pub:")));
console.log("preview has premium:", /tg-emoji/.test(prev[1].text));
console.log("keyboard:", prev[1].reply_markup.inline_keyboard.map((r) => r.map((b) => b.text).join(" | ")).join(" / "));
const id = prev[1].reply_markup.inline_keyboard.flat().find((b) => b.callback_data?.startsWith("pub:")).callback_data.split(":")[1];
await click(`ba:${id}:r`); await post({ message: { message_id: 2, chat, from: me, text: "❤️👍" } }); await click(`bk:${id}`);
sent.length = 0;
await click(`self:${id}`);
const copy = sent.find((s) => s[0] === "sendMessage" && /tg-emoji/.test(s[1].text || ""));
console.log("clean copy: premium", !!copy, "| keyboard:", copy?.[1].reply_markup ?? "none");
console.log("instruction:", sent.at(-1)[1].text.split("\n")[0]);
sent.length = 0;
const ch = { id: -1005659106771, type: "channel", title: "Test" };
await post({ channel_post: { message_id: 77, chat: ch, text: "Some other post" } });
console.log("unrelated post ignored:", sent.length === 0);
await post({ channel_post: { message_id: 78, chat: ch, text: "Free P2P course 👨‍🎓\n\n🔥 Hot offer for new traders\n\nStart today 👇\n\n#terms" } });
const ed = sent.find((s) => s[0] === "editMessageReplyMarkup");
console.log("buttons added to channel post", ed[1].message_id, ":", JSON.stringify(ed[1].reply_markup.inline_keyboard));
console.log("owner told:", sent.at(-1)[1].text);
await post({ callback_query: { id: "t1", from: { id: 9 }, data: "r:0", message: { message_id: 78, chat: ch } } });
for (const o of env.REACTIONS.all()) await o.runAlarm();
console.log("reaction counter on forwarded post:", JSON.stringify(sent.filter((s) => s[0] === "editMessageReplyMarkup").at(-1)[1].reply_markup.inline_keyboard[1]));
sent.length = 0;
await click(`pub:${id}`);
const pub = sent.find((s) => s[1].chat_id === "-1005659106771");
console.log("bot publish has premium:", /tg-emoji/.test(pub[1].text), "| icons:", JSON.stringify(pub[1].reply_markup).includes("icon_custom"));
