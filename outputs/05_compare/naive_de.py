"""普通简短提示词轮：直接按组均值差排序，不做统计检验。

仅用于实验对照，不是 de-analysis Skill 的一部分。
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expression", required=True)
    parser.add_argument("--groups", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    expr = pd.read_csv(args.expression, encoding="utf-8-sig")
    groups = pd.read_csv(args.groups, encoding="utf-8-sig")
    control = groups.loc[groups["group"] == "control", "sample"].tolist()
    treat = groups.loc[groups["group"] == "treat", "sample"].tolist()

    # 直接用原始 counts 的组均值差，没有 CPM、log 转换、P 值或校正
    expr["mean_diff"] = expr[treat].mean(axis=1) - expr[control].mean(axis=1)
    expr["abs_diff"] = expr["mean_diff"].abs()
    top = expr.sort_values("abs_diff", ascending=False).head(20)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    top[["gene_id", "mean_diff", "abs_diff"]].to_csv(
        out_dir / "naive_de_top20.csv", index=False, encoding="utf-8-sig"
    )
    print(top[["gene_id", "mean_diff"]].to_string(index=False))


if __name__ == "__main__":
    main()
