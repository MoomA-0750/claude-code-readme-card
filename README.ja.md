# claude-code-readme-card

[English](./README.md) | 日本語

GitHub のプロフィール README に貼る、Claude Code 風のアニメーション SVG カードを生成します。
依存ライブラリはなく Python 標準ライブラリのみで動作し、出力は自己完結した 1 枚の SVG です
（アニメーションはファイル内に埋め込まれた CSS なので、画像として読み込まれても動きます）。

## 例

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./card-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./card-light.svg">
  <img alt="Claude Code card" src="./card-light.svg">
</picture>

## 使い方

まず例のプロフィール本文をコピーして編集します。これが応答として表示される文章で、
自分の内容を書く場所です。`about.md` は gitignore してあるので、あなたのコピーは
リポジトリに入りません。

```bash
cp about.example.md about.md
```

編集したらカードを生成します。

```bash
python3 generate_card.py \
  --name "YourName" \
  --org "your-org" \
  --model "Opus 5" \
  --cwd "~/your-project" \
  --prompt "Tell me about yourself" \
  --response-file about.md \
  --theme both \
  --out card.svg
```

`--theme both` を指定すると `card-light.svg` と `card-dark.svg` の 2 つが出力されます。
上の例のカードは `about.example.md` から生成したもので、対応しているマークダウン記法が
ひととおり含まれています。

### ライト / ダークの切り替え

GitHub は README 内の `<picture>` と `prefers-color-scheme` を解釈するので、1 つの埋め込みで
閲覧者のテーマに追従できます。マークダウンの画像記法（`![...](...)`）ではこれができないため、
HTML の形で書く必要があります。

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./card-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./card-light.svg">
  <img alt="Claude Code card" src="./card-light.svg">
</picture>
```

片方のテーマだけでよければ `--theme light`（または `dark`）で生成して、そのまま貼れます。

```markdown
![claude code](./card.svg)
```

### 応答本文について

`--response`（または `--response-file`）が、自分のプロフィール内容を書く場所です。
アシスタントの返答として、以下のマークダウンのサブセットで描画されます。

| 記法 | 表示 |
| --- | --- |
| `# 見出し` / `## 見出し` | 太字・アクセント色の見出し |
| `- 項目` / `* 項目` | 箇条書き。折り返した行は文字位置に揃います |
| `**太字**` | 太字 |
| `` `コード` `` | コード色のインラインコード |
| ` ``` ` フェンス | 字下げされたコードブロック |
| 空行 | 縦方向の余白 |

長い行は自動で折り返され、日本語などの全角文字はターミナルと同じく 1 文字単位で折り返します。
実際の書き方は `about.example.md` を参照してください。

### オプション

| フラグ | デフォルト | 説明 |
| --- | --- | --- |
| `--name` | `Guest` | 「Welcome back {name}!」に表示される名前 |
| `--org` | `Personal` | アカウント行に表示される組織名 |
| `--model` | `Sonnet 5` | アカウント行のモデル名 |
| `--plan` | `Claude Pro` | アカウント行のプラン名 |
| `--cwd` | `~/project` | グリーティングの下に表示されるパス |
| `--title` | `Claude Code` | ボックス上枠線上に表示されるタイトル |
| `--prompt` | `Tell me about yourself` | `❯` の入力行。折り返し、末尾にカーソルが付きます |
| `--response` | — | 応答本文（マークダウンのサブセット） |
| `--response-file` | — | `--response` をファイルから読み込みます |
| `--tips` | 例が 2 行 | 「Tips for getting started」の行 |
| `--whatsnew` | 例が 3 行 | 「What's new」の行 |
| `--thinking-word` | `Forming` | スピナーの横に出る単語 |
| `--thinking-suffix` | `(esc to interrupt)` | その後ろに続く文字列 |
| `--theme` | `light` | `light` / `dark` / `both` |
| `--out` | `card.svg` | 出力先のパス |

## 動くもの

アニメーションはすべて SVG 内の `<style>` に書かれた CSS `@keyframes` なので、
SVG が単なる `<img>` として読み込まれても再生されます。

- プロンプト文末に付くカーソルの点滅
- スピナーは `·` → `+` → `*` → `✻` → `*` → `+` と、CLI と同じように開いて閉じます。
  文字ではなくベクター図形で描いているため、閲覧者のフォントに関係なく同じ見た目になります。
- マスコットがゆっくり上下し、ときどき瞬きします

## 1 文字ずつ座標を指定している理由

各行のテキストは、フォントに文字送りを任せず、SVG の 1 文字ごとの `x` 指定によって
ターミナルの桁位置に固定しています。閲覧者の環境では、ラテン文字用フォントと日本語用フォントで
「全角＝半角ちょうど 2 倍」が成り立つとは限りません。これをやらないとカーソルが文末から
ずれ、折り返しも崩れます。日本語のプロンプトでは特に目立ちます。

## マスコットのカスタマイズ

マスコットは `generate_card.py` 内のピクセルグリッドです。`MASCOT_PIXELS` を編集すれば
形を変えられます。1 文字が 1 ピクセルで、`#` が本体、`S` が影、`O` が目、`.` が透明です。
与えたグリッドに合わせて自動でサイズ調整と中央寄せをするので、行や列は自由に増やせます。

> このマスコットは、ターミナルのウェルカム画面の見た目に寄せて描いた独自のピクセルアートです。
> Anthropic の実際のアートワークではありません。
