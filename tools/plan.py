"""plan.tsv + log/sessions.tsv 로 오늘 공부할 것을 정량적으로 정한다.

usage:
  python3 tools/plan.py next                          # /study 가 다음에 할 항목 1개
  python3 tools/plan.py today                         # 오늘 남은 예산과 일정
  python3 tools/plan.py progress                      # 단계별 진척, 보정 계수, 남은 공부일
  python3 tools/plan.py log <id> <분> <정답률%> <done|partial>   # 계획 밖 주제는 id 를 x:<concept> 로
  python3 tools/plan.py test

규칙:
- 하루 예산 DAILY_MIN 분을 트랙 A:B = A_SHARE:(1-A_SHARE) 로 나눈다.
- next: 오늘 예산 대비 덜 쓴 트랙에서, 아직 done 이 아닌 첫 항목.
- 계획 밖 세션(x:...)은 트랙 X 로 잡혀 트랙 예산은 안 줄이지만, 하루 총 예산에는 포함된다.
- done 은 세션 끝에 정답률 >= PASS_PCT 이고 그 항목 분량을 끝냈을 때만 기록한다(skill 이 판단).
- 보정 계수 k = done 항목의 실제 분 합 / 예상 분 합. 남은 시간 예측에 곱한다.
"""
import csv, sys
from collections import defaultdict
from datetime import date
from math import ceil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "plan.tsv"
SESSIONS = ROOT / "log" / "sessions.tsv"
DAILY_MIN = 500  # 10시간 = 50분 세션 10회 + 휴식. 휴식 빼고 순수 공부 시간
A_SHARE = 0.6    # 트랙 A:B = 3:2
PASS_PCT = 80    # 완료 기준 정답률 (모르겠음은 오답으로 계산)
FIELDS = ["date", "id", "minutes", "accuracy", "status"]


def read(path):
    if not path.exists():
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def state(plan, sessions):
    spent, done = defaultdict(int), set()
    for s in sessions:
        spent[s["id"]] += int(s["minutes"])
        if s["status"] == "done":
            done.add(s["id"])
    est = sum(int(p["est_min"]) for p in plan if p["id"] in done)
    k = sum(spent[i] for i in done) / est if est else 1.0
    return spent, done, k


def remaining(p, spent, k):
    """보정한 예상치에서 이미 쓴 시간을 뺀 값. 예상을 넘겼는데 아직 미완료면 한 세션(50분)."""
    left = round(int(p["est_min"]) * k) - spent[p["id"]]
    return left if left > 0 else 50


def budgets():
    a = round(DAILY_MIN * A_SHARE)
    return {"A": a, "B": DAILY_MIN - a}


def used_today(plan, sessions, today):
    track = {p["id"]: p["track"] for p in plan}
    used = defaultdict(int)
    for s in sessions:
        if s["date"] == today:
            used[track.get(s["id"], "X")] += int(s["minutes"])
    return used


def next_item(plan, sessions, today):
    spent, done, k = state(plan, sessions)
    used, budget = used_today(plan, sessions, today), budgets()
    if sum(used.values()) >= DAILY_MIN:
        return None, 0
    tracks = sorted(budget, key=lambda t: (used[t] / budget[t], t))
    for t in tracks:
        if used[t] >= budget[t]:
            continue
        for p in plan:
            if p["track"] == t and p["id"] not in done:
                return p, remaining(p, spent, k)
    return None, 0


def today_plan(plan, sessions, today):
    """트랙별 남은 예산을 순서대로 항목에 채운다."""
    spent, done, k = state(plan, sessions)
    used, budget = used_today(plan, sessions, today), budgets()
    out = {}
    for t in budget:
        left, items = budget[t] - used[t], []
        for p in plan:
            if left <= 0:
                break
            if p["track"] == t and p["id"] not in done:
                need = remaining(p, spent, k)
                items.append((p, min(need, left), need))
                left -= need
        out[t] = (used[t], budget[t], items)
    return out


def progress(plan, sessions):
    spent, done, k = state(plan, sessions)
    rows = []
    stages = list(dict.fromkeys((p["track"], p["stage"]) for p in plan))
    for t, st in stages:
        ps = [p for p in plan if (p["track"], p["stage"]) == (t, st)]
        left = sum(remaining(p, spent, k) for p in ps if p["id"] not in done)
        rows.append((t, st, sum(p["id"] in done for p in ps), len(ps), left))
    days = {t: ceil(sum(r[4] for r in rows if r[0] == t) / b) for t, b in budgets().items()}
    return rows, k, days


def log(args):
    pid, minutes, acc, status = args
    assert status in ("done", "partial"), status
    assert pid.startswith("x:") or any(p["id"] == pid for p in read(PLAN)), f"plan.tsv 에 없는 id: {pid} (계획 밖이면 x:<concept>)"
    if status == "done" and int(acc) < PASS_PCT:
        sys.exit(f"정답률 {acc}% < {PASS_PCT}% 이므로 done 이 아니라 partial 로 기록해야 함")
    new = not SESSIONS.exists()
    with open(SESSIONS, "a", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        if new:
            w.writerow(FIELDS)
        w.writerow([date.today().isoformat(), pid, int(minutes), int(acc), status])


def demo():
    plan = [
        {"id": "A-1", "track": "A", "stage": "la", "est_min": "60"},
        {"id": "A-2", "track": "A", "stage": "la", "est_min": "100"},
        {"id": "B-1", "track": "B", "stage": "cs", "est_min": "100"},
    ]
    d = "2026-10-02"
    assert next_item(plan, [], d)[0]["id"] == "A-1"  # 동률이면 A
    s = [{"date": d, "id": "A-1", "minutes": "90", "accuracy": "85", "status": "done"}]
    _, _, k = state(plan, s)
    assert k == 1.5  # 60분 예상 → 90분 걸림
    p, need = next_item(plan, s, d)
    assert p["id"] == "B-1" and need == 150  # A 를 더 썼으니 B, 예상 100 × 1.5
    s.append({"date": d, "id": "B-1", "minutes": "50", "accuracy": "60", "status": "partial"})
    assert remaining(plan[2], state(plan, s)[0], k) == 100
    tp = today_plan(plan, s, d)
    assert tp["A"][0] == 90 and tp["A"][2][0][0]["id"] == "A-2" and tp["A"][2][0][1] == 150
    rows, _, days = progress(plan, s)
    assert rows[0][2:] == (1, 2, 150) and days == {"A": 1, "B": 1}
    over = [{"date": d, "id": "A-1", "minutes": "300", "accuracy": "0", "status": "partial"}]
    assert next_item(plan, over, d)[0]["id"] == "B-1"  # A 예산 소진
    assert remaining(plan[0], state(plan, over)[0], 1.0) == 50  # 예상 초과 미완료 → 한 세션
    adhoc = [{"date": d, "id": "x:quaternion", "minutes": "500", "accuracy": "90", "status": "done"}]
    assert used_today(plan, adhoc, d)["X"] == 500 and next_item(plan, adhoc, d)[0] is None  # 계획 밖도 하루 총량에 포함
    assert state(plan, adhoc)[2] == 1.0  # 보정 계수에는 영향 없음


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "today"
    if cmd == "test":
        demo(); print("ok"); sys.exit()
    plan, sessions, today = read(PLAN), read(SESSIONS), date.today().isoformat()
    if cmd == "log":
        log(sys.argv[2:])
    elif cmd == "next":
        p, need = next_item(plan, sessions, today)
        if not p:
            print("오늘 예산 소진. 쉬거나 복습만.")
        else:
            print(f"{p['id']}\t{p['stage']}\t{p['concept']}\t{p['title']}\t{p['source']}\t남은 약 {need}분")
    elif cmd == "today":
        x = used_today(plan, sessions, today)["X"]
        if x:
            print(f"## 계획 밖: {x}분 사용 (하루 총 {DAILY_MIN}분에 포함)")
        for t, (used, budget, items) in today_plan(plan, sessions, today).items():
            print(f"## 트랙 {t}: {used}/{budget}분 사용")
            for p, take, need in items:
                part = f" (남은 {need}분 중 오늘 {take}분)" if take < need else ""
                print(f"- {p['id']} {p['title']} · {p['source']} · {take}분{part}")
    elif cmd == "progress":
        rows, k, days = progress(plan, sessions)
        print(f"보정 계수 k = {k:.2f} (실제/예상, done 항목 기준)")
        for t, st, d, n, left in rows:
            print(f"- {t} {st}: {d}/{n} 완료, 남은 약 {left}분")
        print("남은 공부일: " + ", ".join(f"트랙 {t} {n}일" for t, n in days.items()))
    else:
        print(__doc__)
