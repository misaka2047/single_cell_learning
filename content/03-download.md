---
num: 3
slug: download
title: 下载与工程化：把 GEO 变成可分析的项目
short: 文件、校验、metadata 对齐，一个都不能少
duration: 50 min
summary: 从 GEO series matrix 读取分组，下载 4 个人类样本和 1 个 RPKM 矩阵，核对 SHA256，建立可复现的目录结构。
keywords: GEO下载, series matrix, curl, SHA256, metadata, 文件结构, 数据工程
---

## 本章目标

1. 看懂 GEO 的 series matrix、suppl 文件、sample-level 文件；
2. 把两个数据集下载到正确的目录并核对完整性；
3. 产出一张“GSM → 供者 → 分组”的对照表。

<div class="callout why" markdown="1">
<span class="callout-title">为什么先做数据工程</span>
公共数据再分析最常见的事故不是模型选错，而是**文件下错、版本变了、样本顺序对不上**。后面的 QC、聚类、DE 都建立在这张矩阵上；如果 metadata 错位，所有结果都会“看起来很合理但全错”。
</div>

## 3.1 建立目录

在项目根目录执行：

```powershell
New-Item -ItemType Directory -Force data, data/processed, results, figures, code
```

目标结构：

```text
single-cell-learning/
├─ data/
│  ├─ GSM2230757_human1_umifm_counts.csv.gz
│  ├─ GSM2230758_human2_umifm_counts.csv.gz
│  ├─ GSM2230759_human3_umifm_counts.csv.gz
│  ├─ GSM2230760_human4_umifm_counts.csv.gz
│  ├─ GSE81608_human_islets_rpkm.txt.gz
│  ├─ GSE81608_series_matrix.txt.gz
│  ├─ GSE84133_series_matrix.txt.gz
│  └─ Homo_sapiens.gene_info.gz
├─ data/processed/      # .h5ad
├─ figures/             # .png
├─ results/             # .csv
└─ code/                # .py
```

## 3.2 GEO 的三层文件

| 层级 | 例子 | 用途 |
|---|---|---|
| Series matrix | `GSE84133-GPL16791_series_matrix.txt.gz` | 样本 metadata；本教程用它确认供者、疾病、年龄、性别、BMI |
| Series suppl | `GSE84133_RAW.tar` | 作者打包的所有样本文件（可能很大，且下载慢） |
| Sample suppl | `GSM2230757_human1_umifm_counts.csv.gz` | 单个样本的矩阵；适合只下载需要的样本 |

GSE84133 的 4 个人类样本在 **sample-level suppl**；GSE81608 只有一个 gene-level RPKM 矩阵。

## 3.3 下载命令

NCBI FTP 从某些网络会很慢。`code/download_ranges.py` 会把 gzip 切成多个 byte range 并行下载，再按顺序拼接。gzip 是字节流，因此按序拼接 range 可以精确重建原文件。

```powershell
# GSE84133 的 4 个人类样本
python code/download_ranges.py `
  "https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2230nnn/GSM2230757/suppl/GSM2230757_human1_umifm_counts.csv.gz" `
  "data/GSM2230757_human1_umifm_counts.csv.gz" --workers 6 --chunk-mb 2

# GSE81608 的 RPKM 矩阵
python code/download_ranges.py `
  "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE81nnn/GSE81608/suppl/GSE81608_human_islets_rpkm.txt.gz" `
  "data/GSE81608_human_islets_rpkm.txt.gz" --workers 8 --chunk-mb 4
```

series matrix 和 gene_info 较小，可以直接：

```powershell
curl.exe -L --fail -o data/GSE84133_series_matrix.txt.gz `
  "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE84nnn/GSE84133/matrix/GSE84133-GPL16791_series_matrix.txt.gz"

curl.exe -L --fail -o data/GSE81608_series_matrix.txt.gz `
  "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE81nnn/GSE81608/matrix/GSE81608_series_matrix.txt.gz"

curl.exe -L --fail -o data/Homo_sapiens.gene_info.gz `
  "https://ftp.ncbi.nlm.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz"
```

完整 URL 和 SHA256 见 [数据说明](../code/DATA_README.md)。

## 3.4 核对 metadata

打开 series matrix，找 `!Sample_characteristics_ch1`：

```python
import gzip
with gzip.open("data/GSE84133_series_matrix.txt.gz", "rt") as fh:
    for line in fh:
        if line.startswith("!Sample_characteristics_ch1"):
            print(line.strip()[:500])
```

你应该看到：

| GSM | 供者 | 条件 | 年龄 | 性别 | BMI |
|---|---|---|---|---|---|
| GSM2230757 | D1 | No | 17 | male | 21.5 |
| GSM2230758 | D2 | No | 51 | female | 21.1 |
| GSM2230759 | D3 | No | 38 | male | 27.5 |
| GSM2230760 | D4 | **Yes** | 59 | female | 29.9 |

> 注意：只有 D4 是 T2D。这个表会直接写进 `00_prepare_data.py` 的 metadata 字典。

## 3.5 预期结果

下载完成后，文件大小应接近：

| 文件 | 大小 |
|---|---:|
| `GSM2230757_human1_umifm_counts.csv.gz` | 5.67 MB |
| `GSM2230758_human2_umifm_counts.csv.gz` | 4.96 MB |
| `GSM2230759_human3_umifm_counts.csv.gz` | 9.77 MB |
| `GSM2230760_human4_umifm_counts.csv.gz` | 4.25 MB |
| `GSE81608_human_islets_rpkm.txt.gz` | 37.22 MB |
| `GSE81608_series_matrix.txt.gz` | 44 KB |
| `GSE84133_series_matrix.txt.gz` | 3 KB |
| `Homo_sapiens.gene_info.gz` | 5.20 MB |

核对校验和：

```powershell
Get-FileHash data/GSE81608_human_islets_rpkm.txt.gz -Algorithm SHA256
```

<div class="callout expected" markdown="1">
<span class="callout-title">你应该看到</span>
`data/` 下有 8 个文件；`GSE84133_series_matrix` 能打印出 4 个样本；GSE81608 matrix 用 `gzip.open` 能读出 1,601 列（1 个基因 ID 列 + 1,600 个细胞）。
</div>

## 3.6 排错表

| 现象 | 原因 | 处理 |
|---|---|---|
| 404 Not Found | 把 series-level 文件名拼到了 sample-level 路径 | GSE84133 用 `geo/samples/GSM.../suppl/`，不是 `geo/series/.../suppl/` |
| 下载 0 字节/极慢 | NCBI 限速/连接卡住 | 用 `download_ranges.py`；先 `curl -r 0-1000000` 测试速度 |
| `gzip.BadGzipFile` | 下载中断或 range 拼接顺序错 | 删除文件重下；不要手工改 `.gz` |
| PowerShell 报“非交互模式” | `Invoke-WebRequest` 进度条问题 | 改用 `curl.exe` |
| metadata 列数对不上 | 矩阵列和 series matrix 顺序不一致 | 按 `Sample_1...Sample_N` 显式对齐，不要靠默认顺序 |

<div class="callout check" markdown="1">
<span class="callout-title">检查点</span>
**Q1**：为什么 GSE84133 的 4 个文件在 sample-level suppl，而不是 series-level？

**Q2**：如果下载的 GSE81608 矩阵只有 1,000 列，可能是哪里错了？

**Q3**：为什么要用 SHA256，而不是只看文件大小？

<details><summary>参考答案</summary>

1. 作者把每个人类样本作为一个 GSM 上传；series-level 只有打包的 `RAW.tar`。按 GSM 下载可以跳过不需要的 mouse 样本。
2. 可能下载被截断、range 拼接顺序错、或拿到的不是同一个文件版本；用文件大小和 SHA256 核对。
3. 文件大小相同不代表内容相同；SHA256 能发现传输损坏/版本替换。

</details>
</div>

## 下一步

数据齐了，下一步把它们读成 AnnData：细胞 × 基因矩阵、metadata、layers，以及 GSE81608 的 Entrez ID 映射。
