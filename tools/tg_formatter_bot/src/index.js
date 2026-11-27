// m_redactor_bot — lays out Telegram posts in the Ganesha Pay house style and publishes them on a button press.
// The model (Cloudflare Workers AI, free daily allocation) returns only the post STRUCTURE as JSON;
// src/render.js builds the Telegram HTML, so markup is always valid. Code checks numbers/wording against the draft.
// Posts can also be loaded by date from the Google Sheets content plan (apps_script/Code.gs): text + visual.
// Cloudflare Worker routes: POST /webhook (Telegram), GET /setup (webhook + commands), GET /img/<id> (visual for link previews).
// Secrets (Cloudflare dashboard → Worker → Settings → Variables and Secrets): BOT_TOKEN, PLAN_URL, PLAN_KEY.
// Vars (wrangler.toml): OWNER_ID, CHANNEL_ID, MODEL, PREMIUM_EMOJI, PLAN_STATUS. Bindings: DRAFTS (KV), AI (Workers AI).
import { Buffer } from "node:buffer";
import { DurableObject } from "cloudflare:workers";
import { SYSTEM, LINKS, BUTTON_LABELS } from "./prompt.js";
import { renderPost, parseLayout, checkLayout, fallbackLayout, prepareDraft } from "./render.js";
import PREMIUM from "../premium_emoji.json";

const TTL = 60 * 60 * 24 * 14; // drafts and visuals live 14 days
const DEFAULT_MODEL = "@cf/qwen/qwen3.8-27b";
const BACKUP_MODEL = "@cf/openai/gpt-oss-120b";   // used when the main model errors
const CAPTION_MAX = 1024;                          // Telegram limit for a caption under a photo/video
const PLAN_BUTTON = "📅 Контент-план";

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
async function tgUpload(env, method, field, fields, bytes, name, mime) {
  const fd = new FormData();
  for (const [k, v] of Object.entries(fields)) if (v !== undefined && v !== null) fd.append(k, typeof v === "object" ? JSON.stringify(v) : String(v));
  fd.append(field, new Blob([bytes], { type: mime }), name);
  const r = await fetch(`https://api.telegram.org/bot${env.BOT_TOKEN}/${method}`, { method: "POST", body: fd });
  const j = await r.json();
  if (!j.ok) console.log(`tg ${method} upload failed`, j.description);
  return j;
}
async function webhookSecret(env) {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`whk:${env.BOT_TOKEN}`));
  return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 48);
}
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const newId = () => crypto.randomUUID().replace(/-/g, "").slice(0, 10);
const plainLen = (html) => html.replace(/<[^>]+>/g, "").replace(/&(amp|lt|gt);/g, "x").length;

// ---------- KV ----------
const getDraft = async (env, id) => JSON.parse((await env.DRAFTS.get(`d:${id}`)) || "null");
const putDraft = (env, d) => env.DRAFTS.put(`d:${d.id}`, JSON.stringify(d), { expirationTtl: TTL });
const linkMsg = (env, msgId, draftId) => env.DRAFTS.put(`m:${msgId}`, draftId, { expirationTtl: TTL });

// ---------- Workers AI ----------
function answerText(r) {
  if (typeof r === "string") return r;
  if (r?.choices?.[0]?.message?.content) return r.choices[0].message.content;
  if (typeof r?.response === "string") return r.response;
  if (r?.response && typeof r.response === "object") return JSON.stringify(r.response);
  if (Array.isArray(r?.output)) {   // responses-style output
    return r.output.flatMap((o) => o.content || []).filter((c) => c.type === "output_text").map((c) => c.text).join("");
  }
  return "";
}
const USAGE = [];   // token usage log of the current /debug request
async function callModel(env, messages, temperature, model = env.MODEL || DEFAULT_MODEL) {
  const input = { messages, max_tokens: 2500, temperature };
  if (/gpt-oss|qwen3/.test(model)) input.reasoning_effort = "low";
  if (/qwen3/.test(model)) input.chat_template_kwargs = { enable_thinking: false };
  Object.assign(input, env.AI_OPTS || {});
  const t0 = Date.now();
  const r = await env.AI.run(model, input);
  USAGE.push({ model, ms: Date.now() - t0, usage: r?.usage });
  return answerText(r);
}

// Lays out the draft: model -> JSON -> checks -> one corrective retry -> best result (or the no-model fallback).
async function layout(env, d, instruction, variant) {
  const prep = prepareDraft(d.source);
  const finish = (p) => {
    if (prep.hashtag && !instruction) p.hashtag = prep.hashtag;   // the hashtag written in the draft/plan wins (an edit may change it)
    if (prep.links.length) {   // links written in the draft decide the buttons; the model only names them
      const own = (p.buttons || []).map((b) => (typeof b === "string" ? { link: b } : b || {}));
      p.buttons = prep.links.slice(0, 2).map((k, i) => ({ link: k, text: (own.find((b) => b.link === k) || own[i] || {}).text || BUTTON_LABELS[k] }));
    }
    return p;
  };
  const short = d.media ? " (it goes under a picture; keep the layout compact)" : "";
  const messages = [{ role: "system", content: SYSTEM }, { role: "user", content: `Draft${short}:\n${prep.text}\nJSON:` }];
  if (d.layout && (instruction || variant)) {
    messages.push({ role: "assistant", content: JSON.stringify(d.layout) });
    messages.push({ role: "user", content: instruction
      ? `Owner's change request (may be in Russian): ${instruction}\nApply it and return the full updated JSON. Keep the draft's facts and numbers.`
      : "Give a different layout of the same draft: another headline and emoji, different blocks and emphasis, another button label. Same words, same facts. Return JSON." });
  }
  let best = null, model = env.MODEL || DEFAULT_MODEL;
  const t0 = Date.now();
  for (let attempt = 0; attempt < 2; attempt++) {
    if (attempt && Date.now() - t0 > 30000) break;   // keep the whole reply well under a minute
    let text = "";
    try { text = await callModel(env, messages, variant ? 0.9 : attempt ? 0.4 : 0.2, model); }
    catch (e) { console.log("AI error", model, e.message); if (model === BACKUP_MODEL) break; model = BACKUP_MODEL; continue; }
    const p = parseLayout(text);
    if (!p) { messages.push({ role: "assistant", content: text.slice(0, 3000) }, { role: "user", content: "That was not valid JSON of the required shape. Return only the JSON object." }); continue; }
    finish(p);
    const r = renderPost(p);
    const c = checkLayout(prep.text, p, { caption: false, html: r.html });
    const cand = { p, r, c };
    if (!best || c.problems.length < best.c.problems.length) best = cand;
    if (!c.problems.length || instruction) break;   // an edit may change numbers on purpose; just report it
    messages.push({ role: "assistant", content: JSON.stringify(p) }, { role: "user", content: `Fix these problems and return the full JSON again:\n- ${c.problems.join("\n- ")}` });
  }
  if (!best) {
    const p = finish(fallbackLayout(prep.text));
    const r = renderPost(p);
    return { layout: p, ...r, notes: ["Модель не ответила — сделал простую раскладку без ИИ. Нажми «Другой вариант» позже.", ...prep.notes, ...checkLayout(prep.text, p, { html: r.html }).notes] };
  }
  return { layout: best.p, ...best.r, notes: [...prep.notes, ...best.c.notes] };
}

// ---------- content plan (Google Apps Script web app) ----------
async function planCall(env, body) {
  if (!env.PLAN_URL || !env.PLAN_KEY) throw new Error("Контент-план не подключён: добавь секреты PLAN_URL и PLAN_KEY в Cloudflare.");
  const r = await fetch(env.PLAN_URL, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ ...body, key: String(env.PLAN_KEY).trim() }), redirect: "follow" });
  const t = await r.text();
  let j;
  try { j = JSON.parse(t); } catch { throw new Error(`Apps Script ответил не JSON (HTTP ${r.status}). Проверь доступ веб-приложения: «Все» (Anyone).`); }
  if (j.error === "no BOT_KEY") throw new Error("Apps Script: в свойствах скрипта нет BOT_KEY (Налаштування проєкту → Властивості скрипта).");
  if (j.error) throw new Error(j.error === "forbidden" ? "Apps Script: ключ не совпадает (PLAN_KEY в Cloudflare ≠ BOT_KEY в скрипте)." : `Apps Script: ${j.error}`);
  return j;
}
const DATE_RE = /^\s*(\d{1,2})[.\/\-\s](\d{1,2})(?:[.\/\-\s]\d{2,4})?\s*$/;
const normDate = (dd, mm) => `${String(dd).padStart(2, "0")}.${String(mm).padStart(2, "0")}`;
const statusIcon = (p) => (/posted|опубликован/i.test(p.status) ? "✅" : !p.hasText ? "⚠️" : "📝");

async function showPlan(env, chatId) {
  let list;
  try { list = await planCall(env, { action: "list", back: 1, ahead: 14 }); }
  catch (e) { return tg(env, "sendMessage", { chat_id: chatId, text: `❌ ${e.message}` }); }
  const posts = (list.posts || []).slice(0, 12);
  if (!posts.length) return tg(env, "sendMessage", { chat_id: chatId, text: "В плане нет постов на ближайшие 2 недели. Напиши дату, например 29.11." });
  const rows = posts.map((p) => [{ text: `${statusIcon(p)} ${p.date} · ${String(p.topic || p.category || "без темы").slice(0, 34)}`, callback_data: `plan:${p.date}` }]);
  return tg(env, "sendMessage", {
    chat_id: chatId, reply_markup: { inline_keyboard: rows },
    text: "Выбери дату поста или напиши дату сообщением, например 29.11.\n✅ опубликован · 📝 готов к оформлению · ⚠️ нет текста",
  });
}

function mediaKind(mime, size) {
  if (/^image\/gif/.test(mime)) return "animation";
  if (/^image\//.test(mime)) return size > 10 * 1024 * 1024 ? "document" : "photo";
  if (/^video\//.test(mime)) return "video";
  return "document";
}

async function loadPlanPost(env, chatId, date) {
  await tg(env, "sendChatAction", { chat_id: chatId, action: "upload_photo" });
  const status = await tg(env, "sendMessage", { chat_id: chatId, text: `⏳ Загружаю пост ${date} из контент-плана…` });
  const done = () => status.ok && tg(env, "deleteMessage", { chat_id: chatId, message_id: status.result.message_id });
  let p;
  try { p = await planCall(env, { action: "post", date }); }
  catch (e) { await done(); return tg(env, "sendMessage", { chat_id: chatId, text: `❌ ${e.message}` }); }
  if (!p.found) { await done(); return tg(env, "sendMessage", { chat_id: chatId, text: `На ${date} в контент-плане поста нет.` }); }
  if (!String(p.text || "").trim()) { await done(); return tg(env, "sendMessage", { chat_id: chatId, text: `На ${date} («${p.topic}») в плане нет текста.` }); }

  const d = { id: newId(), source: p.text, plan: { date: p.date, topic: p.topic, status: p.status }, media: null, planNotes: [] };
  if (p.file?.b64) {
    const bytes = Buffer.from(p.file.b64, "base64");
    const key = `img:${crypto.randomUUID().replace(/-/g, "")}`;
    await env.DRAFTS.put(key, bytes, { expirationTtl: TTL, metadata: { mime: p.file.mime } });
    d.media = { kind: mediaKind(p.file.mime, bytes.length), mime: p.file.mime, name: p.file.name || "visual", key };
  } else {
    const what = p.fileNote ? p.fileNote : p.visualNote ? `в плане: «${p.visualNote}»` : "в плане пусто";
    d.askVisual = `🖼 Для поста ${p.date} нет готового визуала (${what}).\nПришли фото или видео — прикреплю к этому посту. Жду.`;
  }
  if (/posted|опубликован/i.test(p.status)) d.planNotes.push(`В плане статус «${p.status}» — этот пост уже публиковался.`);
  if (String(p.poll || "").trim()) d.planNotes.push("К посту есть опрос (колонка POLL) — его бот пока не публикует.");
  await done();
  return runFormat(env, chatId, d, null);
}

// ---------- post helpers ----------
const BASE_PMAP = Object.fromEntries(Object.entries(PREMIUM).map(([k, v]) => [k, v[0]]));
const pmap = (env) => env.PMAP || BASE_PMAP;
function withPremium(env, html) {
  if (env.PREMIUM_EMOJI !== "on") return html;
  const PM = pmap(env);
  // replace emoji only in text (outside tags) with the premium version
  const keys = Object.keys(PM).sort((a, b) => b.length - a.length);
  return html.split(/(<[^>]+>)/).map((part) => {
    if (part.startsWith("<")) return part;
    let out = part;
    for (const k of keys) {
      const bare = k.replace(/️/g, "");
      for (const variant of new Set([k, bare])) {
        if (variant && out.includes(variant)) out = out.split(variant).join(`\u0000${k}\u0000`);
      }
    }
    return out.replace(/\u0000([^\u0000]+)\u0000/g, (_, ch) => `<tg-emoji emoji-id="${PM[ch]}">${ch}</tg-emoji>`);
  }).join("");
}
// ---------- buttons under the post ----------
// d.buttons: link buttons [{text, url, style}]; d.reactions: reaction buttons [{emoji, ceid, style}] (one row, counters).
const STYLES = [undefined, "success", "primary", "danger"];
const DOT = { undefined: "⚪", success: "🟢", primary: "🔵", danger: "🔴" };
const STYLE_NAME = { undefined: "обычный", success: "зелёный", primary: "синий", danger: "красный" };
const LINK_CHOICES = [["manager", "💬 Менеджер"], ["start", "🚀 Старт работы"], ["academy", "🎓 Курс EN"], ["academy_hi", "🎓 Курс HI"]];
const MAX_REACTIONS = 6;
const cb = (text, data, style) => ({ text, callback_data: data, ...(style ? { style } : {}) });
const styled = (o, style) => (style ? { ...o, style } : o);

// reaction button: emoji + counter; a premium emoji goes into icon_custom_emoji_id (needs a Fragment username)
function reactionButton(env, r, count, data) {
  const premium = env.PREMIUM_EMOJI === "on" && r.ceid;
  const text = premium ? (count ? String(count) : "\u2060") : count ? `${r.emoji} ${count}` : r.emoji;
  return styled({ text, callback_data: data, ...(premium ? { icon_custom_emoji_id: r.ceid } : {}) }, r.style);
}
// the post's own buttons; in the channel reactions are live (r:i), in the preview they only explain themselves
const AUTO_ICON = { manager: "💬", start: "🚀", academy: "👨‍🎓", academy_hi: "👨‍🎓" };
function linkIcon(env, b) {
  if (env.PREMIUM_EMOJI !== "on" || b.ceid === null) return null;
  if (b.ceid) return b.ceid;
  const k = Object.keys(LINKS).find((x) => LINKS[x] === b.url);
  return (k && pmap(env)[AUTO_ICON[k]]) || null;
}
function linkButton(env, b) {
  const icon = linkIcon(env, b);
  return styled({ text: b.text, url: b.url, ...(icon ? { icon_custom_emoji_id: icon } : {}) }, b.style);
}
function postRows(env, d, { channel = false, counts = [] } = {}) {
  const rows = (d.buttons || []).map((b) => [linkButton(env, b)]);
  const rx = d.reactions || [];
  if (rx.length) rows.push(rx.map((r, i) => reactionButton(env, r, counts[i] || 0, channel ? `r:${i}` : `rp:${d.id}`)));
  return rows;
}

function controls(env, d) {
  const id = d.id, btns = d.buttons || [], rx = d.reactions || [], kb = d.kb || "main";
  if (kb === "btns") {   // editor: every post button is shown as itself; tap one to set it up
    const rows = btns.map((b, i) => [cb(`${b.text}  ›`, `be:${id}:u:${i}`, b.style)]);
    if (rx.length) rows.push(rx.map((r, i) => cb(r.emoji, `be:${id}:r:${i}`, r.style)));
    rows.push([cb("➕ Ссылка", `ba:${id}:u`), cb("➕ Реакция", `ba:${id}:r`)]);
    rows.push([cb("✅ Готово", `bk:${id}`)]);
    return rows;
  }
  const m = kb.match(/^(u|r|l):(\d+)$/);
  if (m) {
    const i = Number(m[2]);
    if (m[1] === "u" && btns[i]) return [
      [linkButton(env, btns[i])],
      [cb("✏️ Текст", `bt:${id}:${i}`), cb("🔗 Ссылка", `bl:${id}:${i}`), cb("😀 Эмодзи", `bi:${id}:${i}`)],
      [cb(`${DOT[btns[i].style]} Цвет`, `bc:${id}:u:${i}`), cb("🗑 Удалить", `bd:${id}:u:${i}`)],
      [cb("⬅️ Назад", `bm:${id}`)],
    ];
    if (m[1] === "l" && btns[i]) return [
      ...LINK_CHOICES.map(([k, label]) => [cb(`${btns[i].url === LINKS[k] ? "✓ " : ""}${label}`, `bs:${id}:${i}:${k}`)]),
      [cb("✍️ Своя ссылка", `bu:${id}:${i}`)],
      [cb("⬅️ Назад", `be:${id}:u:${i}`)],
    ];
    if (m[1] === "r" && rx[i]) return [
      [reactionButton(env, rx[i], 0, `rp:${id}`)],
      [cb("😀 Эмодзи", `re:${id}:${i}`), cb(`${DOT[rx[i].style]} Цвет`, `bc:${id}:r:${i}`)],
      [cb("🗑 Удалить", `bd:${id}:r:${i}`), cb("⬅️ Назад", `bm:${id}`)],
    ];
  }
  return [
    ...postRows(env, d),
    [cb("📤 Опубликовать", `pub:${id}`), cb("🔁 Другой вариант", `redo:${id}`)],
    [cb("✏️ Поправить текст", `edit:${id}`), cb(d.media ? "🖼 Заменить визуал" : "🖼 Добавить визуал", `vis:${id}`)],
    [cb("🔘 Кнопки", `bm:${id}`)],
  ];
}
const setKb = (env, chatId, d) => tg(env, "editMessageReplyMarkup", { chat_id: chatId, message_id: d.previewId, reply_markup: { inline_keyboard: controls(env, d) } });

// emoji from a message: premium (custom_emoji entities) and normal ones, in order
function emojisOf(msg) {
  const text = msg.text || msg.caption || "";
  const ents = (msg.entities || msg.caption_entities || []).filter((e) => e.type === "custom_emoji");
  const out = [];
  let pos = 0;
  const plain = (chunk) => {
    for (const { segment } of new Intl.Segmenter("en", { granularity: "grapheme" }).segment(chunk)) {
      if (/\p{Extended_Pictographic}|\p{Regional_Indicator}/u.test(segment)) out.push({ emoji: segment });
    }
  };
  for (const e of ents.sort((a, b) => a.offset - b.offset)) {
    plain(text.slice(pos, e.offset));
    out.push({ emoji: text.slice(e.offset, e.offset + e.length), ceid: e.custom_emoji_id });
    pos = e.offset + e.length;
  }
  plain(text.slice(pos));
  return out;
}

// pending input: what the next message from the owner means
const setPending = (env, chatId, obj) => env.DRAFTS.put(`pending:${chatId}`, JSON.stringify(obj), { expirationTtl: 3600 });
async function getPending(env, chatId) {
  const v = await env.DRAFTS.get(`pending:${chatId}`);
  if (!v) return null;
  try { return JSON.parse(v); } catch { return { id: v, kind: "edit" }; }
}

// a photo/video/file from the owner becomes the post's visual
async function attachMedia(env, chatId, d, msg) {
  let media;
  if (msg.photo) {
    const ph = msg.photo[msg.photo.length - 1];
    media = { kind: "photo", fileId: ph.file_id, mime: "image/jpeg", name: "photo.jpg" };
    // keep a copy so a long post can show the picture as a large preview above the text
    const f = await tg(env, "getFile", { file_id: ph.file_id });
    if (f.ok && f.result.file_path) {
      const r = await fetch(`https://api.telegram.org/file/bot${env.BOT_TOKEN}/${f.result.file_path}`);
      if (r.ok) {
        const key = `img:${crypto.randomUUID().replace(/-/g, "")}`;
        await env.DRAFTS.put(key, await r.arrayBuffer(), { expirationTtl: TTL, metadata: { mime: "image/jpeg" } });
        media.key = key;
      }
    }
  } else if (msg.video) media = { kind: "video", fileId: msg.video.file_id, mime: msg.video.mime_type || "video/mp4", name: "video.mp4" };
  else if (msg.animation) media = { kind: "animation", fileId: msg.animation.file_id, mime: "video/mp4", name: "animation.mp4" };
  else if (msg.document) media = { kind: "document", fileId: msg.document.file_id, mime: msg.document.mime_type || "", name: msg.document.file_name || "file" };
  else return false;
  for (const id of d.previewIds || [d.previewId]) if (id) await tg(env, "deleteMessage", { chat_id: chatId, message_id: id });
  d.media = media; d.kb = "main"; d.notes = []; d.planNotes = []; delete d.askVisual;
  await sendPreview(env, chatId, d);
  return true;
}

// How the post is shown: text only, picture + caption, picture as a large preview above a long text, or media + separate text.
function postMode(d, html) {
  if (!d.media) return "text";
  if (plainLen(html) <= CAPTION_MAX) return "caption";
  return d.media.kind === "photo" && d.media.key ? "preview" : "split";
}
const METHOD = { photo: ["sendPhoto", "photo"], video: ["sendVideo", "video"], animation: ["sendAnimation", "animation"], document: ["sendDocument", "document"] };
function fileIdOf(kind, msg) {
  if (kind === "photo") return msg.photo?.[msg.photo.length - 1]?.file_id;
  return msg[kind]?.file_id || msg.document?.file_id;
}
async function sendMediaMsg(env, chatId, d, extra) {
  const [method, field] = METHOD[d.media.kind];
  if (d.media.fileId) return tg(env, method, { chat_id: chatId, [field]: d.media.fileId, ...extra });
  const bytes = await env.DRAFTS.get(d.media.key, "arrayBuffer");
  if (!bytes) return { ok: false, description: "визуал устарел, загрузи пост из плана заново" };
  const r = await tgUpload(env, method, field, { chat_id: chatId, ...extra }, bytes, d.media.name, d.media.mime);
  if (r.ok) d.media.fileId = fileIdOf(d.media.kind, r.result);
  return r;
}
// sends the post; returns { ok, ids: [all message ids], mainId, mode, description }
async function sendPost(env, chatId, d, html, markup) {
  const mode = postMode(d, html);
  const text = { chat_id: chatId, text: html, parse_mode: "HTML", reply_markup: markup };
  let r, ids = [];
  if (mode === "text") r = await tg(env, "sendMessage", { ...text, link_preview_options: { is_disabled: true } });
  else if (mode === "caption") r = await sendMediaMsg(env, chatId, d, { caption: html, parse_mode: "HTML", reply_markup: markup });
  else if (mode === "preview") r = await tg(env, "sendMessage", { ...text, link_preview_options: { url: `${env.ORIGIN}/img/${d.media.key.slice(4)}`, prefer_large_media: true, show_above_text: true } });
  else {
    const m = await sendMediaMsg(env, chatId, d, {});
    if (!m.ok) return { ok: false, description: m.description, mode };
    ids.push(m.result.message_id);
    r = await tg(env, "sendMessage", { ...text, link_preview_options: { is_disabled: true } });
  }
  if (!r.ok) return { ok: false, description: r.description, ids, mode };
  ids.push(r.result.message_id);
  return { ok: true, ids, mainId: r.result.message_id, mode };
}

const emojiRefused = (r) => !r.ok && /emoji|icon/i.test(r.description || "");
async function sendPreview(env, chatId, d) {
  let html = withPremium(env, d.html);
  let markup = { inline_keyboard: controls(env, d) };
  let r = await sendPost(env, chatId, d, html, markup);
  if (emojiRefused(r) && env.PREMIUM_EMOJI === "on") {   // e.g. the Fragment username is not attached yet
    const why = r.description;
    env = { ...env, PREMIUM_EMOJI: "off" };
    html = d.html; markup = { inline_keyboard: controls(env, d) };
    r = await sendPost(env, chatId, d, html, markup);
    d.notes = [...(d.notes || []), `Telegram не принял премиум-эмодзи (${why}) — показал с обычными. Проверь /channel: должен быть виден юзернейм с Fragment.`];
  }
  if (!r.ok) {   // show the HTML raw so nothing is lost, keep the buttons
    const t = await tg(env, "sendMessage", {
      chat_id: chatId, parse_mode: "HTML", reply_markup: markup,
      text: `⚠️ Telegram не принял пост (${esc(r.description || "")}). Нажми «Другой вариант» или «Поправить».\n\n<code>${esc(d.html).slice(0, 3500)}</code>`,
    });
    r = t.ok ? { ok: true, ids: [t.result.message_id], mainId: t.result.message_id, mode: "error" } : r;
  }
  if (r.ok) { d.previewId = r.mainId; d.previewIds = r.ids; d.previewMode = r.mode; await linkMsg(env, r.mainId, d.id); }
  const notes = [...(d.planNotes || []), ...(d.notes || [])];
  if (d.media && r.mode === "preview") notes.push("Текст длиннее 1024 символов: картинка стоит крупным превью над текстом.");
  if (d.media && r.mode === "split") notes.push("Текст длиннее 1024 символов: визуал и текст уйдут двумя сообщениями.");
  if (notes.length) await tg(env, "sendMessage", { chat_id: chatId, text: `📝 ${notes.join("\n")}`, reply_parameters: r.ok ? { message_id: r.mainId } : undefined });
  if (d.askVisual && !d.media) {
    await tg(env, "sendMessage", { chat_id: chatId, text: d.askVisual, reply_parameters: r.ok ? { message_id: r.mainId } : undefined });
    await setPending(env, chatId, { id: d.id, kind: "photo" });
    delete d.askVisual;
  }
  await putDraft(env, d);
}
// ---------- handlers ----------
async function runFormat(env, chatId, d, instruction, variant = false) {
  await tg(env, "sendChatAction", { chat_id: chatId, action: "typing" });
  const status = await tg(env, "sendMessage", { chat_id: chatId, text: instruction ? "✏️ Правлю…" : variant ? "🔁 Делаю другой вариант…" : "⏳ Оформляю…" });
  try {
    const out = await layout(env, d, instruction, variant);
    const keep = d.buttonsEdited ? d.buttons : null;
    Object.assign(d, out, { kb: "main" });
    if (keep) d.buttons = keep;   // buttons edited by hand stay as they are (reactions are never touched by the model)
    await sendPreview(env, chatId, d);
  } catch (e) {
    console.log("format error", e.stack || e);
    await tg(env, "sendMessage", { chat_id: chatId, text: `❌ Ошибка: ${e.message}` });
  } finally {
    if (status.ok) await tg(env, "deleteMessage", { chat_id: chatId, message_id: status.result.message_id });
  }
}

const HELP = `Пришли текст поста (или фото с подписью) — верну его оформленным в стиле канала.
Или нажми «${PLAN_BUTTON}» / напиши дату (например 29.11) — возьму текст и визуал из контент-плана.

Под превью:
📤 Опубликовать — отправить в канал
🔁 Другой вариант — переформатировать заново
✏️ Поправить текст — написать, что изменить (или просто ответь на превью); так же меняется хештег
🖼 Визуал — прислать фото/видео к посту (или ответь фото на превью)
🔘 Кнопки — текст, ссылка и цвет кнопок, добавить/удалить

/plan — контент-план · /emoji — свои премиум-эмодзи · /channel — настройки`;
const MENU = { keyboard: [[{ text: PLAN_BUTTON }]], resize_keyboard: true, is_persistent: true };

async function onMessage(env, msg) {
  const chatId = msg.chat.id;
  const text = msg.text ?? msg.caption ?? "";
  if (text.startsWith("/start") || text.startsWith("/help")) return tg(env, "sendMessage", { chat_id: chatId, text: HELP, reply_markup: MENU });
  if (text.startsWith("/channel")) {
    const me = await tg(env, "getMe", {});
    const info = me.ok ? await tg(env, "getChat", { chat_id: me.result.id }) : null;
    const names = info?.ok ? [info.result.username, ...(info.result.active_usernames || [])].filter((v, k, a) => v && a.indexOf(v) === k) : [];
    return tg(env, "sendMessage", { chat_id: chatId, text: `Канал для публикации: ${env.CHANNEL_ID}\nКонтент-план: ${env.PLAN_URL ? "подключён" : "не подключён"}\nПремиум-эмодзи: ${env.PREMIUM_EMOJI === "on" ? "вкл" : "выкл"}\nЮзернеймы бота: ${names.length ? names.map((n) => "@" + n).join(", ") : "—"}` });
  }
  if (text.startsWith("/plan") || text === PLAN_BUTTON) return showPlan(env, chatId);
  if (text.startsWith("/emoji")) {
    await setPending(env, chatId, { kind: "pemoji" });
    return tg(env, "sendMessage", { chat_id: chatId, text: "Пришли премиум-эмодзи, которые бот должен ставить в постах (можно сразу много). Каждый заменит свой обычный аналог: например премиум-🔥 вместо обычного 🔥.\nЭмодзи из постов канала бот уже знает." });
  }
  const dm = !msg.photo && text.match(DATE_RE);
  if (dm && Number(dm[1]) <= 31 && Number(dm[2]) <= 12) return loadPlanPost(env, chatId, normDate(dm[1], dm[2]));

  const hasMedia = !!(msg.photo || msg.video || msg.animation || msg.document);
  const pending = await getPending(env, chatId);
  const clear = () => env.DRAFTS.delete(`pending:${chatId}`);

  // a reply to a preview: media -> visual for that post, text -> edit instruction
  if (msg.reply_to_message) {
    const rid = await env.DRAFTS.get(`m:${msg.reply_to_message.message_id}`);
    const d = rid && (await getDraft(env, rid));
    if (d && hasMedia && !msg.caption) { if (pending?.kind === "photo") await clear(); return attachMedia(env, chatId, d, msg); }
    if (d && text) return runFormat(env, chatId, d, text);
  }
  if (pending?.kind === "pemoji" && text && !hasMedia) {   // /emoji: the owner's premium versions of ordinary emoji
    await clear();
    const found = emojisOf(msg).filter((e) => e.ceid);
    if (!found.length) return tg(env, "sendMessage", { chat_id: chatId, text: "Премиум-эмодзи в сообщении не нашёл. Отправь /emoji ещё раз и пришли именно премиум-эмодзи." });
    const map = JSON.parse((await env.DRAFTS.get("pe:map")) || "{}");
    for (const e of found) map[e.emoji] = e.ceid;
    await env.DRAFTS.put("pe:map", JSON.stringify(map));
    return tg(env, "sendMessage", { chat_id: chatId, text: `✅ Запомнил: ${found.map((e) => e.emoji).join(" ")}\nТеперь эти эмодзи в постах будут премиум-версиями. Всего своих: ${Object.keys(map).length}.` });
  }
  if (pending) {
    const d = await getDraft(env, pending.id);
    if (!d) await clear();
    else if (pending.kind === "photo" && hasMedia && !msg.caption) { await clear(); return attachMedia(env, chatId, d, msg); }
    else if (pending.kind === "btext" && text && !hasMedia) {
      await clear();
      const b = d.buttons?.[pending.i];
      if (b) { b.text = text.trim().slice(0, 64); d.buttonsEdited = true; d.kb = `u:${pending.i}`; await setKb(env, chatId, d); await putDraft(env, d); }
      return tg(env, "sendMessage", { chat_id: chatId, text: `✅ Текст кнопки: ${text.trim().slice(0, 64)}` });
    } else if (pending.kind === "burl" && text && !hasMedia) {
      let u = text.trim();
      if (/^(t\.me|www\.)/i.test(u)) u = `https://${u}`;
      if (!/^(https?:\/\/|tg:\/\/)\S+$/i.test(u)) return tg(env, "sendMessage", { chat_id: chatId, text: "Это не похоже на ссылку. Пришли адрес вида https://… или t.me/…" });
      await clear();
      const b = d.buttons?.[pending.i];
      if (!b) return;
      const old = b.url; b.url = u; d.buttonsEdited = true; d.kb = `u:${pending.i}`;
      const r = await setKb(env, chatId, d);
      if (!r.ok) { b.url = old; return tg(env, "sendMessage", { chat_id: chatId, text: `Telegram не принял ссылку: ${r.description}` }); }
      await putDraft(env, d);
      return tg(env, "sendMessage", { chat_id: chatId, text: `✅ Ссылка кнопки: ${u}` });
    } else if (pending.kind === "bicon" && text && !hasMedia) {
      const b = d.buttons?.[pending.i];
      const found = emojisOf(msg).find((e) => e.ceid);
      if (!b) { await clear(); return; }
      if (/^(нет|no|-)$/i.test(text.trim())) b.ceid = null;
      else if (/^(авто|auto)$/i.test(text.trim())) delete b.ceid;
      else if (found) b.ceid = found.ceid;
      else return tg(env, "sendMessage", { chat_id: chatId, text: "На кнопку ставится только премиум-эмодзи. Пришли его (или «нет» / «авто»)." });
      await clear();
      d.buttonsEdited = true; d.kb = `u:${pending.i}`;
      const r = await setKb(env, chatId, d); await putDraft(env, d);
      return tg(env, "sendMessage", { chat_id: chatId, text: r.ok ? (env.PREMIUM_EMOJI === "on" ? "✅ Эмодзи кнопки обновлён." : "✅ Сохранил. Покажется, когда включим премиум-эмодзи.") : `Telegram: ${r.description}` });
    } else if (pending.kind === "remoji" && text && !hasMedia) {
      const found = emojisOf(msg);
      if (!found.length) return tg(env, "sendMessage", { chat_id: chatId, text: "Не нашёл эмодзи. Пришли одно или несколько, например ❤️🔥👍 (можно премиум)." });
      await clear();
      d.reactions = d.reactions || [];
      if (pending.i >= 0 && d.reactions[pending.i]) Object.assign(d.reactions[pending.i], { emoji: found[0].emoji, ceid: found[0].ceid });
      else for (const e of found) if (d.reactions.length < MAX_REACTIONS) d.reactions.push(e);
      d.buttonsEdited = true; d.kb = "btns";
      const r = await setKb(env, chatId, d); await putDraft(env, d);
      const prem = found.some((e) => e.ceid) && env.PREMIUM_EMOJI !== "on" ? "\nПремиум-эмодзи сохранил: на кнопке он появится после покупки username на Fragment, пока будет обычный." : "";
      return tg(env, "sendMessage", { chat_id: chatId, text: r.ok ? `✅ Реакции: ${d.reactions.map((x) => x.emoji).join(" ")}${prem}` : `Telegram: ${r.description}` });
    } else if (pending.kind === "edit" && text && !hasMedia) { await clear(); return runFormat(env, chatId, d, text); }
  }
  if (hasMedia && !text) return tg(env, "sendMessage", { chat_id: chatId, text: "Получил файл без текста. Чтобы прикрепить его к посту, нажми «🖼 Визуал» под превью или ответь этим фото на превью. Для нового поста пришли фото с подписью." });
  if (!text) return tg(env, "sendMessage", { chat_id: chatId, text: "Пришли текст поста или фото с подписью." });

  const d = { id: newId(), source: text, media: msg.photo ? { kind: "photo", fileId: msg.photo[msg.photo.length - 1].file_id } : null };
  return runFormat(env, chatId, d, null);
}

async function onCallback(env, cq) {
  const chatId = cq.message.chat.id;
  const [action, id, arg, arg2] = cq.data.split(":");
  if (action === "plan") {
    await tg(env, "answerCallbackQuery", { callback_query_id: cq.id, text: `Загружаю ${id}…` });
    return loadPlanPost(env, chatId, id);
  }
  const d = await getDraft(env, id);
  if (!d) return tg(env, "answerCallbackQuery", { callback_query_id: cq.id, text: "Черновик устарел, пришли текст заново." });
  if (d.photo && !d.media) d.media = { kind: "photo", fileId: d.photo };   // drafts saved by the older version
  if (!["unpub", "vrm"].includes(action)) d.previewId = cq.message.message_id;   // these come from other messages
  const ack = (text) => tg(env, "answerCallbackQuery", { callback_query_id: cq.id, ...(text ? { text } : {}) });
  const i = Number(arg), b = d.buttons?.[i];

  // ----- button editor (only the keyboard changes) -----
  const kind = arg, j = Number(arg2);                       // be/bc/bd: kind = u (link) | r (reaction)
  const list = kind === "r" ? (d.reactions = d.reactions || []) : (d.buttons = d.buttons || []);
  const save = async (text) => { const r = await setKb(env, chatId, d); await putDraft(env, d); return ack(r.ok ? text : `Telegram: ${r.description}`.slice(0, 190)); };
  if (action === "bm") { d.kb = "btns"; return save(); }
  if (action === "bk") { d.kb = "main"; return save(); }
  if (action === "be" && list[j]) { d.kb = `${kind}:${j}`; return save(); }
  if (action === "ba" && kind === "u") {
    if (d.buttons.length >= 3) return ack("Не больше 3 кнопок-ссылок");
    d.buttons.push({ text: BUTTON_LABELS.start, url: LINKS.start }); d.buttonsEdited = true;
    d.kb = `u:${d.buttons.length - 1}`;
    return save("Добавил START WORKING — поменяй текст и ссылку");
  }
  if (action === "ba" && kind === "r") {
    if ((d.reactions || []).length >= MAX_REACTIONS) return ack(`Не больше ${MAX_REACTIONS} реакций`);
    await setPending(env, chatId, { id: d.id, kind: "remoji", i: -1 }); await putDraft(env, d); await ack();
    return tg(env, "sendMessage", { chat_id: chatId, text: "Пришли эмодзи для реакций — одно или сразу несколько, например ❤️🔥👍. Можно премиум-эмодзи." });
  }
  if (action === "re" && d.reactions?.[i]) {
    await setPending(env, chatId, { id: d.id, kind: "remoji", i }); await putDraft(env, d); await ack();
    return tg(env, "sendMessage", { chat_id: chatId, text: `Пришли новый эмодзи вместо ${d.reactions[i].emoji}.` });
  }
  if (action === "bc" && list[j]) {
    const it = list[j];
    it.style = STYLES[(STYLES.indexOf(it.style) + 1) % STYLES.length];
    if (!it.style) delete it.style;
    d.buttonsEdited = true;
    return save(`Цвет: ${STYLE_NAME[it.style]}`);
  }
  if (action === "bd" && list[j]) { list.splice(j, 1); d.buttonsEdited = true; d.kb = "btns"; return save("Удалено"); }
  if (action === "bt" && b) {
    await setPending(env, chatId, { id: d.id, kind: "btext", i }); await putDraft(env, d); await ack();
    return tg(env, "sendMessage", { chat_id: chatId, text: `Пришли новый текст для кнопки «${b.text}».\nВ канале кнопки обычно капсом: WRITE OUR MANAGER, START WORKING.` });
  }
  if (action === "bl" && b) { d.kb = `l:${i}`; return save(); }
  if (action === "bi" && b) {
    await setPending(env, chatId, { id: d.id, kind: "bicon", i }); await putDraft(env, d); await ack();
    return tg(env, "sendMessage", { chat_id: chatId, text: `Пришли премиум-эмодзи для кнопки «${b.text}» — он встанет перед текстом.\nНапиши «нет», чтобы убрать, или «авто» — эмодзи по ссылке (💬 менеджер, 🚀 старт, 👨‍🎓 курс).` });
  }
  if (action === "bs" && b && LINKS[arg2]) { b.url = LINKS[arg2]; d.buttonsEdited = true; d.kb = `u:${i}`; return save("Ссылка изменена"); }
  if (action === "bu" && b) {
    await setPending(env, chatId, { id: d.id, kind: "burl", i }); await putDraft(env, d); await ack();
    return tg(env, "sendMessage", { chat_id: chatId, text: `Пришли ссылку для кнопки «${b.text}» (https://… или t.me/…).` });
  }
  if (action === "rp") return ack("Реакции заработают в канале после публикации: подписчики нажимают — счётчик растёт.");

  // ----- visual -----
  if (action === "vis") {
    await setPending(env, chatId, { id: d.id, kind: "photo" }); await putDraft(env, d); await ack();
    return tg(env, "sendMessage", {
      chat_id: chatId, reply_parameters: { message_id: cq.message.message_id },
      text: d.media ? "Пришли новое фото или видео — заменю визуал этого поста." : "Пришли фото или видео — прикреплю к этому посту.",
      reply_markup: d.media ? { inline_keyboard: [[cb("🗑 Убрать визуал", `vrm:${d.id}`)]] } : undefined,
    });
  }
  if (action === "vrm") {
    await env.DRAFTS.delete(`pending:${chatId}`);
    for (const pid of d.previewIds || [d.previewId]) if (pid) await tg(env, "deleteMessage", { chat_id: chatId, message_id: pid });
    d.media = null; d.kb = "main"; d.notes = []; d.planNotes = [];
    await ack("Визуал убран");
    return sendPreview(env, chatId, d);
  }

  if (action === "edit") {
    await setPending(env, chatId, { id: d.id, kind: "edit" });
    await putDraft(env, d); await ack();
    return tg(env, "sendMessage", { chat_id: chatId, text: "Что поправить? Напиши одним сообщением — например: «короче», «цифры в цитату», «другой заголовок», «хештег #ask».", reply_parameters: { message_id: cq.message.message_id } });
  }
  if (action === "redo") {
    await tg(env, "answerCallbackQuery", { callback_query_id: cq.id, text: "Делаю другой вариант…" });
    return runFormat(env, chatId, d, null, true);
  }
  if (action === "pub") {
    const html = withPremium(env, d.html);
    const rows = postRows(env, d, { channel: true });
    let r = await sendPost(env, env.CHANNEL_ID, d, html, rows.length ? { inline_keyboard: rows } : undefined);
    if (emojiRefused(r) && env.PREMIUM_EMOJI === "on") {
      return tg(env, "answerCallbackQuery", { callback_query_id: cq.id, show_alert: true, text: `Не опубликовано: Telegram не принял премиум-эмодзи (${r.description}). Проверь, что юзернейм с Fragment привязан к боту (/channel).`.slice(0, 190) });
    }
    if (!r.ok) return tg(env, "answerCallbackQuery", { callback_query_id: cq.id, text: `Не опубликовано: ${r.description}`.slice(0, 190), show_alert: true });
    d.published = { chat: env.CHANNEL_ID, id: r.mainId, ids: r.ids }; await putDraft(env, d);
    if (d.reactions?.length) {   // counters live in a Durable Object per channel message
      const stub = env.REACTIONS.get(env.REACTIONS.idFromName(`${env.CHANNEL_ID}:${r.mainId}`));
      await stub.init({ chat: String(env.CHANNEL_ID), msg: r.mainId, buttons: d.buttons || [], reactions: d.reactions });
    }
    let planLine = "";
    if (d.plan && env.PLAN_STATUS !== "off") {
      try { await planCall(env, { action: "status", date: d.plan.date, value: "Posted" }); planLine = `\nСтатус ${d.plan.date} в контент-плане: Posted.`; }
      catch (e) { planLine = `\nСтатус в плане не обновил: ${e.message}`; }
    }
    const cid = String(env.CHANNEL_ID).replace(/^-100/, "");
    await tg(env, "answerCallbackQuery", { callback_query_id: cq.id, text: "Опубликовано ✅" });
    return tg(env, "sendMessage", {
      chat_id: chatId, text: `✅ Опубликовано в канал.${planLine}`, reply_parameters: { message_id: cq.message.message_id },
      reply_markup: { inline_keyboard: [[{ text: "Открыть пост", url: `https://t.me/c/${cid}/${r.mainId}` }, { text: "🗑 Удалить из канала", callback_data: `unpub:${d.id}` }]] },
    });
  }
  if (action === "unpub" && d.published) {
    let ok = true, why = "";
    for (const mid of d.published.ids || [d.published.id]) {
      const r = await tg(env, "deleteMessage", { chat_id: d.published.chat, message_id: mid });
      if (!r.ok) { ok = false; why = r.description; }
    }
    await tg(env, "answerCallbackQuery", { callback_query_id: cq.id, text: ok ? "Удалено из канала" : `Не удалось: ${why}`.slice(0, 190) });
    if (ok) { delete d.published; await putDraft(env, d); }
    return;
  }
  return tg(env, "answerCallbackQuery", { callback_query_id: cq.id });
}

async function onReaction(env, cq) {
  const chat = String(cq.message.chat.id);
  if (chat !== String(env.CHANNEL_ID)) return tg(env, "answerCallbackQuery", { callback_query_id: cq.id });
  const stub = env.REACTIONS.get(env.REACTIONS.idFromName(`${chat}:${cq.message.message_id}`));
  const res = await stub.vote(String(cq.from.id), Number(cq.data.slice(2)));
  return tg(env, "answerCallbackQuery", { callback_query_id: cq.id, text: res.ok ? (res.state === "removed" ? `${res.emoji} убрано` : `${res.emoji} +1`) : "" });
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
  if (u.callback_query && /^r:\d+$/.test(u.callback_query.data || "") && u.callback_query.message) {
    return onReaction(env, u.callback_query);
  }
  if (u.callback_query) {
    if (String(u.callback_query.from.id) !== owner) return tg(env, "answerCallbackQuery", { callback_query_id: u.callback_query.id, text: "Нет доступа" });
    return onCallback(env, u.callback_query);
  }
}

export default {
  async fetch(request, env0, ctx) {
    const url = new URL(request.url);
    const env = { ...env0, ORIGIN: url.origin };
    if (env.PREMIUM_EMOJI === "on" && url.pathname === "/webhook") {
      try { env.PMAP = { ...BASE_PMAP, ...JSON.parse((await env.DRAFTS.get("pe:map")) || "{}") }; } catch {}
    }
    if (request.method === "GET" && url.pathname.startsWith("/img/")) {   // visuals for large link previews (random ids)
      const id = url.pathname.slice(5).replace(/\.\w+$/, "");
      if (!/^[0-9a-f]{32}$/.test(id)) return new Response("not found", { status: 404 });
      const { value, metadata } = await env.DRAFTS.getWithMetadata(`img:${id}`, "arrayBuffer");
      if (!value) return new Response("not found", { status: 404 });
      return new Response(value, { headers: { "content-type": metadata?.mime || "image/jpeg", "cache-control": "public, max-age=86400" } });
    }
    if (request.method === "GET" && url.pathname === "/setup") {
      const secret = await webhookSecret(env);
      const hook = await tg(env, "setWebhook", { url: `${url.origin}/webhook`, secret_token: secret, allowed_updates: ["message", "callback_query", "my_chat_member"], drop_pending_updates: true });
      const cmds = await tg(env, "setMyCommands", { commands: [{ command: "plan", description: "Посты из контент-плана" }, { command: "emoji", description: "Свои премиум-эмодзи" }, { command: "help", description: "Как пользоваться" }, { command: "channel", description: "Настройки и юзернеймы бота" }] });
      return Response.json({ webhook: hook.ok ? "ok" : hook.description, commands: cmds.ok ? "ok" : cmds.description });
    }
    if (request.method === "POST" && url.pathname === "/webhook") {
      if (request.headers.get("X-Telegram-Bot-Api-Secret-Token") !== (await webhookSecret(env))) return new Response("forbidden", { status: 403 });
      const update = await request.json();
      // process inline and drop Telegram retries
      if (await env.DRAFTS.get(`u:${update.update_id}`)) return new Response("dup");
      await env.DRAFTS.put(`u:${update.update_id}`, "1", { expirationTtl: 3600 });
      // awaited inline and also registered with waitUntil, so the work survives if Telegram stops waiting
      const job = onUpdate(env, update).catch((e) => console.log("update error", e.stack || e));
      ctx.waitUntil(job);
      await job;
      return new Response("ok");
    }
    // optional test hook: only when the TEST_KEY secret exists (used for tuning the prompt; remove the secret afterwards)
    if (request.method === "POST" && url.pathname === "/debug" && env.TEST_KEY && request.headers.get("X-Test-Key") === env.TEST_KEY) {
      const body = await request.json();
      const t0 = Date.now();
      const e2 = { ...env, MODEL: body.model || env.MODEL, AI_OPTS: body.opts || null };
      USAGE.length = 0;
      const d = { id: "debug", source: body.draft, media: null, layout: body.layout || null };
      const out = await layout(e2, d, body.instruction || null, !!body.variant);
      return Response.json({ ms: Date.now() - t0, calls: USAGE, ...out });
    }
    return new Response("m_redactor_bot is running");
  },
};

// One Durable Object per published channel message with reactions: votes (one per user) and a batched keyboard update.
export class Reactions extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    this.sql.exec("CREATE TABLE IF NOT EXISTS votes (uid TEXT PRIMARY KEY, idx INTEGER NOT NULL)");
    this.sql.exec("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT NOT NULL)");
  }
  meta() {
    const row = this.sql.exec("SELECT v FROM meta WHERE k = 'post'").toArray()[0];
    return row ? JSON.parse(row.v) : null;
  }
  async init(post) {
    this.sql.exec("INSERT OR REPLACE INTO meta (k, v) VALUES ('post', ?)", JSON.stringify(post));
    return true;
  }
  counts(n) {
    const c = new Array(n).fill(0);
    for (const r of this.sql.exec("SELECT idx, COUNT(*) AS n FROM votes GROUP BY idx").toArray()) if (r.idx < n) c[r.idx] = r.n;
    return c;
  }
  // tap the same reaction again = remove it; tap another = move the vote
  async vote(uid, idx) {
    const post = this.meta();
    if (!post || !post.reactions[idx]) return { ok: false };
    const cur = this.sql.exec("SELECT idx FROM votes WHERE uid = ?", uid).toArray()[0];
    let state;
    if (cur && cur.idx === idx) { this.sql.exec("DELETE FROM votes WHERE uid = ?", uid); state = "removed"; }
    else { this.sql.exec("INSERT OR REPLACE INTO votes (uid, idx) VALUES (?, ?)", uid, idx); state = cur ? "moved" : "added"; }
    if (!(await this.ctx.storage.getAlarm())) await this.ctx.storage.setAlarm(Date.now() + 1000);   // one edit per second at most
    return { ok: true, state, emoji: post.reactions[idx].emoji };
  }
  async alarm() {
    const post = this.meta();
    if (!post) return;
    const d = { buttons: post.buttons, reactions: post.reactions };
    const rows = postRows(this.env, d, { channel: true, counts: this.counts(post.reactions.length) });
    const r = await tg(this.env, "editMessageReplyMarkup", { chat_id: post.chat, message_id: post.msg, reply_markup: { inline_keyboard: rows } });
    if (!r.ok && r.parameters?.retry_after) await this.ctx.storage.setAlarm(Date.now() + r.parameters.retry_after * 1000);
  }
}
