"""Rebuild equalizer_dark.svg / equalizer_light.svg from the public GitHub contribution calendar."""
import datetime
import math
import re
import urllib.request

USER = "alblopnov"
W = 1043
T = {
    "dark": dict(bg="#0d1117", off="#21262d", head="#f0883e", val="#c9d1d9", dim="#6e7681", g="#58a6ff", a="#7ee787", m="#f0883e"),
    "light": dict(bg="#ffffff", off="#eaeef2", head="#bc4c00", val="#24292f", dim="#8c959f", g="#0969da", a="#1a7f37", m="#bc4c00"),
}


def fetch():
    req = urllib.request.Request(f"https://github.com/users/{USER}/contributions", headers={"User-Agent": "profile-equalizer"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8")


def weekly(html):
    cells = {}
    for d, r, c in re.findall(r'data-date="([^"]+)" id="contribution-day-component-(\d+)-(\d+)"', html):
        cells[f"{r}-{c}"] = (d, int(c))
    cnt = {}
    for fid, txt in re.findall(r'<tool-tip[^>]*for="contribution-day-component-([\d-]+)"[^>]*>([^<]*)</tool-tip>', html):
        m = re.match(r"(\d+) contribution", txt)
        cnt[fid] = int(m.group(1)) if m else 0
    weeks, wdate = {}, {}
    for k, (d, c) in cells.items():
        weeks[c] = weeks.get(c, 0) + cnt.get(k, 0)
        wdate.setdefault(c, d)
    order = sorted(weeks)
    if not order:
        raise SystemExit("No contribution data found; leaving files untouched.")
    return [weeks[c] for c in order], [wdate[c] for c in order]


def build(name, t, vals, dates):
    H, N, gap = 226, len(vals), 4
    bw = (W - 56 - gap * (N - 1)) / N
    seg, sh, sg = 10, 10, 3
    base = H - 46
    h = lambda s: s * (sh + sg)
    mx = max(vals) or 1
    lev = [0 if v == 0 else max(1, round(seg * math.sqrt(v / mx))) for v in vals]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Consolas,Menlo,monospace" font-size="11"><defs><linearGradient id="g" gradientUnits="userSpaceOnUse" x1="0" y1="{base}" x2="0" y2="{base-h(seg)}"><stop offset="0" stop-color="{t["g"]}"/><stop offset=".6" stop-color="{t["a"]}"/><stop offset="1" stop-color="{t["m"]}"/></linearGradient>']
    for i, L in enumerate(lev):
        x = 28 + i * (bw + gap)
        d = 0.8 + (i * 37 % 7) * 0.17
        pk, ks = (1.4, [0.3, 1.4, 0.6, 1.1, 0.3]) if L == 0 else (L, [L * .55, L, L * .75, L * .95, L * .55])
        vh = ";".join(f"{h(k):.0f}" for k in ks)
        vy = ";".join(f"{base-h(k):.0f}" for k in ks)
        o.append(f'<clipPath id="c{i}"><rect x="{x:.1f}" width="{bw:.1f}" y="{base-h(pk)}" height="{h(pk)}"><animate attributeName="height" values="{vh}" dur="{d:.2f}s" repeatCount="indefinite"/><animate attributeName="y" values="{vy}" dur="{d:.2f}s" repeatCount="indefinite"/></rect></clipPath>')
    o.append(f'</defs><rect width="100%" height="100%" rx="12" fill="{t["bg"]}"/>')
    o.append(f'<text x="28" y="22" fill="{t["head"]}" font-weight="bold">NOW PLAYING</text><text x="{W-28}" y="22" text-anchor="end" fill="{t["val"]}">{sum(vals)} public contributions in the last year</text>')
    last_m = None
    for i in range(N):
        x = 28 + i * (bw + gap)
        op = 1 if lev[i] else 0.45
        for s_ in range(seg):
            y = base - (s_ + 1) * (sh + sg) + sg
            o.append(f'<rect x="{x:.1f}" y="{y}" width="{bw:.1f}" height="{sh}" rx="1.5" fill="{t["off"]}"/>')
        for s_ in range(seg):
            y = base - (s_ + 1) * (sh + sg) + sg
            o.append(f'<rect x="{x:.1f}" y="{y}" width="{bw:.1f}" height="{sh}" rx="1.5" fill="url(#g)" opacity="{op}" clip-path="url(#c{i})"/>')
        m = dates[i][5:7]
        if m != last_m:
            o.append(f'<text x="{x:.1f}" y="{base+16}" fill="{t["dim"]}">{datetime.date(2000, int(m), 1).strftime("%b")}</text>')
            last_m = m
    o.append(f'<text x="28" y="{H-8}" fill="{t["dim"]}">each column = 1 week  ·  taller and hotter = more commits, PRs and reviews</text></svg>')
    with open(f"equalizer_{name}.svg", "w", encoding="utf-8") as f:
        f.write("".join(o))


if __name__ == "__main__":
    vals, dates = weekly(fetch())
    for n, t in T.items():
        build(n, t, vals, dates)
    print(f"{sum(vals)} contributions over {len(vals)} weeks")
