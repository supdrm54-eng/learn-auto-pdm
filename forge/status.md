# status — learn-auto-pdm

| 단계 | 상태 | 날짜 | 메모 |
|---|---|---|---|
| 0 원본 고르기 | 완료 | 2026-10-31 | Day5 예지보전 · 3시간. 정답 메모 수치 전부 직접 계산과 일치 → `forge/brief.md` |
| 1 커리큘럼 | 완료 · 승인 ① (2026-10-31) | 2026-10-31 | `learn-auto-pdm` 확정, 블록 7개 180분 → `forge/curriculum.md` |
| 2 수업 | 완료 | 2026-10-31 | SKILL.md + 블록 7개. 린트 오류 0 · 경고 13(퀴즈 미작성 6, expected 자리표시자 7 — 3·4단계에서 채움) → `forge/qa/lint_stage2.txt`. 공식 문서 URL 11개 열림 확인(ISO 403이라 제외). 4단계 숙제: Block 3 정비 시점 규칙(엄격 연속 상승이면 설비B 온도 시작이 15:40, 범위 안 상승 시작 12:40) 정답 스크립트에서 확정 |
| 3 퀴즈 | 완료 | 2026-10-31 | 블록 1~6 각 2문항, 총 12문항(정답 위치 2·1·3·2·1·3·2·1·3·2·1·3) + `## 과제와 다음`. 린트 오류 0 · 경고 7(expected 자리표시자만) → `forge/qa/lint_stage3.txt`. B6 Q2 수치 직접 검증: 단위 미정리 시 설비B 진동 후보 1건(상한 2.206)으로 줄어듦 → 문항 수정 |
| 4 실습 MVP | 완료 · 승인 ② (2026-10-31) | 2026-10-31 | `assets/lab/` 원본 CSV 4개 + README, `assets/answers/build_pdm.py` → output 9종·`index.html`·`expected.json`(40값). verify_numbers 40/40 일치·본문 40/40, lint 오류 0·경고 0 → `forge/qa/`. 원본 대조 → `forge/qa/source_check.md`. 렌더: Playwright 미설치라 render_check.py 대신 앱 내장 브라우저로 점검 — 콘솔 오류 0, 375px 폭 scrollWidth 375(가로 스크롤 없음), SVG 차트 4·이상 점 4·상승 시작선 2·막대 4. preview.png 없음 |
| 5 학습자 자료 | 완료 | 2026-10-31 | `GUIDE.md` (0 먼저 알아 둘 것 ~ 6 제출물 + 부록 B VS Code, 수업 체험 = Block 3). 수치는 expected.json과 대조해 일치, verify 40/40 · lint 0/0 유지. 매뉴얼 덱은 건너뜀 — 이 PC에 Node·LibreOffice 없음(선택 항목). 2단계 스킬 설치 안내는 6단계에서 정할 저장소 주소 자리 `<만든 사람 GitHub 아이디>`로 둠 |
| 6 배포 | 다음 | | |
| 7 배우기·공유 | 대기 | | |
