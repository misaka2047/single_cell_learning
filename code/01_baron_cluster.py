"""Baron/GSE84133: QC, normalization, HVG, PCA, UMAP, Leiden clustering.

No mitochondrial fraction is available: the processed GEO matrix contains
only the 20,125 protein-coding genes retained by the authors and no MT- genes.
QC therefore uses detected genes and total UMI counts only.
"""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("NUMBA_DISABLE_INTEL_SVML", "1")

import anndata as ad
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scanpy as sc

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
FIG = ROOT / "figures"
RES = ROOT / "results"
FIG.mkdir(exist_ok=True)
RES.mkdir(exist_ok=True)

SEED = 42
np.random.seed(SEED)
sc.settings.verbosity = 1
sc.settings.set_figure_params(dpi=150, frameon=False, figsize=(5, 4))


def main() -> None:
    a = sc.read_h5ad(DATA / "baron_raw.h5ad")
    print(a)
    a.var["mt"] = a.var_names.str.upper().str.startswith("MT-")
    sc.pp.calculate_qc_metrics(
        a, qc_vars=["mt"], percent_top=[50], log1p=False, inplace=True
    )
    a.obs["log10_total_counts"] = np.log10(a.obs["total_counts"].clip(lower=1))

    qc_cols = ["n_genes_by_counts", "total_counts", "pct_counts_in_top_50_genes"]
    qc_summary = (
        a.obs.groupby(["donor", "condition"], observed=True)[qc_cols]
        .agg(["median", "min", "max"])
        .round(2)
    )
    qc_summary.to_csv(RES / "baron_qc_by_donor.csv")
    print(qc_summary)

    # QC thresholds chosen from the 1st percentile of the full dataset.
    print("before QC:", a.shape)
    sc.pp.filter_cells(a, min_genes=800)
    sc.pp.filter_cells(a, min_counts=1500)
    sc.pp.filter_cells(a, max_genes=5000)
    sc.pp.filter_genes(a, min_cells=3)
    print("after QC:", a.shape)
    a.obs["n_genes_detected"] = a.obs["n_genes_by_counts"]
    a.obs["total_umi"] = a.obs["total_counts"]

    # QC figure (post-filter distributions, per donor)
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
    sc.pl.violin(
        a, "n_genes_detected", groupby="donor", ax=axes[0], show=False, rotation=0
    )
    sc.pl.violin(a, "total_umi", groupby="donor", ax=axes[1], show=False, rotation=0)
    fig.tight_layout()
    fig.savefig(FIG / "baron_qc_violin.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    # Normalization: counts per 10k, log1p. Keep raw log-normalized matrix
    # for marker testing after subsetting to HVGs.
    a.layers["counts"] = a.X.copy()
    sc.pp.normalize_total(a, target_sum=1e4)
    sc.pp.log1p(a)
    a.layers["lognorm"] = a.X.copy()
    a.raw = a

    sc.pp.highly_variable_genes(
        a, n_top_genes=2000, batch_key="donor", flavor="seurat"
    )
    print("HVGs:", int(a.var["highly_variable"].sum()))
    a = a[:, a.var["highly_variable"]].copy()
    sc.pp.scale(a, max_value=10)

    sc.tl.pca(a, n_comps=50, svd_solver="arpack", random_state=SEED)
    sc.pp.neighbors(a, n_neighbors=15, n_pcs=30, random_state=SEED)
    sc.tl.umap(a, random_state=SEED)
    sc.tl.leiden(
        a,
        resolution=0.6,
        random_state=SEED,
        flavor="igraph",
        n_iterations=2,
        directed=False,
        key_added="leiden",
    )
    print(a.obs["leiden"].value_counts().sort_index().to_string())

    # Cluster markers on the full log-normalized matrix (raw).
    sc.tl.rank_genes_groups(
        a, "leiden", method="wilcoxon", use_raw=True, n_genes=100
    )
    frames = []
    for grp in a.obs["leiden"].cat.categories:
        df = sc.get.rank_genes_groups_df(a, group=grp)
        df["cluster"] = grp
        frames.append(df)
    markers = pd.concat(frames, ignore_index=True)
    markers.to_csv(RES / "baron_cluster_markers.csv", index=False)

    top = (
        markers.query("pvals_adj < 0.05")
        .sort_values(["cluster", "logfoldchanges"], ascending=[True, False])
        .groupby("cluster", observed=True)
        .head(8)
    )
    top.to_csv(RES / "baron_cluster_top_markers.csv", index=False)

    # UMAP panels
    fig, axes = plt.subplots(2, 2, figsize=(10, 9))
    sc.pl.umap(
        a, color="leiden", ax=axes[0, 0], show=False, legend_loc="on data",
        legend_fontsize=8, title="Leiden clusters",
    )
    sc.pl.umap(
        a, color="donor", ax=axes[0, 1], show=False, title="Donor",
        palette="tab10",
    )
    sc.pl.umap(
        a, color="condition", ax=axes[1, 0], show=False, title="Condition",
        palette={"Control": "#4C78A8", "T2D": "#E45756"},
    )
    sc.pl.umap(
        a, color="author_label", ax=axes[1, 1], show=False, title="Author label",
        legend_fontsize=6,
    )
    fig.tight_layout()
    fig.savefig(FIG / "baron_umap_overview.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    # Dotplot of canonical markers, split endocrine / non-endocrine.
    endocrine = {
        "Beta": ["INS", "IAPP", "MAFA", "NKX6-1", "PDX1", "UCN3"],
        "Alpha": ["GCG", "IRX2", "ARX", "TTR"],
        "Delta": ["SST", "HHEX", "LEPR"],
        "PP": ["PPY", "S100B"],
        "Epsilon": ["GHRL"],
    }
    nonendo = {
        "Acinar": ["CPA1", "CELA3A", "PRSS1", "AMY2A"],
        "Ductal": ["KRT19", "CFTR", "MUC1", "TFF1"],
        "Endothelial": ["PECAM1", "VWF", "CDH5"],
        "Stellate": ["COL1A1", "PDGFRB", "RGS5", "ACTA2"],
        "Immune": ["CD68", "LYZ", "C1QA", "TPSAB1", "CD3D"],
        "Schwann": ["SOX10", "PLP1", "S100B"],
    }
    for name, m in [("endocrine", endocrine), ("nonendocrine", nonendo)]:
        dp = sc.pl.dotplot(
            a,
            m,
            groupby="leiden",
            standard_scale="var",
            use_raw=True,
            show=False,
            figsize=(9, 4.2),
            return_fig=True,
        )
        dp.savefig(FIG / f"baron_dotplot_{name}.png", dpi=220, bbox_inches="tight")
        plt.close("all")

    a.write_h5ad(DATA / "baron_clustered.h5ad")
    print("wrote", DATA / "baron_clustered.h5ad")
    print("wrote figures to", FIG)


if __name__ == "__main__":
    main()
