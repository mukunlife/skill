#!/usr/bin/env python
"""把医患对话原文整理为结构化问答记录。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import parse  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="医疗对话整理为问答记录")
    parser.add_argument("--input", required=True, help="对话文本文件（UTF-8）")
    parser.add_argument("--output-dir", required=True, help="输出目录")
    parser.add_argument("--title", default="医疗对话问答记录")
    parser.add_argument(
        "--doctor-label", action="append", default=[], help="额外的医生标签，可重复"
    )
    parser.add_argument(
        "--patient-label", action="append", default=[], help="额外的患者标签，可重复"
    )
    return parser.parse_args(argv)


def render_turn(turn: dict) -> str:
    return f"**{turn['speaker']}：** {turn['text']}（原文第 {turn['line_no']} 行）"


def write_markdown(
    path: Path,
    meta: dict,
    pairs: list[dict],
    unmatched: list[dict],
    notes: list[dict],
    others: list[dict],
    parse_errors: list[dict],
    empty_content: list[dict],
) -> None:
    lines = [
        f"# {meta['title']}",
        "",
        f"> 来源：`{meta['source']}`（共 {meta['total_lines']} 行）。",
        "> 整理规则：仅去除时间戳和说话人标签，以下内容逐字来自原文，"
        "未补充、未改写、未推断。规则见 `references/rules.md`。",
        "",
        "## 统计",
        "",
        f"- 有效发言：{meta['turns']} 条（合并连续同一说话人后）",
        f"- 问答对：{meta['pairs']}",
        f"- 未配对的患者发言：{meta['unmatched']}",
        f"- 医生单方面说明：{meta['doctor_notes']}",
        f"- 其他角色发言：{meta['other_turns']}",
        f"- 格式错误行：{meta['parse_errors']}；空内容行：{meta['empty_content']}",
        "",
        "## 问答记录",
        "",
    ]
    if pairs:
        for pair in pairs:
            question = pair["question"]
            answer = pair["answer"]
            lines += [
                f"### Q{pair['pair_id']}",
                "",
                render_turn(question),
                "",
                render_turn(answer),
                "",
            ]
    else:
        lines += ["未识别到完整的患者—医生问答对。", ""]

    def appendix(title: str, items: list[dict], empty_text: str) -> None:
        lines.extend([f"## {title}", ""])
        if not items:
            lines.extend([empty_text, ""])
            return
        for item in items:
            reason = f"——{item.get('reason', '')}" if item.get("reason") else ""
            lines.append(f"- {render_turn(item)}{reason}")
        lines.append("")

    appendix("未配对的患者发言", unmatched, "无。")
    appendix("医生单方面说明", notes, "无。")
    appendix("其他角色发言", others, "无。")

    lines.extend(["## 解析异常", ""])
    if not parse_errors and not empty_content:
        lines.extend(["无。", ""])
    for item in parse_errors:
        lines.append(f"- 第 {item['line_no']} 行：`{item['text']}`（{item['reason']}）")
    for item in empty_content:
        lines.append(
            f"- 第 {item['line_no']} 行：{item['speaker']} 的发言为空（{item['reason']}）"
        )
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source = Path(args.input)
    if not source.exists():
        print(f"[错误] 文件不存在：{source}")
        return 2
    try:
        text = source.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        print(f"[错误] 无法按 UTF-8 读取 {source}：{exc}")
        return 2

    doctor_labels = tuple(args.doctor_label)
    patient_labels = tuple(args.patient_label)
    turns, parse_errors, empty_content = parse.parse_dialogue(
        text, doctor_labels, patient_labels
    )
    if not turns:
        print("[错误] 没有识别到任何有效发言，请检查格式和说话人标签")
        return 2

    merged = parse.merge_turns(turns)
    pairs, unmatched, notes, others = parse.pair_turns(merged)

    meta = {
        "title": args.title,
        "source": str(args.input),
        "source_name": source.name,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_lines": len(text.splitlines()),
        "turns": len(merged),
        "source_turns": len(turns),
        "pairs": len(pairs),
        "unmatched": len(unmatched),
        "doctor_notes": len(notes),
        "other_turns": len(others),
        "parse_errors": len(parse_errors),
        "empty_content": len(empty_content),
        "parse_options": {
            "doctor_labels": list(doctor_labels),
            "patient_labels": list(patient_labels),
        },
    }

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": meta,
        "pairs": pairs,
        "unmatched_patient": unmatched,
        "doctor_notes": notes,
        "other_turns": others,
        "parse_errors": parse_errors,
        "empty_content": empty_content,
    }
    (out_dir / "qa.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_markdown(
        out_dir / "qa.md",
        meta,
        pairs,
        unmatched,
        notes,
        others,
        parse_errors,
        empty_content,
    )

    print(
        f"[完成] 有效发言 {meta['turns']} 条，问答对 {meta['pairs']} 个，"
        f"未配对 {meta['unmatched']} 条，解析异常 {meta['parse_errors']} 行。"
        f"输出目录：{out_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
