"""Write a compact session-info file for reproducibility."""
from __future__ import annotations

import platform
import sys
from pathlib import Path

import importlib.metadata as md

ROOT = Path(__file__).resolve().parents[1]
pkgs = [
    "scanpy",
    "anndata",
    "numpy",
    "pandas",
    "scipy",
    "scikit-learn",
    "matplotlib",
    "seaborn",
    "statsmodels",
    "h5py",
    "umap-learn",
    "leidenalg",
    "igraph",
    "gseapy",
]
lines = [
    f"python: {sys.version}",
    f"platform: {platform.platform()}",
    f"machine: {platform.machine()}",
    "",
]
for p in pkgs:
    try:
        lines.append(f"{p}: {md.version(p)}")
    except md.PackageNotFoundError:
        lines.append(f"{p}: not installed")
(ROOT / "results").mkdir(exist_ok=True)
(ROOT / "results" / "session_info.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
