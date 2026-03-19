# AI 소설 스튜디오

AI의 도움을 받아 소설 설정을 정리하고, 회차를 만들고, 검수까지 할 수 있는 프로그램입니다.

이 문서는 두 부분으로 나뉩니다.

- 위쪽: 처음 쓰는 분을 위한 아주 쉬운 설치/실행 방법
- 아래쪽: 익숙한 분이나 개발자를 위한 고급 설명

---

## 처음 쓰는 분은 여기만 보세요

### 1. 준비물

먼저 아래 3가지만 있으면 됩니다.

- Windows 11 컴퓨터
- 인터넷 연결
- Python 설치 프로그램

Python이 아직 없다면 먼저 설치해 주세요.

1. 인터넷 브라우저에서 `https://www.python.org/downloads/` 로 들어갑니다.
2. `Download Python` 버튼을 눌러 설치 파일을 받습니다.
3. 설치할 때 `Add python.exe to PATH`에 체크한 뒤 설치합니다.

설치가 끝났으면 다음으로 넘어가세요.

### 2. 프로그램 폴더 받기

이미 누군가에게 이 폴더를 받았다면 이 단계는 건너뛰셔도 됩니다.

GitHub에서 직접 받는 가장 쉬운 방법은 아래와 같습니다.

1. 이 저장소 페이지에서 초록색 `Code` 버튼을 누릅니다.
2. `Download ZIP`을 누릅니다.
3. 내려받은 ZIP 파일을 바탕화면이나 문서 폴더에 풉니다.
4. 폴더 이름이 `novel_autowriter_1`인지 확인합니다.

### 3. 처음 한 번만 설치하기

이 단계는 **처음 한 번만** 하면 됩니다.

1. `novel_autowriter_1` 폴더를 엽니다.
2. 폴더 창 위쪽 주소칸을 한 번 클릭합니다.
3. 주소칸에 `cmd`라고 쓰고 `Enter`를 누릅니다.
4. 검은 창이 열리면 아래 두 줄을 **한 줄씩** 붙여넣고 `Enter`를 누릅니다.

```bat
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
```

설치가 끝날 때까지 기다리면 됩니다.

### 4. 실행하기

이제부터는 보통 이 방법으로 실행하면 됩니다.

1. `novel_autowriter_1` 폴더 안의 [run_novel_autowriter.bat](./run_novel_autowriter.bat) 파일을 더블클릭합니다.
2. 잠시 후 검은 창이 하나 열립니다.
3. 브라우저가 열리면서 프로그램 화면이 보이면 성공입니다.

중요:

- 검은 창이 떠 있는 동안 프로그램이 실행 중입니다.
- **검은 창을 닫으면 프로그램도 같이 종료됩니다.**

브라우저가 자동으로 안 열리면 주소창에 아래 주소를 직접 넣어 주세요.

```text
http://127.0.0.1:8501
```

### 5. 처음 실행한 뒤 해야 할 일

프로그램이 열리면 보통 아래 순서로 하시면 됩니다.

1. 왼쪽에서 새 작품 이름을 적고 `새 작품 추가`를 누릅니다.
2. 왼쪽 `API / 모델 설정`을 엽니다.
3. 아래 둘 중 하나를 고릅니다.

#### 방법 A. Google API Key 사용

이 방법이 가장 이해하기 쉽습니다.

1. `Google API Key` 칸에 본인 키를 붙여넣습니다.
2. `이번 실행에만 적용`을 누르거나, 원하면 `보안 저장소에 저장`을 누릅니다.

#### 방법 B. Gemini CLI 사용

이 방법은 이미 Gemini CLI 로그인까지 해 둔 분에게 맞습니다.

1. `LLM 백엔드`를 `자동` 또는 `Gemini CLI만 사용`으로 둡니다.
2. `CLI 연결 테스트`를 눌러 연결 상태를 확인합니다.

### 6. 평소에는 어떻게 켜나요?

처음 설치만 끝났다면, 다음부터는 아주 단순합니다.

1. 폴더를 엽니다.
2. [run_novel_autowriter.bat](./run_novel_autowriter.bat)를 더블클릭합니다.
3. 검은 창을 닫지 않은 채 브라우저에서 사용합니다.

---

## 문제 생기면 이렇게 해 보세요

### 브라우저가 안 열릴 때

주소창에 아래 주소를 직접 넣어 보세요.

```text
http://127.0.0.1:8501
```

### `python`을 찾을 수 없다고 나올 때

Python이 아직 설치되지 않았거나, 설치할 때 `Add python.exe to PATH`를 체크하지 않은 경우입니다.

다시 Python 설치 파일을 실행해서 설치해 주세요.

### `run_novel_autowriter.bat`를 눌렀는데 바로 꺼질 때

처음 설치가 아직 안 끝났을 가능성이 큽니다.

다시 검은 창을 열고 아래 명령을 한 줄씩 실행해 주세요.

```bat
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 검은 창을 닫았더니 화면이 멈출 때

정상입니다. 검은 창이 프로그램 본체입니다.

다시 [run_novel_autowriter.bat](./run_novel_autowriter.bat)를 실행해 주세요.

### 작품 내용은 어디에 저장되나요?

보통 이 폴더 안의 `data` 폴더에 저장됩니다.

중요한 원고라면 가끔 `data` 폴더를 다른 곳에 복사해 백업해 두세요.

---

## 고급 / 개발자용 안내

### Git으로 내려받기

```bat
git clone https://github.com/twozeroone-1/novel_autowriter_1.git
cd novel_autowriter_1
```

### 가상환경 만들기와 패키지 설치

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 직접 실행하기

```bat
streamlit run main.py
```

또는 배치 파일로 실행할 수도 있습니다.

```bat
run_novel_autowriter.bat
```

### `.env` 파일 방식으로 API 키 넣기

앱 안에서 직접 입력하는 방법이 가장 쉽지만, 원하면 파일 방식도 쓸 수 있습니다.

1. [.env.example](./.env.example)를 복사해서 `.env` 파일을 만듭니다.
2. `GOOGLE_API_KEY` 값을 본인 키로 바꿉니다.

예시:

```env
GOOGLE_API_KEY="여기에_본인_API_KEY"
GEMINI_MODEL="gemini-3-flash-preview"
```

여러 API 키를 fallback 용도로 넣고 싶다면 쉼표(`,`)로 구분할 수 있습니다.

### Streamlit Community Cloud로 무료 배포하기

이 앱은 Community Cloud에서는 `수동/반자동 작업용`으로 쓰는 것을 권장합니다.

중요:

- `[5] 자동화 연재 모드`와 `[6] 외부 플랫폼 업로드`는 클라우드 모드에서 숨겨집니다.
- 작품 데이터는 서버 로컬 디스크 대신 GitHub 저장소에 저장하도록 설정해야 합니다.
- Gemini CLI, `.env` 저장, `keyring` 저장은 클라우드 모드에서 숨겨집니다.

#### 1. Community Cloud용 데이터 저장소 준비

1. GitHub에 비공개 저장소 하나를 새로 만듭니다.
2. 이 저장소는 작품 데이터(JSON/Markdown)만 저장하는 용도로 쓰는 편이 안전합니다.
3. GitHub Personal Access Token(PAT)을 하나 준비합니다.

필요 권한:

- 해당 저장소 `Contents` 읽기/쓰기

#### 2. 앱 저장소를 Community Cloud에 연결

1. Streamlit Community Cloud에서 이 저장소를 선택합니다.
2. 메인 파일은 `main.py`로 지정합니다.
3. Python 버전은 기본값으로 두어도 되지만, 로컬과 너무 다르지 않은 버전을 권장합니다.

#### 3. Secrets 설정

Community Cloud의 앱 설정에서 `Secrets`에 아래 값을 넣으세요.

예시는 [.streamlit/secrets.toml.example](./.streamlit/secrets.toml.example) 파일에도 있습니다.

```toml
APP_RUNTIME = "community_cloud"
GOOGLE_API_KEY = "your_google_api_key"
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_BACKEND = "api"
GITHUB_STORAGE_REPO = "owner/private-data-repo"
GITHUB_STORAGE_TOKEN = "github_pat_xxx"
```

설명:

- `APP_RUNTIME`: 클라우드 제한 모드를 켭니다.
- `GOOGLE_API_KEY`: Gemini API 호출용 키입니다.
- `GITHUB_STORAGE_REPO`: 작품 데이터를 저장할 비공개 저장소입니다.
- `GITHUB_STORAGE_TOKEN`: 위 저장소에 쓸 수 있는 토큰입니다.

#### 4. 클라우드에서 가능한 일

- 작품 설정 작성
- 아이디어/플롯 작업
- 회차 생성
- 원고 검수
- 반자동 흐름 사용
- 저장 후 다시 불러오기

#### 5. 클라우드에서 빠진 기능

- 자동화 연재 스케줄
- 외부 플랫폼 자동 업로드
- 로컬 폴더 열기
- `.env` / `keyring` / Gemini CLI 기반 설정

#### 6. 추천 운영 방식

가끔 접속해서 집필/검수만 할 거라면 Community Cloud로 충분합니다.

하지만 아래가 필요하면 VPS가 더 맞습니다.

- 항상 켜져 있는 예약 실행
- 브라우저 기반 업로드 자동화
- 서버 파일시스템을 직접 다루는 워크플로
- 더 예측 가능한 장기 운영

### Gemini CLI 사용

Gemini CLI를 쓰려면 먼저 사용자가 별도로 OAuth 로그인을 끝내야 합니다.

앱 실행 후 왼쪽 `API / 모델 설정`에서:

- `LLM 백엔드`를 `자동` 또는 `Gemini CLI만 사용`으로 선택
- `CLI 연결 테스트` 실행

### 데이터 백업과 옮기기

작품 내용은 주로 `data` 폴더에 들어 있습니다.

다른 컴퓨터로 옮길 때는 아래 순서가 가장 안전합니다.

1. 새 컴퓨터에 이 프로그램 폴더를 준비합니다.
2. 처음 설치를 한 번 끝냅니다.
3. 기존 컴퓨터의 `data` 폴더를 통째로 복사해서 새 컴퓨터에 덮어씁니다.

### Git 주의사항

작품 원고와 설정 데이터는 보통 `data/` 아래에 들어가며, 현재 `.gitignore`에 의해 Git 추적에서 제외됩니다.

이미 과거에 `data/`가 Git에 올라간 적이 있다면 한 번만 아래 명령을 사용해 추적을 해제할 수 있습니다.

```bat
git rm -r --cached data
```
