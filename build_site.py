"""Build the static course website.

Source of truth:
  site/content/*.md      chapter text (with a tiny front matter)
  site/assets/style.css  visual design
  site/assets/app.js     progress / search / copy interactions
  figures/*.png          analysis figures

Output:
  site/index.html
  site/chapters/*.html
  site/code.html
  site/full-report.html
  site/code/*.py
  site/figures/*.png
  site/downloads/single-cell-tutorial-code.zip
"""
from __future__ import annotations

import html as html_lib
import json
import re
import shutil
import zipfile
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
CONTENT = SITE / "content"
ASSETS = SITE / "assets"
CHAPTERS_DIR = SITE / "chapters"
FIG_DIR = SITE / "figures"
CODE_DIR = SITE / "code"
DOWNLOADS = SITE / "downloads"

FIGURES = [
    "baron_qc_violin.png",
    "gse81608_qc_genes.png",
    "baron_umap_overview.png",
    "baron_umap_annotated.png",
    "baron_dotplot_celltype.png",
    "baron_composition_by_donor.png",
    "baron_beta_fraction.png",
    "gse81608_umap_overview.png",
    "gse81608_composition.png",
    "de_method_comparison.png",
    "gse81608_pvalue_diagnostics.png",
    "gse81608_beta_selected_genes.png",
]

CODE_FILES = [
    ("00_prepare_data.py", "把 GEO CSV/RPKM 读成 AnnData，补 metadata，映射基因 ID"),
    ("01_baron_cluster.py", "GSE84133：QC、归一化、HVG、PCA、UMAP、Leiden"),
    ("02_baron_annotate.py", "GSE84133：marker 注释、ARI、细胞组成"),
    ("03_gse81608_cluster.py", "GSE81608：QC、log2、聚类"),
    ("04_gse81608_de.py", "GSE81608：注释、pseudobulk DE、阳性/阴性对照"),
    ("05_report_figures.py", "生成汇总指标和三种 DE 方法对照图"),
    ("06_session_info.py", "记录软件版本"),
    ("07_build_html.py", "把 REPORT.md 转成独立的完整 HTML 报告"),
    ("download_ranges.py", "多线程 HTTP Range 下载 gzip"),
    ("run_all.ps1", "Windows 一键按顺序运行"),
]

# Single source of truth for hover definitions and the glossary page.
# Keep definitions to 1-2 short sentences: they are tooltips, not a textbook.
GLOSSARY = [
    # data / formats
    dict(term="scRNA-seq", aliases=["single-cell RNA-seq", "scRNAseq", "scRNA seq"],
         category="数据与格式",
         definition="单细胞 RNA 测序：逐个细胞测量转录组，用来分辨细胞类型、状态和组间差异。"),
    dict(term="UMI", aliases=["UMIs", "unique molecular identifier"],
         category="数据与格式",
         definition="唯一分子标识符：建库时给每条原始 RNA 分子加标签，用于去重和估计真实分子数。"),
    dict(term="AnnData", aliases=["anndata"],
         category="数据与格式",
         definition="Python 单细胞数据结构：X 存表达矩阵，obs 存细胞注释，var 存基因注释，layers/obsm 存原始值和降维结果。"),
    dict(term="counts", aliases=["count matrix", "raw counts", "计数矩阵"],
         category="数据与格式",
         definition="原始计数矩阵：每个基因在每个细胞中检测到的 UMI/reads 数，尚未归一化。"),
    dict(term="RPKM/TPM", aliases=["RPKM", "TPM"],
         category="数据与格式",
         definition="已按基因长度和测序深度归一化的表达量；GSE81608 使用 RPKM，不能再做 CP10k。"),
    dict(term="metadata", aliases=["meta data", "元数据"],
         category="数据与格式",
         definition="样本/细胞注释信息：供者、分组、年龄、性别、BMI、批次等；分组错位是最常见的事故。"),
    dict(term="供者", aliases=["donor", "donors"],
         category="数据与格式",
         definition="提供样本的个体。在疾病比较中，供者才是生物学重复，不是细胞。"),
    dict(term="批次效应", aliases=["batch", "batch effect", "批次"],
         category="数据与格式",
         definition="不同时间、建库、测序或中心带来的技术差异；可能与疾病分组共线，无法单独校正。"),
    dict(term="稀疏矩阵", aliases=["sparse matrix", "sparse"],
         category="数据与格式",
         definition="只存非零值的矩阵；单细胞数据通常 85% 以上为 0，用稀疏存储可省大量内存。"),
    dict(term="Entrez GeneID", aliases=["Entrez", "GeneID"],
         category="数据与格式",
         definition="NCBI 基因数字 ID；GSE81608 第一列是它，需要映射到基因 symbol 才能做 marker/富集。"),
    # QC / preprocessing
    dict(term="QC", aliases=["quality control", "质控"],
         category="预处理与质控",
         definition="质控：按检测基因数、UMI、线粒体比例、双细胞等指标过滤低质量细胞。"),
    dict(term="nGene", aliases=["detected genes", "检测基因数"],
         category="预处理与质控",
         definition="每个细胞检测到的基因数；过低提示空液滴/死细胞，过高提示双细胞。"),
    dict(term="线粒体比例", aliases=["mito%", "mitochondrial fraction", "线粒体"],
         category="预处理与质控",
         definition="线粒体基因 counts 占总 counts 的比例；过高提示细胞应激/死亡。本数据无 MT- 基因，无法计算。"),
    dict(term="双细胞", aliases=["doublet", "doublets"],
         category="预处理与质控",
         definition="两个细胞被同一液滴包住，表达谱是两种细胞的混合；会形成假簇/假 marker。"),
    dict(term="环境 RNA", aliases=["ambient RNA", "ambient"],
         category="预处理与质控",
         definition="细胞裂解后释放、被其他液滴捕获的 RNA；会让所有细胞都“表达”某些基因。"),
    dict(term="空液滴", aliases=["empty droplet", "empty droplets"],
         category="预处理与质控",
         definition="没有细胞、只含少量游离 RNA 的液滴；应在 QC 中用 EmptyDrops 等方法剔除。"),
    dict(term="归一化", aliases=["normalization", "normalisation"],
         category="预处理与质控",
         definition="消除测序深度/基因长度差异，让不同细胞可比；counts 用 CP10k，RPKM 只做 log。"),
    dict(term="CP10k", aliases=["CPM", "counts per 10k"],
         category="预处理与质控",
         definition="counts per 10,000：把每个细胞的 counts 缩放到 1 万，再做 log1p；只适用于 counts。"),
    dict(term="log1p", aliases=["log2(x+1)", "log(x+1)"],
         category="预处理与质控",
         definition="log(1+x) 变换：压缩表达量、避免 log(0)，让高表达基因不主导 PCA。"),
    dict(term="HVG", aliases=["highly variable genes", "高变基因", "HVGs"],
         category="预处理与质控",
         definition="高变基因：在细胞间变异大的基因，用于 PCA/聚类；本教程选 2,000 个。"),
    dict(term="scaling", aliases=["scale", "z-score", "标准化"],
         category="预处理与质控",
         definition="对每个基因做 z-score（减均值、除标准差），常截断到 ±10；会把稀疏矩阵变稠密。"),
    # dim reduction / clustering
    dict(term="PCA", aliases=["principal component analysis", "主成分分析"],
         category="降维与聚类",
         definition="主成分分析：把高维表达压到少数正交主成分，保留主要变异。"),
    dict(term="kNN", aliases=["k-nearest neighbors", "k 近邻", "k-nearest neighbours"],
         category="降维与聚类",
         definition="k 近邻：每个细胞找最相似的 k 个细胞，构建细胞相似图；Leiden 在这张图上聚类。"),
    dict(term="UMAP", aliases=["Uniform Manifold Approximation and Projection"],
         category="降维与聚类",
         definition="非线性降维可视化：保留局部邻接，适合看细胞群；全局距离/簇间距离不可靠。"),
    dict(term="Leiden", aliases=["Leiden clustering", "Leiden 聚类"],
         category="降维与聚类",
         definition="图聚类算法：在 kNN 图上找社区，resolution 控制簇的粗细。"),
    dict(term="resolution", aliases=["分辨率"],
         category="降维与聚类",
         definition="Leiden 的粒度参数：越大簇越多/越细；不是细胞类型数，需 marker 注释后合并。"),
    dict(term="批次校正", aliases=["batch correction", "integration", "整合"],
         category="降维与聚类",
         definition="让同一细胞类型跨批次对齐；Harmony/ComBat/scVI/BBKNN 都是常见方法，但分组与批次共线时可能过校正。"),
    dict(term="Harmony", aliases=["harmony"],
         category="降维与聚类",
         definition="基于 PCA 的迭代批次整合方法，常用于多样本 scRNA-seq；不改变原始表达矩阵。"),
    dict(term="ComBat", aliases=["combat"],
         category="降维与聚类",
         definition="基于经验贝叶斯的批次校正，直接校正表达矩阵；可能把真实生物学差异一起校正掉。"),
    dict(term="scVI", aliases=["scvi"],
         category="降维与聚类",
         definition="变分自编码器模型，可做批次整合、降维和差异表达；需要 counts 和一定计算资源。"),
    dict(term="BBKNN", aliases=["bbknn"],
         category="降维与聚类",
         definition="批次平衡 kNN：在每个批次内找邻居再合并，构建整合图；适合多样本聚类。"),
    # annotation
    dict(term="marker gene", aliases=["marker", "标记基因"],
         category="注释与验证",
         definition="标记基因：某细胞类型高表达、其他类型低表达的基因，用来注释细胞类型。"),
    dict(term="dotplot", aliases=["dot plot", "点图"],
         category="注释与验证",
         definition="点图：点大小=表达该基因的细胞比例，颜色=组内平均表达；常用于检查 marker。"),
    dict(term="细胞类型注释", aliases=["cell type annotation", "cell annotation"],
         category="注释与验证",
         definition="用 marker/参考标签给簇命名；是有置信度的假说，不是绝对真理。"),
    dict(term="ARI", aliases=["adjusted Rand index", "调整兰德指数"],
         category="注释与验证",
         definition="调整兰德指数：比较两种分组的一致性，1=完全一致，0≈随机；对稀有类型不敏感。"),
    dict(term="label transfer", aliases=["标签转移"],
         category="注释与验证",
         definition="用参考图谱的标签映射到新数据；依赖参考的细胞类型覆盖和批次相似性。"),
    # statistics / DE
    dict(term="pseudobulk", aliases=["伪批量", "pseudo-bulk"],
         category="统计与差异表达",
         definition="伪批量：把同一供者/样本的细胞聚合后再做 DE，避免把细胞当独立重复。"),
    dict(term="伪重复", aliases=["pseudoreplication", "pseudo-replication"],
         category="统计与差异表达",
         definition="把同一供者的细胞当独立样本，低估标准误、夸大显著性；单细胞 DE 最常见的错误。"),
    dict(term="差异表达", aliases=["DE", "differential expression"],
         category="统计与差异表达",
         definition="比较两组间基因表达均值/比例；本教程用供者水平 pseudobulk，而不是细胞水平 t 检验。"),
    dict(term="FDR", aliases=["false discovery rate", "错误发现率"],
         category="统计与差异表达",
         definition="错误发现率：多重检验校正后，被判为显著的基因中预期假阳性的比例。"),
    dict(term="BH", aliases=["Benjamini-Hochberg", "Benjamini–Hochberg"],
         category="统计与差异表达",
         definition="Benjamini-Hochberg：最常用的 FDR 校正方法；本教程用 BH 校正所有检验基因。"),
    dict(term="log2FC", aliases=["log2 fold change", "log2 倍数变化"],
         category="统计与差异表达",
         definition="log2 倍数变化：效应量，T2D 与对照的表达比值取 log2；比 p 值更能说明差异大小。"),
    dict(term="效应量", aliases=["effect size"],
         category="统计与差异表达",
         definition="差异的大小（如 log2FC、Cohen's d），与 p 值不同；大 n 下微小效应也可能显著。"),
    dict(term="置信区间", aliases=["confidence interval", "CI"],
         category="统计与差异表达",
         definition="效应量的不确定性范围；比单个 p 值更能说明估计的精度。"),
    dict(term="协变量", aliases=["covariate", "covariates"],
         category="统计与差异表达",
         definition="模型中调整的变量，如年龄、性别、BMI、批次；目的是控制混杂。"),
    dict(term="混杂因素", aliases=["confounder", "confounding", "混杂"],
         category="统计与差异表达",
         definition="同时与分组和结局相关，可能制造假关联；疾病与批次共线时尤其危险。"),
    dict(term="检验效能", aliases=["power", "statistical power"],
         category="统计与差异表达",
         definition="真实效应存在时检出它的概率；取决于样本量、效应量和噪声。16 名供者对中等效应可能不足。"),
    dict(term="混合模型", aliases=["mixed model", "mixed-effects model"],
         category="统计与差异表达",
         definition="含固定效应和随机效应（如供者随机截距）的模型，用来处理同一供者细胞的相关性。"),
    dict(term="DESeq2", aliases=["deseq2"],
         category="统计与差异表达",
         definition="基于负二项分布的 bulk RNA-seq DE 方法；常用于 pseudobulk counts。"),
    dict(term="limma-voom", aliases=["limma voom", "voom"],
         category="统计与差异表达",
         definition="线性模型 + voom 权重，常用于 bulk/pseudobulk counts；对中小样本较稳健。"),
    dict(term="PyDESeq2", aliases=["pydeseq2"],
         category="统计与差异表达",
         definition="DESeq2 的 Python 实现，可用于 pseudobulk counts 的差异表达。"),
    dict(term="成分数据", aliases=["compositional data"],
         category="统计与差异表达",
         definition="各类型比例总和为 1 的数据；普通 t 检验/ANOVA 不完全适用，可用 CLR/ILR、scCODA、propeller。"),
    dict(term="scCODA", aliases=["scCODA"],
         category="统计与差异表达",
         definition="单细胞组成数据的贝叶斯模型，考虑成分性质，用于检验细胞类型比例变化。"),
    dict(term="propeller", aliases=["propeller"],
         category="统计与差异表达",
         definition="基于 log-ratio 的组成数据检验方法，适合细胞类型比例的比较。"),
    # pitfalls / general
    dict(term="double dipping", aliases=["double-dipping", "双重 dipping"],
         category="常见陷阱",
         definition="用同一数据先选特征（如 HVG/DE 基因）再做检验，p 值会偏小；应独立数据或预设特征。"),
    dict(term="P-hacking", aliases=["p-hacking", "p值操纵"],
         category="常见陷阱",
         definition="反复换阈值/模型/协变量直到显著；会破坏结果可信度，应预注册分析计划。"),
    dict(term="ground truth", aliases=["金标准"],
         category="常见陷阱",
         definition="独立验证的真实标签；作者注释通常只是参考，不是严格 ground truth。"),
    dict(term="inDrop", aliases=["indrop"],
         category="常见陷阱",
         definition="液滴微流控 scRNA-seq 平台；GSE84133 使用 inDrop，UMI counts 与 10x 类似但建库不同。"),
]



def parse_chapter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"missing front matter: {path}")
    _, fm, body = text.split("---", 2)
    meta: dict[str, str] = {}
    for line in fm.strip().splitlines():
        if not line.strip():
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    meta["body"] = body.strip()
    meta["file"] = path.name
    return meta


def md(text: str) -> str:
    html = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "md_in_html", "sane_lists", "toc"],
        extension_configs={"toc": {"permalink": False}},
    )
    # Markdown puts a lone image in <p>; wrap image + following caption in
    # <figure> so the caption styling and print page-breaks work.
    html = re.sub(
        r"<p>\s*(<img[^>]+?/?>)\s*</p>\s*<figcaption>(.*?)</figcaption>",
        r"<figure>\1<figcaption>\2</figcaption></figure>",
        html,
        flags=re.S,
    )
    html = re.sub(
        r"<p>\s*(<img[^>]+?/?>)\s*</p>",
        r"<figure>\1</figure>",
        html,
    )
    return html


def strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html).strip()


def chapter_toc(html: str) -> str:
    heads = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', html, flags=re.S)
    if len(heads) < 2:
        return ""
    items = "".join(
        f'<li><a href="#{anchor}">{strip_tags(title)}</a></li>'
        for anchor, title in heads
    )
    return f'<details class="chapter-toc" open><summary>本章内容</summary><ol>{items}</ol></details>'


def read_chapters() -> list[dict]:
    chapters = [parse_chapter(p) for p in sorted(CONTENT.glob("*.md"))]
    chapters.sort(
        key=lambda c: (1, 99)
        if c["num"] == "A"
        else (0, int(c["num"]) if c["num"].isdigit() else 99)
    )
    return chapters


def sidebar(chapters: list[dict], active: str, base: str) -> str:
    items = []
    for c in chapters:
        cls = "chapter-link active" if c["slug"] == active else "chapter-link"
        items.append(
            f'<li><a class="{cls}" data-slug="{c["slug"]}" '
            f'href="{base}chapters/{c["slug"]}.html">'
            f'<span class="nav-num">{c["num"]}</span>'
            f'<span class="nav-title">{c["title"]}</span>'
            f'<span class="nav-dot" aria-hidden="true"></span></a></li>'
        )
    return f"""
<aside class="sidebar" id="sidebar">
  <a class="brand" href="{base}index.html">
    <span class="brand-mark">sc</span>
    <span class="brand-text"><b>单细胞学习站</b><small>从公共数据到可复现结论</small></span>
  </a>
  <div class="side-progress">
    <div class="side-progress-head"><span>学习进度</span><b id="progress-text">0 / {len(chapters)}</b></div>
    <div class="progress-track"><div class="progress-fill" id="progress-fill"></div></div>
  </div>
  <nav class="side-nav" aria-label="课程目录">
    <p class="side-label">课程</p>
    <ol>{''.join(items)}</ol>
    <p class="side-label">资源</p>
    <ul class="resource-list">
      <li><a class="{'active' if active == 'glossary' else ''}" href="{base}glossary.html">术语表（悬停注释）</a></li>
      <li><a href="{base}full-report.html">完整分析报告</a></li>
      <li><a class="{'active' if active == 'code' else ''}" href="{base}code.html">代码与数据</a></li>
      <li><a href="{base}downloads/single-cell-tutorial-code.zip">下载代码包</a></li>
    </ul>
  </nav>
  <div class="side-foot">
    <p>数据：GSE84133 · GSE81608</p>
    <p>Python / Scanpy · 2026</p>
  </div>
</aside>
<div class="sidebar-overlay" id="sidebar-overlay"></div>
"""


def topbar(base: str) -> str:
    return f"""
<header class="topbar">
  <button class="icon-btn menu-btn" id="menu-btn" aria-label="打开目录" aria-expanded="false">☰</button>
  <a class="topbar-brand" href="{base}index.html">scRNA<span>·</span>学习站</a>
  <div class="search-wrap">
    <input id="site-search" type="search" placeholder="搜索章节、关键词…" autocomplete="off" aria-label="搜索">
    <div class="search-results" id="search-results" hidden></div>
  </div>
  <div class="topbar-meta"><span id="topbar-progress">0 / 0</span></div>
</header>
"""


def page_shell(title: str, body: str, chapters: list[dict], active: str,
               base: str, slug: str, description: str = "") -> str:
    glossary_attr = ' data-glossary-page="true"' if slug == "glossary" else ""
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · 单细胞学习站</title>
<meta name="description" content="{description}">
<link rel="stylesheet" href="{base}assets/style.css">
</head>
<body data-base="{base}" data-slug="{slug}"{glossary_attr}>
<a class="skip" href="#main">跳到正文</a>
{topbar(base)}
{sidebar(chapters, active, base)}
<main class="main" id="main">
{body}
<footer class="footer">
  <p>单细胞研究范式入门 · 基于 GSE84133 与 GSE81608 的真实再分析</p>
  <p><a href="{base}glossary.html">术语表</a> · <a href="{base}full-report.html">完整报告</a> · <a href="{base}code.html">代码与数据</a> · <a href="{base}index.html">返回首页</a></p>
</footer>
</main>
<script src="{base}assets/glossary-data.js"></script>
<script src="{base}assets/glossary.js"></script>
<script src="{base}assets/search-index.js"></script>
<script src="{base}assets/app.js"></script>
</body>
</html>
"""


def chapter_page(c: dict, chapters: list[dict]) -> str:
    body_html = md(c["body"])
    toc = chapter_toc(body_html)
    idx = chapters.index(c)
    prev_c = chapters[idx - 1] if idx > 0 else None
    next_c = chapters[idx + 1] if idx + 1 < len(chapters) else None
    pager = []
    if prev_c:
        pager.append(
            f'<a class="pager-link prev" href="../chapters/{prev_c["slug"]}.html">'
            f'<span>上一章</span><b>{prev_c["num"]}. {prev_c["title"]}</b></a>'
        )
    if next_c:
        pager.append(
            f'<a class="pager-link next" href="../chapters/{next_c["slug"]}.html">'
            f'<span>下一章</span><b>{next_c["num"]}. {next_c["title"]}</b></a>'
        )
    body = f"""
<header class="chapter-hero">
  <div class="chapter-kicker">第 {c["num"]} 步 · {c["duration"]}</div>
  <h1>{c["title"]}</h1>
  <p class="chapter-lead">{c["summary"]}</p>
  <p class="gloss-hint">提示：正文中带虚线下划线的术语可悬停（或点击）查看简要解释；完整列表见 <a href="../glossary.html">术语表</a>。</p>
  <div class="chapter-actions">
    <button class="btn btn-primary" id="mark-complete" data-slug="{c["slug"]}">标记本章完成</button>
    <button class="btn btn-ghost" onclick="window.print()">打印本章</button>
  </div>
</header>
<div class="chapter-body">
  {toc}
  <article class="prose">
    {body_html}
  </article>
  <nav class="pager">{''.join(pager)}</nav>
</div>
"""
    return page_shell(
        f'{c["num"]}. {c["title"]}', body, chapters, c["slug"], "../", c["slug"],
        c.get("summary", ""),
    )


def index_page(chapters: list[dict]) -> str:
    cards = []
    for c in chapters:
        cards.append(
            f'<a class="course-card" data-slug="{c["slug"]}" href="chapters/{c["slug"]}.html">'
            f'<div class="course-card-top"><span class="course-num">{c["num"]}</span>'
            f'<span class="course-time">{c["duration"]}</span></div>'
            f'<h3>{c["title"]}</h3><p>{c["short"]}</p>'
            f'<span class="course-state" data-state="{c["slug"]}">未开始</span></a>'
        )
    body = f"""
<section class="hero">
  <div class="hero-inner">
    <div class="hero-copy">
      <p class="eyebrow">医学研究生 · 单细胞入门</p>
      <h1>从公共数据到<br><em>可复现结论</em></h1>
      <p class="hero-lead">12 步 + 附录，把两个真实的人类胰岛公共数据集跑完：QC、聚类、注释、组成分析、pseudobulk 差异表达。每一步都告诉你：做什么、为什么、应该看到什么、结果怎么读。</p>
      <div class="hero-actions">
        <a class="btn btn-primary" href="chapters/paradigm.html">开始第 1 步 →</a>
        <a class="btn btn-ghost" href="full-report.html">先看完整报告</a>
      </div>
      <p class="hero-note">12 步 + 附录 · 预计 6–8 小时 · 可分 3 次完成 · 所有结果均来自本机真实运行</p>
    </div>
    <div class="hero-panel" aria-label="关键结果">
      <div class="hero-stat"><b>8,531</b><span>QC 后细胞</span></div>
      <div class="hero-stat"><b>11</b><span>注释细胞类型</span></div>
      <div class="hero-stat"><b>0 / 9,929</b><span>pseudobulk 显著基因</span></div>
      <div class="hero-stat"><b>3,086</b><span>阳性对照显著基因</span></div>
      <p class="hero-panel-note">0 个不是“失败”：阳性对照证明流程有检验效能。</p>
    </div>
  </div>
</section>

<section class="section">
  <div class="section-head">
    <p class="eyebrow">先看结论</p>
    <h2>这套教程想让你带走的三件事</h2>
  </div>
  <div class="three-grid">
    <div class="info-card"><span class="info-icon">01</span><h3>先定推断单位</h3><p>细胞是观测单位，供者才是生物学重复。把 503 个 β 细胞当独立样本，会得到 1,217 个假阳性。</p></div>
    <div class="info-card"><span class="info-icon">02</span><h3>每一步都有预期</h3><p>细胞数、基因数、聚类数、ARI、显著基因数都给出真实值；对不上时知道从哪里查。</p></div>
    <div class="info-card"><span class="info-icon">03</span><h3>阴性结果也要解释</h3><p>GSE81608 的 T2D 全局差异不可检出；阳性对照和 QQ 图告诉你这不是流程坏了。</p></div>
  </div>
</section>

<section class="section">
  <div class="section-head split">
    <div><p class="eyebrow">课程目录</p><h2>12 步 + 附录，从选题到可复现</h2></div>
    <p class="section-note">建议按顺序；每章末尾有检查点和排错表；正文术语可悬停查看解释。</p>
  </div>
  <div class="course-grid">{''.join(cards)}</div>
</section>

<section class="section">
  <div class="section-head"><p class="eyebrow">数据</p><h2>两个真实数据集，各司其职</h2></div>
  <div class="dataset-grid">
    <article class="dataset-card">
      <div class="dataset-tag">发现 · 图谱</div>
      <h3>GSE84133</h3>
      <p class="dataset-sub">Baron et al., Cell Systems 2016</p>
      <ul><li>4 名供者，8,569 个细胞</li><li>inDrop UMI counts，20,125 个基因</li><li>3 对照 + 1 T2D：只做图谱，不做疾病比较</li></ul>
      <a class="text-link" href="chapters/download.html">看下载与处理 →</a>
    </article>
    <article class="dataset-card">
      <div class="dataset-tag alt">验证 · 疾病</div>
      <h3>GSE81608</h3>
      <p class="dataset-sub">Xin et al., Cell Metabolism 2016</p>
      <ul><li>18 名供者（12 对照 / 6 T2D）</li><li>1,600 个 α/β/δ/PP 细胞，RPKM</li><li>503 个 β 细胞；16 名供者用于 pseudobulk</li></ul>
      <a class="text-link" href="chapters/de.html">看差异表达 →</a>
    </article>
  </div>
</section>

<section class="section">
  <div class="section-head"><p class="eyebrow">怎么用</p><h2>不要一口气读完，按“做—对—读”循环</h2></div>
  <div class="how-grid">
    <div><b>1. 读目标</b><p>先看本章“要做什么”和“为什么”，不要先复制代码。</p></div>
    <div><b>2. 跟着做</b><p>在项目根目录执行命令；每段代码都能在 <a href="code.html">代码与数据</a> 找到完整文件。</p></div>
    <div><b>3. 对预期</b><p>把终端输出/图与“预期结果”对照；对不上先看排错表，不要继续往下跑。</p></div>
    <div><b>4. 做检查点</b><p>能用自己的话回答检查点，再点“标记本章完成”。</p></div>
  </div>
</section>

<section class="section cta-section">
  <div>
    <p class="eyebrow">准备好了吗</p>
    <h2>先写清楚你的问题，再打开数据。</h2>
    <p>第 1 步不写代码：用一句话说清楚“在什么组织、什么细胞、比较什么、推断单位是什么”。</p>
  </div>
  <a class="btn btn-primary" href="chapters/paradigm.html">进入第 1 步 →</a>
</section>
"""
    return page_shell("单细胞研究范式入门", body, chapters, "index", "", "index",
                      "面向医学研究生的单细胞公共数据逐步复现教程")


CATEGORY_ORDER = [
    "数据与格式",
    "预处理与质控",
    "降维与聚类",
    "注释与验证",
    "统计与差异表达",
    "常见陷阱",
]


def glossary_page(chapters: list[dict]) -> str:
    groups: dict[str, list[dict]] = {c: [] for c in CATEGORY_ORDER}
    for g in GLOSSARY:
        groups.setdefault(g["category"], []).append(g)

    sections = []
    for cat in CATEGORY_ORDER:
        items = groups.get(cat, [])
        if not items:
            continue
        cards = []
        for g in items:
            aliases = [a for a in g.get("aliases", []) if a.lower() != g["term"].lower()]
            alias_html = ""
            if aliases:
                alias_html = (
                    '<p class="gloss-alias">也写作：'
                    + "、".join(html_lib.escape(a) for a in aliases[:4])
                    + "</p>"
                )
            cards.append(
                f'<div class="gloss-entry" data-term="{html_lib.escape(g["term"])}" '
                f'data-keywords="{html_lib.escape(" ".join([g["term"], *aliases, g["definition"]]))}">'
                f'<h3>{html_lib.escape(g["term"])}</h3>'
                f'<p>{html_lib.escape(g["definition"])}</p>{alias_html}</div>'
            )
        sections.append(
            f'<section class="glossary-cat"><div class="glossary-cat-head">'
            f'<h2>{cat}</h2><span>{len(items)} 个</span></div>'
            f'<div class="glossary-grid">{"".join(cards)}</div></section>'
        )

    body = f"""
<header class="chapter-hero">
  <div class="chapter-kicker">术语表 · {len(GLOSSARY)} 个词条</div>
  <h1>不熟悉的词，悬停就能看</h1>
  <p class="chapter-lead">网站正文中第一次出现的专业术语会带虚线下划线；把鼠标移上去（或点击/键盘聚焦）即可看到一句话解释。下面是完整列表，也可以直接搜索。</p>
  <div class="chapter-actions">
    <a class="btn btn-primary" href="chapters/paradigm.html">回到第 1 步</a>
    <a class="btn btn-ghost" href="chapters/appendix.html">附录速查</a>
  </div>
</header>
<div class="glossary-tools">
  <input id="glossary-search" type="search" placeholder="搜索术语、缩写或中文解释…" autocomplete="off" aria-label="搜索术语">
  <span id="glossary-count">{len(GLOSSARY)} 个词条</span>
</div>
<div class="glossary-body">
  {''.join(sections)}
</div>
"""
    return page_shell("术语表", body, chapters, "glossary", "", "glossary",
                      "单细胞分析常见术语与缩写的中文速查表")


def code_page(chapters: list[dict]) -> str:
    rows = "".join(
        f'<tr><td><a href="code/{name}">{name}</a></td><td>{desc}</td></tr>'
        for name, desc in CODE_FILES
    )
    body = f"""
<header class="chapter-hero">
  <div class="chapter-kicker">资源</div>
  <h1>代码与数据</h1>
  <p class="chapter-lead">网站里的每个数字都来自这些脚本的真实运行。建议先读章节，再打开对应脚本；不要直接跑完所有代码而不看中间输出。</p>
  <div class="chapter-actions">
    <a class="btn btn-primary" href="downloads/single-cell-tutorial-code.zip">下载代码包（不含原始数据）</a>
    <a class="btn btn-ghost" href="full-report.html">完整报告</a>
  </div>
</header>
<div class="chapter-body">
  <article class="prose">
    <div class="callout note" markdown="1">
**数据不在压缩包里。** 原始 GEO 文件约 60 MB，需按 [数据说明](code/DATA_README.md) 的 URL 下载；压缩包只含脚本、说明和报告。
    </div>
    <h2>脚本地图</h2>
    <table><thead><tr><th>文件</th><th>作用</th></tr></thead><tbody>{rows}</tbody></table>
    <h2>运行顺序</h2>
    <pre><code>python -m pip install -r requirements.txt
$env:NUMBA_DISABLE_INTEL_SVML = "1"   # Windows 兼容性 workaround

python code/00_prepare_data.py
python code/01_baron_cluster.py
python code/02_baron_annotate.py
python code/03_gse81608_cluster.py
python code/04_gse81608_de.py
python code/05_report_figures.py
python code/06_session_info.py</code></pre>
    <h2>你需要准备什么</h2>
    <ul>
      <li>Python 3.11–3.13；按 <code>requirements.txt</code> 安装依赖。</li>
      <li>至少 4 GB 内存；本教程的 h5ad 中间文件合计约 1.2 GB。</li>
      <li>能访问 NCBI FTP；下载慢时用 <code>code/download_ranges.py</code>。</li>
    </ul>
    <div class="callout warn" markdown="1">
**不要跳过 metadata 核对。** 分组、供者、细胞数对不上时，后面的所有图和统计都会错；先读 `GSE*_series_matrix.txt.gz` 的 `!Sample_characteristics_ch1`。
    </div>
  </article>
</div>
"""
    return page_shell("代码与数据", body, chapters, "code", "", "code",
                      "本教程的全部可复现代码与数据说明")


def build() -> None:
    for d in (CHAPTERS_DIR, FIG_DIR, CODE_DIR, DOWNLOADS):
        d.mkdir(parents=True, exist_ok=True)

    chapters = read_chapters()
    print("chapters:", [(c["num"], c["slug"]) for c in chapters])

    # copy figures
    for name in FIGURES:
        src = ROOT / "figures" / name
        if src.exists():
            shutil.copy2(src, FIG_DIR / name)
        else:
            print("WARNING missing figure:", src)

    # copy code
    for p in (ROOT / "code").glob("*.py"):
        shutil.copy2(p, CODE_DIR / p.name)
    if (ROOT / "code" / "run_all.ps1").exists():
        shutil.copy2(ROOT / "code" / "run_all.ps1", CODE_DIR / "run_all.ps1")
    shutil.copy2(ROOT / "requirements.txt", CODE_DIR / "requirements.txt")

    # copy data/results readmes
    if (ROOT / "data" / "README.md").exists():
        shutil.copy2(ROOT / "data" / "README.md", CODE_DIR / "DATA_README.md")
    if (ROOT / "results" / "README.md").exists():
        shutil.copy2(ROOT / "results" / "README.md", CODE_DIR / "RESULTS_README.md")

    # pages
    for c in chapters:
        html = chapter_page(c, chapters)
        (CHAPTERS_DIR / f'{c["slug"]}.html').write_text(html, encoding="utf-8")
        print("wrote", c["slug"])

    (SITE / "index.html").write_text(index_page(chapters), encoding="utf-8")
    (SITE / "glossary.html").write_text(glossary_page(chapters), encoding="utf-8")
    (SITE / "code.html").write_text(code_page(chapters), encoding="utf-8")

    # full report: copy the standalone HTML, but add a back link
    report = ROOT / "REPORT.html"
    if report.exists():
        html = report.read_text(encoding="utf-8")
        banner = ('<div style="max-width:1080px;margin:18px auto 0;padding:10px 16px;'
                  'font-family:Microsoft YaHei,sans-serif;font-size:14px;">'
                  '<a href="index.html" style="color:#0b6e99;text-decoration:none;">'
                  '← 返回课程网站</a></div>')
        html = html.replace("<body>", "<body>" + banner, 1)
        (SITE / "full-report.html").write_text(html, encoding="utf-8")

    # search index
    course = [
        {
            "num": c["num"],
            "slug": c["slug"],
            "title": c["title"],
            "short": c["short"],
            "duration": c["duration"],
            "keywords": c.get("keywords", ""),
        }
        for c in chapters
    ]
    js = "window.COURSE = " + json.dumps(course, ensure_ascii=False, indent=2) + ";\n"
    (ASSETS / "search-index.js").write_text(js, encoding="utf-8")

    glossary_data = [
        {
            "term": g["term"],
            "aliases": g.get("aliases", []),
            "definition": g["definition"],
            "category": g["category"],
        }
        for g in GLOSSARY
    ]
    gloss_js = (
        "window.GLOSSARY = "
        + json.dumps(glossary_data, ensure_ascii=False, indent=2)
        + ";\n"
    )
    (ASSETS / "glossary-data.js").write_text(gloss_js, encoding="utf-8")

    # zip
    zip_path = DOWNLOADS / "single-cell-tutorial-code.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in (ROOT / "code").glob("*.py"):
            z.write(p, f"code/{p.name}")
        if (ROOT / "code" / "run_all.ps1").exists():
            z.write(ROOT / "code" / "run_all.ps1", "code/run_all.ps1")
        for name, arc in [
            ("requirements.txt", "requirements.txt"),
            ("README.md", "README.md"),
            ("REPORT.md", "REPORT.md"),
            ("data/README.md", "data/README.md"),
            ("results/README.md", "results/README.md"),
        ]:
            p = ROOT / name
            if p.exists():
                z.write(p, arc)
    print("wrote", zip_path)
    print("done")


if __name__ == "__main__":
    build()
