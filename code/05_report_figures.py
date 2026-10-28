"""Create summary metrics and report figures from saved analysis outputs."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"
RES = ROOT / "results"

SUMMARY = [
    dict(
        dataset="GSE84133 (Baron 2016)",
        assay="inDrop UMI counts",
        cells_raw=8569,
        genes_raw=20125,
        cells_after_qc=8531,
        genes_after_qc=16353,
        donors=4,
        groups="3 control, 1 T2D",
        clusters=19,
        cell_types=11,
        ari=0.968,
        use="unsupervised atlas / annotation",
    ),
    dict(
        dataset="GSE81608 (Xin 2016)",
        assay="gene-level RPKM",
        cells_raw=1600,
        genes_raw=39851,
        cells_after_qc=1600,
        genes_after_qc=39851,
        donors=18,
        groups="12 control, 6 T2D",
        clusters=8,
        cell_types=4,
        ari=0.856,
        use="T2D vs control pseudobulk DE",
    ),
]

NAIVE_LABEL = "Cell-level\n(naive, n=503 cells)"
PB_LABEL = "Pseudobulk\nT2D vs control\n(16 donors)"
PC_LABEL = "Pseudobulk\nbeta vs alpha\n(14 paired donors)"


def main() -> None:
    metrics = pd.DataFrame(SUMMARY)
    metrics.to_csv(RES / "summary_metrics.csv", index=False)
    print(metrics.to_string(index=False))

    naive = pd.read_csv(RES / "gse81608_beta_celllevel_naive_de.csv")
    pb = pd.read_csv(RES / "gse81608_beta_pseudobulk_de.csv")
    pc = pd.read_csv(RES / "gse81608_beta_vs_alpha_positive_control.csv")

    n_naive = int((naive["padj"] < 0.05).sum())
    n_pb = int((pb["padj"] < 0.05).sum())
    n_pc = int((pc["padj"] < 0.05).sum())
    comparison = pd.DataFrame(
        {
            "analysis": ["cell-level naive", "pseudobulk T2D vs control",
                         "pseudobulk beta vs alpha"],
            "genes_tested": [len(naive), len(pb), len(pc)],
            "significant_fdr_0.05": [n_naive, n_pb, n_pc],
        }
    )
    comparison.to_csv(RES / "de_method_comparison.csv", index=False)
    print(comparison.to_string(index=False))

    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    labels = [NAIVE_LABEL, PB_LABEL, PC_LABEL]
    counts = [n_naive, n_pb, n_pc]
    tested = [len(naive), len(pb), len(pc)]
    colors = ["#F58518", "#B0B0B0", "#54A24B"]
    bars = ax.bar(labels, counts, color=colors, width=0.6)
    for bar, c, t in zip(bars, counts, tested):
        ax.text(bar.get_x() + bar.get_width() / 2, c + max(counts) * 0.02,
                f"{c:,} / {t:,}", ha="center", fontsize=8)
    ax.set_ylabel("Genes at FDR < 0.05")
    ax.set_title("The same data, three analysis choices")
    ax.set_ylim(0, max(counts) * 1.18)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / "de_method_comparison.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    # p-value diagnostics for the pseudobulk T2D test
    p = pb["p"].dropna().to_numpy()
    p = p[np.isfinite(p)]
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.5))
    axes[0].hist(p, bins=20, color="#4C78A8", edgecolor="white")
    axes[0].axhline(len(p) / 20, color="grey", ls="--", lw=0.8)
    axes[0].set_xlabel("p-value")
    axes[0].set_ylabel("Genes")
    axes[0].set_title("Pseudobulk p-values are uniform")
    axes[0].spines[["top", "right"]].set_visible(False)

    obs = -np.log10(np.sort(p))
    exp = -np.log10(np.arange(1, len(p) + 1) / (len(p) + 1))
    axes[1].scatter(exp, obs, s=3, color="#4C78A8", alpha=0.55, linewidth=0)
    lim = max(exp.max(), obs.max()) * 1.03
    axes[1].plot([0, lim], [0, lim], color="grey", ls="--", lw=0.8)
    axes[1].set_xlabel("Expected -log10(p)")
    axes[1].set_ylabel("Observed -log10(p)")
    axes[1].set_title("QQ plot: no global T2D signal")
    axes[1].spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / "gse81608_pvalue_diagnostics.png", dpi=220,
                bbox_inches="tight")
    plt.close(fig)

    print("wrote summary metrics and DE figures")


if __name__ == "__main__":
    main()
