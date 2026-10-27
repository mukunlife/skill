# TCGA-KIRC 数据说明

本目录存放实验提供的肾透明细胞癌（Kidney Renal Clear Cell Carcinoma, TCGA-KIRC）
RNA-seq 数据，用于 `de-analysis` Skill 的真实数据运行。

## 文件

| 文件 | 内容 |
|---|---|
| `gene_counts.tsv` | 60,660 个基因 × 20 个样本的原始 counts（STAR gene counts） |
| `sample_info.csv` | 样本分组、患者 ID、GDC file UUID 与下载地址 |
| `gene_annotation.tsv` | Ensembl `gene_id` 对应的 `gene_name`、`gene_type` |
| `groups.csv` | 从 `sample_info.csv` 派生的两列分组表，供 Skill 直接读取 |
| `annotate_results.py` | 给差异分析结果补 `gene_name` / `gene_type` 的辅助脚本 |

## 分组

| 组 | 样本类型 | 样本数 | 样本名后缀 |
|---|---|---:|---|
| Normal | Solid Tissue Normal（癌旁） | 10 | `-11A` |
| Tumor | Primary Tumor（原发灶） | 10 | `-01A` |

同一患者同时有 Normal 和 Tumor 样本（配对设计）。本实验按任务书要求做两组比较，
Skill 使用非配对 Welch t 检验；配对设计带来的功效损失在实验记录中作为限制说明。

## `groups.csv` 的生成

```python
import pandas as pd

s = pd.read_csv("TCGA-KIRC/sample_info.csv", encoding="utf-8-sig")
g = s[["sample_id", "group"]].rename(columns={"sample_id": "sample"})
g.to_csv("TCGA-KIRC/groups.csv", index=False, encoding="utf-8")
```

## 复现命令

```powershell
# 差异分析
.\.venv\Scripts\python.exe .\skills\de-analysis\scripts\run.py `
  --expression .\TCGA-KIRC\gene_counts.tsv `
  --groups .\TCGA-KIRC\groups.csv `
  --group-a Normal --group-b Tumor `
  --output-dir .\outputs\07_tcga_kirc

# 结果核验
.\.venv\Scripts\python.exe .\skills\de-analysis\scripts\checks.py `
  --output-dir .\outputs\07_tcga_kirc `
  --expression .\TCGA-KIRC\gene_counts.tsv `
  --groups .\TCGA-KIRC\groups.csv `
  --group-a Normal --group-b Tumor

# 补基因名称
.\.venv\Scripts\python.exe .\TCGA-KIRC\annotate_results.py `
  --results .\outputs\07_tcga_kirc\de_results.csv `
  --annotation .\TCGA-KIRC\gene_annotation.tsv `
  --outdir .\outputs\07_tcga_kirc
```

## 结果摘要

- 60,660 个基因，显著 3,442 个（Tumor 中上调 1,851、下调 1,591）。
- 筛选标准：|log2FC| ≥ 1 且 padj < 0.05；CPM + log2、Welch t、BH 校正。
- 10,900 个基因在全部样本中为 0，保留并标记 `zero_variance`。
- `checks.py` 13 项全部通过。

## 来源

`sample_info.csv` 的 `source_url` 列保留了每个样本的 GDC 下载地址
（`https://api.gdc.cancer.gov/data/<file_uuid>`），项目字段为 `TCGA-KIRC`。
