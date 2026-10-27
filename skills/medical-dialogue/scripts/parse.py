"""医疗对话的解析、合并与配对核心逻辑。"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

LINE_RE = re.compile(
    r"^\s*(?:\[(?P<time>[^\]]+)\]\s*)?"
    r"(?P<speaker>[^:：]{1,12})\s*[:：]\s*(?P<text>.*)$"
)
TIMESTAMP_RE = re.compile(r"\[[^\]]*\]")

DEFAULT_DOCTOR_LABELS = {"医生", "医师", "doctor", "dr", "dr."}
DEFAULT_PATIENT_LABELS = {"患者", "病人", "patient"}


@dataclass
class Turn:
    turn_id: int
    line_no: str
    speaker: str
    role: str
    text: str

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["source_turn_ids"] = [self.turn_id]
        return payload


def classify_speaker(
    speaker: str,
    doctor_labels: tuple[str, ...] = (),
    patient_labels: tuple[str, ...] = (),
) -> str:
    key = speaker.strip().lower()
    doctors = {label.lower() for label in DEFAULT_DOCTOR_LABELS | set(doctor_labels)}
    patients = {label.lower() for label in DEFAULT_PATIENT_LABELS | set(patient_labels)}
    if key in doctors:
        return "doctor"
    if key in patients:
        return "patient"
    return "other"


def parse_dialogue(
    text: str,
    doctor_labels: tuple[str, ...] = (),
    patient_labels: tuple[str, ...] = (),
) -> tuple[list[Turn], list[dict], list[dict]]:
    """返回 (发言列表, 格式错误行, 空内容行)。"""
    turns: list[Turn] = []
    parse_errors: list[dict] = []
    empty_content: list[dict] = []

    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip().lstrip("﻿")
        if not line:
            continue
        match = LINE_RE.match(line)
        if not match:
            parse_errors.append(
                {
                    "line_no": str(line_no),
                    "text": line,
                    "reason": "未识别为“说话人：内容”格式",
                }
            )
            continue
        speaker = match.group("speaker").strip()
        content = match.group("text").strip()
        if not content:
            empty_content.append(
                {"line_no": str(line_no), "speaker": speaker, "reason": "空内容"}
            )
            continue
        role = classify_speaker(speaker, doctor_labels, patient_labels)
        turns.append(
            Turn(
                turn_id=len(turns) + 1,
                line_no=str(line_no),
                speaker=speaker,
                role=role,
                text=content,
            )
        )
    return turns, parse_errors, empty_content


def merge_turns(turns: list[Turn]) -> list[dict]:
    """合并连续且说话人相同的发言；保留原始行号区间与来源 turn_id。"""
    merged: list[dict] = []
    for turn in turns:
        if merged and merged[-1]["speaker"] == turn.speaker:
            last = merged[-1]
            last["text"] = f"{last['text']} {turn.text}"
            first_line = last["line_no"].split("-")[0]
            last["line_no"] = f"{first_line}-{turn.line_no}"
            last["source_turn_ids"].append(turn.turn_id)
        else:
            merged.append(turn.to_dict())
    return merged


def pair_turns(merged: list[dict]) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """按规则配对，返回 (问答对, 未配对患者发言, 医生说明, 其他角色)。"""
    pairs: list[dict] = []
    unmatched_patient: list[dict] = []
    doctor_notes: list[dict] = []
    other_turns: list[dict] = []

    index = 0
    while index < len(merged):
        current = merged[index]
        if current["role"] == "patient":
            if index + 1 < len(merged) and merged[index + 1]["role"] == "doctor":
                pairs.append(
                    {
                        "pair_id": len(pairs) + 1,
                        "question": current,
                        "answer": merged[index + 1],
                    }
                )
                index += 2
            else:
                item = dict(current)
                item["reason"] = "缺少医生回应"
                unmatched_patient.append(item)
                index += 1
        elif current["role"] == "doctor":
            item = dict(current)
            item["reason"] = "医生单方面说明"
            doctor_notes.append(item)
            index += 1
        else:
            item = dict(current)
            item["reason"] = "其他角色发言"
            other_turns.append(item)
            index += 1

    return pairs, unmatched_patient, doctor_notes, other_turns


def normalize_for_check(text: str) -> str:
    """去掉时间戳和所有空白，用于逐字追溯核验。"""
    return re.sub(r"\s+", "", TIMESTAMP_RE.sub("", text))
