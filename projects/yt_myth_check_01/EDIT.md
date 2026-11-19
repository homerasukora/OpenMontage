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
| 0:00 | Три цитаты-мифа по одной, на каждой штамп «MYTH?» (удар + встряска), плашка P2P MYTH CHECK |
| 0:08 | Arnold, карточка «Episode 1 · P2P Myth Check» |
| 0:13 | Punch-in, «Arnold · Manager», список трёх мифов |
| 0:22 | MYTH 1 — цитата «P2P processing is a scam.» → Arnold + Red flags → Green flags (6 пунктов, фото Devansh) → штамп MYTH |
| 0:59 | MYTH 2 — цитата → Arnold + «What triggers freezes» → «In Ganesha Pay: verified merchants only», ~5 in 10,000 → штамп MYTH |
| 1:27 | MYTH 3 — цитата → «Average Ganesha Pay agent: up to ₹4,00,000 a month», «Depends on volume. Not guaranteed.», «More? Depends on your bank accounts» → Arnold: Shifts · Confirmations · Limits → штамп MYTH |
| 1:46 | Все три цитаты со штампом MYTH → Arnold + панель Academy → финальная карточка: New to P2P → Free Academy course / Already trading → Message a manager / Links in the description |
