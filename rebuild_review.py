"""レビューページを再生成するスクリプト（GitHub API直接呼び出し方式）"""
from pathlib import Path
from build import parse_article_file, markdown_to_html

TEMPLATE_HEAD = """<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>REVIEW: {title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:'Helvetica Neue','Noto Sans JP',sans-serif;background:#fff;color:#333;line-height:1.9;font-size:16px;}}
.bar{{background:#f59e0b;color:#fff;padding:10px 16px;font-size:0.85em;text-align:center;position:sticky;top:0;z-index:100;}}
article{{max-width:720px;margin:0 auto;padding:24px 16px;padding-bottom:80px;}}
h1{{font-size:1.4em;line-height:1.4;margin-bottom:16px;color:#1e3a5f;}}
h2{{font-size:1.15em;margin:28px 0 12px;padding-bottom:6px;border-bottom:2px solid #e2e8f0;color:#1e3a5f;}}
h3{{font-size:1em;margin:20px 0 8px;color:#334155;}}
p{{margin-bottom:12px;}}
ul{{margin:12px 0;padding-left:20px;}}
li{{margin-bottom:6px;}}
a{{color:#2563eb;}}
blockquote{{border-left:3px solid #2563eb;padding:8px 12px;margin:12px 0;background:#f0f4ff;font-size:0.9em;}}
table{{width:100%;border-collapse:collapse;margin:12px 0;font-size:0.8em;}}
th{{background:#f0f4ff;padding:6px 8px;text-align:left;border:1px solid #e2e8f0;}}
td{{padding:6px 8px;border:1px solid #e2e8f0;}}
strong{{color:#1e3a5f;}}
hr{{border:none;border-top:1px solid #e2e8f0;margin:20px 0;}}
.back{{display:block;text-align:center;padding:16px;color:#2563eb;text-decoration:none;}}
</style></head><body>
<div class="bar">REVIEW MODE - 未承認・確認用プレビュー</div>
<article>{content}</article>
<a href="index.html" class="back">&larr; 一覧に戻る</a>
"""

FLOATING_JS = """
<div id="reviewToggle" onclick="togglePanel()" style="position:fixed;bottom:20px;right:20px;background:#f59e0b;color:#fff;width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.5em;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,0.3);z-index:200;">&#9998;</div>

<div id="reviewPanel" style="display:none;position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:3px solid #f59e0b;padding:16px;z-index:199;max-height:60vh;overflow-y:auto;box-shadow:0 -4px 20px rgba(0,0,0,0.15);">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
<h3 style="font-size:1em;color:#1e293b;">レビュー</h3>
<button onclick="togglePanel()" style="background:none;border:none;font-size:1.3em;cursor:pointer;">&#10005;</button>
</div>
<div style="font-size:0.85em;margin-bottom:8px;">
<label style="display:block;padding:4px 0;"><input type="checkbox"> 参考文献あり</label>
<label style="display:block;padding:4px 0;"><input type="checkbox"> アフィリエイト開示あり</label>
<label style="display:block;padding:4px 0;"><input type="checkbox"> 事実/推測が分離</label>
<label style="display:block;padding:4px 0;"><input type="checkbox"> 料金に出典あり</label>
<label style="display:block;padding:4px 0;"><input type="checkbox"> 景表法リスクなし</label>
<label style="display:block;padding:4px 0;"><input type="checkbox"> 内容に誤りなし</label>
</div>
<textarea id="feedback" placeholder="指摘事項を入力..." style="width:100%;height:60px;border:1px solid #e2e8f0;border-radius:8px;padding:8px;font-size:0.9em;resize:none;font-family:inherit;"></textarea>
<div style="display:flex;gap:6px;margin-top:8px;">
<button class="rbtn" style="background:#10b981;" onclick="doAction('approve')">承認</button>
<button class="rbtn" style="background:#2563eb;" onclick="doAction('fix')">AI修正</button>
<button class="rbtn" style="background:#ef4444;" onclick="doAction('reject')">差戻し</button>
</div>
<div id="result" style="margin-top:8px;font-size:0.85em;"></div>
</div>

<style>.rbtn{flex:1;padding:10px;border:none;border-radius:8px;font-size:0.85em;cursor:pointer;font-weight:600;color:#fff;}.rbtn:disabled{opacity:0.5;}</style>

<script>
var ARTICLE_ID = "__SLUG__";
var TOKEN = localStorage.getItem("gh_token") || "";

function togglePanel() {
  var p = document.getElementById("reviewPanel");
  var t = document.getElementById("reviewToggle");
  if (p.style.display === "none") { p.style.display = "block"; t.style.display = "none"; }
  else { p.style.display = "none"; t.style.display = "flex"; }
}

async function doAction(action) {
  if (!TOKEN) {
    TOKEN = prompt("GitHub Personal Access Token を入力（初回のみ・ブラウザに保存されます）:");
    if (!TOKEN) return;
    localStorage.setItem("gh_token", TOKEN);
  }
  var feedback = document.getElementById("feedback").value;
  if (action === "fix" && !feedback.trim()) { alert("指摘事項を入力してください"); return; }
  if (action === "approve" && !confirm("この記事を承認しますか？")) return;

  var btns = document.querySelectorAll(".rbtn");
  btns.forEach(function(b){ b.disabled = true; });
  var result = document.getElementById("result");
  result.innerHTML = '<div style="color:#2563eb;">GitHub Actions を実行中...</div>';

  try {
    var resp = await fetch(
      "https://api.github.com/repos/yangpinggaoye15-dotcom/ai-tools-lab/actions/workflows/review-action.yml/dispatches",
      {
        method: "POST",
        headers: {
          "Authorization": "Bearer " + TOKEN,
          "Accept": "application/vnd.github.v3+json",
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          ref: "main",
          inputs: { article_id: ARTICLE_ID, action: action, feedback: feedback || "" }
        })
      }
    );
    if (resp.status === 204) {
      var msgs = { approve: "承認しました", fix: "AI修正を開始しました", reject: "差戻ししました" };
      result.innerHTML = '<div style="color:#10b981;font-weight:600;">' + msgs[action] + '</div><div style="color:#666;font-size:0.8em;margin-top:4px;">GitHub Actionsで処理中（1-2分）</div>';
    } else if (resp.status === 401 || resp.status === 403) {
      localStorage.removeItem("gh_token");
      TOKEN = "";
      result.innerHTML = '<div style="color:#ef4444;">トークンが無効です。再度お試しください。</div>';
      btns.forEach(function(b){ b.disabled = false; });
    } else {
      result.innerHTML = '<div style="color:#ef4444;">エラー(' + resp.status + ')</div>';
      btns.forEach(function(b){ b.disabled = false; });
    }
  } catch(e) {
    result.innerHTML = '<div style="color:#ef4444;">' + e.message + '</div>';
    btns.forEach(function(b){ b.disabled = false; });
  }
}
</script>
"""

articles_dir = Path("../affiliate-generator/output")
review_dir = Path("review")

slugs = {
    "AI文章作成ツール": "ai-writing-comparison",
    "ChatGPT": "chatgpt-alternatives",
    "AI画像生成": "ai-image-generators",
    "AIコード生成": "ai-code-generators",
    "AI動画編集": "ai-video-editors",
    "server_comparison": "server-comparison",
    "vpn_comparison": "vpn-comparison",
    "AIライティング": "ai-writing-tools",
}

for md_file in sorted(articles_dir.glob("20260329_*.md")) + sorted(articles_dir.glob("20260330_*.md")):
    slug = None
    for kw, s in slugs.items():
        if kw in md_file.name:
            slug = s
            break
    if not slug:
        continue

    article = parse_article_file(md_file)
    body_html = markdown_to_html(article["body"])
    title = article["meta"].get("title", slug)

    html = TEMPLATE_HEAD.format(title=title, content=body_html)
    html += FLOATING_JS.replace("__SLUG__", slug)
    html += "</body></html>"

    out = review_dir / f"{slug}.html"
    out.write_text(html, encoding="utf-8")
    print(f"  Built: {out}")

print("Done")
