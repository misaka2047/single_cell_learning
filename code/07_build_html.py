"""Convert REPORT.md to a self-contained, printable HTML page.

Images stay as relative links, so keep REPORT.html next to the figures/ folder.
"""
from __future__ import annotations

from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
md_text = (ROOT / "REPORT.md").read_text(encoding="utf-8")
body = markdown.markdown(
    md_text,
    extensions=["tables", "fenced_code", "toc", "sane_lists", "attr_list"],
    extension_configs={"toc": {"permalink": False}},
)

CSS = """
:root { --ink:#1f2933; --muted:#5f6b7a; --line:#d9e2ec; --accent:#0b6e99; --bg:#f7f9fb; }
* { box-sizing: border-box; }
body {
  margin: 0; padding: 0; background: var(--bg); color: var(--ink);
  font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC",
               "Source Han Sans SC", -apple-system, BlinkMacSystemFont,
               "Segoe UI", sans-serif;
  line-height: 1.85; font-size: 16px;
}
.page {
  max-width: 1080px; margin: 0 auto; padding: 42px 54px 80px;
  background: #fff; box-shadow: 0 0 0 1px rgba(0,0,0,.04);
}
h1 { font-size: 30px; line-height: 1.35; margin: 0 0 14px; color: #12344d; }
h2 { font-size: 23px; margin: 42px 0 12px; padding-bottom: 6px;
     border-bottom: 2px solid var(--line); color: #12344d; }
h3 { font-size: 18px; margin: 28px 0 8px; color: #1d4e6b; }
h4 { font-size: 16px; margin: 20px 0 6px; }
p { margin: 10px 0; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
blockquote {
  margin: 16px 0; padding: 12px 18px; background: #eef7fb;
  border-left: 4px solid var(--accent); color: #24495e;
}
blockquote p { margin: 4px 0; }
img { display: block; max-width: 100%; height: auto; margin: 18px auto 6px;
      border: 1px solid var(--line); border-radius: 6px; background: #fff; }
table { border-collapse: collapse; width: 100%; margin: 16px 0 22px;
        font-size: 14px; }
th, td { border: 1px solid var(--line); padding: 7px 10px; vertical-align: top; }
th { background: #eef3f7; text-align: left; }
tr:nth-child(even) td { background: #fbfcfd; }
code { font-family: Consolas, "SFMono-Regular", Menlo, monospace;
       background: #f1f4f6; padding: 1px 5px; border-radius: 4px; font-size: 13px; }
pre { background: #0f1720; color: #e6edf3; padding: 15px 18px; border-radius: 8px;
      overflow-x: auto; line-height: 1.55; }
pre code { background: transparent; color: inherit; padding: 0; font-size: 13px; }
ul, ol { padding-left: 26px; }
li { margin: 4px 0; }
hr { border: none; border-top: 1px solid var(--line); margin: 30px 0; }
.toc { background: #f8fafc; border: 1px solid var(--line); border-radius: 8px;
       padding: 12px 20px 12px 26px; margin: 18px 0 8px; font-size: 14px; }
.toc ul { margin: 4px 0; padding-left: 20px; }
.toc > ul { padding-left: 6px; }
.toc li { margin: 2px 0; }
.small { color: var(--muted); font-size: 13px; }
@media print {
  body { background: #fff; }
  .page { box-shadow: none; max-width: none; padding: 0; }
  h2 { page-break-after: avoid; }
  img, table { page-break-inside: avoid; }
}
"""

html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>从公共数据到可复现结论：人类胰岛单细胞图谱与 T2D 再分析</title>
<style>{CSS}</style>
</head>
<body>
<div class="page">
{body}
<hr>
<p class="small">本页由 REPORT.md 自动生成。代码、结果表与图片均在本目录中；
数据分析使用 Python / Scanpy。公共数据的使用请遵守 GEO/NCBI 条款并引用原始论文。</p>
</div>
</body>
</html>
"""

(ROOT / "REPORT.html").write_text(html, encoding="utf-8")
print("wrote", ROOT / "REPORT.html", len(html), "chars")
