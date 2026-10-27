#!/usr/bin/env python3
"""课程作业 Skill 结构与可核查性校验（本项目新增）。

在官方 quick_validate.py 之外，额外检查：
- references/index.md 导航、示例输入、入口脚本与核验脚本
- SKILL.md 是否说明了输入输出、执行流程和结果核验
- 是否写入 API 密钥或本机绝对路径
- 指定运行目录时，checks.json 是否通过

用法：
    python scripts/validate_coursework_skill.py <skill目录> [--run-dir <运行输出目录>] \
        [--json-out <报告路径>]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # 允许在未安装 pyyaml 的环境给出明确提示
    yaml = None

TEXT_SUFFIXES = {".md", ".py", ".r", ".txt", ".json", ".yaml", ".yml", ".sh"}
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"ANTHROPIC_AUTH_TOKEN\s*[:=]\s*['\"]?[A-Za-z0-9]", re.I),
    re.compile(r"api[_-]?key\s*[:=]\s*['\"][A-Za-z0-9]{8,}", re.I),
]
ABS_PATH_PATTERN = re.compile(r"[A-Za-z]:\\Users\\|/home/[^/\s]+/|/Users/[^/\s]+/")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def text_files(root: Path) -> list[Path]:
    return [
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="课程作业 Skill 校验")
    parser.add_argument("skill_dir")
    parser.add_argument("--run-dir", default=None, help="可选：检查该目录下 checks.json")
    parser.add_argument("--json-out", default=None, help="可选：把报告写成 JSON")
    args = parser.parse_args(argv)

    skill = Path(args.skill_dir)
    results: list[dict] = []

    def add(name: str, passed: bool, detail: str = "") -> None:
        results.append({"check": name, "passed": bool(passed), "detail": detail})

    if not skill.is_dir():
        print(f"[FAIL] 目录不存在：{skill}")
        return 2

    skill_md = skill / "SKILL.md"
    add("SKILL.md 存在", skill_md.exists(), str(skill_md))
    if not skill_md.exists():
        return finish(results, args.json_out)

    content = read_text(skill_md)
    match = re.match(r"^---\s*\n(.*?)\n---\s*", content, re.DOTALL)
    add("YAML frontmatter 格式正确", bool(match), "以 --- 开头并闭合")
    frontmatter: dict = {}
    if match:
        if yaml is None:
            add("pyyaml 可用", False, "未安装 pyyaml，无法解析 frontmatter")
        else:
            try:
                frontmatter = yaml.safe_load(match.group(1)) or {}
                add("frontmatter 可解析", isinstance(frontmatter, dict), "")
            except yaml.YAMLError as exc:
                add("frontmatter 可解析", False, str(exc))

    name = str(frontmatter.get("name", "")).strip()
    description = str(frontmatter.get("description", "")).strip()
    add("name 存在且为 kebab-case", bool(re.fullmatch(r"[a-z0-9-]+", name)), name or "缺失")
    add("name 与目录名一致", name == skill.name, f"name={name!r}, dir={skill.name!r}")
    add(
        "description 长度 1~1024 且无尖括号",
        bool(description) and len(description) <= 1024 and "<" not in description,
        f"{len(description)} 字符",
    )

    references = skill / "references"
    index_md = references / "index.md"
    add("references/index.md 存在", index_md.exists(), "")
    other_refs = (
        sorted(p for p in references.glob("*.md") if p.name != "index.md")
        if references.is_dir()
        else []
    )
    add("至少有一个深层参考文档", bool(other_refs), f"{len(other_refs)} 个")
    if index_md.exists():
        index_text = read_text(index_md)
        missing_links = [p.name for p in other_refs if p.name not in index_text]
        add("index.md 指向全部深层参考", not missing_links, f"未链接：{missing_links}")
        add(
            "SKILL.md 指向 references/index.md",
            "references/index.md" in content,
            "",
        )

    scripts = skill / "scripts"
    script_files = sorted(
        p for p in scripts.glob("*") if p.suffix.lower() in {".py", ".r"}
    ) if scripts.is_dir() else []
    add("scripts/ 至少有一个脚本", bool(script_files), f"{len(script_files)} 个")
    add(
        "存在独立核验脚本（checks.py）",
        (scripts / "checks.py").exists(),
        "",
    )
    referenced_scripts = [p.name for p in script_files if p.name in content]
    add("SKILL.md 说明了脚本调用方法", bool(referenced_scripts), f"提到：{referenced_scripts}")

    examples = skill / "examples"
    example_files = (
        [p for p in examples.rglob("*") if p.is_file() and p.name != "README.md"]
        if examples.is_dir()
        else []
    )
    add("examples/ 含示例输入", bool(example_files), f"{len(example_files)} 个")

    add("SKILL.md 说明输入与输出", "输入" in content and "输出" in content, "")
    add("SKILL.md 含执行流程", "执行流程" in content or "工作流程" in content, "")
    add("SKILL.md 说明结果核验", "核验" in content, "")

    secrets_hits: list[str] = []
    abs_path_hits: list[str] = []
    for path in text_files(skill):
        for line_no, line in enumerate(read_text(path).splitlines(), start=1):
            if any(pattern.search(line) for pattern in SECRET_PATTERNS):
                secrets_hits.append(f"{path.relative_to(skill)}:{line_no}")
            if ABS_PATH_PATTERN.search(line):
                abs_path_hits.append(f"{path.relative_to(skill)}:{line_no}")
    add("未写入疑似 API 密钥", not secrets_hits, f"命中：{secrets_hits[:5]}")
    add("未写入本机绝对路径", not abs_path_hits, f"命中：{abs_path_hits[:5]}")

    if args.run_dir:
        checks_path = Path(args.run_dir) / "checks.json"
        passed = False
        detail = f"未找到 {checks_path}"
        if checks_path.exists():
            payload = json.loads(read_text(checks_path))
            passed = bool(payload.get("passed"))
            detail = f"passed={passed}"
        add("运行目录的 checks.json 通过", passed, detail)

    return finish(results, args.json_out)


def finish(results: list[dict], json_out: str | None) -> int:
    passed = sum(1 for item in results if item["passed"])
    failed = len(results) - passed
    for item in results:
        mark = "PASS" if item["passed"] else "FAIL"
        line = f"[{mark}] {item['check']}"
        if item["detail"]:
            line += f" — {item['detail']}"
        print(line)
    print(f"\n结果：{passed} 项通过，{failed} 项失败")
    payload = {"passed": failed == 0, "passed_count": passed, "failed_count": failed,
               "checks": results}
    if json_out:
        Path(json_out).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
