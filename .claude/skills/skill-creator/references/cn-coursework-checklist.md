# 中文医学/生物信息课程 Skill 检查清单（本项目新增）

本清单把“智能体实践实验一”的 Skill 要求转成可执行检查项，供
`scripts/validate_coursework_skill.py` 使用。

## 目录结构

```text
skill-name/
├── SKILL.md                 # name / description + 执行流程
├── references/
│   ├── index.md             # 导航：什么条件下读哪份文档
│   ├── overview.md          # 背景、方法、适用边界
│   └── rules.md             # 数据格式、参数、阈值、异常处理
├── scripts/
│   ├── run.py               # 入口：读取输入并产出结果
│   ├── checks.py            # 独立核验：复算或追溯，失败返回非 0
│   └── <helpers>.py         # 辅助模块
└── examples/
    └── <示例输入>            # 可复现的输入，不是空目录
```

文件夹存在不等于被使用：`SKILL.md` 必须明确写出“何时读哪份 reference、何时调用哪个脚本、如何核验结果”。

## 硬性检查项

| 检查 | 通过条件 |
|---|---|
| frontmatter | `name` 为 kebab-case、与目录名一致；`description` 1–1024 字符且无尖括号 |
| 导航 | `references/index.md` 存在，并链接到所有深层参考文档 |
| 脚本 | `scripts/` 至少一个 `.py` 或 `.R`，且存在 `checks.py` |
| 调用说明 | `SKILL.md` 至少提到一个真实脚本文件名 |
| 示例 | `examples/` 至少一个非 README 的输入文件 |
| 说明完整性 | `SKILL.md` 含“输入”“输出”“执行流程”“核验” |
| 安全 | 不出现 `sk-...` 等密钥、`ANTHROPIC_AUTH_TOKEN`、本机绝对路径 |
| 运行核验 | 传 `--run-dir` 时，该目录的 `checks.json` 必须 `passed: true` |

## 推荐检查项（人工）

- 描述是否能让 Skill 在正确时机被触发，而不是只说“处理数据”。
- 方法、阈值、比较方向是否写在 `rules.md`，而不是藏在脚本里。
- `checks.py` 是否独立于 `run.py` 重新计算，而不是只检查文件是否存在。
- 是否明确写出方法局限（例如 t 检验不等同于 DESeq2）。
- 示例数据是否注明来源，模拟数据不得写成教师提供的数据。

## 使用方法

```bash
python scripts/validate_coursework_skill.py <skill目录> \
    --run-dir <该 Skill 的运行输出目录> \
    --json-out <报告路径>
```

退出码 0 表示全部通过；1 表示存在失败项；2 表示路径错误。
