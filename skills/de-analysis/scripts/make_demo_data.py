#!/usr/bin/env python
"""生成可复现的模拟表达数据，供课堂演示和自检使用。

注意：这是模拟数据，不是教师提供的真实表达矩阵。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    out_dir = Path(__file__).resolve().parents[1] / "examples"
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(20241027)
    n_genes = 300
    samples = [
        "Control_1",
        "Control_2",
        "Control_3",
        "Treat_1",
        "Treat_2",
        "Treat_3",
    ]
    groups = ["control"] * 3 + ["treat"] * 3

    # 基础表达量；最后 5 个基因设为全 0，用于测试零方差和低表达处理
    base = rng.lognormal(mean=4.2, sigma=1.0, size=n_genes)
    base[-5:] = 0.0

    # 40 个差异基因，效应量 1.6~3.0（log2），保证 3v3 小样本下仍有可检出的基因
    n_de = 40
    de_idx = rng.choice(np.arange(n_genes - 5), size=n_de, replace=False)
    true_log2fc = np.zeros(n_genes)
    true_log2fc[de_idx] = rng.uniform(1.6, 3.0, size=n_de) * rng.choice(
        [-1.0, 1.0], size=n_de
    )

    size_factors = np.array([0.85, 1.00, 1.15, 0.90, 1.05, 1.10])
    treat_indicator = np.array([0.0, 0.0, 0.0, 1.0, 1.0, 1.0])
    mu = (
        base[:, None]
        * size_factors[None, :]
        * np.power(2.0, true_log2fc[:, None] * treat_indicator[None, :])
    )

    # 负二项离散度参数：n 越大，方差越小；25 对应中等测序噪声
    dispersion_n = 25.0
    probability = dispersion_n / (dispersion_n + mu)
    counts = rng.negative_binomial(dispersion_n, probability)

    gene_ids = [f"GENE{i:04d}" for i in range(1, n_genes + 1)]
    expression = pd.DataFrame(counts.astype(int), columns=samples)
    expression.insert(0, "gene_id", gene_ids)
    expression.to_csv(out_dir / "expression_demo.csv", index=False, encoding="utf-8-sig")

    pd.DataFrame({"sample": samples, "group": groups}).to_csv(
        out_dir / "groups_demo.csv", index=False, encoding="utf-8-sig"
    )

    truth = pd.DataFrame(
        {
            "gene_id": gene_ids,
            "is_de": [1 if i in set(de_idx.tolist()) else 0 for i in range(n_genes)],
            "true_log2fc": np.round(true_log2fc, 4),
        }
    )
    truth.to_csv(out_dir / "truth_demo.csv", index=False, encoding="utf-8-sig")

    print(f"[完成] 已生成 {n_genes} 个基因 × {len(samples)} 个样本的模拟数据：{out_dir}")


if __name__ == "__main__":
    main()
