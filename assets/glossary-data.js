window.GLOSSARY = [
  {
    "term": "scRNA-seq",
    "aliases": [
      "single-cell RNA-seq",
      "scRNAseq",
      "scRNA seq"
    ],
    "definition": "单细胞 RNA 测序：逐个细胞测量转录组，用来分辨细胞类型、状态和组间差异。",
    "category": "数据与格式"
  },
  {
    "term": "UMI",
    "aliases": [
      "UMIs",
      "unique molecular identifier"
    ],
    "definition": "唯一分子标识符：建库时给每条原始 RNA 分子加标签，用于去重和估计真实分子数。",
    "category": "数据与格式"
  },
  {
    "term": "AnnData",
    "aliases": [
      "anndata"
    ],
    "definition": "Python 单细胞数据结构：X 存表达矩阵，obs 存细胞注释，var 存基因注释，layers/obsm 存原始值和降维结果。",
    "category": "数据与格式"
  },
  {
    "term": "counts",
    "aliases": [
      "count matrix",
      "raw counts",
      "计数矩阵"
    ],
    "definition": "原始计数矩阵：每个基因在每个细胞中检测到的 UMI/reads 数，尚未归一化。",
    "category": "数据与格式"
  },
  {
    "term": "RPKM/TPM",
    "aliases": [
      "RPKM",
      "TPM"
    ],
    "definition": "已按基因长度和测序深度归一化的表达量；GSE81608 使用 RPKM，不能再做 CP10k。",
    "category": "数据与格式"
  },
  {
    "term": "metadata",
    "aliases": [
      "meta data",
      "元数据"
    ],
    "definition": "样本/细胞注释信息：供者、分组、年龄、性别、BMI、批次等；分组错位是最常见的事故。",
    "category": "数据与格式"
  },
  {
    "term": "供者",
    "aliases": [
      "donor",
      "donors"
    ],
    "definition": "提供样本的个体。在疾病比较中，供者才是生物学重复，不是细胞。",
    "category": "数据与格式"
  },
  {
    "term": "批次效应",
    "aliases": [
      "batch",
      "batch effect",
      "批次"
    ],
    "definition": "不同时间、建库、测序或中心带来的技术差异；可能与疾病分组共线，无法单独校正。",
    "category": "数据与格式"
  },
  {
    "term": "稀疏矩阵",
    "aliases": [
      "sparse matrix",
      "sparse"
    ],
    "definition": "只存非零值的矩阵；单细胞数据通常 85% 以上为 0，用稀疏存储可省大量内存。",
    "category": "数据与格式"
  },
  {
    "term": "Entrez GeneID",
    "aliases": [
      "Entrez",
      "GeneID"
    ],
    "definition": "NCBI 基因数字 ID；GSE81608 第一列是它，需要映射到基因 symbol 才能做 marker/富集。",
    "category": "数据与格式"
  },
  {
    "term": "QC",
    "aliases": [
      "quality control",
      "质控"
    ],
    "definition": "质控：按检测基因数、UMI、线粒体比例、双细胞等指标过滤低质量细胞。",
    "category": "预处理与质控"
  },
  {
    "term": "nGene",
    "aliases": [
      "detected genes",
      "检测基因数"
    ],
    "definition": "每个细胞检测到的基因数；过低提示空液滴/死细胞，过高提示双细胞。",
    "category": "预处理与质控"
  },
  {
    "term": "线粒体比例",
    "aliases": [
      "mito%",
      "mitochondrial fraction",
      "线粒体"
    ],
    "definition": "线粒体基因 counts 占总 counts 的比例；过高提示细胞应激/死亡。本数据无 MT- 基因，无法计算。",
    "category": "预处理与质控"
  },
  {
    "term": "双细胞",
    "aliases": [
      "doublet",
      "doublets"
    ],
    "definition": "两个细胞被同一液滴包住，表达谱是两种细胞的混合；会形成假簇/假 marker。",
    "category": "预处理与质控"
  },
  {
    "term": "环境 RNA",
    "aliases": [
      "ambient RNA",
      "ambient"
    ],
    "definition": "细胞裂解后释放、被其他液滴捕获的 RNA；会让所有细胞都“表达”某些基因。",
    "category": "预处理与质控"
  },
  {
    "term": "空液滴",
    "aliases": [
      "empty droplet",
      "empty droplets"
    ],
    "definition": "没有细胞、只含少量游离 RNA 的液滴；应在 QC 中用 EmptyDrops 等方法剔除。",
    "category": "预处理与质控"
  },
  {
    "term": "归一化",
    "aliases": [
      "normalization",
      "normalisation"
    ],
    "definition": "消除测序深度/基因长度差异，让不同细胞可比；counts 用 CP10k，RPKM 只做 log。",
    "category": "预处理与质控"
  },
  {
    "term": "CP10k",
    "aliases": [
      "CPM",
      "counts per 10k"
    ],
    "definition": "counts per 10,000：把每个细胞的 counts 缩放到 1 万，再做 log1p；只适用于 counts。",
    "category": "预处理与质控"
  },
  {
    "term": "log1p",
    "aliases": [
      "log2(x+1)",
      "log(x+1)"
    ],
    "definition": "log(1+x) 变换：压缩表达量、避免 log(0)，让高表达基因不主导 PCA。",
    "category": "预处理与质控"
  },
  {
    "term": "HVG",
    "aliases": [
      "highly variable genes",
      "高变基因",
      "HVGs"
    ],
    "definition": "高变基因：在细胞间变异大的基因，用于 PCA/聚类；本教程选 2,000 个。",
    "category": "预处理与质控"
  },
  {
    "term": "scaling",
    "aliases": [
      "scale",
      "z-score",
      "标准化"
    ],
    "definition": "对每个基因做 z-score（减均值、除标准差），常截断到 ±10；会把稀疏矩阵变稠密。",
    "category": "预处理与质控"
  },
  {
    "term": "PCA",
    "aliases": [
      "principal component analysis",
      "主成分分析"
    ],
    "definition": "主成分分析：把高维表达压到少数正交主成分，保留主要变异。",
    "category": "降维与聚类"
  },
  {
    "term": "kNN",
    "aliases": [
      "k-nearest neighbors",
      "k 近邻",
      "k-nearest neighbours"
    ],
    "definition": "k 近邻：每个细胞找最相似的 k 个细胞，构建细胞相似图；Leiden 在这张图上聚类。",
    "category": "降维与聚类"
  },
  {
    "term": "UMAP",
    "aliases": [
      "Uniform Manifold Approximation and Projection"
    ],
    "definition": "非线性降维可视化：保留局部邻接，适合看细胞群；全局距离/簇间距离不可靠。",
    "category": "降维与聚类"
  },
  {
    "term": "Leiden",
    "aliases": [
      "Leiden clustering",
      "Leiden 聚类"
    ],
    "definition": "图聚类算法：在 kNN 图上找社区，resolution 控制簇的粗细。",
    "category": "降维与聚类"
  },
  {
    "term": "resolution",
    "aliases": [
      "分辨率"
    ],
    "definition": "Leiden 的粒度参数：越大簇越多/越细；不是细胞类型数，需 marker 注释后合并。",
    "category": "降维与聚类"
  },
  {
    "term": "批次校正",
    "aliases": [
      "batch correction",
      "integration",
      "整合"
    ],
    "definition": "让同一细胞类型跨批次对齐；Harmony/ComBat/scVI/BBKNN 都是常见方法，但分组与批次共线时可能过校正。",
    "category": "降维与聚类"
  },
  {
    "term": "Harmony",
    "aliases": [
      "harmony"
    ],
    "definition": "基于 PCA 的迭代批次整合方法，常用于多样本 scRNA-seq；不改变原始表达矩阵。",
    "category": "降维与聚类"
  },
  {
    "term": "ComBat",
    "aliases": [
      "combat"
    ],
    "definition": "基于经验贝叶斯的批次校正，直接校正表达矩阵；可能把真实生物学差异一起校正掉。",
    "category": "降维与聚类"
  },
  {
    "term": "scVI",
    "aliases": [
      "scvi"
    ],
    "definition": "变分自编码器模型，可做批次整合、降维和差异表达；需要 counts 和一定计算资源。",
    "category": "降维与聚类"
  },
  {
    "term": "BBKNN",
    "aliases": [
      "bbknn"
    ],
    "definition": "批次平衡 kNN：在每个批次内找邻居再合并，构建整合图；适合多样本聚类。",
    "category": "降维与聚类"
  },
  {
    "term": "marker gene",
    "aliases": [
      "marker",
      "标记基因"
    ],
    "definition": "标记基因：某细胞类型高表达、其他类型低表达的基因，用来注释细胞类型。",
    "category": "注释与验证"
  },
  {
    "term": "dotplot",
    "aliases": [
      "dot plot",
      "点图"
    ],
    "definition": "点图：点大小=表达该基因的细胞比例，颜色=组内平均表达；常用于检查 marker。",
    "category": "注释与验证"
  },
  {
    "term": "细胞类型注释",
    "aliases": [
      "cell type annotation",
      "cell annotation"
    ],
    "definition": "用 marker/参考标签给簇命名；是有置信度的假说，不是绝对真理。",
    "category": "注释与验证"
  },
  {
    "term": "ARI",
    "aliases": [
      "adjusted Rand index",
      "调整兰德指数"
    ],
    "definition": "调整兰德指数：比较两种分组的一致性，1=完全一致，0≈随机；对稀有类型不敏感。",
    "category": "注释与验证"
  },
  {
    "term": "label transfer",
    "aliases": [
      "标签转移"
    ],
    "definition": "用参考图谱的标签映射到新数据；依赖参考的细胞类型覆盖和批次相似性。",
    "category": "注释与验证"
  },
  {
    "term": "pseudobulk",
    "aliases": [
      "伪批量",
      "pseudo-bulk"
    ],
    "definition": "伪批量：把同一供者/样本的细胞聚合后再做 DE，避免把细胞当独立重复。",
    "category": "统计与差异表达"
  },
  {
    "term": "伪重复",
    "aliases": [
      "pseudoreplication",
      "pseudo-replication"
    ],
    "definition": "把同一供者的细胞当独立样本，低估标准误、夸大显著性；单细胞 DE 最常见的错误。",
    "category": "统计与差异表达"
  },
  {
    "term": "差异表达",
    "aliases": [
      "DE",
      "differential expression"
    ],
    "definition": "比较两组间基因表达均值/比例；本教程用供者水平 pseudobulk，而不是细胞水平 t 检验。",
    "category": "统计与差异表达"
  },
  {
    "term": "FDR",
    "aliases": [
      "false discovery rate",
      "错误发现率"
    ],
    "definition": "错误发现率：多重检验校正后，被判为显著的基因中预期假阳性的比例。",
    "category": "统计与差异表达"
  },
  {
    "term": "BH",
    "aliases": [
      "Benjamini-Hochberg",
      "Benjamini–Hochberg"
    ],
    "definition": "Benjamini-Hochberg：最常用的 FDR 校正方法；本教程用 BH 校正所有检验基因。",
    "category": "统计与差异表达"
  },
  {
    "term": "log2FC",
    "aliases": [
      "log2 fold change",
      "log2 倍数变化"
    ],
    "definition": "log2 倍数变化：效应量，T2D 与对照的表达比值取 log2；比 p 值更能说明差异大小。",
    "category": "统计与差异表达"
  },
  {
    "term": "效应量",
    "aliases": [
      "effect size"
    ],
    "definition": "差异的大小（如 log2FC、Cohen's d），与 p 值不同；大 n 下微小效应也可能显著。",
    "category": "统计与差异表达"
  },
  {
    "term": "置信区间",
    "aliases": [
      "confidence interval",
      "CI"
    ],
    "definition": "效应量的不确定性范围；比单个 p 值更能说明估计的精度。",
    "category": "统计与差异表达"
  },
  {
    "term": "协变量",
    "aliases": [
      "covariate",
      "covariates"
    ],
    "definition": "模型中调整的变量，如年龄、性别、BMI、批次；目的是控制混杂。",
    "category": "统计与差异表达"
  },
  {
    "term": "混杂因素",
    "aliases": [
      "confounder",
      "confounding",
      "混杂"
    ],
    "definition": "同时与分组和结局相关，可能制造假关联；疾病与批次共线时尤其危险。",
    "category": "统计与差异表达"
  },
  {
    "term": "检验效能",
    "aliases": [
      "power",
      "statistical power"
    ],
    "definition": "真实效应存在时检出它的概率；取决于样本量、效应量和噪声。16 名供者对中等效应可能不足。",
    "category": "统计与差异表达"
  },
  {
    "term": "混合模型",
    "aliases": [
      "mixed model",
      "mixed-effects model"
    ],
    "definition": "含固定效应和随机效应（如供者随机截距）的模型，用来处理同一供者细胞的相关性。",
    "category": "统计与差异表达"
  },
  {
    "term": "DESeq2",
    "aliases": [
      "deseq2"
    ],
    "definition": "基于负二项分布的 bulk RNA-seq DE 方法；常用于 pseudobulk counts。",
    "category": "统计与差异表达"
  },
  {
    "term": "limma-voom",
    "aliases": [
      "limma voom",
      "voom"
    ],
    "definition": "线性模型 + voom 权重，常用于 bulk/pseudobulk counts；对中小样本较稳健。",
    "category": "统计与差异表达"
  },
  {
    "term": "PyDESeq2",
    "aliases": [
      "pydeseq2"
    ],
    "definition": "DESeq2 的 Python 实现，可用于 pseudobulk counts 的差异表达。",
    "category": "统计与差异表达"
  },
  {
    "term": "成分数据",
    "aliases": [
      "compositional data"
    ],
    "definition": "各类型比例总和为 1 的数据；普通 t 检验/ANOVA 不完全适用，可用 CLR/ILR、scCODA、propeller。",
    "category": "统计与差异表达"
  },
  {
    "term": "scCODA",
    "aliases": [
      "scCODA"
    ],
    "definition": "单细胞组成数据的贝叶斯模型，考虑成分性质，用于检验细胞类型比例变化。",
    "category": "统计与差异表达"
  },
  {
    "term": "propeller",
    "aliases": [
      "propeller"
    ],
    "definition": "基于 log-ratio 的组成数据检验方法，适合细胞类型比例的比较。",
    "category": "统计与差异表达"
  },
  {
    "term": "double dipping",
    "aliases": [
      "double-dipping",
      "双重 dipping"
    ],
    "definition": "用同一数据先选特征（如 HVG/DE 基因）再做检验，p 值会偏小；应独立数据或预设特征。",
    "category": "常见陷阱"
  },
  {
    "term": "P-hacking",
    "aliases": [
      "p-hacking",
      "p值操纵"
    ],
    "definition": "反复换阈值/模型/协变量直到显著；会破坏结果可信度，应预注册分析计划。",
    "category": "常见陷阱"
  },
  {
    "term": "ground truth",
    "aliases": [
      "金标准"
    ],
    "definition": "独立验证的真实标签；作者注释通常只是参考，不是严格 ground truth。",
    "category": "常见陷阱"
  },
  {
    "term": "inDrop",
    "aliases": [
      "indrop"
    ],
    "definition": "液滴微流控 scRNA-seq 平台；GSE84133 使用 inDrop，UMI counts 与 10x 类似但建库不同。",
    "category": "常见陷阱"
  }
];
