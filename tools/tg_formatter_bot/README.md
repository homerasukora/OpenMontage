# m_redactor_bot — форматирование постов Ganesha Pay

Telegram-бот на Cloudflare Workers. Владелец присылает черновик → Claude оформляет его в стиле канала
(жирный заголовок с эмодзи, курсив, blockquote, хештег, кнопки) → превью с кнопками →
публикация **только** по кнопке «📤 Опубликовать» и **только** в канал из `CHANNEL_ID`.

- Доступ: только `OWNER_ID`, остальным «Это закрытый бот.»
- Канал: тестовый приватный канал (`CHANNEL_ID` в `wrangler.toml`), бот — админ с правом публикации.
- Стиль: few-shot из постов t.me/ganeshapay (`examples.json`), правила в `src/prompt.js`.
  Факты, цифры и обещания модель не меняет; риски пишет в заметке 📝 по-русски.
- Хештеги: #knowledge #cases #terms #meme #ask (переключаются кнопками).
- Ссылки на кнопках: только менеджер `smmtg-mng` и Academy `smmtg-acen`.
- Премиум-эмодзи: `PREMIUM_EMOJI="off"`. Включать после покупки username на Fragment и привязки к боту
  (id эмодзи из канала — в `premium_emoji.json`).

## Кнопки превью
📤 Опубликовать · 🔁 Другой вариант · ✏️ Поправить (или reply на превью с правкой) ·
🔘 Убрать/вернуть кнопки · хештеги. После публикации: «Открыть пост», «🗑 Удалить из канала».

## Деплой
```bash
npm install
npx wrangler login                       # или CLOUDFLARE_API_TOKEN в окружении
npx wrangler kv namespace create DRAFTS  # id → wrangler.toml
npx wrangler deploy
```
Секреты задаются в Cloudflare Dashboard → Workers → m-redactor-bot → Settings → Variables and Secrets
(тип **Secret**): `BOT_TOKEN`, `ANTHROPIC_API_KEY`. В чат их не присылать.

Потом открыть `https://m-redactor-bot.<subdomain>.workers.dev/setup` — ставит webhook с секретом и команды.

## Проверка без сети
```bash
npx wrangler deploy --dry-run --outdir dist
node test/sim.mjs $PWD/dist/index.js off   # моки Telegram и Claude: превью, хештег, публикация, дубль, чужой, плохой секрет
```
