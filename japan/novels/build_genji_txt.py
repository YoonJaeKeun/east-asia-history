#!/usr/bin/env python3
"""Build a UTF-8 plain-text reader edition from the current Genji drafts."""

import re
from pathlib import Path


BASE = Path(__file__).resolve().parent
SOURCE_DIR = BASE / "genji-complete"
OUTPUT = SOURCE_DIR / "겐지 이야기 현재 번역본 제1-13첩.txt"
CHAPTERS = [
    "01-kiritsubo.md",
    "02-hahakigi.md",
    "03-utsusemi.md",
    "04-yugao.md",
    "05-wakamurasaki.md",
    "06-suetsumuhana.md",
    "07-momijinoga.md",
    "08-hananoen.md",
    "09-aoi.md",
    "10-sakaki.md",
    "11-hanachirusato.md",
    "12-suma.md",
    "13-akashi.md",
]


def reader_text(source: str) -> str:
    """Remove Markdown/editorial markup while retaining prose and verse."""
    source = source.split("\n## 번역·대조 기록", 1)[0]
    lines: list[str] = []
    for line in source.splitlines():
        if line.startswith("> 번역 상태:"):
            continue
        if line.strip() == "---":
            continue
        line = re.sub(r"^#\s+", "", line)
        line = re.sub(r"^>\s?", "    ", line)
        line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
        line = re.sub(r"\*(.*?)\*", r"\1", line)
        lines.append(line.rstrip())
    return "\n".join(lines).strip()


parts = [
    "겐지 이야기 현대 한국어 번역본",
    "무라사키 시키부",
    "",
    "수록 범위: 제1첩 기리쓰보 ~ 제13첩 아카시",
    "※ 제1~12첩은 현재 대조 완료본이며, 제13첩은 원문 대조·확장 작업 중인 원고입니다.",
]

for filename in CHAPTERS:
    path = SOURCE_DIR / filename
    parts.extend(("", "=" * 72, "", reader_text(path.read_text(encoding="utf-8"))))

OUTPUT.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")
print(OUTPUT)
