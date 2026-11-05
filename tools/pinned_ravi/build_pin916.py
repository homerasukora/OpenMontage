s=open('dash_render_169.py').read()
head=s[:s.index('# ---------- screen panel ----------')]
a=head.index('SC = json.load('); b=head.index('WORDS = json.load(')
head=head[:a]+head[b:]
head=head.replace('WORDS = json.load(open(f"{D}/words.json")); LT = json.load(open(f"{D}/vo.json"))["lines"]',
 'WORDS = json.load(open(f"{D}/words.json")); LT = json.load(open(f"{D}/vo.json"))["lines"]; DUR = A["dur"]; CUTS = A["cuts"]')
assert 'W, H, FPS = 1920, 1080, 25' in head; head=head.replace('W, H, FPS = 1920, 1080, 25','W, H, FPS = 1080, 1920, 25')
subs=s[s.index('# ---------- subtitles ----------'):s.index('# ---------- compose ----------')]
subs=subs[:subs.index('GREEN = {')]+'GREEN = {"arnold", "koipay", "guest", "traders", "ravi", "rickshaw", "$500", "step", "volume", "full-time", "₹2", "lakh", "month", "respect", "steady", "daily", "rates", "3%", "1%", "payin", "payout", "dashboard", "requests", "history", "commission", "support", "24/7", "telegram", "ready", "start", "today", "links"}\n'+subs[subs.index('chunks, cur = []'):]
assert 'SUB_Y = 985' in subs; subs=subs.replace('SUB_Y = 985','SUB_Y = 1560')
assert 'len(cur) == 3 or len(" ".join(x["w"] for x in cur)) >= 15' in subs
subs=subs.replace('len(cur) == 3 or len(" ".join(x["w"] for x in cur)) >= 15','len(cur) == 3 or len(" ".join(x["w"] for x in cur)) >= 14')
body=open('pin916_scenes.py').read()
open('pin916_render.py','w').write(head+body.split('#@@SUBS@@')[0]+subs+body.split('#@@SUBS@@')[1])
