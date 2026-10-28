# Raw data provenance

All files are public. They are **not** redistributed with this tutorial; download
them into this `data/` directory with the commands below.

## 1. GSE84133 — Baron et al., Cell Systems 2016

GEO series: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE84133

Human pancreatic islet cells, inDrop UMI-filtered counts. We use the four human
samples only; the two mouse samples are not needed for this tutorial.

| Sample | GSM | Donor | Condition | Age | Sex | BMI | Cells |
|---|---|---|---|---|---|---|---|
| human1 | GSM2230757 | D1 | Control | 17 | M | 21.5 | 1,937 |
| human2 | GSM2230758 | D2 | Control | 51 | F | 21.1 | 1,724 |
| human3 | GSM2230759 | D3 | Control | 38 | M | 27.5 | 3,605 |
| human4 | GSM2230760 | D4 | T2D | 59 | F | 29.9 | 1,303 |

Direct URLs (sample-level supplementary files):

- https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2230nnn/GSM2230757/suppl/GSM2230757_human1_umifm_counts.csv.gz
- https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2230nnn/GSM2230758/suppl/GSM2230758_human2_umifm_counts.csv.gz
- https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2230nnn/GSM2230759/suppl/GSM2230759_human3_umifm_counts.csv.gz
- https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM2230nnn/GSM2230760/suppl/GSM2230760_human4_umifm_counts.csv.gz

Metadata source: `GSE84133-GPL16791_series_matrix.txt.gz` (series matrix).

## 2. GSE81608 — Xin et al., Cell Metabolism 2016

GEO series: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE81608

Gene-level RPKM matrix, 1,600 cell columns from 18 donors (12 non-diabetic,
6 T2D). The associated paper reports 1,492 cells after its own filtering; the
GEO matrix contains 1,600 columns, so the exact cell set differs slightly.

- Matrix: https://ftp.ncbi.nlm.nih.gov/geo/series/GSE81nnn/GSE81608/suppl/GSE81608_human_islets_rpkm.txt.gz
- Metadata: https://ftp.ncbi.nlm.nih.gov/geo/series/GSE81nnn/GSE81608/matrix/GSE81608_series_matrix.txt.gz

The first column contains Entrez GeneIDs, mapped to HGNC symbols with:

- https://ftp.ncbi.nlm.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz

## 3. Download helper

The NCBI FTP server can be slow from some networks. `code/download_ranges.py`
splits each gzip file into byte ranges and downloads them in parallel; gzip is a
byte stream, so concatenating the ranges in order reconstructs the file exactly.

```powershell
python code/download_ranges.py `
  "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE81nnn/GSE81608/suppl/GSE81608_human_islets_rpkm.txt.gz" `
  "data/GSE81608_human_islets_rpkm.txt.gz" --workers 8 --chunk-mb 4
```

## 4. SHA256 checksums

| File | Bytes | SHA256 |
|---|---:|---|
| GSM2230757_human1_umifm_counts.csv.gz | 5,670,823 | 6FDEE6C7F0C2C3098F851C761D7FAFA4F9A359AF200703258F7FDA255DDD3E69 |
| GSM2230758_human2_umifm_counts.csv.gz | 4,960,352 | 376BBEA51A35096B56E3E30B36E33B8A43EAD9ABCF5C5C87B4FCBFD04E76D5D7 |
| GSM2230759_human3_umifm_counts.csv.gz | 9,767,500 | 187C77C0914043E2D56253A634B8CAD5194EF87A64109E4F824DF303FF5C215F |
| GSM2230760_human4_umifm_counts.csv.gz | 4,253,067 | FD54CC3D83E213AC473632B2B938F608D48378C48FB1E0D0F7919CF2EFA41E86 |
| GSE81608_human_islets_rpkm.txt.gz | 37,222,002 | 2F7A64A5A6FA6F44E6B6B4BEF122608B3C2E6FC163B3B3B36487BF88204F2025 |
| GSE81608_series_matrix.txt.gz | 44,214 | D7CC1F4C1527F1EBE8AAFB9BD5F640F0B844276D4C0390968C0756568DBE397A |
| GSE84133_series_matrix.txt.gz | 3,149 | 0F8F3D82F7CE3FB81161C09738E0BBF05C6626A1A28A32EE4A81D1FA5E476509 |
| Homo_sapiens.gene_info.gz | 5,199,342 | 8A1C9AB8B86A1B924D0AF9E48DDD818F2D715857212D474A318EB8026585F17B |
