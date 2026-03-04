import streamlit as st

from core.llm import LLMError


def render_tab_generate(generator, is_llm_ready, safe_open_folder):
    st.header("다음 회차 생성기")
    st.info("현재 설정된 세계관 (`data/config.json`) 과 등장인물 (`data/characters.json`) 데이터가 프롬프트에 자동 주입됩니다.")

    chapter_title = st.text_input("회차 제목 (저장용 파일명)", value="제 2화: 얼음의 숲에서")
    user_instruction = st.text_area(
        "이번 회차 전개 지시사항",
        value="레온과 세리아가 숲속에서 길을 잃고 몬스터와 처음 조우하는 장면을 긴장감 있게 써줘. 세리아가 마법을 쓰려다 실수하는 장면 포함할 것.",
        height=150,
    )
    target_length = st.number_input(
        "생성 분량(글자 수) 목표치",
        min_value=500,
        max_value=20000,
        value=5000,
        step=500,
        help="원하는 글자수를 지정하세요. AI가 사건의 묘사나 대화를 조절하여 이 분량을 맞추려 노력합니다.",
    )
    use_plot = st.checkbox("📌 저장된 대형 플롯을 이번 회차 생성에 반영", value=False)
    plot_strength = st.selectbox(
        "플롯 반영 강도",
        options=["loose", "balanced", "strict"],
        index=1,
        disabled=not use_plot,
        help="loose: 느슨하게 참고 / balanced: 권장 / strict: 플롯 우선",
    )

    col1, col2 = st.columns([1, 2])
    with col1:
        generate_btn = st.button("원고 초안 생성하기", type="primary")
    with col2:
        if st.button("📂 저장폴더 열기", key="open_folder_1"):
            safe_open_folder(generator.chapters_dir)

    if generate_btn:
        if not is_llm_ready():
            pass
        elif not user_instruction.strip():
            st.warning("지시사항을 입력해 주세요.")
        else:
            with st.spinner(f"작가가 원고를 집필 중입니다 (목표: {target_length}자 내외)... ☕"):
                try:
                    draft = generator.create_chapter(
                        user_instruction,
                        target_length,
                        include_plot=use_plot,
                        plot_strength=plot_strength,
                    )
                    st.session_state['current_draft'] = draft
                    st.session_state['current_title'] = chapter_title
                    if 'edited_draft' in st.session_state:
                        del st.session_state['edited_draft']
                    st.success("초안 생성이 완료되었습니다!")
                except LLMError as e:
                    st.error(f"초안 생성 실패: {e}")
                except Exception as e:
                    st.error(f"초안 생성 중 알 수 없는 오류: {e}")

    if 'current_draft' in st.session_state:
        st.divider()
        st.subheader("생성된 문서 초안")
        st.text_area("수정 가능한 초안", value=st.session_state['current_draft'], height=400, key="edited_draft")

        col1, col2 = st.columns([1, 2])
        with col1:
            save_draft_btn = st.button("현재 상태로 파일 저장 (마크다운)")
        with col2:
            if st.button("📂 저장폴더 열기", key="open_folder_2"):
                safe_open_folder(generator.chapters_dir)

        if save_draft_btn:
            saved_path = generator.save_chapter(st.session_state['current_title'], st.session_state['edited_draft'])
            st.success(f"파일이 저장되었습니다: `{saved_path}`")


def render_tab_review(generator, reviewer, safe_open_folder):
    st.header("편집자 검수 보고서")
    st.markdown("생성된 원고가 세계관과 충돌하지 않는지, 어색한 문맥은 없는지 PD의 시선으로 검토합니다.")

    saved_files = []
    if generator.chapters_dir.exists():
        saved_files = [f.name for f in generator.chapters_dir.iterdir() if f.is_file() and f.suffix == '.md']

    selected_file = st.selectbox("📂 검수할 원고 파일 선택", options=["새로 생성된 초안 사용"] + saved_files)

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
        edited_draft_to_review = st.text_area("이 내용을 바탕으로 편집자에게 검수를 요청합니다.", value=draft_to_review, height=300)

        if st.button("현재 원고 검토 요청", type="primary"):
            with st.spinner("편집자가 원고를 꼼꼼히 읽고 있습니다... 👓"):
                try:
                    report = reviewer.review_chapter(edited_draft_to_review)
                    st.session_state['review_report'] = report
                    st.session_state['reviewing_draft'] = edited_draft_to_review
                    st.session_state['reviewing_title'] = review_title
                except LLMError as e:
                    st.error(f"검수 요청 실패: {e}")
                except Exception as e:
                    st.error(f"검수 중 알 수 없는 오류: {e}")

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
                with open(report_path, "w", encoding="utf-8") as f:
                    f.write(st.session_state['review_report'])
                st.success(f"리포트가 저장되었습니다: `{report_path}`")
        with col_r2:
            if st.button("📂 저장폴더 열기", key="open_folder_report"):
                safe_open_folder(generator.chapters_dir)

        st.divider()
        st.subheader("리포트 피드백 반영")
        if st.button("✨ 리포트 피드백을 반영하여 초안 자동 수정", type="primary"):
            with st.spinner("작가가 피드백을 반영하여 원고를 수정하고 있습니다... ✍️"):
                try:
                    revised = reviewer.revise_draft(st.session_state.get('reviewing_draft', draft_to_review), st.session_state['review_report'])
                    st.session_state['revised_draft'] = revised
                    if 'edited_revised_draft' in st.session_state:
                        del st.session_state['edited_revised_draft']
                    st.success("수정본 작성이 완료되었습니다!")
                except LLMError as e:
                    st.error(f"수정본 생성 실패: {e}")
                except Exception as e:
                    st.error(f"수정본 생성 중 알 수 없는 오류: {e}")

    if 'revised_draft' in st.session_state:
        st.divider()
        st.subheader("✨ 피드백이 반영된 수정본")
        st.text_area("수정 가능한 최종본", value=st.session_state['revised_draft'], height=400, key="edited_revised_draft")

        col1, col2 = st.columns([1, 2])
        with col1:
            save_revised_btn = st.button("수정본 파일 저장 (마크다운)")
        with col2:
            if st.button("📂 저장폴더 열기", key="open_folder_3"):
                safe_open_folder(generator.chapters_dir)

        if save_revised_btn:
            base_title = st.session_state.get('reviewing_title', "수정된_원고")
            saved_path = generator.save_chapter(base_title + "_수정본", st.session_state['edited_revised_draft'])
            st.success(f"수정본 파일이 저장되었습니다: `{saved_path}`")

            with st.spinner("다음 회차를 위해 방금 저장한 내용을 컨텍스트에 요약하여 반영 중입니다 (필요시 자동 압축 🔄)..."):
                try:
                    new_summary = generator.summarize_chapter(st.session_state['edited_revised_draft'])
                    generator.ctx.update_summary(new_summary, generator_instance=generator)
                    st.success("다음 회차를 위한 설정 갱신(이전 줄거리 요약 자동 추가/압축)이 완료되었습니다!")
                except LLMError as e:
                    st.error(f"요약 갱신 실패: {e}")
                except Exception as e:
                    st.error(f"요약 갱신 중 알 수 없는 오류: {e}")
