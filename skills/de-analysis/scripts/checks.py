#!/usr/bin/env python
"""独立核验差异分析结果：文件、字段、数值一致性与阈值一致性。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import data_io  # noqa: E402
import stats_utils  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="核验 de-analysis 的输出")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--expression", required=True)
    parser.add_argument("--groups", required=True)
    parser.add_argument("--group-a", required=True)
    parser.add_argument("--group-b", required=True)
    parser.add_argument("--truth", default=None, help="可选真值表（gene_id,is_de）")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out = Path(args.output_dir)
    checks: list[dict] = []

    def add(name: str, passed: bool, detail: str = "") -> None:
        checks.append({"check": name, "passed": bool(passed), "detail": detail})

    def finish() -> int:
        payload = {
            "passed": all(item["passed"] for item in checks),
            "checks": checks,
        }
        data_io.write_json(out / "checks.json", payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["passed"] else 1

    required = [
        "de_results.csv",
        "de_significant.csv",
        "volcano.png",
        "summary.md",
        "analysis_config.json",
        "validation.json",
    ]
    missing = [name for name in required if not (out / name).exists()]
    add("必需文件齐全", not missing, f"缺失：{missing}")
    if missing:
        return finish()

    config = json.loads((out / "analysis_config.json").read_text(encoding="utf-8"))
    res = pd.read_csv(out / "de_results.csv", encoding="utf-8-sig")
    sig = pd.read_csv(out / "de_significant.csv", encoding="utf-8-sig")
    expr, sample_cols = data_io.read_expression(args.expression)
    groups = data_io.read_groups(args.groups)

    expected_ids = expr["gene_id"].tolist()
    add(
        "基因数量与输入一致",
        len(res) == len(expected_ids),
        f"输入 {len(expected_ids)}，结果 {len(res)}",
    )
    add(
        "基因 ID 与输入一致",
        set(res["gene_id"]) == set(expected_ids),
        "按 gene_id 集合比较",
    )

    columns = {
        "gene_id",
        "mean_a",
        "mean_b",
        "base_mean",
        "log2FoldChange",
        "pvalue",
        "padj",
        "zero_variance",
        "significant",
    }
    add("结果字段完整", columns.issubset(res.columns), f"缺少：{sorted(columns - set(res.columns))}")

    numeric = res[["log2FoldChange", "pvalue", "padj", "base_mean"]].to_numpy(float)
    add("关键数值无缺失/无穷", bool(np.isfinite(numeric).all()), "")
    add(
        "P 值与 padj 在 [0,1]",
        bool(
            res["pvalue"].between(0, 1).all()
            and res["padj"].between(0, 1).all()
        ),
        f"pvalue 范围 {res['pvalue'].min():.3g}~{res['pvalue'].max():.3g}；"
        f"padj 范围 {res['padj'].min():.3g}~{res['padj'].max():.3g}",
    )

    # 重新计算，核对表格中的数值确实由脚本按同一配置产生
    data_type, _ = data_io.detect_data_type(
        expr, sample_cols, config.get("data_type", "auto")
    )
    log_expr, _ = data_io.to_log_expression(expr, sample_cols, data_type)
    a_samples = groups.loc[groups["group"] == args.group_a, "sample"].tolist()
    b_samples = groups.loc[groups["group"] == args.group_b, "sample"].tolist()
    stat = stats_utils.compute_stats(log_expr, a_samples, b_samples, config["test"])
    padj = stats_utils.bh_fdr(stat["pvalue"])

    aligned = res.set_index("gene_id").reindex(expected_ids)
    max_lfc_diff = float(
        np.max(np.abs(aligned["log2FoldChange"].to_numpy() - stat["log2FoldChange"]))
    )
    max_p_diff = float(
        np.max(np.abs(aligned["pvalue"].to_numpy() - stat["pvalue"]))
    )
    max_padj_diff = float(np.max(np.abs(aligned["padj"].to_numpy() - padj)))
    add("log2FoldChange 可复算", max_lfc_diff < 1e-6, f"最大偏差 {max_lfc_diff:.2e}")
    add("pvalue 可复算", max_p_diff < 1e-6, f"最大偏差 {max_p_diff:.2e}")
    add("padj 可复算", max_padj_diff < 1e-6, f"最大偏差 {max_padj_diff:.2e}")

    expected_sig = (res["padj"] < config["padj_threshold"]) & (
        res["log2FoldChange"].abs() >= config["log2fc_threshold"]
    )
    add(
        "显著标记与阈值一致",
        bool((expected_sig == res["significant"]).all()),
        f"阈值：|log2FC|>={config['log2fc_threshold']}，"
        f"padj<{config['padj_threshold']}",
    )
    add(
        "显著基因表与结果表一致",
        set(sig["gene_id"]) == set(res.loc[res["significant"], "gene_id"]),
        f"显著表 {len(sig)} 行，结果表标记 {int(res['significant'].sum())} 行",
    )

    summary = (out / "summary.md").read_text(encoding="utf-8")
    add(
        "说明包含比较方向",
        args.group_a in summary and args.group_b in summary,
        f"{args.group_a} -> {args.group_b}",
    )

    volcano = out / "volcano.png"
    add("火山图非空", volcano.stat().st_size > 1024, f"{volcano.stat().st_size} bytes")

    if args.truth:
        truth = pd.read_csv(args.truth, encoding="utf-8-sig")
        truth_ids = set(truth.loc[truth["is_de"].astype(int) == 1, "gene_id"])
        sig_ids = set(sig["gene_id"])
        tp = len(truth_ids & sig_ids)
        recall = tp / len(truth_ids) if truth_ids else float("nan")
        precision = tp / len(sig_ids) if sig_ids else float("nan")
        add(
            "与真值对比",
            True,
            f"真差异基因 {len(truth_ids)}，检出 {tp}，"
            f"召回率 {recall:.3f}，精确率 {precision:.3f}",
        )

    return finish()


if __name__ == "__main__":
    raise SystemExit(main())
