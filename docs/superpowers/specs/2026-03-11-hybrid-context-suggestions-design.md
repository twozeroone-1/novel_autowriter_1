# 하이브리드 Context Suggestion 설계

**목표**

`STATE`와 `PREVIOUS SUMMARY`를 각 모드의 성격에 맞게 AI가 제안하거나 자동 반영하도록 통일한다. 대화형 탭에서는 사용자가 최종 승인하고, 무인 자동화 탭에서는 자동 반영을 허용하되 백업과 로그를 남긴다.

**핵심 원칙**

- `STATE`는 다음 회차를 위한 현재 상황판이다.
- `PREVIOUS SUMMARY`는 누적 줄거리 기록이다.
- 둘 다 AI가 다룰 수 있지만, 반영 시점과 저장 권한은 모드에 따라 달라야 한다.

## 모드별 정책

### 1. 작품 설정 관리

대상: [ui/workspace.py](/c:/Users/W/novel_autowriter_1/ui/workspace.py)

- `STATE`
  - AI 초안 생성 버튼 제공
  - 자동 저장 금지
- `PREVIOUS SUMMARY`
  - AI 초안 생성 버튼 제공
  - 자동 저장 금지

이 탭은 설계/편집용이므로 “제안”만 제공한다.

### 2. 원고 검수

대상: [ui/chapters.py](/c:/Users/W/novel_autowriter_1/ui/chapters.py) 의 검수 탭

- 검수 리포트 단계에서는 `STATE`/`PREVIOUS SUMMARY`를 건드리지 않는다.
- 수정본이 생성된 뒤, 사용자가 이 수정본을 최신 회차로 반영하려는 순간에만 AI 제안을 보여준다.
- 사용자가 승인할 때만 저장한다.

검수 대상이 과거 원고일 수도 있으므로, 무조건 현재 프로젝트 상태를 덮어쓰면 안 된다.

### 3. 반자동 연재 모드

대상: [ui/chapters.py](/c:/Users/W/novel_autowriter_1/ui/chapters.py) 의 반자동 탭

- 파이프라인 종료 후 REVIEW 단계에서
  - `AI 제안 STATE`
  - `AI 제안 PREVIOUS SUMMARY`
  를 함께 보여준다.
- 사용자가 수정 후 저장한다.
- 저장 전까지 `config.json`은 변경하지 않는다.

### 4. 자동화 연재 모드

대상: [ui/automation.py](/c:/Users/W/novel_autowriter_1/ui/automation.py), 자동화 실행 경로

- 기본 정책은 자동 반영이다.
- 자동 반영 전 이전 `state`/`summary_of_previous`를 백업한다.
- 실행 기록에 다음을 남긴다.
  - state updated
  - summary updated
  - partial failure
- 둘 중 하나가 실패하면 부분 실패로 기록하고, 실패한 필드는 기존 값을 유지한다.

## 구현 단위

### 공통 개념

모든 모드가 같은 규칙을 쓰려면, “AI 제안 생성”과 “최종 반영”을 분리해야 한다.

- 제안 생성
  - `state_suggestion`
  - `summary_suggestion`
- 반영
  - interactive: 사용자 승인 후 저장
  - automation: 정책에 따라 자동 저장

### 필요한 공통 함수

별도 유틸 또는 기존 클래스 내부 메서드 형태로 아래 책임이 필요하다.

- 최종 원고 기준 `STATE` 제안 생성
- 최종 원고 기준 `PREVIOUS SUMMARY` 갱신안 생성
- interactive 저장값 선택
- automation 반영 전 백업 생성
- automation 반영 결과 로그 작성

## 오류 처리

- `STATE` 제안 실패
  - 대화형 모드: 경고 표시, 기존 `state` 유지
  - 자동화 모드: 기존 `state` 유지, partial failure 기록
- `PREVIOUS SUMMARY` 제안 실패
  - 대화형 모드: 경고 표시, 기존 `summary` 유지
  - 자동화 모드: 기존 `summary` 유지, partial failure 기록

한 필드 실패 때문에 회차 저장 자체를 실패로 돌리지 않는다.

## 범위 제외

이번 변경에서 제외한다.

- diff 뷰
- 되돌리기 UI
- 별도 히스토리 브라우저
- 과거 원고 자동 최신화 판단의 고도화

이번 목표는 각 모드의 저장 권한과 AI 제안 위치를 일관되게 만드는 것이다.
