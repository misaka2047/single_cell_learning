---
num: 2
slug: databases
title: 数据库检索：如何找到“能用的”公共数据
short: 不是所有 GSE 都能支撑你的问题
duration: 45 min
summary: 从 GEO 到 CELLxGENE、HCA、HPAP，学会用 metadata 筛选数据，而不是只看标题和细胞数。
keywords: GEO, CELLxGENE, Human Cell Atlas, HPAP, 数据库, metadata, 数据选择
---

## 本章目标

1. 知道常用单细胞数据库各自适合什么；
2. 会用 metadata 判断一个数据集能不能回答你的问题；
3. 能解释为什么本教程选 GSE84133 做图谱、GSE81608 做疾病比较。

<div class="callout why" markdown="1">
<span class="callout-title">为什么“找到数据”不等于“能用数据”</span>
一个 GSE 页面可能写着“single-cell RNA-seq of human islets”，但打开 metadata 才发现：只有 1 名 T2D 供者、没有年龄/性别、只有聚类标签没有 counts、或者所有样本来自同一个批次。**数据选择错误，后面所有分析都救不回来。**
</div>

## 2.1 常用资源地图

| 资源 | 适合做什么 | 要注意什么 |
|---|---|---|
| [GEO](https://www.ncbi.nlm.nih.gov/geo/) | 最常用的原始/处理后 scRNA-seq 数据 | 以 GSE 为单位；必须看 sample metadata 和 supplementary |
| [CELLxGENE](https://cellxgene.cziscience.com/) | 已整理、带标准注释的图谱，可在线浏览/下载 h5ad | schema 统一，但版本和细胞筛选不同 |
| [Human Cell Atlas](https://www.humancellatlas.org/) | 人体组织参考图谱 | 数据量大；部分项目受控访问 |
| [HPAP / PANC-DB](https://hpap.pmacs.upenn.edu/) | 人类胰腺/胰岛，糖尿病相关 | 临床元数据丰富；部分数据需按页面说明申请 |
| [Single Cell Portal](https://singlecell.broadinstitute.org/) | Broad 项目图谱、在线可视化 | 项目格式不统一，下载前看清版本 |
| [ArrayExpress / BioStudies](https://www.ebi.ac.uk/biostudies/arrayexpress) | 欧洲镜像/补充资源 | 并非所有 GSE 都有镜像 |
| [Tabula Sapiens](https://tabula-sapiens-portal.ds.czbiohub.org/) | 多器官健康人参考 | 适合做标签转移/参考，不适合直接做疾病比较 |
| [GTEx](https://gtexportal.org/) | 组织 bulk/eQTL | 不是单细胞；可做 deconvolution/验证 |

肥胖方向可以先看 [GSE176171](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE176171)（人/鼠白色脂肪单细胞图谱），再按同一套 metadata 标准筛选。

## 2.2 GEO 页面到底看什么

打开一个 GSE，按这个顺序看：

1. **Series 标题与 summary**：物种、组织、平台、疾病。
2. **Overall design**：多少供者、多少组、是否有配对。
3. **Sample metadata**：`!Sample_characteristics_ch1` 是金矿，包含 age、sex、BMI、HbA1c、condition、cell subtype。
4. **Supplementary files**：raw counts、processed counts、RPKM/TPM、还是只有聚类标签？
5. **样本级 supplementary**：能否只下载需要的样本，避免下整包？
6. **论文**：数据版本、过滤规则、作者用的模型。

<div class="callout warn" markdown="1">
<span class="callout-title">三个真实坑</span>
- GSE84133 有 4 名供者，但只有 **1 名 T2D**；不要按“2 vs 2”设计。
- GSE81608 论文报告 1,492 个细胞，GEO 矩阵有 **1,600 列**；处理后矩阵不一定等于论文的分析集。
- 两个数据集的 processed matrix 都**没有 MT- 基因**，所以不能算线粒体比例；不要为了“流程完整”编一个 0%。
</div>

## 2.3 检索策略

以 GEO 为例，关键词可以这样组合：

```text
("single-cell"[All Fields] OR "scRNA-seq"[All Fields])
AND (pancreatic islet*[All Fields] OR "islet of Langerhans"[All Fields])
AND ("type 2 diabetes"[All Fields] OR T2D[All Fields])
```

但关键词只负责“召回”，真正的筛选靠 metadata：

- **物种/组织**：人？胰岛？全胰腺？脂肪？
- **疾病定义**：T2D 如何诊断？对照是否匹配年龄/BMI？
- **供者数**：每组多少？是否有配对？
- **平台**：10x、inDrop、Smart-seq2、snRNA-seq；不同平台不要直接拼。
- **数据层级**：raw counts / processed counts / RPKM / 只有标签。
- **元数据**：age、sex、BMI、HbA1c、islet purity、batch、解离方案。
- **作者标签**：能做独立验证，但不是 ground truth。

## 2.4 本教程的选择及理由

| | GSE84133 | GSE81608 |
|---|---|---|
| 组织 | 人胰岛（inDrop） | 人胰岛（单细胞 RNA-seq） |
| 细胞数 | 8,569 | 1,600（论文 1,492） |
| 供者 | 4（3 对照，1 T2D） | 18（12 对照，6 T2D） |
| 基因 | 20,125 | 39,851 |
| 数据类型 | UMI counts | gene-level RPKM |
| 作者标签 | 14 类 | α/β/δ/PP |
| 本教程用途 | 图谱、聚类、注释 | T2D vs 对照 pseudobulk DE |

**为什么不是只用一个数据集？**

- GSE84133 细胞类型丰富、作者标签完整，适合学习聚类/注释；但疾病比较被供者共线毁掉。
- GSE81608 供者多、分组相对平衡，适合疾病比较；但 RPKM 不是 counts，且没有线粒体/空液滴信息。
- 两个数据集互补，正好演示“发现 vs 验证”和“数据限制”。

## 2.5 预期产出：一张数据选择表

在开始下载前，你应该能填出：

| 列 | 你的数据集 |
|---|---|
| GEO accession | GSE84133 / GSE81608 |
| 组织/物种 | 人胰岛 |
| 平台/数据类型 | inDrop counts / RPKM |
| 供者数（对照/T2D） | 4（3/1） / 18（12/6） |
| 细胞数 | 8,569 / 1,600 |
| 主要细胞类型 | 胰岛 + 胰腺外分泌/基质/免疫 |
| 可用协变量 | 年龄、性别、BMI；GSE81608 还有种族 |
| 主要限制 | 1 名 T2D；RPKM |

<div class="callout check" markdown="1">
<span class="callout-title">检查点</span>
**Q1**：GSE84133 的 4 名供者中，T2D 有几名？你怎么确认？

**Q2**：如果一个数据集只有“cell type labels”而没有表达矩阵，你能做什么、不能做什么？

**Q3**：为什么 GSE81608 的 1,600 列和论文的 1,492 个细胞不一致也可能是正常的？

<details><summary>参考答案</summary>

1. 1 名（D4）。读 `GSE84133-GPL16791_series_matrix.txt.gz` 的 `!Sample_characteristics_ch1`，不要凭文件名猜。
2. 可以做组成/标签分析，不能重新聚类、做 marker 或 DE；也无法验证作者注释。
3. 论文可能做了额外 QC/过滤，或者 GEO 矩阵包含了作者未纳入最终分析的低质量细胞；以 metadata 和矩阵实际内容为准。

</details>
</div>

## 下一步

第 3 步开始动手：下载文件、核对 metadata、建立项目目录。你会看到“数据工程”其实占整个项目很大一部分时间。
