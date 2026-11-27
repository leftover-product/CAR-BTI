#!/usr/bin/env python3
"""
CAR-BTI OGP・シェアページ・相性招待OGP・リッチSEO記事・法務ページ 自動生成スクリプト
index.html 内の <script id="carbti-catalog" type="application/json"> を単一データ源（SSOT）として読み込み、
1. ogp.jpg + ogp/<TYPE>.jpg + ogp/<TYPE>_<CAR>.jpg + ogp/vs_<TYPE>.jpg（全241枚、日本語入り1200x630）
2. share/<TYPE>.html / share/<TYPE>_<CAR>.html（全224ページ、noindex、?v=5、&from=share&vs=<TYPE>）
3. vs/<TYPE>.html（全16ページ、noindex、GA4付き相性招待専用OGP）
4. types/<TYPE>.html（全16ページ、純粋車両ヒーロー・4文字解説・あるある・地雷・相性・FAQPage/Article JSON-LD）
5. privacy.html / terms.html / sitemap.xml / robots.txt
6. index.html の meta URL・GA4・SITE_URL 同期
を一括生成します。
"""
import html as htmllib
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "site_config.json")
INDEX_PATH = os.path.join(ROOT, "index.html")
SWIFT_SRC = os.path.join(ROOT, "scripts", "render_ogp.swift")
SWIFT_BIN = "/tmp/carbti_render_ogp"

CLUSTER_ACCENTS = {
    "FC": [56, 189, 248],
    "FO": [52, 211, 153],
    "AC": [167, 139, 250],
    "AO": [251, 191, 36],
}

LETTER_MEANINGS = {
    "F": ("機能・体験重視 (Function)", "走り・使い勝手・メカニズムの実力や旅の体験に惚れる"),
    "A": ("造形・空間重視 (Aesthetic)", "ボディライン・艶・配色・車内空間など見た目の世界観に惚れる"),
    "C": ("創る・弄る (Create)", "カスタム・DIY・ショップ施工で自分色に仕立てる過程を楽しむ"),
    "O": ("守る・味わう (Original)", "メーカー純正の完成度やオリジナル状態・走りの体験をそのまま愛でる"),
    "S": ("社交・共有 (Social)", "イベント・ドライブ・SNSで仲間と感動を分かち合いたい"),
    "I": ("没入・孤高 (Immersion)", "自分の世界観の中でマイペースに愛車・推し車と向き合いたい"),
    "R": ("ロマン・感性 (Romance)", "スペックより音・ときめき・一目惚れなど直感の感動を大切にする"),
    "L": ("論理・データ (Logic)", "数値・構造・歴史的背景・コスパなどの納得感を重視する"),
}


def hex_from_rgb(rgb):
    return "#%02x%02x%02x" % tuple(rgb)


def extract_catalog(index_html):
    m = re.search(
        r'<script id="carbti-catalog" type="application/json">\s*(.*?)\s*</script>',
        index_html,
        flags=re.DOTALL,
    )
    if not m:
        raise RuntimeError("index.html に #carbti-catalog JSON ブロックが見つかりません")
    return json.loads(m.group(1))


def build_ga4_snippet(ga_id):
    if not ga_id:
        return ""
    return (
        f'<script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>\n'
        f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}"
        f"gtag('js',new Date());gtag('config','{ga_id}');</script>"
    )


def compat_score(a, b):
    s = 40
    if a[0] == b[0]:
        s += 20
    if a[1] == b[1]:
        s += 18
    if a[2] == b[2]:
        s += 12
    if a[3] == b[3]:
        s += 6
    if a[0] == b[0] and a[1] == b[1] and a[2] == b[2] and a[3] != b[3]:
        s += 8
    return s


def get_compat(code):
    flip_map = {"F": "A", "A": "F", "C": "O", "O": "C", "S": "I", "I": "S", "R": "L", "L": "R"}

    def flip(c, idx):
        arr = list(c)
        arr[idx] = flip_map[arr[idx]]
        return "".join(arr)

    best = flip(code, 3)
    rival = flip(flip(code, 0), 3)
    enemy = flip(flip(flip(flip(code, 0), 1), 2), 3)
    return {
        "best": (best, compat_score(code, best)),
        "rival": (rival, compat_score(code, rival)),
        "enemy": (enemy, compat_score(code, enemy)),
    }


def ensure_swift_renderer():
    need_build = not os.path.exists(SWIFT_BIN) or os.path.getmtime(SWIFT_SRC) > os.path.getmtime(SWIFT_BIN)
    if need_build:
        env = os.environ.copy()
        env["TMPDIR"] = "/tmp"
        cmd = [
            "swiftc",
            "-module-cache-path",
            "/tmp/swift_mc",
            "-O",
            SWIFT_SRC,
            "-o",
            SWIFT_BIN,
        ]
        res = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"render_ogp.swift compile failed:\n{res.stderr}")


def render_all_ogp(jobs):
    ensure_swift_renderer()
    jobs_path = "/tmp/carbti_ogp_jobs.json"
    with open(jobs_path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False)
    res = subprocess.run([SWIFT_BIN, jobs_path], capture_output=True, text=True)
    if res.returncode != 0 or f"SWIFT_OGP_OK:{len(jobs)}" not in res.stdout:
        raise RuntimeError(f"render_ogp failed:\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")


def build_share_html(code, jp_name, site_url, suffix=""):
    esc_name = htmllib.escape(jp_name)
    og_img = f"{site_url}/ogp/{code}{suffix}.jpg?v=5"
    share_url = f"{site_url}/share/{code}{suffix}.html"
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="robots" content="noindex, follow" />
<title>CAR-BTI 診断結果｜{code}：{esc_name}</title>
<meta name="description" content="CAR-BTI（車好き16タイプ診断）の結果は【{code}：{esc_name}】！あなたも全28問で自分の車好きタイプと本音×リアルな交流スタイルを診断しよう。" />
<meta property="og:title" content="CAR-BTI 診断結果｜{code}：{esc_name}" />
<meta property="og:description" content="車好き16タイプ診断の結果は【{code}：{esc_name}】！車種不問・全13車種対応のライセンスカードを発行。" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="CAR-BTI｜車好き16タイプ診断" />
<meta property="og:url" content="{share_url}" />
<meta property="og:image" content="{og_img}" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="CAR-BTI 診断結果｜{code}：{esc_name}" />
<meta name="twitter:description" content="車好き16タイプ診断の結果は【{code}：{esc_name}】！" />
<meta name="twitter:image" content="{og_img}" />
<link rel="icon" type="image/svg+xml" href="../favicon.svg" />
<script>
  const qs = location.search ? location.search.replace(/^\\?/, '&') : '';
  location.replace('../#result?type={code}&from=share&vs={code}' + qs);
</script>
</head>
<body style="background:#070b14;color:#f1f5f9;font-family:sans-serif;display:grid;place-items:center;min-height:100vh;margin:0;">
  <p>診断結果ページへ移動しています… <a id="fb-link" href="../#result?type={code}&from=share&vs={code}" style="color:#38bdf8;">こちらをクリック</a></p>
  <script>document.getElementById('fb-link').href = '../#result?type={code}&from=share&vs={code}' + (location.search ? location.search.replace(/^\\?/, '&') : '');</script>
</body>
</html>
"""


def build_vs_html(code, jp_name, site_url, ga_snippet):
    esc_name = htmllib.escape(jp_name)
    og_img = f"{site_url}/ogp/vs_{code}.jpg?v=5"
    vs_url = f"{site_url}/vs/{code}.html"
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="robots" content="noindex, follow" />
<title>🤝 友達から相性診断の招待｜相手は【{code}：{esc_name}】｜CAR-BTI</title>
<meta name="description" content="CAR-BTI（車好き16タイプ診断）の友達相性診断！相手は【{code}：{esc_name}】。あなたも28問に答えて2人の相性％をチェックしよう！" />
<meta property="og:title" content="🤝 相性診断の招待｜相手は【{code}：{esc_name}】" />
<meta property="og:description" content="28問の車好き16タイプ診断に答えると、{code}との相性％と相性コメントがすぐわかります！" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="CAR-BTI｜車好き16タイプ診断" />
<meta property="og:url" content="{vs_url}" />
<meta property="og:image" content="{og_img}" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="🤝 相性診断の招待｜相手は【{code}：{esc_name}】" />
<meta name="twitter:description" content="28問の車好き16タイプ診断に答えて、{code}との相性％をチェック！" />
<meta name="twitter:image" content="{og_img}" />
<link rel="icon" type="image/svg+xml" href="../favicon.svg" />
{ga_snippet}
<script>location.replace('../?vs={code}');</script>
</head>
<body style="background:#070b14;color:#f1f5f9;font-family:sans-serif;display:grid;place-items:center;min-height:100vh;margin:0;">
  <p>相性診断ページへ移動しています… <a href="../?vs={code}" style="color:#38bdf8;">こちらをクリック</a></p>
</body>
</html>
"""


def build_type_seo_html(code, t_obj, cl_obj, all_types, accent_rgb, site_url, ga_snippet):
    jp_name = t_obj["name"]
    catch = t_obj["catch"]
    esc_name = htmllib.escape(jp_name)
    esc_catch = htmllib.escape(catch)
    cl_label = f"{cl_obj['code']}｜{cl_obj['name']}"
    og_img = f"{site_url}/ogp/{code}.jpg?v=5"
    hero_car_img = f"../images/{t_obj['car']}_{t_obj['bg']}.jpg"
    page_url = f"{site_url}/types/{code}.html"
    accent_hex = hex_from_rgb(accent_rgb)

    long_html = "\n        ".join(f"<p>{htmllib.escape(p)}</p>" for p in t_obj["longDesc"])
    wc_html = "\n        ".join(
        f'<span style="display:inline-block;padding:5px 11px;margin:4px;border-radius:999px;background:rgba(255,255,255,0.05);border:1px solid rgba(148,163,184,0.22);color:{accent_hex};font-weight:800;font-size:{"16px" if w == 3 else ("13.5px" if w == 2 else "12px")};">{htmllib.escape(word)}</span>'
        for word, w in t_obj["wordcloud"]
    )
    letters_html = "\n        ".join(
        f'<div style="padding:10px 12px;border-radius:10px;background:rgba(255,255,255,0.04);border:1px solid rgba(148,163,184,0.2);">'
        f'<strong style="color:{accent_hex};font-size:14px;">{ch}｜{htmllib.escape(LETTER_MEANINGS[ch][0])}</strong>'
        f'<div style="font-size:12.5px;color:#cbd5e1;margin-top:2px;">{htmllib.escape(LETTER_MEANINGS[ch][1])}</div></div>'
        for ch in code
    )

    comp = get_compat(code)
    compat_cards = [
        ("最高の相棒", "#34d399", comp["best"][0], comp["best"][1], "価値観と距離感が一致し、感性×論理で補い合えるパートナー。"),
        ("刺激的ライバル", "#fbbf24", comp["rival"][0], comp["rival"][1], "楽しむ場の温度感は近く、見る視点の違いが刺激になる好敵手。"),
        ("異文化ペア", "#f43f5e", comp["enemy"][0], comp["enemy"][1], "価値観が真逆のペア。違いを面白がり尊重する距離感が鍵。"),
    ]
    compat_html = "\n        ".join(
        f'<a href="./{c_code}.html" style="display:block;padding:14px;border-radius:12px;background:rgba(255,255,255,0.04);border:1px solid rgba(148,163,184,0.22);text-decoration:none;color:#f1f5f9;">'
        f'<div style="font-size:11.5px;font-weight:800;color:{c_col};">{lbl}（相性 {pct}%）</div>'
        f'<div style="font-size:20px;font-weight:900;margin:2px 0;">{c_code}</div>'
        f'<div style="font-size:13px;font-weight:800;margin-bottom:4px;">{htmllib.escape(all_types[c_code]["name"])}</div>'
        f'<div style="font-size:12px;color:#94a3b8;line-height:1.5;">{desc}</div></a>'
        for lbl, c_col, c_code, pct, desc in compat_cards
    )

    other_links = "".join(
        f'<a href="./{c}.html" style="display:inline-block;padding:6px 12px;margin:4px;border-radius:10px;background:#10182b;border:1px solid rgba(148,163,184,0.25);color:#e2e8f0;text-decoration:none;font-size:13px;">{c}：{htmllib.escape(meta["name"])}</a>'
        for c, meta in all_types.items() if c != code
    )

    ld_article = json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": f"{code}（{jp_name}）の特徴・あるある・相性｜CAR-BTI 車好き16タイプ診断",
        "description": catch,
        "image": og_img,
        "url": page_url,
        "dateModified": "2026-11-27",
        "inLanguage": "ja",
        "author": {"@type": "Organization", "name": "CAR-BTI 運営事務局"},
    }, ensure_ascii=False)

    ld_faq = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f"車好き16タイプ診断の{code}（{jp_name}）とはどんなタイプですか？",
                "acceptedAnswer": {"@type": "Answer", "text": f"{catch} {t_obj['longDesc'][0]}"},
            },
            {
                "@type": "Question",
                "name": f"{code}と一番相性が良いタイプは？",
                "acceptedAnswer": {"@type": "Answer", "text": f"最高の相棒は{comp['best'][0]}（{all_types[comp['best'][0]]['name']}・相性{comp['best'][1]}%）です。価値観と距離感が一致し、感性×論理で補い合えます。"},
            },
        ],
    }, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{code}（{esc_name}）の性格・あるある・相性｜CAR-BTI 車好き16タイプ診断</title>
<meta name="description" content="CAR-BTI（車好き16タイプ診断）の【{code}：{esc_name}】タイプを徹底解説。{esc_catch} 4文字の意味・あるある・立ち回り・地雷・他タイプとの相性まで公開中。" />
<link rel="canonical" href="{page_url}" />
<meta property="og:title" content="{code}（{esc_name}）｜CAR-BTI 車好き16タイプ診断" />
<meta property="og:description" content="{esc_catch} あなたも無料28問で自分の車好きタイプを診断しよう。" />
<meta property="og:type" content="article" />
<meta property="og:site_name" content="CAR-BTI｜車好き16タイプ診断" />
<meta property="og:url" content="{page_url}" />
<meta property="og:image" content="{og_img}" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:image" content="{og_img}" />
<link rel="icon" type="image/svg+xml" href="../favicon.svg" />
<script type="application/ld+json">{ld_article}</script>
<script type="application/ld+json">{ld_faq}</script>
{ga_snippet}
</head>
<body style="margin:0;background:#070b14;color:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Noto Sans JP',sans-serif;line-height:1.8;">
  <main style="max-width:800px;margin:0 auto;padding:24px 18px 60px;">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:14px;">
      <a href="../" style="color:#38bdf8;text-decoration:none;font-size:13.5px;font-weight:800;">← CAR-BTI トップへ戻る</a>
      <a href="../#result?type={code}&from=share&vs={code}" style="color:#cbd5e1;text-decoration:none;font-size:12.5px;">結果カード画面で開く →</a>
    </div>

    <article style="border-radius:18px;overflow:hidden;border:1px solid rgba(148,163,184,0.25);background:#0d1324;">
      <img src="{hero_car_img}" alt="{code} {esc_name} イメージ車両" style="width:100%;aspect-ratio:16/9;object-fit:cover;display:block;" />
      <div style="padding:24px;">
        <span style="display:inline-block;padding:4px 11px;border-radius:999px;font-size:12px;font-weight:800;color:{accent_hex};border:1px solid {accent_hex};">{htmllib.escape(cl_label)}</span>
        <h1 style="margin:10px 0 6px;font-size:clamp(22px,4vw,28px);font-weight:900;line-height:1.3;">{code}：{esc_name}</h1>
        <p style="margin:0 0 18px;color:#cbd5e1;font-size:15px;font-weight:700;">{esc_catch}</p>
        <div style="display:flex;flex-wrap:wrap;gap:10px;margin-bottom:24px;">
          <a href="../" style="display:inline-block;padding:12px 20px;border-radius:12px;background:{accent_hex};color:#070b14;font-weight:900;text-decoration:none;">自分の車好きタイプを診断する（28問・無料）</a>
          <a href="../?vs={code}" style="display:inline-block;padding:12px 20px;border-radius:12px;background:#1e293b;color:#f1f5f9;font-weight:700;text-decoration:none;border:1px solid rgba(148,163,184,0.35);">{code}との相性を診断する</a>
        </div>

        <h2 style="font-size:18px;font-weight:900;margin:22px 0 10px;border-left:4px solid {accent_hex};padding-left:10px;">4文字アルファベット（{code}）の意味</h2>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px;margin-bottom:22px;">
        {letters_html}
        </div>

        <h2 style="font-size:18px;font-weight:900;margin:24px 0 10px;border-left:4px solid {accent_hex};padding-left:10px;">このタイプの本質・どんな車好き？</h2>
        <div style="color:#e2e8f0;font-size:14.5px;">
        {long_html}
        </div>

        <h2 style="font-size:18px;font-weight:900;margin:26px 0 10px;border-left:4px solid {accent_hex};padding-left:10px;">あるある・生態ワード</h2>
        <div style="padding:14px;border-radius:14px;background:rgba(255,255,255,0.03);border:1px solid rgba(148,163,184,0.2);">
        {wc_html}
        </div>

        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;margin-top:24px;">
          <div style="padding:16px;border-radius:14px;background:rgba(255,255,255,0.04);border:1px solid rgba(148,163,184,0.22);">
            <h3 style="margin:0 0 6px;font-size:15px;font-weight:900;color:#7dd3fc;">イベント・オフ会・SNSでの立ち回り</h3>
            <p style="margin:0;font-size:13.5px;color:#cbd5e1;">{htmllib.escape(t_obj["meetup"])}</p>
          </div>
          <div style="padding:16px;border-radius:14px;background:rgba(255,255,255,0.04);border:1px solid rgba(148,163,184,0.22);">
            <h3 style="margin:0 0 6px;font-size:15px;font-weight:900;color:#fda4af;">沼りポイント＆苦手なこと（地雷）</h3>
            <p style="margin:0;font-size:13.5px;color:#cbd5e1;">{htmllib.escape(t_obj["pitfall"])}</p>
          </div>
        </div>

        <h2 style="font-size:18px;font-weight:900;margin:26px 0 12px;border-left:4px solid {accent_hex};padding-left:10px;">{code} と他タイプの相性</h2>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px;">
        {compat_html}
        </div>
      </div>
    </article>

    <section style="margin-top:28px;">
      <h2 style="font-size:18px;font-weight:900;margin:0 0 10px;">他の車好き16タイプを見る</h2>
      <div>{other_links}</div>
    </section>

    <footer style="margin-top:34px;padding-top:16px;border-top:1px solid rgba(148,163,184,0.2);font-size:12px;color:#94a3b8;display:flex;flex-wrap:wrap;justify-content:space-between;gap:10px;">
      <span>※CAR-BTI（車好き16タイプ診断）は個人の趣味・傾向を楽しむ非公式の娯楽診断コンテンツです。</span>
      <span><a href="../privacy.html" style="color:#38bdf8;">プライバシーポリシー</a> ／ <a href="../terms.html" style="color:#38bdf8;">利用規約・免責事項</a></span>
    </footer>
  </main>
</body>
</html>
"""


def build_legal_page(kind, site_url, ga_snippet):
    if kind == "privacy":
        title = "プライバシーポリシー｜CAR-BTI 車好き16タイプ診断"
        body = """
        <h1>プライバシーポリシー</h1>
        <p>CAR-BTI 運営事務局（以下「当事務局」）は、CAR-BTI（車好き16タイプ診断、公開URL：{site_url}/ 以下「当サイト」）における利用者情報の取り扱いについて、以下のとおりプライバシーポリシーを定めます。</p>
        <h2>1. 個人情報の非収集について</h2>
        <p>当サイトは氏名・メールアドレス・電話番号・住所・自動車登録番号等の個人を特定できる情報の登録を不要としています。診断結果のカスタム欄で入力されたニックネームおよび愛車名は、ご利用の端末のブラウザ内（localStorage）および端末内での画像書き出しにのみ利用され、共有URLや当事務局サーバーへ送信されることはありません。</p>
        <h2>2. 外部送信およびアクセス解析ツールの利用（電気通信事業法に基づく開示）</h2>
        <p>当サイトではサービス改善および不正アクセス防止・表示最適化のため、以下の第三者サービスへ利用情報を外部送信しています。</p>
        <ul>
          <li><strong>Google アナリティクス（GA4）／提供者：Google LLC</strong><br>
          送信される情報：閲覧ページURL、診断の開始・完了・シェア・関心企画投票等のイベント種別（匿名化されたタイプコードや車種系統ラベルを含む）、ブラウザ・端末種別、IPアドレス等のアクセス情報（個人特定情報は含みません）。<br>
          利用目的：利用状況の分析および診断体験・企画の改善。<br>
          オプトアウト：Google アナリティクス オプトアウト アドオン（https://tools.google.com/dlpage/gaoptout）により無効化できます。</li>
          <li><strong>Google Fonts／提供者：Google LLC</strong><br>
          送信される情報：フォント取得時のアクセス情報（IPアドレス、ブラウザ情報等）。<br>
          利用目的：Webフォントの配信および表示品質の維持。</li>
        </ul>
        <h2>3. ブラウザ内保存（localStorage）の利用</h2>
        <p>当サイトは、再訪時の診断結果表示・友達との相性コレクション・企画投票状態の保持のために、ブラウザの localStorage 機能を使用します。ブラウザ設定または画面上の履歴クリア操作により、いつでも削除できます。</p>
        <h2>4. 改定およびお問い合わせ窓口</h2>
        <p>当事務局は必要に応じて本ポリシーを改定します。プライバシーに関するお問い合わせは公開リポジトリ（GitHub: leftover-product/CAR-BTI）の Issues 窓口よりご連絡ください。</p>
        <p style="color:#94a3b8;font-size:13px;">制定・最終改定日：2026年11月27日｜運営主体：CAR-BTI 運営事務局（代表：leftover-product）</p>
        """.format(site_url=site_url)
    else:
        title = "利用規約・免責事項｜CAR-BTI 車好き16タイプ診断"
        body = """
        <h1>利用規約・免責事項</h1>
        <p>本規約は、CAR-BTI 運営事務局（以下「当事務局」）が提供する「CAR-BTI｜車好き16タイプ診断」（公開URL：{site_url}/ 以下「当サイト」）の利用条件を定めるものです。</p>
        <h2>1. 本サービスの性質・非公式表記</h2>
        <p>当サイトの診断結果、相性判定、解説文は、車好き同士のコミュニケーションや趣味の自己理解を楽しむための娯楽コンテンツです。心理学・医学的評価や購入・整備等の専門的助言を行うものではありません。また、当サイトは独立した非公式サービスであり、実在の自動車メーカー・部品メーカー・各種団体および第三者の登録商標とは一切関係ありません。</p>
        <h2>2. 知的財産権</h2>
        <p>当サイトに掲載されているオリジナル架空車両イラスト（全65点）、OGP画像、プログラム、テキスト、デザインの著作権および関連権利は当事務局または正当な権利者に帰属します。個人のSNSシェア・プロフィール利用の範囲を超えた無断転載・商用再配布・改変販売を禁止します。</p>
        <h2>3. 禁止事項</h2>
        <ul>
          <li>当サイトへの不正アクセス、過度な負荷をかける行為、URLパラメータ等を用いた悪意あるスクリプト実行の試み</li>
          <li>当サイトの診断結果や画像を用いた他者への誹謗中傷、迷惑行為、法令または公序良俗に反する行為</li>
        </ul>
        <h2>4. 免責事項・サービス変更</h2>
        <p>当事務局は、当サイトの正確性・完全性・継続性について保証するものではなく、利用により生じた損害について法令上許される範囲内で責任を負いません。内容は予告なく変更・停止される場合があります。</p>
        <h2>5. 準拠法およびお問い合わせ窓口</h2>
        <p>本規約は日本法に準拠します。一般のお問い合わせおよび法人提携・メディア掲載・権利確認に関するご連絡は、公開リポジトリ（GitHub: leftover-product/CAR-BTI）の Issues 窓口にて受け付けています。</p>
        <p style="color:#94a3b8;font-size:13px;">制定・最終改定日：2026年11月27日｜運営主体：CAR-BTI 運営事務局（代表：leftover-product）</p>
        """.format(site_url=site_url)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title}</title>
<link rel="canonical" href="{site_url}/{kind}.html" />
<link rel="icon" type="image/svg+xml" href="./favicon.svg" />
{ga_snippet}
</head>
<body style="margin:0;background:#070b14;color:#e2e8f0;font-family:-apple-system,BlinkMacSystemFont,'Noto Sans JP',sans-serif;line-height:1.85;">
  <main style="max-width:780px;margin:0 auto;padding:28px 18px 60px;">
    <div style="margin-bottom:18px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;">
      <a href="./" style="color:#38bdf8;text-decoration:none;font-weight:800;font-size:14px;">← CAR-BTI トップへ戻る</a>
      <span style="font-size:13px;"><a href="./privacy.html" style="color:#94a3b8;">プライバシーポリシー</a> ／ <a href="./terms.html" style="color:#94a3b8;">利用規約・免責事項</a></span>
    </div>
    <article style="background:#0d1324;border:1px solid rgba(148,163,184,0.22);border-radius:18px;padding:26px;">
      {body}
    </article>
  </main>
</body>
</html>
"""


def main():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    site_url = cfg.get("site_url", "").strip().rstrip("/")
    ga_id = cfg.get("ga_measurement_id", "").strip()
    ga_snippet = build_ga4_snippet(ga_id)
    if not site_url.startswith("https://"):
        print("ERROR: site_config.json の site_url に https:// から始まる公開URLを設定してください。", file=sys.stderr)
        sys.exit(1)

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        index_html = f.read()

    catalog = extract_catalog(index_html)
    cars = catalog["CARS"]
    clusters = catalog["CLUSTERS"]
    types = catalog["TYPES"]

    ogp_dir = os.path.join(ROOT, "ogp")
    share_dir = os.path.join(ROOT, "share")
    vs_dir = os.path.join(ROOT, "vs")
    types_dir = os.path.join(ROOT, "types")
    for d in (ogp_dir, share_dir, vs_dir, types_dir):
        os.makedirs(d, exist_ok=True)

    # 1. Prepare all 241 OGP rendering jobs
    jobs = [{
        "kind": "root",
        "out": os.path.join(ROOT, "ogp.jpg"),
        "src": os.path.join(ROOT, "images", "coupe_highway.jpg"),
        "code": "CAR-BTI",
        "cluster": "16 TYPES",
        "title": "あなたの「車好きタイプ」と\n仲間との距離感を診断する。",
        "subtitle": f"全16タイプ × 全{len(cars)}車種（軽・旧車・EV対応）\n本音×リアル28問で愛車スタイルを診断",
        "accent": [56, 189, 248],
    }]

    for code, t_obj in types.items():
        cl_code = t_obj["cluster"]
        cl_obj = clusters[cl_code]
        accent = CLUSTER_ACCENTS[cl_code]
        cl_label = f"{cl_code} | {cl_obj['name']}"
        ogp_title = t_obj.get("ogpTitle", t_obj["name"])
        jobs.append({
            "kind": "type",
            "out": os.path.join(ogp_dir, f"{code}.jpg"),
            "src": os.path.join(ROOT, "images", f"{t_obj['car']}_{t_obj['bg']}.jpg"),
            "code": code,
            "cluster": cl_label,
            "title": ogp_title,
            "subtitle": t_obj["catch"],
            "accent": accent,
        })
        jobs.append({
            "kind": "vs",
            "out": os.path.join(ogp_dir, f"vs_{code}.jpg"),
            "src": os.path.join(ROOT, "images", f"{t_obj['car']}_{t_obj['bg']}.jpg"),
            "code": code,
            "cluster": cl_label,
            "title": ogp_title,
            "subtitle": "28問に答えて、このタイプとの相性％＆相性コメントをチェックしよう！",
            "accent": accent,
        })
        for c in cars:
            cid = c["id"]
            jobs.append({
                "kind": "type",
                "out": os.path.join(ogp_dir, f"{code}_{cid}.jpg"),
                "src": os.path.join(ROOT, "images", f"{cid}_{t_obj['bg']}.jpg"),
                "code": code,
                "cluster": f"{cl_label} | {c['short']}",
                "title": ogp_title,
                "subtitle": t_obj["catch"],
                "accent": accent,
            })

    render_all_ogp(jobs)

    # 2. Generate share/*.html, vs/*.html, types/*.html
    for code, t_obj in types.items():
        cl_obj = clusters[t_obj["cluster"]]
        accent = CLUSTER_ACCENTS[t_obj["cluster"]]
        jp_name = t_obj["name"]

        with open(os.path.join(share_dir, f"{code}.html"), "w", encoding="utf-8") as f:
            f.write(build_share_html(code, jp_name, site_url))
        with open(os.path.join(vs_dir, f"{code}.html"), "w", encoding="utf-8") as f:
            f.write(build_vs_html(code, jp_name, site_url, ga_snippet))
        with open(os.path.join(types_dir, f"{code}.html"), "w", encoding="utf-8") as f:
            f.write(build_type_seo_html(code, t_obj, cl_obj, types, accent, site_url, ga_snippet))

        for c in cars:
            cid = c["id"]
            with open(os.path.join(share_dir, f"{code}_{cid}.html"), "w", encoding="utf-8") as f:
                f.write(build_share_html(code, jp_name, site_url, f"_{cid}"))

    # 3. Generate standalone legal pages, sitemap.xml & robots.txt
    for kind in ("privacy", "terms"):
        with open(os.path.join(ROOT, f"{kind}.html"), "w", encoding="utf-8") as f:
            f.write(build_legal_page(kind, site_url, ga_snippet))

    urls = [f"{site_url}/"] + [f"{site_url}/types/{code}.html" for code in types.keys()] + [f"{site_url}/privacy.html", f"{site_url}/terms.html"]
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        sitemap_xml += f"  <url><loc>{u}</loc></url>\n"
    sitemap_xml += "</urlset>\n"
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap_xml)
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {site_url}/sitemap.xml\n")

    # 4. Safely update index.html metadata, GA4, and SITE_URL constant only
    index_html = re.sub(
        r'<!-- GA4_INJECT_START -->.*?<!-- GA4_INJECT_END -->',
        f'<!-- GA4_INJECT_START -->{ga_snippet}<!-- GA4_INJECT_END -->',
        index_html,
        flags=re.DOTALL,
    )
    index_html = re.sub(r'(<meta property="og:url" content=")[^"]+(")', rf'\g<1>{site_url}/\g<2>', index_html)
    index_html = re.sub(r'(<link rel="canonical" href=")[^"]+(")', rf'\g<1>{site_url}/\g<2>', index_html)
    index_html = re.sub(r'(<meta property="og:image" content=")[^"]+(")', rf'\g<1>{site_url}/ogp.jpg?v=5\g<2>', index_html)
    index_html = re.sub(r'(<meta name="twitter:image" content=")[^"]+(")', rf'\g<1>{site_url}/ogp.jpg?v=5\g<2>', index_html)
    index_html = re.sub(r'const SITE_URL = "[^"]*";', f'const SITE_URL = "{site_url}";', index_html, count=1)

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(index_html)

    n_share = len(types) * (1 + len(cars))
    print(f"OK: Generated {len(jobs)} OGP images, {n_share} share pages, {len(types)} vs pages, {len(types)} SEO type pages + privacy/terms for {site_url}")


if __name__ == "__main__":
    main()
