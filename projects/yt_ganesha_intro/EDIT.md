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
