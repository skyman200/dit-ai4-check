#!/usr/bin/env python3
"""구글드라이브 '결과받기' 폴더를 읽어 제출완료 학과 목록(submitted.json)을 갱신.

동작(멱등·가역):
- 결과받기/<학과>/…_AI적용_확정_….pdf 확정 마커가 있는 학과 폴더명을 수집한다.
- submitted.json = {"submitted":[학과명...], "asOf":"YYYY-MM-DD"} 로 저장한다.
- 랜딩(index.html)이 이 파일을 fetch 해 '제출완료' 배지를 표시한다(정적 렌더).
- 제출이 취소(마커 삭제)되면 목록에서 자동 제외된다.

rclone은 읽기 전용(lsf)만 사용한다. 토큰은 출력하지 않는다.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REMOTE = os.environ.get("AID_RESULT_REMOTE", "gdrive:AID/결과받기")
CONFIRM_MARKER = "_AI적용_확정_"
OUT = Path(os.environ.get("AID_SUBMITTED", "submitted.json"))


def submitted_departments() -> list[str]:
    """확정 마커가 존재하는 학과 폴더명 목록(정렬)."""
    out = subprocess.run(
        ["rclone", "lsf", REMOTE, "-R", "--files-only", "--format", "p"],
        check=True, capture_output=True, text=True,
    ).stdout
    depts: set[str] = set()
    for line in out.splitlines():
        line = line.strip()
        if CONFIRM_MARKER not in line or "/" not in line:
            continue
        dept = line.split("/", 1)[0].strip()
        if dept:
            depts.add(dept)
    return sorted(depts)


def main() -> int:
    depts = submitted_departments()
    # 러너는 UTC → 한국 날짜(KST)로 표기
    kst_today = datetime.now(timezone(timedelta(hours=9))).date()
    payload = {"submitted": depts, "asOf": kst_today.isoformat()}
    new = json.dumps(payload, ensure_ascii=False, indent=1)

    old = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
    if new.strip() == old.strip():
        print(f"변경 없음 — 제출완료 {len(depts)}개 학과")
        return 0

    OUT.write_text(new, encoding="utf-8")
    print(f"submitted.json 갱신 — 제출완료 {len(depts)}개: {', '.join(depts) or '(없음)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
