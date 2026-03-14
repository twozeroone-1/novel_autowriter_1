from core.context import ContextManager
from core.llm import generate_text


class Reviewer:
    def __init__(self, project_name: str = "default_project"):
        self.ctx = ContextManager(project_name=project_name)

    def _build_plot_block(self, *, include_plot: bool = False, plot_strength: str = "balanced") -> str:
        plot_outline = self.ctx.get_plot_outline()
        if not include_plot or not plot_outline:
            return ""

        return f"""
[PLOT OUTLINE] (long-range plot guide)
{plot_outline}

[PLOT STRENGTH]
{plot_strength}
"""

    def review_chapter(
        self,
        draft_content: str,
        include_plot: bool = False,
        plot_strength: str = "balanced",
    ) -> str:
        """Review the draft against project context and optional long-range plot."""

        world_ctx = self.ctx.get_worldview_context()
        char_ctx = self.ctx.get_character_context()
        continuity_ctx = self.ctx.get_continuity_context()
        state_ctx = self.ctx.get_state_context()
        plot_block = self._build_plot_block(include_plot=include_plot, plot_strength=plot_strength)

        prompt = f"""You are a web novel editor and review lead.
Review the draft against the project context below and produce a practical report.

{world_ctx}
{continuity_ctx}
{state_ctx}

{char_ctx}
{plot_block}

[DRAFT]
{draft_content}

[REVIEW CHECKLIST]
1. Setting/canon conflicts: character traits, speaking style, worldview rules, fixed continuity.
2. Narrative flow: whether it connects naturally from prior events and whether scene progression is coherent.
3. Prose issues: awkward sentences, repetitive phrasing, unclear wording, or broken rhythm.
4. Plot alignment: when a plot outline is provided, point out if the chapter drifts too far from it.

Write a clear report and include concrete revision guidance where needed.
"""
        print(">> Generating review report...")
        result = generate_text(
            prompt,
            system_instruction="You are a rigorous fiction editor who gives concrete, actionable feedback.",
            project_name=self.ctx.project_name,
            feature="review",
        )
        return result

    def revise_draft(
        self,
        draft_content: str,
        review_report: str,
        include_plot: bool = False,
        plot_strength: str = "balanced",
    ) -> str:
        """Revise the draft using the review report and optional long-range plot."""

        world_ctx = self.ctx.get_worldview_context()
        char_ctx = self.ctx.get_character_context()
        continuity_ctx = self.ctx.get_continuity_context()
        state_ctx = self.ctx.get_state_context()
        plot_block = self._build_plot_block(include_plot=include_plot, plot_strength=plot_strength)

        prompt = f"""You are revising a web novel draft based on an editorial review.
Keep the draft natural while fixing issues raised in the review.

{world_ctx}
{continuity_ctx}
{state_ctx}

{char_ctx}
{plot_block}

[DRAFT]
{draft_content}

[REVIEW REPORT]
{review_report}

Revise the draft so it resolves continuity, narrative flow, prose, and plot-alignment issues.
Return only the revised body text without a title.
"""
        print(">> Generating revised draft...")
        result = generate_text(
            prompt,
            system_instruction="You are a skilled fiction writer who can revise drafts cleanly from editorial notes.",
            project_name=self.ctx.project_name,
            feature="revise",
        )
        return result
