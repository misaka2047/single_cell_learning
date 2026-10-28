"""Annotate Baron clusters with canonical markers and quantify composition.

The 19 Leiden clusters are deliberately merged into 12 major cell types.
Two rare author-labelled populations (epsilon cells, n=18; T cells, n=7)
are not recovered as independent clusters at this resolution; this is
reported rather than hidden.
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
from sklearn.metrics import adjusted_rand_score, confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
FIG = ROOT / "figures"
RES = ROOT / "results"
FIG.mkdir(exist_ok=True)
RES.mkdir(exist_ok=True)

CLUSTER_TO_TYPE = {
    "0": "Acinar",
    "1": "Beta",
    "2": "Beta",
    "3": "Beta",
    "4": "Delta",
    "5": "Stellate",
    "6": "Schwann",
    "7": "Ductal",
    "8": "Alpha",
    "9": "Alpha",
    "10": "Alpha",
    "11": "Ductal",
    "12": "Beta",
    "13": "PP",
    "14": "Endothelial",
    "15": "Ductal",
    "16": "Macrophage",
    "17": "Mast",
    "18": "Ductal",
}

# Optional finer label for clusters that correspond to known substates.
CLUSTER_TO_SUBTYPE = {
    **CLUSTER_TO_TYPE,
    "2": "Beta (ER-stress high)",
    "5": "Stellate (activated)",
    "18": "Ductal (REG+)",
}


def main() -> None:
    a = sc.read_h5ad(DATA / "baron_clustered.h5ad")
    a.obs["cell_type"] = (
        a.obs["leiden"].astype(str).map(CLUSTER_TO_TYPE).astype("category")
    )
    a.obs["subtype"] = (
        a.obs["leiden"].astype(str).map(CLUSTER_TO_SUBTYPE).astype("category")
    )
    if a.obs["cell_type"].isna().any():
        raise ValueError("unmapped Leiden cluster")

    # Annotation quality against the author's labels (not ground truth,
    # but an independent check on the marker-based calls).
    labels = a.obs["author_label"].astype(str)
    pred = a.obs["cell_type"].astype(str)
    ari = adjusted_rand_score(labels, pred)
    pd.Series({"adjusted_rand_index": ari}).to_csv(
        RES / "baron_annotation_ari.csv"
    )
    cm = pd.crosstab(pred, labels)
    cm.to_csv(RES / "baron_annotation_confusion.csv")
    print(f"ARI vs author labels: {ari:.3f}")
    print(cm.to_string())

    # Composition per donor.
    comp = pd.crosstab(a.obs["donor"], a.obs["cell_type"])
    comp_pct = comp.div(comp.sum(axis=1), axis=0) * 100
    comp_pct.round(2).to_csv(RES / "baron_celltype_composition_pct.csv")
    comp.to_csv(RES / "baron_celltype_counts.csv")
    print(comp_pct.round(1).to_string())

    # Stacked bar by donor, with condition annotation.
    donors = list(comp_pct.index)
    cond = a.obs.groupby("donor", observed=True)["condition"].first()
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    bottom = np.zeros(len(donors))
    colors = plt.cm.tab20(np.linspace(0, 1, comp_pct.shape[1]))
    for j, ct in enumerate(comp_pct.columns):
        vals = comp_pct[ct].values
        ax.bar(donors, vals, bottom=bottom, label=ct, color=colors[j], width=0.72)
        bottom += vals
    ax.set_ylabel("% of cells")
    ax.set_xlabel("Donor")
    ax.set_title("Cell-type composition (one T2D donor, three controls)")
    ax.set_xticks(range(len(donors)))
    ax.set_xticklabels([f"{d}\n{cond[d]}" for d in donors])
    ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "baron_composition_by_donor.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    # Beta-cell fraction per donor (descriptive; n=1 T2D donor).
    beta_pct = comp_pct.get("Beta", pd.Series(0, index=comp_pct.index))
    fig, ax = plt.subplots(figsize=(4.2, 3.2))
    ax.scatter(
        np.arange(len(beta_pct)),
        beta_pct.values,
        c=["#E45756" if cond[d] == "T2D" else "#4C78A8" for d in beta_pct.index],
        s=70,
    )
    ax.set_xticks(range(len(beta_pct)))
    ax.set_xticklabels(beta_pct.index)
    ax.set_ylabel("Beta cells (% of islet cells)")
    ax.set_title("Beta-cell fraction")
    for i, v in enumerate(beta_pct.values):
        ax.text(i, v + 1, f"{v:.1f}%", ha="center", fontsize=8)
    ax.set_ylim(0, max(beta_pct.values) * 1.25)
    fig.tight_layout()
    fig.savefig(FIG / "baron_beta_fraction.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    # UMAP with final labels
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    sc.pl.umap(
        a,
        color="cell_type",
        ax=axes[0],
        show=False,
        title="Annotated cell types",
        legend_fontsize=8,
    )
    sc.pl.umap(
        a,
        color="subtype",
        ax=axes[1],
        show=False,
        title="Subtypes retained for beta/acinar/stellate",
        legend_fontsize=7,
    )
    fig.tight_layout()
    fig.savefig(FIG / "baron_umap_annotated.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    # Marker dotplot by final cell type
    markers = {
        "Beta": ["INS", "IAPP", "MAFA", "NKX6-1", "PDX1", "UCN3"],
        "Alpha": ["GCG", "IRX2", "ARX", "TTR"],
        "Delta": ["SST", "HHEX", "LEPR"],
        "PP": ["PPY"],
        "Acinar": ["CPA1", "CELA3A", "PRSS1"],
        "Ductal": ["KRT19", "CFTR", "MUC1", "TFF1"],
        "Endothelial": ["PECAM1", "VWF", "CDH5"],
        "Stellate": ["COL1A1", "PDGFRB", "RGS5"],
        "Macrophage": ["CD68", "LYZ", "C1QA"],
        "Mast": ["TPSAB1", "CPA3"],
        "Schwann": ["SOX10", "PLP1"],
    }
    dp = sc.pl.dotplot(
        a,
        markers,
        groupby="cell_type",
        standard_scale="var",
        use_raw=True,
        show=False,
        figsize=(11, 4.8),
        return_fig=True,
    )
    dp.savefig(FIG / "baron_dotplot_celltype.png", dpi=220, bbox_inches="tight")
    plt.close("all")

    # Marker table by final cell type for the report.
    sc.tl.rank_genes_groups(
        a, "cell_type", method="wilcoxon", use_raw=True, n_genes=50
    )
    rows = []
    for grp in a.obs["cell_type"].cat.categories:
        df = sc.get.rank_genes_groups_df(a, group=grp)
        df["cell_type"] = grp
        rows.append(df)
    pd.concat(rows, ignore_index=True).to_csv(
        RES / "baron_celltype_markers.csv", index=False
    )

    a.write_h5ad(DATA / "baron_annotated.h5ad")
    print("wrote", DATA / "baron_annotated.h5ad")


if __name__ == "__main__":
    main()
