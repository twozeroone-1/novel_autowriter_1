import streamlit as st
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import time
import uuid

from core.generator import Generator
from core.reviewer import Reviewer
from core.automator import Automator
from core.planner import Planner
from core.automation_state import AutomationState
from core.context import validate_project_name
from core.llm import get_llm_provider, get_llm_readiness, is_oauth_fallback_enabled
from core.ui.tab_project import render_tab_project
from core.ui.tab_generate_review import render_tab_generate, render_tab_review
from core.ui.tab_auto import render_tab_semi_auto, render_tab_full_auto
from core.ui.tab_planning import render_tab_ideas, render_tab_plot

st.set_page_config(page_title="AI 웹소설 자동화 스튜디오", page_icon="✍️", layout="wide")

load_dotenv(override=True)

def set_env_variable(key: str, value: str):
    """ .env 파일의 특정 환경 변수를 업데이트하거나 새로 기록합니다. """
    env_file = Path(__file__).resolve().parent / ".env"
    if not env_file.exists():
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

def get_project_list():
    """data/projects 하위의 폴더 목록을 가져옵니다."""
    base_dir = Path("data/projects")
    if not base_dir.exists():
        base_dir.mkdir(parents=True)
        return []
    result = []
    for d in base_dir.iterdir():
        if not d.is_dir() or d.name == "default_project":
            continue
        try:
            validate_project_name(d.name)
        except ValueError:
            continue
        result.append(d.name)
    return result


def safe_open_folder(path_obj: Path):
    abs_path = os.path.abspath(str(path_obj))
    try:
        if platform.system() == "Windows":
            os.startfile(abs_path)  # type: ignore[attr-defined]
        elif platform.system() == "Darwin":
            subprocess.run(["open", abs_path], check=True)
        else:
            subprocess.run(["xdg-open", abs_path], check=True)
    except Exception as e:
        st.error(f"폴더 열기 실패: {e}")


def auth_gate():
    secret_token = ""
    try:
        secret_token = str(st.secrets.get("APP_ACCESS_TOKEN", "")).strip()
    except Exception:
        secret_token = ""
    if not secret_token:
        secret_token = os.getenv("APP_ACCESS_TOKEN", "").strip()
    if not secret_token:
        return

    if "authed" not in st.session_state:
        st.session_state["authed"] = False

    if not st.session_state["authed"]:
        st.title("🔐 앱 접근 인증")
        entered = st.text_input("접근 토큰", type="password")
        if st.button("인증하기", type="primary"):
            if entered.strip() == secret_token:
                st.session_state["authed"] = True
                st.success("인증 성공")
                st.rerun()
            else:
                st.error("토큰이 올바르지 않습니다.")
        st.stop()


def get_next_auto_chapter_number(chapters_dir: Path) -> int:
    pattern = re.compile(r"^\[Auto\]\s*제\s*(\d+)화")
    max_num = 0
    for f in chapters_dir.iterdir():
        if not f.is_file() or f.suffix != ".md":
            continue
        match = pattern.match(f.stem)
        if not match:
            continue
        max_num = max(max_num, int(match.group(1)))
    return max_num + 1 if max_num > 0 else 1


def is_llm_ready(show_error: bool = True) -> bool:
    ready, message = get_llm_readiness()
    if not ready and show_error:
        st.error(message)
    return ready

def main():
    auth_gate()
    # 사이드바 (프로젝트 선택 및 환경설정)
    with st.sidebar:
        st.header("📚 작품(Workspace) 관리")
        
        # 새 작품 생성 폼
        new_project_name = st.text_input("새 작품 이름 만들기", placeholder="예: 나의_판타지_소설")
        if st.button("➕ 새 작품 추가", use_container_width=True):
            if new_project_name.strip():
                try:
                    validated_name = validate_project_name(new_project_name.strip())
                except ValueError as e:
                    st.error(str(e))
                    validated_name = ""
                if validated_name == "default_project":
                    st.error("'default_project'는 예약된 이름입니다. 다른 이름을 사용해 주세요.")
                elif validated_name:
                    # 특수문자나 띄어쓰기 가공 처리 없이 통과 (폴더명으로 사용)
                    target_dir = Path("data/projects") / validated_name
                    if not target_dir.exists():
                        target_dir.mkdir(parents=True)
                        st.session_state['current_project'] = validated_name
                        # 새 프로젝트 생성 시 이전 프로젝트의 UI 텍스트(session_state) 초기화
                        for key in ['ta_worldview', 'ta_tone', 'ta_continuity', 'ta_state', 'current_draft', 'current_title', 'review_report', 'revised_draft']:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.success(f"'{validated_name}' 작품이 생성되었습니다.")
                        st.rerun()
                    else:
                        st.error("이미 존재하는 작품 이름입니다.")
            else:
                st.warning("작품 이름을 입력해 주세요.")
                
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
            # 전환 전 세션 초기화
            for key in ['ta_worldview', 'ta_tone', 'ta_continuity', 'ta_state', 'current_draft', 'current_title', 'review_report', 'revised_draft']:
                if key in st.session_state:
                    del st.session_state[key]
            
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
                    # 세션 지우기 및 초기화
                    del st.session_state['current_project']
                    for key in ['ta_worldview', 'ta_tone', 'ta_continuity', 'ta_state', 'current_draft', 'current_title', 'review_report', 'revised_draft']:
                        if key in st.session_state:
                            del st.session_state[key]
                            
                    # 삭제 후 남은 프로젝트가 있는지 확인 후 업데이트
                    remaining_projects = get_project_list()
                    if remaining_projects:
                        st.session_state['current_project'] = remaining_projects[0]
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"삭제 중 오류가 발생했습니다: {e}")
                    
        st.divider()
        st.header("⚙️ API 및 모델 설정")
        provider_options = ["google_api", "gemini_cli_oauth"]
        provider_labels = {
            "google_api": "Google API Key",
            "gemini_cli_oauth": "Gemini CLI OAuth",
        }
        current_provider = get_llm_provider()
        selected_provider = st.selectbox(
            "LLM 실행 방식",
            options=provider_options,
            index=provider_options.index(current_provider) if current_provider in provider_options else 0,
            format_func=lambda v: provider_labels.get(v, v),
        )

        if selected_provider != current_provider:
            set_env_variable("LLM_PROVIDER", selected_provider)
            load_dotenv(override=True)
            st.success(f"✅ LLM 실행 방식이 '{provider_labels[selected_provider]}'(으)로 변경되었습니다.")
            st.rerun()

        fallback_to_api = st.checkbox(
            "Gemini OAuth 실패 시 API 키로 자동 fallback",
            value=is_oauth_fallback_enabled(),
            help="OAuth 모드에서 네트워크/응답 오류가 발생하면 Google API 키 모드로 자동 재시도합니다.",
        )
        if fallback_to_api != is_oauth_fallback_enabled():
            set_env_variable("LLM_FALLBACK_TO_API", "true" if fallback_to_api else "false")
            load_dotenv(override=True)
            st.success("✅ fallback 설정이 적용되었습니다.")
            st.rerun()

        if selected_provider == "google_api":
            current_api_key = os.getenv("GOOGLE_API_KEY", "")
            new_api_key = st.text_input(
                "🔑 Google API Key",
                value=current_api_key,
                type="password",
                help="여러 개의 키를 쉼표(,)로 구분하여 입력하시면 하나가 막혔을 때 다음 키로 자동 우회(Fallback)합니다.",
            )
            if st.button("API 키 갱신", use_container_width=True):
                if new_api_key.strip():
                    set_env_variable("GOOGLE_API_KEY", new_api_key.strip())
                    load_dotenv(override=True)
                    st.success("✅ API 키가 적용되었습니다.")
                    st.rerun()
        else:
            st.info("Gemini CLI OAuth 모드입니다. API 키 없이 `gemini` 로그인 세션을 사용합니다.")
            st.caption("인증이 필요한 경우 터미널에서 `gemini`를 실행해 로그인해 주세요.")

        ready, ready_msg = get_llm_readiness(selected_provider)
        if ready:
            st.caption(f"준비 상태: {ready_msg}")
        else:
            st.warning(f"준비 상태: {ready_msg}")
                
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
    planner = Planner()
    auto_state = AutomationState(generator.ctx.data_dir)
    if "auto_owner_id" not in st.session_state:
        st.session_state["auto_owner_id"] = str(uuid.uuid4())
    
    st.title(f"✍️ AI 웹소설 스튜디오 - [{st.session_state['current_project']}]")
    st.markdown("현재 선택된 작품 환경에서 설정 관리, 회차 생성, 검수를 진행합니다.")
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "[1] 프로젝트 통합 설정",
        "[2] 회차 생성",
        "[3] 원고 검수",
        "[4] 반자동 연재 모드",
        "[5] 자동화 연재 모드",
        "[6] 아이디어/제목",
        "[7] 대형 플롯",
    ])

    with tab1:
        render_tab_project(generator, is_llm_ready)

    with tab2:
        render_tab_generate(generator, is_llm_ready, safe_open_folder)

    with tab3:
        render_tab_review(generator, reviewer, safe_open_folder)

    with tab4:
        render_tab_semi_auto(generator, automator, is_llm_ready)

    with tab5:
        render_tab_full_auto(generator, automator, auto_state, is_llm_ready, get_next_auto_chapter_number)

    with tab6:
        render_tab_ideas(planner, is_llm_ready)

    with tab7:
        render_tab_plot(generator, planner, is_llm_ready)

if __name__ == "__main__":
    main()
