# 반자동 연재 모드 State 제안 UI 설계

**목표**

반자동 연재 모드의 REVIEW 단계에서 `CURRENT STATE`를 사용자가 맨손으로 다시 쓰게 하지 않고, 방금 생성된 회차를 기준으로 AI가 자동 정리한 `state` 제안안을 먼저 보여준다. 사용자는 이 제안안을 검토하고 수정한 뒤 최종 저장한다.

**배경**

현재 반자동 연재 모드에서는 초안 생성, 검토, 수정, 저장, `summary_of_previous` 갱신까지 한 번에 수행된다. 하지만 REVIEW 단계의 `CURRENT STATE` 입력창은 기존 `config["state"]` 값을 그대로 다시 편집하게 되어 있어, 실제 사용 경험은 반자동이 아니라 “요약만 자동, state는 수동”에 가깝다.

반면 코드베이스에는 이미 상태 요약용 LLM 기능이 있다. [core/generator.py](/c:/Users/W/novel_autowriter_1/core/generator.py) 의 `summarize_state()`는 원고를 바탕으로 다음 회차용 상태를 요약하는 책임을 갖고 있어, 반자동 파이프라인에 자연스럽게 편입할 수 있다.

## 접근 방식

### 옵션 1: 현행 유지

REVIEW 단계에서 `CURRENT STATE`를 계속 수동 입력으로 둔다.

장점:
- 구현이 가장 단순하다.
- AI 오요약이 저장될 위험이 없다.

단점:
- 반자동 모드의 체감 자동화가 낮다.
- 사용자가 직전 회차를 다시 읽고 state를 직접 정리해야 한다.
- `summary_of_previous`는 자동 제안인데 `state`만 수동이라 UX 결이 맞지 않는다.

### 옵션 2: AI 제안 + 사용자 승인

반자동 실행 후 `state` 제안안을 AI가 생성해서 REVIEW 단계에 표시하고, 사용자가 수정 후 저장한다.

장점:
- 자동화 체감과 통제권을 동시에 확보한다.
- 다음 회차 품질에 직접 연결되는 `state`를 사용자가 마지막으로 확인할 수 있다.
- 기존 파이프라인과 가장 자연스럽게 맞물린다.

단점:
- 결과 객체와 UI에 필드가 조금 늘어난다.
- 상태 제안 실패 시 fallback 처리 문구가 필요하다.

### 옵션 3: AI 자동 덮어쓰기

반자동 실행이 끝나면 `config["state"]`를 바로 AI 결과로 덮어쓴다.

장점:
- 사용자 입력이 거의 필요 없다.

단점:
- 잘못된 state가 조용히 누적될 수 있다.
- 생성 품질 문제가 다음 회차 전체에 전이된다.
- 반자동 모드의 신뢰성이 떨어진다.

## 추천안

옵션 2를 채택한다. 반자동 모드의 핵심은 “AI가 먼저 처리하고, 사용자가 최종 승인한다”는 것이다. `state`는 다음 회차 생성 품질을 좌우하는 핵심 문맥이므로 자동 저장보다 제안안 표시가 더 안전하다.

## UX 설계

반자동 연재 모드 REVIEW 단계에서 다음 구조로 보여준다.

1. `AI 제안 STATE`
- 방금 생성된 최종 원고를 바탕으로 정리한 새 `state` 제안안
- 읽기 전용 표시 또는 보조 텍스트 영역으로 노출

2. `CURRENT STATE 업데이트`
- 사용자가 실제로 수정하고 저장하는 편집창
- 기본값은 `AI 제안 STATE`를 우선 사용한다
- AI 제안 생성이 실패한 경우에만 기존 `config["state"]`를 기본값으로 사용한다

3. `PREVIOUS SUMMARY`
- 지금처럼 자동 갱신 결과를 검토 후 수정 가능하게 유지한다

필요하면 보조 버튼을 나중에 추가할 수 있지만, 1차 구현은 단순하게 간다. 핵심은 “AI 제안안이 분명히 보인다”와 “최종 저장은 편집창 기준이다” 두 가지다.

## 데이터 흐름

현재 [core/automator.py](/c:/Users/W/novel_autowriter_1/core/automator.py) 의 `run_single_cycle()`은 다음 결과를 반환한다.

- `draft`
- `draft_path`
- `review_report`
- `review_report_path`
- `revised_draft`
- `saved_path`
- `new_summary`
- `summary_error`

여기에 아래 필드를 추가한다.

- `new_state`
- `state_error`

동작 순서:

1. 초안 생성
2. 자동 검토
3. 자동 수정
4. 최종 원고 저장
5. `summary_of_previous` 자동 갱신
6. `state` 자동 요약 생성

`state` 자동 요약은 저장 직전이 아니라 REVIEW 표시용 결과다. 사용자가 최종 저장 버튼을 누르기 전까지 `config.json`에는 반영하지 않는다.

## 저장 규칙

REVIEW 단계 진입 직후에는 설정 파일을 건드리지 않는다.

사용자가 `상태 저장` 버튼을 누를 때만:
- `config["state"] = 최종 편집값`
- `config["summary_of_previous"] = 최종 편집값`

즉, `new_state`와 `new_summary`는 제안안이지 저장 완료 상태가 아니다.

## 오류 처리

`state` 제안 생성이 실패하면:
- 경고 문구를 보여준다.
- `CURRENT STATE 업데이트` 편집창 기본값은 기존 `config["state"]`를 사용한다.
- `PREVIOUS SUMMARY` 흐름은 기존대로 유지한다.

이 방식이면 LLM 호출 하나가 실패해도 반자동 파이프라인 전체가 멈추지 않는다.

## 테스트 방향

다음 수준에서 검증한다.

1. `Automator.run_single_cycle()`
- `summarize_state()` 성공 시 `new_state`가 결과에 포함되는지
- 실패 시 `state_error`만 설정되고 나머지 결과는 유지되는지

2. REVIEW UI
- AI 제안 state가 있으면 편집 기본값으로 들어가는지
- AI 제안 state가 없으면 기존 config state를 기본값으로 쓰는지
- 경고 문구 조건이 올바른지

3. 회귀 방지
- 기존 `summary_of_previous` 검토/저장 흐름이 깨지지 않는지

## 범위 제외

이번 변경에서는 다음을 하지 않는다.

- `state` 자동 제안의 diff 뷰
- “기존 state 복원” 버튼
- 별도 히스토리 저장
- 완전 자동 덮어쓰기

이 변경의 목적은 반자동 모드의 가장 큰 UX 공백을 메우는 것이다.
