# CAR-BTI Antigravity 自動運用ハーネス指示書

## 0. 前提ルール（最重要）
- オーナー（ユーザー）は**非エンジニア**です。
- ユーザーにコードの編集やコマンド入力を求めないでください。すべてのファイル編集・スクリプト実行・検証・GitHubへの反映（`git add` / `commit` / `push`）は、エージェント側で自律実行してください。
- ユーザーへの報告は、専門用語を避けて「何を直したか」「テストに通ったか」「公開URL」だけを簡潔に日本語で伝えてください。

---

## 1. 初回セットアップ手順（最初の1回だけ実行）
ユーザーから「公開URL（例：`https://〇〇.github.io/car-bti/`）」を聞き取り、以下を自動実行する：
1. `site_config.json` の `"site_url"` をその公開URLへ書き換える。
2. ターミナルで `python3 scripts/build_ogp.py` を実行し、全16タイプ別のXカード画像（`ogp/*.jpg`）とシェア専用ページ（`share/*.html`）を生成し、`index.html` のXシェアURLを更新する。
3. ターミナルで `python3 scripts/harness_verify.py` を実行し、`ALL CHECKS OK` を確認する。
4. GitHubリポジトリへ `git add -A && git commit -m "Setup X OGP cards & harness" && git push` を実行し、GitHub Pagesでの公開完了を報告する。

---

## 2. 通常アップデート時の自動ハーネス（毎回の修正で必ず実行）
ユーザーから文言修正・機能追加・デザイン変更の依頼を受けたら、以下のパイプラインを順番に実行する：
1. **実装**：`index.html` 等を修正する（禁止ワード：「車好きOS」「価値観OS」は使わず「車好きタイプ」に統一）。
2. **OGP再生成**：`python3 scripts/build_ogp.py` を実行して16タイプ別カードとメタタグを最新化。
3. **自動検証**：`python3 scripts/harness_verify.py` を実行。1つでも `[NG]` が出たら自動で原因を修正し、`ALL CHECKS OK` になるまで公開しない。
4. **自動公開**：検証通過後、`git add -A && git commit -m "<変更内容の要約>" && git push` を実行してGitHub Pagesへ自動反映する。
5. **完了報告**：変更点と公開URLをユーザーへ簡潔に報告する。
