window.COURSE = [
  {
    "num": "1",
    "slug": "paradigm",
    "title": "研究范式：先写清楚你要回答的问题",
    "short": "把“我想做单细胞”变成一个可检验的问题",
    "duration": "35 min",
    "keywords": "研究范式, 推断单位, 供者, 伪重复, 发现与验证, 分析计划"
  },
  {
    "num": "2",
    "slug": "databases",
    "title": "数据库检索：如何找到“能用的”公共数据",
    "short": "不是所有 GSE 都能支撑你的问题",
    "duration": "45 min",
    "keywords": "GEO, CELLxGENE, Human Cell Atlas, HPAP, 数据库, metadata, 数据选择"
  },
  {
    "num": "3",
    "slug": "download",
    "title": "下载与工程化：把 GEO 变成可分析的项目",
    "short": "文件、校验、metadata 对齐，一个都不能少",
    "duration": "50 min",
    "keywords": "GEO下载, series matrix, curl, SHA256, metadata, 文件结构, 数据工程"
  },
  {
    "num": "4",
    "slug": "anndata",
    "title": "AnnData 与基因 ID：单细胞数据的“底盘”",
    "short": "把 CSV/RPKM 变成 scanpy 能理解的对象",
    "duration": "45 min",
    "keywords": "AnnData, scanpy, obs, var, layers, Entrez, 基因ID, 稀疏矩阵"
  },
  {
    "num": "5",
    "slug": "qc",
    "title": "QC：哪些细胞应该被删掉",
    "short": "先看分布，再定阈值；不要机械套用 20% 线粒体",
    "duration": "50 min",
    "keywords": "QC, 质控, 线粒体, 双细胞, Scrublet, 空液滴, 阈值, nGene, UMI"
  },
  {
    "num": "6",
    "slug": "normalization",
    "title": "归一化与 HVG：把不同细胞放到同一把尺子上",
    "short": "counts 和 RPKM 不能用同一套归一化",
    "duration": "45 min",
    "keywords": "归一化, CP10k, log1p, RPKM, HVG, 高变基因, scale, double dipping"
  },
  {
    "num": "7",
    "slug": "clustering",
    "title": "降维与聚类：从 2 万个基因到一张 UMAP",
    "short": "PCA、kNN、UMAP、Leiden，以及“聚类数 ≠ 细胞类型数”",
    "duration": "55 min",
    "keywords": "PCA, UMAP, Leiden, kNN, resolution, 聚类, 批次, Harmony, 降维"
  },
  {
    "num": "8",
    "slug": "annotation",
    "title": "细胞类型注释：marker、标签与验证",
    "short": "把 19 个簇变成 11 类细胞，并知道置信边界",
    "duration": "50 min",
    "keywords": "细胞注释, marker, dotplot, ARI, 混淆矩阵, 稀有细胞, 注释验证"
  },
  {
    "num": "9",
    "slug": "composition",
    "title": "组成分析：比例变化到底说明了什么",
    "short": "按供者算比例，不要把细胞混在一起算",
    "duration": "40 min",
    "keywords": "细胞组成, 比例, 成分数据, scCODA, propeller, 胰岛纯度, β细胞"
  },
  {
    "num": "10",
    "slug": "de",
    "title": "差异表达：为什么必须做 pseudobulk",
    "short": "同一个数据集，1,217 个“显著” vs 0 个显著",
    "duration": "75 min",
    "keywords": "差异表达, pseudobulk, 伪重复, FDR, DESeq2, limma, 协变量, 阳性对照"
  },
  {
    "num": "11",
    "slug": "interpretation",
    "title": "结果解读：阴性结果、阳性对照与可发表的表述",
    "short": "0 个显著基因，怎么写才不被审稿人挑错",
    "duration": "45 min",
    "keywords": "结果解读, 阴性结果, 阳性对照, 效应量, 置信区间, 论文写作"
  },
  {
    "num": "12",
    "slug": "reproducibility",
    "title": "可复现性与下一步：把项目做成“能重跑”的研究",
    "short": "目录、环境、种子、版本、检查清单",
    "duration": "45 min",
    "keywords": "可复现性, 随机种子, session info, 排错, 肥胖, GSE176171, HPAP, 下一步"
  },
  {
    "num": "A",
    "slug": "appendix",
    "title": "附录：命令速查、文件地图与术语表",
    "short": "卡住时先来这里查",
    "duration": "参考",
    "keywords": "附录, 命令, 文件, 术语, 排错, 速查"
  }
];
