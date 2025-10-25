"""
시공사 에이전트
"""

from .base_agent import BaseAgent

class ContractorAgent(BaseAgent):
    """시공사 (현장 소장) 에이전트"""

    def __init__(self, use_llm=True):
        super().__init__("시공사", "현장소장", use_llm)
    
    def respond(self, issue, project, impact_result=None):
        """이슈에 대한 시공사 응답"""
        
        if impact_result is None:
            message = self._report_response(issue, project)
        else:
            message = self._execution_response(issue, project, impact_result)
        
        return self.add_to_history(message)
    
    def _report_response(self, issue, project):
        """문제 보고 응답"""
        if self.use_llm:
            system_prompt = f"""당신은 {project.name}의 시공사(현장소장)입니다.

역할:
- 현장 시공 책임자
- 공정 관리 및 작업 조율
- 작업자 안전과 품질 책임

성격:
- 실용적이고 현장 중심적
- 공기 준수에 민감
- 문제 해결 지향적

말투:
- 직설적이고 명확하게
- 현장 용어 사용
- 2-3문장으로 간결하게

반드시 "[시공사]"로 시작하세요."""

            user_message = self._build_context_message(issue, project)
            user_message += "\n\n현장에서 위 이슈가 발생했습니다. 시공사 현장소장으로서 상황을 보고하세요."

            llm_response = self._generate_llm_response(system_prompt, user_message)

            if llm_response and llm_response.startswith('[시공사]'):
                return llm_response

        # LLM 실패 시 기본 템플릿
        phase = issue['phase']
        severity = issue['severity']

        severity_text = {
            'S3': '심각한',
            'S2': '중간 수준의',
            'S1': '경미한'
        }

        return f"[시공사] 현장에서 {severity_text.get(severity, '')} {issue['name']} 문제가 발생했습니다. 작업을 중단하고 대책을 논의해야 합니다."
    
    def _execution_response(self, issue, project, impact_result):
        """실행 계획 응답"""
        if self.use_llm:
            system_prompt = f"""당신은 {project.name}의 시공사(현장소장)입니다.

역할:
- 실행 계획 수립 및 자원 배치
- 공정표 조정
- 하도급업체 조율

판단 기준:
- 지연 4주 이상 → 인력/장비 추가 투입 검토
- BIM으로 조기 탐지 시 → 신속 대응 가능 강조
- 설계 단계에서 해결 시 → 현장 영향 없음 확인
- 재작업 필요 시 → 구체적 실행 계획 제시

말투:
- 실행 가능한 방안 제시
- 공기와 비용 명시
- 2-3문장으로 간결하게

반드시 "[시공사]"로 시작하세요."""

            user_message = self._build_context_message(issue, project, impact_result)
            user_message += "\n\n영향 분석이 완료되었습니다. 시공사로서 실행 계획을 제시하세요."

            llm_response = self._generate_llm_response(system_prompt, user_message)

            if llm_response and llm_response.startswith('[시공사]'):
                return llm_response

        # LLM 실패 시 기본 템플릿
        delay = impact_result['delay_weeks']
        cost = impact_result['cost_increase'] * 100
        detected = impact_result['detected']

        if project.bim_enabled and detected:
            if impact_result.get('detection_phase') == '설계':
                return f"[시공사] BIM 모델을 확인했습니다. 설계 단계에서 이미 해결된 사항이므로 현장 작업에 문제없습니다."
            else:
                return f"[시공사] BIM 4D 시뮬레이션으로 대체 공정을 검토했습니다. 약 {delay:.1f}주 지연, {cost:.1f}% 비용 증가 예상됩니다."

        return f"[시공사] 재작업 및 공정 조정이 필요합니다. 약 {delay:.1f}주 지연, {cost:.1f}% 비용 증가를 예상합니다."