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
import re
import subprocess
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

REMOTE = os.environ.get("AID_RESULT_REMOTE", "gdrive:AID/결과받기")
CONFIRM_MARKER = "_AI적용_확정_"
OUT = Path(os.environ.get("AID_SUBMITTED", "submitted.json"))


def submitted_departments() -> tuple[list[str], dict]:
    """확정 마커가 존재하는 학과 폴더명 목록(정렬) + 학과별 결과폴더 지도 {학과명: {url, madeAt}}."""
    out = subprocess.run(
        ["rclone", "lsf", REMOTE, "-R", "--files-only", "--format", "p"],
        check=True, capture_output=True, text=True,
    ).stdout
    depts: set[str] = set()
    made: dict[str, str] = {}
    for line in out.splitlines():
        line = line.strip()
        if CONFIRM_MARKER not in line or "/" not in line:
            continue
        dept = line.split("/", 1)[0].strip()
        if not dept:
            continue
        depts.add(dept)
        m = re.search(r"(\d{8}_\d{4})", line)
        if m and m.group(1) > made.get(dept, ""):
            made[dept] = m.group(1)
    # 학과 폴더 ID → 공개 URL (웹앱에서 서버 조회 없이 즉시 '결과 폴더 열기' 링크 표시용)
    folders: dict[str, dict] = {}
    try:
        lst = subprocess.run(
            ["rclone", "lsjson", REMOTE, "--dirs-only"],
            check=True, capture_output=True, text=True,
        ).stdout
        for d in json.loads(lst or "[]"):
            name = unicodedata.normalize("NFC", d.get("Name", "")).strip()
            fid = d.get("ID")
            if name and fid:
                folders[name] = {"url": f"https://drive.google.com/drive/folders/{fid}", "madeAt": made.get(name, "")}
    except Exception as e:  # 폴더 지도는 부가 정보 — 실패해도 배지 갱신은 진행
        print(f"폴더 지도 생성 실패(무시): {e}", file=sys.stderr)
    return sorted(depts), folders


DEPT_DATA_FOLDER_ID = os.environ.get("AID_DEPT_DATA_FOLDER_ID", "1r0QylZKNLHNRfCKoAuUnWyPWKmFHxzKL")


def submission_progress() -> dict:
    """학과별 과목 제출 진행 {학과명: {done, need}} — 서버의 과목별 제출 기록(_ai4_sel_<dc>.json)과 정적 데이터 대조."""
    import tempfile
    progress: dict[str, dict] = {}
    try:
        idx = json.loads(Path("data/index.json").read_text(encoding="utf-8"))
    except Exception as e:
        print(f"index.json 읽기 실패(무시): {e}", file=sys.stderr)
        return progress
    tmp = Path(tempfile.mkdtemp())
    try:
        subprocess.run(["rclone", "copy", "--drive-root-folder-id", DEPT_DATA_FOLDER_ID, "gdrive:", str(tmp),
                        "--include", "_ai4_sel_*.json"], check=True, capture_output=True, text=True)
    except Exception as e:
        print(f"제출 기록 복사 실패(무시): {e}", file=sys.stderr)
        return progress
    for d in idx.get("depts", []):
        dc, name = d.get("dc"), unicodedata.normalize("NFC", d.get("name", ""))
        need = sum(1 for c in d.get("courses", []) if c.get("status") == "적용대상")
        f = tmp / f"_ai4_sel_{dc}.json"
        done = 0
        if f.exists():
            try:
                rec = json.loads(f.read_text(encoding="utf-8"))
                targets = {unicodedata.normalize("NFC", c["name"]) for c in d.get("courses", []) if c.get("status") == "적용대상"}
                done = sum(1 for k in (rec.get("courses") or {}) if unicodedata.normalize("NFC", k) in targets)
            except Exception:
                done = 0
        if need or done:
            progress[name] = {"done": done, "need": need}
    return progress


def main() -> int:
    depts, folders = submitted_departments()
    # 러너는 UTC → 한국 날짜(KST)로 표기
    kst_today = datetime.now(timezone(timedelta(hours=9))).date()
    progress = submission_progress()
    payload = {"submitted": depts, "folders": folders, "progress": progress, "asOf": kst_today.isoformat()}
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
