import json
import os
import re
import shutil
from dataclasses import dataclass
from typing import Any, Callable

import streamlit as st
from dotenv import load_dotenv

from core.api_key_store import (
    delete_api_key_from_secure_storage,
    env_file_has_key,
    get_secure_api_key,
    has_secure_storage,
    save_api_key_to_secure_storage,
    set_runtime_api_key,
)
from core.app_paths import DATA_PROJECTS_DIR
from core.generator import Generator
from core.llm import LLMError
from core.model_catalog import get_available_models
from core.token_budget import get_budget_recommendations, get_field_stats


@dataclass(frozen=True)
class TextAssistAction:
    label: str
    button_key: str
    empty_warning: str
    spinner_text: str
    error_prefix: str
    notice: str
    transform: Callable[[str], str]


@dataclass(frozen=True)
class ProjectFieldSpec:
    section_title: str
    subtitle: str
    guide_text: str
    input_label: str
    config_key: str
    textarea_key: str
    height: int
    actions: tuple[TextAssistAction, ...]


@dataclass(frozen=True)
class ProjectFieldPanel:
    spec: ProjectFieldSpec
    char_count: int
    recommended_max_chars: int
    status: str
    tip: str
    expander_label: str
    preview_text: str
    expanded: bool


def render_section_header(title: str, subtitle: str, guide_text: str) -> None:
    st.subheader(title)
    subtitle_col, guide_col = st.columns([3, 2])
    with subtitle_col:
        st.caption(subtitle)
    with guide_col:
        st.caption(f"권장 길이: {guide_text}")


def build_project_field_specs(generator: Generator) -> tuple[ProjectFieldSpec, ProjectFieldSpec, ProjectFieldSpec, ProjectFieldSpec]:
    return (
        ProjectFieldSpec(
            section_title="1. STORY BIBLE",
            subtitle="세계관과 연재 목표",
            guide_text="700~1500자",
            input_label="세계관, 배경, 핵심 인물 전제, 연재 목표를 정리하세요",
            config_key="worldview",
            textarea_key="ta_worldview",
            height=250,
            actions=(
                TextAssistAction(
                    label="STORY_BIBLE 구체화",
                    button_key="assist_worldview_expand",
                    empty_warning="먼저 STORY BIBLE 초안을 적어 주세요.",
                    spinner_text="AI가 STORY BIBLE을 더 구체적으로 다듬는 중입니다...",
                    error_prefix="STORY BIBLE 구체화 중 오류가 발생했습니다",
                    notice="STORY BIBLE 구체화 내용을 반영했습니다.",
                    transform=generator.elaborate_worldview,
                ),
                TextAssistAction(
                    label="STORY_BIBLE 압축",
                    button_key="assist_worldview_compress",
                    empty_warning="압축할 STORY BIBLE 내용이 없습니다.",
                    spinner_text="AI가 STORY BIBLE을 핵심만 남기도록 압축하는 중입니다...",
                    error_prefix="STORY BIBLE 압축 중 오류가 발생했습니다",
                    notice="STORY BIBLE 압축 내용을 반영했습니다.",
                    transform=generator.compress_worldview,
                ),
            ),
        ),
        ProjectFieldSpec(
            section_title="2. STYLE GUIDE",
            subtitle="문체와 서술 규칙",
            guide_text="200~600자",
            input_label="시점, 문장 길이, 대사 비중, 금지 표현 등을 정리하세요",
            config_key="tone_and_manner",
            textarea_key="ta_tone",
            height=250,
            actions=(
                TextAssistAction(
                    label="STYLE_GUIDE 정리",
                    button_key="assist_tone_structure",
                    empty_warning="먼저 STYLE GUIDE 초안을 적어 주세요.",
                    spinner_text="AI가 STYLE GUIDE를 규칙 목록으로 정리하는 중입니다...",
                    error_prefix="STYLE GUIDE 정리 중 오류가 발생했습니다",
                    notice="STYLE GUIDE 정리 내용을 반영했습니다.",
                    transform=generator.structure_style_guide,
                ),
            ),
        ),
        ProjectFieldSpec(
            section_title="3. CONTINUITY",
            subtitle="고정 설정과 관계도",
            guide_text="300~900자",
            input_label="절대 바뀌면 안 되는 룰, 지명, 관계도, 고정 설정을 적어 주세요",
            config_key="continuity",
            textarea_key="ta_continuity",
            height=250,
            actions=(
                TextAssistAction(
                    label="CONTINUITY 정리",
                    button_key="assist_continuity_structure",
                    empty_warning="먼저 CONTINUITY 초안을 적어 주세요.",
                    spinner_text="AI가 CONTINUITY를 고정 설정 문서로 정리하는 중입니다...",
                    error_prefix="CONTINUITY 정리 중 오류가 발생했습니다",
                    notice="CONTINUITY 정리 내용을 반영했습니다.",
                    transform=generator.structure_continuity,
                ),
            ),
        ),
        ProjectFieldSpec(
            section_title="4. STATE",
            subtitle="현재 상황과 감정선",
            guide_text="150~500자",
            input_label="직전 사건, 미해결 갈등, 현재 감정선과 다음 목표를 적어 주세요",
            config_key="state",
            textarea_key="ta_state",
            height=250,
            actions=(
                TextAssistAction(
                    label="STATE 요약",
                    button_key="assist_state_summarize",
                    empty_warning="먼저 STATE 초안을 적어 주세요.",
                    spinner_text="AI가 STATE를 현재 상황 중심으로 정리하는 중입니다...",
                    error_prefix="STATE 요약 중 오류가 발생했습니다",
                    notice="STATE 요약 내용을 반영했습니다.",
                    transform=generator.summarize_state,
                ),
            ),
        ),
    )


def summarize_text_preview(text: str, *, max_chars: int = 90, empty_fallback: str = "아직 작성되지 않았습니다.") -> str:
    normalized = " ".join(line.strip() for line in str(text).splitlines() if line.strip())
    normalized = re.sub(r"[#*_`]+", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if not normalized:
        return empty_fallback
    if len(normalized) <= max_chars:
        return normalized
    return f"{normalized[:max_chars].rstrip()}..."


def build_project_field_panels(
    specs: tuple[ProjectFieldSpec, ...],
    field_stats: list[dict],
    config: dict,
) -> tuple[ProjectFieldPanel, ...]:
    stats_by_key = {row["key"]: row for row in field_stats}
    pending_panels: list[dict[str, Any]] = []
    first_attention_index: int | None = None

    for index, spec in enumerate(specs):
        row = stats_by_key[spec.config_key]
        preview_text = summarize_text_preview(config.get(spec.config_key, ""))

        needs_attention = row["status"] != "적정"
        if needs_attention and first_attention_index is None:
            first_attention_index = index

        pending_panels.append(
            {
                "spec": spec,
                "char_count": row["chars"],
                "recommended_max_chars": row["recommended_max_chars"],
                "status": row["status"],
                "tip": row["tip"],
                "expander_label": f"{spec.section_title} · {row['chars']:,}자 · {row['status']}",
                "preview_text": preview_text,
            }
        )

    return tuple(
        ProjectFieldPanel(
            spec=item["spec"],
            char_count=item["char_count"],
            recommended_max_chars=item["recommended_max_chars"],
            status=item["status"],
            tip=item["tip"],
            expander_label=item["expander_label"],
            preview_text=item["preview_text"],
            expanded=first_attention_index == index if first_attention_index is not None else False,
        )
        for index, item in enumerate(pending_panels)
    )


def maybe_apply_text_assist(
    generator: Generator,
    config: dict,
    *,
    source_text: str,
    config_key: str,
    textarea_key: str,
    action: TextAssistAction,
    ensure_api_key: Callable[[], bool],
    run_with_status: Callable[..., Any],
) -> None:
    if not st.button(action.label, key=action.button_key, use_container_width=True):
        return
    if not source_text.strip():
        st.warning(action.empty_warning)
        return
    if not ensure_api_key():
        return

    transformed_text = run_with_status(
        lambda: action.transform(source_text),
        action.spinner_text,
        error_prefix=action.error_prefix,
    )
    if transformed_text is None:
        return

    config[config_key] = transformed_text
    generator.ctx.save_config(config)
    st.session_state["_pending_project_textarea_reset"] = textarea_key
    st.session_state["_pending_project_notice"] = action.notice
    st.rerun()


def render_project_text_field(
    generator: Generator,
    config: dict,
    panel: ProjectFieldPanel,
    *,
    ensure_api_key: Callable[[], bool],
    run_with_status: Callable[..., Any],
) -> str:
    spec = panel.spec
    with st.expander(panel.expander_label, expanded=panel.expanded):
        st.caption(f"{spec.subtitle} · 권장 {panel.recommended_max_chars:,}자")
        st.caption(f"현재 요약: {panel.preview_text}")
        if panel.status != "적정":
            st.info(panel.tip)

        field_text = st.text_area(
            spec.input_label,
            value=config.get(spec.config_key, ""),
            height=spec.height,
            key=spec.textarea_key,
        )

        if spec.actions:
            button_cols = st.columns(len(spec.actions))
            for col, action in zip(button_cols, spec.actions):
                with col:
                    maybe_apply_text_assist(
                        generator,
                        config,
                        source_text=field_text,
                        config_key=spec.config_key,
                        textarea_key=spec.textarea_key,
                        action=action,
                        ensure_api_key=ensure_api_key,
                        run_with_status=run_with_status,
                    )

        return field_text


def render_character_management_panel(generator: Generator, config: dict) -> None:
    with st.expander("등장인물 JSON 관리", expanded=False):
        st.markdown("### 1. AI로 주요 등장인물 추출")
        st.info("STORY BIBLE, CONTINUITY, STATE, 이전 줄거리 요약을 바탕으로 주요 캐릭터를 자동 추출합니다.")

        if st.button("설정 문서 기반으로 등장인물 자동 추출", type="primary", use_container_width=True):
            has_source = any(
                config.get(field, "").strip()
                for field in ("worldview", "continuity", "state", "summary_of_previous")
            )
            if not has_source:
                st.warning("먼저 STORY BIBLE, CONTINUITY, STATE 중 하나 이상을 채워 주세요.")
            else:
                with st.spinner("AI가 등장인물을 추출하는 중입니다..."):
                    try:
                        extracted_json_str = generator.generate_characters(
                            worldview=config.get("worldview", ""),
                            continuity=config.get("continuity", ""),
                            state=config.get("state", ""),
                            summary_of_previous=config.get("summary_of_previous", ""),
                        )
                        parsed_chars = json.loads(extracted_json_str)
                        generator.ctx.save_characters(parsed_chars)
                        st.success("등장인물을 저장했습니다.")
                        st.rerun()
                    except json.JSONDecodeError:
                        st.error("AI 응답에서 올바른 JSON 배열을 추출하지 못했습니다.")
                        st.code(extracted_json_str)
                    except ValueError as exc:
                        st.error(f"등장인물 형식이 올바르지 않습니다: {exc}")
                    except LLMError as exc:
                        st.error(f"등장인물 추출 중 오류가 발생했습니다: {exc}")
                    except Exception as exc:
                        st.error(f"등장인물 추출 중 예기치 못한 오류가 발생했습니다: {exc}")

        st.divider()
        st.markdown("### 2. 수동 편집")
        st.info("필요하면 JSON을 직접 수정해서 저장할 수 있습니다.")

        characters = generator.ctx.get_characters()
        char_json_str = json.dumps(characters, ensure_ascii=False, indent=4) if characters else "[]"
        chars_text = st.text_area("현재 등장인물 JSON", value=char_json_str, height=320)

        if st.button("등장인물 저장", key="save_char"):
            try:
                parsed_chars = json.loads(chars_text)
                generator.ctx.save_characters(parsed_chars)
                st.success("등장인물 정보를 저장했습니다.")
            except json.JSONDecodeError:
                st.error("JSON 문법을 확인해 주세요.")
            except ValueError as exc:
                st.error(f"등장인물 형식 오류입니다: {exc}")
            except Exception as exc:
                st.error(f"알 수 없는 오류가 발생했습니다: {exc}")


def render_sidebar(
    *,
    normalize_project_name: Callable[[str], tuple[str | None, str | None]],
    get_project_list: Callable[[], list[str]],
    clear_project_state: Callable[[], None],
    get_cached_generator: Callable[[str], Generator],
    load_project_textareas: Callable[[dict], None],
    clear_cached_resources: Callable[[], None],
    set_env_variable: Callable[[str, str], None],
) -> str:
    with st.sidebar:
        st.header("작품 관리")

        new_project_name = st.text_input(
            "새 작품 이름",
            placeholder="예: 회귀 아카데미 판타지",
            help="공백을 써도 됩니다. 연속된 공백은 하나로 정리됩니다.",
        )
        if st.button("새 작품 추가", use_container_width=True):
            project_name, project_name_error = normalize_project_name(new_project_name)
            if project_name_error:
                st.error(project_name_error)
            else:
                target_dir = DATA_PROJECTS_DIR / project_name
                if target_dir.exists():
                    st.error("이미 존재하는 작품 이름입니다.")
                else:
                    Generator(project_name=project_name)
                    clear_project_state()
                    st.session_state["current_project"] = project_name
                    st.success(f"'{project_name}' 작품을 만들었습니다.")
                    st.rerun()

        st.divider()

        projects = get_project_list()
        if not projects:
            st.warning("저장된 작품이 없습니다. 먼저 작품을 만들어 주세요.")
            st.stop()

        current_project = st.session_state.get("current_project")
        if current_project not in projects:
            st.session_state["current_project"] = projects[0]

        selected_project = st.selectbox(
            "현재 작업 작품",
            options=projects,
            index=projects.index(st.session_state["current_project"]),
        )
        if selected_project != st.session_state["current_project"]:
            clear_project_state()
            st.session_state["current_project"] = selected_project
            temp_generator = get_cached_generator(selected_project)
            load_project_textareas(temp_generator.ctx.get_config())
            st.rerun()

        with st.expander("현재 작품 삭제", expanded=False):
            current_project_name = st.session_state["current_project"]
            st.warning(f"정말 '{current_project_name}' 작품을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.")
            delete_confirmation = st.text_input(
                "확인용으로 작품 이름을 다시 입력해 주세요.",
                key="delete_project_confirm",
                placeholder=current_project_name,
            )
            delete_disabled = delete_confirmation.strip() != current_project_name
            if st.button("작품 삭제", type="primary", use_container_width=True, disabled=delete_disabled):
                target_dir = DATA_PROJECTS_DIR / current_project_name
                try:
                    shutil.rmtree(target_dir)
                    clear_cached_resources()
                    clear_project_state()
                    st.session_state.pop("delete_project_confirm", None)
                    st.session_state.pop("current_project", None)

                    remaining_projects = get_project_list()
                    if remaining_projects:
                        st.session_state["current_project"] = remaining_projects[0]

                    st.success(f"'{current_project_name}' 작품을 삭제했습니다.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"작품 삭제 중 오류가 발생했습니다: {exc}")

        runtime_api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        secure_storage_available = has_secure_storage()
        secure_api_key_exists = bool(get_secure_api_key())
        plain_env_key_exists = env_file_has_key()

        st.divider()
        if secure_api_key_exists:
            st.caption("API 상태: 보안 저장소 사용 중")
        elif runtime_api_key:
            st.caption("API 상태: 이번 실행에만 적용됨")
        else:
            st.caption("API 상태: 설정 안 됨")

        with st.expander("API / 모델 설정", expanded=False):
            if secure_api_key_exists:
                st.caption("보안 저장소에 API 키가 저장되어 있으며 앱 시작 시 자동 로드됩니다.")
            elif runtime_api_key:
                st.caption("현재 실행 환경에 API 키가 적용되어 있습니다.")
            else:
                st.caption("설정된 API 키가 없습니다.")

            if plain_env_key_exists:
                st.warning("`.env`에 평문 API 키가 남아 있습니다. 가능하면 보안 저장소로 옮기는 편이 안전합니다.")

            new_api_key = st.text_input(
                "Google API Key",
                value="",
                type="password",
                help="쉼표로 여러 키를 넣으면 순차적으로 fallback 됩니다.",
            )
            runtime_col, secure_col = st.columns(2)
            with runtime_col:
                if st.button("이번 실행에만 적용", use_container_width=True):
                    if new_api_key.strip():
                        set_runtime_api_key(new_api_key.strip())
                        st.success("API 키를 현재 실행에만 적용했습니다. 앱을 재시작하면 사라집니다.")
                        st.rerun()
            with secure_col:
                secure_button_disabled = not secure_storage_available
                if st.button("보안 저장소에 저장", use_container_width=True, disabled=secure_button_disabled):
                    ok, message = save_api_key_to_secure_storage(new_api_key.strip())
                    if ok:
                        load_dotenv(override=True)
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

            if not secure_storage_available:
                st.info("보안 저장소를 사용하려면 `keyring`이 필요합니다. 현재는 평문 저장 없이 런타임 적용만 가능합니다.")

            if secure_api_key_exists:
                if st.button("보안 저장소의 API 키 삭제", use_container_width=True):
                    ok, message = delete_api_key_from_secure_storage()
                    if ok:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

            with st.expander("고급: 평문 `.env` 저장", expanded=False):
                st.warning("이 옵션은 API 키를 프로젝트의 `.env` 파일에 평문으로 저장합니다.")
                if st.button("그래도 `.env`에 저장", use_container_width=True):
                    if new_api_key.strip():
                        set_env_variable("GOOGLE_API_KEY", new_api_key.strip())
                        load_dotenv(override=True)
                        st.success("API 키를 `.env`에 저장했습니다.")
                        st.rerun()

            current_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            available_models = get_available_models()
            selected_model = st.selectbox(
                "Gemini 모델",
                options=available_models,
                index=available_models.index(current_model) if current_model in available_models else 0,
            )
            if selected_model != current_model:
                set_env_variable("GEMINI_MODEL", selected_model)
                load_dotenv(override=True)
                st.success(f"기본 모델을 '{selected_model}'로 변경했습니다.")
                st.rerun()

            st.link_button(
                "토큰 사용량 보기",
                "https://aistudio.google.com/app/usage?timeRange=last-28-days",
                use_container_width=True,
            )

    return st.session_state["current_project"]


def render_project_settings_tab(
    app: Any,
    *,
    ensure_api_key: Callable[[], bool],
    run_with_status: Callable[..., Any],
) -> None:
    generator = app.generator

    pending_widget_reset = st.session_state.pop("_pending_project_textarea_reset", None)
    if pending_widget_reset:
        reset_keys = pending_widget_reset if isinstance(pending_widget_reset, list) else [pending_widget_reset]
        for widget_key in reset_keys:
            st.session_state.pop(widget_key, None)

    st.header("프로젝트 통합 설정")
    st.markdown(
        "네 가지 문서(`STORY_BIBLE`, `STYLE_GUIDE`, `CONTINUITY`, `STATE`)가 "
        "AI의 기본 입력으로 들어가며 작품의 고정 설정과 현재 상태를 결정합니다."
    )
    st.caption("AI 보조 버튼은 각 필드별로만 동작하므로 필요한 부분만 정리할 수 있습니다.")

    pending_project_notice = st.session_state.pop("_pending_project_notice", "")
    if pending_project_notice:
        st.success(pending_project_notice)

    config = generator.ctx.get_config()
    field_stats = get_field_stats(config)
    budget_recommendations = get_budget_recommendations(config)

    with st.expander("길이 가이드와 압축 팁", expanded=False):
        total_config_chars = sum(row["chars"] for row in field_stats)
        st.metric("설정 문서 총 글자 수", f"{total_config_chars:,}자")
        st.dataframe(
            [
                {
                    "문서": row["label"],
                    "현재 글자 수": row["chars"],
                    "권장 최대": row["recommended_max_chars"],
                    "상태": row["status"],
                }
                for row in field_stats
            ],
            use_container_width=True,
            hide_index=True,
        )
        for recommendation in budget_recommendations:
            st.write(f"- {recommendation}")

    specs = build_project_field_specs(generator)
    panels = build_project_field_panels(specs, field_stats, config)
    filled_count = sum(1 for panel in panels if panel.char_count > 0)
    attention_count = sum(1 for panel in panels if panel.status != "적정")
    total_config_chars = sum(panel.char_count for panel in panels)

    overview_col, attention_col, total_col = st.columns(3)
    with overview_col:
        st.metric("작성 완료", f"{filled_count}/4")
    with attention_col:
        st.metric("확인 필요", f"{attention_count}개")
    with total_col:
        st.metric("핵심 설정 글자 수", f"{total_config_chars:,}자")

    if attention_count:
        st.caption("비어 있거나 길이 조정이 필요한 문서는 자동으로 먼저 펼쳐집니다.")
    else:
        st.caption("모든 핵심 문서가 권장 길이 안에 있습니다. 필요한 문서만 펼쳐서 수정하면 됩니다.")

    field_values: dict[str, str] = {}
    for panel in panels:
        field_values[panel.spec.config_key] = render_project_text_field(
            generator,
            config,
            panel,
            ensure_api_key=ensure_api_key,
            run_with_status=run_with_status,
        )

    st.divider()
    save_col, info_col = st.columns([1, 4])
    with save_col:
        if st.button("4개 문서 저장", type="primary", use_container_width=True):
            config["worldview"] = field_values["worldview"]
            config["tone_and_manner"] = field_values["tone_and_manner"]
            config["continuity"] = field_values["continuity"]
            config["state"] = field_values["state"]
            generator.ctx.save_config(config)
            st.success("프로젝트 설정을 저장했습니다.")
    with info_col:
        st.info("필요한 문서만 저장해도 되지만, 네 문서를 같이 정리하면 생성 품질이 더 안정적입니다.")

    st.divider()
    summary_value = config.get("summary_of_previous", "")
    summary_chars = len(str(summary_value))
    summary_preview = summarize_text_preview(summary_value, max_chars=120, empty_fallback="아직 요약이 없습니다.")
    with st.expander(f"PREVIOUS SUMMARY · {summary_chars:,}자", expanded=summary_chars == 0):
        st.caption("이전 줄거리 요약 · 권장 400~1200자")
        st.caption(f"현재 요약: {summary_preview}")
        st.markdown("회차를 저장할 때 자동으로 갱신되지만, 필요하면 여기서 직접 수정할 수 있습니다.")
        summary_text = st.text_area(
            "이전 줄거리",
            value=summary_value,
            height=150,
        )
        if st.button("이전 줄거리 저장", key="save_sum"):
            config["summary_of_previous"] = summary_text
            generator.ctx.save_config(config)
            st.success("이전 줄거리를 저장했습니다.")

    st.divider()
    render_character_management_panel(generator, config)
