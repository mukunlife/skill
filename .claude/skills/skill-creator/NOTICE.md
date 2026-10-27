# 来源与修改记录

## 原始来源

- 项目：Anthropic `skills` 仓库
- 地址：https://github.com/anthropics/skills
- 路径：`skills/skill-creator`
- 提交：`dbd4588f9e1033efb41dad4bef2f7947c8993d44`（2026-10-09）
- 许可：Apache License 2.0（见同目录 `LICENSE.txt`，原始版权归 Anthropic, PBC）

## 本项目的修改（2026-10-27）

| 文件 | 修改 | 原因 |
|---|---|---|
| `scripts/quick_validate.py` | `read_text()` 改为 `read_text(encoding="utf-8")` | 原版在 Windows 默认 GBK 下读取中文 SKILL.md 会抛 `UnicodeDecodeError` |
| `scripts/validate_coursework_skill.py` | 新增 | 在官方结构校验之外，检查导航、示例、核验脚本、密钥/绝对路径，以及运行结果 `checks.json` |
| `references/cn-coursework-checklist.md` | 新增 | 把“智能体实践实验一”的 Skill 要求写成可执行清单 |
| `SKILL.md` | 新增“课程作业增强”一节 | 说明何时读取新参考文档、何时运行新校验脚本 |

## 说明

- 本改造仅用于课程实验，不代表 Anthropic 官方版本。
- Apache 2.0 允许修改与再分发；本目录保留原始 `LICENSE.txt` 与本 NOTICE。
- 如再分发，请同时保留上述来源、提交号、许可和修改记录。
