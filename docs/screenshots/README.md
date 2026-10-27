# 截图目录

## 已放入（2026-10-27）

| 文件 | 内容 |
|---|---|
| `01_ccswitch_deepseek.png` | CC Switch 中启用 DeepSeek 服务商，未显示密钥 |
| `01b_connection_ok_file.png` | `connection_ok.txt` 实际内容 |
| `02b_claude_cli_connected.png` | Claude Code CLI 使用当前配置回复“连接成功” |
| `02c_api_probe.png` | 向 DeepSeek 端点发送最小请求：HTTP 200、模型一致、密钥 REDACTED |
| `03_files_exist.png` | 资源管理器中 `connection_ok.txt`、`实验记录.txt`、`skills/`、`outputs/`、`TCGA-KIRC/` |
| `05a_file_modified_content.png` | `实验记录.txt` 在 Agent 之外被修改后的内容 |
| `05b_agent_reread.png` | Agent 读取修改后的 `实验记录.txt`：4 行、237 字节 |
| `07_de_checks.png` | TCGA-KIRC 真实数据 `checks.py`：13 项全部通过 |
| `08_dialogue_checks.png` | `medical-dialogue` `checks.py`：7 项全部通过 |
| `09_skill_list.png` | 新会话 Skill 列表：`de-analysis`、`medical-dialogue`、`skill-creator` |
| `11_existing_skill_before_after.png` | 改造前 GBK 崩溃 vs 改造后 `Skill is valid!` |
| `12_zip_and_tree.png` | 提交 ZIP 与项目根目录 |

## 仍需补拍

| 文件 | 内容 |
|---|---|
| `02_vscode_connected.png` | VS Code 扩展面板内的成功响应（若教师要求扩展面板而非 CLI） |
| `06_webchat_compare.png` | 网页 Chat 对“创建实验记录.txt 并读取”的实际回复 |
| `10_github_repo.png` | 推送成功后的 GitHub 仓库首页 |

## 注意

- 截图中不得出现完整 API 密钥；已有截图已确认无密钥。
- 新增截图后，在 `docs/实验记录.md` 对应位置加 Markdown 图片行，再运行
  `python docs/build_docx.py` 重新生成 docx。
