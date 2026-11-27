#!/usr/bin/env python3
"""
CAR-BTI 自動検証ハーネス（v5.2 ラチェット強化版）
GitHubへ公開する前に必ず実行し、全項目PASSを確認します。
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BGS = ["highway", "city", "nature", "touge", "garage"]
TYPES = [
    "FCSR", "FCSL", "FCIR", "FCIL",
    "FOSR", "FOSL", "FOIR", "FOIL",
    "ACSR", "ACSL", "ACIR", "ACIL",
    "AOSR", "AOSL", "AOIR", "AOIL",
]
FORBIDDEN_TRADEMARKS = [
    "ロードスター", "アルヴェル", "ステップワゴン", "デリカ", "スイスポ", "ヤリス",
    "N-BOX", "ハスラー", "ジムニー", "テスラ", "BYD", "F1", "WRC",
]

errors = []


def x_weight(s):
    w = 0
    for ch in s:
        if ch == "\n":
            w += 1
        elif 0x20 <= ord(ch) <= 0x7E:
            w += 1
        else:
            w += 2
    return w


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

# 2. Root assets & legal/provenance check
for fn in ["index.html", "ogp.jpg", "favicon.svg", "apple-touch-icon.png", "icon-512.png", "manifest.json", "sitemap.xml", "robots.txt", "CNAME", "privacy.html", "terms.html", "ASSETS_PROVENANCE.md"]:
    p = os.path.join(ROOT, fn)
    if not os.path.exists(p):
        errors.append(f"必須ファイル不足: {fn}")
if os.path.exists(os.path.join(ROOT, "ogp.jpg")) and os.path.getsize(os.path.join(ROOT, "ogp.jpg")) < 10000:
    errors.append("ルート ogp.jpg が破損しています")

# 3. Read index.html & extract SSOT catalog
idx_path = os.path.join(ROOT, "index.html")
cars = []
catalog = {}
html = ""
if os.path.exists(idx_path):
    with open(idx_path, "r", encoding="utf-8") as f:
        html = f.read()
    m = re.search(r'<script id="carbti-catalog" type="application/json">\s*(.*?)\s*</script>', html, flags=re.DOTALL)
    if not m:
        errors.append("index.html に #carbti-catalog JSON が見つかりません")
    else:
        catalog = json.loads(m.group(1))
        cars = [c["id"] for c in catalog.get("CARS", [])]

    if f'content="{site_url}/ogp.jpg' not in html:
        errors.append("index.html の og:image が完全URLになっていません")
    if f'const SITE_URL = "{site_url}";' not in html:
        errors.append("index.html の SITE_URL が site_config.json と一致しません")
    if "Q 01 / 28" not in html or "28問" not in html:
        errors.append("index.html の質問数表記(28問)が統一されていません")
    if re.search(r"mbti", html, flags=re.IGNORECASE):
        errors.append("index.html に登録商標表記 'MBTI' が残っています")
    for tm in FORBIDDEN_TRADEMARKS:
        pat = rf"(?<![A-Za-z0-9#]){re.escape(tm)}(?![A-Za-z0-9])" if tm.isascii() else re.escape(tm)
        if re.search(pat, html, flags=re.IGNORECASE if not tm.isascii() else 0):
            errors.append(f"index.html に実在車名・ブランド商標 '{tm}' が残っています")

    for label, content in [("index.html", html), ("manifest.json", open(os.path.join(ROOT, "manifest.json"), encoding="utf-8").read())]:
        stray_os = re.findall(r"(?<![A-Za-z])OS(?![A-Za-z])", content)
        if stray_os:
            errors.append(f"{label} に禁止表記 'OS' が残っています: {len(stray_os)} 箇所")

    scripts = re.findall(r"<script>([\s\S]*?)</script>", html)
    if scripts:
        app_js = max(scripts, key=len)
        js_tmp = "/tmp/carbti_verify_app.js"
        with open(js_tmp, "w", encoding="utf-8") as f:
            f.write(app_js)
        res = subprocess.run(["node", "--check", js_tmp], capture_output=True, text=True)
        if res.returncode != 0:
            errors.append(f"index.html のJS構文エラー: {res.stderr.strip()}")

        smoke_js = f"""
const fs = require('fs');
const vm = require('vm');
let code = fs.readFileSync('{js_tmp}', 'utf8').replace(/window\\.addEventListener[\\s\\S]*$/, '');
code += '\\n;globalThis.__v = {{ QUESTIONS, TYPES, CARS, SHARE_SUMMARIES, state, computeResult, compatScore, getCompat, startNewQuiz }};';
const el = () => ({{ style:{{setProperty(){{}}}}, classList:{{add(){{}},remove(){{}},toggle(){{}}}}, innerHTML:'', textContent:'' }});
const ctx = {{ console, Math, JSON, String, Number, Array, Object, Set, URLSearchParams, encodeURIComponent, Date,
  localStorage: {{getItem:()=>null,setItem(){{}}}},
  document: {{ getElementById: (id) => id === 'carbti-catalog' ? {{ textContent: {json.dumps(json.dumps(catalog, ensure_ascii=False))} }} : el(), querySelectorAll: ()=>[], createElement: el, addEventListener(){{}} }},
  window: {{ scrollTo(){{}}, addEventListener(){{}} }}, location: {{ hash:'', search:'', origin:'{site_url}', pathname:'/' }}, history: {{ replaceState(){{}} }}, navigator: {{}}, setTimeout, clearTimeout }};
vm.createContext(ctx); vm.runInContext(code, ctx);
const v = ctx.__v;
if (v.QUESTIONS.length !== 28) throw new Error('QUESTIONS length != 28: ' + v.QUESTIONS.length);
for (const ax of ['FA','CO','SI','RL']) {{
  const qs = v.QUESTIONS.filter(q => q.axis === ax);
  if (qs.filter(q=>q.dir>0).length !== 3 || qs.filter(q=>q.dir<0).length !== 3) throw new Error('Axis imbalance ' + ax);
}}
for (const c of Object.keys(v.TYPES)) {{
  const g = v.getCompat(c);
  if (v.compatScore(c, g.best) <= v.compatScore(c, g.rival) || v.compatScore(c, g.rival) <= v.compatScore(c, g.enemy)) throw new Error('Compat order broken ' + c);
}}
console.log('NODE_SMOKE_OK');
"""
        sres = subprocess.run(["node", "-e", smoke_js], capture_output=True, text=True)
        if sres.returncode != 0 or "NODE_SMOKE_OK" not in sres.stdout:
            errors.append(f"JS自動スモークテスト失敗: {sres.stderr.strip()} {sres.stdout.strip()}")

# 4. Car illustrations check (13 cars x 5 bgs = 65)
missing_imgs = []
for c in cars:
    for b in BGS:
        p = os.path.join(ROOT, "images", f"{c}_{b}.jpg")
        if not os.path.exists(p) or os.path.getsize(p) < 10000:
            missing_imgs.append(f"images/{c}_{b}.jpg")
if missing_imgs:
    errors.append(f"不足・破損している車両画像が {len(missing_imgs)} 枚あります: {missing_imgs[:5]}")

# 5. Check all 16 types, 208 type_car, 16 vs, 16 SEO pages & X lengths
types_data = catalog.get("TYPES", {})
summaries_data = catalog.get("SHARE_SUMMARIES", {})
for t in TYPES:
    t_obj = types_data.get(t, {})
    jp_name = t_obj.get("name", "")
    if jp_name and jp_name not in (t_obj.get("longDesc") or [""])[0]:
        errors.append(f"{t} の longDesc[0] に新タイプ名が反映されていません")

    worst_tweet = f"私は【{t}：{jp_name}】\n{summaries_data.get(t, '')}\n🚗軽自動車・K-CAR／人見知り歓迎\n#CARBTI #車好き診断"
    wt = x_weight(worst_tweet) + 24
    if wt > 280:
        errors.append(f"{t} のXシェア文面が280文字制限を超えています ({wt}/280)")

    for p, desc in [
        (os.path.join(ROOT, "ogp", f"{t}.jpg"), f"ogp/{t}.jpg"),
        (os.path.join(ROOT, "ogp", f"vs_{t}.jpg"), f"ogp/vs_{t}.jpg"),
    ]:
        if not os.path.exists(p) or os.path.getsize(p) < 10000:
            errors.append(f"OGP画像不足/破損: {desc}")

    sh_p = os.path.join(ROOT, "share", f"{t}.html")
    if not os.path.exists(sh_p):
        errors.append(f"シェアページ不足: share/{t}.html")
    else:
        sh = open(sh_p, encoding="utf-8").read()
        if f'content="{site_url}/ogp/{t}.jpg' not in sh or jp_name not in sh or 'noindex' not in sh or f'&from=share&vs={t}' not in sh:
            errors.append(f"share/{t}.html のURL・noindex・from=share設定が未同期です")

    vs_p = os.path.join(ROOT, "vs", f"{t}.html")
    if not os.path.exists(vs_p):
        errors.append(f"相性招待ページ不足: vs/{t}.html")
    else:
        vs_h = open(vs_p, encoding="utf-8").read()
        if f'content="{site_url}/ogp/vs_{t}.jpg' not in vs_h or jp_name not in vs_h or 'noindex' not in vs_h:
            errors.append(f"vs/{t}.html のOGP・noindex・タイプ名が未同期です")

    tp_p = os.path.join(ROOT, "types", f"{t}.html")
    if not os.path.exists(tp_p):
        errors.append(f"SEOページ不足: types/{t}.html")
    else:
        tp_h = open(tp_p, encoding="utf-8").read()
        text_only = re.sub(r"<[^>]+>", "", tp_h)
        if len(text_only) < 900 or jp_name not in tp_h or f'content="{site_url}/ogp/{t}.jpg' not in tp_h or '"FAQPage"' not in tp_h or '../images/' not in tp_h or '../privacy.html' not in tp_h:
            errors.append(f"types/{t}.html のコンテンツ・FAQPage・純粋画像・法務リンクが不足しています")
        if re.search(r"mbti", tp_h, flags=re.IGNORECASE):
            errors.append(f"types/{t}.html に 'MBTI' が残っています")

    for cid in cars:
        ogp_c = os.path.join(ROOT, "ogp", f"{t}_{cid}.jpg")
        sh_c = os.path.join(ROOT, "share", f"{t}_{cid}.html")
        if not os.path.exists(ogp_c) or os.path.getsize(ogp_c) < 10000:
            errors.append(f"車種別OGP不足: ogp/{t}_{cid}.jpg")
        if not os.path.exists(sh_c):
            errors.append(f"車種別シェアページ不足: share/{t}_{cid}.html")
        else:
            shc_txt = open(sh_c, encoding="utf-8").read()
            if f'content="{site_url}/ogp/{t}_{cid}.jpg' not in shc_txt or jp_name not in shc_txt or 'noindex' not in shc_txt:
                errors.append(f"share/{t}_{cid}.html が未同期です")

if errors:
    print("=== HARNESS VERIFICATION FAILED ===")
    for e in errors:
        print(" [NG]", e)
    sys.exit(1)
else:
    print("=== HARNESS VERIFICATION PASSED (ALL CHECKS OK) ===")
    print(f" - {len(cars)*5}/{len(cars)*5} car illustrations verified ({len(cars)} categories x 5 scenes)")
    print(f" - {1 + len(TYPES)*(2 + len(cars))} OGP images verified (root + 16 type + {len(TYPES)*len(cars)} type_car + 16 vs)")
    print(f" - {len(TYPES)*(1 + len(cars))} share pages (noindex+from=share), {len(TYPES)} vs pages (noindex), {len(TYPES)} SEO pages (+FAQPage)")
    print(" - privacy.html, terms.html, ASSETS_PROVENANCE.md, JS smoke test, trademark/OS/MBTI guards verified")
    sys.exit(0)
