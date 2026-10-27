# 参考资料导航

按任务需要读取，不必一次全部加载。

| 文档 | 何时必须读取 | 内容 |
|---|---|---|
| [rules.md](rules.md) | 每次执行分析前 | 输入列名、样本对应规则、数据类型判断、检验方法选择、筛选阈值、输出字段、异常处理 |
| [overview.md](overview.md) | 需要解释方法、判断结果可靠性、或用户质疑方法时 | counts 与 normalized 的区别、Welch t 检验与 BH 校正原理、与 DESeq2 的差异、适用边界 |

## 读取顺序

1. 先读 `rules.md`，据此校验输入和选择参数。
2. 分析完成后，若需要写方法学说明或解释局限性，再读 `overview.md`。
3. 用户给出非默认阈值或非默认检验方法时，仍以 `rules.md` 的字段定义为准，并在 `summary.md` 中记录偏离默认值的原因。

## 相关脚本

- 数据读取与校验：`scripts/data_io.py`
- 统计计算：`scripts/stats_utils.py`
- 入口：`scripts/run.py`
- 结果复核：`scripts/checks.py`
