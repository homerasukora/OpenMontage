// JSON layout -> Telegram HTML in the Ganesha Pay house style, plus fidelity checks against the draft.
import { LINKS, HASHTAGS, BUTTON_LABELS } from "./prompt.js";

const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

// ₹312075 / ₹3,120,75 / ₹ 1000000 -> ₹3,12,075 / ₹10,00,000
export function indianRupees(s) {
  return String(s).replace(/₹\s?(\d[\d,]*)/g, (m, num) => {
    const d = num.replace(/,/g, "");
    if (d.length < 4) return `₹${num}`;
    const last3 = d.slice(-3), rest = d.slice(0, -3);
    return `₹${rest.replace(/\B(?=(\d{2})+(?!\d))/g, ",")},${last3}`;
  });
}

// inline markers -> HTML. quote=true: the plain parts are wrapped in <i>, links stay bold-italic.
function inline(raw, { quote = false } = {}) {
  const text = indianRupees(String(raw ?? "").replace(/\s*\n\s*/g, " ").trim());
  const parts = text.split(/(\[[^\]\n]+\]\((?:manager|start|academy|academy_hi)\))/);
  const out = parts.map((p) => {
    const link = p.match(/^\[([^\]\n]+)\]\((manager|start|academy|academy_hi)\)$/);
    if (link) return `<a href="${LINKS[link[2]]}"><b><i>${esc(link[1].replace(/[*_]/g, ""))}</i></b></a>`;
    let h = esc(p);
    h = h.replace(/\*\*\*([^*\n]+?)\*\*\*/g, quote ? "<b>$1</b>" : "<b><i>$1</i></b>");
    h = h.replace(/\*\*([^*\n]+?)\*\*/g, "<b>$1</b>");
    h = h.replace(/__([^_\n<>]+?)__/g, "<u>$1</u>");
    h = h.replace(/(^|[^\w*])\*([^*\n<>]+?)\*(?![\w*])/g, quote ? "$1$2" : "$1<i>$2</i>");
    h = h.replace(/\*+/g, "").replace(/(^|\s)__|__(\s|$)/g, "$1$2");
    if (!quote || !h.trim()) return h;
    const lead = h.match(/^\s*/)[0], tail = h.match(/\s*$/)[0];
    return `${lead}<i>${h.trim()}</i>${tail}`;
  }).join("");
  return balanced(out) ? out : esc(text.replace(/[*_]{2,}|\[|\]\((manager|start|academy|academy_hi)\)/g, ""));
}

function balanced(html) {
  const stack = [];
  for (const m of html.matchAll(/<(\/?)([a-z]+)[^>]*>/g)) {
    if (!m[1]) stack.push(m[2]);
    else if (stack.pop() !== m[2]) return false;
  }
  return stack.length === 0;
}

const stripEmojiEnd = (s) => String(s ?? "").replace(/[\s👇.]+$/u, "").trim();

// the draft's closing call to action sometimes stays a plain paragraph — lift it into "cta"
const CTA_RE = /\b(hurry|message|join|start|apply|share|write|tap|click|earn|learn|sign up|contact|register|dm|text us|ask|comment|follow|subscribe|open|try)\b/i;
export function normalizeLayout(p) {
  const blocks = (p.blocks || []).filter(Boolean);
  const last = blocks[blocks.length - 1];
  if (!String(p.cta || "").trim() && last?.type === "text" && p.hashtag !== "cases") {
    const sents = String(last.text || "").split(/(?<=[.!?])\s+/);
    const tail = sents[sents.length - 1];
    if (CTA_RE.test(tail) && allWords(tail).length <= 10) {
      p.cta = tail;
      const rest = sents.slice(0, -1).join(" ").trim();
      if (rest) last.text = rest; else blocks.pop();
    }
  }
  p.blocks = blocks;
  return p;
}

export function renderPost(p) {
  normalizeLayout(p);
  const out = [];
  const head = String(p.headline || "").replace(/[*_]/g, "").trim();
  if (head) out.push(`<b>${esc(indianRupees(head))}${p.headline_emoji ? " " + esc(p.headline_emoji) : ""}</b>`);
  for (const b of p.blocks || []) {
    if (!b) continue;
    if (b.type === "quote") {
      const items = (b.items || []).filter((i) => i && String(i.text || "").trim());
      if (items.length) out.push(`<blockquote>${items.map((i) => `${i.emoji ? esc(i.emoji) + " " : ""}${inline(i.text, { quote: true })}`).join("\n")}</blockquote>`);
    } else if (b.type === "shout") {
      if (String(b.text || "").trim()) out.push(`🇮🇳 — <b><u>${esc(String(b.text).replace(/[*_]/g, "").trim().toUpperCase())}</u></b>`);
    } else if (String(b.text || "").trim()) {
      out.push(inline(b.text));
    }
  }
  const cta = stripEmojiEnd(p.cta);
  if (cta) out.push(`<b>${inline(cta).replace(/<\/?b>/g, "")} 👇</b>`);
  const tag = HASHTAGS.includes(p.hashtag) ? p.hashtag : "knowledge";
  out.push(`#${tag}`);
  return { html: out.join("\n\n"), hashtag: tag, buttons: layoutButtons(p) };
}

// [{link, text}] or ["manager"] -> [{text, url}]; labels are short caps without markup or numbers that are not in the post
export function layoutButtons(p) {
  const seen = new Set(), res = [];
  for (const b of p.buttons || []) {
    const link = typeof b === "string" ? b : b?.link;
    if (!LINKS[link] || seen.has(link)) continue;
    seen.add(link);
    let text = typeof b === "object" ? String(b.text || "").replace(/[*_\[\]<>]/g, "").replace(/\s+/g, " ").trim() : "";
    if (!text || text.length > 32) text = BUTTON_LABELS[link];
    res.push({ text: text.toUpperCase(), url: LINKS[link], style: "success" });   // call-to-action buttons are green by default
  }
  return res.slice(0, 2);
}

// ---------- parsing the model answer ----------
export function parseLayout(text) {
  let t = String(text || "").replace(/<think>[\s\S]*?<\/think>/g, "").trim();
  t = t.replace(/^```(?:json)?\s*/i, "").replace(/```\s*$/, "");
  const a = t.indexOf("{"), b = t.lastIndexOf("}");
  if (a < 0 || b <= a) return null;
  try {
    const j = JSON.parse(t.slice(a, b + 1));
    if (!j || typeof j !== "object" || !Array.isArray(j.blocks)) return null;
    return j;
  } catch { return null; }
}

// ---------- fidelity checks (draft vs layout) ----------
const plain = (s) => String(s ?? "").replace(/\[([^\]]+)\]\((?:manager|start|academy|academy_hi)\)/g, "$1").replace(/[*_]/g, "");
export function layoutText(p, { headline = true } = {}) {
  const parts = [headline ? p.headline : "", p.cta];
  for (const b of p.blocks || []) { parts.push(b?.text); for (const i of b?.items || []) parts.push(i?.text); }
  return plain(parts.filter(Boolean).join("\n"));
}
const numList = (s) => (String(s).match(/\d[\d,.]*\d|\d/g) || []).map((n) => n.replace(/,/g, "").replace(/\.0+$/, ""));
const numbers = (s) => new Set(numList(s));
const counts = (arr) => arr.reduce((m, x) => m.set(x, (m.get(x) || 0) + 1), new Map());
const allWords = (s) => String(s).toLowerCase().match(/[a-z0-9]+/g) || [];
const sentences = (s) => String(s).split(/\n+|(?<=[.!?])\s+/).map((x) => x.trim()).filter((x) => allWords(x).length >= 2);
const STOP = new Set("a an the and or of to in on at for with by from is are was were be been it its this that these those your you our we us he she they his her their my me i as if so but not no do does did have has had will can just get got more most up out about into over than then there here what who how why when which all any each per via".split(" "));
const words = (s) => (String(s).toLowerCase().match(/[a-z]+/g) || []).map((w) => w.replace(/(ies|es|s)$/, "")).filter((w) => w.length > 2 && !STOP.has(w));

const RISKY = [
  [/guarantee/i, "«guaranteed» — гарантированный доход обещать нельзя"],
  [/passive income|passive earning/i, "«passive income» — работа требует внимания, так называть нельзя"],
  [/risk[- ]?free|no risk|zero risk/i, "«no risk» — нельзя обещать отсутствие рисков"],
  [/100% safe|fully safe|completely safe|totally safe/i, "«100% safe» — нельзя обещать полную безопасность"],
  [/no (bank )?(blocks|freezes)|never (get )?block|no blocking/i, "обещание «без блокировок» — так писать нельзя"],
  [/easy money|quick money|get rich/i, "«easy money» — хайп, против правил канала и YouTube/Meta"],
  [/earn (up to|from|over|more than)|₹[\d,]+\s*(\/|per|a)\s*(day|month|week)/i, "обещание дохода — подавай как возможность, проверь цифру и ставку перед публикацией"],
];

export function checkLayout(source, p, { caption = false, html = "" } = {}) {
  const problems = [];   // reasons to retry the model
  const notes = [];      // shown to the owner (Russian)
  const out = layoutText(p);
  const srcN = numbers(source), outN = numbers(out);
  const added = [...outN].filter((n) => !srcN.has(n));
  const lost = [...srcN].filter((n) => !outN.has(n));
  if (added.length) { problems.push(`You added numbers that are not in the draft: ${added.join(", ")}. Use only the draft's numbers.`); notes.push(`⚠️ Появились числа, которых нет в черновике: ${added.join(", ")}`); }
  if (lost.length) { problems.push(`You dropped numbers from the draft: ${lost.join(", ")}. Keep every number.`); notes.push(`⚠️ Пропали числа из черновика: ${lost.join(", ")}`); }

  // a number used more often than in the draft = a new claim (the headline may repeat a figure)
  const srcC = counts(numList(source)), bodyC = counts(numList(layoutText(p, { headline: false })));
  const extra = [...bodyC].filter(([n, k]) => srcC.has(n) && k > srcC.get(n)).map(([n]) => n);
  if (extra.length) problems.push(`These numbers appear more often than in the draft: ${extra.join(", ")}. Do not repeat a figure or turn a word into a number.`);

  // every sentence of the draft must survive; no sentence may appear twice
  const outBag = counts(allWords(out));
  const lostS = sentences(source).filter((x) => { const w = allWords(x); return w.filter((t) => outBag.has(t)).length / w.length < 0.6; });
  if (lostS.length) { problems.push(`You dropped these lines of the draft: ${lostS.map((x) => `"${x}"`).join("; ")}. Put them back.`); notes.push(`Похоже, пропало: ${lostS.map((x) => `«${x}»`).join("; ")}`); }
  const seen = new Map(), srcSent = counts(sentences(source).map((x) => allWords(x).join(" ")));
  for (const x of sentences(layoutText(p, { headline: false }))) { const k = allWords(x).join(" "); seen.set(k, (seen.get(k) || 0) + 1); }
  const dup = [...seen].filter(([k, n]) => n > 1 && n > (srcSent.get(k) || 0)).map(([k]) => k);
  if (dup.length) problems.push(`You repeated a sentence: "${dup[0]}". Each sentence of the draft goes in exactly once (the CTA too).`);

  const srcW = new Set(words(source)), outW = words(out);
  const newW = [...new Set(outW.filter((w) => !srcW.has(w)))];
  if (newW.length > 6) { problems.push(`You added words that are not in the draft (${newW.slice(0, 8).join(", ")}). Keep the owner's wording.`); notes.push(`Добавлены слова не из черновика: ${newW.slice(0, 8).join(", ")}`); }
  const outSet = new Set(outW);
  const missW = [...srcW].filter((w) => !outSet.has(w));
  if (srcW.size >= 8 && missW.length / srcW.size > 0.2) { problems.push(`You dropped parts of the draft (missing: ${missW.slice(0, 8).join(", ")}). Keep every sentence.`); notes.push(`Похоже, часть текста пропала: ${missW.slice(0, 8).join(", ")}`); }

  for (const [re, msg] of RISKY) if (re.test(source) || re.test(out)) notes.push(`❗ ${msg}`);
  if (!String(p.cta || "").trim() && !(p.buttons || []).length && p.hashtag !== "cases" && p.hashtag !== "meme") notes.push("Нет призыва к действию (CTA) и кнопок.");
  const plainLen = html.replace(/<[^>]+>/g, "").length;
  if (caption && plainLen > 1024) notes.push(`Подпись к фото длиннее 1024 символов (${plainLen}) — Telegram её не примет.`);
  if (!caption && plainLen > 4096) notes.push(`Пост длиннее 4096 символов (${plainLen}).`);
  return { problems, notes };
}

// ---------- no-model fallback: simple deterministic layout ----------
export function fallbackLayout(source) {
  const lines = String(source).split("\n").map((l) => l.trim()).filter(Boolean);
  const first = lines[0] || "";
  const short = first.split(/\s+/).length <= 8 && !/[.!?]$/.test(first);
  const headline = short ? lines.shift() : first.split(/\s+/).slice(0, 5).join(" ");
  const blocks = [];
  let quote = null;
  for (const l of lines) {
    const m = l.match(/^[-•*–]\s*(.+)$/);
    if (m) { if (!quote) { quote = { type: "quote", items: [] }; blocks.push(quote); } quote.items.push({ emoji: "📌", text: m[1] }); }
    else { quote = null; blocks.push({ type: "text", text: l }); }
  }
  return { headline, headline_emoji: "✨", blocks, cta: "", hashtag: "knowledge", buttons: [] };
}

// ---------- draft preparation: links -> buttons, hashtag -> fixed, placeholders -> notes ----------
const LINK_BY_URL = Object.fromEntries(Object.entries(LINKS).map(([k, u]) => [u.replace(/^https?:\/\//, ""), k]));
export function prepareDraft(source) {
  let text = String(source || "").replace(/\r/g, "");
  const links = [], notes = [];
  text = text.replace(/https?:\/\/\S+/g, (u) => {
    const k = LINK_BY_URL[u.replace(/^https?:\/\//, "").replace(/[).,]+$/, "")];
    if (k) links.push(k); else notes.push(`Ссылка из текста не в списке кнопок, вставь её вручную при необходимости: ${u}`);
    return "";
  });
  let hashtag = null;
  text = text.replace(/(^|\s)#(knowledge|cases|terms|meme|ask)\b/gi, (m, sp, t) => { hashtag = hashtag || t.toLowerCase(); return sp; });
  for (const m of text.match(/\[[A-Z][^\]\n]{3,80}\]/g) || []) notes.push(`В тексте заглушка ${m} — замени перед публикацией.`);
  text = text.split("\n").map((l) => l.replace(/[ \t]+$/, "")).join("\n").replace(/\n{3,}/g, "\n\n").trim();
  return { text, hashtag, links: [...new Set(links)], notes };
}
