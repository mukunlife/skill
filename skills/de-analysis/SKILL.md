---
name: de-analysis
description: 两组样本基因表达差异分析。读取表达矩阵与样本分组表，校验样本对应关系和数据类型，自动选择检验方法，输出差异基因结果表（含 log2FoldChange、P 值、校正后 P 值）、火山图和结果说明。适用于 RNA-seq 或芯片数据的两组比较、差异基因筛选和火山图绘制。
---

# 两组基因表达差异分析

## 适用任务

- 两组独立样本（如 control vs treatment、normal vs tumor）的基因表达比较。
- 需要输出可复核的差异基因表、火山图和文字说明。
- 需要先检查表达矩阵与分组信息是否一一对应。

## 不适用

- 三组及以上比较、时间序列、配对样本、单细胞数据。
- 需要 DESeq2/edgeR 精确负二项模型的正式发表级分析（本 Skill 用 Python 近似实现，限制见 `references/overview.md`）。

## 输入

| 输入 | 格式 | 必需 |
|---|---|---|
| 表达矩阵 | CSV/TSV，第一列 `gene_id`，其余每列一个样本 | 是 |
| 分组表 | CSV，含 `sample` 和 `group` 两列，恰好两组 | 是 |
| 比较组 | `--group-a`（基准组）、`--group-b`（比较组） | 是（需与分组表一致） |

`log2FoldChange = mean(log2 表达, group-b) - mean(log2 表达, group-a)`，即正值表示在 group-b 中更高。方向必须在结果说明中写明。

## 执行流程

1. **先读导航**：打开 `references/index.md`，按其中条件决定还要读哪些参考文档。
2. **确认规则**：执行分析前必须读 `references/rules.md`，确认数据格式、数据类型判断、检验方法和筛选阈值。用户自定义阈值时以用户为准，并在说明中记录。
3. **只做校验**：
   ```bash
   python scripts/run.py \
     --expression <表达矩阵> --groups <分组表> \
     --group-a <基准组> --group-b <比较组> \
     --output-dir <输出目录> --validate-only
   ```
   校验失败（退出码 2）时不得继续分析，应报告缺失样本、重复 ID 等具体问题。
4. **完整分析**：
   ```bash
   python scripts/run.py \
     --expression <表达矩阵> --groups <分组表> \
     --group-a <基准组> --group-b <比较组> \
     --output-dir <输出目录> \
     [--data-type auto|counts|normalized] \
     [--test welch|mannwhitney] \
     [--log2fc 1.0] [--padj 0.05]
   ```
5. **结果核验**：
   ```bash
   python scripts/checks.py \
     --output-dir <输出目录> \
     --expression <表达矩阵> --groups <分组表> \
     --group-a <基准组> --group-b <比较组>
   ```
   `checks.py` 退出码非 0 时，不得宣称分析完成，应定位并修复问题后重跑。

## 输出

| 文件 | 内容 |
|---|---|
| `de_results.csv` | 全部基因：gene_id、均值、log2FoldChange、pvalue、padj、significant |
| `de_significant.csv` | 通过阈值的差异基因，按 padj 升序 |
| `volcano.png` | 火山图（横轴 log2FC，纵轴 -log10 padj） |
| `summary.md` | 比较方向、方法、阈值、样本数、上下调数量、前 10 基因、限制 |
| `analysis_config.json` | 本次运行的参数和数据模式，供复核 |
| `validation.json` | 样本与分组的校验报告 |
| `checks.json` | 结果核验报告（由 `checks.py` 生成） |

## 结果核验要求（报告时必须包含）

- 表达矩阵样本数与分组表样本数是否一致，缺失/多余样本清单。
- 判定为 counts 还是 normalized，以及是否做了 log2 转换。
- 检验方法、比较方向、筛选阈值。
- 显著基因数、上调数、下调数。
- `checks.py` 的通过情况，以及已知真值数据（如有）的召回率。
- 若样本每组少于 3 例，必须提示统计功效有限。

## 脚本说明

- `scripts/run.py`：入口，负责参数解析、流程编排和输出。
- `scripts/data_io.py`：读取、格式校验、数据类型判断、log 转换。
- `scripts/stats_utils.py`：fold change、Welch t / Mann-Whitney、BH 校正。
- `scripts/checks.py`：独立复核输出与输入是否一致。
- `scripts/make_demo_data.py`：生成可复现的演示数据（非教师数据）。

脚本只依赖 pandas、numpy、scipy、matplotlib。不要用模型心算代替脚本结果。
