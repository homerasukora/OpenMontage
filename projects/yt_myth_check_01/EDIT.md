# P2P Myth Check #1 — монтаж

Итог: 1920×1080, 30 fps, ~2:09.

## Пайплайн (как в YouTube #1)
1. Озвучка ElevenLabs `eleven_v4`, голос Raj; дубли: хук a, интро a (в b «Ganeshape»), миф 1 a, миф 2 b, миф 3 b, CTA a.
2. Нарезка длинных частей по тишине (≤15 с для Wan): миф 1 @ 13.43 / 23.71 с, миф 2 @ 13.11, миф 3 @ 8.35, CTA @ 10.86.
3. Wan 3.0 1080p 16:9, 11 клипов, фото студии Arnold + аудио, промпт `tools/yt_ganesha_intro/wan_prompt.txt`.
   Студия во всех клипах совпадает. Видео подогнано к чистой озвучке по словам (`tools/yt_ganesha_intro/align.py`).
4. Рендер `tools/yt_myth_check/myth_render.py`, звук `tools/yt_myth_check/mix.py` (голос + бэд `bed.py` + синтезированный «удар печати»).

## Сцены
| Время | Сцена |
|---|---|
| 0:00 | Arnold в кадре с первой секунды. Цитаты-мифы по одной справа → штамп «MYTH?» (удар + встряска) → плашка сжимается и улетает в корзину «MYTHS» |
| 0:09 | Карточка «Episode 1 · P2P Myth Check» |
| 0:13 | Punch-in, «Arnold · Manager», список трёх мифов |
| 0:22 | MYTH 1 — цитата «P2P processing is a scam.» → Arnold + Red flags → Green flags (6 пунктов, фото Devansh) → штамп MYTH |
| 0:59 | MYTH 2 — цитата → Arnold + «What triggers freezes» → «In Ganesha Pay: verified merchants only», ~5 in 10,000 → штамп MYTH |
| 1:27 | MYTH 3 — цитата → «Average Ganesha Pay agent: up to ₹4,00,000 a month», «Depends on volume. Not guaranteed.», «More? Depends on your bank accounts» → Arnold: Shifts · Confirmations · Limits → штамп MYTH |
| 1:46 | Все три цитаты со штампом MYTH → Arnold + панель Academy → финальная карточка: New to P2P → Free Academy course / Already trading → Message a manager / Links in the description |

## Правки v2 (19.11)
- Хук с лицом Arnold: плашка → штамп MYTH? → полёт в корзину MYTHS (звук удара + мягкий «плюх» корзины).
- Синхрон губ 0:13–0:22: в клипе интро Wan сдвинул свою звуковую дорожку на ~0.5 с относительно губ. Проверка губ
  (`lipeval.py`: открытие рта по кадрам ↔ огибающая озвучки) показала, что губы идут по чистой озвучке → для интро
  и первой части мифа 2 карта по словам заменена на прямое соответствие.
- Субтитры «P2P processing» (ASR дал «P two P»).
- Green flags и кружок — с «A real platform shows green flags» (~0:35); до этого Arnold в кадре с Red flags.
- На финальной карточке логотип в левом верхнем углу убран (он уже есть над кнопками).

## Shorts 9:16 — «Is P2P processing a scam?» (23.11)
`tools/yt_myth_check/myth_shorts_render.py` + `myth_shorts_mix.py`, 1080×1920, 58 с, −15.8 LUFS.
Раскладка как у Shorts «Who we are» v4: Arnold сверху (лицо свободно), субтитры под ним, крупные плашки, логотип под плашкой.
Состав: миф 1 целиком (0:22.20–0:59.44 мастера) → CTA целиком (1:46.36–2:07.6).
Плашки: цитата «P2P processing is a scam.» + штамп MYTH? → Red flags (3) → Green flags 1 (KYB, 3% + 1%, live volume) →
Green flags 2 (real manager, agent results, free Academy) → цитата + штамп MYTH (удар + встряска) → Ganesha Pay Academy → две кнопки + «Links in the description».
