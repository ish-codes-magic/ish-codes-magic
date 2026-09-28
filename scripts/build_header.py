"""Builds assets/header.svg: an animated Python REPL that "loads" me like a
Hugging Face model and asks what I do.

Edit LINES / SHARDS / ANSWER below, then run:  python scripts/build_header.py

Only SMIL animations are used, so the SVG animates inside a GitHub <img>
(no scripts, no web fonts, no external requests). Every text row gets an
explicit textLength so layout is identical whichever monospace font the
viewer's OS falls back to.
"""

from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets" / "header.svg"

W = 880
FONT = 14
CHAR = FONT * 0.6          # advance width we lay the text out at
LINE = 25                  # row height
PAD_X = 28
TOP = 64                   # baseline of first row (below the title bar)

C = {
    "bg": "#0d1117", "bar": "#161b22", "border": "#30363d",
    "dim": "#8b949e", "text": "#e6edf3", "kw": "#ff7b72", "fn": "#d2a8ff",
    "str": "#a5d6ff", "ok": "#3fb950", "track": "#21262d",
}

TYPE_SPEED = 0.035         # seconds per typed character
STREAM_SPEED = 0.07        # seconds per streamed "token" (word)

SHARDS = ["DESY", "CERN", "IISER Pune", "Coriolis", "Hashkraft"]
ANSWER = [
    "'Founding Engineer & AI Lead @ Storefox.ai. I build LLM pipelines that turn",
    " noisy real-world audio into insight, obsess over evals, and care a lot about",
    " making AI safe and reliable.'",
]


def spans(parts):
    """[(text, colour), ...] -> (tspans xml, plain length)."""
    xml = "".join(f'<tspan fill="{C[c]}">{escape(t)}</tspan>' for t, c in parts)
    return xml, sum(len(t) for t, _ in parts)


class Svg:
    def __init__(self):
        self.defs, self.body, self.row, self.t = [], [], 0, 0.4

    def y(self):
        return TOP + self.row * LINE

    def _clip(self, cid, y, stops, begin, dur, full):
        """A clipPath rect whose width steps through `stops` (typing/streaming)."""
        stops = [0] + [v + 2 for v in stops] + [full]
        values = ";".join(f"{v:.1f}" for v in stops)
        self.defs.append(
            f'<clipPath id="{cid}"><rect x="{PAD_X - 2}" y="{y - FONT - 2}" height="{LINE}" width="0">'
            f'<animate attributeName="width" values="{values}" calcMode="discrete" '
            f'begin="{begin:.2f}s" dur="{dur:.2f}s" fill="freeze"/></rect></clipPath>'
        )

    def text(self, parts, *, mode, cid):
        """mode: 'type' (char by char) or 'stream' (word by word)."""
        xml, n = spans(parts)
        y = self.y()
        plain = "".join(t for t, _ in parts)
        if mode == "type":
            dur = max(n * TYPE_SPEED, 0.2)
            stops = [(i + 1) * CHAR for i in range(n)]
        else:
            ends = [i for i, ch in enumerate(plain) if ch == " "] + [n]
            dur = max(len(ends) * STREAM_SPEED, 0.2)
            stops = [e * CHAR for e in ends]
        self._clip(cid, y, stops, self.t, dur, W)
        self.body.append(
            f'<text x="{PAD_X}" y="{y}" textLength="{n * CHAR:.1f}" clip-path="url(#{cid})">{xml}</text>'
        )
        self.t += dur
        self.row += 1

    def pause(self, s):
        self.t += s


def build():
    s = Svg()
    P = (">>> ", "dim")

    s.text([P, ("from", "kw"), (" transformers ", "text"), ("import", "kw"), (" AutoModel", "text")],
           mode="type", cid="l1")
    s.pause(0.35)
    s.text([P, ("ishita = AutoModel.", "text"), ("from_pretrained", "fn"), ("(", "text"),
            ('"ish-codes-magic/ishita-pal"', "str"), (")", "text")], mode="type", cid="l2")
    s.pause(0.3)

    # progress bar: fills one shard at a time, shard names light up in sync
    y = s.y()
    label = "Loading checkpoint shards: "
    s.body.append(f'<text x="{PAD_X}" y="{y}" fill="{C["dim"]}" textLength="{len(label) * CHAR:.1f}" '
                  f'opacity="0">{label}<set attributeName="opacity" to="1" begin="{s.t:.2f}s" fill="freeze"/></text>')
    bx, bw, bh = PAD_X + len(label) * CHAR + 4, 220, 10
    step = 0.45
    fills = ";".join(f"{bw * i / len(SHARDS):.1f}" for i in range(len(SHARDS) + 1))
    s.body.append(f'<rect x="{bx:.1f}" y="{y - 10}" width="{bw}" height="{bh}" rx="2" fill="{C["track"]}"/>')
    s.body.append(
        f'<rect x="{bx:.1f}" y="{y - 10}" height="{bh}" rx="2" width="0" fill="{C["ok"]}">'
        f'<animate attributeName="width" values="{fills}" calcMode="discrete" begin="{s.t:.2f}s" '
        f'dur="{step * (len(SHARDS) + 1):.2f}s" fill="freeze"/></rect>'
    )
    for i in range(len(SHARDS) + 1):
        cnt = f"{i}/{len(SHARDS)}"
        start = s.t + step * i
        end = f'<set attributeName="opacity" to="0" begin="{start + step:.2f}s" fill="freeze"/>' if i < len(SHARDS) else ""
        s.body.append(
            f'<text x="{bx + bw + 12:.1f}" y="{y}" fill="{C["text"]}" opacity="0" textLength="{len(cnt) * CHAR:.1f}">{cnt}'
            f'<set attributeName="opacity" to="1" begin="{start:.2f}s" fill="freeze"/>{end}</text>'
        )
    s.row += 1

    # shard names as a comment row, each lighting up with its bar segment
    y = s.y()
    x = PAD_X
    head = "# shards: "
    s.body.append(f'<text x="{x}" y="{y}" fill="{C["dim"]}" textLength="{len(head) * CHAR:.1f}" opacity="0">{head}'
                  f'<set attributeName="opacity" to="1" begin="{s.t:.2f}s" fill="freeze"/></text>')
    x += len(head) * CHAR
    for i, name in enumerate(SHARDS):
        seg = name + ("  ·  " if i < len(SHARDS) - 1 else "")
        at = s.t + step * (i + 1)
        s.body.append(
            f'<text x="{x:.1f}" y="{y}" textLength="{len(seg) * CHAR:.1f}" fill="{C["dim"]}" opacity="0">'
            f'{escape(seg)}<set attributeName="opacity" to="0.3" begin="{s.t:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="1" begin="{at:.2f}s" fill="freeze"/>'
            f'<set attributeName="fill" to="{C["ok"]}" begin="{at:.2f}s" fill="freeze"/></text>'
        )
        x += len(seg) * CHAR
    s.row += 1
    s.t += step * (len(SHARDS) + 1)
    s.pause(0.3)

    s.text([P, ("ishita.", "text"), ("generate", "fn"), ("(", "text"), ('"What do you do?"', "str"), (")", "text")],
           mode="type", cid="l3")
    s.pause(0.4)
    for i, line in enumerate(ANSWER):
        s.text([(line, "str")], mode="stream", cid=f"a{i}")

    # final prompt with a blinking cursor
    y = s.y()
    s.body.append(f'<text x="{PAD_X}" y="{y}" fill="{C["dim"]}" textLength="{4 * CHAR:.1f}" opacity="0">&gt;&gt;&gt; '
                  f'<set attributeName="opacity" to="1" begin="{s.t:.2f}s" fill="freeze"/></text>')
    s.body.append(
        f'<rect x="{PAD_X + 4 * CHAR:.1f}" y="{y - FONT + 2}" width="{CHAR:.1f}" height="{FONT + 2}" fill="{C["text"]}" opacity="0">'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" '
        f'begin="{s.t:.2f}s" repeatCount="indefinite"/></rect>'
    )

    H = y + 28
    dots = "".join(f'<circle cx="{22 + i * 20}" cy="18" r="6" fill="{c}"/>'
                   for i, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]))
    title = "~/ish-codes-magic  —  python3"
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" xml:space="preserve" role="img" aria-labelledby="t d">
<title id="t">ishita-pal</title>
<desc id="d">A Python REPL loads ish-codes-magic/ishita-pal with transformers. Checkpoint shards: {", ".join(SHARDS)}. ishita.generate("What do you do?") returns: {escape(" ".join(a.strip() for a in ANSWER))}</desc>
<defs>{"".join(s.defs)}</defs>
<style>text{{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono","DejaVu Sans Mono",monospace;font-size:{FONT}px;white-space:pre}}</style>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="{C["bg"]}" stroke="{C["border"]}"/>
<path d="M0.5 36 V10.5 a10 10 0 0 1 10 -10 H{W - 10.5} a10 10 0 0 1 10 10 V36 Z" fill="{C["bar"]}"/>
<line x1="0.5" y1="36" x2="{W - 0.5}" y2="36" stroke="{C["border"]}"/>
{dots}
<text x="{W / 2}" y="22.5" text-anchor="middle" fill="{C["dim"]}" style="font-size:12px">{escape(title)}</text>
{chr(10).join(s.body)}
</svg>
"""
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT} ({len(svg):,} bytes, animation ends at {s.t:.1f}s)")


if __name__ == "__main__":
    build()
