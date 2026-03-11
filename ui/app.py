import os
import re
from dataclasses import dataclass
import streamlit as st
from dotenv import load_dotenv

from core.api_key_store import load_secure_api_key_into_environment
from core.app_paths import DATA_PROJECTS_DIR, ENV_FILE_PATH
from core.automator import Automator
from core.file_utils import update_env_file
from core.generator import Generator
from core.planner import Planner
from core.reviewer import Reviewer
from ui.chapters import (
    ensure_api_key,
    render_auto_mode_tab,
    render_generation_tab,
    render_review_tab,
    run_with_status,
)
from ui.planning import (
    render_idea_tab as render_idea_tab_panel,
    render_plot_tab as render_plot_tab_panel,
)
from ui.workspace import (
    render_project_settings_tab as render_project_settings_tab_panel,
    render_sidebar as render_sidebar_panel,
)

st.set_page_config(page_title="AI 소설 스튜디오", page_icon="📚", layout="wide")

load_dotenv(override=True)
load_secure_api_key_into_environment()

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
    "gen_use_plot",
    "gen_plot_strength",
    "token_budget_report",
    "token_budget_error",
    "idea_platform",
    "idea_keywords",
    "idea_tone",
    "idea_result",
    "idea_result_view",
    "plot_platform",
    "plot_title",
    "plot_phase1",
    "plot_phase2",
    "plot_phase3",
    "plot_result",
    "plot_result_view",
    "delete_project_confirm",
]
HIDDEN_PROJECT_NAMES = {"default_project", "sample"}
PROJECT_NAME_PATTERN = re.compile(r"^[0-9A-Za-z\uAC00-\uD7A3 _-]{1,50}$")


def set_env_variable(key: str, value: str) -> None:
    update_env_file(ENV_FILE_PATH, key, value)
    os.environ[key] = value


def clear_project_state() -> None:
    for key in PROJECT_STATE_KEYS:
        st.session_state.pop(key, None)


def normalize_project_name(raw_name: str) -> tuple[str | None, str | None]:
    normalized = " ".join(raw_name.strip().split())
    if not normalized:
        return None, "작품 이름을 입력해 주세요."

    if normalized in HIDDEN_PROJECT_NAMES:
        return None, f"`{normalized}`는 예약된 이름입니다. 다른 이름을 사용해 주세요."

    if normalized in {".", ".."} or any(sep in normalized for sep in ("/", "\\", ":")):
        return None, "작품 이름에는 경로 문자(/, \\, :)와 `.` `..`를 사용할 수 없습니다."

    if not PROJECT_NAME_PATTERN.fullmatch(normalized):
        return None, "작품 이름에는 한글, 영문, 숫자, 공백, 밑줄(_), 하이픈(-)만 사용할 수 있습니다."

    return normalized, None


def get_project_list() -> list[str]:
    if not DATA_PROJECTS_DIR.exists():
        DATA_PROJECTS_DIR.mkdir(parents=True)
        return []
    projects = [
        path.name
        for path in DATA_PROJECTS_DIR.iterdir()
        if path.is_dir() and path.name not in HIDDEN_PROJECT_NAMES
    ]
    return sorted(projects, key=str.casefold)


@st.cache_resource(show_spinner=False)
def get_cached_generator(project_name: str) -> Generator:
    return Generator(project_name=project_name)


@st.cache_resource(show_spinner=False)
def get_cached_reviewer(project_name: str) -> Reviewer:
    return Reviewer(project_name=project_name)


def clear_cached_resources() -> None:
    get_cached_generator.clear()
    get_cached_reviewer.clear()


@dataclass(frozen=True)
class AppServices:
    generator: Generator
    reviewer: Reviewer
    automator: Automator
    planner: Planner
    config_path_hint: str
    chars_path_hint: str


def load_project_textareas(config: dict) -> None:
    st.session_state["ta_worldview"] = config.get("worldview", "여기에 세계관(STORY_BIBLE)을 작성해 주세요.")
    st.session_state["ta_tone"] = config.get("tone_and_manner", "여기에 문체(STYLE_GUIDE) 지침을 작성해 주세요.")
    st.session_state["ta_continuity"] = config.get("continuity", "여기에 변경 불가 규칙, 주요 표기, 관계도를 작성해 주세요.")
    st.session_state["ta_state"] = config.get("state", "여기에 현재 갈등, 감정선, 다음 목표를 작성해 주세요.")


def build_app_services(project_name: str) -> AppServices:
    generator = get_cached_generator(project_name)
    reviewer = get_cached_reviewer(project_name)
    automator = Automator(project_name=project_name, generator=generator, reviewer=reviewer)
    planner = Planner()
    return AppServices(
        generator=generator,
        reviewer=reviewer,
        automator=automator,
        planner=planner,
        config_path_hint=generator.ctx.config_path.as_posix(),
        chars_path_hint=generator.ctx.chars_path.as_posix(),
    )


def main() -> None:
    current_project = render_sidebar_panel(
        normalize_project_name=normalize_project_name,
        get_project_list=get_project_list,
        clear_project_state=clear_project_state,
        get_cached_generator=get_cached_generator,
        load_project_textareas=load_project_textareas,
        clear_cached_resources=clear_cached_resources,
        set_env_variable=set_env_variable,
    )

    app = build_app_services(current_project)

    st.title(f"AI 소설 스튜디오 - [{current_project}]")
    st.markdown("현재 선택한 작품 환경에서 설정 관리, 회차 생성, 검수, 아이디어와 플롯 설계를 진행합니다.")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "[1] 프로젝트 통합 설정",
            "[2] 회차 생성",
            "[3] 원고 검수",
            "[4] 반자동 연재 모드",
            "[5] 아이디어/제목",
            "[6] 대형 플롯",
        ]
    )

    with tab1:
        render_project_settings_tab_panel(
            app,
            ensure_api_key=ensure_api_key,
            run_with_status=run_with_status,
        )

    with tab2:
        render_generation_tab(app)

    with tab3:
        render_review_tab(app)

    with tab4:
        render_auto_mode_tab(app)

    with tab5:
        render_idea_tab_panel(
            app,
            ensure_api_key=ensure_api_key,
            run_with_status=run_with_status,
        )

    with tab6:
        render_plot_tab_panel(
            app,
            ensure_api_key=ensure_api_key,
            run_with_status=run_with_status,
        )


if __name__ == "__main__":
    main()

