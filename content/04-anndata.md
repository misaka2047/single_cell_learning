---
num: 4
slug: anndata
title: AnnData 与基因 ID：单细胞数据的“底盘”
short: 把 CSV/RPKM 变成 scanpy 能理解的对象
duration: 45 min
summary: 理解 X、obs、var、layers 的分工；构建两个 AnnData；把 GSE81608 的 Entrez ID 映射成基因符号。
keywords: AnnData, scanpy, obs, var, layers, Entrez, 基因ID, 稀疏矩阵
---

## 本章目标

1. 能解释 AnnData 的 `X`、`obs`、`var`、`layers` 各存什么；
2. 把 GSE84133 的 4 个 CSV 合并成一个稀疏矩阵；
3. 把 GSE81608 的 Entrez GeneID 映射成 HGNC symbol；
4. 对照本章的预期输出，确认数据没有错位。

<div class="callout why" markdown="1">
<span class="callout-title">为什么用 AnnData，而不是一个大 DataFrame</span>
单细胞矩阵通常是“细胞 × 基因”的稀疏矩阵：85% 以上是 0。AnnData 把**表达矩阵**和**细胞/基因注释**放在同一个对象里，并且支持 `layers` 保存原始 counts/RPKM、`obsm` 保存 PCA/UMAP。后面 Scanpy 的每个函数都围绕这个结构工作；结构错了，函数不会报错，但结果会悄悄错。
</div>

## 4.1 AnnData 的五个槽位

| 槽位 | 维度 | 本教程存什么 |
|---|---|---|
| `X` | 细胞 × 基因 | 当前分析用的表达矩阵（log 后） |
| `obs` | 细胞 × 字段 | donor、condition、age、sex、author_label |
| `var` | 基因 × 字段 | gene symbol、是否 HVG、是否 MT |
| `layers` | 细胞 × 基因 | `counts` / `rpkm` / `lognorm`，保留原始值 |
| `obsm` | 细胞 × 低维 | PCA、UMAP |
| `uns` | 任意 | 数据集说明、配色、参数 |

最小示例：

```python
import anndata as ad
import pandas as pd
from scipy.sparse import csr_matrix

adata = ad.AnnData(
    X=csr_matrix(counts),                  # cells x genes
    obs=pd.DataFrame(metadata, index=cell_ids),
    var=pd.DataFrame(index=gene_names),
)
adata.layers["counts"] = adata.X.copy()    # 原始值单独留一份
adata.var_names_make_unique()
```

## 4.2 数据集 A：GSE84133

每个 CSV 的列是：

```text
cell_id, barcode, assigned_cluster, A1BG, A1CF, A2M, ...
```

前 3 列是 metadata，第 4 列开始是 20,125 个基因的 UMI counts。代码在
[`00_prepare_data.py`](../code/00_prepare_data.py)：

```python
df = pd.read_csv(path, dtype={0: str, 1: str, 2: str}, low_memory=False)
obs = pd.DataFrame({
    "cell_id": df.iloc[:, 0].astype(str),
    "barcode": df.iloc[:, 1].astype(str),
    "author_label": df.iloc[:, 2].astype(str),
    "donor": meta["donor"], "condition": meta["condition"],
    "age": meta["age"], "sex": meta["sex"], "bmi": meta["bmi"],
}, index=df.iloc[:, 0].astype(str))
X = csr_matrix(df.iloc[:, 3:].to_numpy(dtype=np.float32))
```

四个样本用 `ad.concat(..., join="outer")` 合并；缺失基因填 0。

**预期输出**：

```text
reading human1 ... 1,937 cells x 20,125 genes
reading human2 ... 1,724 cells x 20,125 genes
reading human3 ... 3,605 cells x 20,125 genes
reading human4 ... 1,303 cells x 20,125 genes
wrote .../baron_raw.h5ad (8569, 20125)
```

> 8,569 = 1,937 + 1,724 + 3,605 + 1,303。论文报告 8,629 个细胞，GEO 处理后矩阵是 8,569；以你下载到的矩阵为准。

## 4.3 数据集 B：GSE81608

矩阵是“基因 × 细胞”，第一列是 `gene.id`，值是 1、2、3…，不是基因符号。它们是 **Entrez GeneID**；用 NCBI `Homo_sapiens.gene_info.gz` 映射：

```python
gene_info = pd.read_csv("data/Homo_sapiens.gene_info.gz", sep="\t",
                        dtype=str, usecols=["GeneID", "Symbol"])
id2sym = dict(zip(gene_info["GeneID"], gene_info["Symbol"]))
symbols = [id2sym.get(str(g), f"Entrez:{g}") for g in rpkm.index]
```

然后转置成“细胞 × 基因”：

```python
adata = ad.AnnData(
    X=csr_matrix(rpkm.T.to_numpy(dtype=np.float32)),
    obs=meta,
    var=pd.DataFrame(index=symbols),
)
adata.layers["rpkm"] = adata.X.copy()
```

**预期输出**：

```text
raw matrix (39851, 1600) (genes x cells)
mapped 37,987/39,851 Entrez IDs to symbols
wrote .../gse81608_raw.h5ad (1600, 39851)
```

<div class="callout expected" markdown="1">
<span class="callout-title">你应该看到</span>
- `baron_raw.h5ad`：8,569 × 20,125；
- `gse81608_raw.h5ad`：1,600 × 39,851；
- `gse81608_raw.obs` 有 `donor`、`condition`、`age`、`sex`、`author_label`；
- `gse81608_raw.layers["rpkm"]` 与 `X` 相同（后续才 log2）。
</div>

## 4.4 为什么用稀疏矩阵

8,569 × 20,125 的稠密 float32 约 690 MB；稀疏存储只保留非零值，通常 100–300 MB。GSE81608 更极端：39,851 个基因，大部分细胞只表达几千个。

```python
from scipy.sparse import csr_matrix
X = csr_matrix(dense_array)   # 只存非零
```

> 但 `sc.pp.scale` 会把稀疏矩阵变稠密；所以先选 HVG（2,000 个基因）再 scale，是本教程的顺序。

## 4.5 常见错误

| 错误 | 后果 | 检查 |
|---|---|---|
| 行列转置错 | 细胞当基因，聚类完全乱 | `adata.shape` 应是 cells × genes |
| obs index 与矩阵行不对应 | 分组错位 | `adata.obs_names[:3]` 与 CSV 第一列对齐 |
| 基因名重复 | `var_names` 不唯一，索引出错 | `var_names_make_unique()` |
| 把 RPKM 当 counts 做 CP10k | 双重归一化 | 看 `layers` 和列名 |
| 把 metadata 拼错顺序 | 疾病/年龄错配 | 用 `pd.concat(..., axis=1)` 按 index 对齐，不靠位置 |

<div class="callout check" markdown="1">
<span class="callout-title">检查点</span>
**Q1**：`X` 和 `layers["counts"]` 有什么区别？为什么要留两份？

**Q2**：GSE81608 的 39,851 个“基因”里，为什么有 1,864 个没有映射到 symbol？

**Q3**：如果 `adata.shape` 是 `(20125, 8569)`，哪里错了？

<details><summary>参考答案</summary>

1. `X` 是当前分析矩阵（归一化/log 后），`layers` 保留原始值；DE 或重新归一化时需要原始 counts/RPKM。
2. Entrez ID 可能已 retired、非蛋白编码、或 NCBI gene_info 中没有对应 symbol；保留 `Entrez:<id>` 避免丢失。
3. 矩阵转置了；AnnData 约定是 cells × genes。

</details>
</div>

## 下一步

结构对了，下一步做 QC：决定哪些细胞应该被删掉。你会看到，GSE84133 的 99.6% 细胞被保留，而 GSE81608 一个都不删。
