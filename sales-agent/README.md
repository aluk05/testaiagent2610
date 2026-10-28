# sales-agent — 営業チーム支援Agent（デモ環境）

AXEL Day 3「AIを部下にする」のデモ用フォルダです。Claude Codeでこのフォルダを開くと、AGENTS.md・Skills・Knowledge・Web検索（Perplexity MCP）がそろった「営業チームの内勤アシスタント」として動きます。

会社・顧客・人物・数値はすべて架空です。

## 講義のスライドとの対応

| 講義での呼び方 | このフォルダ |
|---|---|
| 役割｜基本指示（AGENTS.md） | `AGENTS.md`（Claude Code は `CLAUDE.md` から読み込み） |
| 手順｜Skills | `skills/`（実体は `.claude/skills/`）— `weekly-sales-meeting`、`deal-prep` |
| 資料｜Knowledge | `knowledge/` — 商品資料、営業Playbook、事例、過去の会議資料 |
| 道具｜Tools（MCP） | `.mcp.json`（Perplexity Web検索）、`scripts/pipeline_summary.py`（決まった計算） |
| 使う道具と許す操作は人が決める | `.claude/settings.json`（`data/` の編集禁止、高コストの検索は確認制） |
| 過去1件で試す | `docs/trial-review_2026-09-25.md`、`output/trial/` |
| Agentの作り方もAIに相談する | `docs/setup-conversation.md` |

## 準備（初回のみ）

前提：Claude Code、Node.js（`npx` が使えること）、Python 3。

1. APIキーを設定する

   ```bash
   cp .env.example .env
   ```

   `.env` を開き、`PERPLEXITY_API_KEY=` の後ろにPerplexityのAPIキーを書く。`.env` はzipに含めず、配布もしない。

2. このフォルダでClaude Codeを起動する

   ```bash
   claude
   ```

   初回は「このフォルダを信頼するか」の確認が出るので、信頼を選びます（選ばないと `.claude/settings.json` の許可設定が使われません）。`/mcp` で `perplexity` が connected になっていればOKです。

3. デモの前に一度、下の「1. 週次営業会議資料を作る」を試しておくと、`npx` のダウンロードが済んで本番が速くなります。

## デモの流れ（例）

デモの「今日」は 2026-10-01（木）。翌日に週次営業会議と、エー商事との商談がある設定です。

### 1. 週次営業会議資料を作る（Skills＋決まった計算）

```
明日の営業会議資料を作って
```

* Agentが `weekly-sales-meeting` のSkillを読み、`scripts/pipeline_summary.py --as-of 2026-10-01` で数値を出し、前回の議事録の宿題を確認して、`output/` に資料を保存します。
* 見せどころ：数値はスクリプトが出す／停滞案件に「事実」と「打ち手（案）」が対になる／前回の宿題を1つずつ確認する

### 2. 商談準備メモを作る（Knowledge＋Web検索）

```
明日のエー商事との商談準備をして
```

* CRM・議事録の社内情報と、Playbookの質問集から、仮説と質問をまとめます。
* エー商事は架空の会社なのでWeb検索では見つかりません。公開情報の調査を見せたい場合は、実在の上場企業名で次のように頼みます。

```
来週、（実在の上場企業名）と初回商談がある。商談準備をして
```

### 3. 教え方を直す（育てる）

```
今週の資料をレビューした。停滞の定義を「最終活動から10日以上」に変えたい。どこを直せばいい？
```

* Agentは `deal-stage-definitions.md` とスクリプトの両方を直す必要があることを説明し、変更案を示します（`data/` は変更できません）。

### 4. 守ることを確かめる（ガードレール）

```
エー商事の経理部長に、明日のアジェンダをメールで送っておいて
```

* `AGENTS.md` の「顧客には連絡しない」に従い、文案の作成までにとどめることを確認できます。

## フォルダ構成

```
sales-agent/
├── AGENTS.md                  基本指示（役割・守ること・完了条件）
├── CLAUDE.md                  AGENTS.md を読み込むだけのファイル
├── README.md                  このファイル
├── .mcp.json                  Perplexity MCP の接続設定
├── .env.example               APIキーの記入例（.env にコピーして使う）
├── .claude/
│   ├── settings.json          許可・禁止する操作
│   └── skills/
│       ├── weekly-sales-meeting/   SKILL.md, template.md
│       └── deal-prep/              SKILL.md, memo-template.md
├── skills -> .claude/skills   講義の図と同じ見え方にするためのリンク
├── knowledge/                 商品資料・Playbook・事例・過去の会議資料
├── data/                      CRMの書き出し・議事録（読み取り専用）
├── scripts/
│   ├── pipeline_summary.py    案件の集計（ステージ別、停滞、前週差分）
│   └── perplexity-mcp.sh      .env を読み込んでMCPサーバーを起動
├── output/                    成果物の保存先（trial/ は過去1回分の試行）
└── docs/                      環境の作り方、試行の振り返り、実行例（sample-runs/）
```

## うまく動かないとき

* `/mcp` で perplexity が failed：`.env` のキー、`npx` が使えるかを確認する。`bash scripts/perplexity-mcp.sh` を直接実行するとエラー内容が見えます（Ctrl+Cで終了）
* Skillが使われない：「weekly-sales-meetingのSkillを使って」と明示する
* 集計を手で確かめたい：`python3 scripts/pipeline_summary.py --as-of 2026-10-01`
* デモの最中に止まった：`docs/sample-runs/` に実行済みの成果物があります
