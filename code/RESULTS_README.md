# Results guide

All tables are UTF-8 CSV unless noted.

## Dataset A: GSE84133 (Baron)

| File | Meaning |
|---|---|
| `baron_qc_by_donor.csv` | QC medians/min/max per donor before filtering |
| `baron_cluster_markers.csv` | Wilcoxon markers for all 19 Leiden clusters |
| `baron_cluster_top_markers.csv` | Top 8 markers per cluster |
| `baron_annotation_ari.csv` | ARI between marker-based labels and author labels |
| `baron_annotation_confusion.csv` | Confusion matrix (predicted type x author label) |
| `baron_celltype_counts.csv` | Cell counts per donor x cell type |
| `baron_celltype_composition_pct.csv` | Donor-level percentages |
| `baron_celltype_markers.csv` | Markers for the final merged cell types |

## Dataset B: GSE81608 (Xin)

| File | Meaning |
|---|---|
| `gse81608_qc_by_donor.csv` | Detected genes per donor |
| `gse81608_cluster_markers.csv` | Markers for the 8 Leiden clusters |
| `gse81608_annotation_ari.csv` | ARI between our labels and author labels |
| `gse81608_annotation_confusion.csv` | Confusion matrix |
| `gse81608_composition_pct.csv` | Author-label composition per donor |
| `gse81608_beta_fraction_test.csv` | Beta fraction: median and Mann-Whitney test |
| `gse81608_beta_pseudobulk_rpkm.csv` | Donor x gene pseudobulk RPKM (beta cells) |
| `gse81608_beta_pseudobulk_meta.csv` | Donor-level covariates and beta-cell counts |
| `gse81608_beta_pseudobulk_de.csv` | Primary DE result (T2D vs control) |
| `gse81608_beta_celllevel_naive_de.csv` | Deliberately naive cell-level DE (teaching counterexample) |
| `gse81608_beta_vs_alpha_positive_control.csv` | Positive-control DE (beta vs alpha) |
| `de_method_comparison.csv` | Significant-gene counts across the three analyses |
| `summary_metrics.csv` | Dataset-level summary |
| `session_info.txt` | Software versions |

## Key numbers

- GSE84133: 8,531 cells, 16,353 genes after QC; 19 clusters; 11 cell types;
  ARI 0.968.
- GSE81608: 1,600 cells, 18 donors; 503 beta cells; 16 donors with >=10 beta
  cells; 9,929 genes tested; 0 genes at FDR<0.05.
- Naive cell-level DE: 1,217/39,851 genes at FDR<0.05.
- Positive control beta vs alpha: 3,086/11,053 genes at FDR<0.05.
