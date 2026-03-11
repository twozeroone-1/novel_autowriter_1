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
