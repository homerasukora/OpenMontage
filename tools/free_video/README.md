# free-video

CLI для генерации видео через движок **Open Generative AI** (github.com/anil-matcha/open-generative-ai).
Репозиторий — веб-студия; сама генерация идёт на api.muapi.ai (оплата за каждую генерацию, нужен ключ MuAPI).
Локальные движки репозитория (sd.cpp, Wan2GP) требуют видеокарту — в облачной сессии её нет.

Ключ: переменная `MUAPI_API_KEY` в настройках окружения (или Network secret для `api.muapi.ai`).
Каталог моделей `models.json` выгружен из `packages/studio/src/models.js` (t2v 127, i2v 211, v2v 92, lipsync 17, t2i 94, i2i 98).

```bash
free-video models --kind lipsync              # список моделей и их параметров
free-video models --kind i2v --search wan
free-video t2v     --model seedance-pro-t2v --prompt "..." --aspect-ratio 9:16 --duration 5 --resolution 1080p -o out.mp4
free-video i2v     --model wan3.0-image-to-video --image photo.png --prompt "..." --resolution 1080p -o out.mp4
free-video lipsync --model ltx-2.3-lipsync --image face.png --audio voice.mp3 --prompt "..." --resolution 1080p -o out.mp4
free-video result  REQUEST_ID -o out.mp4       # дозабрать готовую задачу
```
`--dry-run` печатает запрос без отправки (кредиты не тратятся). `--set key=value` — любые доп. параметры модели.
Обновить каталог: `node dump_models.mjs <repo>/packages/studio/src/models.js > models.json`.
