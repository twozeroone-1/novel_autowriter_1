# Novel Autowriter

AI를 활용하여 자동으로 소설을 작성해주는 프로그램입니다.

## 🚀 설치 및 실행 방법

### 1단계: 코드 가져오기 (Clone)

터미널(또는 명령 프롬프트)을 열고 아래 명령어를 입력하여 코드를 다운로드합니다.

```bash
git clone https://github.com/twozeroone-1/novel_autowriter_1.git
cd novel_autowriter_1
```

### 2단계: 가상환경 설정 및 라이브러리 설치

Python 가상환경(venv)을 만들고, 프로그램 실행에 필요한 패키지들을 한 번에 설치합니다.

```bash
# 가상환경 생성 (Windows)
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 필수 패키지 설치
pip install -r requirements.txt
```

### 3단계: 환경설정 (API 키 설정)

이 프로그램은 Google Gemini(또는 기타 언어모델)의 API 키가 필요합니다. 보안상의 이유로 개인 API 키는 Github에 올라가지 않습니다.

1. 다운로드 받은 폴더 안에 있는 `.env.example` 파일을 복사하여 `.env` 라는 이름으로 파일을 만듭니다.
2. 새로 만든 `.env` 파일을 메모장 등으로 열어서 임시로 적힌 `"여기에_구글_API_키를_입력하세요"` 부분을 지우고 **본인의 실제 API 키**를 붙여넣고 저장합니다.

```env
# .env 파일 수정한 예시
GOOGLE_API_KEY="AIzaSy...자신의실제키..."
GEMINI_MODEL="gemini-3-flash-preview"
```

### 4단계: 프로그램 실행

모든 준비가 끝났습니다! 아래 명령어로 프로그램을 실행하세요.

```bash
streamlit run main.py
```

---

## 🔄 컴퓨터 재시작 후 다시 실행할 때 (일상적인 사용)

처음 설치가 끝난 후, 나중에 컴퓨터를 껐다 켜고 다시 소설 작업을 이어서 하고 싶을 때는 딱 **두 줄**의 명령어만 순서대로 입력하면 됩니다.

1. VS Code나 터미널에서 `novel_autowriter` (본인의 작업 폴더)를 열어줍니다.
2. 터미널(명령 프롬프트)창에 아래 두 줄을 순서대로 입력하고 실행합니다.

```bash
# 1. 가상환경 켜기 (필수!)
venv\Scripts\activate

# 2. 프로그램 실행하기
streamlit run main.py
```
