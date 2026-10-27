# 提交副本说明

本目录按实验提交清单提供两个自建 Skill 的完整副本：

- `de-analysis/`：两组基因表达差异分析
- `medical-dialogue/`：医疗对话整理为问答记录

每个目录都包含 `SKILL.md`、`references/`、`scripts/` 和 `examples/` 示例输入。

## 与运行时目录的关系

- Claude Code 实际加载的是项目根目录下的 `.claude/skills/`，两份内容一致。
- 本目录是**提交与展示副本**；修改 Skill 时应以 `.claude/skills/` 为准，再同步到这里。
- 改造过的现有 Skill `skill-creator` 只保留在 `.claude/skills/`，因为提交清单只要求
  “两个自建专业 Skill”；它的来源与改动见
  `outputs/06_existing_skill/modification_record.md`。

## 未参与提交的上游候选 Skill

`scientific-critical-thinking/` 和 `scientific-writing/` 是下载评估过的第三方 Skill
（K-Dense Inc.，MIT），没有修改，也没有在实验记录中使用，**不属于本次两个自建 Skill**。
提交前建议删除这两个目录，避免与 `de-analysis`、`medical-dialogue` 混淆。
