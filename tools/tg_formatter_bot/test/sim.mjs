const mod = await import(process.argv[2]);
const kv = new Map();
const env = { BOT_TOKEN: "123:TEST", ANTHROPIC_API_KEY: "sk-test", OWNER_ID: "726625635", CHANNEL_ID: "-1005659106771", MODEL: "claude-opus-5-5", PREMIUM_EMOJI: process.argv[3] || "off",
  DRAFTS: { get: async k => kv.get(k) ?? null, put: async (k, v) => kv.set(k, v), delete: async k => kv.delete(k) } };
let mid = 100; const sent = []; let lastClaude = null;
globalThis.fetch = async (url, init) => {
  url = String(url);
  if (url.includes("api.telegram.org")) {
    const method = url.split("/").pop(); const body = JSON.parse(init.body); sent.push([method, body]);
    return new Response(JSON.stringify({ ok: true, result: { message_id: ++mid } }), { headers: { "content-type": "application/json" } });
  }
  if (url.includes("api.anthropic.com")) {
    lastClaude = JSON.parse(init.body);
    const text = `<post>\n<b>Free P2P course 👨‍🎓</b>\n\nNot sure what <b><i>PAYIN</i></b> means?\n\n<blockquote>⏳ <i>Around 20 minutes a day</i></blockquote>\n\n<b>Answer your questions 👇</b>\n\n#knowledge\n</post>\n<hashtag>#knowledge</hashtag>\n<buttons>[{"text":"Free P2P course","url":"https://g.ganeshapay.io/smmtg-acen"}]</buttons>\n<notes>—</notes>`;
    return new Response(JSON.stringify({ id: "msg_1", type: "message", role: "assistant", model: "claude-opus-5-5", stop_reason: "end_turn", content: [{ type: "text", text }], usage: { input_tokens: 10, output_tokens: 10 } }), { headers: { "content-type": "application/json", "request-id": "req_1" } });
  }
  throw new Error("unexpected " + url);
};
const secretOf = async () => { const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`whk:${env.BOT_TOKEN}`)); return [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, "0")).join("").slice(0, 48); };
const post = async (u) => (await mod.default.fetch(new Request("https://x.workers.dev/webhook", { method: "POST", headers: { "X-Telegram-Bot-Api-Secret-Token": await secretOf() }, body: JSON.stringify(u) }), env, { waitUntil() {} })).text();
console.log("1", await post({ update_id: 1, message: { message_id: 1, chat: { id: 726625635, type: "private" }, from: { id: 726625635 }, text: "free course draft text" } }));
const prev = sent.find(s => s[0] === "sendMessage" && s[1].parse_mode === "HTML");
console.log("preview html:\n" + prev[1].text); console.log("keyboard:", JSON.stringify(prev[1].reply_markup.inline_keyboard.map(r => r.map(b => b.text))));
console.log("claude req: model", lastClaude.model, "effort", JSON.stringify(lastClaude.output_config), "fallbacks", lastClaude.fallbacks, "sys cache", JSON.stringify(lastClaude.system[0].cache_control), "sys len", lastClaude.system[0].text.length);
const draftId = prev[1].reply_markup.inline_keyboard.flat().find(b => b.callback_data?.startsWith("pub:")).callback_data.split(":")[1];
console.log("2", await post({ update_id: 2, callback_query: { id: "c1", from: { id: 726625635 }, data: `tag:${draftId}:cases`, message: { message_id: prev[1] ? 103 : 0, chat: { id: 726625635 } } } }));
console.log("edited:", sent.filter(s => s[0] === "editMessageText").map(s => s[1].text.split("\n").slice(-1)[0]));
console.log("3", await post({ update_id: 3, callback_query: { id: "c2", from: { id: 726625635 }, data: `pub:${draftId}`, message: { message_id: 103, chat: { id: 726625635 } } } }));
const pub = sent.find(s => s[0] === "sendMessage" && s[1].chat_id === "-1005659106771");
console.log("published to", pub[1].chat_id, "buttons", JSON.stringify(pub[1].reply_markup), "\n" + pub[1].text);
console.log("4 dup", await post({ update_id: 3, callback_query: { id: "c2", from: { id: 726625635 }, data: `pub:${draftId}`, message: { message_id: 103, chat: { id: 726625635 } } } }));
console.log("5 stranger", await post({ update_id: 5, message: { message_id: 9, chat: { id: 1, type: "private" }, from: { id: 1 }, text: "hi" } }), sent.slice(-1)[0][1].text);
console.log("6 bad secret", (await mod.default.fetch(new Request("https://x.workers.dev/webhook", { method: "POST", body: "{}" }), env, {})).status);
