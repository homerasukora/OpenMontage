# Lesson 2 — хинди (готовая озвучка заказчика), Ganesha Pay Noir, 16:9, 85.6 с, 24 fps

Исходник: видео с уже готовой хинди-озвучкой (85.7 с, 2056 кадров, 24 fps). Звук не меняется.

## Маска
- RVM ResNet50, `FPS=24 matte.py ... 198,504,776,991,1117,1121,1236,1781,2049` (сброс на склейках).
- Кадры 1056–1116: наезд и быстрый зум исходника — маска держится. Кадры 1117–1120: зум-блюр-переход исходника,
  на размытых кадрах маска ловила неон «K» (до 1221 px) и стол → эти 4 кадра заменены плавным наплывом
  1116 → 1121 (`patch_frames.py`).
- Готовый файл: неон 0 px, структура фона вне ведущего 0 px.

## Субтитры
- Речь порезана на куски 1.2–3.2 с по самым тихим точкам (`hi_phrases.py`), каждый распознан Whisper medium (hi);
  текст восстановлен вручную по распознаванию и смыслу английского Lesson 2 (`spans_hi.txt`: начало, конец, текст,
  `|` — смена экрана; время внутри фразы делится по числу символов).
- Название — латиницей «Ganesha Pay».
- Не подтверждено распознаванием (уточнить по слуху):
  - ~29.7 с: «Ganesha Pay प्रोवाइड करता है:» — «क्या» не слышно, записано как звучит;
  - ~72 с: «कि आपको Ganesha Pay **जॉइन** करना ही है» — слово перед «करना ही है» неразборчиво, «जॉइन» по смыслу оригинала.
- Подпись «पाठ 2» — Noto Serif Devanagari; субтитры — Noto Sans Devanagari SemiBold 56 px, шампань.

## Сборка
```
python3 tools/lesson1_blackbg/render.py src.mp4 alpha.mkv words.json video_only.mp4 --fps 24 --cut 0,0 --end 2049 \
    --shots 198,504,776,991,1117,1121,1236,1781,2049 --fonts fonts --logo assets/ganesha_pay_wordmark_noir.png --static \
    --label "पाठ 2" --label-font NotoSerifDeva:SemiBold --sub-font NotoSansDeva:SemiBold --subs projects/lesson2_hi/subs.json
python3 tools/lesson1_blackbg/patch_frames.py video_only.mp4 video_fix.mp4 24 1117 1120
# mux video_fix.mp4 + исходный звук
```
