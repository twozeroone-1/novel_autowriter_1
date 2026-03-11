# Automated Serialization Mode Design

**Date:** 2026-03-11

## Goal

기존 `[4] 반자동 연재 모드`와 별도로 `[7] 자동화 연재 모드`를 추가한다.

이 모드는 Streamlit 서버 프로세스가 살아 있는 동안 프로젝트별 작업 큐와 예약 규칙을 기준으로 회차를 자동 실행한다. 실행 범위는 `초안 생성 -> 검수 -> 수정 -> 저장 -> STATE 갱신 -> PREVIOUS SUMMARY 갱신`까지 전부 포함하며, 브라우저 탭이 닫혀 있어도 `streamlit run` 프로세스가 살아 있으면 계속 동작한다.

## Scope

### In scope

- `[7] 자동화 연재 모드` 탭 추가
- 프로젝트별 자동화 설정 저장
- 두 가지 스케줄 타입 지원
  - 매일/요일별 특정 시각
  - N시간마다 반복
- 작업 큐 기반 실행
  - `title`, `instruction`, `target_length`
- 서버 프로세스 기준 예약 실행
- 자동화 실행 상태/최근 이력 표시
- 실패 시 즉시 1회 재시도 후 `paused`
- `STATE`, `PREVIOUS SUMMARY`까지 완전 자동 갱신

### Out of scope

- OS 레벨 예약 작업 등록
- 앱 프로세스가 꺼져 있어도 실행되는 백그라운드 서비스
- 큐가 비었을 때 AI가 다음 작업을 스스로 생성하는 기능
- 여러 프로젝트를 동시에 병렬 실행하는 오케스트레이션

## Current Constraints

- 현재 [core/automator.py](/c:/Users/W/novel_autowriter_1/core/automator.py)는 단일 회차 자동 실행만 제공한다.
- 현재 [ui/chapters.py](/c:/Users/W/novel_autowriter_1/ui/chapters.py)의 `[4] 반자동 연재 모드`는 사용자가 버튼을 눌러야만 실행된다.
- 앱은 Streamlit 기반이므로 “항상 돌아가는 백그라운드 워커” 대신, 서버 프로세스가 살아 있는 동안 주기적으로 상태를 검사하는 폴링형 런타임이 더 현실적이다.
- Streamlit 세션 상태만으로는 브라우저 탭 종료 뒤 예약 실행을 유지할 수 없으므로, 자동화 상태는 파일에 저장되어야 한다.

## Recommended Architecture

### 1. 탭 분리

`[4] 반자동 연재 모드`는 유지한다. 이 탭은 “지금 1회 실행” 용도로 남긴다.

새 `[7] 자동화 연재 모드`는 운영 패널 역할을 한다.

- 스케줄 설정
- 작업 큐
- 런타임 상태
- 최근 실행 이력

이 분리를 통해 사용자는 “수동 실행”과 “예약 운영”을 헷갈리지 않게 된다.

### 2. 프로젝트별 자동화 저장소

프로젝트별 자동화 상태는 별도 디렉터리로 분리한다.

예시:

- `data/projects/<project>/automation/config.json`
- `data/projects/<project>/automation/queue.json`
- `data/projects/<project>/automation/runtime.json`
- `data/projects/<project>/automation/history.jsonl`

각 파일 책임:

- `config.json`
  - 활성 여부
  - 스케줄 규칙
  - retry 정책
  - poll interval
- `queue.json`
  - 대기 중/실패/완료 작업 목록
  - 순서 정보
- `runtime.json`
  - 현재 상태: `idle`, `running`, `paused`
  - 현재 실행 중 작업 id
  - 마지막 실행 시각
  - 마지막 성공/실패 메시지
  - 다음 실행 예정 시각
- `history.jsonl`
  - 각 자동 실행의 결과 로그

### 3. 자동화 런타임 서비스

새 모듈 `core/automation_runtime.py`를 둔다.

이 서비스는 다음 역할만 담당한다.

- 현재 시각 기준 스케줄 도래 여부 판정
- 현재 프로젝트의 런타임 상태 확인
- 실행 가능하면 큐의 다음 작업을 하나 꺼냄
- `Automator.run_single_cycle()` 호출
- 성공/실패 결과를 저장소에 기록

Streamlit 서버 안에서 이 서비스는 “UI 렌더 때마다 조건 확인”이 아니라, 최소 폴링 간격을 둔 가드로 호출된다. 예를 들면 최근 검사 시각이 30초 이내면 다시 검사하지 않는다. 이렇게 해야 리렌더마다 불필요한 디스크 I/O와 중복 실행을 막을 수 있다.

### 4. 작업 큐 방식

큐 항목 예시:

```json
{
  "id": "job_20260311_001",
  "title": "12화 붕괴의 전조",
  "instruction": "주인공이 ...",
  "target_length": 5000,
  "status": "pending",
  "attempt_count": 0,
  "created_at": "2026-03-11T21:00:00+09:00",
  "last_error": ""
}
```

예약 시각이 오면 스케줄러는 큐에서 첫 `pending` 작업 하나만 실행한다.

성공 시:

- 작업 상태를 `done`으로 변경
- `runtime`을 `idle`로 되돌림
- 이력 기록

실패 시:

- 같은 작업을 즉시 1회 재시도
- 또 실패하면 작업 상태를 `failed`
- `runtime` 상태를 `paused`
- `pause_reason`에 실패 원인 기록

이 정책은 무인 실행 중 조용히 실패를 반복하지 않게 해 준다.

### 5. 스케줄 모델

지원하는 스케줄은 두 계층이다.

#### Calendar schedule

- `daily`
  - 예: 매일 21:00
- `weekly`
  - 예: 월/수/금 07:30

#### Interval schedule

- `every_n_hours`
  - 예: 6시간마다
  - 기준점은 마지막 성공 실행 시각 또는 명시적 시작 시각

여러 규칙을 동시에 둘 수는 있지만, 1차 버전에서는 “프로젝트당 활성 규칙 1개”가 가장 안전하다. 규칙 여러 개를 동시에 허용하면 중복 트리거와 큐 소비 충돌 문제가 급격히 늘어난다.

추천 1차 범위:

- 한 프로젝트당 활성 스케줄 1개
- 타입만 `daily`, `weekly`, `interval` 중 하나 선택

## UI Design

`[7] 자동화 연재 모드`는 네 개의 블록으로 구성한다.

### A. 자동화 스케줄

- 자동화 활성화 체크박스
- 스케줄 타입 선택
  - 매일
  - 요일별
  - N시간마다
- 시각 또는 시간 간격 입력
- 저장 버튼

### B. 작업 큐

- 새 작업 추가 폼
  - 회차 제목
  - 지시사항
  - 목표 글자 수
- 큐 목록
  - 순서
  - 상태
  - 재시도 횟수
  - 삭제 / 맨 위로 / 건너뛰기

### C. 런타임 상태

- 현재 상태
  - `idle`
  - `running`
  - `paused`
- 현재 처리 중 작업
- 마지막 실행 시각
- 다음 실행 예정 시각
- 마지막 오류
- 수동 재개 버튼

### D. 최근 실행 이력

- 최근 N회 실행 목록
- 회차 제목
- 시작/종료 시각
- 성공/실패
- 저장 경로
- 실패 메시지

## Data Flow

### 예약 검사

1. 앱이 렌더되거나 주기 검사 훅이 호출됨
2. 현재 프로젝트의 `config`와 `runtime`을 읽음
3. 자동화가 비활성화면 종료
4. `runtime`이 `running`이면 종료
5. `runtime`이 `paused`면 종료
6. 현재 시각이 스케줄 도래 시각이면 큐에서 다음 `pending` 작업 선택

### 작업 실행

1. 선택된 작업을 `running`으로 표시
2. `runtime.current_job_id` 갱신
3. `Automator.run_single_cycle()` 호출
4. 성공 시 결과 경로/요약 갱신 결과를 `history`에 기록
5. 작업 상태를 `done`으로 변경
6. `runtime`을 `idle`로 복귀

### 실패 처리

1. 1차 실패 시 `attempt_count += 1`
2. 즉시 같은 작업 1회 재시도
3. 재시도도 실패하면
   - 작업 상태 `failed`
   - `runtime.status = paused`
   - `runtime.last_error` 기록
   - `history`에 실패 이벤트 기록

## Error Handling

오류는 세 종류로 나눈다.

### 1. 일시적 실행 오류

- CLI/API 일시 실패
- 타임아웃
- 파일 저장 중 일시 오류

이 경우에는 즉시 1회 재시도 후 실패면 중지한다.

### 2. 작업 자체의 오류

- 제목 없음
- 지시사항 비어 있음
- 설정 파일 손상

이 경우 재시도 가치가 낮으므로 첫 실패만으로 `failed + paused` 처리해도 된다.

### 3. 런타임 일관성 오류

- `runtime`은 `running`인데 실제 작업 id가 없음
- `queue`에 같은 id가 중복

이 경우 스케줄러는 실행을 멈추고 관리 화면에서 복구 안내를 보여준다.

## Testing Strategy

### Unit tests

- 스케줄 판정
  - daily
  - weekly
  - interval
- 큐 상태 전이
  - `pending -> running -> done`
  - `pending -> running -> retry -> failed`
- paused 상태에서 추가 실행이 막히는지
- 런타임 복구

### Integration-style tests

- fake `Automator`로 성공/실패 시나리오 실행
- 자동 실행 후 `STATE`, `PREVIOUS SUMMARY`까지 갱신 기록 확인
- history 기록 생성 확인

### UI tests

- `[7]` 탭 렌더
- 스케줄 저장
- 큐 추가/삭제
- paused 배지 표시
- 최근 실행 이력 표시

## Rollout Plan

### Phase 1

- 자동화 저장소/스케줄 판정/큐 실행 엔진 추가
- 테스트 추가

### Phase 2

- `[7] 자동화 연재 모드` UI 추가
- 상태 표시/이력 표시 연결

### Phase 3

- merged main에서 Playwright smoke
- 실제 CLI/auto 백엔드로 예약 실행 검증

## Risks

- Streamlit은 전통적인 백그라운드 서버 프레임워크가 아니므로 폴링 설계를 보수적으로 해야 한다.
- 브라우저가 없어도 서버 프로세스가 죽으면 예약도 멈춘다.
- 사용자가 같은 프로젝트를 여러 탭에서 열면 중복 실행 가드가 필요하다.
- 긴 자동 실행 중 Streamlit rerun이 겹치지 않게 런타임 잠금 개념이 필요할 수 있다.

## Decision Summary

- `[4] 반자동`은 유지하고 `[7] 자동화 연재 모드`를 새로 만든다.
- 자동화는 작업 큐 방식으로만 간다.
- 브라우저 탭은 닫혀 있어도 되고, `streamlit run` 프로세스가 살아 있으면 예약 실행된다.
- 스케줄 타입은 `daily`, `weekly`, `interval`을 지원한다.
- 실패 정책은 `즉시 1회 재시도 후 paused`다.
- `STATE`, `PREVIOUS SUMMARY` 갱신도 완전 자동 처리한다.
