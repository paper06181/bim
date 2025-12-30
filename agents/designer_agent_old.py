"""
설계사 에이전트
"""

from .base_agent import BaseAgent

class DesignerAgent(BaseAgent):
    """설계사 에이전트"""
    
    def __init__(self):
        super().__init__("설계사", "설계팀")
    
    def respond(self, issue, project, impact_result=None):
        """이슈에 대한 설계사 응답"""
        
        if impact_result is None:
            message = self._analysis_response(issue, project)
        else:
            message = self._solution_response(issue, project, impact_result)
        
        return self.add_to_history(message)
    
    def _analysis_response(self, issue, project):
        """원인 분석 응답"""
        category = issue['category']
        
        if category == '설계':
            if project.bim_enabled:
                return f"[설계사] {issue['name']} 문제입니다. BIM 모델을 검토하여 원인을 파악하겠습니다."
            else:
                return f"[설계사] {issue['name']} 문제입니다. 2D 도면을 재검토하여 원인을 파악하겠습니다."
        
        return f"[설계사] {issue['name']} 문제에 대해 기술적 검토를 진행하겠습니다."
    
    def _solution_response(self, issue, project, impact_result):
        """해결책 제시 응답"""
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