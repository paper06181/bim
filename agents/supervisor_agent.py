"""
감리사 에이전트
"""

from .base_agent import BaseAgent

class SupervisorAgent(BaseAgent):
    """감리사 에이전트"""

    def __init__(self, use_llm=True):
        super().__init__("감리사", "감리팀", use_llm)
    
    def respond(self, issue, project, impact_result=None):
        """이슈에 대한 감리사 응답"""
        
        if impact_result is None:
            message = self._inspection_response(issue, project)
        else:
            message = self._approval_response(issue, project, impact_result)
        
        return self.add_to_history(message)
    
    def _inspection_response(self, issue, project):
        """검토 응답"""
        if self.use_llm:
            system_prompt = f"""당신은 {project.name}의 감리사입니다.

역할:
- 공사 감독 및 품질 관리
- 법규 준수 확인
- 건축주 대리인

성격:
- 공정하고 객관적
- 법규와 계약 조건 엄수
- 품질과 안전 최우선

말투:
- 전문적이고 중립적
- 법규 및 기준 언급
- 2-3문장으로 간결하게

반드시 "[감리사]"로 시작하세요."""

            user_message = self._build_context_message(issue, project)
            user_message += "\n\n이슈가 보고되었습니다. 감리사로서 검토 의견을 제시하세요."

            llm_response = self._generate_llm_response(system_prompt, user_message)

            if llm_response and llm_response.startswith('[감리사]'):
                return llm_response

        # LLM 실패 시 기본 템플릿
        return f"[감리사] {issue['name']} 문제에 대해 계약 조건 및 법규 적합성을 검토하겠습니다."
    
    def _approval_response(self, issue, project, impact_result):
        """승인 응답"""
        if self.use_llm:
            system_prompt = f"""당신은 {project.name}의 감리사입니다.

역할:
- 시정 조치 승인/불승인 결정
- 건축주 이익 보호
- 품질 기준 준수 확인

판단 기준:
- 지연 1주 미만, 조기 탐지 → 승인
- 지연 6주 이상 → 건축주에게 정식 보고 요구
- 법규 위반 가능성 → 즉시 조치 요구
- BIM으로 해결 시 → 긍정적 평가

말투:
- 승인/불승인 명확히 표현
- 법규 및 계약 근거 제시
- 2-3문장으로 간결하게

반드시 "[감리사]"로 시작하세요."""

            user_message = self._build_context_message(issue, project, impact_result)
            user_message += "\n\n해결 방안이 제시되었습니다. 감리사로서 승인 여부를 결정하세요."

            llm_response = self._generate_llm_response(system_prompt, user_message)

            if llm_response and llm_response.startswith('[감리사]'):
                return llm_response

        # LLM 실패 시 기본 템플릿
        delay = impact_result['delay_weeks']
        detected = impact_result['detected']

        if detected and delay < 1:
            return f"[감리사] 조기 발견으로 적절히 처리되었습니다. 공정 진행을 승인합니다."

        if delay > 6:
            return f"[감리사] 지연이 {delay:.1f}주로 예상됩니다. 건축주에게 정식 보고가 필요합니다."

        return f"[감리사] 제시된 해결 방안이 적절하다고 판단됩니다. 시정 조치를 승인합니다."