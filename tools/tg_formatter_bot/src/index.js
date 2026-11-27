// m_redactor_bot — formats Telegram posts in the Ganesha Pay house style with Claude and publishes them on a button press.
// Cloudflare Worker: POST /webhook (Telegram updates), GET /setup (registers the webhook + commands).
// Secrets (Cloudflare dashboard → Worker → Settings → Variables and Secrets): BOT_TOKEN, ANTHROPIC_API_KEY.
// Vars (wrangler.toml): OWNER_ID, CHANNEL_ID, MODEL, PREMIUM_EMOJI. KV binding: DRAFTS.
import Anthropic from "@anthropic-ai/sdk";
import { SYSTEM, HASHTAGS } from "./prompt.js";
import PREMIUM from "../premium_emoji.json";

const TTL = 60 * 60 * 24 * 14; // drafts live 14 days

// ---------- Telegram helpers ----------
async function tg(env, method, body) {
  const r = await fetch(`https://api.telegram.org/bot${env.BOT_TOKEN}/${method}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  const j = await r.json();
  if (!j.ok) console.log(`tg ${method} failed`, j.description);
  return j;
}
async function webhookSecret(env) {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`whk:${env.BOT_TOKEN}`));
  return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 48);
}
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const newId = () => crypto.randomUUID().replace(/-/g, "").slice(0, 10);

// ---------- KV ----------
const getDraft = async (env, id) => JSON.parse((await env.DRAFTS.get(`d:${id}`)) || "null");
const putDraft = (env, d) => env.DRAFTS.put(`d:${d.id}`, JSON.stringify(d), { expirationTtl: TTL });
const linkMsg = (env, msgId, draftId) => env.DRAFTS.put(`m:${msgId}`, draftId, { expirationTtl: TTL });

// ---------- Claude ----------
function parseAnswer(text) {
  const tag = (name) => {
    const m = text.match(new RegExp(`<${name}>([\\s\\S]*?)</${name}>`));
    return m ? m[1].trim() : null;
  };
  let buttons = [];
  try { buttons = JSON.parse(tag("buttons") || "[]"); } catch { buttons = []; }
  buttons = (Array.isArray(buttons) ? buttons : []).filter((b) => b && b.text && /^https:\/\//.test(b.url)).slice(0, 2);
  const hashtag = (tag("hashtag") || "").replace("#", "").trim();
  return { html: tag("post") || text.trim(), hashtag: HASHTAGS.includes(hashtag) ? hashtag : null, buttons, notes: tag("notes") || "—" };
}

async function format(env, draft, instruction) {
  const client = new Anthropic({ apiKey: env.ANTHROPIC_API_KEY });
  const messages = [{ role: "user", content: `${draft.photo ? "Photo caption draft" : "Draft"}:\n\n${draft.source}` }];
  for (const turn of draft.turns || []) {
    messages.push({ role: "assistant", content: turn.answer });
    messages.push({ role: "user", content: turn.instruction });
  }
  if (instruction) {
    messages.push({ role: "assistant", content: draft.lastAnswer });
    messages.push({ role: "user", content: instruction });
  }
  const response = await client.beta.messages.create({
    model: env.MODEL || "claude-opus-5-5",
    max_tokens: 8000,
    system: [{ type: "text", text: SYSTEM, cache_control: { type: "ephemeral" } }],
    messages,
    output_config: { effort: "low" },   // formatting is a light task; low keeps replies fast
    betas: ["server-side-fallback-2026-07-01"],
    fallbacks: "default",
  });
  if (response.stop_reason === "refusal") throw new Error("Модель отказалась форматировать этот текст.");
  const text = response.content.filter((b) => b.type === "text").map((b) => b.text).join("");
  if (instruction) draft.turns = [...(draft.turns || []), { answer: draft.lastAnswer, instruction }];
  draft.lastAnswer = text;
  return parseAnswer(text);
}

// ---------- post helpers ----------
function setHashtag(html, tagName) {
  const lines = html.trimEnd().split("\n");
  if (/^#\w+$/.test(lines[lines.length - 1].trim())) lines.pop();
  while (lines.length && lines[lines.length - 1].trim() === "") lines.pop();
  return `${lines.join("\n")}\n\n#${tagName}`;
}
function withPremium(env, html) {
  if (env.PREMIUM_EMOJI !== "on") return html;
  // replace emoji only in text (outside tags), first known custom emoji id per character
  const keys = Object.keys(PREMIUM).sort((a, b) => b.length - a.length);
  return html.split(/(<[^>]+>)/).map((part) => {
    if (part.startsWith("<")) return part;
    let out = part;
    for (const k of keys) {
      const bare = k.replace(/️/g, "");
      for (const variant of new Set([k, bare])) {
        if (variant && out.includes(variant)) out = out.split(variant).join(`\u0000${k}\u0000`);
      }
    }
    return out.replace(/\u0000([^\u0000]+)\u0000/g, (_, ch) => `<tg-emoji emoji-id="${PREMIUM[ch][0]}">${ch}</tg-emoji>`);
  }).join("");
}
const urlRows = (buttons) => (buttons || []).map((b) => [{ text: b.text, url: b.url }]);
function controls(d) {
  const tags = HASHTAGS.map((t) => ({ text: (d.hashtag === t ? "✓ #" : "#") + t, callback_data: `tag:${d.id}:${t}` }));
  return [
    ...urlRows(d.buttons),
    [{ text: "📤 Опубликовать", callback_data: `pub:${d.id}` }, { text: "🔁 Другой вариант", callback_data: `redo:${d.id}` }],
    [{ text: "✏️ Поправить", callback_data: `edit:${d.id}` }, { text: d.buttons?.length ? "🔘 Убрать кнопки" : "🔘 Кнопки", callback_data: `btn:${d.id}` }],
    tags.slice(0, 3), tags.slice(3),
  ];
}
async function sendPreview(env, chatId, d) {
  const html = withPremium(env, d.html);
  const common = { chat_id: chatId, parse_mode: "HTML", reply_markup: { inline_keyboard: controls(d) } };
  let r = d.photo
    ? await tg(env, "sendPhoto", { ...common, photo: d.photo, caption: html })
    : await tg(env, "sendMessage", { ...common, text: html, link_preview_options: { is_disabled: true } });
  if (!r.ok) {   // broken HTML from the model: show it raw so nothing is lost, keep the buttons
    r = await tg(env, "sendMessage", {
      chat_id: chatId, parse_mode: "HTML", reply_markup: { inline_keyboard: controls(d) },
      text: `⚠️ Telegram не принял разметку (${esc(r.description)}). Нажми «Другой вариант» или «Поправить».\n\n<code>${esc(d.html).slice(0, 3500)}</code>`,
    });
  }
  if (r.ok) { d.previewId = r.result.message_id; await linkMsg(env, r.result.message_id, d.id); }
  if (d.notes && d.notes !== "—") await tg(env, "sendMessage", { chat_id: chatId, text: `📝 ${d.notes}`, reply_parameters: r.ok ? { message_id: r.result.message_id } : undefined });
  await putDraft(env, d);
}
async function refreshPreview(env, chatId, d) {
  const html = withPremium(env, d.html);
  const markup = { inline_keyboard: controls(d) };
  const r = d.photo
    ? await tg(env, "editMessageCaption", { chat_id: chatId, message_id: d.previewId, caption: html, parse_mode: "HTML", reply_markup: markup })
    : await tg(env, "editMessageText", { chat_id: chatId, message_id: d.previewId, text: html, parse_mode: "HTML", reply_markup: markup, link_preview_options: { is_disabled: true } });
  return r.ok;
}

// ---------- handlers ----------
async function runFormat(env, chatId, d, instruction) {
  await tg(env, "sendChatAction", { chat_id: chatId, action: "typing" });
  const status = await tg(env, "sendMessage", { chat_id: chatId, text: instruction ? "✏️ Правлю…" : "⏳ Форматирую…" });
  try {
    const out = await format(env, d, instruction);
    Object.assign(d, out, { hashtag: out.hashtag || d.hashtag || "knowledge" });
    d.html = setHashtag(d.html, d.hashtag);
    await sendPreview(env, chatId, d);
  } catch (e) {
    let msg = e.message;
    if (e instanceof Anthropic.AuthenticationError) msg = "Неверный ключ Claude API (ANTHROPIC_API_KEY).";
    else if (e instanceof Anthropic.RateLimitError) msg = "Лимит запросов к Claude, попробуй через минуту.";
    else if (e instanceof Anthropic.APIError) msg = `Ошибка Claude API ${e.status}: ${e.message}`;
    await tg(env, "sendMessage", { chat_id: chatId, text: `❌ ${msg}` });
  } finally {
    if (status.ok) await tg(env, "deleteMessage", { chat_id: chatId, message_id: status.result.message_id });
  }
}

const HELP = `Пришли текст поста (или фото с подписью) — верну его оформленным в стиле канала.

Под превью:
📤 Опубликовать — отправить в канал
🔁 Другой вариант — переформатировать заново
✏️ Поправить — написать, что изменить (или просто ответь на превью)
🔘 Кнопки — показать/убрать кнопки под постом
#… — сменить хештег

/channel — куда публикую`;

async function onMessage(env, msg) {
  const chatId = msg.chat.id;
  const text = msg.text ?? msg.caption ?? "";
  if (text.startsWith("/start") || text.startsWith("/help")) return tg(env, "sendMessage", { chat_id: chatId, text: HELP });
  if (text.startsWith("/channel")) return tg(env, "sendMessage", { chat_id: chatId, text: `Канал для публикации: ${env.CHANNEL_ID}\nПремиум-эмодзи: ${env.PREMIUM_EMOJI === "on" ? "вкл" : "выкл"}` });

  // an edit instruction: reply to a preview, or the message right after «✏️ Поправить»
  let targetId = null;
  if (msg.reply_to_message) targetId = await env.DRAFTS.get(`m:${msg.reply_to_message.message_id}`);
  if (!targetId) { targetId = await env.DRAFTS.get(`pending:${chatId}`); if (targetId) await env.DRAFTS.delete(`pending:${chatId}`); }
  if (targetId && text) {
    const d = await getDraft(env, targetId);
    if (d) return runFormat(env, chatId, d, text);
  }
  if (!text) return tg(env, "sendMessage", { chat_id: chatId, text: "Пришли текст поста или фото с подписью." });

  const d = { id: newId(), source: text, photo: msg.photo ? msg.photo[msg.photo.length - 1].file_id : null, turns: [] };
  return runFormat(env, chatId, d, null);
}

async function onCallback(env, cq) {
  const chatId = cq.message.chat.id;
  const [action, id, arg] = cq.data.split(":");
  const d = await getDraft(env, id);
  if (!d) return tg(env, "answerCallbackQuery", { callback_query_id: cq.id, text: "Черновик устарел, пришли текст заново." });
  d.previewId = cq.message.message_id;

  if (action === "tag") {
    d.hashtag = arg; d.html = setHashtag(d.html, arg);
    await putDraft(env, d); await refreshPreview(env, chatId, d);
    return tg(env, "answerCallbackQuery", { callback_query_id: cq.id, text: `#${arg}` });
  }
  if (action === "btn") {
    d.buttons = d.buttons?.length ? [] : [{ text: "Message a manager", url: "https://g.ganeshapay.io/smmtg-mng" }, { text: "Free P2P course", url: "https://g.ganeshapay.io/smmtg-acen" }];
    await putDraft(env, d); await refreshPreview(env, chatId, d);
    return tg(env, "answerCallbackQuery", { callback_query_id: cq.id });
  }
  if (action === "edit") {
    await env.DRAFTS.put(`pending:${chatId}`, d.id, { expirationTtl: 3600 });
    await tg(env, "answerCallbackQuery", { callback_query_id: cq.id });
    return tg(env, "sendMessage", { chat_id: chatId, text: "Что поправить? Напиши одним сообщением — например: «короче», «цифры в цитату», «другой заголовок».", reply_parameters: { message_id: cq.message.message_id } });
  }
  if (action === "redo") {
    await tg(env, "answerCallbackQuery", { callback_query_id: cq.id, text: "Делаю другой вариант…" });
    return runFormat(env, chatId, d, "Make a different variant of this post: another headline and a different arrangement of emphasis, same facts and the same house style.");
  }
  if (action === "pub") {
    const html = withPremium(env, d.html);
    const common = { chat_id: env.CHANNEL_ID, parse_mode: "HTML", reply_markup: d.buttons?.length ? { inline_keyboard: urlRows(d.buttons) } : undefined };
    const r = d.photo
      ? await tg(env, "sendPhoto", { ...common, photo: d.photo, caption: html })
      : await tg(env, "sendMessage", { ...common, text: html, link_preview_options: { is_disabled: true } });
    if (!r.ok) return tg(env, "answerCallbackQuery", { callback_query_id: cq.id, text: `Не опубликовано: ${r.description}`.slice(0, 190), show_alert: true });
    d.published = { chat: env.CHANNEL_ID, id: r.result.message_id }; await putDraft(env, d);
    const cid = String(env.CHANNEL_ID).replace(/^-100/, "");
    await tg(env, "answerCallbackQuery", { callback_query_id: cq.id, text: "Опубликовано ✅" });
    return tg(env, "sendMessage", {
      chat_id: chatId, text: "✅ Опубликовано в канал.", reply_parameters: { message_id: cq.message.message_id },
      reply_markup: { inline_keyboard: [[{ text: "Открыть пост", url: `https://t.me/c/${cid}/${r.result.message_id}` }, { text: "🗑 Удалить из канала", callback_data: `unpub:${d.id}` }]] },
    });
  }
  if (action === "unpub" && d.published) {
    const r = await tg(env, "deleteMessage", { chat_id: d.published.chat, message_id: d.published.id });
    await tg(env, "answerCallbackQuery", { callback_query_id: cq.id, text: r.ok ? "Удалено из канала" : `Не удалось: ${r.description}`.slice(0, 190) });
    if (r.ok) { delete d.published; await putDraft(env, d); }
    return;
  }
  return tg(env, "answerCallbackQuery", { callback_query_id: cq.id });
}

async function onUpdate(env, u) {
  const owner = String(env.OWNER_ID);
  if (u.my_chat_member) {   // bot added to / removed from a channel -> tell the owner the chat id
    const c = u.my_chat_member.chat, st = u.my_chat_member.new_chat_member.status;
    if (c.type === "channel") return tg(env, "sendMessage", { chat_id: owner, text: `Канал «${c.title}» (${c.id}): статус бота — ${st}.` });
    return;
  }
  if (u.message && u.message.chat.type === "private") {
    if (String(u.message.from.id) !== owner) return tg(env, "sendMessage", { chat_id: u.message.chat.id, text: "Это закрытый бот." });
    return onMessage(env, u.message);
  }
  if (u.callback_query) {
    if (String(u.callback_query.from.id) !== owner) return tg(env, "answerCallbackQuery", { callback_query_id: u.callback_query.id, text: "Нет доступа" });
    return onCallback(env, u.callback_query);
  }
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (request.method === "GET" && url.pathname === "/setup") {
      const secret = await webhookSecret(env);
      const hook = await tg(env, "setWebhook", { url: `${url.origin}/webhook`, secret_token: secret, allowed_updates: ["message", "callback_query", "my_chat_member"], drop_pending_updates: true });
      const cmds = await tg(env, "setMyCommands", { commands: [{ command: "help", description: "Как пользоваться" }, { command: "channel", description: "Куда публикую" }] });
      return Response.json({ webhook: hook.ok ? "ok" : hook.description, commands: cmds.ok ? "ok" : cmds.description });
    }
    if (request.method === "POST" && url.pathname === "/webhook") {
      if (request.headers.get("X-Telegram-Bot-Api-Secret-Token") !== (await webhookSecret(env))) return new Response("forbidden", { status: 403 });
      const update = await request.json();
      // process inline (waitUntil is capped at ~30 s; a Claude call can take longer) and drop Telegram retries
      if (await env.DRAFTS.get(`u:${update.update_id}`)) return new Response("dup");
      await env.DRAFTS.put(`u:${update.update_id}`, "1", { expirationTtl: 3600 });
      try { await onUpdate(env, update); } catch (e) { console.log("update error", e.stack || e); }
      return new Response("ok");
    }
    return new Response("m_redactor_bot is running");
  },
};
