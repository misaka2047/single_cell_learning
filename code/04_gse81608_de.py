"""GSE81608: annotate clusters, composition, and donor-level pseudobulk DE.

Why pseudobulk?
  Cells from one donor are not independent observations. Testing T2D vs
  control on thousands of cells treats one donor as thousands of replicates
  (pseudo-replication) and inflates significance. We therefore average RPKM
  within each donor x cell type, then fit one model per gene across donors.
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
import seaborn as sns
from scipy import stats
from sklearn.metrics import adjusted_rand_score
from statsmodels.stats.multitest import multipletests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
FIG = ROOT / "figures"
RES = ROOT / "results"
FIG.mkdir(exist_ok=True)
RES.mkdir(exist_ok=True)

SEED = 42
np.random.seed(SEED)

CLUSTER_TO_TYPE = {
    "0": "Alpha",
    "1": "Beta",
    "2": "Alpha",
    "3": "Alpha",
    "4": "Alpha",
    "5": "Alpha",
    "6": "Delta",
    "7": "PP",
}


def annotate() -> sc.AnnData:
    a = sc.read_h5ad(DATA / "gse81608_clustered.h5ad")
    a.obs["cell_type"] = (
        a.obs["leiden"].astype(str).map(CLUSTER_TO_TYPE).astype("category")
    )
    if a.obs["cell_type"].isna().any():
        raise ValueError("unmapped cluster")
    ari = adjusted_rand_score(
        a.obs["author_label"].astype(str), a.obs["cell_type"].astype(str)
    )
    pd.Series({"adjusted_rand_index": ari}).to_csv(
        RES / "gse81608_annotation_ari.csv"
    )
    pd.crosstab(
        a.obs["cell_type"].astype(str), a.obs["author_label"].astype(str)
    ).to_csv(RES / "gse81608_annotation_confusion.csv")
    print(f"ARI vs author labels: {ari:.3f}")
    print(
        pd.crosstab(
            a.obs["cell_type"].astype(str), a.obs["author_label"].astype(str)
        ).to_string()
    )

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    sc.pl.umap(
        a,
        color="cell_type",
        ax=axes[0],
        show=False,
        title="Annotated cell types",
        legend_fontsize=9,
    )
    sc.pl.umap(
        a,
        color="condition",
        ax=axes[1],
        show=False,
        title="Condition",
        palette={"Control": "#4C78A8", "T2D": "#E45756"},
    )
    fig.tight_layout()
    fig.savefig(FIG / "gse81608_umap_annotated.png", dpi=220, bbox_inches="tight")
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
        groupby="cell_type",
        standard_scale="var",
        use_raw=True,
        show=False,
        figsize=(6.5, 3.8),
        return_fig=True,
    )
    dp.savefig(FIG / "gse81608_dotplot_celltype.png", dpi=220, bbox_inches="tight")
    plt.close("all")
    a.write_h5ad(DATA / "gse81608_annotated.h5ad")
    return a


def composition(a: sc.AnnData) -> None:
    # Curated author labels are used here so that composition is independent
    # of our clustering choices.
    counts = pd.crosstab(a.obs["donor"], a.obs["author_label"])
    pct = counts.div(counts.sum(axis=1), axis=0) * 100
    pct.round(2).to_csv(RES / "gse81608_composition_pct.csv")
    cond = a.obs.groupby("donor", observed=True)["condition"].first()

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
    bottom = np.zeros(len(pct))
    colors = {"alpha": "#F58518", "beta": "#54A24B", "delta": "#E45756",
              "PP": "#4C78A8"}
    for ct in ["alpha", "beta", "delta", "PP"]:
        vals = pct[ct].values
        axes[0].bar(
            np.arange(len(pct)), vals, bottom=bottom, label=ct,
            color=colors[ct], width=0.75,
        )
        bottom += vals
    axes[0].set_xticks(np.arange(len(pct)))
    axes[0].set_xticklabels(
        [f"{d}\n{cond[d]}" for d in pct.index], rotation=90, fontsize=6
    )
    axes[0].set_ylabel("% of cells")
    axes[0].set_title("Islet-cell composition per donor")
    axes[0].legend(fontsize=7, frameon=False, ncol=4, loc="upper center",
                   bbox_to_anchor=(0.5, -0.35))

    beta_pct = pct["beta"]
    groups = [beta_pct[cond.index[cond == c]].values for c in ["Control", "T2D"]]
    axes[1].boxplot(groups, tick_labels=["Control", "T2D"], widths=0.5,
                    showfliers=False)
    for i, (g, c) in enumerate(zip(groups, ["#4C78A8", "#E45756"])):
        x = np.random.default_rng(SEED).normal(i + 1, 0.06, len(g))
        axes[1].scatter(x, g, color=c, s=28, alpha=0.85, edgecolor="white")
    u = stats.mannwhitneyu(groups[0], groups[1], alternative="two-sided")
    axes[1].set_ylabel("Beta cells (% of cells)")
    axes[1].set_title(f"Beta fraction (Mann-Whitney p={u.pvalue:.3f})")
    fig.tight_layout()
    fig.savefig(FIG / "gse81608_composition.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    pd.DataFrame(
        {
            "control_median_beta_pct": [np.median(groups[0])],
            "t2d_median_beta_pct": [np.median(groups[1])],
            "mannwhitney_p": [u.pvalue],
            "n_control": [len(groups[0])],
            "n_t2d": [len(groups[1])],
        }
    ).to_csv(RES / "gse81608_beta_fraction_test.csv", index=False)


def naive_celllevel_de() -> None:
    """Deliberately wrong analysis: treat every cell as an independent sample."""
    raw = sc.read_h5ad(DATA / "gse81608_raw.h5ad")
    beta = raw[raw.obs["author_label"].astype(str) == "beta"].copy()
    X = beta.layers["rpkm"].toarray()
    X = np.log2(X + 1)
    is_t2d = (beta.obs["condition"] == "T2D").to_numpy()
    tstat, pval = stats.ttest_ind(
        X[is_t2d], X[~is_t2d], axis=0, equal_var=False
    )
    pval = np.nan_to_num(pval, nan=1.0)
    padj = multipletests(pval, method="fdr_bh")[1]
    res = pd.DataFrame(
        {
            "gene": beta.var_names,
            "log2FC_T2D_vs_Control": X[is_t2d].mean(0) - X[~is_t2d].mean(0),
            "p": pval,
            "padj": padj,
        }
    ).sort_values("p")
    res.to_csv(RES / "gse81608_beta_celllevel_naive_de.csv", index=False)
    n_sig = int((res["padj"] < 0.05).sum())
    print(
        f"[naive cell-level] {n_sig:,}/{len(res):,} genes at FDR<0.05 "
        "(pseudo-replication; do not interpret biologically)"
    )
    print(res.head(10)[["gene", "log2FC_T2D_vs_Control", "padj"]].to_string(index=False))


def positive_control_de() -> None:
    """Beta vs alpha pseudobulk: a positive control that the DE engine works."""
    raw = sc.read_h5ad(DATA / "gse81608_raw.h5ad")
    rows = {}
    for ct in ["alpha", "beta"]:
        sub = raw[raw.obs["author_label"].astype(str) == ct]
        d = {}
        for donor, s in sub.obs.groupby("donor", observed=True):
            if len(s) < 10:
                continue
            idx = sub.obs_names.get_indexer(s.index)
            d[donor] = np.asarray(sub.layers["rpkm"][idx].mean(axis=0)).ravel()
        rows[ct] = pd.DataFrame(d, index=raw.var_names).T
    common = rows["alpha"].index.intersection(rows["beta"].index)
    A = np.log2(rows["alpha"].loc[common].to_numpy() + 1)
    B = np.log2(rows["beta"].loc[common].to_numpy() + 1)
    genes = raw.var_names
    keep = ((rows["alpha"].loc[common] > 1).sum(0) >= len(common) * 0.5) | (
        (rows["beta"].loc[common] > 1).sum(0) >= len(common) * 0.5
    )
    A, B, genes = A[:, keep], B[:, keep], genes[keep]
    tstat, pval = stats.ttest_rel(B, A, axis=0)
    pval = np.nan_to_num(pval, nan=1.0)
    padj = multipletests(pval, method="fdr_bh")[1]
    res = pd.DataFrame(
        {
            "gene": genes,
            "log2FC_Beta_vs_Alpha": (B - A).mean(axis=0),
            "p": pval,
            "padj": padj,
            "n_paired_donors": len(common),
        }
    ).sort_values("p")
    res.to_csv(RES / "gse81608_beta_vs_alpha_positive_control.csv", index=False)
    print(
        f"[positive control beta vs alpha] "
        f"{int((res['padj'] < 0.05).sum()):,}/{len(res):,} genes at FDR<0.05, "
        f"{len(common)} paired donors"
    )
    print(res.head(12)[["gene", "log2FC_Beta_vs_Alpha", "padj"]].to_string(index=False))


def pseudobulk_de() -> pd.DataFrame:
    raw = sc.read_h5ad(DATA / "gse81608_raw.h5ad")
    beta = raw[raw.obs["author_label"].astype(str) == "beta"].copy()
    print("beta cells:", beta.n_obs)

    rows, meta_rows = [], []
    for donor, sub in beta.obs.groupby("donor", observed=True):
        if len(sub) < 10:
            continue
        idx = beta.obs_names.get_indexer(sub.index)
        mean_rpkm = np.asarray(beta.layers["rpkm"][idx].mean(axis=0)).ravel()
        rows.append(mean_rpkm)
        meta_rows.append(
            {
                "donor": donor,
                "condition": sub["condition"].iloc[0],
                "age": sub["age"].iloc[0],
                "sex": sub["sex"].iloc[0],
                "n_beta": len(sub),
            }
        )
    pb = pd.DataFrame(rows, index=[m["donor"] for m in meta_rows],
                      columns=beta.var_names)
    meta = pd.DataFrame(meta_rows).set_index("donor")
    print(meta.to_string())
    pb.to_csv(RES / "gse81608_beta_pseudobulk_rpkm.csv")
    meta.to_csv(RES / "gse81608_beta_pseudobulk_meta.csv")

    expressed = (pb > 1).sum(axis=0) >= max(6, int(0.5 * len(pb)))
    genes = pb.columns[expressed]
    print(f"genes tested: {len(genes):,} / {pb.shape[1]:,}")
    Y = np.log2(pb[genes].to_numpy() + 1)  # donors x genes

    n = len(pb)
    is_t2d = (meta["condition"] == "T2D").astype(float).to_numpy()
    age = meta["age"].to_numpy(dtype=float)
    age = (age - age.mean()) / age.std(ddof=0)
    is_male = (meta["sex"] == "M").astype(float).to_numpy()
    X = np.column_stack([np.ones(n), is_t2d, age, is_male])

    coef, _, rank, _ = np.linalg.lstsq(X, Y, rcond=None)
    resid = Y - X @ coef
    dof = n - rank
    sigma2 = (resid ** 2).sum(axis=0) / dof
    xtx_inv = np.linalg.inv(X.T @ X)
    se = np.sqrt(sigma2 * xtx_inv[1, 1])
    tstat = coef[1] / np.where(se > 0, se, np.nan)
    pval = 2 * stats.t.sf(np.abs(tstat), dof)
    pval = np.nan_to_num(pval, nan=1.0)
    padj = multipletests(pval, method="fdr_bh")[1]

    res = pd.DataFrame(
        {
            "gene": genes,
            "log2FC_T2D_vs_Control": coef[1],
            "t": tstat,
            "p": pval,
            "padj": padj,
            "mean_rpkm_control": pb.loc[meta["condition"] == "Control", genes].mean().values,
            "mean_rpkm_t2d": pb.loc[meta["condition"] == "T2D", genes].mean().values,
            "n_donors": n,
        }
    ).sort_values("p")
    res.to_csv(RES / "gse81608_beta_pseudobulk_de.csv", index=False)

    sig = res[(res["padj"] < 0.05) & (res["log2FC_T2D_vs_Control"].abs() > 0.5)]
    print(
        f"DE at FDR<0.05 & |log2FC|>0.5: {len(sig):,} "
        f"({(sig['log2FC_T2D_vs_Control'] > 0).sum()} up, "
        f"{(sig['log2FC_T2D_vs_Control'] < 0).sum()} down)"
    )
    print(sig.head(20)[["gene", "log2FC_T2D_vs_Control", "padj"]].to_string(index=False))

    # Volcano
    fig, ax = plt.subplots(figsize=(5.6, 4.6))
    x = res["log2FC_T2D_vs_Control"]
    y = -np.log10(res["padj"].clip(lower=1e-300))
    sig_mask = (res["padj"] < 0.05) & (x.abs() > 0.5)
    ax.scatter(x[~sig_mask], y[~sig_mask], s=4, c="#B0B0B0", alpha=0.5, linewidth=0)
    ax.scatter(x[sig_mask & (x > 0)], y[sig_mask & (x > 0)], s=8, c="#E45756",
               alpha=0.8, linewidth=0, label="Up in T2D")
    ax.scatter(x[sig_mask & (x < 0)], y[sig_mask & (x < 0)], s=8, c="#4C78A8",
               alpha=0.8, linewidth=0, label="Down in T2D")
    ax.axhline(-np.log10(0.05), ls="--", c="grey", lw=0.8)
    ax.axvline(0, ls="-", c="grey", lw=0.5)
    known = ["INS", "IAPP", "MAFA", "NKX6-1", "PDX1", "UCN3", "SLC2A2",
             "HSPA5", "DDIT3", "HERPUD1", "ATF4", "XBP1"]
    for g in known:
        hit = res[res["gene"] == g]
        if not hit.empty:
            ax.annotate(g, (hit["log2FC_T2D_vs_Control"].iloc[0],
                            -np.log10(max(hit["padj"].iloc[0], 1e-300))),
                        fontsize=6, alpha=0.9)
    ax.set_xlabel("log2 fold change (T2D / Control)")
    ax.set_ylabel("-log10 FDR")
    ax.set_title(f"Beta-cell pseudobulk DE (n={n} donors)")
    ax.legend(fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "gse81608_beta_volcano.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    # Selected-gene donor-level plots
    selected = ["INS", "IAPP", "MAFA", "PDX1", "UCN3", "SLC2A2",
                "HSPA5", "DDIT3"]
    selected = [g for g in selected if g in res["gene"].values]
    fig, axes = plt.subplots(2, 4, figsize=(11, 5.2))
    rng = np.random.default_rng(SEED)
    for ax, g in zip(axes.ravel(), selected):
        vals = np.log2(pb[g].to_numpy() + 1)
        for i, c in enumerate(["Control", "T2D"]):
            mask = (meta["condition"] == c).to_numpy()
            v = vals[mask]
            ax.boxplot([v], positions=[i], widths=0.55, showfliers=False)
            ax.scatter(i + rng.normal(0, 0.05, len(v)), v,
                       c="#4C78A8" if c == "Control" else "#E45756",
                       s=18, alpha=0.9, edgecolor="white", linewidth=0.3)
        row = res[res["gene"] == g].iloc[0]
        ax.set_title(f"{g}\nFDR={row['padj']:.2g}", fontsize=8)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Ctrl", "T2D"], fontsize=7)
        ax.set_ylabel("log2(RPKM+1)", fontsize=7)
        ax.tick_params(labelsize=7)
    for ax in axes.ravel()[len(selected):]:
        ax.axis("off")
    fig.suptitle("Beta-cell pseudobulk expression by donor", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "gse81608_beta_selected_genes.png", dpi=220,
                bbox_inches="tight")
    plt.close(fig)

    # Top-gene heatmap (donor x gene, z-scored)
    top = res[sig_mask].head(30)["gene"].tolist()
    if top:
        mat = np.log2(pb[top].to_numpy() + 1)
        z = (mat - mat.mean(axis=0)) / np.where(mat.std(axis=0) == 0, 1,
                                                mat.std(axis=0))
        order = np.argsort((meta["condition"] == "T2D").to_numpy())
        fig, ax = plt.subplots(figsize=(7.2, 3.8))
        im = ax.imshow(z[order].T, aspect="auto", cmap="RdBu_r", vmin=-2, vmax=2)
        ax.set_xticks(range(len(order)))
        ax.set_xticklabels(
            [f"{meta.index[i]}\n{meta['condition'].iloc[i]}" for i in order],
            rotation=90, fontsize=6,
        )
        ax.set_yticks(range(len(top)))
        ax.set_yticklabels(top, fontsize=6)
        ax.set_title("Top DE genes in beta cells (z-score)")
        fig.colorbar(im, ax=ax, shrink=0.7, label="z-score")
        fig.tight_layout()
        fig.savefig(FIG / "gse81608_beta_top_heatmap.png", dpi=220,
                    bbox_inches="tight")
        plt.close(fig)
    return res


def enrichment(res: pd.DataFrame) -> None:
    """Optional Enrichr query; skipped cleanly if the service is unreachable."""
    try:
        import gseapy as gp
    except Exception as exc:  # noqa: BLE001
        print("gseapy unavailable:", exc)
        return
    sig = res[(res["padj"] < 0.05) & (res["log2FC_T2D_vs_Control"].abs() > 0.5)]
    up = sig[sig["log2FC_T2D_vs_Control"] > 0].head(200)["gene"].tolist()
    down = sig[sig["log2FC_T2D_vs_Control"] < 0].head(200)["gene"].tolist()
    if not up and not down:
        print("no significant genes for enrichment")
        return
    outs = []
    for label, genes in [("up", up), ("down", down)]:
        if len(genes) < 5:
            continue
        try:
            enr = gp.enrichr(
                gene_list=genes,
                gene_sets=["MSigDB_Hallmark_2020", "KEGG_2021_Human"],
                organism="human",
                outdir=None,
            )
            df = enr.results.copy()
            df["direction"] = label
            df["n_genes"] = len(genes)
            outs.append(df)
        except Exception as exc:  # noqa: BLE001
            print(f"enrichr failed for {label}: {exc}")
    if outs:
        out = pd.concat(outs, ignore_index=True)
        out.to_csv(RES / "gse81608_beta_enrichment.csv", index=False)
        print("enrichment terms:", len(out))


if __name__ == "__main__":
    a = annotate()
    composition(a)
    naive_celllevel_de()
    positive_control_de()
    res = pseudobulk_de()
    enrichment(res)
