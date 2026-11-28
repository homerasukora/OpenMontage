# virus_robots — VIRUS2027 "signal" renderer (9:16)

Генерирует вертикальное видео 1080×1920 кодом: 3D-сцена (three.js) → ASCII-дизер цифрами → чистый слой линий
(сетка пола, wireframe-сферы) → HUD (заголовки, трекинг-боксы, метки) → аналоговый/CRT проход
(RGB-сдвиг, сканлайны, зерно, виньетка, glitch-всплеск на склейках).

Стиль: референсы (белые/чёрные 3D-сцены с цифровым дизером) + VIRUS2027 Web Styleguide:
`#090806` / `#e8e3db` / сигнальный `#FF531F`, Barlow Condensed 800 (заголовки), IBM Plex Mono (метки).

## Файлы
- `web/main.js` — движок: рендер-таргеты, ASCII- и CRT-шейдеры, робот-фабрика, HUD-хелперы, хром кадра.
- `web/shots.js` — сцены (шоты): 3D-объекты, камера, тайминг, HUD каждого шота.
- `render.mjs` — headless Chromium (Playwright) + ffmpeg.
- `assets/v_mark_from_video.png` — V-знак, вырезанный из прошлого ролика (временно, нужен оригинальный SVG).
- `fonts/` — Barlow Condensed, IBM Plex Mono, Inter (OFL).

## Установка
```bash
cd tools/virus_robots
bash setup.sh            # three.js + модель робота Xbot.glb (three.js examples, Mixamo)
```

## Рендер
```bash
NODE_PATH=$(npm root -g) node render.mjs stills /path/out 2.5,7,11.5   # кадры по таймкодам
NODE_PATH=$(npm root -g) node render.mjs video  /path/out.mp4 30        # всё видео
NODE_PATH=$(npm root -g) node render.mjs video  /path/part.mp4 30 4.6 9.2  # отрезок
```
Рендер программный (SwiftShader): ~1–2 с на кадр в облаке.

## Настройки, которые чаще всего крутить
- размер ASCII-ячейки: `CELL` в `main.js` (сейчас 9×14 px);
- доля «тона» под цифрами: `mixTone` у шота (0 — только цифры, 1 — без цифр);
- сила glitch на склейках: блок `// 5. CRT` в `renderAt`;
- хром кадра (верхние метки, прогресс, V-знак): функция `chrome()`.
