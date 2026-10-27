# 数据格式与分析规则

## 1. 表达矩阵

- 第一列必须是基因标识，列名建议为 `gene_id`；若为其他列名，脚本会把第一列重命名为 `gene_id`。
- 其余列必须是样本，列名即样本名，需与分组表 `sample` 列逐字一致（区分大小写）。
- 值为数值；原始 counts 应为非负整数，归一化表达可为小数。缺失值、空值直接判为校验失败。
- 基因 ID 不允许重复。

## 2. 分组表

- 必需两列：`sample`、`group`（列名不区分大小写，读取后会统一）。
- 本 Skill 只支持**恰好两组**；多组请先拆分或改用其他方法。
- 两组样本名必须与表达矩阵样本列完全一一对应；缺失或多出都判为校验失败。
- 每组至少 2 个样本才能计算组内方差；每组少于 3 个样本时应在结论中提示统计功效不足。
- **配对设计**（同一患者的两份样本、治疗前后）本 Skill 按非配对处理，会丢弃配对信息。
  可以运行，但必须在 `summary.md` 和结论中写明“未利用配对信息、结果偏保守”；
  需要配对结论时应改用配对 t 检验或带配对因子的 DESeq2 设计。

## 3. 比较方向

- `--group-a` 为基准组，`--group-b` 为比较组。
- `log2FoldChange = mean(log2 表达 | group-b) - mean(log2 表达 | group-a)`。
- 说明中必须写明“正值表示在 group-b 中表达更高”。

## 4. 数据类型判断（默认 `--data-type auto`）

| 判定 | 条件 | 处理 |
|---|---|---|
| counts | 全部值非负、接近整数，且最大值 > 20 | 按列计算 CPM，再 `log2(CPM + 1)` |
| normalized | 其余情况（含已取 log 的负值、小数强度值） | 若全部非负且最大值 > 50，视为线性强度并做 `log2(x + 1)`；否则视为已在 log 尺度，直接使用 |

判断不明确时（例如 CPM 被四舍五入成整数），必须用 `--data-type counts|normalized` 显式指定，并在说明中记录。自动判断结果写入 `analysis_config.json`。

## 5. 检验方法

- 默认 `welch`：对每个基因做双侧 Welch t 检验（不假设两组方差相等）。
- 可选 `mannwhitney`：双侧 Mann-Whitney U 检验，适用于明显非正态、样本量小或离群值多的数据。
- 两组均为常数时：均值相同则 p = 1；均值不同则按 t 检验结果处理，但必须在说明中标记该基因为零方差。
- 全部为 0 的基因：不参与有效差异判断，结果中保留但标记 `zero_variance = true`。

## 6. 多重检验校正

- 使用 Benjamini-Hochberg 方法计算 `padj`（FDR）。
- p 值为 NaN 时先按 1 处理再校正，并在 `analysis_config.json` 中记录 NaN 数量。

## 7. 差异基因筛选（默认）

- `|log2FoldChange| >= 1.0` 且 `padj < 0.05`。
- 阈值可由 `--log2fc`、`--padj` 修改；自定义值必须写入 `summary.md`。
- 不得只按 p 值或只按 fold change 筛选；不得在未做多重校正时把 p 值称为“校正后 P 值”。

## 8. 输出字段

`de_results.csv` / `de_significant.csv` 至少包含：

| 字段 | 含义 |
|---|---|
| `gene_id` | 基因名称或编号 |
| `mean_a` / `mean_b` | 各组在 log2 尺度上的均值 |
| `base_mean` | 全部样本 log2 表达均值 |
| `log2FoldChange` | group-b 相对 group-a 的 log2 倍数变化 |
| `pvalue` | 原始 P 值 |
| `padj` | BH 校正后 P 值 |
| `significant` | 是否通过阈值 |
| `zero_variance` | 两组是否均为零方差 |

## 9. 异常处理

- 校验失败：退出码 2，写出 `validation.json`，不得生成差异结果。
- 结果核验失败：`checks.py` 退出码 1，必须修复后重跑，不得只口头说明。
- 图无法生成（如 matplotlib 后端问题）：仍需输出表格和说明，并在报告中标明缺图原因。
