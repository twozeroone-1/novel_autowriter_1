# Gemini CLI Backend Design

**Date:** 2026-03-11

## Goal

`Gemini API`와 사용자가 별도로 OAuth 로그인해 둔 `Gemini CLI`를 같은 앱에서 함께 지원한다.  
사용자는 앱 전체 기본 백엔드를 `auto`, `api`, `cli` 중에서 고를 수 있고, `auto`에서는 `Gemini CLI`를 우선 사용하되 사용할 수 없으면 기존 `Gemini API`로 자동 폴백한다.

이 설계의 1차 목표는 새로운 채팅 UI를 만드는 것이 아니라, 현재 앱의 생성/검수/기획 기능이 공통 LLM 진입점 뒤에서 `Gemini CLI`를 선택적으로 사용할 수 있게 만드는 것이다.

## Scope

### In scope

- 앱 전체 LLM 백엔드 설정 추가: `auto`, `api`, `cli`
- `Gemini CLI` 실행 가능 여부와 간단한 연결 상태 표시
- `Generator`, `Reviewer`, `Planner`가 공통 LLM 진입점을 통해 `Gemini CLI`를 사용할 수 있도록 변경
- `auto` 모드에서 `CLI -> API` 자동 폴백
- Windows에서 `gemini.cmd` 호출 지원
- `system_instruction`을 CLI 호출에서도 동작하게 만드는 프롬프트 조합 규칙
- 테스트 가능한 백엔드 추상화 계층 도입

### Out of scope

- 새 대시보드 채팅 탭 추가
- Gemini CLI의 내부 OAuth 토큰 파일을 직접 읽거나 수정하는 기능
- 기능별 별도 백엔드 오버라이드 UI
- CLI의 도구 사용 능력을 앱 기능으로 노출하는 것

## Current Constraints

- 현재 앱의 LLM 호출은 사실상 [core/llm.py](/c:/Users/W/novel_autowriter_1/core/llm.py)에 집중되어 있고, [core/generator.py](/c:/Users/W/novel_autowriter_1/core/generator.py), [core/reviewer.py](/c:/Users/W/novel_autowriter_1/core/reviewer.py), [core/planner.py](/c:/Users/W/novel_autowriter_1/core/planner.py)가 그 함수를 사용한다.
- UI 설정은 프로젝트별 설정과 앱 전체 설정이 섞여 있는데, API 키/모델은 현재 사이드바에서 `.env`와 런타임 환경 변수로 관리한다.
- 이 구조상 `Gemini CLI`를 기능별로 따로 붙이는 것보다 공통 백엔드 계층을 두는 편이 안전하다.
- Windows 환경에서는 `gemini.ps1`이 실행 정책에 막힐 수 있으므로 `gemini.cmd`를 우선 사용해야 한다.
- `gemini --help` 기준으로 CLI는 one-shot 호출과 모델 선택을 지원하지만, 별도 `system instruction` 플래그는 드러나지 않는다.

## Recommended Architecture

### 1. 공통 백엔드 추상화 계층

새 모듈 `core/llm_backend.py`를 추가하고 아래 역할을 분리한다.

- `LlmBackendMode`: `auto`, `api`, `cli`
- `LlmRequest`: `prompt`, `system_instruction`, `temperature`, `model_name`
- `LlmBackendResult`: `text`, `backend_used`, `diagnostics`
- `GeminiApiBackend`: 기존 `google-genai` 기반 호출 담당
- `GeminiCliBackend`: 로컬 `gemini` 실행 파일 기반 호출 담당
- `resolve_backend_mode()`: UI/환경 변수 값을 읽어 실제 모드를 정함
- `probe_gemini_cli()`: 실행 파일 존재 여부와 최소 상태 정보 확인

기존 [core/llm.py](/c:/Users/W/novel_autowriter_1/core/llm.py)는 외부 공개 진입점으로 남기되, 내부적으로는 새 백엔드 계층을 호출하는 얇은 파사드로 바꾼다.

### 2. CLI 호출 방식

`GeminiCliBackend`는 공식 Gemini CLI 프로세스를 subprocess로 실행한다.

- Windows: `gemini.cmd`
- macOS/Linux: `gemini`
- 실행은 one-shot 모드 사용
- 모델명은 현재 앱 설정의 `GEMINI_MODEL`을 그대로 전달
- 작업 디렉터리는 임시 디렉터리로 분리해, 앱 소스 트리와 파일 도구가 섞이지 않게 함

CLI에 별도 `system instruction` 인자가 없으므로, 호출 시 프롬프트를 아래처럼 합성한다.

1. `system_instruction`이 있으면 상단에 시스템 역할 블록 삽입
2. 그 아래에 실제 사용자 프롬프트 본문 삽입
3. 구조화 응답이 필요한 기능은 기존처럼 응답 형식을 프롬프트에서 엄격하게 지정

즉, API와 CLI가 완전히 같은 wire format을 쓰지는 않지만, 앱 입장에서는 같은 `generate_text()` 계약을 유지한다.

### 3. 자동 우선순위 선택

앱 전체 기본값은 `auto`로 둔다.

- `auto`: `CLI`가 실행 가능하고 호출이 성공하면 `CLI` 사용
- `auto`: `CLI`가 없거나 인증/실행에 실패하면 `API`로 폴백
- `cli`: `CLI`만 사용, 실패 시 즉시 오류
- `api`: 기존 API만 사용

이렇게 하면 사용자는 평소에는 `auto`를 써도 되고, 문제를 분리하고 싶을 때만 `api` 또는 `cli`를 강제로 선택할 수 있다.

## UI Design

사이드바의 `API / 모델 설정` 섹션에 앱 전체 LLM 백엔드 설정을 추가한다.

표시 항목:

- `LLM 백엔드`: `auto`, `api`, `cli`
- `Gemini CLI 상태`: `설치됨`, `설치 안 됨`, `테스트 필요`, `호출 실패`
- `Gemini CLI 경로`: 자동 감지된 실행 파일 경로
- `CLI 연결 테스트` 버튼

설정 저장 위치는 기존 모델 설정과 같은 계열로 맞춘다.

- `.env` 키 예시: `GEMINI_BACKEND=auto`
- 보안 저장이 필요한 비밀은 아니므로 keyring 대상은 아님

UI 원칙:

- 백엔드 설정은 앱 전체 기본값 하나만 둔다
- 기능별 세부 오버라이드는 1차 범위에서 제외
- 상태 표시는 자동 테스트하지 않고, 명시적 `연결 테스트` 버튼으로만 수행한다

자동 테스트를 매번 하지 않는 이유는:

- Streamlit rerun 때마다 CLI를 실행하면 느리다
- 인증 실패/네트워크 실패가 UI 전체를 시끄럽게 만든다
- 사용자가 의도적으로 API만 쓰고 싶을 수도 있다

## Data Flow

### API mode

1. UI가 `GEMINI_BACKEND=api`를 설정
2. `generate_text()`가 `GeminiApiBackend` 호출
3. 기존과 동일하게 `google-genai`로 응답 수신

### CLI mode

1. UI가 `GEMINI_BACKEND=cli`를 설정
2. `generate_text()`가 `GeminiCliBackend` 호출
3. CLI adapter가 프롬프트를 조합하고 subprocess 실행
4. stdout 텍스트를 읽어 정리한 뒤 문자열 반환

### Auto mode

1. `GeminiCliBackend` 호출 시도
2. 실행 파일 없음, 인증 실패, 프로세스 실패, 타임아웃이면 진단 정보 축적
3. `GeminiApiBackend` 호출 시도
4. 성공 시 최종 결과와 `backend_used=api` 반환
5. 둘 다 실패하면 합성 오류 반환

## Error Handling

CLI는 API와 실패 양상이 다르므로 분류가 필요하다.

### CLI 쪽에서 재분류할 오류

- 실행 파일 없음
- PowerShell 정책 문제
- 프로세스 exit code 실패
- stdout 비어 있음
- 타임아웃
- 인증/세션 없음으로 보이는 메시지

분류 결과는 내부적으로 `CliUnavailableError`, `CliAuthError`, `CliInvocationError` 같은 타입으로 나눈다.

`auto`에서는 아래만 API 폴백 대상으로 본다.

- CLI 미설치
- CLI 인증 실패
- CLI 실행 실패

반대로 아래는 즉시 실패시킨다.

- 메모리 부족
- 내부 파서 버그
- 호출 계약 위반

## Prompt and Output Strategy

CLI 1차 버전은 undocumented JSON event schema에 의존하지 않는다.

- 우선순위는 `stdout`의 최종 텍스트를 그대로 받아 기존처럼 사용
- JSON이 필요한 기능은 현재 `_extract_first_json_value()` 기반 파서를 그대로 재사용
- 필요하면 이후 2차에서 `--output-format json` 전용 파서를 추가

이 선택의 이유:

- 현재 CLI 버전 변화에 덜 민감하다
- 기존 생성/기획/등장인물 추출 파서와 잘 맞는다
- 회차 생성은 본질적으로 텍스트 생성이므로 text mode가 충분하다

## Testing Strategy

### Unit tests

- 백엔드 모드 해석 테스트
- CLI 실행 파일 경로 선택 테스트
- `system_instruction` 프롬프트 합성 테스트
- `auto` 모드의 `CLI -> API` 폴백 테스트
- `cli` 강제 모드의 실패 전파 테스트
- CLI 상태 프로브 테스트

### Integration-style tests

- subprocess mocking으로 CLI stdout 반환 시 `Generator/Reviewer/Planner`가 그대로 동작하는지 검증
- `Generator.generate_characters()` 같은 JSON 소비 경로가 CLI 응답 텍스트에서도 파싱되는지 확인

### Manual verification

- Windows 11에서 `gemini.cmd`가 있는 환경
- CLI 미설치 환경
- CLI 설치 + OAuth 인증 안 된 환경
- CLI 설치 + OAuth 인증된 환경
- API 키만 있는 환경
- `auto`, `api`, `cli` 세 모드에서 `[2]`, `[3]`, `[5]`, `[6]` 동작 확인

## Rollout Plan

### Phase 1

- 백엔드 추상화 계층 추가
- 사이드바에 백엔드 선택 및 CLI 상태 표시 추가
- `Generator`, `Reviewer`, `Planner` 전부 공통 `generate_text()`를 통해 새 백엔드 사용
- 테스트 추가

### Phase 2

- CLI 연결 테스트 UX 개선
- `--output-format json` 지원 여부 검토
- 기능별 오버라이드 필요성 재평가

## Risks

- Gemini CLI의 출력 형식이 버전별로 달라질 수 있다
- CLI는 API보다 시작 지연이 더 클 수 있다
- `system_instruction`을 별도 필드가 아닌 프롬프트 합성으로 넣기 때문에 API와 완전히 동일한 거동은 보장되지 않는다
- Windows에서는 `gemini.ps1` 대신 `gemini.cmd` 우회를 반드시 고정해야 한다

## Decision Summary

- 새 채팅 UI는 만들지 않는다
- `Gemini CLI`는 공식 CLI 프로세스를 직접 실행하는 방식으로만 붙인다
- 앱 전체 기본 백엔드는 `auto`
- `auto`는 `CLI 우선, 실패 시 API`
- 구현은 기능별 패치가 아니라 공통 백엔드 추상화 계층으로 진행한다
