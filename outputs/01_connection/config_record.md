# Agent 与 DeepSeek API 配置记录

记录时间：2026-10-27
记录人：牛晨杰（2024187025）

## 1. 工具与版本

| 工具 | 版本 / 说明 |
|---|---|
| VS Code | 1.133.0（x64） |
| Claude Code 扩展 | `anthropic.claude-code@2.1.311` |
| CC Switch | 4.0.21（安装包 `CC-Switch-v4.0.21-Windows.msi`） |
| Python | 3.14.7（系统同时存在 3.8；本实验使用 3.14.7 虚拟环境） |
| R | 未安装；两个 Skill 的脚本均使用 Python，故不影响实验 |
| Git | 2.56.0.windows.3（winget 安装） |

> 实验说明写的是 Python 3.10、R 4.0 以上；本机实际为 Python 3.14.7、无 R。
> 差异已如实记录，脚本只使用 pandas/numpy/scipy/matplotlib，Python 3.10+ 均可运行。

## 2. 连接配置

配置文件：`C:\Users\21336\.claude\settings.json`（用户级，不在本仓库内）

| 配置项 | 值 |
|---|---|
| `ANTHROPIC_BASE_URL` | `https://api.deepseek.com/anthropic` |
| `ANTHROPIC_MODEL` | `deepseek-flash[1M]` |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | `deepseek-flash[1M]` |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | `deepseek-flash[1M]` |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | `deepseek-flash[1M]` |
| `ANTHROPIC_AUTH_TOKEN` | 已配置；本记录与仓库中均不保存明文 |
| CC Switch `live-state.json` | `"claude": {"mode": "direct"}` |

## 3. 实际请求核验

仅看配置或模型自述不足以判断服务商，因此用 `verify_endpoint.py` 按上述配置向
`https://api.deepseek.com/anthropic/v1/messages` 发送了一次最小请求：

```json
{
  "base_url": "https://api.deepseek.com/anthropic",
  "model_configured": "deepseek-flash[1M]",
  "auth_token": "REDACTED",
  "http_status": 200,
  "response_model": "deepseek-flash[1M]",
  "server_header": "openresty"
}
```

完整结果见同目录 `api_probe.json`（已把 token 写为 REDACTED）。

**结论**：请求实际发往 `api.deepseek.com`，返回 HTTP 200，响应模型为
`deepseek-flash[1M]`；CC Switch 为 direct 模式，没有经本地代理转发。可以确认本次
配置连接的是 DeepSeek，而不是仅凭模型自述。

## 4. 文件创建与回读

- 在工作区创建 `connection_ok.txt`，内容按要求写入并回读成功。
- 工作区文件：[connection_ok.txt](connection_ok.txt)；项目副本保存在本目录。
- 实验三的 `实验记录.txt` 创建、外部修改、再次读取的过程见
  `outputs/02_file_ops/file_ops_log.md`。

## 5. 安全注意事项

- `ANTHROPIC_AUTH_TOKEN` 是明文密钥，只存在于用户级 `settings.json`，**不要提交到 Git**。
- 截图时必须遮住 CC Switch 和 `settings.json` 中的密钥。
- 本仓库的 `.gitignore` 已排除 `.claude/settings.json`、`.claude/settings.local.json` 和 `.venv/`。
- 如密钥曾出现在截图或聊天记录中，建议在 DeepSeek 控制台轮换。
