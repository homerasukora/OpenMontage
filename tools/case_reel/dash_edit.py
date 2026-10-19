"""Edit decision list for the KoiPay dashboard ad: VO-timed scenes mapped to source ranges, crops and blur boxes."""
import json, sys

D = sys.argv[1]                      # project dir with words.json / vo.json
WORDS = json.load(open(f"{D}/words.json")); VO = json.load(open(f"{D}/vo.json")); LT = VO["lines"]
END = round(VO["dur"] + 3.6, 2)      # hold the CTA

def cue(word, line, n=0):
    hits = [w for w in WORDS if w["line"] == line and w["w"].lower().strip(".,?!:").startswith(word.lower())]
    return hits[n]["s"]

LOGO = [395, 0, 485, 62]             # SURFGATE logo (top-left of the app header)

# crop = [x, y, w, h] in source pixels; keyframes interpolate start -> end over the (sub)scene
S = [
    dict(name="hook", s=0.0, e=LT[1][0]),
    dict(name="intro", s=LT[1][0], e=LT[2][0], src=(0.5, 4.5), crops=[[395, 0, 1120, 1080], [395, 20, 1120, 1050]],
         head="KoiPay Trader Dashboard"),
    dict(name="home", s=LT[2][0], e=LT[3][0], src=(0.5, 8.5), crops=[[395, 50, 1120, 600], [395, 480, 1120, 600]],
         head="Home", callout=("Today · 7D · 30D · Custom", cue("today", 2))),
    dict(name="sahil", s=LT[3][0], e=LT[4][0]),
    dict(name="accounts", s=LT[4][0], e=cue("set", 4) - 0.1, src=(84.0, 95.0), crops=[[395, 140, 1120, 900], [860, 260, 640, 514]],
         head="Bank accounts", callout=("On / off in one tap", cue("switch", 4)),
         blur=[[400, 315, 1330, 470], [400, 665, 1330, 820]]),
    dict(name="limits", s=cue("set", 4) - 0.1, e=LT[5][0], src=(104.0, 116.0), crops=[[640, 170, 640, 760], [660, 380, 560, 665]],
         head="Limits per account", callout=("Daily · Monthly · Count · Amount", cue("daily", 4) + 0.3)),
    dict(name="forwarder", s=LT[5][0], e=LT[6][0], src=(170.6, 177.0), crops=[[620, 230, 680, 620], [640, 260, 640, 584]],
         head="SMS Forwarder", callout=("Auto-confirm from bank SMS", cue("confirmed", 5))),
    dict(name="payins", s=LT[6][0], e=LT[7][0], src=(243.6, 247.6), crops=[[395, 60, 1120, 900], [395, 170, 760, 611]],
         head="PayIns", callout=("Receipt inside the request", cue("receipt", 6)),
         blur=[[1150, 360, 1505, 445], [1150, 675, 1505, 760], [1150, 990, 1505, 1075]]),
    dict(name="payouts", s=LT[7][0], e=LT[8][0], src=(272.2, 277.2), crops=[[395, 60, 1120, 840], [395, 120, 960, 720]],
         head="Payouts", callout=("Most overdue first", cue("overdue", 7)),
         blur=[[405, 425, 720, 462], [1030, 488, 1320, 528], [405, 890, 720, 928], [1030, 952, 1320, 992]]),
    dict(name="settle", s=LT[8][0], e=LT[9][0], src=(308.6, 312.6), crops=[[600, 230, 720, 620], [620, 260, 680, 586]],
         head="Settlement", callout=("Rate shown before you confirm", cue("rate", 8))),
    dict(name="report", s=LT[9][0], e=cue("filter", 9) - 0.1, src=(318.0, 330.0), crops=[[395, 70, 1120, 900], [395, 250, 800, 643]],
         head="Reports", callout=("Earning on every operation", cue("earning", 9))),
    dict(name="filters", s=cue("filter", 9) - 0.1, e=LT[10][0], src=(336.0, 340.0), crops=[[650, 120, 600, 800], [650, 120, 600, 800]],
         head="Filters · Export", callout=("UTR · Bank · Date", cue("utr", 9))),
    dict(name="score", s=LT[10][0], e=cue("shows", 10) - 0.1, src=(355.0, 361.0), crops=[[395, 100, 1120, 680], [395, 100, 1120, 680]],
         head="Trader score"),
    dict(name="improve", s=cue("shows", 10) - 0.1, e=LT[11][0], src=(374.5, 378.5), crops=[[740, 270, 440, 540], [740, 270, 440, 540]],
         head="Trader score", callout=("How to improve", cue("improve", 10) - 0.3)),
    dict(name="team", s=LT[11][0], e=LT[12][0], src=(396.0, 402.0), crops=[[740, 190, 440, 720], [740, 190, 440, 720]],
         head="Team access", callout=("Can't see your earnings", cue("can't", 11))),
    dict(name="cta", s=LT[12][0], e=END),
]
for sc in S:
    sc["s"] = round(sc["s"], 3); sc["e"] = round(sc["e"], 3)
    sc.setdefault("blur", []); sc["blur"] = sc["blur"] + [LOGO]

if __name__ == "__main__":
    json.dump(dict(scenes=S, end=END), open(f"{D}/scenes.json", "w"), indent=1)
    src = sys.argv[2]; fc, cat = [], ""
    for k, sc in enumerate(S):
        d = sc["e"] - sc["s"]
        if "src" in sc:
            a, b = sc["src"]
            fc.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,setpts={d / (b - a):.5f}*PTS,fps=25,trim=duration={d:.3f},setpts=PTS-STARTPTS[v{k}];")
        else:
            fc.append(f"color=black:s=1920x1080:r=25:d={d:.3f}[v{k}];")
        cat += f"[v{k}]"
    fc.append(f"{cat}concat=n={len(S)}:v=1:a=0[v]")
    print(json.dumps(["-i", src, "-filter_complex", "".join(fc), "-map", "[v]"]))
    for sc in S: print(f"{sc['name']:10s} {sc['s']:6.2f} {sc['e']:6.2f}", file=sys.stderr)
