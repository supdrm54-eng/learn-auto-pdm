"""learn-auto-pdm 정답 스크립트 — Block 1~5 산출물과 대시보드를 한 번에 만든다.

사용: 작업 폴더(안에 data/ 가 있는 곳)에서 실행한다.
    python build_pdm.py
만드는 것:
    output/cases_table.md, output/sensor_clean.csv, output/unit_fix_log.md   (Block 1)
    output/normal_range.csv, output/anomaly_candidates.csv                    (Block 2)
    output/trend_judgement.md                                                 (Block 3)
    output/report.md                                                          (Block 4)
    output/pilot_ranking.csv, output/pilot_note.md                            (Block 5)
    index.html                                                                (Block 3~5 대시보드)
    expected.json                                                             (검증 기준값)
"""
import csv
import html
import json
import re
import statistics as st
from pathlib import Path

DATA = Path("data")
OUT = Path("output")
OUT.mkdir(exist_ok=True)

SENSOR_TRAP = DATA / "Day5_설비센서_단위혼재_함정_가상.csv"
CASES = DATA / "Day5_예지보전_도입사례_실데이터.csv"
PILOT = DATA / "Day5_공정별_파일럿평가_가정값_가상.csv"

VARS = [("진동(mm/s)", "진동", "mm/s"), ("온도(℃)", "온도", "℃"), ("압력(bar)", "압력", "bar")]
BASELINE_POINTS = 12          # 기준 구간: 첫 4시간(08:00~11:40)
SAVING_RATES = (0.20, 0.30)   # 절감률 가정(추정) — 원본 정답 메모의 20~30%

expected = {}


def put(key, value, block, decimals=None):
    """expected.json 에 넣을 값을 모은다."""
    expected[key] = {"value": value, "decimals": decimals, "block": block}


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def short(eq):
    """'설비A(프레스 메인모터)' → '설비A'"""
    return eq.split("(")[0]


def hhmm(t):
    return t[-5:]


# ───────────── Block 0 · 데이터 행 수 ─────────────
lab_files = sorted(DATA.glob("*.csv"))
put("lab_file_count", len(lab_files), 0, 0)
put("rows_sensor", len(read_csv(DATA / "Day5_설비센서_50건_가상.csv")), 0, 0)
put("rows_trap", len(read_csv(SENSOR_TRAP)), 0, 0)
put("rows_cases", len(read_csv(CASES)), 0, 0)
put("rows_pilot", len(read_csv(PILOT)), 0, 0)

# ───────────── Block 1 · 도입사례 표 ─────────────
cases = read_csv(CASES)
lines = ["# 예지보전 도입사례 (공개 보도 실데이터)", "",
         "| 기업 | 설비 | 사용 센서 | 예측 대상 | 보고된 효과 | 연도 | 출처 |",
         "|---|---|---|---|---|---|---|"]
with_numbers = 0
for c in cases:
    effect = c["효과(보고된 수치 그대로)"]
    if "수치 미공개" in effect:
        effect = re.sub(r"수치 미공개\((.*?)\)", r"수치 미공개 — \1", effect)
    else:
        with_numbers += 1
    lines.append(f"| {c['기업']} | {c['설비/공정']} | {c['사용센서(진동·온도·압력 등)']} | {c['예측대상']} | "
                 f"{effect} | {c['발표연도']} | {c['출처URL']} |")
sensor_hits = {k: sum(k in c["사용센서(진동·온도·압력 등)"] for c in cases) for k in ("진동", "온도", "압력")}
top = max(sensor_hits, key=sensor_hits.get)
lines += ["", f"가장 자주 쓰인 센서: {top} ({sensor_hits[top]}건 / 진동 {sensor_hits['진동']} · 온도 {sensor_hits['온도']} · 압력 {sensor_hits['압력']}). "
          "센서 종류를 밝히지 않은 사례가 있어 건수는 명시된 것만 셌다."]
(OUT / "cases_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
put("cases_with_numbers", with_numbers, 1, 0)

# ───────────── Block 1 · 단위 정리 ─────────────
# 설비마다 가장 많이 쓰인 기록장치를 '주 로거'로 보고, 다른 기록장치 행 중
# 주 로거 중앙값의 절반 미만이거나 두 배 초과인 값만 단위가 다르다고 판단한다.
CONVERT = {
    "진동(mm/s)": ("in/s", lambda v: round(v * 25.4, 2)),
    "온도(℃)": ("℉", lambda v: round((v - 32) * 5 / 9, 1)),
    "압력(bar)": ("psi", lambda v: round(v * 0.0689476, 1)),
}
trap = read_csv(SENSOR_TRAP)
fixes = []
for eq in sorted({r["설비"] for r in trap}):
    rows = [r for r in trap if r["설비"] == eq]
    loggers = [r["기록장치"] for r in rows]
    main_logger = max(set(loggers), key=loggers.count)
    for col, (unit, conv) in CONVERT.items():
        med = st.median(float(r[col]) for r in rows if r["기록장치"] == main_logger)
        for r in rows:
            v = float(r[col])
            if r["기록장치"] != main_logger and not (med / 2 <= v <= med * 2):
                new = conv(v)
                fixes.append({"설비": short(eq), "시각": hhmm(r["시간"]), "항목": col.split("(")[0],
                              "기록값": f"{v:g} {unit}", "환산값": new, "단위": col[col.index("(") + 1:-1],
                              "기록장치": r["기록장치"],
                              "근거": f"주 로거 {main_logger} 중앙값 {med:g}의 범위(½~2배) 밖"})
                r[col] = f"{new:g}"
with open(OUT / "sensor_clean.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(trap[0].keys()))
    w.writeheader()
    w.writerows(trap)
log = ["# 단위 정리 기록", "", "| 설비 | 시각 | 항목 | 기록값 | 환산값 | 기록장치 | 근거 |", "|---|---|---|---|---|---|---|"]
log += [f"| {x['설비']} | {x['시각']} | {x['항목']} | {x['기록값']} | {x['환산값']:g} {x['단위']} | {x['기록장치']} | {x['근거']} |" for x in fixes]
(OUT / "unit_fix_log.md").write_text("\n".join(log) + "\n", encoding="utf-8")
put("unit_fix_count", len(fixes), 1, 0)
put("unit_fix_a_temp", sum(x["설비"] == "설비A" and x["항목"] == "온도" for x in fixes), 1, 0)
put("unit_fix_b_vib", sum(x["설비"] == "설비B" and x["항목"] == "진동" for x in fixes), 1, 0)
put("unit_fix_b_press", sum(x["설비"] == "설비B" and x["항목"] == "압력" for x in fixes), 1, 0)
put("fix_a_1000_temp", next(x["환산값"] for x in fixes if x["설비"] == "설비A" and x["시각"] == "10:00"), 1, 1)
put("fix_b_1500_press", next(x["환산값"] for x in fixes if x["설비"] == "설비B" and x["시각"] == "15:00"), 1, 1)

# ───────────── Block 2 · 설비별 평균 ± 2σ ─────────────
clean = trap
series = {}   # (설비, 변수) → [(시각, 값)]
for r in clean:
    for col, _, _ in VARS:
        series.setdefault((short(r["설비"]), col), []).append((hhmm(r["시간"]), float(r[col])))

ranges, anomalies = {}, []
for (eq, col), pts in series.items():
    vals = [v for _, v in pts]
    m, s = st.mean(vals), st.stdev(vals)        # 표본표준편차(n-1)
    lo, hi = m - 2 * s, m + 2 * s
    ranges[(eq, col)] = (m, s, lo, hi)
    for t, v in pts:
        if not lo <= v <= hi:
            anomalies.append({"설비": eq, "시각": t, "변수": col, "값": v, "하한": lo, "상한": hi,
                              "방향": "상한 초과" if v > hi else "하한 미만"})

with open(OUT / "normal_range.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["설비", "변수", "평균", "표준편차", "하한", "상한"])
    for (eq, col), (m, s, lo, hi) in sorted(ranges.items()):
        w.writerow([eq, col, f"{m:.3f}", f"{s:.3f}", f"{lo:.3f}", f"{hi:.3f}"])
with open(OUT / "anomaly_candidates.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["설비", "시각", "변수", "값", "하한", "상한", "벗어난 방향"])
    for a in anomalies:
        w.writerow([a["설비"], a["시각"], a["변수"], f"{a['값']:g}", f"{a['하한']:.3f}", f"{a['상한']:.3f}", a["방향"]])

r_ = lambda eq, col: ranges[(eq, col)]
put("a_vib_mean", round(r_("설비A", "진동(mm/s)")[0], 3), 2, 3)
put("a_vib_low", round(r_("설비A", "진동(mm/s)")[2], 2), 2, 2)
put("a_vib_high", round(r_("설비A", "진동(mm/s)")[3], 2), 2, 2)
put("b_vib_low", round(r_("설비B", "진동(mm/s)")[2], 2), 2, 2)
put("b_vib_high", round(r_("설비B", "진동(mm/s)")[3], 2), 2, 2)
put("b_temp_low", round(r_("설비B", "온도(℃)")[2], 2), 2, 2)
put("b_temp_high", round(r_("설비B", "온도(℃)")[3], 2), 2, 2)
put("anomaly_total", len(anomalies), 2, 0)


def fmt_points(eq, col):
    return "·".join(f"{a['시각']} {a['값']:g}" for a in anomalies if a["설비"] == eq and a["변수"] == col)


put("anomaly_list", ", ".join(f"{eq} {col.split('(')[0]} {fmt_points(eq, col)}"
                              for eq, col in dict.fromkeys((a["설비"], a["변수"]) for a in anomalies)), 2)

# ───────────── Block 3 · 노이즈 vs 추세, 상승 시작 시각 ─────────────
def judge(eq, col, t):
    pts = series[(eq, col)]
    i = [x for x, _ in pts].index(t)
    lo, hi = ranges[(eq, col)][2:]
    if i + 1 < len(pts) and lo <= pts[i + 1][1] <= hi:
        return "노이즈"
    if i >= 2 and pts[i - 2][1] < pts[i - 1][1] < pts[i][1]:
        return "추세"
    return "판정 보류"


def rise_start(eq, col):
    """기준 구간 최댓값을 넘은 뒤 끝까지 다시 내려오지 않는 첫 시각."""
    pts = series[(eq, col)]
    base = max(v for _, v in pts[:BASELINE_POINTS])
    for i in range(BASELINE_POINTS, len(pts)):
        if all(v > base for _, v in pts[i:]):
            return pts[i][0], base
    return None, base


for a in anomalies:
    a["판정"] = judge(a["설비"], a["변수"], a["시각"])
starts = {k: rise_start(*k) for k in series}

jl = ["# 노이즈 vs 추세 판정", "", "실습용 가상 데이터 · 평상 범위 = 설비별 평균 ± 2σ(표본표준편차)", "",
      "| 설비 | 변수 | 이상 후보 | 판정 | 상승 시작 시각 | 근거 |", "|---|---|---|---|---|---|"]
for (eq, col) in sorted(series):
    cand = fmt_points(eq, col) or "없음"
    js = sorted({a["판정"] for a in anomalies if a["설비"] == eq and a["변수"] == col})
    start, base = starts[(eq, col)]
    verdict = "·".join(js) if js else ("범위 안 상승(추정)" if start else "정상")
    why = f"기준 구간 최댓값 {base:g}" + (f" → {start}부터 끝까지 그 위" if start else " 위로 계속 머문 구간 없음")
    jl.append(f"| {eq} | {col} | {cand} | {verdict} | {start or '없음'} | {why} |")
b_vib_start = starts[("설비B", "진동(mm/s)")][0]
b_temp_start = starts[("설비B", "온도(℃)")][0]
jl += ["", f"**정비 필요 시점**: 설비B 진동 상승 시작 {b_vib_start} (추세). 설비B 온도는 {b_temp_start}부터 평상 범위 안에서 먼저 오르기 시작했다(범위 안 상승, 추정 — 마찰·윤활 문제 의심 근거).",
       "설비A 진동 12:40 값은 다음 시점에 평상 범위로 돌아와 노이즈로 본다 — 기록하고 관찰."]
(OUT / "trend_judgement.md").write_text("\n".join(jl) + "\n", encoding="utf-8")

first = lambda eq, col: next(a for a in anomalies if a["설비"] == eq and a["변수"] == col)
put("a_vib_outlier", fmt_points("설비A", "진동(mm/s)"), 3)
put("a_vib_judgement", first("설비A", "진동(mm/s)")["판정"], 3)
put("b_vib_outliers", fmt_points("설비B", "진동(mm/s)"), 3)
put("b_vib_judgement", first("설비B", "진동(mm/s)")["판정"], 3)
put("b_temp_outlier", fmt_points("설비B", "온도(℃)"), 3)
put("b_temp_judgement", first("설비B", "온도(℃)")["판정"], 3)
put("b_vib_trend_start", b_vib_start, 3)
put("b_temp_rise_start", b_temp_start, 3)


def window(eq, col, center, before, after):
    """원본 실습과제 2 수열이 나온 구간(시작~끝 시각)."""
    pts = series[(eq, col)]
    i = [x for x, _ in pts].index(center)
    return f"{pts[i - before][0]}~{pts[min(i + after, len(pts) - 1)][0]}"


put("task2_noise_window", window("설비A", "진동(mm/s)", first("설비A", "진동(mm/s)")["시각"], 3, 1), 3)
put("task2_trend_window", window("설비B", "진동(mm/s)", series[("설비B", "진동(mm/s)")][-1][0], 4, 0), 3)

# ───────────── Block 5 · 파일럿 선정 ─────────────
pilot = []
for r in read_csv(PILOT):
    loss = float(r["시간당정지손실(만원)"]) * float(r["연간고장건수"]) * float(r["평균정지시간(h)"])
    inv = float(r["센서·구축 초기투자(만원)"])
    assert round(loss) == round(float(r["연간정지손실(만원, =손실×건수×시간)"])), r["공정"]
    pilot.append({"공정": r["공정"], "시간당손실": float(r["시간당정지손실(만원)"]), "연간손실": loss,
                  "투자": inv, "배수": loss / inv, "용이성": r["센서부착용이성(상중하)"]})
pilot.sort(key=lambda p: -p["배수"])
with open(OUT / "pilot_ranking.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["순위", "공정", "시간당정지손실(만원)", "연간정지손실(만원)", "초기투자(만원)", "배수", "센서부착용이성", "비고"])
    for i, p in enumerate(pilot, 1):
        w.writerow([i, p["공정"], f"{p['시간당손실']:g}", f"{p['연간손실']:.0f}", f"{p['투자']:.0f}", f"{p['배수']:.2f}", p["용이성"], "실습용 가상 데이터"])
best = pilot[0]
net = {}
for rate in SAVING_RATES:
    saving = best["연간손실"] * rate
    net[rate] = (saving, saving - best["투자"], best["투자"] / saving)
assembly = next(p for p in pilot if p["공정"] == "조립")
top_hourly = max(pilot, key=lambda p: p["시간당손실"])
note = [
    "# 파일럿 선정 메모 (실습용 가상 데이터)", "",
    f"시간당 정지손실만 보면 {top_hourly['공정']}({top_hourly['시간당손실']:,.0f}만원)이 가장 크지만, 연간 고장이 적고 센서 대상이 흩어져 연간 정지손실 ÷ 초기 투자 배수가 {assembly['배수']:.2f}배에 그친다. "
    f"같은 기준에서 {best['공정']}는 {best['배수']:.2f}배라 작게 시작해 빨리 증명하기에 맞다.", "",
    "## 1순위 순효과 (보수적 추정 — 부품비 절감 0, 정지손실 절감만)", "",
    "| 절감률(추정) | 연간 절감액(만원) | 1년 순효과(만원) | 투자 회수(년) |", "|---|---|---|---|",
]
note += [f"| {int(r * 100)}% | {s:,.0f} | {n:,.0f} | {pb:.1f} |" for r, (s, n, pb) in net.items()]
note += ["", "## 성과 지표", "", "- 계획 외 정지 시간(시간/월) — 파일럿 전 3개월 기준선 대비",
         "- MTBF(고장 간 평균 시간) — 같은 설비군의 파일럿 전후 비교"]
(OUT / "pilot_note.md").write_text("\n".join(note) + "\n", encoding="utf-8")

put("pilot_ranking", " > ".join(f"{p['공정']} {p['배수']:.2f}" for p in pilot), 5)
put("pilot_first", best["공정"], 5)
put("press_annual_loss", round(best["연간손실"]), 5, 0)
put("press_saving_20", round(net[0.20][0]), 5, 0)
put("press_net_20", round(net[0.20][1]), 5, 0)
put("press_payback_20", round(net[0.20][2], 1), 5, 1)
put("press_saving_30", round(net[0.30][0]), 5, 0)
put("press_payback_30", round(net[0.30][2], 1), 5, 1)
put("assembly_ratio", round(assembly["배수"], 2), 5, 2)

# ───────────── Block 4 · 4단 보고서 ─────────────
rB = lambda col: ranges[("설비B", col)]
report = f"""# 예지보전 진단 보고서 — 프레스 메인모터 · 차체 용접로봇 감속기

> 실습용 가상 데이터 기반 (2026-09-15 08:00~16:00, 20분 간격 25시점 × 설비 2대)

**핵심 요약**
1. 이상 후보 {len(anomalies)}건 — 설비A 진동 1건은 노이즈, 설비B 진동 2건·온도 1건은 추세.
2. 설비B 감속기는 진동이 {b_vib_start}부터 연속 상승, 온도는 그보다 이른 {b_temp_start}부터 오르기 시작 → 다음 휴무일 계획 정비 권고.
3. 개선안: 설비B 측정 주기 단축과 '연속 상승' 추세 경보 추가(추정 기준, 2주 운영 후 재조정).

## ① 현황 진단

| 설비 | 변수 | 이상 후보 | 평상 범위 |
|---|---|---|---|
""" + "\n".join(
    f"| {a['설비']} | {a['변수']} | {a['시각']} {a['값']:g} | {a['하한']:.2f} ~ {a['상한']:.2f} |" for a in anomalies
) + f"""

설비A 온도·압력, 설비B 압력은 이상 후보가 없다.

## ② 이상 패턴과 원인 추정

- 설비A 진동 {fmt_points('설비A', '진동(mm/s)')}: 다음 시점에 평상 범위로 돌아온 한 번의 튐 → **노이즈**. 측정 오류·순간 외란 가능(추정).
- 설비B 진동 {fmt_points('설비B', '진동(mm/s)')}: {b_vib_start}부터 매 시점 상승하며 상한 {rB('진동(mm/s)')[3]:.2f}을 넘음 → **추세**.
- 설비B 온도 {fmt_points('설비B', '온도(℃)')}: {b_temp_start}부터 평상 범위 안에서 먼저 오르다가 마지막에 상한 {rB('온도(℃)')[3]:.2f}을 넘음 → **추세**.
- 온도가 먼저 오르고 진동이 뒤따르는 패턴은 감속기 윤활 부족·베어링 마모 초기와 맞는다(추정 — 현장 확인 필요). 압력은 평상이라 유압 계통 문제 가능성은 낮다(추정).

## ③ 정비 권고 시점

- 설비B(차체 용접로봇 감속기): 진동 상승 시작 {b_vib_start}을 정비 필요 시점으로 본다. 라인을 바로 세우기보다 **다음 휴무일 계획 정비**(윤활 상태·베어링 점검)를 권고하고, 그때까지 측정 주기를 줄여 관찰한다.
- 설비A(프레스 메인모터): 정비 불필요. 같은 튐이 반복되면 센서·배선부터 점검한다.

## ④ 개선안

- 점검 주기: 설비B 진동·온도 측정 20분 → 5분(추정 기준).
- 임계값: 한 점 기준(평균 ± 2σ)은 유지하고, '기준 구간 최댓값을 넘은 상태가 3회 연속'이면 점검 경보를 추가(추정 기준). 2주 운영 후 오경보 수를 보고 재조정.

## 우리 설비의 유지보수 단계

지금은 20분 간격 센서 데이터로 이상 후보와 추세를 판정할 수 있으니 **예측 정비(③)의 입구**에 있다. 다음 단계로 가려면 판정 규칙을 경보 등급(관찰·점검·정지)과 담당자에 연결하고, 정비 결과(실제 마모 여부)를 기록해 기준을 다듬어야 한다. 예방 정비 대비 예측 정비는 멀쩡한 부품 교체와 계획 외 정지를 함께 줄이지만, 센서·분석 초기 투자가 필요하다(효과 규모는 추정).

## 검토 기록

- 노이즈를 추세로 본 곳: 없음(설비A 12:40은 노이즈로 분류).
- 단위: 단위혼재 {len(fixes)}행을 ℃·mm/s·bar로 환산한 `sensor_clean.csv`만 사용.
- '추정' 표기: 원인·개선 기준·효과 문장에 모두 표기.
"""
(OUT / "report.md").write_text(report, encoding="utf-8")

# ───────────── 대시보드 index.html ─────────────
def chart(eq, col, label, unit):
    """평상 범위 띠 + 선 + 이상 후보 점 + 상승 시작 세로선을 그린 SVG."""
    pts = series[(eq, col)]
    m, s, lo, hi = ranges[(eq, col)]
    vals = [v for _, v in pts]
    ymin, ymax = min(vals + [lo]), max(vals + [hi])
    pad = (ymax - ymin) * 0.08 or 1
    ymin, ymax = ymin - pad, ymax + pad
    W, H, L, R, T, B = 520, 220, 44, 12, 14, 26
    x = lambda i: L + i * (W - L - R) / (len(pts) - 1)
    y = lambda v: T + (ymax - v) * (H - T - B) / (ymax - ymin)
    path = " ".join(f"{'M' if i == 0 else 'L'}{x(i):.1f},{y(v):.1f}" for i, (_, v) in enumerate(pts))
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{html.escape(eq)} {label} 추이">',
           f'<rect x="{L}" y="{y(hi):.1f}" width="{W - L - R}" height="{y(lo) - y(hi):.1f}" class="band"/>',
           f'<line x1="{L}" x2="{W - R}" y1="{y(hi):.1f}" y2="{y(hi):.1f}" class="limit"/>']
    for v in (ymin + pad, (ymin + ymax) / 2, ymax - pad):
        out.append(f'<text x="{L - 6}" y="{y(v) + 4:.1f}" class="tick" text-anchor="end">{v:.1f}</text>')
    for i in range(0, len(pts), 6):
        out.append(f'<text x="{x(i):.1f}" y="{H - 8}" class="tick" text-anchor="middle">{pts[i][0]}</text>')
    start = starts[(eq, col)][0]
    if start:
        i = [t for t, _ in pts].index(start)
        out.append(f'<line x1="{x(i):.1f}" x2="{x(i):.1f}" y1="{T}" y2="{H - B}" class="start"/>')
        out.append(f'<text x="{x(i) - 4:.1f}" y="{T + 10}" class="start-label" text-anchor="end">상승 시작 {start}</text>')
    out.append(f'<path d="{path}" class="line"/>')
    for i, (t, v) in enumerate(pts):
        if not lo <= v <= hi:
            out.append(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="5" class="dot"><title>{t} {v:g} {unit}</title></circle>')
    out.append("</svg>")
    return (f'<figure class="card chart"><figcaption><b>{html.escape(eq)}</b> {label} ({unit}) '
            f'<span class="muted">평상 범위 {lo:.2f}~{hi:.2f}</span></figcaption>{"".join(out)}</figure>')


def bars():
    mx = max(p["배수"] for p in pilot)
    rows = []
    for p in pilot:
        w = p["배수"] / mx * 100
        cls = "bar best" if p is best else "bar"
        rows.append(f'<div class="bar-row"><span class="bar-name">{p["공정"]}</span>'
                    f'<span class="bar-track"><span class="{cls}" style="width:{w:.1f}%"></span></span>'
                    f'<span class="bar-val">{p["배수"]:.2f}배</span></div>')
    return "".join(rows)


eq_names = {short(r["설비"]): r["설비"] for r in clean}
judg_rows = "".join(
    f"<tr><td>{a['설비']}</td><td>{a['변수'].split('(')[0]}</td><td>{a['시각']}</td><td>{a['값']:g}</td>"
    f"<td>{a['하한']:.2f}~{a['상한']:.2f}</td><td><span class='tag {'warn' if a['판정'] == '추세' else ''}'>{a['판정']}</span></td></tr>"
    for a in anomalies)
net_rows = "".join(f"<tr><td>{int(r * 100)}%</td><td>{s:,.0f}</td><td>{n:,.0f}</td><td>{pb:.1f}년</td></tr>" for r, (s, n, pb) in net.items())
charts = "".join(chart(eq, col, lab, unit) for eq in ("설비A", "설비B") for col, lab, unit in VARS[:2])

page = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>예지보전 대시보드</title>
<style>
:root {{ --bg:#f7f7f5; --card:#fff; --ink:#1d1d1b; --muted:#6b6b66; --line:#2f5d8a; --band:#2f5d8a1f; --limit:#2f5d8a80;
  --dot:#c0392b; --start:#b7791f; --border:#e3e2dd; --best:#2f5d8a; --bar:#b8c4cf; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#161615; --card:#21211f; --ink:#ecebe6; --muted:#a3a29c;
  --line:#7fb0e0; --band:#7fb0e026; --limit:#7fb0e080; --dot:#ff6b5b; --start:#e3a84a; --border:#33332f; --best:#7fb0e0; --bar:#4a5560; }} }}
:root[data-theme="dark"] {{ --bg:#161615; --card:#21211f; --ink:#ecebe6; --muted:#a3a29c; --line:#7fb0e0; --band:#7fb0e026;
  --limit:#7fb0e080; --dot:#ff6b5b; --start:#e3a84a; --border:#33332f; --best:#7fb0e0; --bar:#4a5560; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:15px/1.55 system-ui,-apple-system,"Malgun Gothic","Apple SD Gothic Neo",sans-serif; }}
main {{ max-width:1080px; margin:0 auto; padding:24px 16px 48px; }}
h1 {{ font-size:1.5rem; margin:0 0 4px; }} h2 {{ font-size:1.1rem; margin:28px 0 10px; }}
.muted {{ color:var(--muted); font-weight:400; }} .note {{ display:inline-block; font-size:.8rem; padding:2px 8px; border:1px solid var(--border); border-radius:99px; color:var(--muted); }}
.summary {{ font-size:1.05rem; margin:10px 0 0; }}
.grid {{ display:grid; gap:12px; grid-template-columns:repeat(auto-fit,minmax(min(100%,240px),1fr)); }}
.charts {{ grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr)); }}
.card {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:14px; margin:0; min-width:0; }}
.kpi b {{ display:block; font-size:1.6rem; }} .kpi span {{ color:var(--muted); font-size:.85rem; }}
figcaption {{ margin-bottom:6px; }} svg {{ width:100%; height:auto; display:block; }}
.band {{ fill:var(--band); }} .limit {{ stroke:var(--limit); stroke-dasharray:4 3; }} .line {{ fill:none; stroke:var(--line); stroke-width:2; }}
.dot {{ fill:var(--dot); }} .start {{ stroke:var(--start); stroke-width:1.5; stroke-dasharray:3 3; }} .start-label {{ fill:var(--start); font-size:11px; }}
.tick {{ fill:var(--muted); font-size:11px; }}
.table-wrap {{ overflow-x:auto; }} table {{ width:100%; border-collapse:collapse; font-size:.9rem; }}
th,td {{ text-align:left; padding:6px 8px; border-bottom:1px solid var(--border); }} th {{ color:var(--muted); font-weight:500; }}
.tag {{ padding:1px 8px; border-radius:99px; border:1px solid var(--border); }} .tag.warn {{ border-color:var(--dot); color:var(--dot); }}
.bar-row {{ display:grid; grid-template-columns:3.5em 1fr 4.5em; gap:8px; align-items:center; margin:6px 0; }}
.bar-track {{ background:var(--bg); border-radius:4px; height:14px; }} .bar {{ display:block; height:100%; border-radius:4px; background:var(--bar); }}
.bar.best {{ background:var(--best); }} .bar-val {{ text-align:right; font-variant-numeric:tabular-nums; }}
ol,ul {{ padding-left:1.2em; margin:6px 0; }} footer {{ margin-top:32px; font-size:.85rem; color:var(--muted); }}
a {{ color:var(--line); word-break:break-all; }}
</style></head>
<body><main>
<span class="note">실습용 가상 데이터</span>
<h1>예지보전 대시보드 <span class="muted">— 프레스 메인모터 · 차체 용접로봇 감속기</span></h1>
<p class="summary">이상 후보 {len(anomalies)}건 중 설비B 감속기의 진동·온도가 <b>추세</b>로 판정됐다. 진동 상승 시작 <b>{b_vib_start}</b> 기준 다음 휴무일 계획 정비를 권고하고, 예지보전 파일럿은 <b>{best['공정']}</b>({best['배수']:.2f}배)부터 시작한다.</p>

<h2>한눈에</h2>
<div class="grid">
 <div class="card kpi"><b>{len(anomalies)}건</b><span>이상 후보 (평균 ± 2σ 밖)</span></div>
 <div class="card kpi"><b>{b_vib_start}</b><span>설비B 진동 상승 시작 = 정비 필요 시점</span></div>
 <div class="card kpi"><b>{b_temp_start}</b><span>설비B 온도 범위 안 상승 시작 (추정)</span></div>
 <div class="card kpi"><b>{best['공정']} {best['배수']:.2f}배</b><span>파일럿 1순위 (연간 정지손실 ÷ 초기 투자)</span></div>
</div>

<h2>센서 추이 <span class="muted">띠 = 평상 범위, 빨간 점 = 이상 후보, 세로 점선 = 상승 시작</span></h2>
<div class="grid charts">{charts}</div>

<h2>노이즈 vs 추세 판정</h2>
<div class="card table-wrap"><table><thead><tr><th>설비</th><th>변수</th><th>시각</th><th>값</th><th>평상 범위</th><th>판정</th></tr></thead><tbody>{judg_rows}</tbody></table></div>

<h2>예지보전 보고서 요약</h2>
<div class="grid">
 <div class="card"><b>정비 권고</b><ul><li>설비B: 진동 {b_vib_start}부터 연속 상승, 온도 {b_temp_start}부터 상승 → 다음 휴무일 윤활·베어링 점검(원인 추정)</li><li>설비A: 12:40 진동은 노이즈 — 관찰, 반복 시 센서·배선 점검</li></ul></div>
 <div class="card"><b>개선안 (추정 기준)</b><ul><li>설비B 측정 주기 20분 → 5분</li><li>'기준 구간 최댓값 초과 3회 연속' 점검 경보 추가, 2주 운영 후 재조정</li></ul></div>
</div>

<h2>파일럿 공정 선정 <span class="muted">연간 정지손실 ÷ 초기 투자</span></h2>
<div class="grid">
 <div class="card">{bars()}<p class="muted">시간당 손실은 조립이 가장 크지만 고장이 드물어 배수는 {assembly['배수']:.2f}배.</p></div>
 <div class="card table-wrap"><b>{best['공정']} 순효과 (보수적 추정, 만원)</b>
  <table><thead><tr><th>절감률</th><th>연간 절감</th><th>1년 순효과</th><th>회수</th></tr></thead><tbody>{net_rows}</tbody></table>
  <p class="muted">부품비 절감은 0으로 두었다. 절감률은 가정값.</p></div>
</div>

<footer>
데이터: KMA 자동차특화 AI 융합 전문가 과정 강의 저장소 <a href="https://github.com/keerhee/kma-auto-genai-3-1">keerhee/kma-auto-genai-3-1</a> <code>data/Day5/</code> — 설비센서·파일럿 가정값은 실습용 가상 데이터.
평상 범위는 설비별 평균 ± 2 × 표본표준편차. 상승 시작 = 첫 4시간 최댓값을 넘은 뒤 다시 내려오지 않는 첫 시각.
만든 방법: Claude Code 수업 <code>learn-auto-pdm</code>.
</footer>
</main></body></html>
"""
Path("index.html").write_text(page, encoding="utf-8")

Path("expected.json").write_text(json.dumps({"values": expected}, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"완료: 이상 후보 {len(anomalies)}건, 단위 정리 {len(fixes)}행, 파일럿 1순위 {best['공정']} {best['배수']:.2f}배")
