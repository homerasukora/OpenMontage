# Ganesha Pay Academy — анонс уроков (16:9, 17.6 с)

`tools/academy_promo/academy_promo.py` (картинка) + `promo_mix.py` (звук) → `renders/ganesha_pay_academy_promo_16x9.mp4`, −15.7 LUFS.

| Время | Сцена |
|---|---|
| 0:00–1.9 | Хук без голоса: «New to P2P processing?» (Cormorant, P2P золотом) |
| 1.9–3.7 | Вордмарк + «Learn it for free · GANESHA PAY ACADEMY» |
| 3.7–4.7 | Флэш 4 уроков по 0.25 с (наезд + золотая вспышка, тик на каждый кадр) |
| 4.7–14.3 | Сплит-экран English \| Hindi: активная половина цветная, с плашкой ENGLISH / HINDI · हिन्दी и крупной фразой; вторая — стоп-кадр, ч/б, размытие. Lesson 2 «So why is the training free?» → «तो ट्रेनिंग फ़्री क्यों है?»; Lesson 4 «Accuracy is extremely important.» → «एक्यूरेसी बेहद ज़रूरी है». Внизу появляются Free · Short lessons · ~20 min a day |
| 14.3–17.6 | CTA: вордмарк, «Learn to work online», Free · Short lessons · ~20 min a day · English & Hindi, золотая кнопка «Link below ↓» |

Звук: спокойный бэд (`bed.py`) с приглушением под голос, свуши на переходах, голос — фрагменты уроков (EN — оригинал, HI — дубляж).
Источники: финальные рендеры уроков EN (Lesson 1 v4, Lesson 2 static, Lesson 3, Lesson 4) и HI (Lesson 1–4).

## v2 (26.11) — под телефон, 23.75 с, −14.3 LUFS → `renders/ganesha_pay_academy_promo_16x9_v2.mp4`
`tools/academy_promo/academy_promo2.py` + `promo_mix2.py`. Всё на весь кадр, крупные подписи (Manrope 64, золото на ключевых словах),
мелкие субтитры самих уроков закрыты затемнением снизу.
1. 0–2.2 Хук: «New to P2P processing?» + «GANESHA PAY ACADEMY · FREE».
2. Триггерные фразы на весь экран (медленный наезд): L1 «What does a processing manager actually do?» →
   L1 «For every successfully processed transaction, you receive a percentage» → L3 «You don't need a complicated professional setup» →
   L4 «Speed, accuracy, security and discipline make a reliable processing manager».
3. Один языковой момент: экран пополам, каждая половина на всю высоту. L2 «So why is the training free?» слева (ENGLISH),
   затем левая замирает в ч/б с размытием, справа хинди «तो ट्रेनिंग फ़्री क्यों है?» (हिन्दी · HINDI).
4. CTA: вордмарк, «Learn to work online», Free · Short lessons · ~20 min a day · English & Hindi, «Link below ↓».

## v3 (26.11) — 16:9 и 9:16, 24 с, −14.5 LUFS
`tools/academy_promo/academy_promo3.py [--vertical]` + `promo_mix3.py` →
`renders/ganesha_pay_academy_promo_16x9_v3.mp4`, `renders/ganesha_pay_academy_promo_9x16_v3.mp4`.
- В начале — выпускная шапочка (mortarboard) в линейной графике бренда: падает сверху с лёгким отскоком, по ней пробегает блик.
- Наша музыка полностью уходит, пока говорит урок (в уроках своя музыка), и возвращается в паузах, на хуке и CTA.
- 9:16: ведущий на весь кадр (вертикальный кроп), вордмарк сверху, подписи крупно в центре-низу (выше зоны интерфейса);
  языковой момент — экран сверху/снизу (English сверху, हिन्दी снизу); CTA с плашками в два ряда.
