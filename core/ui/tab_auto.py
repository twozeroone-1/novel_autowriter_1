import time

import streamlit as st


def render_tab_semi_auto(generator, automator, is_llm_ready):
    st.header("🤖 반자동 연재 모드 (Semi-Auto Mode)")
    st.markdown("클릭 한 번으로 초안 생성부터 검수, 수정, 다음 회차 설정 요약까지 일괄 처리합니다.")

    if 'auto_state' not in st.session_state:
        st.session_state['auto_state'] = 'READY'

    if st.session_state['auto_state'] == 'READY':
        st.info("다음 회차의 지시사항을 입력하고 파이프라인을 가동하세요.")
        st.text_input("회차 제목 (저장용 파일명)", value="제 3화: 새로운 여정", key="auto_title")
        auto_instruction = st.text_area(
            "이번 회차 전개 지시사항",
            value="주인공 일행이 마침내 동굴을 벗어나 거대한 도시의 입구에 도착하는 장면을 장엄하게 묘사해줘.",
            height=150,
            key="auto_inst",
        )
        st.number_input("생성 분량(글자 수) 목표치", min_value=500, max_value=20000, value=5000, step=500, key="auto_len")

        if st.button("🚀 자동 생성 파이프라인 가동", type="primary", use_container_width=True):
            if not is_llm_ready():
                pass
            elif not auto_instruction.strip():
                st.warning("지시사항을 입력해 주세요.")
            else:
                st.session_state['auto_state'] = 'RUNNING'
                st.rerun()

    elif st.session_state['auto_state'] == 'RUNNING':
        st.info("파이프라인이 실행 중입니다. 잠시만 기다려 주세요...")
        try:
            result = automator.run_single_cycle(
                st.session_state['auto_title'],
                st.session_state['auto_inst'],
                st.session_state['auto_len'],
            )
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

        with st.expander("📄 [결과] 최종 수정본 확인", expanded=False):
            st.text_area("수정본 (읽기 전용)", value=result.get('revised_draft', ''), height=400)
            st.info(f"💾 저장 위치: `{result.get('saved_path', '')}`")

        with st.expander("📝 [결과] 편집자 검수 리포트", expanded=False):
            st.markdown(result.get('review_report', ''))

        st.divider()
        st.subheader("⚙️ 다음 회차를 위한 설정(JSON) 갱신")
        st.markdown("방금 생성된 회차의 결과(새로운 인물 등장, 떡밥 회수 등)를 반영하여 아래 설정을 업데이트해 주세요.")

        current_config = generator.ctx.get_config()

        c1, c2 = st.columns(2)
        with c1:
            new_state = st.text_area(
                "🧩 CURRENT STATE 업데이트",
                value=current_config.get("state", ""),
                height=200,
                help="방금 회차를 통해 달라진 현재 상황이나 다음 회차로 이어질 단기 목표를 갱신하세요.",
            )
        with c2:
            new_summary = st.text_area(
                "📜 PREVIOUS SUMMARY (자동 갱신됨)",
                value=current_config.get("summary_of_previous", ""),
                height=200,
                help="AI가 방금 회차의 내용을 요약해 끝부분에 추가한 상태입니다. 필요 시 다듬어주세요.",
            )

        st.divider()
        if st.button("✅ 설정 저장 후 다음 회차 준비 (READY)", type="primary", use_container_width=True):
            current_config["state"] = new_state
            current_config["summary_of_previous"] = new_summary
            generator.ctx.save_config(current_config)

            st.session_state['auto_state'] = 'READY'
            if 'auto_title' in st.session_state:
                del st.session_state['auto_title']
            if 'auto_inst' in st.session_state:
                del st.session_state['auto_inst']

            st.success("설정이 저장되었습니다. 다음 회차를 준비합니다.")
            st.rerun()


def render_tab_full_auto(generator, automator, auto_state, is_llm_ready, get_next_auto_chapter_number):
    st.header("⏱️ 완전 자동화 연재 모드 (Auto Mode)")
    st.markdown("설정된 주기마다 AI가 상황과 요약을 스스로 판단하여 다음 회차를 끝없이 연재합니다.")
    status_snapshot = auto_state.read()
    st.caption(
        f"상태: {status_snapshot.get('last_status', 'IDLE')} | "
        f"누적 사이클: {status_snapshot.get('cycle_count', 0)}"
    )
    if status_snapshot.get("last_error"):
        st.warning(f"최근 오류: {status_snapshot['last_error']}")

    if 'fully_auto_running' not in st.session_state:
        st.session_state['fully_auto_running'] = False
    if 'auto_interval_minutes' not in st.session_state:
        st.session_state['auto_interval_minutes'] = 60
    if 'next_run_time' not in st.session_state:
        st.session_state['next_run_time'] = None
    if 'auto_target_length_full' not in st.session_state:
        st.session_state['auto_target_length_full'] = 5000

    c1, c2 = st.columns(2)
    with c1:
        interval_input = st.number_input(
            "연재 주기 (분 단위)",
            min_value=1,
            max_value=1440,
            value=st.session_state['auto_interval_minutes'],
            step=10,
            disabled=st.session_state['fully_auto_running'],
            help="예: 60분 간격으로 새 회차를 생성합니다.",
        )

    with c2:
        length_input = st.number_input(
            "생성 분량(글자 수) 목표치",
            min_value=500,
            max_value=20000,
            value=st.session_state['auto_target_length_full'],
            step=500,
            disabled=st.session_state['fully_auto_running'],
        )

    st.divider()
    e1, e2, e3 = st.columns(3)
    with e1:
        if st.button("🧯 강제 중지", use_container_width=True):
            st.session_state['fully_auto_running'] = False
            st.session_state['next_run_time'] = None
            auto_state.release_lock(force=True)
            auto_state.checkpoint(status="FORCE_STOPPED")
            st.success("강제 중지 완료")
            st.rerun()
    with e2:
        if st.button("🔓 락 해제", use_container_width=True):
            ok = auto_state.release_lock(force=True)
            if ok:
                st.success("락 해제 완료")
            else:
                st.warning("락 해제 실패")
    with e3:
        if st.button("♻️ 체크포인트 복구", use_container_width=True):
            snap = auto_state.read()
            next_run = int(snap.get("next_run_at", 0))
            if next_run > 0:
                lock_ok = auto_state.acquire_lock(st.session_state["auto_owner_id"])
                if not lock_ok:
                    st.error("다른 세션이 락을 보유 중이라 복구할 수 없습니다. 먼저 락 해제를 확인하세요.")
                else:
                    st.session_state['next_run_time'] = float(next_run)
                    st.session_state['fully_auto_running'] = True
                    auto_state.checkpoint(status="RUNNING", next_run_at=next_run)
                    st.success("체크포인트를 복구했습니다.")
                    st.rerun()
            else:
                st.info("복구 가능한 체크포인트가 없습니다.")

    col_start, col_stop = st.columns(2)
    with col_start:
        if not st.session_state['fully_auto_running']:
            if st.button("🚀 무한 자동 연재 시작", type="primary", use_container_width=True):
                if not is_llm_ready():
                    pass
                else:
                    lock_ok = auto_state.acquire_lock(st.session_state["auto_owner_id"])
                    if not lock_ok:
                        st.error("다른 세션이 자동 연재 락을 보유 중입니다. '락 해제' 후 다시 시도하세요.")
                        st.stop()
                    st.session_state['auto_interval_minutes'] = interval_input
                    st.session_state['auto_target_length_full'] = length_input
                    st.session_state['fully_auto_running'] = True
                    st.session_state['next_run_time'] = time.time() + 5
                    auto_state.checkpoint(
                        status="RUNNING",
                        next_run_at=int(st.session_state['next_run_time']),
                    )
                    st.rerun()
        else:
            st.button("🚀 무한 자동 연재 중...", type="primary", use_container_width=True, disabled=True)

    with col_stop:
        if st.session_state['fully_auto_running']:
            if st.button("🛑 자동 연재 중지", type="secondary", use_container_width=True):
                st.session_state['fully_auto_running'] = False
                st.session_state['next_run_time'] = None
                auto_state.release_lock(st.session_state["auto_owner_id"], force=False)
                auto_state.checkpoint(status="STOPPED")
                st.success("자동 연재가 중지되었습니다.")
                st.rerun()

    if st.session_state['fully_auto_running'] and st.session_state['next_run_time']:
        auto_state.refresh_lock(st.session_state["auto_owner_id"])
        now = time.time()
        remaining_seconds = int(st.session_state['next_run_time'] - now)

        if remaining_seconds > 0:
            mins, secs = divmod(remaining_seconds, 60)
            hours, mins = divmod(mins, 60)
            time_str = f"{hours:02d}:{mins:02d}:{secs:02d}"
            st.info(f"⏳ 다음 연재까지 남은 시간: **{time_str}**")
            time.sleep(1)
            st.rerun()
        else:
            st.warning("🔄 시간이 다 되었습니다! 다음 회차를 생성합니다...")
            next_chapter_num = get_next_auto_chapter_number(generator.chapters_dir)
            auto_title = f"[Auto] 제 {next_chapter_num}화"
            auto_instruction = "이전 연재의 STATE와 누적된 PREVIOUS SUMMARY의 사건 및 감정선을 그대로 이어받아, 흐름이 파탄나거나 모순되지 않게 전개해줘. 너무 급전개가 되지 않도록 하되, 이야기의 진행(새로운 갈등이나 떡밥 등장)은 반드시 포함될 것."

            try:
                auto_state.checkpoint(
                    status="RUNNING",
                    run_started=True,
                    next_run_at=int(st.session_state['next_run_time'] or 0),
                )
                automator.run_single_cycle(
                    auto_title,
                    auto_instruction,
                    st.session_state['auto_target_length_full'],
                )
                st.success(f"🎉 `{auto_title}` 생성이 완료되었습니다!")
                st.session_state['next_run_time'] = time.time() + (st.session_state['auto_interval_minutes'] * 60)
                auto_state.checkpoint(
                    status="RUNNING",
                    run_succeeded=True,
                    next_run_at=int(st.session_state['next_run_time']),
                )
                time.sleep(3)
                st.rerun()
            except Exception as e:
                st.error(f"자동 연재 중 심각한 오류가 발생했습니다: {e}")
                st.session_state['fully_auto_running'] = False
                st.session_state['next_run_time'] = None
                auto_state.release_lock(st.session_state["auto_owner_id"], force=True)
                auto_state.checkpoint(status="ERROR", error=str(e))
                st.button("에러 확인 후 수동 재시작", type="primary")
