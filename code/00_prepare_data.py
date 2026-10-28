"""Build AnnData objects from two public human islet datasets.

Dataset A: GSE84133 (Baron et al., Cell Systems 2016)
  4 human donors, inDrop UMI counts, author cell-type labels.
  Donor 4 is the only T2D donor; donors 1-3 are non-diabetic.

Dataset B: GSE81608 (Xin et al., Cell Metabolism 2016)
  1,600 single cells from 18 donors (6 T2D, 12 non-diabetic), RPKM,
  author labels for alpha/beta/delta/PP cells.

Outputs
-------
data/processed/baron_raw.h5ad
data/processed/gse81608_raw.h5ad
data/processed/gse81608_metadata.csv
"""
from __future__ import annotations

import gzip
import os
from pathlib import Path

os.environ.setdefault("NUMBA_DISABLE_INTEL_SVML", "1")

import anndata as ad
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "processed"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Dataset A: Baron / GSE84133
# ---------------------------------------------------------------------------
BARON = {
    "human1": dict(
        path=DATA / "GSM2230757_human1_umifm_counts.csv.gz",
        donor="D1", condition="Control", age=17, sex="M", bmi=21.5,
        sample="GSM2230757",
    ),
    "human2": dict(
        path=DATA / "GSM2230758_human2_umifm_counts.csv.gz",
        donor="D2", condition="Control", age=51, sex="F", bmi=21.1,
        sample="GSM2230758",
    ),
    "human3": dict(
        path=DATA / "GSM2230759_human3_umifm_counts.csv.gz",
        donor="D3", condition="Control", age=38, sex="M", bmi=27.5,
        sample="GSM2230759",
    ),
    "human4": dict(
        path=DATA / "GSM2230760_human4_umifm_counts.csv.gz",
        donor="D4", condition="T2D", age=59, sex="F", bmi=29.9,
        sample="GSM2230760",
    ),
}


def build_baron() -> ad.AnnData:
    adatas = []
    for key, meta in BARON.items():
        print(f"reading {key}: {meta['path'].name}")
        df = pd.read_csv(
            meta["path"],
            dtype={0: str, 1: str, 2: str},
            low_memory=False,
        )
        obs = pd.DataFrame(
            {
                "cell_id": df.iloc[:, 0].astype(str).values,
                "barcode": df.iloc[:, 1].astype(str).values,
                "author_label": df.iloc[:, 2].astype(str).values,
                "donor": meta["donor"],
                "condition": meta["condition"],
                "age": meta["age"],
                "sex": meta["sex"],
                "bmi": meta["bmi"],
                "sample": meta["sample"],
            },
            index=df.iloc[:, 0].astype(str).values,
        )
        genes = pd.Index(df.columns[3:].astype(str))
        X = csr_matrix(df.iloc[:, 3:].to_numpy(dtype=np.float32))
        a = ad.AnnData(X=X, obs=obs, var=pd.DataFrame(index=genes))
        a.var_names_make_unique()
        a.obs_names_make_unique()
        a.layers["counts"] = a.X.copy()
        adatas.append(a)
        print(f"  {a.n_obs:,} cells x {a.n_vars:,} genes")

    adata = ad.concat(
        adatas,
        axis=0,
        join="outer",
        merge="same",
        fill_value=0,
        index_unique=None,
        label=None,
    )
    adata.obs["condition"] = pd.Categorical(
        adata.obs["condition"], categories=["Control", "T2D"]
    )
    adata.obs["donor"] = pd.Categorical(adata.obs["donor"])
    adata.obs["author_label"] = adata.obs["author_label"].astype("category")
    adata.uns["dataset"] = "GSE84133 (Baron 2016)"
    adata.uns["counts_note"] = "inDrop UMI-filtered counts, raw (not normalized)"
    adata.write_h5ad(OUT / "baron_raw.h5ad")
    print("wrote", OUT / "baron_raw.h5ad", adata.shape)
    return adata


# ---------------------------------------------------------------------------
# Dataset B: Xin / GSE81608
# ---------------------------------------------------------------------------
def read_series_metadata() -> pd.DataFrame:
    """Parse the 1,600 per-cell GEO characteristics columns."""
    fields: dict[str, list[str]] = {}
    with gzip.open(DATA / "GSE81608_series_matrix.txt.gz", "rt", errors="replace") as fh:
        for line in fh:
            if not line.startswith("!Sample_characteristics_ch1"):
                continue
            vals = [x.strip().strip('"') for x in line.rstrip("\n").split("\t")[1:]]
            key = vals[0].split(":", 1)[0].strip()
            fields[key] = vals
    n = len(next(iter(fields.values())))
    meta = pd.DataFrame(
        {k: [v.split(":", 1)[1].strip() for v in vals] for k, vals in fields.items()},
        index=[f"Sample_{i}" for i in range(1, n + 1)],
    )
    meta = meta.rename(
        columns={
            "donor id": "donor",
            "cell subtype": "author_label",
            "gender": "sex",
        }
    )
    meta["condition"] = meta["condition"].replace(
        {"non-diabetic": "Control", "T2D": "T2D"}
    )
    meta["age"] = pd.to_numeric(meta["age"], errors="coerce")
    meta["donor"] = meta["donor"].str.replace(" ", "_", regex=False)
    return meta


def build_gse81608() -> ad.AnnData:
    print("reading GSE81608 RPKM matrix (this may take ~30 s)")
    rpkm = pd.read_csv(
        DATA / "GSE81608_human_islets_rpkm.txt.gz",
        sep="\t",
        index_col=0,
        dtype={0: str},
        low_memory=False,
    )
    print("  raw matrix", rpkm.shape, "(genes x cells)")
    meta = read_series_metadata()
    if list(rpkm.columns) != list(meta.index):
        raise ValueError("matrix columns and GEO metadata order do not match")

    # Entrez GeneID -> HGNC symbol
    gene_info = pd.read_csv(
        DATA / "Homo_sapiens.gene_info.gz",
        sep="\t",
        dtype=str,
        low_memory=False,
        usecols=["GeneID", "Symbol"],
    ).drop_duplicates("GeneID")
    id2sym = dict(zip(gene_info["GeneID"], gene_info["Symbol"]))
    symbols = [id2sym.get(str(g), f"Entrez:{g}") for g in rpkm.index]
    n_mapped = sum(not s.startswith("Entrez:") for s in symbols)
    print(f"  mapped {n_mapped:,}/{len(symbols):,} Entrez IDs to symbols")

    adata = ad.AnnData(
        X=csr_matrix(rpkm.T.to_numpy(dtype=np.float32)),
        obs=meta.copy(),
        var=pd.DataFrame(index=pd.Index(symbols)),
    )
    adata.var_names_make_unique()
    adata.obs_names_make_unique()
    adata.obs["condition"] = pd.Categorical(
        adata.obs["condition"], categories=["Control", "T2D"]
    )
    adata.obs["donor"] = adata.obs["donor"].astype("category")
    adata.obs["author_label"] = adata.obs["author_label"].astype("category")
    adata.layers["rpkm"] = adata.X.copy()
    adata.uns["dataset"] = "GSE81608 (Xin 2016)"
    adata.uns["counts_note"] = "gene-level RPKM; not UMI counts"
    adata.write_h5ad(OUT / "gse81608_raw.h5ad")
    meta.to_csv(OUT / "gse81608_metadata.csv")
    print("wrote", OUT / "gse81608_raw.h5ad", adata.shape)
    print(adata.obs["condition"].value_counts().to_string())
    return adata


if __name__ == "__main__":
    build_baron()
    build_gse81608()
