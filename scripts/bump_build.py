#!/usr/bin/env python3
"""화면 배포 전 빌드 표기를 올린다: index.html 의 BUILD 상수·표기 문구와 version.json 을 같은 값으로 맞춘다.
사용: python3 scripts/bump_build.py            (오늘 날짜 + 알파벳 자동 증가)
      python3 scripts/bump_build.py 2026-09-11a
"""
import json, re, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
html_p = ROOT / "index.html"
ver_p = ROOT / "version.json"
html = html_p.read_text(encoding="utf-8")
cur = re.search(r"var BUILD='([^']+)'", html).group(1)
if len(sys.argv) > 1:
    new = sys.argv[1]
else:
    today = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
    if cur.startswith(today) and cur[-1].isalpha():
        new = today + chr(ord(cur[-1]) + 1)
    else:
        new = today + "a"
html = html.replace(f"var BUILD='{cur}'", f"var BUILD='{new}'").replace(f"화면 빌드 {cur}", f"화면 빌드 {new}")
html_p.write_text(html, encoding="utf-8")
ver_p.write_text(json.dumps({"build": new}) + "\n", encoding="utf-8")
print(f"build {cur} -> {new}")
