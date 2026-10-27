#!/usr/bin/env python
"""核验问答记录是否逐字来自原文、是否覆盖全部发言。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import parse  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="核验 medical-dialogue 的输出")
    parser.add_argument("--input", required=True, help="原始对话文本")
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out = Path(args.output_dir)
    checks: list[dict] = []

    def add(name: str, passed: bool, detail: str = "") -> None:
        checks.append({"check": name, "passed": bool(passed), "detail": detail})

    def finish() -> int:
        payload = {"passed": all(item["passed"] for item in checks), "checks": checks}
        (out / "checks.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["passed"] else 1

    required = ["qa.md", "qa.json"]
    missing = [name for name in required if not (out / name).exists()]
    add("必需文件齐全", not missing, f"缺失：{missing}")
    if missing:
        return finish()

    source = Path(args.input)
    if not source.exists():
        add("原始文件存在", False, str(source))
        return finish()
    text = source.read_text(encoding="utf-8-sig")
    payload = json.loads((out / "qa.json").read_text(encoding="utf-8"))
    meta = payload["meta"]
    options = meta.get("parse_options", {})

    turns, parse_errors, empty_content = parse.parse_dialogue(
        text,
        tuple(options.get("doctor_labels", [])),
        tuple(options.get("patient_labels", [])),
    )
    merged = parse.merge_turns(turns)
    source_norm = "".join(parse.normalize_for_check(item["text"]) for item in merged)
    merged_by_id = {}
    for item in merged:
        for turn_id in item["source_turn_ids"]:
            merged_by_id[turn_id] = item

    pairs = payload.get("pairs", [])
    unmatched = payload.get("unmatched_patient", [])
    notes = payload.get("doctor_notes", [])
    others = payload.get("other_turns", [])

    counts_ok = (
        meta["pairs"] == len(pairs)
        and meta["unmatched"] == len(unmatched)
        and meta["doctor_notes"] == len(notes)
        and meta["other_turns"] == len(others)
        and meta["turns"] == len(merged)
        and meta["parse_errors"] == len(parse_errors)
        and meta["empty_content"] == len(empty_content)
    )
    add(
        "统计数字与实际一致",
        counts_ok,
        f"turns={len(merged)}, pairs={len(pairs)}, unmatched={len(unmatched)}, "
        f"notes={len(notes)}, others={len(others)}, "
        f"parse_errors={len(parse_errors)}, empty={len(empty_content)}",
    )

    output_items: list[dict] = []
    for pair in pairs:
        output_items.append(pair["question"])
        output_items.append(pair["answer"])
    output_items.extend(unmatched)
    output_items.extend(notes)
    output_items.extend(others)

    roles_ok = all(
        pair["question"]["role"] == "patient" and pair["answer"]["role"] == "doctor"
        for pair in pairs
    )
    add("每个问答对均为患者问、医生答", roles_ok, f"问答对 {len(pairs)} 个")

    trace_ok = True
    trace_detail: list[str] = []
    for item in output_items:
        normalized = parse.normalize_for_check(item.get("text", ""))
        if not normalized:
            trace_ok = False
            trace_detail.append(f"空文本（第 {item.get('line_no')} 行）")
            continue
        if normalized not in source_norm:
            trace_ok = False
            trace_detail.append(f"原文中找不到：{item.get('text', '')[:30]}...")
        ids = item.get("source_turn_ids", [])
        source_item = merged_by_id.get(ids[0]) if ids else None
        if source_item is None or source_item["text"] != item.get("text"):
            trace_ok = False
            trace_detail.append(f"与原文不一致（第 {item.get('line_no')} 行）")
    add(
        "输出逐字来自原文",
        trace_ok,
        "; ".join(trace_detail[:5]) if trace_detail else "全部输出均为原文片段",
    )

    represented = [
        turn_id
        for item in output_items
        for turn_id in item.get("source_turn_ids", [])
    ]
    all_ids = [
        turn_id for item in merged for turn_id in item["source_turn_ids"]
    ]
    coverage_ok = sorted(represented) == sorted(all_ids)
    add(
        "全部发言被且仅被覆盖一次",
        coverage_ok,
        f"原文发言片段 {len(all_ids)}，输出覆盖 {len(represented)}，"
        f"去重后 {len(set(represented))}",
    )

    qa_md = (out / "qa.md").read_text(encoding="utf-8")
    md_stats_ok = (
        f"问答对：{meta['pairs']}" in qa_md
        and f"未配对的患者发言：{meta['unmatched']}" in qa_md
        and f"格式错误行：{meta['parse_errors']}" in qa_md
    )
    add("qa.md 统计与 qa.json 一致", md_stats_ok, "")
    add(
        "qa.md 声明逐字整理",
        "未补充、未改写、未推断" in qa_md,
        "",
    )

    return finish()


if __name__ == "__main__":
    raise SystemExit(main())
