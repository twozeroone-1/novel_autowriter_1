import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv

from core.generator import Generator
from core.reviewer import Reviewer

st.set_page_config(page_title="AI 웹소설 자동화 스튜디오", page_icon="✍️", layout="wide")

load_dotenv(override=True)

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

def get_project_list():
    """data/projects 하위의 폴더 목록을 가져옵니다."""
    base_dir = Path("data/projects")
    if not base_dir.exists():
        base_dir.mkdir(parents=True)
        return []
    return [d.name for d in base_dir.iterdir() if d.is_dir()]

def main():
    # 사이드바 (프로젝트 선택 및 환경설정)
    with st.sidebar:
        st.header("📚 작품(Workspace) 관리")
        
        # 새 작품 생성 폼
        new_project_name = st.text_input("새 작품 이름 만들기", placeholder="예: 나의_판타지_소설")
        if st.button("➕ 새 작품 추가", use_container_width=True):
            if new_project_name.strip():
                # 특수문자나 띄어쓰기 가공 처리 없이 통과 (폴더명으로 사용)
                target_dir = Path("data/projects") / new_project_name.strip()
                if not target_dir.exists():
                    target_dir.mkdir(parents=True)
                    st.session_state['current_project'] = new_project_name.strip()
                    st.success(f"'{new_project_name}' 작품이 생성되었습니다.")
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
            st.session_state['current_project'] = selected_project
            # 프로젝트 전환 시 이전의 임시 원고나 리포트 세션을 안전하게 폐기
            for key in ['current_draft', 'current_title', 'review_report', 'revised_draft']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
            
        st.divider()
        st.header("⚙️ API 및 모델 설정")
        current_api_key = os.getenv("GOOGLE_API_KEY", "")
        new_api_key = st.text_input("🔑 Google API Key", value=current_api_key, type="password", help="발급받은 AI 기기를 입력하세요.")
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
            
        st.link_button("🌐 토큰 잔여량 조회 (AI Studio)", "https://aistudio.google.com/app/plan_information", use_container_width=True)

    # 선택된 프로젝트 기반으로 핵심 객체 초기화 (데이터 격리 방어선)
    generator = Generator(project_name=st.session_state['current_project'])
    reviewer = Reviewer() # Reviewer도 이후 Context를 사용할 시 넘겨줘야하지만 현재는 draft 텍스트만 처리함
    
    st.title(f"✍️ AI 웹소설 스튜디오 - [{st.session_state['current_project']}]")
    st.markdown("현재 선택된 작품 환경에서 설정 관리, 회차 생성, 검수를 진행합니다.")
    
    tab1, tab2, tab3 = st.tabs(["[1] 프로젝트 통합 설정", "[2] 회차 생성", "[3] 원고 검수"])

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
            st.info("💡 **Tip:** 세계관(STORY_BIBLE)에 설정 뼈대를 적어놓고 AI에게 살을 붙여달라고 요청하는 기능(구체화 버튼)은 곧 지원될 예정입니다!")

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
        # 등장인물 스키마 관리는 추후 마크다운 구조로 흡수되거나 부가 기능으로 뺄 예정이므로 우선 보존
        with st.expander("👥 등장인물 JSON 스키마 관리 (고급)"):
            import json
            characters = generator.ctx.get_characters()
            char_json_str = json.dumps(characters, ensure_ascii=False, indent=4) if characters else "[]"
            chars_text = st.text_area("현재 등장인물 명단", value=char_json_str, height=200)
            if st.button("💾 등장인물 수동 저장", key="save_char"):
                try:
                    parsed_chars = json.loads(chars_text)
                    generator.ctx.save_characters(parsed_chars)
                    st.success("성공!")
                except Exception as e:
                    st.error("JSON 문법 오류입니다.")

    with tab2:
        st.header("다음 회차 생성기")
        st.info("현재 설정된 세계관 (`data/config.json`) 과 등장인물 (`data/characters.json`) 데이터가 프롬프트에 자동 주입됩니다.")
        
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
                abs_path = os.path.abspath(str(generator.chapters_dir))
                os.startfile(abs_path)
                
        if generate_btn:
            if not os.getenv("GOOGLE_API_KEY"):
                st.error("API 키가 설정되지 않았습니다. 사이드바 설정을 확인해 주세요.")
            elif not user_instruction.strip():
                st.warning("지시사항을 입력해 주세요.")
            else:
                with st.spinner(f"작가가 원고를 집필 중입니다 (목표: {target_length}자 내외)... ☕"):
                    draft = generator.create_chapter(user_instruction, target_length)
                    st.session_state['current_draft'] = draft
                    st.session_state['current_title'] = chapter_title
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
                    abs_path = os.path.abspath(str(generator.chapters_dir))
                    os.startfile(abs_path)
                    
            if save_draft_btn:
                saved_path = generator.save_chapter(st.session_state['current_title'], st.session_state['edited_draft'])
                st.success(f"파일이 저장되었습니다: `{saved_path}`")
                
    with tab3:
        st.header("편집자 검수 보고서")
        st.markdown("생성된 원고가 세계관과 충돌하지 않는지, 어색한 문맥은 없는지 PD의 시선으로 검토합니다.")
        
        if 'current_draft' not in st.session_state:
            st.warning("[2] 회차 생성 탭에서 먼저 초안을 생성해 주세요.")
            
        elif st.button("현재 초안 검토 요청"):
            with st.spinner("편집자가 원고를 꼼꼼히 읽고 있습니다... 👓"):
                report = reviewer.review_chapter(st.session_state['edited_draft'])
                st.session_state['review_report'] = report
                
        if 'review_report' in st.session_state:
            st.divider()
            st.subheader("📝 검수 리포트 결과")
            st.markdown(st.session_state['review_report'])
            
            st.divider()
            st.subheader("리포트 피드백 반영")
            if st.button("✨ 리포트 피드백을 반영하여 초안 자동 수정", type="primary"):
                with st.spinner("작가가 피드백을 반영하여 원고를 수정하고 있습니다... ✍️"):
                    revised = reviewer.revise_draft(st.session_state['edited_draft'], st.session_state['review_report'])
                    st.session_state['revised_draft'] = revised
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
                    abs_path = os.path.abspath(str(generator.chapters_dir))
                    os.startfile(abs_path)
                    
            if save_revised_btn:
                saved_path = generator.save_chapter(st.session_state['current_title'] + "_수정본", st.session_state['edited_revised_draft'])
                st.success(f"수정본 파일이 저장되었습니다: `{saved_path}`")
                
                with st.spinner("다음 회차를 위해 방금 저장한 내용을 컨텍스트에 요약하여 반영 중입니다... 🔄"):
                    new_summary = generator.summarize_chapter(st.session_state['edited_revised_draft'])
                    generator.ctx.update_summary(new_summary)
                    st.success("다음 회차를 위한 설정 갱신(이전 줄거리 요약 자동 추가)도 완료되었습니다!")

if __name__ == "__main__":
    main()
