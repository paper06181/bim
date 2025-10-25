"""
설계사 에이전트 (LLM 통합)
"""

from .base_agent import BaseAgent


class DesignerAgent(BaseAgent):
    """설계사 에이전트"""

    def __init__(self, use_llm=True):
        super().__init__("설계사", "설계팀", use_llm)

    def respond(self, issue, project, impact_result=None):
        """이슈에 대한 설계사 응답"""

        if impact_result is None:
            message = self._analysis_response(issue, project)
        else:
            message = self._solution_response(issue, project, impact_result)

        return self.add_to_history(message)

    def _analysis_response(self, issue, project):
        """원인 분석 응답"""
        if self.use_llm:
            system_prompt = f"""당신은 {project.name}의 설계사(설계팀)입니다.

역할:
- 건축 설계 및 기술적 문제 해결 담당
- 디자인 품질과 기술적 완성도 추구
- 시공 가능성 확보가 중요

성격:
- 전문가로서 자부심
- 문제 발생 시 원인 분석에 집중
- 해결책 제시에 적극적
- 기술 용어를 쉽게 풀어 설명

말투:
- 전문적이지만 이해하기 쉽게
- 원인과 해결 방향 제시
- 2-3문장으로 간결하게

반드시 "[설계사]"로 시작하세요."""

            user_message = self._build_context_message(issue, project)
            user_message += "\n\n위 이슈에 대해 설계사로서 기술적 원인을 분석하세요."

            llm_response = self._generate_llm_response(system_prompt, user_message)

            if llm_response and llm_response.startswith('[설계사]'):
                return llm_response

        # LLM 실패 시 기본 템플릿
        category = issue['category']

        if category == '설계':
            if project.bim_enabled:
                return f"[설계사] {issue['name']} 문제입니다. BIM 모델을 검토하여 원인을 파악하겠습니다."
            else:
                return f"[설계사] {issue['name']} 문제입니다. 2D 도면을 재검토하여 원인을 파악하겠습니다."

        return f"[설계사] {issue['name']} 문제에 대해 기술적 검토를 진행하겠습니다."

    def _solution_response(self, issue, project, impact_result):
        """해결책 제시 응답"""
        if self.use_llm:
            system_prompt = f"""당신은 {project.name}의 설계사(설계팀)입니다.

역할:
- 기술적 문제에 대한 해결책 제시
- BIM 활용 시 데이터 기반 근거 제시
- 설계 변경안 작성 및 시공 가능성 검토

BIM 적용 시:
- "BIM 모델에서 사전 발견" 강조
- 3D 충돌 검토, 자동 물량 산출 등 구체적 언급
- 설계 단계 해결로 현장 영향 최소화 강조

BIM 미적용 시:
- 경험과 직관 기반 판단
- 현장 확인 필요성 언급
- 2D 도면 수정 작업 설명

말투:
- 전문적이고 책임감 있게
- 구체적 해결 방안 제시
- 2-3문장으로 간결하게

반드시 "[설계사]"로 시작하세요."""

            user_message = self._build_context_message(issue, project, impact_result)
            user_message += "\n\n위 영향 분석을 바탕으로 설계사로서 해결 방안을 제시하세요."

            llm_response = self._generate_llm_response(system_prompt, user_message, temperature=0.7)

            if llm_response and llm_response.startswith('[설계사]'):
                return llm_response

        # LLM 실패 시 기본 템플릿
        detected = impact_result['detected']
        phase = impact_result.get('detection_phase', '시공')

        if project.bim_enabled and detected:
            if phase == '설계':
                return f"[설계사] BIM 모델에서 {issue['name']} 문제를 사전에 발견했습니다. 설계 단계에서 수정하여 시공 영향은 없습니다."
            else:
                return f"[설계사] BIM 데이터를 기반으로 {issue['name']} 문제의 해결 방안을 제시하겠습니다."

        delay = impact_result['delay_weeks']
        cost = impact_result['cost_increase'] * 100

        return f"[설계사] {issue['name']} 문제로 약 {delay:.1f}주 지연, {cost:.1f}% 비용 증가가 예상됩니다. 설계 변경안을 작성하겠습니다."
