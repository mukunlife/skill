# 示例数据说明

本目录数据由 `scripts/make_demo_data.py` 生成，**是模拟数据，不是教师提供的表达矩阵**。

| 文件 | 内容 |
|---|---|
| `expression_demo.csv` | 300 个基因 × 6 个样本的模拟 counts 矩阵（含 5 个全 0 基因） |
| `groups_demo.csv` | 样本分组：3 例 control、3 例 treat |
| `truth_demo.csv` | 模拟时设定的真值（40 个差异基因及其真实 log2FC），仅用于自检，不参与分析 |

- 随机种子：`20241027`，可重复生成。
- 模拟方式：负二项分布（dispersion n=25），差异基因的 log2FC 在 1.6–3.0 之间，
  样本间加入 0.85–1.15 的文库大小差异。参数刻意设置为小样本下可检出，便于课堂演示；
  真实数据不会这样理想。
- 换用真实数据时，只需保持 `expression.csv`（第一列 `gene_id`，其余为样本）和
  `groups.csv`（`sample,group` 两列）的列结构，无需修改脚本。
