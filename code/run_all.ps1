# Run all analysis steps from the project root.
# Data must already be downloaded into data/ (see data/README.md).
$ErrorActionPreference = "Stop"
$env:NUMBA_DISABLE_INTEL_SVML = "1"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

python code/00_prepare_data.py
python code/01_baron_cluster.py
python code/02_baron_annotate.py
python code/03_gse81608_cluster.py
python code/04_gse81608_de.py
python code/05_report_figures.py
python code/06_session_info.py
python code/07_build_html.py

Write-Host "Done. Open REPORT.html or REPORT.md."
