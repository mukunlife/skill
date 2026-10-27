"""差异分析的统计计算：fold change、组间检验与 BH 校正。"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def compute_stats(
    log_values: pd.DataFrame,
    a_samples: list[str],
    b_samples: list[str],
    method: str = "welch",
) -> dict:
    """返回每个基因的均值、log2FC、P 值、零方差标记与 NaN 数量。"""
    a = log_values[a_samples].to_numpy(dtype=float)
    b = log_values[b_samples].to_numpy(dtype=float)

    mean_a = a.mean(axis=1)
    mean_b = b.mean(axis=1)
    log2fc = mean_b - mean_a
    std_a = a.std(axis=1, ddof=1)
    std_b = b.std(axis=1, ddof=1)
    zero_variance = (np.isclose(std_a, 0.0, atol=1e-12)) & (
        np.isclose(std_b, 0.0, atol=1e-12)
    )

    if method == "welch":
        with np.errstate(divide="ignore", invalid="ignore"):
            _, pvalue = stats.ttest_ind(
                b, a, axis=1, equal_var=False, nan_policy="omit"
            )
        pvalue = np.asarray(pvalue, dtype=float)
    elif method == "mannwhitney":
        pvalue = np.ones(a.shape[0], dtype=float)
        for i in range(a.shape[0]):
            try:
                pvalue[i] = stats.mannwhitneyu(
                    b[i], a[i], alternative="two-sided"
                ).pvalue
            except ValueError:
                pvalue[i] = np.nan
    else:
        raise ValueError(f"未知检验方法：{method}")

    nan_count = int(np.isnan(pvalue).sum())
    # 两组均为常数且均值相同时，差异必然不显著；其余 NaN 也按 1 处理并记录。
    same_constant = zero_variance & np.isclose(mean_a, mean_b, atol=1e-12)
    pvalue = np.where(np.isnan(pvalue) & same_constant, 1.0, pvalue)
    pvalue = np.where(np.isnan(pvalue), 1.0, pvalue)
    pvalue = np.clip(pvalue, 0.0, 1.0)

    base_mean = log_values[list(a_samples) + list(b_samples)].to_numpy(
        dtype=float
    ).mean(axis=1)

    return {
        "mean_a": mean_a,
        "mean_b": mean_b,
        "base_mean": base_mean,
        "log2FoldChange": log2fc,
        "pvalue": pvalue,
        "zero_variance": zero_variance,
        "nan_pvalue_count": nan_count,
    }


def bh_fdr(pvalue: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg FDR 校正，返回与输入同序的 padj。"""
    p = np.asarray(pvalue, dtype=float)
    m = p.size
    if m == 0:
        return p.copy()
    safe = np.where(np.isfinite(p), p, 1.0)
    order = np.argsort(safe)
    ranked = safe[order]
    adjusted = ranked * m / np.arange(1, m + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    out = np.empty(m, dtype=float)
    out[order] = np.clip(adjusted, 0.0, 1.0)
    return out
