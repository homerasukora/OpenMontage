s=open('dash_render_169.py').read()
head=s[:s.index('# ---------- screen panel ----------')]
a=head.index('SC = json.load('); b=head.index('WORDS = json.load(')
head=head[:a]+head[b:]
head=head.replace('WORDS = json.load(open(f"{D}/words.json")); LT = json.load(open(f"{D}/vo.json"))["lines"]',
 'WORDS = json.load(open(f"{D}/words.json")); LT = json.load(open(f"{D}/vo.json"))["lines"]; DUR = A["dur"]; CUTS = A["cuts"]')
subs=s[s.index('# ---------- subtitles ----------'):s.index('# ---------- compose ----------')]
subs=subs[:subs.index('GREEN = {')]+'GREEN = {"rickshaw", "delhi", "₹14,000", "rides", "siya", "koipay", "ravi", "evening", "$500", "week", "full-time", "₹1", "lakh", "promise", "possible", "₹2–4", "volume", "p2p", "upi", "commission", "payin", "payout", "incoming", "outgoing", "free", "training", "description", "experienced", "manager", "onboarding", "links"}\n'+subs[subs.index('chunks, cur = []'):]
body=open('siya_scenes.py').read()
open('siya_render.py','w').write(head+body.split('#@@SUBS@@')[0]+subs+body.split('#@@SUBS@@')[1])
