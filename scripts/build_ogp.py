#!/usr/bin/env python3
"""
CAR-BTI OGP & Xシェアカード自動生成スクリプト（Antigravityハーネス用）
site_config.json の site_url を読み込み、以下を自動生成・更新します:
  1. ogp/<TYPE>.jpg (1200x630) 全16タイプ別のXカード画像
  2. share/<TYPE>.html         全16タイプ別のXシェア専用ページ（完全URLのog:image付き）
  3. index.html                og:image / twitter:image / Xシェア関数のURLを本番URLへ自動反映
"""
import json, os, re, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "site_config.json")

CARS = ["coupe","supercar","open","sedan","vip_minivan","utility_van","wagon","crocan","urban_suv","compact","truck_work"]

TYPES_META = {
    "FCSR": ("FC", "coupe", "touge", "熱血セッティング志向", "FC CLUSTER", (56, 189, 248)),
    "FCSL": ("FC", "truck_work", "garage", "合理的エンジニア志向", "FC CLUSTER", (56, 189, 248)),
    "FCIR": ("FC", "open", "garage", "孤高のカスタムロマン派", "FC CLUSTER", (56, 189, 248)),
    "FCIL": ("FC", "wagon", "garage", "緻密なデータ探求派", "FC CLUSTER", (56, 189, 248)),
    "FOSR": ("FO", "crocan", "nature", "週末ロードトリップ派", "FO CLUSTER", (52, 211, 153)),
    "FOSL": ("FO", "utility_van", "nature", "語れる実用データ派", "FO CLUSTER", (52, 211, 153)),
    "FOIR": ("FO", "sedan", "nature", "ひとり時間至上主義ドライバー", "FO CLUSTER", (52, 211, 153)),
    "FOIL": ("FO", "supercar", "touge", "設計思想の吟味家", "FO CLUSTER", (52, 211, 153)),
    "ACSR": ("AC", "vip_minivan", "highway", "夜のPA・オーラ魅せ感性派", "AC CLUSTER", (167, 139, 250)),
    "ACSL": ("AC", "urban_suv", "city", "ミリ単位の美学ディレクター", "AC CLUSTER", (167, 139, 250)),
    "ACIR": ("AC", "compact", "garage", "自己満アートの求道者", "AC CLUSTER", (167, 139, 250)),
    "ACIL": ("AC", "sedan", "garage", "質感と音の完全主義者", "AC CLUSTER", (167, 139, 250)),
    "AOSR": ("AO", "compact", "city", "朝活カフェ巡り感性派", "AO CLUSTER", (251, 191, 36)),
    "AOSL": ("AO", "coupe", "city", "カタログ語り＆歴史キュレーター", "AO CLUSTER", (251, 191, 36)),
    "AOIR": ("AO", "open", "nature", "静かなる愛車フェチ・艶守り", "AO CLUSTER", (251, 191, 36)),
    "AOIL": ("AO", "supercar", "garage", "フルノーマル保存の審美眼", "AO CLUSTER", (251, 191, 36)),
}

def load_font(size, bold=True):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def build_type_ogp(code, car, bg, cluster_label, accent_rgb, out_path):
    src = os.path.join(ROOT, "images", f"{car}_{bg}.jpg")
    ogp = Image.new("RGB", (1200, 630), (7, 11, 20))
    hero = Image.open(src).convert("RGB").resize((1200, 675), Image.Resampling.LANCZOS)
    ogp.paste(hero, (0, -22))

    overlay = Image.new("RGBA", (1200, 630), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for x in range(1200):
        alpha = int(max(40, min(238, 238 - (x / 1200) * 195)))
        odraw.line([(x, 0), (x, 630)], fill=(6, 10, 20, alpha))
    odraw.rectangle([0, 0, 1200, 8], fill=(*accent_rgb, 255))
    odraw.rectangle([0, 622, 1200, 630], fill=(244, 63, 94, 255))
    ogp = Image.alpha_composite(ogp.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(ogp)
    f_xl = load_font(124, True)
    f_lg = load_font(34, True)
    f_md = load_font(24, False)
    f_sm = load_font(20, True)

    draw.rounded_rectangle([64, 64, 340, 112], radius=24, fill=(14, 28, 48), outline=accent_rgb, width=2)
    draw.text((88, 77), f"CAR-BTI | {cluster_label}", fill=accent_rgb, font=f_sm)
    draw.text((64, 145), code, fill=(255, 255, 255), font=f_xl)
    draw.text((64, 305), "AUTOMOTIVE PERSONALITY TYPE", fill=accent_rgb, font=f_lg)
    draw.text((64, 365), "Tap to view full license card & compatibility", fill=(203, 213, 225), font=f_md)
    draw.rounded_rectangle([64, 455, 390, 520], radius=16, fill=accent_rgb)
    draw.text((98, 474), "VIEW MY RESULT  >", fill=(6, 12, 24), font=f_sm)
    ogp.save(out_path, format="JPEG", quality=88, optimize=True)

def build_share_html(code, jp_name, site_url, suffix=""):
    og_img = f"{site_url}/ogp/{code}{suffix}.jpg"
    share_url = f"{site_url}/share/{code}{suffix}.html"
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>CAR-BTI 診断結果｜{code}：{jp_name}</title>
<meta name="description" content="CAR-BTI（車好き16タイプ診断）の結果は【{code}：{jp_name}】！あなたも27問で自分の車好きタイプと本音×リアルな交流スタイルを診断しよう。" />
<meta property="og:title" content="CAR-BTI 診断結果｜{code}：{jp_name}" />
<meta property="og:description" content="車好き16タイプ診断の結果は【{code}：{jp_name}】！車種不問・全派閥対応のライセンスカードを発行。" />
<meta property="og:type" content="website" />
<meta property="og:url" content="{share_url}" />
<meta property="og:image" content="{og_img}" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="CAR-BTI 診断結果｜{code}：{jp_name}" />
<meta name="twitter:description" content="車好き16タイプ診断の結果は【{code}：{jp_name}】！" />
<meta name="twitter:image" content="{og_img}" />
<script>
  const qs = location.search ? location.search.replace(/^\\?/, '&') : '';
  location.replace('../index.html#result?type={code}' + qs);
</script>
</head>
<body style="background:#070b14;color:#f1f5f9;font-family:sans-serif;display:grid;place-items:center;min-height:100vh;margin:0;">
  <p>診断結果ページへ移動しています… <a href="../index.html#result?type={code}" style="color:#22d3ee;">こちらをクリック</a></p>
</body>
</html>
"""

def main():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    site_url = cfg.get("site_url", "").strip().rstrip("/")
    if not site_url.startswith("https://"):
        print("ERROR: site_config.json の site_url に https:// から始まる公開URLを設定してください。", file=sys.stderr)
        sys.exit(1)

    ogp_dir = os.path.join(ROOT, "ogp")
    share_dir = os.path.join(ROOT, "share")
    os.makedirs(ogp_dir, exist_ok=True)
    os.makedirs(share_dir, exist_ok=True)

    for code, (cl, car, bg, jp_name, cl_label, accent) in TYPES_META.items():
        build_type_ogp(code, car, bg, cl_label, accent, os.path.join(ogp_dir, f"{code}.jpg"))
        with open(os.path.join(share_dir, f"{code}.html"), "w", encoding="utf-8") as f:
            f.write(build_share_html(code, jp_name, site_url))
        for c in CARS:
            build_type_ogp(code, c, bg, cl_label, accent, os.path.join(ogp_dir, f"{code}_{c}.jpg"))
            with open(os.path.join(share_dir, f"{code}_{c}.html"), "w", encoding="utf-8") as f:
                f.write(build_share_html(code, jp_name, site_url, f"_{c}"))

    # Update index.html with absolute og:image, twitter:image, and X share URL
    idx_path = os.path.join(ROOT, "index.html")
    with open(idx_path, "r", encoding="utf-8") as f:
        html = f.read()

    html = re.sub(r'(<meta property="og:image" content=")[^"]+(")', rf'\g<1>{site_url}/ogp.jpg\g<2>', html)
    html = re.sub(r'(<meta name="twitter:image" content=")[^"]+(")', rf'\g<1>{site_url}/ogp.jpg\g<2>', html)

    # Inject share URL into shareOnX()
    old_share_pattern = r"window\.open\(`https://twitter\.com/intent/tweet\?text=\$\{encodeURIComponent\(text\)\}[^`]*`, '_blank'\);"
    new_share_code = (
        f"const shareUrl = `{site_url}/share/${{t.code}}.html?car=${{state.selectedCar}}&vcar=${{state.visualCar}}&bg=${{state.selectedBg}}&temp=${{state.socialTemp}}&scope=${{state.socialScope}}`;\n"
        "  window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(shareUrl)}`, '_blank');"
    )
    if "const shareUrl =" in html:
        html = re.sub(r"const shareUrl = `[^`]+`;", f"const shareUrl = `{site_url}/share/${{t.code}}_${{state.visualCar}}.html?car=${{carShort}}&vcar=${{state.visualCar}}&bg=${{state.selectedBg}}&temp=${{state.socialTemp}}&open=${{state.socialOpen}}&scope=${{state.socialScope}}&comm=${{state.socialComm}}&real=${{state.realityMode}}&st=${{stShort}}&rg=${{rgIdx}}&ex=${{exIdx}}`;", html)
    else:
        assert re.search(old_share_pattern, html), "shareOnX pattern not found in index.html"
        html = re.sub(old_share_pattern, new_share_code, html, count=1)

    with open(idx_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"OK: Generated 16 OGP images, 16 share pages, and updated index.html for {site_url}")

if __name__ == "__main__":
    main()
