---
num: A
slug: appendix
title: 附录：命令速查、文件地图与术语表
short: 卡住时先来这里查
duration: 参考
summary: 一页式的命令、文件、术语和排错索引；适合打印或放在第二屏。
keywords: 附录, 命令, 文件, 术语, 排错, 速查
---

> 需要边读边查？正文中带虚线下划线的术语可悬停/点击查看解释；58 条完整列表见
> [术语表](../glossary.html)。

## A.1 命令速查

```powershell
# 环境
python -m pip install -r requirements.txt
$env:NUMBA_DISABLE_INTEL_SVML = "1"

# 数据（示例，完整见 data/README.md）
python code/download_ranges.py `
  "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE81nnn/GSE81608/suppl/GSE81608_human_islets_rpkm.txt.gz" `
  "data/GSE81608_human_islets_rpkm.txt.gz" --workers 8 --chunk-mb 4

# 全流程
python code/00_prepare_data.py
python code/01_baron_cluster.py
python code/02_baron_annotate.py
python code/03_gse81608_cluster.py
python code/04_gse81608_de.py
python code/05_report_figures.py
python code/06_session_info.py
```

## A.2 文件地图

| 路径 | 内容 |
|---|---|
| `data/` | 原始 GEO 文件（需下载） |
| `data/processed/baron_raw.h5ad` | Baron 原始 counts + metadata |
| `data/processed/baron_annotated.h5ad` | Baron 聚类 + 注释 |
| `data/processed/gse81608_raw.h5ad` | GSE81608 RPKM + metadata |
| `data/processed/gse81608_annotated.h5ad` | GSE81608 聚类 + 注释 |
| `results/baron_celltype_composition_pct.csv` | Baron 供者水平组成 |
| `results/baron_annotation_ari.csv` | Baron ARI |
| `results/gse81608_beta_pseudobulk_de.csv` | T2D vs 对照 pseudobulk DE |
| `results/gse81608_beta_celllevel_naive_de.csv` | 细胞水平朴素 DE（反例） |
| `results/gse81608_beta_vs_alpha_positive_control.csv` | β vs α 阳性对照 |
| `results/de_method_comparison.csv` | 三种分析对比 |
| `results/summary_metrics.csv` | 数据集汇总指标 |
| `results/session_info.txt` | 软件版本 |
| `figures/` | 所有图（PNG） |
| `REPORT.html` | 完整 Markdown 报告 |

## A.3 术语表

| 术语 | 一句话解释 |
|---|---|
| AnnData | 单细胞矩阵 + 细胞/基因注释 + 降维结果的数据结构 |
| HVG | 高变基因；在细胞间变化大的基因，用于降维 |
| PCA | 主成分分析；把高维表达压到少数主成分 |
| kNN | k 近邻图；每个细胞连到最相似的 k 个细胞 |
| UMAP | 非线性降维可视化；主要保留局部邻接，不保证全局距离 |
| Leiden | 在 kNN 图上找社区的聚类算法；resolution 控制粒度 |
| ARI | 调整兰德指数；比较两种分组的一致性，1=完全一致 |
| pseudobulk | 把同一供者/样本的细胞聚合后再做 DE |
| 伪重复 | 把非独立观测（同一供者的细胞）当独立重复 |
| FDR | 错误发现率；多重检验校正后的显著性 |
| log2FC | log2 倍数变化；效应量 |
| double dipping | 用同一数据选特征又做检验，导致 p 值偏小 |
| 环境 RNA | 细胞裂解后释放、被其他液滴捕获的 RNA |
| 双细胞 | 两个细胞被同一液滴包住，表达谱混合 |

## A.4 最小排错顺序

遇到结果不对，按这个顺序查：

1. **维度**：`adata.shape` 是 cells × genes 吗？
2. **metadata**：分组/供者/细胞标签和矩阵列对得上吗？
3. **归一化**：`X` 是 counts 还是 log？有没有重复归一化？
4. **HVG/PCA**：HVG 数、PCA 方差、kNN 是否正常？
5. **聚类**：resolution 是否极端？是否按供者分开？
6. **注释**：marker 是否特异？有没有双细胞/环境 RNA？
7. **DE**：推断单位、Y 方向、协变量、FDR、阳性对照。

## A.5 引用

- Baron M, et al. *Cell Syst*. 2016;3(4):346-360.e4.
  doi:[10.1016/j.cels.2016.08.011](https://doi.org/10.1016/j.cels.2016.08.011)
- Xin Y, et al. *Cell Metab*. 2016;24(4):608-615.
  doi:[10.1016/j.cmet.2016.08.018](https://doi.org/10.1016/j.cmet.2016.08.018)
- Squair JW, et al. *Nat Commun*. 2021;12:5692.
  doi:[10.1038/s41467-021-25960-2](https://doi.org/10.1038/s41467-021-25960-2)
- Murphy AE, Skene NG. *Nat Commun*. 2022;13:7851.
  doi:[10.1038/s41467-022-35519-4](https://doi.org/10.1038/s41467-022-35519-4)
