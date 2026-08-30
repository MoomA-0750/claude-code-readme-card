# claude-code-readme-card

Generate a Claude Code welcome-screen-style animated SVG card for your GitHub
profile README. No dependencies — pure Python stdlib, outputs a single
self-contained SVG (animation is plain CSS embedded in the file, so it
animates correctly even as a plain markdown image).

## Example

![claude code card](./card.svg)

## Usage

```bash
python3 generate_card.py \
  --name "YourName" \
  --org "Personal" \
  --prompt "Explain this codebase to me" \
  --whatsnew "Added PreModelSwitch/PostModelSwitch hook events" \
             "Added live streaming of subagent tool calls" \
             "Added a spend limit bar to /usage" \
  --out card.svg
```

Then embed it in your profile README:

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
| `--whatsnew` | 3 example lines | Up to 3 "What's new" bullet lines (each truncated if long) |
| `--out` | `card.svg` | Output file path |

## What animates

All animation is CSS `@keyframes` embedded inside the SVG's own `<style>`,
so it plays even when the SVG is loaded as a plain `<img>`:

- Blinking cursor in the prompt box
- Rotating spinner + "thinking" status line (mimics Claude Code's in-progress indicator)
- The mascot idly bobs and occasionally blinks
