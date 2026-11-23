# YouTube #1 «Who we are» — монтаж

Итог: 1920×1080, 30 fps, 2:27, звук −15.8 LUFS (пик −1.4 dB).

## Пайплайн
1. **Озвучка** — ElevenLabs `eleven_v4`, голос *Raj – Indian English Ads & Social*, по 2 дубля на часть,
   выбор по распознаванию (Parakeet): s1 take1, s2_b, s3_a, s4_b, s5_b, s6a_b, s6b_b, s7_a, s8_b, s10_a.
2. **Анимация** — Higgsfield Wan 3.0, 1080p, 16:9, фото студии Arnold + аудио части, промпт `tools/yt_ganesha_intro/wan_prompt.txt`.
   - Wan не принимает части длиннее 15 с (задача падает, кредиты возвращаются) → S3, S4, S6a разрезаны по паузам:
     S3 @ 9.62 с, S4 @ 10.56 с, S6a @ 7.2 с.
   - Wan слегка растягивает/переозвучивает звук в клипе (до +9 %, в S2 «Ganesha Pay» → «Ding Shape»), губы идут за его версией.
     Поэтому в монтаже звучит чистая озвучка ElevenLabs, а видео подгоняется к ней по словам: `align.py` (ASR клипа ↔ ASR озвучки,
     кусочно-линейная карта времени), в рендере — дробные кадры с блендом соседних.
   - В клипе S8 Wan переставил студию (ноутбук справа) → S8 показан только в кружке.
3. **Монтаж** — `tools/yt_ganesha_intro/yt_render.py` (Noir: оникс + изумруд, золото только линии/акценты, текст champagne,
   Cormorant + Manrope, стеклянные плашки, субтитры по словам с золотыми ключевыми словами, логотип слева сверху).
4. **Звук** — голос +13.5 dB, highpass 70 Гц; спокойный бэд `bed.py` (без шумов) на ~20 dB ниже голоса; лимитер −1.5 dBTP.

## Сцены
| Время | Сцена |
|---|---|
| 0:00 | Счётчик ₹0 → ₹3,12,075 «commission · last 30 days», фото Devansh с дашбордом (домен и баннер «Payin Blocked» размыты), «Individual result. Depends on volume.» |
| 0:07 | Arnold в кадре, плашки «Not trading», «Not guessing prices» |
| 0:13 | Punch-in, плашка «Arnold · Manager · Ganesha Pay», главы 01–03 |
| 0:24 | Схема Verified merchant → UPI payments → You (agent) + «Fixed commission on every operation» |
| 0:40 | Arnold слева + панель «One round»; затем карточки PayIn 3% / PayOut 1% + «Commission paid daily in USD» |
| 1:00 | Devansh: фото, «From Bybit P2P → Ganesha Pay», «$2,000 working deposit», Before/Now |
| 1:14 | Таблица Exchange P2P vs Ganesha Pay (Counterparty, Order flow, Commission, Disputes) |
| 1:41 | Карточка «~5 in every 10,000 transactions · ≈ 0.05%» |
| 1:46 | Live counter с сайта (запись экрана в рамке) |
| 1:58 | Ganesha Pay Academy: Free, ~20 min a day, чему учат, сертификат |
| 2:12 | CTA: «Message a manager» / «Free Academy course» / «Links in the description» |

## Рекламные вставки для блогеров (23.11)
Нарезка из финального рендера (графика и субтитры уже вшиты), озвучка — те же отрезки чистого голоса, подложка `bed.py` заново под длину, склейки 0.2 с, −15.5…−16 LUFS.
`tools/yt_ganesha_intro/ad_cut.py <name> start:end ...` (секунды финального таймлайна).
- **60 с** (59.4 с): хук Devansh 0:00–0:13.2 → «кто мы» + один раунд PayIn 3% / PayOut 1% 0:23.88–0:56.15 → CTA и финальная карточка 2:12.27–2:26.6.
- **30 с** (32.5 с): хук → «Ganesha Pay is a P2P processing platform in India with clean merchant traffic.» (0:23.88–0:29.2) → CTA.

## Shorts / Reels 9:16 (23.11)
`tools/yt_ganesha_intro/shorts_render.py` — 1080×1920, 58 с. Сверху Arnold (вертикальный кроп), по центру субтитры,
ниже карточка с графикой из 16:9-сцен (без кружка), вертикальная финальная карточка.
Состав: «кто мы» + один раунд (0:23.88–0:59.62) → споры и 0.05% жалоб (1:37.45–1:46.2) → CTA (2:12.27–2:26.6).
Сознательно убрано для соцсетей: хук с доходом Devansh (₹3,12,075 за 30 дней, «from his phone, not trading»),
фото и кейс Devansh, «I'm Arnold, a manager», сравнение с биржами и логотип Binance.
При загрузке: YouTube Studio → AI use = Yes; Instagram → метка «AI info» (Arnold — сгенерированный ведущий).

### Shorts v2 (23.11)
- Логотип перенесён: по центру под плашкой (y≈1432), в углу его больше нет.
- Вместо уменьшенной графики 16:9 — собственные вертикальные плашки с короткими фразами и крупным шрифтом
  (заголовки Cormorant 72–84, строки Manrope 54, цифры 140–170): «How it works», «One round», PayIn 3% / PayOut +1%,
  «Disputes? Your manager handles them», «~5 per 10,000 payments», две кнопки + «Links in the description».
- Безопасная зона: всё значимое выше y≈1500 и левее x≈960; субтитры не шире 880 px.
- v3: плашка и логотип ниже (~60 px), область ведущего 940 px вместо 860; логотип y≈1462, низ ≈ 1516 (≥ 400 px от нижнего края).
- v4: субтитры под ведущим (y≈1012, на затемнении, не на лице/груди), плашка с y≈1085, логотип y≈1592 — низ кадра занят.
