# Lesson 4 — Ganesha Pay Noir (16:9, 91.25 с, 24 fps)

Оформление как Lesson 2 (static, без камеры): оникс + изумрудное свечение, вордмарк Noir, «LESSON 4» Cormorant,
субтитры Manrope шампанью. Упоминаний Koi нет → склеек нет.

- Исходник 92.6 с, ~24 fps (VFR), декодируется в 2225 кадров (одинаково в маске и рендере).
- Склейки: 204, 367, 609, 826, 1067, 1255, 1483, 1702, 1943; с 2178 — чёрный хвост, обрезан (`--maxframe 2189`),
  звук обрезан до 91.25 с с fade-out 0.4 с. Наезд камеры исходника 924–1007 — маска держится.
- Правки распознавания (сверено Whisper): «Receive, verify, complete…», «bank **or** Telegram passwords»,
  «stop the affected **activity**», «Now, security. Never give…». «verification cards» — обе модели слышат «cards», оставлено.
- Проверка маски: неон в маске ≤ 74 px/кадр (контровой свет), скачков площади нет; готовый файл — неон 0 px,
  структура фона вне ведущего 0 px.

```
FPS=24 python3 tools/lesson1_blackbg/matte.py rvm_resnet50_fp32.onnx src.mov alpha.mkv 0.25 204,367,609,826,1067,1255,1483,1702,1943,2178
python3 tools/lesson1_blackbg/render.py src.mov alpha.mkv projects/lesson4/words.json video_only.mp4 --fps 24 --cut 0,0 \
    --end 2178 --maxframe 2189 --shots 204,367,609,826,1067,1255,1483,1702,1943,2178 --fonts fonts \
    --logo assets/ganesha_pay_wordmark_noir.png --static --label "LESSON 4" --qa alpha_final.mkv
```
