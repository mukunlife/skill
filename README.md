# 智能体实践实验一：Agent 环境配置与 Skill 开发

- 学号：2024187025
- 姓名：牛晨杰
- 日期：2026-10-27
- 环境：VS Code 1.133.0 + Claude Code 扩展 2.1.311 + CC Switch 4.0.21 + DeepSeek API

## 项目内容

| 目录 | 内容 |
|---|---|
| `.claude/skills/de-analysis/` | 自建 Skill：两组基因表达差异分析（运行时目录） |
| `.claude/skills/medical-dialogue/` | 自建 Skill：医疗对话整理为问答记录（运行时目录） |
| `skills/` | 提交清单要求的两个自建 Skill 副本（内容与 `.claude/skills/` 一致） |
| `.claude/skills/skill-creator/` | 安装并改造的现有 Skill（Apache 2.0，来源与改动见 `NOTICE.md`） |
| `outputs/01_connection/` | DeepSeek 配置记录与实际请求核验 |
| `outputs/02_file_ops/` | 文件创建、外部修改、回读记录 |
| `TCGA-KIRC/` | 实验提供的真实表达矩阵、样本分组、基因注释与复现说明 |
| `outputs/03_skill_de/` | 演示数据的差异分析结果表、火山图、说明与核验报告 |
| `outputs/04_skill_dialogue/` | 问答记录、结构化 JSON 与核验报告 |
| `outputs/07_tcga_kirc/` | TCGA-KIRC 真实数据结果表（含基因名称）、火山图、说明与核验报告 |
| `outputs/05_compare/` | 普通提示词 vs 调用 Skill 的对照及异常测试 |
| `outputs/06_existing_skill/` | 现有 Skill 的安装、改造前后输出 |
| `docs/实验记录.md` | 实验记录正文（`实验记录.docx` 由它生成） |

## 主要结果

### de-analysis

**真实数据（TCGA-KIRC，主分析）**

- 数据：60,660 个基因 × 20 个样本（Normal 10、Tumor 10，STAR 原始 counts）。
- 方法：CPM + log2、Welch t 检验、BH 校正。
- 方向：Tumor vs Normal；筛选标准 |log2FC| ≥ 1 且 padj < 0.05。
- 结果：**3,442 个显著基因**（Tumor 中上调 1,851、下调 1,591）；10,900 个全 0 基因
  保留并标记为零方差。
- 标志物方向符合预期：CA9 +7.07、NDUFA4L2 +7.24、EGLN3 +4.66；UMOD −10.17、
  AQP2 −9.25、SLC12A1 −8.21。
- `checks.py` 13 项全部通过，复算最大偏差 0.00e+00。
- 限制：10 例样本为同患者配对设计，本实验按任务书要求使用非配对 Welch，已在
  实验记录 4.5.3 说明。

**演示数据（方法自检）**

- 300 个基因 × 6 个样本（control 3、treat 3，模拟 counts）。
- 结果：20 个显著基因（上调 5、下调 15），精确率 1.000、召回率 0.500。
- `checks.py` 14 项全部通过。

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

# 2. 真实数据差异分析（TCGA-KIRC）
.\.venv\Scripts\python.exe .\.claude\skills\de-analysis\scripts\run.py `
  --expression .\TCGA-KIRC\gene_counts.tsv `
  --groups .\TCGA-KIRC\groups.csv `
  --group-a Normal --group-b Tumor --output-dir .\outputs\07_tcga_kirc

.\.venv\Scripts\python.exe .\.claude\skills\de-analysis\scripts\checks.py `
  --output-dir .\outputs\07_tcga_kirc `
  --expression .\TCGA-KIRC\gene_counts.tsv `
  --groups .\TCGA-KIRC\groups.csv `
  --group-a Normal --group-b Tumor

.\.venv\Scripts\python.exe .\TCGA-KIRC\annotate_results.py `
  --results .\outputs\07_tcga_kirc\de_results.csv `
  --annotation .\TCGA-KIRC\gene_annotation.tsv `
  --outdir .\outputs\07_tcga_kirc

# 3. 演示数据差异分析（方法自检）
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

# 4. 医疗对话整理
.\.venv\Scripts\python.exe .\.claude\skills\medical-dialogue\scripts\run.py `
  --input .\.claude\skills\medical-dialogue\examples\sample_dialogue.txt `
  --output-dir .\outputs\04_skill_dialogue --title "门诊高血压复诊对话（示例）"

.\.venv\Scripts\python.exe .\.claude\skills\medical-dialogue\scripts\checks.py `
  --input .\.claude\skills\medical-dialogue\examples\sample_dialogue.txt `
  --output-dir .\outputs\04_skill_dialogue

# 5. 生成实验记录 docx
.\.venv\Scripts\python.exe .\docs\build_docx.py
```

## 说明与限制

- 主分析使用实验提供的 **TCGA-KIRC 真实数据**；`skills/de-analysis/examples/` 中的
  模拟数据只用于方法自检，参数刻意设为小样本下可检出，不能代表真实数据的表现。
- TCGA-KIRC 的 10 例 Normal 与 10 例 Tumor 来自同一批患者，属于配对设计；本实验按
  任务书要求做两组比较，使用非配对 Welch 检验，配对信息未利用（见实验记录 4.5.3）。
- `de-analysis` 使用 log2 CPM + Welch 检验，不等同于 DESeq2/edgeR；结果说明中已注明
  局限，正式分析应复核。
- `medical-dialogue` 只做逐字结构化，不做诊断、改写或摘要。
- API 密钥不写入仓库；`.gitignore` 已排除 `.claude/settings.json`。
- 实验要求的配置截图、成功响应截图需由使用者在本机补拍，清单见
  `docs/实验记录.md` 第九节。

## 版本

- 本地 Git 首次提交：`c86f7ff8a6e45a2bd570a2129ee1abf980935313`
- 真实数据版提交：`ad51b77`
- 远端仓库：https://github.com/mukunlife/skill （已推送，Public，`main` 分支）

## 来源

- Anthropic `skills` 仓库：https://github.com/anthropics/skills（提交 `dbd4588f9e1033efb41dad4bef2f7947c8993d44`）
- `skill-creator` 许可：Apache License 2.0，原始 `LICENSE.txt` 与 `NOTICE.md` 已保留。
- DeepSeek API 兼容端点：`https://api.deepseek.com/anthropic`
