"""
금융사 에이전트
"""

from .base_agent import BaseAgent

class BankAgent(BaseAgent):
    """금융사 (은행) 에이전트"""

    def __init__(self, use_llm=True):
        super().__init__("금융사", "PF팀", use_llm)
        self.risk_threshold = 0.20
    
    def respond(self, issue, project, impact_result=None):
        """이슈에 대한 금융사 응답"""
        
        if impact_result is None:
            message = self._monitoring_response(issue, project)
        else:
            message = self._risk_assessment_response(issue, project, impact_result)
        
        return self.add_to_history(message)
    
    def _monitoring_response(self, issue, project):
        """모니터링 응답"""
        if self.use_llm:
            pf_amount = int(project.budget * project.pf_ratio / 100000000)
            system_prompt = f"""당신은 {project.name}의 금융사(PF팀)입니다.

역할:
- PF 대출 관리 (대출액 약 {pf_amount}억)
- 프로젝트 리스크 모니터링
- 금리 결정 및 기성금 지급

성격:
- 보수적이고 리스크 회피적
- 재무 지표 중심
- 손실 방지 최우선

말투:
- 전문적이고 신중하게
- 재무적 관점 강조
- 2-3문장으로 간결하게

반드시 "[금융사]"로 시작하세요."""

            user_message = self._build_context_message(issue, project)
            user_message += "\n\n이슈가 발생했습니다. 금융사 PF팀으로서 리스크 모니터링 의견을 제시하세요."

            llm_response = self._generate_llm_response(system_prompt, user_message)

            if llm_response and llm_response.startswith('[금융사]'):
                return llm_response

        # LLM 실패 시 기본 템플릿
        return f"[금융사] {issue['name']} 문제가 프로젝트 리스크에 미치는 영향을 평가하겠습니다."
    
    def _risk_assessment_response(self, issue, project, impact_result):
        """리스크 평가 응답"""
        if self.use_llm:
            system_prompt = f"""당신은 {project.name}의 금융사(PF팀)입니다.

역할:
- 최종 리스크 평가 및 대출 조건 결정
- 금리 인상/유지 결정
- 기성금 지급 승인

판단 기준:
- 지연률 또는 초과율 20% 이상 → 금리 인상 검토
- 금융 비용 증가 → 명확히 언급
- BIM으로 리스크 감소 → 긍정적 평가
- 리스크 관리 가능 수준 → 현 조건 유지

말투:
- 금융 전문 용어 사용
- 구체적 수치 언급
- 2-3문장으로 간결하게

반드시 "[금융사]"로 시작하세요."""

            user_message = self._build_context_message(issue, project, impact_result)

            metrics = project.calculate_final_metrics()
            user_message += f"\n\n## 현재 누적 지표\n"
            user_message += f"- 지연률: {metrics['schedule_delay_rate']*100:.1f}%\n"
            user_message += f"- 예산초과율: {metrics['budget_overrun_rate']*100:.1f}%\n"
            user_message += f"- 현재 금리: {project.current_interest_rate*100:.2f}%\n"
            user_message += "\n금융사로서 최종 리스크 평가 및 대출 조건 결정을 내리세요."

            llm_response = self._generate_llm_response(system_prompt, user_message)

            if llm_response and llm_response.startswith('[금융사]'):
                return llm_response

        # LLM 실패 시 기본 템플릿
        metrics = project.calculate_final_metrics()
        delay_rate = metrics['schedule_delay_rate']
        cost_rate = metrics['budget_overrun_rate']

        if delay_rate > self.risk_threshold or cost_rate > self.risk_threshold:
            rate_increase = impact_result.get('financial_cost', {}).get('rate_increase_bp', 0)
            if rate_increase > 0:
                return f"[금융사] 프로젝트 리스크가 증가하고 있습니다. 금리를 {rate_increase}bp 인상합니다."
            else:
                return f"[금융사] 프로젝트 리스크가 증가하고 있습니다. 면밀히 모니터링하겠습니다."

        if project.bim_enabled and impact_result['detected']:
            return f"[금융사] BIM을 통한 리스크 관리가 잘 되고 있습니다. 현재 금리 조건을 유지하겠습니다."

        return f"[금융사] 현재 리스크 수준은 관리 가능합니다. 기성금 지급을 진행하겠습니다."
    
    def periodic_review(self, project):
        """정기 리스크 검토"""
        metrics = project.calculate_final_metrics()
        
        review = f"\n[금융사 정기 검토 - Day {project.current_day}]\n"
        review += f"누적 지연: {metrics['delay_weeks']:.1f}주\n"
        review += f"예산 초과율: {metrics['budget_overrun_rate']*100:.1f}%\n"
        review += f"현재 금리: {project.current_interest_rate*100:.2f}%\n"
        
        if metrics['budget_overrun_rate'] > self.risk_threshold:
            review += f"경고: 예산 초과율이 {self.risk_threshold*100:.0f}%를 초과했습니다.\n"
        
        return review