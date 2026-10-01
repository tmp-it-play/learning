"""quiz.tsv 분석: 복습 대상(due)과 확신도 캘리브레이션(calib).

usage: python3 tools/stats.py [due|calib]   (기본: 둘 다)
log 형식(TSV): date  topic  concept  result(O/X/?)  confidence(1-3)  note
"""
import csv, sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

LOG = Path(__file__).resolve().parent.parent / "log" / "quiz.tsv"
INTERVALS = [1, 3, 7, 14, 30, 60]  # 연속 정답 수 → 다음 복습까지 일수


def load(path=LOG):
    if not path.exists():
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def due(rows, today=None):
    today = today or date.today()
    hist = defaultdict(list)
    for r in rows:
        hist[(r["topic"], r["concept"])].append(r)
    out = []
    for key, rs in hist.items():
        rs.sort(key=lambda r: r["date"])
        streak = 0
        for r in reversed(rs):
            if r["result"] != "O":
                break
            streak += 1
        nxt = date.fromisoformat(rs[-1]["date"]) + timedelta(days=INTERVALS[min(streak, len(INTERVALS) - 1)] if streak else 1)
        if nxt <= today:
            out.append((nxt.isoformat(), *key))
    return sorted(out)


def calib(rows):
    by = defaultdict(lambda: [0, 0])
    for r in rows:
        if r["result"] == "?":  # 모름은 캘리브레이션에서 제외
            continue
        by[r["confidence"]][0] += r["result"] == "O"
        by[r["confidence"]][1] += 1
    return {c: (ok, n, round(100 * ok / n)) for c, (ok, n) in sorted(by.items())}


def demo():
    rows = [
        {"date": "2026-10-01", "topic": "LA", "concept": "rank", "result": "O", "confidence": "1"},
        {"date": "2026-10-01", "topic": "LA", "concept": "det", "result": "X", "confidence": "3"},
        {"date": "2026-10-01", "topic": "LA", "concept": "span", "result": "?", "confidence": "1"},
    ]
    d = due(rows, date(2026, 10, 2))
    assert ("2026-10-02", "LA", "det") in d and ("2026-10-02", "LA", "span") in d
    assert all(c != "rank" for *_, c in d)  # 1회 정답 → 3일 뒤
    assert ("2026-10-04", "LA", "rank") in due(rows, date(2026, 10, 4))
    assert calib(rows) == {"1": (1, 1, 100), "3": (0, 1, 0)}


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd == "test":
        demo(); print("ok"); sys.exit()
    rows = load()
    if cmd in ("due", "all"):
        print("## 복습 대상")
        for d, t, c in due(rows):
            print(f"- [{t}] {c} (예정 {d})")
    if cmd in ("calib", "all"):
        print("## 확신도별 정답률")
        for c, (ok, n, p) in calib(rows).items():
            print(f"- 확신 {c}: {ok}/{n} = {p}%")
