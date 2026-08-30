#!/usr/bin/env python3
"""Generate a Claude Code-welcome-screen-style animated SVG for a GitHub profile README.

Usage:
    python3 generate_card.py \
        --name "MoomA" \
        --prompt "Let's build something today" \
        --whatsnew "Added PreModelSwitch/PostModelSwitch hook events" \
                   "Added live streaming of subagent tool calls" \
                   "Added a spend limit bar to /usage" \
        --theme both \
        --out card.svg

The output SVG is self-contained (fonts fall back to generic monospace,
animation is plain CSS inside <style>) so it animates correctly even when
embedded via a plain markdown image in a GitHub README.

With --theme both, two files are written (card-light.svg / card-dark.svg)
so a README can switch them by color scheme via <picture>.
"""
import argparse
import os
from xml.sax.saxutils import escape

FONT_STACK = "SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"

THEMES = {
    "light": {
        "bg": "#ffffff",
        "panel": "#fffdfb",
        "border": "#d97757",
        "text": "#2d2a26",
        "muted": "#7a746c",
        "accent": "#d97757",
        "prompt_border": "#d9d3ca",
        "cursor": "#2d2a26",
    },
    "dark": {
        "bg": "#0d1117",
        "panel": "#161b22",
        "border": "#d97757",
        "text": "#e6edf3",
        "muted": "#8b949e",
        "accent": "#e0885f",
        "prompt_border": "#30363d",
        "cursor": "#e6edf3",
    },
}

# Mascot colors stay constant across themes.
MASCOT = {
    "body": "#f2a29a",
    "shade": "#d9847a",
    "eye": "#241f1c",
}

# Pixel-art mascot ("clawd"). Each character is one pixel:
#   '#' body   'S' shaded/darker body   'O' eye   '.' transparent
# Edit this grid to reshape the mascot; the renderer sizes itself to fit.
MASCOT_PIXELS = [
    "...##########...",
    ".##############.",
    "################",
    "################",
    "###OO######OO###",
    "###OO######OO###",
    "###OO######OO###",
    "################",
    "################",
    ".##############.",
    "..SS........SS..",
    "..SS........SS..",
]

PIXEL_SIZE = 6

CHAR_W_RATIO = 0.60  # monospace advance width as a fraction of font-size


def char_width(font_size: float) -> float:
    return font_size * CHAR_W_RATIO


def truncate(s: str, max_chars: int) -> str:
    return s if len(s) <= max_chars else s[: max_chars - 1].rstrip() + "…"


def render_mascot(cx: float, cy: float) -> str:
    """Render the pixel grid as discrete squares, centred on (cx, cy)."""
    rows = len(MASCOT_PIXELS)
    cols = max(len(r) for r in MASCOT_PIXELS)
    origin_x = cx - (cols * PIXEL_SIZE) / 2
    origin_y = cy - (rows * PIXEL_SIZE) / 2

    fills = {"#": MASCOT["body"], "S": MASCOT["shade"], "O": MASCOT["eye"]}
    parts = []
    for r, row in enumerate(MASCOT_PIXELS):
        for c, ch in enumerate(row):
            fill = fills.get(ch)
            if not fill:
                continue
            x = origin_x + c * PIXEL_SIZE
            y = origin_y + r * PIXEL_SIZE
            cls = ' class="eye"' if ch == "O" else ""
            # +0.5 overlap avoids hairline seams between adjacent pixels.
            parts.append(
                f'<rect{cls} x="{x:.1f}" y="{y:.1f}" '
                f'width="{PIXEL_SIZE + 0.5}" height="{PIXEL_SIZE + 0.5}" fill="{fill}"/>'
            )

    # Eyelid pixels: same squares in body colour, faded in briefly to blink.
    lid = []
    for r, row in enumerate(MASCOT_PIXELS):
        for c, ch in enumerate(row):
            if ch != "O":
                continue
            x = origin_x + c * PIXEL_SIZE
            y = origin_y + r * PIXEL_SIZE
            lid.append(
                f'<rect class="mascot-blink" x="{x:.1f}" y="{y:.1f}" '
                f'width="{PIXEL_SIZE + 0.5}" height="{PIXEL_SIZE + 0.5}" fill="{MASCOT["body"]}"/>'
            )

    return "\n      ".join(parts + lid)


def build_svg(args, theme_name: str) -> str:
    C = THEMES[theme_name]

    W, H = 900, 390
    box_x, box_y, box_w, box_h = 20, 20, W - 40, 220
    mid_x = box_x + box_w * 0.48
    col_r_x = mid_x + 24

    name = escape(truncate(args.name, 18))
    org = escape(truncate(args.org, 28))
    model = escape(args.model)
    cwd = escape(truncate(args.cwd, 34))
    prompt = escape(truncate(args.prompt, 78))
    thinking_word = escape(truncate(args.thinking_word, 20))

    whatsnew = [escape(truncate(item, 50)) for item in args.whatsnew[:3]]

    prompt_font_size = 15
    prompt_x = 44
    cursor_x = prompt_x + 18 + len(prompt) * char_width(prompt_font_size)

    mascot_cx = box_x + (mid_x - box_x) / 2
    mascot_cy = box_y + 128
    mascot_svg = render_mascot(mascot_cx, mascot_cy)

    whatsnew_svg = ""
    y = 168
    for line in whatsnew:
        whatsnew_svg += (
            f'<text x="{col_r_x}" y="{y}" font-size="12.5" fill="{C["muted"]}">'
            f'• {line}</text>\n  '
        )
        y += 17

    # Spinner: the outer <g> positions it, the inner <g> only rotates. The
    # asterisk is drawn as vector spokes rather than a text glyph so its centre
    # is exactly (0,0) — a font glyph's ink centre drifts from the em box and
    # makes the spinner wobble, and the font differs per viewer anyway.
    spin_x = 46
    spin_y = box_y + box_h + 117
    spinner_spokes = "\n      ".join(
        f'<line x1="0" y1="0" x2="0" y2="-6.5" stroke="{C["accent"]}" stroke-width="2.2" '
        f'stroke-linecap="round" transform="rotate({i * 60})"/>'
        for i in range(6)
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT_STACK}">
  <style>
    text {{ font-family: {FONT_STACK}; }}

    .cursor {{ animation: blink 1s step-end infinite; }}
    @keyframes blink {{ 0%, 50% {{ opacity: 1; }} 50.01%, 100% {{ opacity: 0; }} }}

    .spinner {{ transform-origin: 0px 0px; animation: spin 1.1s linear infinite; }}
    @keyframes spin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}

    .mascot-bob {{ animation: bob 2.4s ease-in-out infinite; }}
    @keyframes bob {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-4px); }} }}

    .mascot-blink {{ opacity: 0; animation: eyeblink 4.5s ease-in-out infinite; }}
    @keyframes eyeblink {{ 0%, 92%, 100% {{ opacity: 0; }} 94%, 96% {{ opacity: 1; }} }}
  </style>

  <rect x="0" y="0" width="{W}" height="{H}" fill="{C['bg']}"/>

  <!-- main welcome box -->
  <rect x="{box_x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="8" fill="{C['panel']}" stroke="{C['border']}" stroke-width="2"/>
  <text x="{box_x + 20}" y="{box_y + 30}" font-size="15" font-weight="bold" fill="{C['accent']}">Claude Code</text>
  <line x1="{box_x}" y1="{box_y + 44}" x2="{box_x + box_w}" y2="{box_y + 44}" stroke="{C['border']}" stroke-width="1"/>
  <line x1="{mid_x}" y1="{box_y + 44}" x2="{mid_x}" y2="{box_y + box_h}" stroke="{C['border']}" stroke-width="1"/>

  <!-- left column -->
  <text x="{box_x + (mid_x - box_x) / 2}" y="{box_y + 78}" font-size="19" font-weight="bold" fill="{C['text']}" text-anchor="middle">Welcome back {name}!</text>

  <g class="mascot-bob">
    <g shape-rendering="crispEdges">
      {mascot_svg}
    </g>
  </g>

  <text x="{box_x + (mid_x - box_x) / 2}" y="{box_y + 178}" font-size="12" fill="{C['muted']}" text-anchor="middle">{model} · Claude Pro · {org}</text>
  <text x="{box_x + (mid_x - box_x) / 2}" y="{box_y + 196}" font-size="12" fill="{C['muted']}" text-anchor="middle">{cwd}</text>

  <!-- right column -->
  <text x="{col_r_x}" y="{box_y + 68}" font-size="13" font-weight="bold" fill="{C['accent']}">Tips for getting started</text>
  <text x="{col_r_x}" y="{box_y + 86}" font-size="12.5" fill="{C['muted']}">Run /init to create a CLAUDE.md file</text>
  <text x="{col_r_x}" y="{box_y + 103}" font-size="12.5" fill="{C['muted']}">with instructions for Claude</text>

  <text x="{col_r_x}" y="{box_y + 132}" font-size="13" font-weight="bold" fill="{C['accent']}">What's new</text>
  {whatsnew_svg}
  <!-- status line -->
  <rect x="20" y="{box_y + box_h + 24}" width="3" height="16" fill="{C['border']}"/>
  <text x="34" y="{box_y + box_h + 37}" font-size="12.5" fill="{C['muted']}">Using {model} · /model</text>

  <!-- prompt box -->
  <rect x="20" y="{box_y + box_h + 56}" width="{box_w}" height="46" rx="6" fill="{C['panel']}" stroke="{C['prompt_border']}" stroke-width="1.5"/>
  <text x="{prompt_x}" y="{box_y + box_h + 85}" font-size="{prompt_font_size}" fill="{C['text']}">›&#160;{prompt}</text>
  <rect class="cursor" x="{cursor_x:.1f}" y="{box_y + box_h + 71}" width="9" height="18" fill="{C['cursor']}"/>

  <!-- thinking indicator -->
  <g transform="translate({spin_x}, {spin_y})">
    <g class="spinner">
      {spinner_spokes}
    </g>
  </g>
  <text x="62" y="{spin_y + 5}" font-size="12.5" fill="{C['accent']}">{thinking_word}… <tspan fill="{C['muted']}">(esc to interrupt)</tspan></text>
</svg>
"""


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--name", default="Guest")
    p.add_argument("--org", default="Personal")
    p.add_argument("--model", default="Sonnet 5")
    p.add_argument("--cwd", default="~/project")
    p.add_argument("--prompt", default="Let's build something today")
    p.add_argument("--thinking-word", dest="thinking_word", default="Pondering")
    p.add_argument("--theme", choices=["light", "dark", "both"], default="light",
                   help="'both' writes <out>-light.svg and <out>-dark.svg")
    p.add_argument("--whatsnew", nargs="+", default=[
        "Added PreModelSwitch/PostModelSwitch hook events",
        "Added live streaming of subagent tool calls",
        "Added a spend limit bar to /usage",
    ])
    p.add_argument("--out", default="card.svg")
    args = p.parse_args()

    if args.theme == "both":
        stem, ext = os.path.splitext(args.out)
        targets = [("light", f"{stem}-light{ext}"), ("dark", f"{stem}-dark{ext}")]
    else:
        targets = [(args.theme, args.out)]

    for theme_name, path in targets:
        with open(path, "w", encoding="utf-8") as f:
            f.write(build_svg(args, theme_name))
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
