#!/usr/bin/env python3
"""Generate a Claude Code-style animated SVG card for a GitHub profile README.

Usage:
    python3 generate_card.py \
        --name "MoomA" \
        --prompt "Explain this codebase to me" \
        --response-file about.md \
        --theme both \
        --out card.svg

The output SVG is self-contained (fonts fall back to generic monospace,
animation is plain CSS inside <style>) so it animates correctly even when
embedded as a plain image in a GitHub README.

With --theme both, two files are written (card-light.svg / card-dark.svg)
so a README can switch them by color scheme via <picture>.
"""
import argparse
import os
import unicodedata
from xml.sax.saxutils import escape

FONT_STACK = "SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"

THEMES = {
    "light": {
        "bg": "#ffffff",
        "border": "#d97757",
        "text": "#2d2a26",
        "muted": "#7a746c",
        "accent": "#d97757",
        "code": "#b3541e",
        "cursor": "#2d2a26",
    },
    "dark": {
        "bg": "#0d1117",
        "border": "#d97757",
        "text": "#e6edf3",
        "muted": "#8b949e",
        "accent": "#e0885f",
        "code": "#ffa657",
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
    "..############..",
    "..############..",
    "..##O######O##..",
    "..##O######O##..",
    "################",
    "################",
    "..############..",
    "..############..",
    "...#.#....#.#...",
    "...#.#....#.#...",
]

PIXEL_SIZE = 6

CHAR_W_RATIO = 0.60  # monospace advance width as a fraction of font-size


# ---------------------------------------------------------------- text metrics

def char_cols(ch: str) -> int:
    """Terminal column count for one character: CJK/full-width take two."""
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def text_cols(s: str) -> int:
    return sum(char_cols(c) for c in s)


def col_px(font_size: float) -> float:
    return font_size * CHAR_W_RATIO


def truncate(s: str, max_cols: int) -> str:
    """Truncate by display columns, not by len() — CJK is twice as wide."""
    if text_cols(s) <= max_cols:
        return s
    out, used = "", 0
    for ch in s:
        w = char_cols(ch)
        if used + w > max_cols - 1:
            break
        out += ch
        used += w
    return out.rstrip() + "…"


def tokenize(text: str):
    """Split into break-friendly tokens: words keep trailing spaces, CJK breaks
    per character (as terminals wrap it)."""
    out, buf = [], ""
    for ch in text:
        if char_cols(ch) == 2:
            if buf:
                out.append(buf)
                buf = ""
            out.append(ch)
        elif ch == " ":
            buf += ch
            out.append(buf)
            buf = ""
        else:
            buf += ch
    if buf:
        out.append(buf)
    return out


# ------------------------------------------------------------- markdown subset

def parse_inline(s: str):
    """Parse **bold** and `code` into (text, style) segments."""
    segs, buf, i = [], "", 0
    while i < len(s):
        if s.startswith("**", i):
            j = s.find("**", i + 2)
            if j != -1:
                if buf:
                    segs.append((buf, "normal"))
                    buf = ""
                segs.append((s[i + 2:j], "bold"))
                i = j + 2
                continue
        if s[i] == "`":
            j = s.find("`", i + 1)
            if j != -1:
                if buf:
                    segs.append((buf, "normal"))
                    buf = ""
                segs.append((s[i + 1:j], "code"))
                i = j + 1
                continue
        buf += s[i]
        i += 1
    if buf:
        segs.append((buf, "normal"))
    return segs


def flow(segs, max_cols: int, hang: int = 0):
    """Wrap styled segments into lines of at most max_cols columns.

    hang indents continuation lines, so bullet text lines up under itself.
    """
    lines, cur, col = [], [], 0
    for text, style in segs:
        for tok in tokenize(text):
            w = text_cols(tok)
            if col + w > max_cols and cur:
                lines.append(cur)
                cur, col = [], hang
                if tok.strip() == "":
                    continue
            cur.append((tok, style))
            col += w
    lines.append(cur)
    return lines


def emit_line(x, y, tokens, C, font_size, base_fill, indent_cols=0):
    """One <text> element, with every glyph pinned to a terminal column.

    SVG `x` accepts one coordinate per character, so each glyph is placed on
    the grid instead of being advanced by the font. Without this the layout
    drifts: a viewer's Latin and CJK fallback fonts rarely agree that a
    full-width glyph is exactly twice a half-width one, which would leave the
    cursor floating away from the end of the text.
    """
    merged = []
    for t, s in tokens:
        if merged and merged[-1][1] == s:
            merged[-1][0] += t
        else:
            merged.append([t, s])

    cw = col_px(font_size)
    positions, col = [], indent_cols
    parts = []
    for t, s in merged:
        if not t:
            continue
        for ch in t:
            positions.append(x + col * cw)
            col += char_cols(ch)
        if s == "bold":
            parts.append(f'<tspan font-weight="bold" fill="{C["text"]}">{escape(t)}</tspan>')
        elif s == "code":
            parts.append(f'<tspan fill="{C["code"]}">{escape(t)}</tspan>')
        else:
            parts.append(f'<tspan fill="{base_fill}">{escape(t)}</tspan>')

    if not positions:
        return ""

    xs = " ".join(f"{p:.1f}" for p in positions)
    return (f'<text x="{xs}" y="{y:.1f}" font-size="{font_size}" '
            f'xml:space="preserve">{"".join(parts)}</text>')


def render_markdown(md: str, x: float, y: float, max_cols: int, C,
                    font_size: float = 13, line_h: float = 18):
    """Render a small markdown subset. Returns (svg, height_used)."""
    parts, cur_y = [], y
    in_code_block = False

    for raw in md.splitlines():
        line = raw.rstrip()

        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            cur_y += line_h * 0.35
            continue

        if in_code_block:
            parts.append(emit_line(x, cur_y, [(line, "code")], C, font_size,
                                   C["code"], indent_cols=2))
            cur_y += line_h
            continue

        if not line.strip():
            cur_y += line_h * 0.55
            continue

        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            body = line[level:].strip()
            size = font_size + (2 if level == 1 else 1)
            for ln in flow(parse_inline(body), max_cols):
                parts.append(f'<text x="{x:.1f}" y="{cur_y:.1f}" font-size="{size}" '
                             f'font-weight="bold" fill="{C["accent"]}" '
                             f'xml:space="preserve">'
                             f'{escape("".join(t for t, _ in ln))}</text>')
                cur_y += line_h
            continue

        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if stripped.startswith(("- ", "* ")):
            body = stripped[2:]
            base = indent + 2
            lines = flow(parse_inline(body), max_cols - base, hang=0)
            for i, ln in enumerate(lines):
                if i == 0:
                    ln = [("• ", "normal")] + ln
                    parts.append(emit_line(x, cur_y, ln, C, font_size,
                                           C["text"], indent_cols=indent))
                else:
                    parts.append(emit_line(x, cur_y, ln, C, font_size,
                                           C["text"], indent_cols=base))
                cur_y += line_h
            continue

        for ln in flow(parse_inline(stripped), max_cols - indent):
            parts.append(emit_line(x, cur_y, ln, C, font_size, C["text"],
                                   indent_cols=indent))
            cur_y += line_h

    return "\n  ".join(parts), cur_y - y


# ------------------------------------------------------------------- mascot

def render_mascot(cx: float, cy: float) -> str:
    rows = len(MASCOT_PIXELS)
    cols = max(len(r) for r in MASCOT_PIXELS)
    origin_x = cx - (cols * PIXEL_SIZE) / 2
    origin_y = cy - (rows * PIXEL_SIZE) / 2

    fills = {"#": MASCOT["body"], "S": MASCOT["shade"], "O": MASCOT["eye"]}
    body, lids = [], []
    for r, row in enumerate(MASCOT_PIXELS):
        for c, ch in enumerate(row):
            fill = fills.get(ch)
            if not fill:
                continue
            x = origin_x + c * PIXEL_SIZE
            y = origin_y + r * PIXEL_SIZE
            # +0.5 overlap avoids hairline seams between adjacent pixels.
            body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{PIXEL_SIZE + 0.5}" '
                        f'height="{PIXEL_SIZE + 0.5}" fill="{fill}"/>')
            if ch == "O":
                lids.append(f'<rect class="mascot-blink" x="{x:.1f}" y="{y:.1f}" '
                            f'width="{PIXEL_SIZE + 0.5}" height="{PIXEL_SIZE + 0.5}" '
                            f'fill="{MASCOT["body"]}"/>')
    return "\n      ".join(body + lids)


def mascot_height() -> float:
    return len(MASCOT_PIXELS) * PIXEL_SIZE


# ------------------------------------------------------------------ spinner

def spinner_shapes(C) -> str:
    """The CLI cycles · + * ✻ — opening then closing. Drawn as vector spokes
    rather than glyphs so it is identical for every viewer's font."""
    a = C["accent"]

    def spokes(n, length, width):
        return "".join(
            f'<line x1="0" y1="0" x2="0" y2="-{length}" stroke="{a}" '
            f'stroke-width="{width}" stroke-linecap="round" '
            f'transform="rotate({i * (360 / n):.0f})"/>'
            for i in range(n)
        )

    return (
        f'<g class="sp-dot"><circle cx="0" cy="0" r="1.8" fill="{a}"/></g>\n      '
        f'<g class="sp-plus">{spokes(4, 4.2, 2.0)}</g>\n      '
        f'<g class="sp-star">{spokes(6, 5.6, 2.0)}</g>\n      '
        f'<g class="sp-sparkle">{spokes(6, 7.4, 2.2)}</g>'
    )


# -------------------------------------------------------------------- build

def build_svg(args, theme_name: str) -> str:
    C = THEMES[theme_name]

    W = 900
    M = 16
    box_x, box_y, box_w = M, M + 6, W - 2 * M
    split_x = box_x + box_w * 0.44          # vertical divider between columns
    left_cx = box_x + (split_x - box_x) / 2
    right_x = split_x + 18
    right_w = box_x + box_w - 18 - right_x

    small = 12.5
    right_cols = int(right_w / col_px(small))

    # Left column has to hold its own text; sizing off the real column width
    # keeps a long org name or path from spilling outside the box.
    left_w = split_x - box_x - 20
    left_cols_sm = int(left_w / col_px(11.5))
    left_cols_lg = int(left_w / col_px(17))

    name = truncate(args.name, max(4, left_cols_lg - len("Welcome back !")))
    meta = truncate(f"{args.model} · {args.plan} · {args.org}", left_cols_sm)
    cwd = truncate(args.cwd, left_cols_sm)

    # ---- right column: Tips, a rule, then What's new -----------------------
    right_parts = []
    ry = box_y + 30
    right_parts.append(f'<text x="{right_x:.1f}" y="{ry:.1f}" font-size="{small}" '
                       f'font-weight="bold" fill="{C["accent"]}">Tips for getting started</text>')
    ry += 18
    for tip in args.tips[:3]:
        for ln in flow(parse_inline(tip), right_cols):
            right_parts.append(emit_line(right_x, ry, ln, C, small, C["muted"]))
            ry += 16
    ry += 6
    rule_y = ry
    right_parts.append(f'<line x1="{right_x:.1f}" y1="{rule_y:.1f}" '
                       f'x2="{right_x + right_w:.1f}" y2="{rule_y:.1f}" '
                       f'stroke="{C["border"]}" stroke-width="1" opacity="0.5"/>')
    ry += 20
    right_parts.append(f'<text x="{right_x:.1f}" y="{ry:.1f}" font-size="{small}" '
                       f'font-weight="bold" fill="{C["accent"]}">What\'s new</text>')
    ry += 18
    for item in args.whatsnew[:4]:
        right_parts.append(emit_line(right_x, ry,
                                     parse_inline(truncate(item, right_cols)),
                                     C, small, C["muted"]))
        ry += 16
    right_parts.append(f'<text x="{right_x:.1f}" y="{ry:.1f}" font-size="{small}" '
                       f'fill="{C["muted"]}" font-style="italic">/release-notes for more</text>')
    ry += 10
    right_h = ry - box_y

    # ---- left column: greeting, mascot, model, cwd -------------------------
    left_parts = []
    ly = box_y + 46
    left_parts.append(f'<text x="{left_cx:.1f}" y="{ly:.1f}" font-size="17" '
                      f'font-weight="bold" fill="{C["text"]}" text-anchor="middle">'
                      f'Welcome back {escape(name)}!</text>')
    ly += 26
    mascot_cy = ly + mascot_height() / 2
    left_parts.append(f'<g class="mascot-bob"><g shape-rendering="crispEdges">'
                      f'{render_mascot(left_cx, mascot_cy)}</g></g>')
    ly += mascot_height() + 26
    left_parts.append(f'<text x="{left_cx:.1f}" y="{ly:.1f}" font-size="11.5" '
                      f'fill="{C["muted"]}" text-anchor="middle">{escape(meta)}</text>')
    ly += 16
    left_parts.append(f'<text x="{left_cx:.1f}" y="{ly:.1f}" font-size="11.5" '
                      f'fill="{C["muted"]}" text-anchor="middle">{escape(cwd)}</text>')
    ly += 12
    left_h = ly - box_y

    box_h = max(left_h, right_h) + 10

    # ---- prompt line: "❯ <prompt>", cursor parked after the last glyph -----
    body_x = 30
    prompt_fs = 13.5
    body_cols = int((W - body_x - 24) / col_px(prompt_fs))
    prompt_lines = flow(parse_inline(args.prompt), body_cols - 2, hang=2)

    py = box_y + box_h + 42
    prompt_parts = []
    for i, ln in enumerate(prompt_lines):
        toks = [("❯ ", "normal")] + ln if i == 0 else ln
        prompt_parts.append(emit_line(body_x, py, toks, C, prompt_fs, C["text"],
                                      indent_cols=0 if i == 0 else 2))
        last_y = py
        py += 20
    last_cols = text_cols("".join(t for t, _ in prompt_lines[-1]))
    last_cols += 2  # the "❯ " prefix on the first line, or the hanging indent
    cursor_x = body_x + last_cols * col_px(prompt_fs)

    # ---- response markdown -------------------------------------------------
    resp_svg, resp_h = "", 0
    ry2 = py + 14
    if args.response:
        resp_svg, resp_h = render_markdown(args.response, body_x, ry2,
                                           body_cols, C, font_size=13, line_h=18)

    # ---- thinking indicator ------------------------------------------------
    spin_y = ry2 + resp_h + 26
    spin_x = body_x + 8
    H = spin_y + 34

    status = f'{escape(truncate(args.thinking_word, 20))}… '
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H:.0f}" width="{W}" height="{H:.0f}" font-family="{FONT_STACK}">
  <style>
    text {{ font-family: {FONT_STACK}; }}

    .cursor {{ animation: blink 1s step-end infinite; }}
    @keyframes blink {{ 0%, 50% {{ opacity: 1; }} 50.01%, 100% {{ opacity: 0; }} }}

    /* · → + → * → ✻ → * → + , i.e. it opens then closes */
    .sp-dot, .sp-plus, .sp-star, .sp-sparkle {{ animation-duration: 1s;
      animation-timing-function: step-end; animation-iteration-count: infinite; }}
    .sp-dot {{ animation-name: spd; }}
    .sp-plus {{ animation-name: spp; }}
    .sp-star {{ animation-name: sps; }}
    .sp-sparkle {{ animation-name: spk; }}
    @keyframes spd {{ 0% {{ opacity: 1; }} 16.66% {{ opacity: 0; }} 100% {{ opacity: 0; }} }}
    @keyframes spp {{ 0% {{ opacity: 0; }} 16.66% {{ opacity: 1; }} 33.33% {{ opacity: 0; }}
                      83.33% {{ opacity: 1; }} 100% {{ opacity: 0; }} }}
    @keyframes sps {{ 0% {{ opacity: 0; }} 33.33% {{ opacity: 1; }} 50% {{ opacity: 0; }}
                      66.66% {{ opacity: 1; }} 83.33% {{ opacity: 0; }} 100% {{ opacity: 0; }} }}
    @keyframes spk {{ 0% {{ opacity: 0; }} 50% {{ opacity: 1; }} 66.66% {{ opacity: 0; }}
                      100% {{ opacity: 0; }} }}

    .mascot-bob {{ animation: bob 2.4s ease-in-out infinite; }}
    @keyframes bob {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-4px); }} }}

    .mascot-blink {{ opacity: 0; animation: eyeblink 4.5s ease-in-out infinite; }}
    @keyframes eyeblink {{ 0%, 92%, 100% {{ opacity: 0; }} 94%, 96% {{ opacity: 1; }} }}
  </style>

  <rect x="0" y="0" width="{W}" height="{H:.0f}" fill="{C['bg']}"/>

  <!-- welcome box; the title sits on the top border like the CLI's ╭── Claude Code ──╮ -->
  <rect x="{box_x}" y="{box_y}" width="{box_w}" height="{box_h:.1f}" rx="10"
        fill="none" stroke="{C['border']}" stroke-width="1.5"/>
  <line x1="{split_x:.1f}" y1="{box_y}" x2="{split_x:.1f}" y2="{box_y + box_h:.1f}"
        stroke="{C['border']}" stroke-width="1" opacity="0.5"/>
  <rect x="{box_x + 20}" y="{box_y - 9}" width="{(text_cols(args.title) + 2) * col_px(12.5):.1f}"
        height="18" fill="{C['bg']}"/>
  <text x="{box_x + 28}" y="{box_y + 4}" font-size="12.5" font-weight="bold"
        fill="{C['accent']}">{escape(args.title)}</text>

  {chr(10).join("  " + p for p in left_parts)}

  {chr(10).join("  " + p for p in right_parts)}

  <!-- user prompt line -->
  {chr(10).join("  " + p for p in prompt_parts)}
  <rect class="cursor" x="{cursor_x:.1f}" y="{last_y - 11:.1f}" width="8" height="15" fill="{C['cursor']}"/>

  <!-- assistant response -->
  {resp_svg}

  <!-- thinking indicator -->
  <g transform="translate({spin_x:.1f}, {spin_y:.1f})">
      {spinner_shapes(C)}
  </g>
  <text x="{spin_x + 18:.1f}" y="{spin_y + 5:.1f}" font-size="12.5" fill="{C['accent']}">{status}<tspan fill="{C['muted']}">{escape(args.thinking_suffix)}</tspan></text>
</svg>
"""


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--name", default="Guest")
    p.add_argument("--org", default="Personal")
    p.add_argument("--model", default="Sonnet 5")
    p.add_argument("--plan", default="Claude Pro")
    p.add_argument("--cwd", default="~/project")
    p.add_argument("--title", default="Claude Code",
                   help="text shown on the top border of the box")
    p.add_argument("--prompt", default="Tell me about yourself")
    p.add_argument("--response", default="",
                   help="assistant reply, in a small markdown subset")
    p.add_argument("--response-file", dest="response_file",
                   help="read --response from a file")
    p.add_argument("--thinking-word", dest="thinking_word", default="Forming")
    p.add_argument("--thinking-suffix", dest="thinking_suffix",
                   default="(esc to interrupt)")
    p.add_argument("--theme", choices=["light", "dark", "both"], default="light",
                   help="'both' writes <out>-light.svg and <out>-dark.svg")
    p.add_argument("--tips", nargs="+", default=[
        "Run /init to create a CLAUDE.md file with instructions for Claude",
    ])
    p.add_argument("--whatsnew", nargs="+", default=[
        "Added `PreModelSwitch` and `PostModelSwitch` hook events",
        "Added live streaming of a foreground subagent's tool calls",
        "Added a Spend limit bar to `/usage`",
    ])
    p.add_argument("--out", default="card.svg")
    args = p.parse_args()

    if args.response_file:
        with open(args.response_file, encoding="utf-8") as f:
            args.response = f.read()

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
