from typing import Optional

from core.llm import generate_text


class Planner:
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
- 각 아이디어마다: 제목 후보 1개 + 로그라인 2~3문장 + 한 줄 펀치라인
- 식상하지만 클릭이 잘 되는 아이디어 1~2개 포함
- 너무 비슷한 아이디어는 피하고 장르/클리셰 조합을 분산
- 한국 웹소설 독자층 기준으로 "연재 초반 후킹"을 최우선으로 작성
"""
        return generate_text(
            prompt,
            system_instruction="너는 웹소설 시장 트렌드와 클릭률 최적화에 강한 기획자다.",
            max_output_tokens=1400,
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
- 50화 단위 대형 터닝포인트
- 30화 단위 대사건 10개(생략 없이)
- 이야기 스케일은 점진적 확장

[구간별 중점]
- 1~100화: {phase1_focus}
- 101~200화: {phase2_focus}
- 201~300화: {phase3_focus}

[출력 형식]
1) 취약점/보완점 진단 (왜 필요한지 포함)
2) 개선 반영된 최종 로그라인
3) 30화 단위 대사건 10개 (각 사건의 목표/갈등/반전/다음 훅)
4) 독자 유지 장치(클리셰 운용, 떡밥 회수 주기, 이탈 방지 포인트)
"""
        return generate_text(
            prompt,
            system_instruction="너는 장편 연재 구조 설계와 상업성 밸런싱에 능한 시리즈 디렉터다.",
            max_output_tokens=2200,
        ).strip()

