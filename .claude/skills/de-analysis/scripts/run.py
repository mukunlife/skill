#!/usr/bin/env python
"""两组基因表达差异分析入口。

用法示例：
    python scripts/run.py --expression examples/expression_demo.csv \
        --groups examples/groups_demo.csv --group-a control --group-b treat \
        --output-dir ../../outputs/03_skill_de
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import data_io  # noqa: E402
import stats_utils  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="两组样本基因表达差异分析")
    parser.add_argument("--expression", required=True, help="表达矩阵 CSV/TSV")
    parser.add_argument("--groups", required=True, help="分组表 CSV（sample,group）")
    parser.add_argument("--group-a", required=True, help="基准组")
    parser.add_argument("--group-b", required=True, help="比较组")
    parser.add_argument("--output-dir", required=True, help="输出目录")
    parser.add_argument(
        "--data-type",
        choices=["auto", "counts", "normalized"],
        default="auto",
        help="数据类型，默认自动判断",
    )
    parser.add_argument(
        "--test", choices=["welch", "mannwhitney"], default="welch", help="检验方法"
    )
    parser.add_argument("--log2fc", type=float, default=1.0, help="|log2FC| 阈值")
    parser.add_argument("--padj", type=float, default=0.05, help="padj 阈值")
    parser.add_argument(
        "--validate-only", action="store_true", help="只做样本与分组校验"
    )
    return parser.parse_args(argv)


def make_volcano(res: pd.DataFrame, path: Path, args: argparse.Namespace) -> None:
    y = -np.log10(res["padj"].clip(lower=1e-300))
    up = res["significant"] & (res["log2FoldChange"] > 0)
    down = res["significant"] & (res["log2FoldChange"] < 0)
    ns = ~res["significant"]

    fig, ax = plt.subplots(figsize=(7.2, 5.6), dpi=150)
    ax.scatter(
        res.loc[ns, "log2FoldChange"],
        y[ns],
        s=12,
        c="#9aa0a6",
        alpha=0.55,
        linewidths=0,
        label="Not significant",
    )
    ax.scatter(
        res.loc[up, "log2FoldChange"],
        y[up],
        s=16,
        c="#d62728",
        alpha=0.8,
        linewidths=0,
        label="Up in group-b",
    )
    ax.scatter(
        res.loc[down, "log2FoldChange"],
        y[down],
        s=16,
        c="#1f77b4",
        alpha=0.8,
        linewidths=0,
        label="Down in group-b",
    )
    ax.axvline(args.log2fc, color="#444444", linestyle="--", linewidth=0.8)
    ax.axvline(-args.log2fc, color="#444444", linestyle="--", linewidth=0.8)
    ax.axhline(-np.log10(args.padj), color="#444444", linestyle="--", linewidth=0.8)
    ax.set_xlabel("log2FoldChange (group-b vs group-a)")
    ax.set_ylabel("-log10(adjusted P)")
    ax.set_title(f"Volcano: {args.group_b} vs {args.group_a}")
    ax.legend(frameon=False, fontsize=8, loc="upper left")

    top = res.loc[res["significant"]].nsmallest(5, "padj")
    for gene_id, row in top.iterrows():
        ax.annotate(
            str(gene_id),
            (row["log2FoldChange"], -np.log10(max(row["padj"], 1e-300))),
            fontsize=7,
            xytext=(4, 3),
            textcoords="offset points",
        )
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def write_summary(
    path: Path,
    res: pd.DataFrame,
    args: argparse.Namespace,
    report: dict,
    data_type: str,
    data_reason: str,
    transform: str,
    nan_count: int,
    plot_ok: bool,
) -> None:
    n_sig = int(res["significant"].sum())
    n_up = int((res["significant"] & (res["log2FoldChange"] > 0)).sum())
    n_down = int((res["significant"] & (res["log2FoldChange"] < 0)).sum())
    n_a = len(report["samples_per_group"].get(args.group_a, []))
    n_b = len(report["samples_per_group"].get(args.group_b, []))

    top = res.loc[res["significant"]].nsmallest(10, "padj")
    if top.empty:
        top = res.nsmallest(10, "padj")

    lines = [
        "# 差异分析结果说明",
        "",
        f"- 比较方向：**{args.group_b} vs {args.group_a}**；"
        f"log2FoldChange > 0 表示在 {args.group_b} 中表达更高。",
        f"- 样本：{args.group_a} n={n_a}，{args.group_b} n={n_b}，共 {len(res)} 个基因。",
        f"- 数据类型：{data_type}（{data_reason}）。",
        f"- 预处理：{transform}。",
        f"- 检验方法：{'Welch t 检验' if args.test == 'welch' else 'Mann-Whitney U 检验'}（双侧）。",
        "- 多重检验校正：Benjamini-Hochberg（padj 为校正后 P 值）。",
        f"- 筛选标准：|log2FoldChange| >= {args.log2fc:g} 且 padj < {args.padj:g}。",
        f"- 结果：显著基因 **{n_sig}** 个（上调 {n_up}，下调 {n_down}）。",
        f"- 零方差基因：{int(res['zero_variance'].sum())} 个；"
        f"P 值为 NaN 后按 1 处理的基因：{nan_count} 个。",
        "",
        "## 前 10 个基因（按 padj 升序）",
        "",
        "| gene_id | log2FoldChange | pvalue | padj | 显著 |",
        "|---|---:|---:|---:|:---:|",
    ]
    for gene_id, row in top.iterrows():
        lines.append(
            f"| {gene_id} | {row['log2FoldChange']:.4f} | {row['pvalue']:.4g} | "
            f"{row['padj']:.4g} | {'是' if row['significant'] else '否'} |"
        )
    lines += [
        "",
        "## 校验与局限",
        "",
        "- 样本与分组校验：" + ("通过" if report["ok"] else "未通过") + "。",
    ]
    for warning in report["warnings"]:
        lines.append(f"- 提示：{warning}")
    if not plot_ok:
        lines.append("- 火山图生成失败，仅保留表格结果；需排查 matplotlib 环境。")
    lines += [
        "- 本方法在 log2 CPM 上做 Welch 检验，不等同于 DESeq2/edgeR 的负二项模型；",
        "  小样本或低表达基因较多时，P 值可能偏乐观，正式分析建议使用 DESeq2/edgeR 复核。",
        "- 火山图仅反映效应量与显著性，判断候选基因时还应结合 base_mean（表达丰度）。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.log2fc <= 0 or not 0 < args.padj <= 1:
        print("[参数错误] --log2fc 必须 > 0，--padj 必须在 (0, 1] 内")
        return 2

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        expr, sample_cols = data_io.read_expression(args.expression)
        groups = data_io.read_groups(args.groups)
        report = data_io.validate(
            expr, sample_cols, groups, args.group_a, args.group_b
        )
    except data_io.DataError as exc:
        report = {"ok": False, "errors": [str(exc)], "warnings": []}
        data_io.write_json(out_dir / "validation.json", report)
        print(f"[校验失败] {exc}")
        return 2

    data_io.write_json(out_dir / "validation.json", report)
    if not report["ok"]:
        for error in report["errors"]:
            print(f"[校验失败] {error}")
        return 2

    if args.validate_only:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        print("[校验通过] 未执行差异分析（--validate-only）")
        return 0

    try:
        data_type, data_reason = data_io.detect_data_type(
            expr, sample_cols, args.data_type
        )
        log_expr, transform = data_io.to_log_expression(
            expr, sample_cols, data_type
        )
    except data_io.DataError as exc:
        report["ok"] = False
        report["errors"].append(str(exc))
        data_io.write_json(out_dir / "validation.json", report)
        print(f"[数据处理失败] {exc}")
        return 2

    a_samples = report["samples_per_group"][args.group_a]
    b_samples = report["samples_per_group"][args.group_b]
    stat = stats_utils.compute_stats(log_expr, a_samples, b_samples, args.test)
    padj = stats_utils.bh_fdr(stat["pvalue"])

    res = pd.DataFrame(
        {
            "gene_id": expr["gene_id"].values,
            "mean_a": stat["mean_a"],
            "mean_b": stat["mean_b"],
            "base_mean": stat["base_mean"],
            "log2FoldChange": stat["log2FoldChange"],
            "pvalue": stat["pvalue"],
            "padj": padj,
            "zero_variance": stat["zero_variance"],
        }
    )
    res["significant"] = (res["padj"] < args.padj) & (
        res["log2FoldChange"].abs() >= args.log2fc
    )
    res = res.sort_values(["padj", "pvalue", "gene_id"]).reset_index(drop=True)
    res.to_csv(out_dir / "de_results.csv", index=False, encoding="utf-8-sig")
    res.loc[res["significant"]].to_csv(
        out_dir / "de_significant.csv", index=False, encoding="utf-8-sig"
    )

    plot_ok = True
    try:
        make_volcano(res.set_index("gene_id"), out_dir / "volcano.png", args)
    except Exception as exc:  # noqa: BLE001 - 缺图不应阻止表格结果
        plot_ok = False
        print(f"[提示] 火山图生成失败：{exc}")

    write_summary(
        out_dir / "summary.md",
        res.set_index("gene_id"),
        args,
        report,
        data_type,
        data_reason,
        transform,
        stat["nan_pvalue_count"],
        plot_ok,
    )

    config = {
        "skill": "de-analysis",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "expression": str(args.expression),
        "groups": str(args.groups),
        "group_a": args.group_a,
        "group_b": args.group_b,
        "data_type": data_type,
        "data_type_reason": data_reason,
        "transform": transform,
        "test": args.test,
        "log2fc_threshold": args.log2fc,
        "padj_threshold": args.padj,
        "n_genes": int(len(res)),
        "n_significant": int(res["significant"].sum()),
        "n_up": int((res["significant"] & (res["log2FoldChange"] > 0)).sum()),
        "n_down": int((res["significant"] & (res["log2FoldChange"] < 0)).sum()),
        "nan_pvalue_count": stat["nan_pvalue_count"],
        "zero_variance_genes": int(res["zero_variance"].sum()),
        "library_versions": {
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "scipy": __import__("scipy").__version__,
        },
    }
    data_io.write_json(out_dir / "analysis_config.json", config)

    print(
        f"[完成] {config['n_genes']} 个基因，显著 {config['n_significant']} 个"
        f"（上调 {config['n_up']}，下调 {config['n_down']}）。输出目录：{out_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
