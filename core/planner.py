from core.llm import generate_text


class Planner:
    def __init__(self, project_name: str | None = None):
        self.project_name = project_name

    def suggest_ideas(
        self,
        platform_name: str,
        user_keywords: str,
        tone: str = "가볍고 팝한",
        count: int = 5,
    ) -> str:
        prompt = f"""최신 웹소설 독자 트렌드를 고려해 아이디어를 제안해 주세요.

[목표 플랫폼]
{platform_name}

[사용자 관심 키워드]
{user_keywords}

[원하는 톤]
{tone}

[요청]
- 총 {count}개 아이디어
- 각 아이디어마다: 제목 후보 1개 + 로그라인 2~3문장 + 한 줄 차별점
- 상업성과 독창성이 동시에 느껴지는 아이디어 1~2개 포함
- 너무 비슷한 아이디어만 반복하지 말고 소재와 갈등의 조합을 분산
- 웹소설 독자층 기준으로 "연재 초반 흡입력"을 최우선으로 작성
"""
        return generate_text(
            prompt,
            system_instruction="너는 웹소설 시장 트렌드와 클릭률 최적화에 강한 기획자다.",
            project_name=self.project_name,
            feature="idea",
        ).strip()

    def build_macro_plot(
        self,
        platform_name: str,
        title: str,
        phase1_focus: str,
        phase2_focus: str,
        phase3_focus: str,
        total_episodes: int = 300,
    ) -> str:
        prompt = f"""다음 조건으로 장편 웹소설 대형 플롯을 설계해 주세요.

[플랫폼]
{platform_name}

[제목]
{title}

[총 분량]
{total_episodes}화 완결

[전개 구조 요구]
- 50화 단위 대형 아크 설계
- 30화 단위 주요 사건 10개 요약
- 이야기 스케일이 자연스럽게 확장

[구간별 중점]
- 1~100화: {phase1_focus}
- 101~200화: {phase2_focus}
- 201~300화: {phase3_focus}

[출력 형식]
1) 취약점 보완용 진단
2) 개선 반영 최종 로그라인
3) 30화 단위 주요 사건 10개
4) 독자 반응을 위한 운영 포인트
"""
        return generate_text(
            prompt,
            system_instruction="너는 장편 연재 구조 설계와 상업적 반응성에 특화한 시리즈 플래너다.",
            project_name=self.project_name,
            feature="plot",
        ).strip()
