s=open('dash_render_169.py').read()
head=s[:s.index('# ---------- screen panel ----------')]
a=head.index('SC = json.load('); b=head.index('WORDS = json.load(')
head=head[:a]+head[b:]
head=head.replace('WORDS = json.load(open(f"{D}/words.json")); LT = json.load(open(f"{D}/vo.json"))["lines"]',
 'WORDS = json.load(open(f"{D}/words.json")); LT = json.load(open(f"{D}/vo.json"))["lines"]; DUR = A["dur"]; CUTS = A["cuts"]')
subs=s[s.index('# ---------- subtitles ----------'):s.index('# ---------- compose ----------')]
subs=subs[:subs.index('GREEN = {')]+'GREEN = {"usdt", "binance", "p2p", "processing", "differently", "merchant", "marketplace", "spread", "1%", "₹1", "lakh", "₹1,000", "risks", "frozen", "platform", "koipay", "koipay\'s", "payin", "upi", "sms", "forwarder", "automatically", "anti-fraud", "callback", "commission", "dashboard", "payout", "3%", "₹3,000", "payins", "payouts", "completed", "guaranteed", "routing", "limits", "manager", "telegram", "24/7", "@koipayp2p2bot", "description", "onboarding", "accounts", "funds", "hours"}\n'+subs[subs.index('chunks, cur = []'):]
body=open('bin_scenes.py').read()
open('bin_render.py','w').write(head+body.split('#@@SUBS@@')[0]+subs+body.split('#@@SUBS@@')[1])
