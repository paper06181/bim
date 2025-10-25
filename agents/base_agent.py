"""
에이전트 베이스 클래스
"""

from utils.llm_client import LLMClient


class BaseAgent:
    """모든 에이전트의 기본 클래스"""

    def __init__(self, name, role, use_llm=True):
        self.name = name
        self.role = role
        self.use_llm = use_llm
        self.conversation_history = []

        if self.use_llm:
            try:
                self.llm_client = LLMClient()
            except ValueError as e:
                print(f"[Warning] LLM 초기화 실패: {e}")
                print("[Warning] 기본 템플릿 모드로 작동합니다.")
                self.use_llm = False

    def respond(self, issue, project, impact_result=None):
        """이슈에 대한 응답 생성 (하위 클래스에서 구현)"""
        raise NotImplementedError

    def add_to_history(self, message):
        """대화 이력 추가"""
        self.conversation_history.append({
            'speaker': self.name,
            'message': message
        })
        return message

    def _generate_llm_response(self, system_prompt, user_message, temperature=None):
        """LLM을 통한 응답 생성"""
        if not self.use_llm:
            return None

        try:
            response = self.llm_client.generate_response(
                system_prompt,
                user_message,
                temperature
            )
            # LLM 에러 응답 체크 (LLMClient에서 반환하는 에러 메시지)
            if response and "[LLM 응답 생성 실패" in response:
                print(f"[{self.name}] LLM 응답 실패 - 기본 템플릿 사용")
                return None
            return response
        except Exception as e:
            print(f"[{self.name}] LLM 응답 실패: {e}")
            return None

    def _build_context_message(self, issue, project, impact_result=None):
        """컨텍스트 메시지 생성"""
        context = f"""
## 프로젝트 정보
- 이름: {project.name}
- 연면적: {project.gfa}㎡
- 예산: {project.budget:,}원
- 현재 단계: {project.current_phase}
- 현재 일자: Day {project.current_day}
- BIM 적용: {'ON' if project.bim_enabled else 'OFF'}

## 발생 이슈
- ID: {issue['id']}
- 이름: {issue['name']}
- 카테고리: {issue['category']}
- 심각도: {issue['severity']}
- 설명: {issue['description']}
"""

        if impact_result:
            context += f"""
## 영향 분석 결과
- 지연: {impact_result['delay_weeks']:.1f}주
- 비용 증가: {impact_result['cost_increase']*100:.1f}%
- 탐지 여부: {'예' if impact_result['detected'] else '아니오'}
"""
            if impact_result['detected']:
                context += f"- 탐지 단계: {impact_result.get('detection_phase', 'N/A')}\n"
                context += f"- BIM 효과성: {impact_result.get('bim_effectiveness', 0):.2f}\n"

            if impact_result.get('financial_cost'):
                fc = impact_result['financial_cost']
                context += f"""
## 금융 영향
- 추가 이자: {fc['interest_increase']:,.0f}원
- 간접비: {fc['indirect_cost']:,.0f}원
- 총 금융 비용: {fc['total_financial_cost']:,.0f}원
- 금리 인상: +{fc['rate_increase_bp']}bp
"""

        return context.strip()