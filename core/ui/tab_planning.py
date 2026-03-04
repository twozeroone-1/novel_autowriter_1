import streamlit as st

from core.llm import LLMError


def render_tab_ideas(planner, is_llm_ready):
    st.header("💡 아이디어/제목 추천")
    st.markdown("플랫폼 트렌드와 관심 키워드를 바탕으로 웹소설 아이디어와 제목 후보를 생성합니다.")
    idea_platform = st.text_input("플랫폼", value="문피아, 카카오페이지, 노벨피아, 네이버시리즈", key="idea_platform")
    idea_keywords = st.text_input("관심 키워드(쉼표 구분)", value="회귀, 아카데미, 성장, 코미디", key="idea_keywords")
    idea_tone = st.selectbox("원하는 톤", ["가볍고 팝한", "다크하고 강한", "정통 판타지"], index=0, key="idea_tone")
    if st.button("✨ 아이디어/제목 생성", type="primary", use_container_width=True, key="btn_idea_gen"):
        if not is_llm_ready():
            pass
        else:
            with st.spinner("트렌드 기반 아이디어를 생성 중입니다..."):
                try:
                    result = planner.suggest_ideas(
                        platform_name=idea_platform,
                        user_keywords=idea_keywords,
                        tone=idea_tone,
                    )
                    st.session_state["idea_result"] = result
                except LLMError as e:
                    st.error(f"아이디어 생성 실패: {e}")
                except Exception as e:
                    st.error(f"아이디어 생성 중 알 수 없는 오류: {e}")
    if st.session_state.get("idea_result"):
        st.text_area("추천 결과", value=st.session_state["idea_result"], height=360, key="idea_result_view")


def render_tab_plot(generator, planner, is_llm_ready):
    st.header("🧭 대형 플롯 설계")
    st.markdown("300화 장편 기준으로 30화 단위 대사건을 포함한 플롯을 생성하고 저장합니다.")
    p1, p2 = st.columns(2)
    with p1:
        plot_platform = st.text_input("플랫폼", value="노벨피아", key="plot_platform")
        plot_title = st.text_input("작품 제목", value="망한 아카데미에서 살아남는 법", key="plot_title")
        phase1_focus = st.text_area("1~100화 중점", value="독자 어그로용 떡밥과 장르 정착", height=90, key="plot_phase1")
    with p2:
        phase2_focus = st.text_area("101~200화 중점", value="무한반복 쌀먹 패턴 떡밥 회수 및 확장", height=90, key="plot_phase2")
        phase3_focus = st.text_area("201~300화 중점", value="세계관 비밀 공개와 대단원", height=90, key="plot_phase3")
    if st.button("🧠 대형 플롯 생성", type="primary", use_container_width=True, key="btn_plot_gen"):
        if not is_llm_ready():
            pass
        elif not plot_title.strip():
            st.warning("제목을 입력해 주세요.")
        else:
            with st.spinner("플롯을 설계 중입니다..."):
                try:
                    result = planner.build_macro_plot(
                        platform_name=plot_platform,
                        title=plot_title,
                        phase1_focus=phase1_focus,
                        phase2_focus=phase2_focus,
                        phase3_focus=phase3_focus,
                        total_episodes=300,
                    )
                    st.session_state["plot_result"] = result
                except LLMError as e:
                    st.error(f"플롯 생성 실패: {e}")
                except Exception as e:
                    st.error(f"플롯 생성 중 알 수 없는 오류: {e}")
    if st.session_state.get("plot_result"):
        st.text_area("플롯 결과", value=st.session_state["plot_result"], height=360, key="plot_result_view")
        c_plot1, c_plot2 = st.columns(2)
        with c_plot1:
            if st.button("💾 플롯을 프로젝트 설정에 저장", use_container_width=True, key="btn_plot_save"):
                generator.ctx.save_plot_outline(st.session_state["plot_result"])
                st.success("플롯이 저장되었습니다. [2] 회차 생성에서 선택 반영할 수 있습니다.")
        with c_plot2:
            if st.button("📥 저장된 플롯 불러오기", use_container_width=True, key="btn_plot_load"):
                saved_plot = generator.ctx.get_plot_outline()
                if saved_plot:
                    st.session_state["plot_result"] = saved_plot
                    st.success("저장된 플롯을 불러왔습니다.")
                else:
                    st.info("저장된 플롯이 없습니다.")
