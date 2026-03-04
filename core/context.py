import json
import os
import re
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional

# 전역 DATA_DIR 대신 프로젝트 기준 경로 지침
BASE_DATA_DIR = Path("data/projects")
PROJECT_NAME_PATTERN = re.compile(r"^[0-9A-Za-z가-힣 _-]+$")

class Character(BaseModel):
    id: str
    name: str
    role: str
    description: str
    traits: List[str]

class ContextManager:
    def __init__(self, project_name: str = "default_project"):
        """프로젝트(작품) 이름을 기반으로 데이터 경로를 동적으로 초기화합니다."""
        self.project_name = validate_project_name(project_name)
        self.data_dir = BASE_DATA_DIR / self.project_name
        
        # 프로젝트 폴더 및 하위 폴더 자동 생성
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "chapters").mkdir(exist_ok=True)
        
        self.config_path = self.data_dir / "config.json"
        self.chars_path = self.data_dir / "characters.json"
        
        self._ensure_default_files()
        
    def _ensure_default_files(self):
        """필수 파일이 없으면 기본 폼으로 생성합니다."""
        if not self.config_path.exists():
            default_config = {
                "worldview": "여기에 세계관(STORY_BIBLE)을 작성하세요.",
                "tone_and_manner": "여기에 문체(STYLE_GUIDE) 지침을 작성하세요.",
                "continuity": "여기에 절대 변경 불가 룰, 연표, 관계도(CONTINUITY)를 작성하세요.",
                "state": "여기에 현재 회차 떡밥, 갈등 상황, 감정선(STATE)을 작성하세요.",
                "summary_of_previous": "여기에 지난 줄거리 요약이 누적됩니다.",
                "plot_outline": "",
                "plot_version": 0,
            }
            self.save_config(default_config)
            
        if not self.chars_path.exists():
            self.save_characters([])
            
    def _load_json(self, path: Path) -> dict | list:
        if not path.exists():
            return {} if path.name == "config.json" else []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            backup_path = path.with_suffix(path.suffix + ".broken")
            try:
                path.replace(backup_path)
            except Exception:
                pass
            return {} if path.name == "config.json" else []
            
    def get_worldview_context(self) -> str:
        config = self._load_json(self.config_path)
        worldview = config.get("worldview", "")
        tone = config.get("tone_and_manner", "")
        
        # 하이브리드: 텍스트 렌더링 시에는 마크다운 블록처럼 주입
        return f"""[STORY BIBLE] (세계관 및 기본 설정)
{worldview}

[STYLE GUIDE] (문체 및 작성 지침)
{tone}
"""

    def get_continuity_context(self) -> str:
        config = self._load_json(self.config_path)
        continuity = config.get("continuity", "")
        return f"""[CONTINUITY] (고정 설정 - 절대 바꾸거나 어기면 안 되는 룰/연표/설정)
{continuity}
"""

    def get_state_context(self) -> str:
        config = self._load_json(self.config_path)
        state_info = config.get("state", "")
        prev_summary = config.get("summary_of_previous", "")
        
        return f"""[STATE] (현재 회차 상태 - 수거해야 할 떡밥, 갈등, 인물 감정선)
{state_info}

[PREVIOUS_SUMMARY] (이전 줄거리 요약)
{prev_summary}
"""

    def get_character_context(self) -> str:
        chars_data = self._load_json(self.chars_path)
        if not chars_data:
            return "[등장인물 정보 없음]"
            
        context = "[주요 등장인물 프로필]\n"
        for c in chars_data:
            char = Character(**c)
            context += f"- {char.name} ({char.role}): {char.description} (특징: {', '.join(char.traits)})\n"
            
        return context
        
    def get_config(self) -> dict:
        config = self._load_json(self.config_path)
        return config if isinstance(config, dict) else {}
        
    def get_characters(self) -> list:
        chars = self._load_json(self.chars_path)
        return chars if isinstance(chars, list) else []
        
    def save_config(self, config_data: dict):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
            
    def save_characters(self, chars_data: list):
        with open(self.chars_path, "w", encoding="utf-8") as f:
            json.dump(chars_data, f, ensure_ascii=False, indent=4)
            
    def update_summary(self, new_summary: str, generator_instance=None):
        config = self._load_json(self.config_path)
        if not isinstance(config, dict): config = {}
            
        old_summary = config.get("summary_of_previous", "").strip()
        if old_summary:
            updated_summary = old_summary + "\n\n[진행된 줄거리 요약]\n" + new_summary
        else:
            updated_summary = new_summary
            
        # ⚠️ 토큰 최적화 로직 (임계점: 약 3000자)
        # generator_instance가 주어지고, 길이가 초과하면 압축 실행
        if generator_instance and len(updated_summary) > 3000:
            compressed = generator_instance.compress_history_summary(updated_summary)
            if compressed: 
                updated_summary = compressed
            
        config["summary_of_previous"] = updated_summary
        self.save_config(config)
            
    def update_worldview(self, new_worldview: str):
        config = self._load_json(self.config_path)
        if not isinstance(config, dict): config = {}
        config["worldview"] = new_worldview
        self.save_config(config)

    def get_plot_outline(self) -> str:
        config = self._load_json(self.config_path)
        if not isinstance(config, dict):
            return ""
        return str(config.get("plot_outline", "")).strip()

    def save_plot_outline(self, plot_text: str):
        config = self._load_json(self.config_path)
        if not isinstance(config, dict):
            config = {}
        config["plot_outline"] = plot_text
        config["plot_version"] = int(config.get("plot_version", 0)) + 1
        self.save_config(config)

    def build_generation_prompt(
        self,
        user_instruction: str,
        length_goal: int = 5000,
        include_plot: bool = False,
        plot_strength: str = "balanced",
    ) -> str:
        """LLM에 전달할 최종 프롬프트를 조립합니다."""
        world_ctx = self.get_worldview_context()
        char_ctx = self.get_character_context()
        continuity_ctx = self.get_continuity_context()
        state_ctx = self.get_state_context()
        plot_ctx = self.get_plot_outline()
        plot_guard = ""
        if include_plot and plot_ctx:
            plot_guard = f"""
[PLOT OUTLINE] (장기 플롯 가이드, 선택 반영)
{plot_ctx}

[플롯 반영 강도]
{plot_strength}
"""
        
        prompt = f"""당신은 훌륭한 웹소설 작가입니다. 제공된 4대 설정(STORY BIBLE, STYLE GUIDE, CONTINUITY, STATE)과 등장인물 정보를 엄격히 준수하여 다음 회차(본문)를 작성해 주세요. 특히 CONTINUITY 규칙은 절대 어기지 말고, STATE의 떡밥과 감정선을 자연스럽게 녹여내세요.

{world_ctx}
{continuity_ctx}
{state_ctx}
{char_ctx}
{plot_guard}

[이번 회차 작성 지시사항]
{user_instruction}

[분량 및 서술 요구조건]
- 목표 작성 분량: 공백 포함 약 {length_goal}자 내외로 반드시 맞출 것.
- 지정된 분량({length_goal}자)에 맞추어 이야기의 서술량과 사건 전개 페이스를 조절하세요. 분량을 달성하기 위한 억지 서술이나 목표치를 한참 초과하여 글이 불필요하게 늘어지는 것을 방지하고, 목표 글자 수를 엄격히 준수하세요.

위의 제한 조건과 설정에 어긋나지 않도록 유의하며, 바로 소설 본문 작성을 시작하세요. 제목은 생략하고 본문만 출력하세요.
        """
        return prompt


def validate_project_name(name: str) -> str:
    value = (name or "").strip()
    if not value:
        raise ValueError("프로젝트 이름이 비어 있습니다.")
    if value in {".", ".."}:
        raise ValueError("프로젝트 이름이 유효하지 않습니다.")
    if "/" in value or "\\" in value:
        raise ValueError("프로젝트 이름에 경로 구분자(/, \\)를 사용할 수 없습니다.")
    if not PROJECT_NAME_PATTERN.match(value):
        raise ValueError("프로젝트 이름은 한글/영문/숫자/공백/_/- 만 사용할 수 있습니다.")
    return value
