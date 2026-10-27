#!/usr/bin/env python
"""给 de-analysis 的结果表补上基因名称。

用法：
    python TCGA-KIRC/annotate_results.py \
        --results outputs/07_tcga_kirc/de_results.csv \
        --annotation TCGA-KIRC/gene_annotation.tsv \
        --outdir outputs/07_tcga_kirc

输出：
    de_results_annotated.csv      全部基因 + gene_name + gene_type
    de_significant_annotated.csv  显著基因 + gene_name + gene_type（按 padj 升序）
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="为差异分析结果补基因名称")
    parser.add_argument("--results", required=True, help="de_results.csv")
    parser.add_argument("--annotation", required=True, help="gene_annotation.tsv")
    parser.add_argument("--outdir", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    res = pd.read_csv(args.results, encoding="utf-8-sig")
    ann = pd.read_csv(args.annotation, sep="\t", encoding="utf-8-sig")

    if "gene_id" not in ann.columns:
        raise SystemExit("注释表缺少 gene_id 列")
    ann = ann[["gene_id", "gene_name", "gene_type"]].drop_duplicates("gene_id")

    merged = res.merge(ann, on="gene_id", how="left")
    missing = int(merged["gene_name"].isna().sum())

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    merged.to_csv(outdir / "de_results_annotated.csv", index=False, encoding="utf-8-sig")

    sig = merged.loc[merged["significant"]].sort_values("padj")
    sig.to_csv(
        outdir / "de_significant_annotated.csv", index=False, encoding="utf-8-sig"
    )

    print(f"[完成] 注释 {len(merged)} 个基因，未匹配注释 {missing} 个；"
          f"显著基因 {len(sig)} 个。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
