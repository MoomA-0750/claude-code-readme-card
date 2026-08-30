# claude-code-readme-card

Generate a Claude Code welcome-screen-style animated SVG card for your GitHub
profile README. No dependencies — pure Python stdlib, outputs a single
self-contained SVG (animation is plain CSS embedded in the file, so it
animates correctly even as a plain markdown image).

## Example

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./card-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./card-light.svg">
  <img alt="Claude Code card" src="./card-light.svg">
</picture>

## Usage

```bash
python3 generate_card.py \
  --name "YourName" \
  --org "Personal" \
  --prompt "Explain this codebase to me" \
  --whatsnew "Added PreModelSwitch/PostModelSwitch hook events" \
             "Added live streaming of subagent tool calls" \
             "Added a spend limit bar to /usage" \
  --theme both \
  --out card.svg
```

`--theme both` writes `card-light.svg` and `card-dark.svg`.

### Light / dark switching

GitHub honours `<picture>` with `prefers-color-scheme` inside a README, so a
single embed can follow the reader's theme. Note that markdown image syntax
(`![...](...)`) cannot do this — you need the HTML form:

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./card-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./card-light.svg">
  <img alt="Claude Code card" src="./card-light.svg">
</picture>
```

If you only want one theme, generate with `--theme light` (or `dark`) and embed
it the plain way:

```markdown
![claude code](./card.svg)
```

### Options

| Flag | Default | Description |
| --- | --- | --- |
| `--name` | `Guest` | Shown in "Welcome back {name}!" (truncated if long) |
| `--org` | `Personal` | Shown in the org/account line |
| `--model` | `Sonnet 5` | Model name shown in the status lines |
| `--cwd` | `~/project` | Path shown under the welcome message |
| `--prompt` | `Let's build something today` | Text in the prompt box (truncated if long) |
| `--thinking-word` | `Pondering` | Word shown next to the animated spinner |
| `--theme` | `light` | `light`, `dark`, or `both` |
| `--whatsnew` | 3 example lines | Up to 3 "What's new" bullet lines (each truncated if long) |
| `--out` | `card.svg` | Output file path |

## What animates

All animation is CSS `@keyframes` embedded inside the SVG's own `<style>`,
so it plays even when the SVG is loaded as a plain `<img>`:

- Blinking cursor in the prompt box
- Rotating asterisk + "thinking" status line, mimicking Claude Code's
  in-progress indicator. The asterisk is drawn as vector spokes rather than a
  text glyph so it spins exactly in place — a font glyph's ink centre drifts
  from its em box (and the font differs per viewer), which makes it wobble.
- The mascot idly bobs and occasionally blinks

## Customising the mascot

The mascot is a pixel grid in `generate_card.py` — edit `MASCOT_PIXELS` to
reshape it. Each character is one pixel: `#` body, `S` shaded body, `O` eye,
`.` transparent. The renderer sizes and centres itself to whatever grid you
give it, so rows and columns can be added freely.

> The mascot here is an original pixel-art approximation drawn to match the
> look of the terminal welcome screen, not Anthropic's actual artwork.
