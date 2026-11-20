#!/usr/bin/env python3
"""
CAR-BTI 自動検証ハーネス（Antigravity用）
GitHubへ公開する前に必ず実行し、全項目PASSを確認します。
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARS = ["coupe","supercar","open","sedan","vip_minivan","utility_van","wagon","crocan","urban_suv","compact","truck_work"]
BGS = ["highway","city","nature","touge","garage"]
TYPES = ["FCSR","FCSL","FCIR","FCIL","FOSR","FOSL","FOIR","FOIL","ACSR","ACSL","ACIR","ACIL","AOSR","AOSL","AOIR","AOIL"]

errors = []

# 1. Config check
cfg_path = os.path.join(ROOT, "site_config.json")
if not os.path.exists(cfg_path):
    errors.append("site_config.json がありません")
    site_url = ""
else:
    with open(cfg_path, "r", encoding="utf-8") as f:
        site_url = json.load(f).get("site_url", "").strip().rstrip("/")
    if not site_url.startswith("https://") or "YOUR-GITHUB-ID" in site_url:
        errors.append(f"site_config.json の site_url が未設定です: {site_url}")

# 2. All 55 car illustrations check
missing_imgs = []
for c in CARS:
    for b in BGS:
        p = os.path.join(ROOT, "images", f"{c}_{b}.jpg")
        if not os.path.exists(p) or os.path.getsize(p) < 10000:
            missing_imgs.append(f"images/{c}_{b}.jpg")
if missing_imgs:
    errors.append(f"不足・破損している車両画像が {len(missing_imgs)} 枚あります: {missing_imgs[:5]}")

# 3. Root assets check
for fn in ["index.html", "ogp.jpg", "favicon.svg", "apple-touch-icon.png", "icon-512.png", "manifest.json"]:
    if not os.path.exists(os.path.join(ROOT, fn)):
        errors.append(f"必須ファイル不足: {fn}")

# 4. index.html content & OGP URL check
idx_path = os.path.join(ROOT, "index.html")
if os.path.exists(idx_path):
    with open(idx_path, "r", encoding="utf-8") as f:
        html = f.read()
    if 'content="./ogp.jpg"' in html:
        errors.append("index.html の og:image が相対パス(./ogp.jpg)のままです。scripts/build_ogp.py を実行してください。")
    if "&url=${encodeURIComponent(shareUrl)}" not in html:
        errors.append("index.html の Xシェア関数にシェアURLが組み込まれていません。scripts/build_ogp.py を実行してください。")
    stray_os = re.findall(r'(?<![FA])OS(?![RL])', html)
    if stray_os:
        errors.append(f"禁止表記 'OS' が残っています: {len(stray_os)} 箇所")

# 5. 16-type OGP images & share HTML pages check
for t in TYPES:
    ogp_p = os.path.join(ROOT, "ogp", f"{t}.jpg")
    sh_p = os.path.join(ROOT, "share", f"{t}.html")
    if not os.path.exists(ogp_p) or os.path.getsize(ogp_p) < 10000:
        errors.append(f"タイプ別OGP画像不足: ogp/{t}.jpg")
    if not os.path.exists(sh_p):
        errors.append(f"タイプ別シェアページ不足: share/{t}.html")
    else:
        with open(sh_p, "r", encoding="utf-8") as f:
            sh = f.read()
        if f'content="{site_url}/ogp/{t}.jpg"' not in sh:
            errors.append(f"share/{t}.html の og:image が完全URLになっていません")

if errors:
    print("=== HARNESS VERIFICATION FAILED ===")
    for e in errors:
        print(" [NG]", e)
    sys.exit(1)
else:
    print("=== HARNESS VERIFICATION PASSED (ALL CHECKS OK) ===")
    print(" - 55/55 car illustrations verified")
    print(" - 16/16 type OGP images & share HTML pages verified")
    print(" - index.html absolute OGP URL & X share URL verified")
    sys.exit(0)
