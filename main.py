import streamlit as st
import json
import os
import re
import shutil
from pathlib import Path
from dotenv import load_dotenv

from core.generator import Generator
from core.reviewer import Reviewer
from core.automator import Automator
from core.llm import LLMError

st.set_page_config(page_title="AI 웹소설 자동화 스튜디오", page_icon="✍️", layout="wide")

load_dotenv(override=True)

PROJECT_STATE_KEYS = [
    "ta_worldview",
    "ta_tone",
    "ta_continuity",
    "ta_state",
    "current_draft",
    "current_title",
    "edited_draft",
    "review_report",
    "reviewing_draft",
    "reviewing_title",
    "revised_draft",
    "edited_revised_draft",
    "auto_state",
    "auto_result",
    "auto_title",
    "auto_inst",
    "auto_len",
]
PROJECT_NAME_PATTERN = re.compile(r"^[0-9A-Za-z가-힣 _-]{1,50}$")

def set_env_variable(key: str, value: str):
    """ .env 파일의 특정 환경 변수를 업데이트하거나 새로 기록합니다. """
    env_file = ".env"
    if not os.path.exists(env_file):
        with open(env_file, "w", encoding="utf-8") as f:
            f.write("")
            
    with open(env_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    found = False
    with open(env_file, "w", encoding="utf-8") as f:
        for line in lines:
            if line.startswith(f"{key}="):
                f.write(f'{key}="{value}"\n')
                found = True
            else:
                f.write(line)
        if not found:
            f.write(f'{key}="{value}"\n')
            
    os.environ[key] = value

def clear_project_state():
    """프로젝트별 작업 상태를 지워 다른 작품과 섞이지 않게 합니다."""
    for key in PROJECT_STATE_KEYS:
        st.session_state.pop(key, None)

def normalize_project_name(raw_name: str) -> tuple[str | None, str | None]:
    normalized = " ".join(raw_name.strip().split())
    if not normalized:
        return None, "작품 이름을 입력해 주세요."

    if normalized == "default_project":
        return None, "'default_project'는 예약된 이름입니다. 다른 이름을 사용해 주세요."

    if normalized in {".", ".."} or any(sep in normalized for sep in ("/", "\\", ":")):
        return None, "작품 이름에는 경로 문자(/, \\, :)나 '.' '..'를 사용할 수 없습니다."

    if not PROJECT_NAME_PATTERN.fullmatch(normalized):
        return None, "작품 이름에는 한글, 영문, 숫자, 공백, 밑줄(_), 하이픈(-)만 사용할 수 있습니다."

    return normalized, None

def get_project_list():
    """data/projects 하위의 폴더 목록을 가져옵니다."""
    base_dir = Path("data/projects")
    if not base_dir.exists():
        base_dir.mkdir(parents=True)
        return []
    projects = [d.name for d in base_dir.iterdir() if d.is_dir() and d.name != "default_project"]
    return sorted(projects, key=str.casefold)

def open_folder(path: Path):
    if hasattr(os, "startfile"):
        os.startfile(os.path.abspath(str(path)))
        return

    st.error("이 환경에서는 폴더 열기 기능을 사용할 수 없습니다.")

def main():
    # 사이드바 (프로젝트 선택 및 환경설정)
    with st.sidebar:
        st.header("📚 작품(Workspace) 관리")
        
        # 새 작품 생성 폼
        new_project_name = st.text_input("새 작품 이름 만들기", placeholder="예: 나의_판타지_소설")
        if st.button("➕ 새 작품 추가", use_container_width=True):
            project_name, project_name_error = normalize_project_name(new_project_name)
            if project_name_error:
                st.error(project_name_error)
            else:
                target_dir = Path("data/projects") / project_name
                if not target_dir.exists():
                    Generator(project_name=project_name)
                    clear_project_state()
                    st.session_state['current_project'] = project_name
                    st.success(f"'{project_name}' 작품이 생성되었습니다.")
                    st.rerun()
                else:
                    st.error("이미 존재하는 작품 이름입니다.")
                
        st.divider()
        
        # 저장된 프로젝트 목록 불러오기
        projects = get_project_list()
        if not projects:
            st.warning("저장된 작품이 없습니다. 새 작품을 만들어주세요.")
            st.stop()
            
        # 첫 접속 시 가장 상단에 있는 프로젝트를 Session State로 초기화
        if 'current_project' not in st.session_state or st.session_state['current_project'] not in projects:
            st.session_state['current_project'] = projects[0]
            
        # 프로젝트 선택 드롭다운
        selected_project = st.selectbox(
            "현재 작업 중인 소설 선택 ⬇️", 
            options=projects,
            index=projects.index(st.session_state['current_project'])
        )
        
        # 선택된 프로젝트 변경 시 세션 업데이트 및 UI 리로드
        if selected_project != st.session_state['current_project']:
            clear_project_state()
            
            st.session_state['current_project'] = selected_project
            
            # 새 프로젝트의 config.json 데이터를 읽어와서 UI 텍스트 영역 세션 상태를 강제로 채워넣음
            temp_gen = Generator(project_name=selected_project)
            new_config = temp_gen.ctx.get_config()
            st.session_state['ta_worldview'] = new_config.get("worldview", "여기에 세계관(STORY_BIBLE)을 작성하세요.")
            st.session_state['ta_tone'] = new_config.get("tone_and_manner", "여기에 문체(STYLE_GUIDE) 지침을 작성하세요.")
            st.session_state['ta_continuity'] = new_config.get("continuity", "여기에 절대 변경 불가 룰, 연표, 관계도(CONTINUITY)를 작성하세요.")
            st.session_state['ta_state'] = new_config.get("state", "여기에 현재 회차 떡밥, 갈등 상황, 감정선(STATE)을 작성하세요.")
            
            st.rerun()
            
        # 선택된 프로젝트 삭제 기능
        with st.expander("🗑️ 현재 작품 삭제하기"):
            st.warning(f"정말 '{st.session_state['current_project']}' 作品을 삭제하시겠습니까? (복구 불가)")
            if st.button("네, 삭제합니다", type="primary", use_container_width=True):
                target_dir = Path("data/projects") / st.session_state['current_project']
                try:
                    shutil.rmtree(target_dir)
                    st.success(f"'{st.session_state['current_project']}' 작품이 성공적으로 삭제되었습니다.")
                    clear_project_state()
                    del st.session_state['current_project']
                            
                    # 삭제 후 남은 프로젝트가 있는지 확인 후 업데이트
                    remaining_projects = get_project_list()
                    if remaining_projects:
                        st.session_state['current_project'] = remaining_projects[0]
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"삭제 중 오류가 발생했습니다: {e}")
                    
        st.divider()
        st.header("⚙️ API 및 모델 설정")
        current_api_key = os.getenv("GOOGLE_API_KEY", "")
        new_api_key = st.text_input("🔑 Google API Key", value=current_api_key, type="password", help="여러 개의 키를 쉼표(,)로 구분하여 입력하시면 하나가 막혔을 때 다음 키로 자동 우회(Fallback)합니다.")
        if st.button("API 키 갱신", use_container_width=True):
            if new_api_key.strip():
                set_env_variable("GOOGLE_API_KEY", new_api_key.strip())
                load_dotenv(override=True)
                st.success("✅ API 키가 적용되었습니다.")
                st.rerun()
                
        # 생성 AI 모델 선택 드롭다운
        available_models = [
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-2.0-pro-exp",
            "gemini-2.0-flash",
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-3-pro-preview",
            "gemini-3-flash-preview",
            "gemini-3.1-pro-preview"
        ]
        current_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        selected_model = st.selectbox(
            "🧠 Gemini 모델 선택",
            options=available_models,
            index=available_models.index(current_model) if current_model in available_models else 0
        )
        
        if selected_model != current_model:
            set_env_variable("GEMINI_MODEL", selected_model)
            load_dotenv(override=True)
            st.success(f"✅ 모델이 '{selected_model}'(으)로 변경되었습니다.")
            st.rerun()
            
        st.link_button("🌐 토큰 잔여량 조회 (AI Studio)", "https://aistudio.google.com/app/usage?timeRange=last-28-days", use_container_width=True)

    # 선택된 프로젝트 기반으로 핵심 객체 초기화 (데이터 격리 방어선)
    generator = Generator(project_name=st.session_state['current_project'])
    reviewer = Reviewer(project_name=st.session_state['current_project'])
    automator = Automator(project_name=st.session_state['current_project'])
    config_path_hint = generator.ctx.config_path.as_posix()
    chars_path_hint = generator.ctx.chars_path.as_posix()
    
    st.title(f"✍️ AI 웹소설 스튜디오 - [{st.session_state['current_project']}]")
    st.markdown("현재 선택된 작품 환경에서 설정 관리, 회차 생성, 검수를 진행합니다.")
    
    tab1, tab2, tab3, tab4 = st.tabs(["[1] 프로젝트 통합 설정", "[2] 회차 생성", "[3] 원고 검수", "[4] 반자동 연재 모드"])

    with tab1:
        st.header("📚 프로젝트 통합 설정 (OpenClaw 포맷)")
        st.markdown(
            "이곳에 적힌 네 가지 문서(`STORY_BIBLE`, `STYLE_GUIDE`, `CONTINUITY`, `STATE`)가 "
            "AI의 뇌 속으로 들어가 **절대 설정**과 **현재 상황**을 인식하게 만듭니다. 줄글 형식으로 자유롭게 편집하세요."
        )
        
        config = generator.ctx.get_config()
        
        # UI 레이아웃을 위한 2단 분할
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("1. STORY BIBLE (세계관 및 연재 목표)")
            worldview_text = st.text_area(
                "세계관, 기본 배경, 인물 설정, 연재 목표 (분량/수위) 등", 
                value=config.get("worldview", ""), height=250, key="ta_worldview"
            )
            
            st.subheader("2. STYLE GUIDE (문체 지침)")
            tone_text = st.text_area(
                "시점 변경 규칙, 장문/단문 비율, 대사 빈도, 금지 표현 등", 
                value=config.get("tone_and_manner", ""), height=250, key="ta_tone"
            )
            
        with c2:
            st.subheader("3. CONTINUITY (고정 설정 및 연표)")
            continuity_text = st.text_area(
                "🔒 절대 바꾸면 안 되는 룰, 나이/지명/연표, 인물 관계도 등", 
                value=config.get("continuity", ""), height=250, key="ta_continuity"
            )
            
            st.subheader("4. STATE (현재 상태 및 떡밥)")
            state_text = st.text_area(
                "🧩 최근 회차 기준, 미해결 떡밥, 터진 갈등 상황, 인물 감정선", 
                value=config.get("state", ""), height=250, key="ta_state"
            )
            
        st.divider()
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("💾 위 4개 문서 모두 수동 저장", type="primary", use_container_width=True):
                config["worldview"] = worldview_text
                config["tone_and_manner"] = tone_text
                config["continuity"] = continuity_text
                config["state"] = state_text
                generator.ctx.save_config(config)
                st.success("설정이 성공적으로 저장되었습니다.")
        
        with col_btn2:
            if st.button("✨ 설정 뼈대 구체화 (AI 보조)", type="primary", use_container_width=True):
                if not worldview_text.strip():
                    st.warning("먼저 STORY BIBLE (세계관) 입력창에 이야기의 뼈대나 핵심 설정을 간단히 적어주세요.")
                elif not os.getenv("GOOGLE_API_KEY"):
                    st.error("API 키가 설정되지 않았습니다. 좌측 사이드바 설정을 확인해 주세요.")
                else:
                    with st.spinner("AI가 세계관에 살을 붙이고 있습니다... 🧠"):
                        try:
                            # 1. API 호출로 구체화된 텍스트 생성
                            elaborated_text = generator.elaborate_worldview(worldview_text)
                            
                            # 2. config 데이터 업데이트 및 저장
                            config["worldview"] = elaborated_text
                            generator.ctx.save_config(config)
                            
                            # 3. session_state 업데이트 및 화면 새로고침
                            st.session_state['ta_worldview'] = elaborated_text
                            st.success("세계관 구체화 성공! 내용이 자동으로 변경되었습니다.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"구체화 중 오류가 발생했습니다: {e}")

        st.divider()
        # [과거 줄거리 요약 (시스템 자동 누적)]
        st.subheader("📜 누적된 과거 줄거리 요약 (PREVIOUS SUMMARY)")
        st.markdown("이 부분은 회차가 생성되고 저장될 때마다 AI가 자동으로 3줄 요약하여 누적하는 곳입니다. 직접 수정하셔도 좋습니다.")
        summary_text = st.text_area("이전 줄거리 (시스템 자동 갱신 영역)", value=config.get("summary_of_previous", ""), height=150)
        if st.button("💾 줄거리 수동 저장", key="save_sum"):
            config["summary_of_previous"] = summary_text
            generator.ctx.save_config(config)
            st.success("이전 줄거리가 업데이트되었습니다.")
            
        st.divider()
        # 등장인물 스키마 관리 (수동 편집 및 자동 추출)
        with st.expander("👥 등장인물 JSON 스키마 관리 (고급)"):
            import json
            
            st.markdown("### 1. 원터치 자동 추출 (AI 어시스턴트)")
            st.info("위 '1. STORY BIBLE'에 작성된 세계관을 바탕으로 AI가 주요 인물을 자동으로 분석하여 아래 JSON 양식으로 채워줍니다.")
            if st.button("✨ STORY BIBLE에서 모든 주요 등장인물 자동 추출", type="primary", use_container_width=True):
                if not config.get("worldview", "").strip():
                    st.warning("위의 STORY BIBLE 입력창이 비어 있습니다. 먼저 세계관이나 등장인물을 대략적으로 적어주세요.")
                else:
                    with st.spinner("AI가 세계관을 읽고 핵심 인물을 분석 중입니다... 🕵️"):
                        try:
                            # generator 로직을 호출하여 AI가 캐릭터 JSON 배열 생성
                            extracted_json_str = generator.generate_characters(config["worldview"])
                            
                            # 생성된 문자열이 정상적인 JSON 구조인지 파싱 테스트
                            parsed_chars = json.loads(extracted_json_str)
                            
                            # 통과했다면 파일에 저장하고 화면 세션을 리로드하기 위해 ContextManager 객체에 반영
                            generator.ctx.save_characters(parsed_chars)
                            st.success("캐릭터가 성공적으로 추출되어 저장되었습니다!")
                            st.rerun() # 변경된 characters 파일을 다시 읽어오도록 화면 새로고침
                        except json.JSONDecodeError:
                            st.error("AI가 올바른 JSON 형식을 반환하지 못했습니다. 다시 시도해 주세요.")
                            st.code(extracted_json_str) # 디버깅용으로 잘못된 결과를 보여줌
                        except ValueError as e:
                            st.error(f"캐릭터 저장 형식이 올바르지 않습니다: {e}")
                        except LLMError as e:
                            st.error(f"캐릭터 추출 중 오류가 발생했습니다: {e}")
                        except Exception as e:
                            st.error(f"오류가 발생했습니다: {e}")
            
            st.divider()
            st.markdown("### 2. 수동 입력 및 직접 편집")
            st.info('''**[작성 예시]** 아래 양식을 복사하여 수정해 보세요.
```json
[
  {
    "id": "char_001",
    "name": "주인공",
    "role": "주인공",
    "description": "차가운 성격이지만 내면은 따뜻함.",
    "traits": ["냉혈안", "검술 천재"]
  }
]
```''')
            characters = generator.ctx.get_characters()
            char_json_str = json.dumps(characters, ensure_ascii=False, indent=4) if characters else "[]"
            chars_text = st.text_area("현재 등장인물 데이터 (JSON 편집기)", value=char_json_str, height=300)
            
            if st.button("💾 등장인물 정보 수동 저장", key="save_char"):
                try:
                    parsed_chars = json.loads(chars_text)
                    generator.ctx.save_characters(parsed_chars)
                    st.success("성공적으로 저장되었습니다!")
                except json.JSONDecodeError:
                    st.error("JSON 문법 오류입니다. 괄호나 따옴표가 맞는지 확인해 주세요.")
                except ValueError as e:
                    st.error(f"등장인물 형식 오류입니다: {e}")
                except Exception as e:
                    st.error(f"알 수 없는 오류가 발생했습니다: {e}")

    with tab2:
        st.header("다음 회차 생성기")
        st.info(f"현재 프로젝트의 세계관 (`{config_path_hint}`) 과 등장인물 (`{chars_path_hint}`) 데이터가 프롬프트에 자동 주입됩니다.")
        
        chapter_title = st.text_input("회차 제목 (저장용 파일명)", value="제 2화: 얼음의 숲에서")
        user_instruction = st.text_area("이번 회차 전개 지시사항", 
                                       value="레온과 세리아가 숲속에서 길을 잃고 몬스터와 처음 조우하는 장면을 긴장감 있게 써줘. 세리아가 마법을 쓰려다 실수하는 장면 포함할 것.",
                                       height=150)
        target_length = st.number_input("생성 분량(글자 수) 목표치", min_value=500, max_value=20000, value=5000, step=500, help="원하는 글자수를 지정하세요. AI가 사건의 묘사나 대화를 조절하여 이 분량을 맞추려 노력합니다.")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            generate_btn = st.button("원고 초안 생성하기", type="primary")
        with col2:
            if st.button("📂 저장폴더 열기", key="open_folder_1"):
                open_folder(generator.chapters_dir)
                
        if generate_btn:
            if not os.getenv("GOOGLE_API_KEY"):
                st.error("API 키가 설정되지 않았습니다. 사이드바 설정을 확인해 주세요.")
            elif not user_instruction.strip():
                st.warning("지시사항을 입력해 주세요.")
            else:
                with st.spinner(f"작가가 원고를 집필 중입니다 (목표: {target_length}자 내외)... ☕"):
                    try:
                        draft = generator.create_chapter(user_instruction, target_length)
                    except LLMError as e:
                        st.error(f"초안 생성 중 오류가 발생했습니다: {e}")
                    except Exception as e:
                        st.error(f"초안 생성 중 알 수 없는 오류가 발생했습니다: {e}")
                    else:
                        st.session_state['current_draft'] = draft
                        st.session_state['current_title'] = chapter_title.strip() or "무제"
                        # [버그 픽스] 스트림릿 텍스트 에어리어(key="edited_draft")에 새 원고를 강제로 즉시 덮어씌움
                        st.session_state['edited_draft'] = draft
                        st.session_state.pop('review_report', None)
                        st.session_state.pop('reviewing_draft', None)
                        st.session_state.pop('reviewing_title', None)
                        st.session_state.pop('revised_draft', None)
                        st.session_state.pop('edited_revised_draft', None)
                        st.success("초안 생성이 완료되었습니다!")
                    
        if 'current_draft' in st.session_state:
            st.divider()
            st.subheader("생성된 문서 초안")
            st.text_area("수정 가능한 초안", value=st.session_state['current_draft'], height=400, key="edited_draft")
            
            # 저장 버튼
            col1, col2 = st.columns([1, 2])
            with col1:
                save_draft_btn = st.button("현재 상태로 파일 저장 (마크다운)")
            with col2:
                if st.button("📂 저장폴더 열기", key="open_folder_2"):
                    open_folder(generator.chapters_dir)
                    
            if save_draft_btn:
                try:
                    saved_path = generator.save_chapter(st.session_state['current_title'], st.session_state['edited_draft'])
                except Exception as e:
                    st.error(f"파일 저장 중 오류가 발생했습니다: {e}")
                else:
                    st.success(f"파일이 저장되었습니다: `{saved_path}`")
                
    with tab3:
        st.header("편집자 검수 보고서")
        st.markdown("생성된 원고가 세계관과 충돌하지 않는지, 어색한 문맥은 없는지 PD의 시선으로 검토합니다.")
        
        # 저장된 원고 파일 목록 불러오기
        saved_files = []
        if generator.chapters_dir.exists():
            saved_files = [f.name for f in generator.chapters_dir.iterdir() if f.is_file() and f.suffix == '.md']
            
        selected_file = st.selectbox("📂 검수할 원고 파일 선택", options=["새로 생성된 초안 사용"] + saved_files)
        
        # 원고 내용 불러오기
        draft_to_review = ""
        review_title = "임시_제목"
        if selected_file == "새로 생성된 초안 사용":
            if 'current_draft' in st.session_state:
                draft_to_review = st.session_state['current_draft']
                review_title = st.session_state.get('current_title', "새로운_초안")
            else:
                st.info("현재 메모리에 새로 생성된 초안이 없습니다. 위 목록에서 기존에 저장된 파일을 선택하시거나, [2] 회차 생성 탭에서 초안을 먼저 생성해 주세요.")
        else:
            file_path = generator.chapters_dir / selected_file
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    draft_to_review = f.read()
                review_title = selected_file.replace(".md", "")

        if draft_to_review:
            st.subheader("검수 대상 원고")
            # 사용자가 검수 전에 직접 원고를 한 번 더 수정할 수 있도록 text_area로 제공하고 state에 동기화
            edited_draft_to_review = st.text_area("이 내용을 바탕으로 편집자에게 검수를 요청합니다.", value=draft_to_review, height=300)
            
            if st.button("현재 원고 검토 요청", type="primary"):
                with st.spinner("편집자가 원고를 꼼꼼히 읽고 있습니다... 👓"):
                    try:
                        report = reviewer.review_chapter(edited_draft_to_review)
                    except LLMError as e:
                        st.error(f"검수 중 오류가 발생했습니다: {e}")
                    except Exception as e:
                        st.error(f"검수 중 알 수 없는 오류가 발생했습니다: {e}")
                    else:
                        st.session_state['review_report'] = report
                        st.session_state['reviewing_draft'] = edited_draft_to_review # 어떤 원고를 리뷰했는지 기억
                        st.session_state['reviewing_title'] = review_title
                        st.session_state.pop('revised_draft', None)
                        st.session_state.pop('edited_revised_draft', None)
                
        if 'review_report' in st.session_state:
            st.divider()
            st.subheader("📝 검수 리포트 결과")
            st.markdown(st.session_state['review_report'])
            
            col_r1, col_r2 = st.columns([1, 2])
            with col_r1:
                if st.button("💾 이 리포트를 파일로 저장 (.md)", key="save_report_btn"):
                    base_title = st.session_state.get('reviewing_title', "원고")
                    report_filename = f"{base_title}_검수리포트.md"
                    report_path = generator.chapters_dir / report_filename
                    try:
                        with open(report_path, "w", encoding="utf-8") as f:
                            f.write(st.session_state['review_report'])
                    except Exception as e:
                        st.error(f"리포트 저장 중 오류가 발생했습니다: {e}")
                    else:
                        st.success(f"리포트가 저장되었습니다: `{report_path}`")
            with col_r2:
                if st.button("📂 저장폴더 열기", key="open_folder_report"):
                    open_folder(generator.chapters_dir)
            
            st.divider()
            st.subheader("리포트 피드백 반영")
            if st.button("✨ 리포트 피드백을 반영하여 초안 자동 수정", type="primary"):
                with st.spinner("작가가 피드백을 반영하여 원고를 수정하고 있습니다... ✍️"):
                    try:
                        revised = reviewer.revise_draft(
                            st.session_state.get('reviewing_draft', draft_to_review),
                            st.session_state['review_report'],
                        )
                    except LLMError as e:
                        st.error(f"수정본 작성 중 오류가 발생했습니다: {e}")
                    except Exception as e:
                        st.error(f"수정본 작성 중 알 수 없는 오류가 발생했습니다: {e}")
                    else:
                        st.session_state['revised_draft'] = revised
                        st.session_state['edited_revised_draft'] = revised
                        st.success("수정본 작성이 완료되었습니다!")
                    
        if 'revised_draft' in st.session_state:
            st.divider()
            st.subheader("✨ 피드백이 반영된 수정본")
            st.text_area("수정 가능한 최종본", value=st.session_state['revised_draft'], height=400, key="edited_revised_draft")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                save_revised_btn = st.button("수정본 파일 저장 (마크다운)")
            with col2:
                if st.button("📂 저장폴더 열기", key="open_folder_3"):
                    open_folder(generator.chapters_dir)
                    
            if save_revised_btn:
                base_title = st.session_state.get('reviewing_title', "수정된_원고")
                try:
                    saved_path = generator.save_chapter(base_title + "_수정본", st.session_state['edited_revised_draft'])
                except Exception as e:
                    st.error(f"수정본 저장 중 오류가 발생했습니다: {e}")
                else:
                    st.success(f"수정본 파일이 저장되었습니다: `{saved_path}`")
                    
                    with st.spinner("다음 회차를 위해 방금 저장한 내용을 컨텍스트에 요약하여 반영 중입니다 (필요시 자동 압축 🔄)..."):
                        try:
                            new_summary = generator.summarize_chapter(st.session_state['edited_revised_draft'])
                            generator.ctx.update_summary(new_summary, generator_instance=generator)
                        except LLMError as e:
                            st.warning(f"수정본 저장은 완료됐지만 줄거리 요약 갱신은 실패했습니다: {e}")
                        except Exception as e:
                            st.warning(f"수정본 저장은 완료됐지만 줄거리 요약 갱신 중 예상치 못한 오류가 발생했습니다: {e}")
                        else:
                            st.success("다음 회차를 위한 설정 갱신(이전 줄거리 요약 자동 추가/압축)이 완료되었습니다!")

    with tab4:
        st.header("🤖 반자동 연재 모드 (Semi-Auto Mode)")
        st.markdown("클릭 한 번으로 초안 생성부터 검수, 수정, 다음 회차 설정 요약까지 일괄 처리합니다.")

        # 상태 머신 초기화
        if 'auto_state' not in st.session_state:
            st.session_state['auto_state'] = 'READY'
            
        if st.session_state['auto_state'] == 'READY':
            st.info("다음 회차의 지시사항을 입력하고 파이프라인을 가동하세요.")
            auto_chapter_title = st.text_input("회차 제목 (저장용 파일명)", value="제 3화: 새로운 여정", key="auto_title")
            auto_instruction = st.text_area("이번 회차 전개 지시사항", 
                                           value="주인공 일행이 마침내 동굴을 벗어나 거대한 도시의 입구에 도착하는 장면을 장엄하게 묘사해줘.",
                                           height=150, key="auto_inst")
            auto_target_length = st.number_input("생성 분량(글자 수) 목표치", min_value=500, max_value=20000, value=5000, step=500, key="auto_len")
            
            if st.button("🚀 자동 생성 파이프라인 가동", type="primary", use_container_width=True):
                if not os.getenv("GOOGLE_API_KEY"):
                    st.error("API 키가 설정되지 않았습니다. 사이드바 설정을 확인해 주세요.")
                elif not auto_instruction.strip():
                    st.warning("지시사항을 입력해 주세요.")
                else:
                    st.session_state['auto_state'] = 'RUNNING'
                    st.rerun()

        elif st.session_state['auto_state'] == 'RUNNING':
            st.info("파이프라인이 실행 중입니다. 잠시만 기다려 주세요...")
            try:
                # 1 Cycle 풀가동
                result = automator.run_single_cycle(
                    st.session_state['auto_title'], 
                    st.session_state['auto_inst'], 
                    st.session_state['auto_len']
                )
                
                # 결과 저장 후 대기(REVIEW) 상태로 전환
                st.session_state['auto_result'] = result
                st.session_state['auto_state'] = 'REVIEW'
                st.rerun()
            except Exception as e:
                st.error(f"파이프라인 실행 중 오류가 발생했습니다: {e}")
                if st.button("돌아가기"):
                    st.session_state['auto_state'] = 'READY'
                    st.rerun()

        elif st.session_state['auto_state'] == 'REVIEW':
            st.success("🎉 한 회차 자동 생성이 완료되었습니다! 다음 회차로 넘어가기 전 설정을 검토해 주세요.")
            
            result = st.session_state.get('auto_result', {})
            if result.get("summary_error"):
                st.warning(f"회차 저장은 완료됐지만 줄거리 요약 갱신은 실패했습니다: {result['summary_error']}")
            
            with st.expander("📄 [결과] 최종 수정본 확인", expanded=False):
                st.text_area("수정본 (읽기 전용)", value=result.get('revised_draft', ''), height=400)
                st.info(f"💾 저장 위치: `{result.get('saved_path', '')}`")
                
            with st.expander("📝 [결과] 편집자 검수 리포트", expanded=False):
                st.markdown(result.get('review_report', ''))
                
            st.divider()
            st.subheader("⚙️ 다음 회차를 위한 설정(JSON) 갱신")
            st.markdown("방금 생성된 회차의 결과(새로운 인물 등장, 떡밥 회수 등)를 반영하여 아래 설정을 업데이트해 주세요.")
            
            # 현재 JSON 설정 로드
            current_config = generator.ctx.get_config()
            
            c1, c2 = st.columns(2)
            with c1:
                new_state = st.text_area(
                    "🧩 CURRENT STATE 업데이트", 
                    value=current_config.get("state", ""), 
                    height=200, 
                    help="방금 회차를 통해 달라진 현재 상황이나 다음 회차로 이어질 단기 목표를 갱신하세요."
                )
            with c2:
                new_summary = st.text_area(
                    "📜 PREVIOUS SUMMARY (자동 갱신됨)", 
                    value=current_config.get("summary_of_previous", ""), 
                    height=200,
                    help="AI가 방금 회차의 내용을 요약해 끝부분에 추가한 상태입니다. 필요 시 다듬어주세요."
                )

            st.divider()
            if st.button("✅ 설정 저장 후 다음 회차 준비 (READY)", type="primary", use_container_width=True):
                # 변경된 설정 저장
                current_config["state"] = new_state
                current_config["summary_of_previous"] = new_summary
                generator.ctx.save_config(current_config)
                
                # 상태 초기화
                for key in ["auto_result", "auto_title", "auto_inst", "auto_len"]:
                    st.session_state.pop(key, None)
                st.session_state['auto_state'] = 'READY'
                
                st.success("설정이 저장되었습니다. 다음 회차를 준비합니다.")
                st.rerun()

if __name__ == "__main__":
    main()
