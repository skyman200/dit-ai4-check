#!/usr/bin/env python3
"""구글드라이브 '결과받기' 폴더의 확정 제출 여부로 index.html 배지를 자동 갱신.

동작 원리(멱등·가역):
- 각 학과 카드의 `.cnt`(전체/완료/수정 필요) 숫자에서 '기본 배지'를 재계산한다.
    · 수정 필요 N (>0)  -> 수정 N   (b-todo)
    · 수정 필요 없음     -> 적용완료 (b-done)
- 드라이브 '결과받기/<학과>/…_AI적용_확정_…' 마커가 있으면 '제출완료'(b-submit)로 덮어쓴다.
- 제출이 취소(마커 삭제)되면 기본 배지로 자동 복귀한다.

rclone은 읽기 전용(lsf)만 사용한다. 토큰은 출력하지 않는다.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

REMOTE = os.environ.get("AID_RESULT_REMOTE", "gdrive:AID/결과받기")
CONFIRM_MARKER = "_AI적용_확정_"
INDEX = Path(os.environ.get("AID_INDEX", "index.html"))

# nm + badge + 이어지는 cnt 를 한 번에 잡아 배지를 재작성한다.
CARD_RE = re.compile(
    r'(?P<pre><span class="nm">)(?P<nm>[^<]+)'
    r'(?P<mid></span><span class="badge )(?P<cls>[a-z-]+)(?P<q1>">)(?P<txt>[^<]*)'
    r'(?P<post></span></div>\s*<span class="cnt">)(?P<cnt>[^<]*)(?P<end></span>)'
)
NEED_RE = re.compile(r"수정\s*필요\s*(\d+)")


def submitted_departments() -> set[str]:
    """확정 마커가 존재하는 학과 폴더명 집합. (테스트 항목 제외)"""
    out = subprocess.run(
        ["rclone", "lsf", REMOTE, "-R", "--files-only", "--format", "p"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    depts: set[str] = set()
    for line in out.splitlines():
        line = line.strip()
        if CONFIRM_MARKER not in line or "/" not in line:
            continue
        dept = line.split("/", 1)[0].strip()
        if not dept or "테스트" in dept:
            continue
        depts.add(dept)
    return depts


def compute_badge(nm: str, cnt: str, submitted: set[str]) -> tuple[str, str]:
    """(css_class, text) 반환."""
    if nm.strip() in submitted:
        return "b-submit", "제출완료"
    m = NEED_RE.search(cnt)
    if m and int(m.group(1)) > 0:
        return "b-todo", f"수정 {int(m.group(1))}"
    return "b-done", "적용완료"


def main() -> int:
    submitted = submitted_departments()
    print(f"제출완료 학과({len(submitted)}): {', '.join(sorted(submitted)) or '(없음)'}")

    html = INDEX.read_text(encoding="utf-8")

    changed: list[str] = []

    def repl(m: re.Match) -> str:
        nm = m.group("nm")
        cnt = m.group("cnt")
        cls, txt = compute_badge(nm, cnt, submitted)
        if cls != m.group("cls") or txt != m.group("txt"):
            changed.append(f"{nm.strip()}: {m.group('txt')} -> {txt}")
        return (
            m.group("pre") + nm + m.group("mid") + cls + m.group("q1") + txt
            + m.group("post") + cnt + m.group("end")
        )

    new_html, n = CARD_RE.subn(repl, html)
    if n == 0:
        print("경고: 학과 카드를 찾지 못했습니다. index.html 구조를 확인하세요.", file=sys.stderr)
        return 2

    print(f"카드 {n}개 검사, 변경 {len(changed)}건")
    for c in changed:
        print("  · " + c)

    if new_html != html:
        INDEX.write_text(new_html, encoding="utf-8")
        print("index.html 갱신됨")
    else:
        print("변경 없음")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
