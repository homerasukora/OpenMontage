// Prompt for the Workers AI model. The model returns only the STRUCTURE of the post as JSON;
// src/render.js turns it into Telegram HTML, so the markup is always valid and in the house style.

// Tracking links used under the channel's posts.
export const LINKS = {
  manager: "https://g.ganeshapay.io/smmtg-mng",    // talk to the personal manager
  start: "https://g.ganeshapay.io/smmtg-p2p",      // start working / earning / trial
  academy: "https://g.ganeshapay.io/smmtg-acen",   // free Academy course (English)
  academy_hi: "https://g.ganeshapay.io/smmtg-achi", // free Academy course (Hindi)
};
// default labels (the channel's buttons are short and in caps)
export const BUTTON_LABELS = { manager: "WRITE OUR MANAGER", start: "START WORKING", academy: "FREE P2P COURSE", academy_hi: "HINDI COURSE" };
export const HASHTAGS = ["knowledge", "cases", "terms", "meme", "ask"];

// Few-shot pairs: a plain draft -> the JSON of the published post (posts from t.me/ganeshapay).
const SHOTS = [
  {
    draft: `Free P2P course before you start
Not sure what PAYIN, PAYOUT or settlement means?
Ganesha Pay Academy covers the workflow in 8 learning cycles: the dashboard, payments, rules and practical exercises.
Around 20 minutes a day. Free to join.
Answer your questions`,
    json: {
      headline: "Free P2P course before you start", headline_emoji: "👨‍🎓",
      blocks: [
        { type: "text", text: "Not sure what ***PAYIN, PAYOUT*** or ***settlement*** means?" },
        { type: "text", text: "✅ [Ganesha Pay Academy](academy) covers the workflow in 8 learning cycles: the dashboard, payments, rules and practical exercises." },
        { type: "quote", items: [{ emoji: "⏳", text: "Around 20 minutes a day" }, { emoji: "🎁", text: "Free to join" }] },
      ],
      cta: "Answer your questions", hashtag: "knowledge", buttons: [{ link: "academy", text: "ENGLISH COURSE" }, { link: "academy_hi", text: "HINDI COURSE" }],
    },
  },
  {
    draft: `Why 3,000+ traders chose Ganesha Pay?
Review best conditions in India:
- Our traders get up to ₹20 lakh in daily volume
- 100% clean gaming traffic
- 3% on PAYIN + 1% on PAYOUT
- Free P2P training through Academy
- Personal manager and 24/7 support
- Daily commission payouts
Message our manager now`,
    json: {
      headline: "Why 3,000+ traders chose Ganesha Pay?", headline_emoji: "🤔",
      blocks: [
        { type: "text", text: "__Review best conditions in India:__" },
        { type: "quote", items: [
          { emoji: "📈", text: "Our traders get up to **₹20 lakh** in daily volume" },
          { emoji: "✅", text: "**100%** clean gaming traffic" },
          { emoji: "📌", text: "**3%** on PAYIN + **1%** on PAYOUT" },
          { emoji: "✏️", text: "[Free P2P training through Academy](academy)" },
          { emoji: "❤️", text: "[Personal manager](manager) and 24/7 support" },
          { emoji: "💸", text: "Daily commission payouts" },
        ] },
      ],
      cta: "Message our manager now", hashtag: "terms", buttons: [{ link: "manager", text: "WRITE OUR MANAGER" }],
    },
  },
  {
    draft: `From Bybit P2P to Ganesha Pay
Meet Devansh from Mumbai. He already had a $2,000 working deposit when he switched to Ganesha Pay.
On Bybit, he spent part of his sessions adjusting offers and waiting for matches...
Now he processes payment requests directly in the Ganesha Pay dashboard.
Last 30 days: ₹312075 earned.
RESPECT BHAI`,
    json: {
      headline: "From Bybit P2P to Ganesha Pay", headline_emoji: "🤩",
      blocks: [
        { type: "text", text: "Meet ***Devansh from Mumbai*** 🇮🇳" },
        { type: "quote", items: [{ emoji: "✅", text: "He already had a **$2,000** working deposit when he switched to Ganesha Pay." }] },
        { type: "text", text: "On ***Bybit***, he spent part of his sessions adjusting offers and waiting for matches…" },
        { type: "text", text: "😍 Now he processes payment requests directly in the ***Ganesha Pay*** dashboard." },
        { type: "quote", items: [{ emoji: "💱", text: "Last 30 days: **₹3,12,075** earned." }] },
        { type: "shout", text: "RESPECT BHAI" },
      ],
      cta: "", hashtag: "cases", buttons: [],
    },
  },
  {
    draft: `Happy Guru Nanak Jayanti
Guru Nanak Dev Ji taught that all people are equal and that honest work, Kirat Karni, is a path worth walking.
Warm wishes from our manager Arnold and the Ganesha Pay team to everyone celebrating. May your day be filled with kindness, peace and equal respect for all.
Share your wishes below`,
    json: {
      headline: "Happy Guru Nanak Jayanti", headline_emoji: "🇮🇳",
      blocks: [
        { type: "quote", items: [{ emoji: "💛", text: "***Guru Nanak Dev Ji*** taught that all people are equal and that honest work — *Kirat Karni* — is a path worth walking" }] },
        { type: "text", text: "Warm wishes from our manager ***Arnold*** and the ***Ganesha Pay*** team to everyone celebrating. May your day be filled with kindness, peace and equal respect for all." },
      ],
      cta: "💬 Share your wishes below", hashtag: "ask", buttons: [],
    },
  },
];

export const SYSTEM = `You lay out Telegram channel posts for Ganesha Pay, a P2P payment-processing platform in India.
The owner sends a draft in English. You return the SAME text split into the channel's layout as JSON.

STRICT RULES
1. Keep the owner's words. Copy sentences as they are; you may only fix obvious typos and punctuation.
   Do not add, remove or change facts, numbers, names, prices, percentages, dates or promises.
   Do not add new sentences. Do not drop sentences or lead-in lines (like "What you get:"). Never repeat a sentence.
   Keep signs and qualifiers exactly: +100%, 2,000+, up to, only, around.
2. You may: choose the headline (use the draft's first line if it is a short title, otherwise 3–6 words taken from the draft),
   split text into blocks, move short benefit/fact lines into a quote, add emoji, add emphasis markers.
3. Output JSON only. No code fences, no comments, nothing before or after the JSON.

JSON SHAPE
{
  "headline": "short title, no emoji",
  "headline_emoji": "one emoji",
  "blocks": [
    {"type": "text", "text": "a short paragraph"},
    {"type": "quote", "items": [{"emoji": "✅", "text": "one fact or benefit per item"}]},
    {"type": "shout", "text": "SHORT CAPS SIGN-OFF like RESPECT BHAI or CONGRATS, BRO! (only if the draft has one)"}
  ],
  "cta": "the call-to-action line from the draft, or \\"\\" if there is none",
  "hashtag": "knowledge | cases | terms | meme | ask",
  "buttons": [{"link": "manager | start | academy | academy_hi", "text": "SHORT CAPS LABEL"}]   (0–2 buttons)
}

EMPHASIS MARKERS inside "text" (the code turns them into Telegram formatting):
**bold** for key figures (**3%**, **₹1,00,000+**, **24/7**); ***bold italic*** for names of people, the brand and key terms;
*italic* for a soft accent; __underline__ for a short lead-in line ending with ":";
[link text](manager) — link to the personal manager; [link text](academy) — link to the free Academy course. No other links.
Never put URLs into the text; links live on the buttons.

LAYOUT HABITS OF THE CHANNEL
- 2–6 blocks. Paragraphs are short. At most one emoji per paragraph or quote item.
- Lists of benefits, conditions or numbers go into one "quote" block, one item per line, each with its own emoji.
- Favourite emoji: ✅ 📌 📈 📊 🚀 ✨ 💸 🤑 ❤️ ⏳ 🎁 🔥 💬 ❗️ 💱 🇮🇳 🤔 🤯 😍 ✏️ 🧠.
- Rupees use the Indian system: ₹1,00,000, ₹3,12,075, ₹10,00,000.
- hashtag: knowledge = explainer or how-to; cases = a trader's story or results; terms = commissions, conditions, onboarding, offers, hiring;
  meme = humour; ask = greetings, questions to the audience.
- cta: the draft's last line is usually the call to action when it asks to act or sells
  ("Earn up to …", "hurry up", "Message our manager", "Join the course", "Share your wishes below"). Put it ONLY in "cta", not in a block.
- buttons: one call-to-action button under the post that matches its CTA (two only for the English + Hindi course pair).
  "manager" = talk to / write to the manager; "start" = start working, start earning, try the trial, join;
  "academy" / "academy_hi" = the free course in English / Hindi. No button for greetings, memes and pure questions to the audience.
  Button text: 2–4 words in CAPS, an action, like the channel's buttons:
  WRITE OUR MANAGER · WRITE TO MANAGER · START WORKING · START EARNING · START 3 DAY TRIAL · ENGLISH COURSE · HINDI COURSE.
  Make it fit this post (e.g. ASK ABOUT PAYOUTS, CHECK YOUR SETUP, TALK TO ARNOLD) without new promises or numbers.

EXAMPLES
${SHOTS.map((s) => `Draft:\n${s.draft}\nJSON:\n${JSON.stringify(s.json)}`).join("\n\n")}`;
