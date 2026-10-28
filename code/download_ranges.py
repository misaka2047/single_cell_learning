"""Parallel HTTP range downloader for GEO supplementary files.

Gzip files are byte streams, so downloading disjoint byte ranges and
concatenating them in order reconstructs the original .gz exactly.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import os
import time
import urllib.request
from pathlib import Path


def head_size(url: str, timeout: int = 60) -> int:
    req = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return int(r.headers["Content-Length"])


def fetch_range(url: str, start: int, end: int, out: Path, retries: int = 5) -> int:
    headers = {"Range": f"bytes={start}-{end}", "User-Agent": "single-cell-tutorial/1.0"}
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=180) as r:
                data = r.read()
            expected = end - start + 1
            if len(data) != expected:
                raise IOError(f"short read: {len(data)} != {expected}")
            out.write_bytes(data)
            return len(data)
        except Exception as exc:  # noqa: BLE001
            if attempt == retries:
                raise
            print(f"  retry {attempt}/{retries} {out.name}: {exc}", flush=True)
            time.sleep(2 * attempt)
    return 0


def download(url: str, dest: Path, workers: int = 6, chunk_mb: int = 2) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"exists: {dest} ({dest.stat().st_size/1e6:.1f} MB)")
        return
    size = head_size(url)
    chunk = chunk_mb * 1024 * 1024
    ranges = [(i, min(i + chunk - 1, size - 1)) for i in range(0, size, chunk)]
    parts_dir = dest.parent / (dest.name + ".parts")
    parts_dir.mkdir(exist_ok=True)
    print(f"{dest.name}: {size/1e6:.1f} MB in {len(ranges)} chunks, {workers} workers", flush=True)

    t0 = time.time()
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {
            ex.submit(fetch_range, url, a, b, parts_dir / f"{i:05d}.part"): (i, a, b)
            for i, (a, b) in enumerate(ranges)
        }
        done = 0
        for fut in cf.as_completed(futures):
            i, a, b = futures[fut]
            fut.result()
            done += b - a + 1
            print(f"  {done/1e6:.1f}/{size/1e6:.1f} MB  {done/(time.time()-t0)/1e3:.0f} KB/s", flush=True)

    with dest.open("wb") as out:
        for i in range(len(ranges)):
            out.write((parts_dir / f"{i:05d}.part").read_bytes())
    print(f"wrote {dest} ({dest.stat().st_size/1e6:.1f} MB) in {time.time()-t0:.0f}s", flush=True)
    for p in parts_dir.glob("*.part"):
        p.unlink()
    parts_dir.rmdir()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("dest")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--chunk-mb", type=int, default=2)
    args = ap.parse_args()
    download(args.url, Path(args.dest), args.workers, args.chunk_mb)
