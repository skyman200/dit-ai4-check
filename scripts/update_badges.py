#!/usr/bin/env python3
"""구글드라이브 '결과받기' 폴더의 확정 제출 여부를 submitted.json 으로 내보낸다.

정적 렌더 구조(index.html + data.json)에서는 배지를 클라이언트가 그린다.
- 기본 배지(수정 N / 적용완료)는 data.json 의 과목 status 로 계산.
- '제출완료'(b-submit)는 이 스크립트가 만드는 submitted.json 을 클라이언트가 병합해 덮어쓴다.
- 제출이 취소(마커 삭제)되면 submitted.json 에서 빠져 자동으로 기본 배지로 복귀한다.

rclone 은 읽기 전용(lsf)만 사용한다. 토큰은 출력하지 않는다.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REMOTE = os.environ.get("AID_RESULT_REMOTE", "gdrive:AID/결과받기")
CONFIRM_MARKER = "_AI적용_확정_"
OUT = Path(os.environ.get("AID_SUBMITTED", "submitted.json"))


def submitted_departments() -> list[str]:
    """확정 마커가 존재하는 학과 폴더명 목록(정렬, 테스트 제외)."""
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
        if not dept or "테스트" in dept or "TEST" in dept.upper():
            continue
        depts.add(dept)
    return sorted(depts)


def main() -> int:
    submitted = submitted_departments()
    print(f"제출완료 학과({len(submitted)}): {', '.join(submitted) or '(없음)'}")

    payload = json.dumps(
        {"submitted": submitted}, ensure_ascii=False, separators=(",", ":")
    )
    prev = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
    if payload != prev:
        OUT.write_text(payload, encoding="utf-8")
        print(f"{OUT} 갱신됨")
    else:
        print("변경 없음")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
