# 现有 Skill 的安装与改造记录：skill-creator

日期：2026-10-27
改造人：牛晨杰（2024187025）

## 1. 原始来源与许可

| 项目 | 内容 |
|---|---|
| 仓库 | https://github.com/anthropics/skills |
| 路径 | `skills/skill-creator` |
| 提交 | `dbd4588f9e1033efb41dad4bef2f7947c8993d44`（2026-10-09） |
| 许可 | Apache License 2.0（原始 `LICENSE.txt` 已保留在安装目录） |
| 安装位置 | `.claude/skills/skill-creator/` |
| 本地克隆位置 | `C:\Users\21336\tools\anthropic-skills`（不提交） |

选择理由：`skill-creator` 是 Anthropic 官方用于创建/改进 Skill 的 Skill，许可为
Apache 2.0，允许修改与再分发；而官方 `pdf`、`docx` 等 Skill 的 LICENSE 明确禁止
制作衍生作品，不能作为“改造”对象。

## 2. 改造前的问题

直接运行官方 `quick_validate.py` 校验中文 SKILL.md：

```text
Traceback (most recent call last):
  File "...\quick_validate.py", line 22, in validate_skill
    content = skill_md.read_text()
UnicodeDecodeError: 'gbk' codec can't decode byte 0xae in position 61:
illegal multibyte sequence
```

原因：Windows 上 `Path.read_text()` 默认使用 GBK，中文 SKILL.md 是 UTF-8，导致
官方校验脚本在中文环境下不可用。完整日志见 `before_quick_validate.log`。

另一个问题：官方校验只检查 frontmatter。用一个故意有缺陷的样例测试，它仍然返回
`Skill is valid!`，而该样例缺少 references、examples、checks.py，还写入了假密钥和
本机绝对路径。

## 3. 具体改动

| 文件 | 改动 | 目的 |
|---|---|---|
| `scripts/quick_validate.py` | `read_text()` → `read_text(encoding="utf-8")` | 修复 Windows 中文环境下的 GBK 解码崩溃 |
| `scripts/validate_coursework_skill.py` | 新增 20 项校验 | 检查导航、示例、脚本、核验、密钥、绝对路径、运行结果 `checks.json` |
| `references/cn-coursework-checklist.md` | 新增 | 把实验要求写成可执行清单 |
| `SKILL.md` | 新增“课程作业增强”一节 | 说明何时读新参考、何时跑新校验 |
| `NOTICE.md` | 新增 | 保留来源、提交号、许可和修改记录 |

原始 `LICENSE.txt` 未改动。

## 4. 改造前后输出对比

### 4.1 结构校验

| 对象 | 改造前（官方脚本） | 改造后（修复编码 + 增强校验） |
|---|---|---|
| `de-analysis` | GBK `UnicodeDecodeError` | `Skill is valid!`；课程校验 20/20 通过 |
| `medical-dialogue` | GBK `UnicodeDecodeError` | `Skill is valid!`；课程校验 20/20 通过 |
| 缺陷样例 | （官方脚本因中文崩溃） | 课程校验 6 项通过、**11 项失败** |

缺陷样例的失败项包括：name 与目录名不一致、缺 `references/index.md`、缺深层参考、
缺 `checks.py`、缺示例输入、SKILL.md 未说明输入输出/流程/核验、命中假密钥、命中本机
绝对路径。

修复编码后，官方结构校验对缺陷样例仍返回 `Skill is valid!`，说明“结构校验通过”
不等于“满足课程可核查要求”；这正是新增脚本要补的缺口。

### 4.2 自建 Skill 的运行核验

| Skill | `checks.py` | 课程校验 |
|---|---|---|
| de-analysis | 14 项全部通过；复算 log2FC/P/padj 最大偏差 0.00e+00；真值精确率 1.000、召回率 0.500 | 20/20 |
| medical-dialogue | 7 项全部通过；18 个原文片段全部被且仅被覆盖一次 | 20/20 |

## 5. 复现命令

```powershell
# 改造前（原始脚本，会因 GBK 失败）
python C:\Users\21336\tools\anthropic-skills\skills\skill-creator\scripts\quick_validate.py `
  .claude\skills\de-analysis

# 改造后：官方结构校验
python .claude\skills\skill-creator\scripts\quick_validate.py .claude\skills\de-analysis

# 改造后：课程增强校验（含运行结果）
python .claude\skills\skill-creator\scripts\validate_coursework_skill.py `
  .claude\skills\de-analysis --run-dir outputs\03_skill_de
```

## 6. 相关文件

- `before_quick_validate.log` — 改造前的 GBK 报错
- `after_quick_validate.log` — 修复后两个 Skill 的校验结果
- `broken_validation.log` — 缺陷样例的 11 项失败明细
- `structure_only_vs_coursework.log` — 官方结构校验 vs 课程增强校验
- `validate_de.json`、`validate_dialogue.json` — 课程校验报告

## 7. 说明

- 这是课程实验中的本地改造，不代表 Anthropic 官方版本。
- 如再分发，需保留 Apache 2.0 `LICENSE.txt` 与 `NOTICE.md`。
- 缺陷样例放在系统临时目录，仅用于测试，未提交到仓库；其中的密钥是明显的假值
  `sk-DUMMY...`，不是真实凭据。
