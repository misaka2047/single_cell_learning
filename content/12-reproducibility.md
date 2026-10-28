---
num: 12
slug: reproducibility
title: 可复现性与下一步：把项目做成“能重跑”的研究
short: 目录、环境、种子、版本、检查清单
duration: 45 min
summary: 用一份可复现清单收尾；掌握真实排错表；把同一流程迁移到肥胖/糖尿病更大的队列。
keywords: 可复现性, 随机种子, session info, 排错, 肥胖, GSE176171, HPAP, 下一步
---

## 本章目标

1. 能检查一个单细胞项目是否“可重跑”；
2. 能处理本教程遇到的真实报错；
3. 知道下一步该学什么、用什么数据。

<div class="callout why" markdown="1">
<span class="callout-title">为什么可复现性不是“最后再补”</span>
单细胞分析有大量分叉：QC 阈值、HVG 数、resolution、协变量、FDR。没有记录，三个月后你自己也复现不了。可复现性不是“把代码放 GitHub”这么简单，而是**数据版本 + 参数 + 随机种子 + 环境 + 预期输出**都能对上。
</div>

## 12.1 可复现清单

- [ ] 原始数据 URL、下载日期、SHA256；
- [ ] 数据版本（GEO 可能更新）；
- [ ] 样本 metadata 与矩阵列/行一一对应；
- [ ] 基因 ID 类型与映射表；
- [ ] QC 阈值及保留/删除的细胞数；
- [ ] 归一化方法；
- [ ] HVG 数量、batch key；
- [ ] PCA/邻接图/聚类参数、随机种子；
- [ ] 注释 marker 与独立验证（作者标签/蛋白）；
- [ ] DE 的推断单位、协变量、FDR；
- [ ] 阴性/阳性对照；
- [ ] 软件版本（`results/session_info.txt`）。

本教程的结果：

| 项目 | 结果 |
|---|---|
| GSE84133 QC 后 | 8,531 × 16,353 |
| GSE84133 聚类/类型 | 19 簇 / 11 类 |
| GSE84133 ARI | 0.968 |
| GSE81608 | 1,600 × 39,851，18 名供者 |
| β 细胞 / pseudobulk 供者 | 503 / 16 |
| 细胞水平 DE | 1,217 / 39,851 |
| pseudobulk DE | 0 / 9,929 |
| 阳性对照 | 3,086 / 11,053 |

## 12.2 运行方式

```powershell
python -m pip install -r requirements.txt
$env:NUMBA_DISABLE_INTEL_SVML = "1"   # Windows 兼容性 workaround

python code/00_prepare_data.py
python code/01_baron_cluster.py
python code/02_baron_annotate.py
python code/03_gse81608_cluster.py
python code/04_gse81608_de.py
python code/05_report_figures.py
python code/06_session_info.py
```

或者：

```powershell
powershell -ExecutionPolicy Bypass -File code/run_all.ps1
```

> 运行前先按 [数据说明](../code/DATA_README.md) 下载数据；代码包不含原始数据。

## 12.3 真实排错表

这些错误在本教程的实际运行中都出现过：

| 报错/现象 | 原因 | 解决 |
|---|---|---|
| `LLVM ERROR: Symbol not found: __svml_sqrtf16` | numba/llvmlite 在 Windows 的 SVML 兼容性 | `$env:NUMBA_DISABLE_INTEL_SVML="1"` |
| `ModuleNotFoundError: scanpy` | 未安装/装错 Python 环境 | `python -m pip install -r requirements.txt` |
| `KeyError: 'pct_counts_top_50'` | Scanpy 版本字段名变化 | 用 `pct_counts_in_top_50_genes` |
| `LinAlgError: Incompatible dimensions` | `lstsq(X, Y)` 的 Y 是 genes × donors | 改成 donors × genes |
| 下载 404 | series-level 路径拼了 sample-level 文件 | 用 `geo/samples/GSM.../suppl/` |
| 下载 0 字节/极慢 | NCBI 限速/连接卡住 | 用 `download_ranges.py`，先 range 测试 |
| 所有 p 值 NaN | 基因方差为 0/有 NaN | 过滤低表达基因；`nan_to_num` |
| `gzip.BadGzipFile` | 下载截断/拼接顺序错 | 删除重下，核对 SHA256 |
| 聚类全是一簇 | 未归一化/未 log/HVG 太少 | 检查 `X` 分布、HVG 数 |
| 每个供者一簇 | 强批次/供者效应 | 检查 donor UMAP；谨慎校正 |

## 12.4 常见坑（比报错更危险）

| 坑 | 后果 | 修复 |
|---|---|---|
| 把细胞当独立重复 | p 值极小、假阳性 | pseudobulk/混合模型 |
| 用文件名猜分组 | 分组标错 | 读 series matrix |
| 疾病与批次共线 | 无法区分 | 独立队列/配对设计 |
| 机械套用 mito<20% | 丢失真实细胞 | 看分布、按组织定阈值 |
| 用 HVG 做过又做 DE | double dipping | 预设基因集/独立数据 |
| 用 marker 聚类又用同一 marker 验证 | 循环论证 | 独立标签/蛋白验证 |
| 只看 p，不看效应量 | 大 n 下微小差异也显著 | 报告 log2FC/CI |
| 忽略环境 RNA/双细胞 | 混合簇/假 marker | SoupX/Scrublet |
| 过度解释组成比例 | 分选/纯度混杂 | 供者水平 + 纯度协变量 |
| 只报显著结果 | 发表偏倚 | 报告阴性/阳性对照 |

## 12.5 下一步：把流程迁移到肥胖/糖尿病

### 数据

- **HPAP / PANC-DB**：人类胰腺/胰岛，糖尿病相关，临床元数据丰富；按页面说明申请/下载。
- **GSE176171**：人/鼠白色脂肪单细胞图谱，适合做肥胖方向；注意脂肪组织解离偏差。
- **CELLxGENE / HCA**：找带标准注释的参考图谱，做标签转移/验证。
- **GTEx**：bulk/eQTL，可做 deconvolution 或外部验证（不是单细胞）。

### 方法

- pseudobulk + DESeq2/limma-voom（R）或 PyDESeq2；
- 混合模型（供者随机效应）处理细胞水平相关性；
- 组成分析：scCODA、propeller；
- 细胞通讯：CellChat/CellPhoneDB；
- 调控网络：SCENIC；
- 轨迹/RNA velocity：Monocle3/scVelo；
- 空间转录组：把细胞类型映射回组织位置；
- 功效分析：供者数、每供者细胞数、效应量。

### 学习节奏

| 时间 | 目标 |
|---|---|
| 两周 | 重跑本教程；改一个参数（resolution/HVG/QC），观察结果变化 |
| 一个月 | 加入 GSE176171 或 HPAP；重复同一流程；学习 pseudobulk R 实现 |
| 两个月 | 选一个临床问题，设计发现+验证两队列；做功效分析；预注册分析计划 |

## 12.6 推荐阅读

1. Luecken & Theis, *Mol Syst Biol* 2019：单细胞分析最佳实践教程。
2. Heumos et al., *Nat Rev Genet* 2023：跨模态单细胞分析最佳实践。
3. Squair et al., *Nat Commun* 2021：单细胞 DE 的假发现。
4. Murphy & Skene, *Nat Commun* 2022：pseudobulk 方法比较。
5. Baron et al., *Cell Syst* 2016；Xin et al., *Cell Metab* 2016：本教程的数据来源。

<div class="callout check" markdown="1">
<span class="callout-title">最终检查点</span>
**Q1**：如果别人拿到你的项目，最需要哪三样东西才能重跑？

**Q2**：为什么本教程的 pseudobulk 只用了 16 名供者？

**Q3**：你下一步准备用哪个数据集、回答什么问题？

<details><summary>参考答案</summary>

1. 原始数据/校验和、完整代码与参数、软件版本/环境（外加预期输出）。
2. 只保留有 ≥10 个 β 细胞的供者：10 名对照 + 6 名 T2D；另外 2 名对照 β 细胞太少，聚合不可靠。
3. 开放题。建议选一个明确组织/细胞/对比，并先写功效分析和验证计划。

</details>
</div>

## 结语

如果你只记住一句话：

> **先确定推断单位，再谈显著性；先看 metadata，再做图；阴性结果也要有阳性对照。**

这比记住任何一个参数都重要。
