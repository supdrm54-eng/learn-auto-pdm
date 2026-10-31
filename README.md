# 자동차 예지보전 AI 활용 — learn-auto-pdm

프레스 메인모터와 용접로봇 감속기의 센서 데이터(진동·온도·압력)에서 고장 징후를 읽어 정비 시점과 예지보전 파일럿 공정을 정하고, 결과를 대시보드로 공개하는 3시간 자율학습 수업이다. 수업은 Claude Code 스킬 `/learn-auto-pdm`이 진행한다 (Skills as Curriculum). 이 강의는 supdrm54-eng가 course-forge로 KMA 자동차특화 AI 융합 전문가 과정 5일차(예지보전)를 바탕으로 직접 만들었다.

- **결과 대시보드**: https://supdrm54-eng.github.io/learn-auto-pdm/
- 처음이면 [GUIDE.md](GUIDE.md)부터. 기본 환경은 Claude 데스크톱 앱(Code 탭). VS Code는 GUIDE 부록 B

## 설치 — 한 줄

Claude Code 입력칸에 붙여 넣는다.

```
npx skills add supdrm54-eng/learn-auto-pdm --agent claude-code --global --yes 를 실행해 줘
```

새 세션에서 `/learn-auto-pdm`을 입력하면 수업이 시작된다. Node.js가 없거나 zip을 받았다면 GUIDE.md 2단계대로 설치한다.

## 블록

| Block | 주제 | 끝나면 생기는 것 |
|---|---|---|
| 0 | 준비 | `~/pdm-lab` 작업 폴더와 데이터 4종, `env_check.txt` |
| 1 | 고장은 예고하고 온다 — 데이터 점검 | 도입사례 표, 단위(℉·in/s·psi)를 바로잡은 센서 파일 |
| 2 | 평상 범위 — 설비별 평균 ± 2σ | 평상 범위 표, 이상 후보 4건 |
| 3 | 노이즈인가 추세인가 — 정비 시점 | 판정표, 정비 필요 시점, 대시보드 차트 |
| 4 | 예지보전 보고서 4단 | 현황·원인 추정·정비 시점·개선안 보고서 |
| 5 | 어디부터 할까 — 파일럿 공정 선정 | 공정별 배수·순효과 표, 대시보드 패널 |
| 6 | 배포와 공유 | 공개 대시보드 주소, README, 공유 메시지 |

## 수업 방식

| 구분 | 내용 |
|---|---|
| 목표 — AI Native | AI에게 맡기는 것이 기본인 방식으로 일한다. 기준은 내가 정하고, 계산·차트·보고서는 Claude가 하고, 결과는 내가 확인한다 |
| 방법 — Skills as Curriculum | 스킬이 블록마다 설명 → 실습 → STOP → 확인·퀴즈를 진행한다 |
| 형식 — 자율학습 | 강사 없이 자기 속도로, 판단형 퀴즈 12문항과 정답 수치로 스스로 점검한다 |

## 원본 강의와 데이터 출처

| 자료 | 출처 | 구분 |
|---|---|---|
| 원본 강의 | [keerhee/kma-auto-genai-3-1](https://github.com/keerhee/kma-auto-genai-3-1) `Day5_예지보전/` — Hook 케이스(포스코 등대공장), 인트로, 본 강의 "자동차 예지보전 AI 활용", 보강 실습 | 강의 흐름·용어·실습과제·모범답안을 따름 |
| `Day5_설비센서_50건_가상.csv` | 원본 저장소 `data/Day5/` | 실습용 가상 데이터 |
| `Day5_설비센서_단위혼재_함정_가상.csv` | 원본 저장소 `data/Day5/` | 실습용 가상 데이터 |
| `Day5_공정별_파일럿평가_가정값_가상.csv` | 원본 저장소 `data/Day5/` | 실습용 가정값 |
| `Day5_예지보전_도입사례_실데이터.csv` | 원본 저장소 `data/Day5/` — 각 행의 `출처URL`(파이낸셜뉴스, BMW 그룹 보도자료, Siemens 블로그, 포스코 뉴스룸, Machinery) | 공개 보도 실데이터, 수치는 보도 그대로 |

데이터 상세는 [`.claude/skills/learn-auto-pdm/assets/lab/README.md`](.claude/skills/learn-auto-pdm/assets/lab/README.md). 대시보드의 모든 수치는 정답 스크립트 [`build_pdm.py`](.claude/skills/learn-auto-pdm/assets/answers/build_pdm.py)를 실행한 결과다.

## 개정 이력

| 날짜 | 바뀐 점 |
|---|---|
| 2026-10-31 | 첫 판 — 블록 7개(180분), 퀴즈 12문항, 정답 수치 40개 검증 |
| 2026-10-31 | 배포하며 찾은 4건 반영 — Block 0에서 gh 확인·설치, Block 6에 `gh auth setup-git`·noreply 작성자 주소·일회용 코드 Authorize/만료 안내 ([self_review](forge/self_review.md)) |

## 만든 방법

- `/course-forge`로 만들었다. 제작 기록(원본 요약·커리큘럼·검수 결과)은 [`forge/`](forge/)에 있다.
- 출처: 원본 강의 저장소 https://github.com/keerhee/kma-auto-genai-3-1
