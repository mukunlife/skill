"""读取、校验表达矩阵与分组表，并完成数据类型判断和 log 转换。"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


class DataError(ValueError):
    """输入数据不满足本 Skill 约定时抛出。"""


def read_table(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise DataError(f"文件不存在：{path}")
    sep = "\t" if path.suffix.lower() in {".tsv", ".txt"} else ","
    try:
        df = pd.read_csv(path, sep=sep, encoding="utf-8-sig")
    except Exception as exc:  # noqa: BLE001 - 交给调用方统一报告
        raise DataError(f"无法读取 {path.name}：{exc}") from exc
    if df.shape[1] < 2:
        raise DataError(f"{path.name} 至少需要 1 列基因 ID 和 1 列样本")
    return df


def read_expression(path: str | Path) -> tuple[pd.DataFrame, list[str]]:
    df = read_table(path)
    gene_col = df.columns[0]
    df = df.rename(columns={gene_col: "gene_id"})
    df["gene_id"] = df["gene_id"].astype(str).str.strip()

    if (df["gene_id"] == "").any():
        raise DataError("表达矩阵存在空基因 ID")
    if df["gene_id"].duplicated().any():
        dup = df.loc[df["gene_id"].duplicated(), "gene_id"].head(5).tolist()
        raise DataError(f"基因 ID 重复，例如：{dup}")

    sample_cols = [str(c).strip() for c in df.columns[1:]]
    df.columns = ["gene_id", *sample_cols]
    if len(set(sample_cols)) != len(sample_cols):
        raise DataError("表达矩阵存在重复的样本列名")

    for col in sample_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    values = df[sample_cols].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        bad = df.loc[~np.isfinite(values).all(axis=1), "gene_id"].head(5).tolist()
        raise DataError(f"存在缺失值、非数值或无穷值，例如基因：{bad}")
    return df, sample_cols


def read_groups(path: str | Path) -> pd.DataFrame:
    df = read_table(path)
    lower = {str(c).strip().lower(): c for c in df.columns}
    if "sample" not in lower or "group" not in lower:
        raise DataError("分组表必须包含 sample 和 group 两列")
    groups = pd.DataFrame(
        {
            "sample": df[lower["sample"]].astype(str).str.strip(),
            "group": df[lower["group"]].astype(str).str.strip(),
        }
    )
    if (groups[["sample", "group"]] == "").any().any():
        raise DataError("分组表存在空样本名或空组名")
    if groups["sample"].duplicated().any():
        dup = groups.loc[groups["sample"].duplicated(), "sample"].head(5).tolist()
        raise DataError(f"分组表样本重复：{dup}")
    return groups


def validate(
    expr: pd.DataFrame,
    sample_cols: list[str],
    groups: pd.DataFrame,
    group_a: str,
    group_b: str,
) -> dict:
    """收集所有校验问题，返回结构化报告而不是在第一处直接退出。"""
    errors: list[str] = []
    warnings: list[str] = []

    matrix_samples = set(sample_cols)
    group_samples = set(groups["sample"])
    missing_in_matrix = sorted(group_samples - matrix_samples)
    missing_in_groups = sorted(matrix_samples - group_samples)
    if missing_in_matrix:
        errors.append(f"分组表中的样本在表达矩阵中缺失：{missing_in_matrix}")
    if missing_in_groups:
        errors.append(f"表达矩阵中的样本在分组表中缺失：{missing_in_groups}")

    all_groups = sorted(groups["group"].unique().tolist())
    if len(all_groups) != 2:
        errors.append(f"本 Skill 仅支持两组，当前分组为 {all_groups}")
    for label, name in (("group-a", group_a), ("group-b", group_b)):
        if name not in all_groups:
            errors.append(f"{label}={name!r} 不在分组表中，现有分组：{all_groups}")
    if group_a == group_b:
        errors.append("group-a 与 group-b 不能相同")

    samples_per_group: dict[str, list[str]] = {}
    for name in (group_a, group_b):
        if name in all_groups:
            samples = groups.loc[groups["group"] == name, "sample"].tolist()
            samples_per_group[name] = samples
            if len(samples) < 2:
                errors.append(f"组 {name!r} 只有 {len(samples)} 个样本，至少需要 2 个")
            elif len(samples) < 3:
                warnings.append(f"组 {name!r} 只有 {len(samples)} 个样本，统计功效有限")

    values = expr[sample_cols].to_numpy(dtype=float)
    if (values < 0).any():
        warnings.append("表达矩阵含负值，将按已在 log 尺度处理，请确认数据类型")
    zero_genes = int((values == 0).all(axis=1).sum())
    if zero_genes:
        warnings.append(f"有 {zero_genes} 个基因在所有样本中均为 0，将保留但标记为零方差")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "group_a": group_a,
        "group_b": group_b,
        "all_groups": all_groups,
        "samples_per_group": samples_per_group,
        "n_matrix_samples": len(sample_cols),
        "n_group_samples": len(groups),
        "matrix_only_samples": missing_in_groups,
        "groups_only_samples": missing_in_matrix,
        "zero_genes": zero_genes,
    }


def detect_data_type(
    expr: pd.DataFrame, sample_cols: list[str], override: str = "auto"
) -> tuple[str, str]:
    values = expr[sample_cols].to_numpy(dtype=float)
    is_integer = bool(np.allclose(values, np.rint(values), atol=1e-8))
    non_negative = bool((values >= 0).all())

    if override == "counts":
        if not non_negative:
            raise DataError("显式指定 --data-type counts，但矩阵含负值")
        if not is_integer:
            raise DataError("显式指定 --data-type counts，但矩阵含非整数值")
        return "counts", "用户显式指定为原始 counts"
    if override == "normalized":
        return "normalized", "用户显式指定为归一化表达"
    if override != "auto":
        raise DataError(f"未知的 --data-type：{override}")

    if non_negative and is_integer and float(values.max()) > 20:
        return "counts", "非负整数且最大值 > 20，自动判为原始 counts"
    return "normalized", "非整数或数值范围较小，自动判为归一化表达"


def to_log_expression(
    expr: pd.DataFrame, sample_cols: list[str], data_type: str
) -> tuple[pd.DataFrame, str]:
    values = expr[sample_cols].astype(float)
    if data_type == "counts":
        library = values.sum(axis=0)
        if (library <= 0).any():
            bad = library[library <= 0].index.tolist()
            raise DataError(f"样本文库大小（总 counts）为 0：{bad}")
        cpm = values.div(library, axis=1) * 1e6
        return np.log2(cpm + 1.0), "CPM 归一化后取 log2(x + 1)"

    arr = values.to_numpy(dtype=float)
    if (arr >= 0).all() and float(arr.max()) > 50:
        return np.log2(values + 1.0), "线性强度取 log2(x + 1)"
    return values.copy(), "视为已在 log 尺度，直接使用"


def write_json(path: str | Path, payload: dict) -> None:
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
