# Lesson 1 — хинди-версия (Ganesha Pay Noir, 16:9, 56.7 с)

Картинка, маска, склейка и оформление — из Lesson 1 v4 (`projects/lesson1/EDIT.md`). Заменены звук, субтитры и подпись.

## Перевод (`script_hi.txt`)
Разговорный хинди; термины, которые трейдеры говорят по-английски (platform, transaction, merchant, payout, volume),
записаны деванагари. Осознанные решения:
- «a percentage» → «उसका एक परसेंटेज» (не «एक प्रतिशत» — слышится как «1 %»);
- «make sure» → «पक्का करते हैं»; «When an approved payout appears» → «अप्रूव्ड पेआउट आने पर»;
- «Next, we'll learn…» → «आगे सीखेंगे कि…» (разговорное, без «हम» — короче для тайминга).
Субтитры (`subs_hi.txt`) = текст озвучки слово в слово, разбиты вручную по смыслу (`|`).

## Озвучка
- ElevenLabs (голос Prashant, eleven_v4) сгенерирован, но хост выдачи файлов закрыт сетью окружения → не использован.
- Локально: **Piper** `hi_IN-rohan-medium` (rhasspy/piper; модель из релизов k2-fsa/sherpa-onnx `tts-models`),
  пакет `piper-tts`. Сравнивались: AI4Bharat Indic-TTS FastPitch+HiFiGAN (hi, male), Piper pratham, Piper rohan —
  по разборчивости (Whisper medium, CER по тексту): rohan 0.18, pratham 0.23, AI4Bharat 0.27 → rohan.
- `fit_tts.py`: каждая фраза синтезируется отдельно, темп (length_scale 0.90…0.78) подбирается, чтобы фраза влезла
  в окно английской. `dub.py`: фраза ставится на место английской (может начаться до 0.3 с раньше), доп. ускорение
  ≤ ×1.06 (сильнее — смазываются английские слова), перехлёсты уходят в паузы; loudnorm −16 LUFS.
  Речь заканчивается в 56.35 с при длине видео 56.7 с.
- Озвучка закадровая: губы ведущего под английскую речь.

## Оформление
- Подпись «पाठ 1» — Noto Serif Devanagari SemiBold, золото (брендбук: Noto Serif Devanagari для заголовков на хинди).
- Субтитры — Noto Sans Devanagari SemiBold 56 px, шампань, мягкая тень; текст рисуется строкой целиком
  (по буквам ломаются связки и огласовки).

## Сборка
```
python3 tools/lesson1_blackbg/fit_tts.py hi_IN-rohan-medium.onnx projects/lesson1_hi/script_hi.txt clips/
python3 tools/lesson1_blackbg/dub.py clips projects/lesson1_hi/script_hi.txt dub.wav subs.json projects/lesson1_hi/subs_hi.txt
python3 tools/lesson1_blackbg/render.py src.mov alpha.mkv words.json video_only.mp4 --cut 1645,1691 --end 1747 \
    --shots 302,547,815,1026,1266,1448 --fonts fonts --logo assets/ganesha_pay_wordmark_noir.png --static \
    --label "पाठ 1" --label-font NotoSerifDeva:SemiBold --sub-font NotoSansDeva:SemiBold --subs subs.json --qa alpha_final.mkv
# mux video_only.mp4 + dub.wav
```
