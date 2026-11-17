# Binance P2P vs processing — Ganesha Pay Noir (16:9, 2:01, 25 fps)

Пересборка 2-минутного KoiPay-ролика (эталон `3303997423435676855.mp4`) из чистых исходников в стиле Ganesha Pay.
Фон съёмки не трогали (логотипов в кадре нет).

## Монтажный лист (`edl.json`, итоговая лента — `plan.json`)
| | Источник | Текст |
|---|---|---|
| A | IMG_8203 | Trading USDT on Binance P2P? … Processing works differently. |
| B | эталон 10.95–20.62 | On Binance P2P, you're a merchant… earn the spread. |
| C | эталон 20.62–29.24 | Do the math… If the rate doesn't move against you, |
| D | IMG_8207 | and the risks are yours… bank account frozen. |
| E | эталон 40.10–50.05 | A processing platform removes the marketplace layer… to traders. |
| F | video-1523: 0–0.54 + 1.36–14.15 | Here's a ~~Koi Pay~~ pay-in… confirms the payment automatically. |
| G | IMG_8214 | Anti-fraud… You send an approved outgoing payment. |
| H | IMG_8213 с 1.21 | ~~KoiPay's rates is~~ About 3% on pay-in, 1% on payout… |
| I | IMG_8212 | You earn per completed operation… exact rates. |
| J | IMG_8211 | Your dashboard… support works 24/7. |
| K | video-1525 (6.4 с) | Before you start, discuss… with the manager. |
| L | video-1525 (11 с): 0–1.95 + 5.8–11.0 | Already trading P2P? ~~Apply through at @KoiPayP2P2Bot.~~ The link is in the description… |

- B, C, E — фрагментов не было, взяты из эталона (848×476) по согласованию; показаны как полноэкранная графика,
  ведущий — в кружке (лицо по маске RVM, `headtrack.py`), C — без кружка. Логотип/субтитры/плашки эталона в кадр не попадают.
- Проверка: распознавание итогового звука — упоминаний Koi нет.

## Оформление
Оникс + изумруд, золото — линии/акценты, шампань — текст; заголовки Cormorant, текст/цифры Manrope.
Логотип Noir — слева сверху (на кадре — на ониксовой плашке, как «спокойный участок»). Субтитры 1–2 слова,
ключевые слова золотом, мягкая тень + затемнение низа кадра. Плашки справа, пункты появляются под слова.
Полноэкранные сцены: Marketplace (телефон с записью экрана Binance), spread math, Processing removes / How requests reach you,
Ganesha Pay · base rates, Your dashboard. Финал: «Free P2P training» + золотая кнопка «Link below — in the description» + стрелка ↓.

## Звук
Голос: каждая часть loudnorm −18 LUFS, склейки 12 мс. У эталона есть музыкальная подложка → под весь ролик положен
спокойный bed (`tools/siya/podcast.py`, XT=−10, −31 LUFS), уровень фона в частях эталона и фрагментов совпал.
Итог −14 LUFS.

## К подтверждению
- Ставки «≈3% PayIn / ≈1% PayOut» и пример «₹1 lakh → ₹3,000 / ₹1,000» озвучены в исходниках — для Ganesha Pay
  нужно подтверждение актуальности; на экране есть «Your manager confirms your exact terms».
