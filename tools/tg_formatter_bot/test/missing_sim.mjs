// Offline check: emoji without a premium version are listed; the owner replies with premium ones -> preview re-sent with them.
// npx wrangler deploy --dry-run --outdir dist && node test/missing_sim.mjs $PWD/dist/index.js
import { loadWorker, doNamespace } from "./load.mjs";
const mod = await loadWorker(process.argv[2]);
const kv = new Map();
let sys = "";
const LAYOUT = { headline: "Paid daily", headline_emoji: "💵", blocks: [{ type: "quote", items: [{ emoji: "🔥", text: "Hot offer" }, { emoji: "📥", text: "PayIn 3%" }] }], cta: "Start today", hashtag: "terms", buttons: [{ link: "start", text: "START WORKING" }] };
const env = { BOT_TOKEN: "123:TEST", OWNER_ID: "726625635", CHANNEL_ID: "-1005659106771", PREMIUM_EMOJI: "owner",
  AI: { run: async (m, input) => { sys = input.messages[0].content; return { choices: [{ message: { content: JSON.stringify(LAYOUT) } }] }; } },
  DRAFTS: { get: async (k) => kv.get(k)?.v ?? null, getWithMetadata: async (k) => ({ value: kv.get(k)?.v ?? null }), put: async (k, v) => kv.set(k, { v }), delete: async (k) => kv.delete(k) } };
env.REACTIONS = await doNamespace(mod.Reactions, () => env);
let mid = 100; const sent = [];
globalThis.fetch = async (url, init) => { sent.push([String(url).split("/").pop(), JSON.parse(init.body)]); return new Response(JSON.stringify({ ok: true, result: { message_id: ++mid } })); };
const secret = await (async () => { const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`whk:${env.BOT_TOKEN}`)); return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 48); })();
let uid = 0;
const post = (u) => mod.default.fetch(new Request("https://b.workers.dev/webhook", { method: "POST", headers: { "X-Telegram-Bot-Api-Secret-Token": secret }, body: JSON.stringify({ update_id: ++uid, ...u }) }), env, { waitUntil() {} });
const me = { id: 726625635 }, chat = { id: 726625635, type: "private" };
await post({ message: { message_id: 1, chat, from: me, text: "Paid daily. Hot offer. PayIn 3%. Start today" } });
console.log("prompt emoji rule:", sys.match(/- Use ONLY[^\n]*/)[0].slice(0, 90) + "…");
console.log("note:", sent.find((s) => s[1].text?.startsWith?.("📝"))[1].text);
const prev = sent.find((s) => s[0] === "sendMessage" && s[1].reply_markup?.inline_keyboard);
console.log("CTA button style:", prev[1].reply_markup.inline_keyboard[0][0].style);
sent.length = 0;
await post({ message: { message_id: 2, chat, from: me, text: "💵📥", entities: [{ type: "custom_emoji", offset: 0, length: 2, custom_emoji_id: "111" }, { type: "custom_emoji", offset: 2, length: 2, custom_emoji_id: "222" }] } });
console.log("bot:", sent.find((s) => s[1].text?.startsWith?.("✅"))[1].text.split("\n")[0]);
const again = sent.find((s) => s[0] === "sendMessage" && s[1].parse_mode === "HTML");
console.log("re-sent preview:", again[1].text.replace(/\n+/g, " / "));
console.log("old preview deleted:", sent.some((s) => s[0] === "deleteMessage"), "| new notes:", sent.filter((s) => s[1].text?.startsWith?.("📝")).length);
