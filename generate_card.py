#!/usr/bin/env python3
"""Generate a Claude Code-welcome-screen-style animated SVG for a GitHub profile README.

Usage:
    python3 generate_card.py \
        --name "MoomA" \
        --prompt "Let's build something today" \
        --whatsnew "Added PreModelSwitch/PostModelSwitch hook events" \
                   "Added live streaming of subagent tool calls" \
                   "Added a spend limit bar to /usage" \
        --out card.svg

The output SVG is self-contained (fonts fall back to generic monospace,
animation is plain CSS inside <style>) so it animates correctly even when
embedded via a plain markdown image in a GitHub README:

    ![claude code](./card.svg)
"""
import argparse
from xml.sax.saxutils import escape

FONT_STACK = "SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"

COLORS = {
    "bg": "#fffdfb",
    "border": "#d97757",
    "text": "#2d2a26",
    "muted": "#7a746c",
    "accent": "#d97757",
    "mascot_body": "#f2a29a",
    "mascot_dark": "#d9847a",
    "mascot_eye": "#241f1c",
    "prompt_border": "#d9d3ca",
    "cursor": "#2d2a26",
}

CHAR_W_RATIO = 0.60  # monospace advance width as a fraction of font-size


def char_width(font_size: float) -> float:
    return font_size * CHAR_W_RATIO


def truncate(s: str, max_chars: int) -> str:
    return s if len(s) <= max_chars else s[: max_chars - 1].rstrip() + "…"


def build_svg(args) -> str:
    W, H = 900, 390
    box_x, box_y, box_w, box_h = 20, 20, W - 40, 220
    mid_x = box_x + box_w * 0.48
    col_r_x = mid_x + 24

    name = escape(truncate(args.name, 18))
    org = escape(args.org)
    model = escape(args.model)
    cwd = escape(args.cwd)
    prompt = escape(truncate(args.prompt, 78))
    thinking_word = escape(args.thinking_word)

    whatsnew_lines = [[truncate(item, 50)] for item in args.whatsnew[:3]]

    # --- prompt cursor position (monospace width estimate) ---
    prompt_font_size = 15
    prompt_x = 44
    cursor_x = prompt_x + 18 + len(prompt) * char_width(prompt_font_size)

    # --- mascot pixel-art (simple axolotl/pig blob) ---
    mascot_cx = box_x + (mid_x - box_x) / 2
    mascot_cy = box_y + 128

    whatsnew_svg = ""
    y = 168
    for lines in whatsnew_lines:
        for i, line in enumerate(lines):
            prefix = "• " if i == 0 else "  "
            whatsnew_svg += (
                f'<text x="{col_r_x}" y="{y}" font-size="12.5" fill="{COLORS["muted"]}">'
                f'{escape(prefix)}{line}</text>\n'
            )
            y += 17

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT_STACK}">
  <style>
    text {{ font-family: {FONT_STACK}; }}
    .cursor {{ animation: blink 1s step-end infinite; }}
    @keyframes blink {{ 0%, 50% {{ opacity: 1; }} 50.01%, 100% {{ opacity: 0; }} }}

    .spinner {{ transform-origin: 46px 372px; animation: spin 1.1s linear infinite; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}

    .mascot-bob {{ animation: bob 2.4s ease-in-out infinite; }}
    @keyframes bob {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-4px); }} }}

    .mascot-blink {{ animation: eyeblink 4.5s ease-in-out infinite; }}
    @keyframes eyeblink {{ 0%, 92%, 100% {{ opacity: 0; }} 94%, 96% {{ opacity: 1; }} }}
  </style>

  <rect x="0" y="0" width="{W}" height="{H}" fill="{COLORS['bg']}"/>

  <!-- main welcome box -->
  <rect x="{box_x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="8" fill="#ffffff" stroke="{COLORS['border']}" stroke-width="2"/>
  <text x="{box_x + 20}" y="{box_y + 30}" font-size="15" font-weight="bold" fill="{COLORS['accent']}">Claude Code</text>
  <line x1="{box_x}" y1="{box_y + 44}" x2="{box_x + box_w}" y2="{box_y + 44}" stroke="{COLORS['border']}" stroke-width="1"/>
  <line x1="{mid_x}" y1="{box_y + 44}" x2="{mid_x}" y2="{box_y + box_h}" stroke="{COLORS['border']}" stroke-width="1"/>

  <!-- left column -->
  <text x="{box_x + (mid_x - box_x) / 2}" y="{box_y + 78}" font-size="19" font-weight="bold" fill="{COLORS['text']}" text-anchor="middle">Welcome back {name}!</text>

  <g class="mascot-bob">
    <g transform="translate({mascot_cx}, {mascot_cy})">
      <rect x="-30" y="-16" width="60" height="38" rx="18" fill="{COLORS['mascot_body']}"/>
      <rect x="-24" y="18" width="10" height="14" rx="3" fill="{COLORS['mascot_dark']}"/>
      <rect x="14" y="18" width="10" height="14" rx="3" fill="{COLORS['mascot_dark']}"/>
      <rect x="-16" y="-6" width="7" height="11" rx="1.5" fill="{COLORS['mascot_eye']}"/>
      <rect x="9" y="-6" width="7" height="11" rx="1.5" fill="{COLORS['mascot_eye']}"/>
      <rect class="mascot-blink" x="-16" y="-6" width="7" height="11" rx="1.5" fill="{COLORS['mascot_body']}"/>
      <rect class="mascot-blink" x="9" y="-6" width="7" height="11" rx="1.5" fill="{COLORS['mascot_body']}"/>
    </g>
  </g>

  <text x="{box_x + (mid_x - box_x) / 2}" y="{box_y + 178}" font-size="12" fill="{COLORS['muted']}" text-anchor="middle">{model} · Claude Pro · {org}</text>
  <text x="{box_x + (mid_x - box_x) / 2}" y="{box_y + 196}" font-size="12" fill="{COLORS['muted']}" text-anchor="middle">{cwd}</text>

  <!-- right column -->
  <text x="{col_r_x}" y="{box_y + 68}" font-size="13" font-weight="bold" fill="{COLORS['accent']}">Tips for getting started</text>
  <text x="{col_r_x}" y="{box_y + 86}" font-size="12.5" fill="{COLORS['muted']}">Run /init to create a CLAUDE.md file</text>
  <text x="{col_r_x}" y="{box_y + 103}" font-size="12.5" fill="{COLORS['muted']}">with instructions for Claude</text>

  <text x="{col_r_x}" y="{box_y + 132}" font-size="13" font-weight="bold" fill="{COLORS['accent']}">What's new</text>
  {whatsnew_svg}

  <!-- status line -->
  <rect x="20" y="{box_y + box_h + 24}" width="3" height="16" fill="{COLORS['border']}"/>
  <text x="34" y="{box_y + box_h + 37}" font-size="12.5" fill="{COLORS['muted']}">Using {model} · /model</text>

  <!-- prompt box -->
  <rect x="20" y="{box_y + box_h + 56}" width="{box_w}" height="46" rx="6" fill="#ffffff" stroke="{COLORS['prompt_border']}" stroke-width="1.5"/>
  <text x="{prompt_x}" y="{box_y + box_h + 85}" font-size="{prompt_font_size}" fill="{COLORS['text']}">›&#160;{prompt}</text>
  <rect class="cursor" x="{cursor_x:.1f}" y="{box_y + box_h + 71}" width="9" height="18" fill="{COLORS['cursor']}"/>

  <!-- thinking indicator -->
  <text class="spinner" x="40" y="{box_y + box_h + 122}" font-size="16" fill="{COLORS['accent']}" text-anchor="middle">✻</text>
  <text x="58" y="{box_y + box_h + 122}" font-size="12.5" fill="{COLORS['accent']}">{thinking_word}… <tspan fill="{COLORS['muted']}">(esc to interrupt)</tspan></text>
</svg>
"""
    return svg


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--name", default="Guest")
    p.add_argument("--org", default="Personal")
    p.add_argument("--model", default="Sonnet 5")
    p.add_argument("--cwd", default="~/project")
    p.add_argument("--prompt", default="Let's build something today")
    p.add_argument("--thinking-word", dest="thinking_word", default="Pondering")
    p.add_argument("--whatsnew", nargs="+", default=[
        "Added PreModelSwitch/PostModelSwitch hook events",
        "Added live streaming of subagent tool calls",
        "Added a spend limit bar to /usage",
    ])
    p.add_argument("--out", default="card.svg")
    args = p.parse_args()

    svg = build_svg(args)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
