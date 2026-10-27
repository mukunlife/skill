# 智能体实践实验一：Agent 环境配置与 Skill 开发

- 学号：2024187025
- 姓名：牛晨杰
- 日期：2026-10-27
- 环境：VS Code 1.133.0 + Claude Code 扩展 2.1.311 + CC Switch 4.0.21 + DeepSeek API

## 项目内容

| 目录 | 内容 |
|---|---|
| `.claude/skills/de-analysis/` | 自建 Skill：两组基因表达差异分析（SKILL.md、references、scripts、examples） |
| `.claude/skills/medical-dialogue/` | 自建 Skill：医疗对话整理为问答记录（SKILL.md、references、scripts、examples） |
| `.claude/skills/skill-creator/` | 安装并改造的现有 Skill（Apache 2.0，来源与改动见 `NOTICE.md`） |
| `outputs/01_connection/` | DeepSeek 配置记录与实际请求核验 |
| `outputs/02_file_ops/` | 文件创建、外部修改、回读记录 |
| `outputs/03_skill_de/` | 差异分析结果表、火山图、说明与核验报告 |
| `outputs/04_skill_dialogue/` | 问答记录、结构化 JSON 与核验报告 |
| `outputs/05_compare/` | 普通提示词 vs 调用 Skill 的对照及异常测试 |
| `outputs/06_existing_skill/` | 现有 Skill 的安装、改造前后输出 |
| `docs/实验记录.md` | 实验记录正文（`实验记录.docx` 由它生成） |

## 主要结果

### de-analysis

- 演示数据：300 个基因 × 6 个样本（control 3、treat 3，模拟 counts）。
- 方法：CPM + log2、Welch t 检验、BH 校正。
- 方向：treat vs control；筛选标准 |log2FC| ≥ 1 且 padj < 0.05。
- 结果：**20 个显著基因**（上调 5、下调 15），精确率 1.000、召回率 0.500。
- `checks.py` 14 项全部通过，log2FC/P/padj 复算最大偏差 0.00e+00。

### medical-dialogue

- 示例对话 20 行：17 条有效发言（合并后）、7 个问答对。
- 显式列出：未配对患者发言 1 条、医生单方面说明 1 条、其他角色 1 条、
  格式错误 1 行、空内容 1 行。
- `checks.py` 7 项全部通过，18 个原文片段全部被且仅被覆盖一次。

### 现有 Skill 改造

- 来源：`anthropics/skills` → `skills/skill-creator`，提交 `dbd4588`，Apache 2.0。
- 修复官方 `quick_validate.py` 在 Windows 下用 GBK 读取中文 SKILL.md 的崩溃。
- 新增课程增强校验 `validate_coursework_skill.py`：导航、示例、核验脚本、密钥、
  绝对路径、运行结果 `checks.json`，共 20 项。
- 改造后两个自建 Skill 均 20/20 通过；缺陷样例被抓出 11 项失败。

## 复现

```powershell
# 1. 创建虚拟环境（已提交的 .venv 不在仓库中）
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pandas numpy scipy matplotlib python-docx pyyaml

# 2. 差异分析
.\.venv\Scripts\python.exe .\.claude\skills\de-analysis\scripts\run.py `
  --expression .\.claude\skills\de-analysis\examples\expression_demo.csv `
  --groups .\.claude\skills\de-analysis\examples\groups_demo.csv `
  --group-a control --group-b treat --output-dir .\outputs\03_skill_de

.\.venv\Scripts\python.exe .\.claude\skills\de-analysis\scripts\checks.py `
  --output-dir .\outputs\03_skill_de `
  --expression .\.claude\skills\de-analysis\examples\expression_demo.csv `
  --groups .\.claude\skills\de-analysis\examples\groups_demo.csv `
  --group-a control --group-b treat `
  --truth .\.claude\skills\de-analysis\examples\truth_demo.csv

# 3. 医疗对话整理
.\.venv\Scripts\python.exe .\.claude\skills\medical-dialogue\scripts\run.py `
  --input .\.claude\skills\medical-dialogue\examples\sample_dialogue.txt `
  --output-dir .\outputs\04_skill_dialogue --title "门诊高血压复诊对话（示例）"

.\.venv\Scripts\python.exe .\.claude\skills\medical-dialogue\scripts\checks.py `
  --input .\.claude\skills\medical-dialogue\examples\sample_dialogue.txt `
  --output-dir .\outputs\04_skill_dialogue

# 4. 生成实验记录 docx
.\.venv\Scripts\python.exe .\docs\build_docx.py
```

## 说明与限制

- 表达矩阵是**模拟数据**，不是教师提供的真实数据；参数刻意设为小样本下可检出，
  便于课堂演示。替换为真实数据时保持同样列结构即可。
- `de-analysis` 使用 log2 CPM + Welch 检验，不等同于 DESeq2/edgeR；结果说明中已注明
  局限，正式分析应复核。
- `medical-dialogue` 只做逐字结构化，不做诊断、改写或摘要。
- API 密钥不写入仓库；`.gitignore` 已排除 `.claude/settings.json`。
- 实验要求的配置截图、成功响应截图需由使用者在本机补拍，清单见
  `docs/实验记录.md` 第九节。

## 来源

- Anthropic `skills` 仓库：https://github.com/anthropics/skills（提交 `dbd4588f9e1033efb41dad4bef2f7947c8993d44`）
- `skill-creator` 许可：Apache License 2.0，原始 `LICENSE.txt` 与 `NOTICE.md` 已保留。
- DeepSeek API 兼容端点：`https://api.deepseek.com/anthropic`
