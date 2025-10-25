"""
건축주 에이전트
"""

from .base_agent import BaseAgent


class OwnerAgent(BaseAgent):
    """건축주 (발주자) 에이전트"""

    def __init__(self, use_llm=True):
        super().__init__("건축주", "발주자", use_llm)
        self.risk_tolerance = 0.15
    
    def respond(self, issue, project, impact_result=None):
        """이슈에 대한 건축주 응답"""
        
        if impact_result is None:
            message = self._initial_response(issue, project)
        else:
            message = self._decision_response(issue, project, impact_result)
        
        return self.add_to_history(message)
    
    def _initial_response(self, issue, project):
        """초기 응답"""
        if self.use_llm:
            system_prompt = f"""당신은 {project.name}의 건축주(발주자)입니다.

역할:
- 프로젝트 소유주이자 최종 의사결정권자
- 예산과 일정 관리에 가장 민감
- 투자 수익 극대화가 목표

성격:
- 보수적이고 위험 회피 성향
- 비용 절감과 일정 준수를 최우선시
- 전문가 의견을 듣되 최종 판단은 독립적

말투:
- 격식을 차리고 간결하게
- 핵심을 묻는 질문 위주
- 2-3문장 이내로 짧게

반드시 "[건축주]"로 시작하세요."""

            user_message = self._build_context_message(issue, project)
            user_message += "\n\n위 이슈가 발생했습니다. 건축주로서 첫 반응을 보이세요."

            llm_response = self._generate_llm_response(system_prompt, user_message)

            if llm_response and llm_response.startswith('[건축주]'):
                return llm_response

        # LLM 실패 시 기본 템플릿
        return f"[건축주] {issue['name']} 문제가 발생했다고 들었습니다. 비용과 일정에 어떤 영향이 있습니까?"

    def _decision_response(self, issue, project, impact_result):
        """의사결정 응답"""
        if self.use_llm:
            system_prompt = f"""당신은 {project.name}의 건축주(발주자)입니다.

역할:
- 최종 의사결정권자
- 예산 초과와 일정 지연에 민감
- 리스크 최소화 추구

판단 기준:
- 지연 4주 이상 또는 비용 2% 이상 증가 → 심각하게 우려
- 지연 1주 미만 → 수용 가능
- BIM으로 조기 탐지 시 → 긍정적 평가
- 금융 비용(금리 인상) 발생 시 → 강하게 우려

말투:
- 명확하고 단호하게
- 승인/거부를 명시
- 2-3문장으로 간결하게

반드시 "[건축주]"로 시작하세요."""

            user_message = self._build_context_message(issue, project, impact_result)
            user_message += "\n\n위 영향 분석을 바탕으로 최종 의사결정을 내리세요."

            llm_response = self._generate_llm_response(system_prompt, user_message, temperature=0.6)

            if llm_response and llm_response.startswith('[건축주]'):
                return llm_response

        # LLM 실패 시 기본 템플릿
        delay = impact_result['delay_weeks']
        cost = impact_result['cost_increase'] * 100
        detected = impact_result['detected']

        if detected and delay < 1:
            return f"[건축주] {'BIM 덕분에' if project.bim_enabled else ''} 조기에 발견하여 큰 영향이 없다니 다행입니다. 승인하겠습니다."

        if delay > 4 or cost > 2:
            return f"[건축주] 지연 {delay:.1f}주, 비용 {cost:.1f}% 증가는 심각합니다. 대안은 없습니까?"

        return f"[건축주] 지연 {delay:.1f}주, 비용 {cost:.1f}% 증가를 승인합니다. 이후 유사 문제 재발 방지에 힘써주십시오."
    
    def assess_project_risk(self, project):
        """프로젝트 전체 리스크 평가"""
        metrics = project.calculate_final_metrics()
        
        if metrics['budget_overrun_rate'] > self.risk_tolerance:
            return f"[건축주] 예산 초과율이 {metrics['budget_overrun_rate']*100:.1f}%입니다. 우려스럽습니다."
        
        return f"[건축주] 현재까지는 관리 가능한 수준입니다."