"""GSE81608 (Xin 2016): QC, log2 transform, clustering, marker discovery.

The GEO matrix is gene-level RPKM (not UMI counts), so:
  * no mitochondrial fraction / doublet detection is possible;
  * normalization is log2(RPKM + 1), not counts-per-10k;
  * differential expression later uses donor-level pseudobulk, never
    cell-level Wilcoxon tests.
"""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("NUMBA_DISABLE_INTEL_SVML", "1")

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


def main() -> None:
    a = sc.read_h5ad(DATA / "gse81608_raw.h5ad")
    a.var["mt"] = a.var_names.str.upper().str.startswith("MT-")
    sc.pp.calculate_qc_metrics(
        a, qc_vars=["mt"], percent_top=None, log1p=False, inplace=True
    )
    print(a)
    print(a.obs.groupby(["condition"], observed=True).size().to_string())
    print(a.obs.groupby(["donor", "condition"], observed=True).size().to_string())
    print(
        a.obs.groupby("author_label", observed=True)[
            ["n_genes_by_counts", "total_counts"]
        ]
        .median()
        .round(0)
        .to_string()
    )
    qc = (
        a.obs.groupby(["donor", "condition"], observed=True)["n_genes_by_counts"]
        .agg(["median", "min", "max", "count"])
        .round(1)
    )
    qc.to_csv(RES / "gse81608_qc_by_donor.csv")

    # No cells are removed: every cell detects >2,400 genes. We keep the
    # author-curated matrix intact and record the QC instead of applying an
    # arbitrary threshold.
    a.layers["log2rpkm"] = a.X.copy()
    a.X = a.X.copy()
    a.X.data = np.log2(a.X.data + 1)
    a.raw = a

    fig, ax = plt.subplots(figsize=(8, 3.2))
    sc.pl.violin(
        a,
        "n_genes_by_counts",
        groupby="donor",
        ax=ax,
        show=False,
        rotation=90,
        size=0,
    )
    ax.set_title("Detected genes per cell (RPKM > 0)")
    fig.tight_layout()
    fig.savefig(FIG / "gse81608_qc_genes.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

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
        resolution=0.4,
        random_state=SEED,
        flavor="igraph",
        n_iterations=2,
        directed=False,
        key_added="leiden",
    )
    print(a.obs["leiden"].value_counts().sort_index().to_string())

    sc.tl.rank_genes_groups(
        a, "leiden", method="wilcoxon", use_raw=True, n_genes=50
    )
    frames = []
    for grp in a.obs["leiden"].cat.categories:
        df = sc.get.rank_genes_groups_df(a, group=grp)
        df["cluster"] = grp
        frames.append(df)
    pd.concat(frames, ignore_index=True).to_csv(
        RES / "gse81608_cluster_markers.csv", index=False
    )

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    sc.pl.umap(
        a,
        color="leiden",
        ax=axes[0],
        show=False,
        legend_loc="on data",
        legend_fontsize=9,
        title="Leiden clusters",
    )
    sc.pl.umap(
        a,
        color="condition",
        ax=axes[1],
        show=False,
        title="Condition",
        palette={"Control": "#4C78A8", "T2D": "#E45756"},
    )
    sc.pl.umap(
        a,
        color="author_label",
        ax=axes[2],
        show=False,
        title="Author label",
        legend_fontsize=8,
    )
    fig.tight_layout()
    fig.savefig(FIG / "gse81608_umap_overview.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    markers = {
        "Beta": ["INS", "IAPP", "MAFA", "NKX6-1", "PDX1", "UCN3", "SLC2A2"],
        "Alpha": ["GCG", "IRX2", "ARX", "TTR"],
        "Delta": ["SST", "HHEX", "LEPR"],
        "PP": ["PPY"],
    }
    dp = sc.pl.dotplot(
        a,
        markers,
        groupby="leiden",
        standard_scale="var",
        use_raw=True,
        show=False,
        figsize=(8, 4),
        return_fig=True,
    )
    dp.savefig(FIG / "gse81608_dotplot_markers.png", dpi=220, bbox_inches="tight")
    plt.close("all")

    a.write_h5ad(DATA / "gse81608_clustered.h5ad")
    print("wrote", DATA / "gse81608_clustered.h5ad")


if __name__ == "__main__":
    main()
