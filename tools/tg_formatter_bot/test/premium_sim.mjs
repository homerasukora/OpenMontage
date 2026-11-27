// Offline check of PREMIUM_EMOJI=on: text emoji -> <tg-emoji>, icons on link/reaction buttons, /emoji picks, fallback if Telegram refuses.
// npx wrangler deploy --dry-run --outdir dist && node test/premium_sim.mjs $PWD/dist/index.js
import { loadWorker, doNamespace } from "./load.mjs";
const mod = await loadWorker(process.argv[2]);
const kv = new Map();
const LAYOUT = { headline: "Free P2P course", headline_emoji: "👨‍🎓", blocks: [{ type: "quote", items: [{ emoji: "🔥", text: "Hot offer" }, { emoji: "💵", text: "Paid daily" }] }], cta: "Start today", hashtag: "terms", buttons: [{ link: "start", text: "START WORKING" }] };
let refuse = false;
const env = { BOT_TOKEN: "123:TEST", OWNER_ID: "726625635", CHANNEL_ID: "-1005659106771", PREMIUM_EMOJI: "on",
  AI: { run: async () => ({ choices: [{ message: { content: JSON.stringify(LAYOUT) } }] }) },
  DRAFTS: { get: async (k) => kv.get(k)?.v ?? null, getWithMetadata: async (k) => ({ value: kv.get(k)?.v ?? null }), put: async (k, v) => kv.set(k, { v }), delete: async (k) => kv.delete(k) } };
env.REACTIONS = await doNamespace(mod.Reactions, () => env);
let mid = 100; const sent = [];
globalThis.fetch = async (url, init) => {
  const method = String(url).split("/").pop(); const body = JSON.parse(init.body); sent.push([method, body]);
  if (refuse && /tg-emoji|icon_custom/.test(init.body)) return new Response(JSON.stringify({ ok: false, description: "Bad Request: custom emoji entities can't be used" }));
  if (method === "getMe") return new Response(JSON.stringify({ ok: true, result: { id: 42, username: "m_redactor_bot" } }));
  if (method === "getChat") return new Response(JSON.stringify({ ok: true, result: { id: 42, username: "m_redactor_bot", active_usernames: ["m_redactor_bot", "gflabs"] } }));
  return new Response(JSON.stringify({ ok: true, result: { message_id: ++mid } }));
};
const secret = await (async () => { const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`whk:${env.BOT_TOKEN}`)); return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 48); })();
let uid = 0;
const post = (u) => mod.default.fetch(new Request("https://b.workers.dev/webhook", { method: "POST", headers: { "X-Telegram-Bot-Api-Secret-Token": secret }, body: JSON.stringify({ update_id: ++uid, ...u }) }), env, { waitUntil() {} });
const me = { id: 726625635 }, chat = { id: 726625635, type: "private" };
const say = (text, entities) => post({ message: { message_id: 500 + uid, chat, from: me, text, entities } });
const click = (data) => post({ callback_query: { id: "c" + uid, from: me, data, message: { message_id: 999, chat } } });
await say("/channel"); console.log(sent.at(-1)[1].text.split("\n").pop());
await say("/emoji"); await say("💵", [{ type: "custom_emoji", offset: 0, length: 2, custom_emoji_id: "777" }]); console.log(sent.at(-1)[1].text.split("\n")[0]);
await say("Free P2P course. Hot offer. Paid daily. Start today");
const prev = sent.find((s) => s[0] === "sendMessage" && s[1].reply_markup?.inline_keyboard?.flat().some((b) => b.callback_data?.startsWith("pub:")));
console.log(prev[1].text);
console.log("link button:", JSON.stringify(prev[1].reply_markup.inline_keyboard[0][0]));
const id = prev[1].reply_markup.inline_keyboard.flat().find((b) => b.callback_data?.startsWith("pub:")).callback_data.split(":")[1];
await click(`ba:${id}:r`); await say("❤️🔥", [{ type: "custom_emoji", offset: 2, length: 2, custom_emoji_id: "555" }]);
await click(`bk:${id}`);
console.log("reaction row:", JSON.stringify(sent.filter((s) => s[0] === "editMessageReplyMarkup").at(-1)[1].reply_markup.inline_keyboard[1]));
refuse = true; sent.length = 0;
await say("Another post. Hot offer. Start today");
const fb = sent.filter((s) => s[0] === "sendMessage" && s[1].parse_mode === "HTML");
console.log("fallback preview has tg-emoji:", /tg-emoji/.test(fb.at(-1)[1].text), "| note:", sent.find((s) => s[1].text?.startsWith?.("📝"))?.[1].text.slice(0, 80));
