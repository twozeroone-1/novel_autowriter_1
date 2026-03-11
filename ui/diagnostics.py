import streamlit as st

from core.diagnostics import build_recent_summary, load_recent_llm_runs


def format_sidebar_summary(summary: dict) -> str:
    latest_backend = summary.get("latest_backend") or "-"
    return f"24h {summary.get('run_count', 0)} runs / {summary.get('failure_count', 0)} failed / last {latest_backend}"


def filter_runs(
    runs: list[dict],
    *,
    success_filter: str = "all",
    requested_backend: str = "all",
    actual_backend: str = "all",
    model_name: str = "all",
) -> list[dict]:
    filtered: list[dict] = []
    for run in runs:
        if success_filter == "failed" and run.get("success", False):
            continue
        if success_filter == "success" and not run.get("success", False):
            continue
        if requested_backend != "all" and run.get("requested_backend") != requested_backend:
            continue
        if actual_backend != "all" and run.get("actual_backend") != actual_backend:
            continue
        if model_name != "all" and run.get("model") != model_name:
            continue
        filtered.append(run)
    return filtered


def build_detail_rows(records: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for record in records:
        rows.append(
            {
                **record,
                "status": "success" if record.get("success") else "failed",
            }
        )
    return rows


def get_diagnostics_warning_text() -> str:
    return "This panel may contain sensitive prompt and response text. Open raw details only when needed."


def get_sidebar_summary(project_name: str) -> dict:
    return build_recent_summary(load_recent_llm_runs(project_name))


def render_diagnostics_panel(project_name: str) -> None:
    records = load_recent_llm_runs(project_name)
    summary = build_recent_summary(records)

    with st.expander("Advanced: diagnostics / run history", expanded=False):
        st.warning(get_diagnostics_warning_text())
        st.caption(format_sidebar_summary(summary))

        success_filter = st.selectbox("Result", ["all", "success", "failed"], key="diag_success_filter")
        requested_backend = st.selectbox(
            "Requested backend",
            ["all"] + sorted({record.get("requested_backend") for record in records if record.get("requested_backend")}),
            key="diag_requested_backend",
        )
        actual_backend = st.selectbox(
            "Actual backend",
            ["all"] + sorted({record.get("actual_backend") for record in records if record.get("actual_backend")}),
            key="diag_actual_backend",
        )
        model_name = st.selectbox(
            "Model",
            ["all"] + sorted({record.get("model") for record in records if record.get("model")}),
            key="diag_model_name",
        )

        filtered_records = filter_runs(
            records,
            success_filter=success_filter,
            requested_backend=requested_backend,
            actual_backend=actual_backend,
            model_name=model_name,
        )

        if not filtered_records:
            st.caption("No diagnostics records in the last 24 hours.")
            return

        for index, row in enumerate(build_detail_rows(filtered_records)):
            label = (
                f"{row.get('timestamp', '-')}"
                f" | {row.get('feature', '-')}"
                f" | {row.get('status', '-')}"
                f" | {row.get('actual_backend', '-')}"
                f" | {row.get('model', '-')}"
                f" | {row.get('duration_ms', 0)} ms"
            )
            with st.expander(label, expanded=False):
                st.text_area("Prompt", value=row.get("prompt_text", ""), height=160, key=f"diag_prompt_{index}")
                st.text_area("Response", value=row.get("response_text", ""), height=160, key=f"diag_response_{index}")
                st.text_area("stderr", value=row.get("stderr_text", ""), height=100, key=f"diag_stderr_{index}")
                st.text_area("Error", value=row.get("error_text", ""), height=100, key=f"diag_error_{index}")
                st.text_area(
                    "Fallback note",
                    value=row.get("fallback_note", ""),
                    height=80,
                    key=f"diag_fallback_{index}",
                )
