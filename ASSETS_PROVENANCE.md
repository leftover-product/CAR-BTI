# CAR-BTI アセット権利・商標配慮台帳（Assets Provenance）

本ファイルは CAR-BTI（車好き16タイプ診断）で使用している画像・フォント・コード・名称の権利関係および商標配慮方針を記録した台帳です。

## 1. 車両イラスト（`images/*.jpg` 計65点：13車種 × 5背景）
- **性質**：すべて実在車両・写真・他社著作物の転載ではなく、CAR-BTI 用に新規生成した**架空のオリジナル車両イラスト**（1280×720px JPEG）。
- **既存11系統（55点）**：`coupe`, `supercar`, `open`, `sedan`, `vip_minivan`, `utility_van`, `wagon`, `crocan`, `urban_suv`, `compact`, `truck_work`（各5背景 `highway`, `city`, `nature`, `touge`, `garage`）。
- **v5追加2系統（10点）**：
  - `kei_*`（5点）：2026-11-26 生成。丸目LED・ツートン軽クロスオーバー（実在エンブレム・ナンバー文字・透かしなし）。
  - `classic_*`（5点）：2026-11-26 生成。70s-80s調オリジナル2ドアハードトップ（実在エンブレム・ナンバー文字・透かしなし）。
- **生成ツール・確認**：Antigravity `image-generator` によりプロンプトベースで生成し、全点目視にて実在ロゴ・透かし混入がないことを確認済み。

## 2. OGPシェアカード画像（`ogp.jpg` + `ogp/*.jpg` 計241点）
- **生成方法**：`scripts/build_ogp.py` および macOS 標準 CoreGraphics / AppKit レンダラー `scripts/render_ogp.swift` により上記65点のオリジナルイラストと静的テキストを合成して毎回生成。
- **使用フォント**：macOS システム搭載ヒラギノ角ゴシック（OGP静止画像書き出し用途）、および Web 表示用 Google Fonts（`Noto Sans JP`, `Rajdhani`：SIL Open Font License）。

## 3. 商標・名称配慮ポリシー
- サービス名・本文・メタタグにおいて第三者登録商標との混同を避けるため、特定自動車モデル名・企業ブランド名・レース商標等は一般名称（例：「オープンカー」「軽自動車」「国際レース」等）へ統一しています。
- 登録商標の最終確認（J-PlatPat等による「CAR-BTI」区分の先行商標確認）および独立ドメイン運用方針は事業オーナー確認事項として管理します。
