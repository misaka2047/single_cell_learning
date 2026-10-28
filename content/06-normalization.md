---
num: 6
slug: normalization
title: 归一化与 HVG：把不同细胞放到同一把尺子上
short: counts 和 RPKM 不能用同一套归一化
duration: 45 min
summary: 理解 library size、log 变换和 HVG 的作用；对 counts 做 CP10k+log1p，对 RPKM 做 log2(x+1)。
keywords: 归一化, CP10k, log1p, RPKM, HVG, 高变基因, scale, double dipping
---

## 本章目标

1. 能区分 counts 与 RPKM/TPM 的归一化方式；
2. 解释为什么先 log 再选 HVG；
3. 复现两个数据集的 HVG=2,000 与 PCA。

<div class="callout why" markdown="1">
<span class="callout-title">为什么归一化是“隐形的地基”</span>
每个细胞的测序深度不同。如果不归一化，高深度细胞的所有基因都“更高”，聚类会按建库质量而不是细胞类型分开。归一化就是把细胞放到同一把尺子上；但**尺子选错**（比如对 RPKM 再做 CP10k）会把真实差异也抹掉。
</div>

## 6.1 两种数据类型，两种做法

| 数据类型 | 已经做了什么 | 本教程的做法 |
|---|---|---|
| UMI counts（GSE84133） | 只数了 UMI，未按深度归一化 | 每个细胞缩放到 1e4，再 `log1p` |
| RPKM（GSE81608） | 已按基因长度和测序深度归一化 | 直接 `log2(x+1)` |

```python
# counts
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)

# RPKM
adata.X.data = np.log2(adata.X.data + 1)
```

> **不要**对 RPKM 再做 CP10k；**不要**在 log 后的数据上再 `normalize_total`。顺序错了，HVG、PCA、DE 都会跟着错。

## 6.2 为什么 log

- 表达量跨越几个数量级；log 压缩极端值，让高表达基因不主导 PCA。
- `log1p` 处理 0：`log1p(0)=0`，不会出现 `log(0)`。
- 对 counts，`log1p(CP10k)` 是 Scanpy 的常用组合；对 RPKM，`log2(RPKM+1)` 是常见做法。

## 6.3 HVG：从 2 万个基因到 2 千个

HVG（highly variable genes）保留在细胞间变化大的基因，去掉“所有细胞都表达”或“都不表达”的基因。它降低噪声和计算量，但**不改变生物学结论**——前提是不要用 DE 结果来选 HVG。

```python
sc.pp.highly_variable_genes(
    adata, n_top_genes=2000, batch_key="donor", flavor="seurat"
)
adata = adata[:, adata.var["highly_variable"]].copy()
sc.pp.scale(adata, max_value=10)
```

- `batch_key="donor"`：让 HVG 在供者间更稳定，而不是被某个供者主导。
- `flavor="seurat"`：按表达均值和离散度选；数据应是 log 后的。
- `scale(max_value=10)`：z-score 每个基因，限制极端值；会把稀疏矩阵变稠密。

**预期输出**：

```text
HVGs: 2000
```

两个数据集都保留 2,000 个 HVG。

## 6.4 常见错误

| 错误 | 后果 | 正确做法 |
|---|---|---|
| 对 RPKM 再做 CP10k | 双重归一化，差异被压缩 | RPKM 只做 log2(x+1) |
| 先 scale 再选 HVG | HVG 被 z-score 影响 | 先 HVG，再 scale |
| 用全部样本的 DE 基因选 HVG | double dipping，p 值偏小 | 预设基因集/独立数据 |
| 不按 batch 选 HVG | HVG 被单一批次主导 | `batch_key="donor"` |
| 对 log 数据再 normalize_total | 归一化错误 | 检查 `adata.X.max()` 和分布 |

<div class="callout expected" markdown="1">
<span class="callout-title">你应该看到</span>
- `adata.var["highly_variable"].sum() == 2000`；
- PCA 的 explained variance ratio 前几个主成分较高，随后下降；
- `adata.X` 的数值范围大概在 -10 到 10（scale 后），不再是 counts。
</div>

<div class="callout check" markdown="1">
<span class="callout-title">检查点</span>
**Q1**：为什么 GSE81608 不需要 `normalize_total`？

**Q2**：HVG 选 2,000 个，会不会漏掉稀有细胞类型的 marker？

**Q3**：为什么先 HVG 再 scale，而不是反过来？

<details><summary>参考答案</summary>

1. RPKM 已经按基因长度和测序深度归一化；再做 CP10k 是双重归一化。
2. 可能。HVG 是全局选择，稀有类型的 marker 可能不在前 2,000；可以用 marker 基因强制保留，或做全基因 DE。
3. scale 会让所有基因均值为 0、方差为 1，改变 HVG 的均值-离散度关系；HVG 应在 log 后的原始尺度上选。

</details>
</div>

## 下一步

有了归一化矩阵和 HVG，下一步做 PCA、kNN、UMAP、Leiden，把细胞分成簇。你会看到 19 个簇，但它们不是 19 种细胞类型。
