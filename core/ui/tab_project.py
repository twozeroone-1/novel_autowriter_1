import json

import streamlit as st


def render_tab_project(generator, is_llm_ready):
    st.header("📚 프로젝트 통합 설정")
    st.markdown(
        "이곳에 적힌 네 가지 문서(`STORY_BIBLE`, `STYLE_GUIDE`, `CONTINUITY`, `STATE`)가 "
        "AI의 뇌 속으로 들어가 **절대 설정**과 **현재 상황**을 인식하게 만듭니다. 줄글 형식으로 자유롭게 편집하세요."
    )

    config = generator.ctx.get_config()

    c1, c2 = st.columns(2)

    if 'ta_worldview' not in st.session_state:
        st.session_state['ta_worldview'] = config.get("worldview", "")
    if 'ta_tone' not in st.session_state:
        st.session_state['ta_tone'] = config.get("tone_and_manner", "")
    if 'ta_continuity' not in st.session_state:
        st.session_state['ta_continuity'] = config.get("continuity", "")
    if 'ta_state' not in st.session_state:
        st.session_state['ta_state'] = config.get("state", "")

    with c1:
        st.subheader("1. STORY BIBLE (세계관 및 연재 목표)")
        worldview_text = st.text_area(
            "세계관, 기본 배경, 인물 설정, 연재 목표 (분량/수위) 등",
            height=250,
            key="ta_worldview",
        )

        st.subheader("2. STYLE GUIDE (문체 지침)")
        tone_text = st.text_area(
            "시점 변경 규칙, 장문/단문 비율, 대사 빈도, 금지 표현 등",
            height=250,
            key="ta_tone",
        )

    with c2:
        st.subheader("3. CONTINUITY (고정 설정 및 연표)")
        continuity_text = st.text_area(
            "🔒 절대 바꾸면 안 되는 룰, 나이/지명/연표, 인물 관계도 등",
            height=250,
            key="ta_continuity",
        )

        st.subheader("4. STATE (현재 상태 및 떡밥)")
        state_text = st.text_area(
            "🧩 최근 회차 기준, 미해결 떡밥, 터진 갈등 상황, 인물 감정선",
            height=250,
            key="ta_state",
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
            elif not is_llm_ready():
                pass
            else:
                with st.spinner("AI가 세계관에 살을 붙이고 있습니다... 🧠"):
                    try:
                        elaborated_text = generator.elaborate_worldview(worldview_text)
                        config["worldview"] = elaborated_text
                        generator.ctx.save_config(config)
                        del st.session_state['ta_worldview']
                        st.success("세계관 구체화 성공! 내용이 자동으로 변경되었습니다.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"구체화 중 오류가 발생했습니다: {e}")

    st.divider()
    st.subheader("📜 누적된 과거 줄거리 요약 (PREVIOUS SUMMARY)")
    st.markdown("이 부분은 회차가 생성되고 저장될 때마다 AI가 자동으로 3줄 요약하여 누적하는 곳입니다. 직접 수정하셔도 좋습니다.")
    summary_text = st.text_area("이전 줄거리 (시스템 자동 갱신 영역)", value=config.get("summary_of_previous", ""), height=150)
    if st.button("💾 줄거리 수동 저장", key="save_sum"):
        config["summary_of_previous"] = summary_text
        generator.ctx.save_config(config)
        st.success("이전 줄거리가 업데이트되었습니다.")

    st.divider()
    with st.expander("👥 등장인물 JSON 스키마 관리 (고급)"):
        st.markdown("### 1. 원터치 자동 추출 (AI 어시스턴트)")
        st.info("위 '1. STORY BIBLE'에 작성된 세계관을 바탕으로 AI가 주요 인물을 자동으로 분석하여 아래 JSON 양식으로 채워줍니다.")
        if st.button("✨ STORY BIBLE에서 모든 주요 등장인물 자동 추출", type="primary", use_container_width=True):
            if not config.get("worldview", "").strip():
                st.warning("위의 STORY BIBLE 입력창이 비어 있습니다. 먼저 세계관이나 등장인물을 대략적으로 적어주세요.")
            else:
                with st.spinner("AI가 세계관을 읽고 핵심 인물을 분석 중입니다... 🕵️"):
                    try:
                        extracted_json_str = generator.generate_characters(config["worldview"])
                        parsed_chars = json.loads(extracted_json_str)
                        generator.ctx.save_characters(parsed_chars)
                        st.success("캐릭터가 성공적으로 추출되어 저장되었습니다!")
                        st.rerun()
                    except json.JSONDecodeError:
                        st.error("AI가 올바른 JSON 형식을 반환하지 못했습니다. 다시 시도해 주세요.")
                        st.code(extracted_json_str)
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
            except Exception as e:
                st.error(f"알 수 없는 오류가 발생했습니다: {e}")
