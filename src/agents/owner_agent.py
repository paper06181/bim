"""
건축주 에이전트 - 현실적인 상세 프롬프트
"""

from .base_agent import BaseAgent
from typing import Dict, Any
import json


class OwnerAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="건축주", role="발주자")

    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        project_summary = context.get("project_summary", {})
        cumulative = context.get("cumulative", {})
        issue_status = context.get('issue_status', {})

        return f"""당신은 건설 프로젝트의 건축주(발주자)입니다.

【현재 프로젝트 상황】
- 총 공사비: {project_summary.get('총공사비', 'N/A')}
- 목표 공기: {project_summary.get('목표공기', 'N/A')}
- 현재 진행률: {context.get('progress_rate', 0) * 100:.1f}%
- 경과일: Day {context.get('current_day', 0)}

【누적 현황】
- 누적 지연: {cumulative.get('total_delay_days', 0):.1f}일
- 누적 비용 초과: {cumulative.get('total_cost_overrun', 0):.2f}%
- 일일 금융 비용: {context.get('daily_finance_cost', 'N/A')}

【진행 중인 이슈 현황】
- 해결 완료: {len(issue_status.get('해결완료', []))}개
- 진행 중: {len(issue_status.get('진행중', []))}개
- 대기 중: {len(issue_status.get('대기중', []))}개

【건축주의 주요 관심사】
1. 전체 프로젝트 일정 준수 (지연 시 금융 비용 누적)
2. 예산 내 완공 (추가 비용 발생 시 승인 필요)
3. 품질 확보 (하자 발생 시 장기적 손실)
4. 진행 중인 여러 이슈들 간의 우선순위 결정
5. 자원(인력, 장비, 예산) 배분 최적화

【의사결정 원칙】
1. 안전사고는 무조건 최우선 (공사 중단도 감수)
2. 여러 이슈가 동시 진행 중이면 critical path 우선
3. 진행 중인 이슈들과 신규 이슈의 상호 영향 고려
4. 누적 지연이 10% 초과 시 비용 투입해서라도 단축
5. 전문가(시공사, 설계사) 의견 존중하되 최종 결정은 사업성 기반

【반드시 고려해야 할 사항】
- 현재 진행 중인 {len(issue_status.get('진행중', []))}개 이슈와의 자원 경쟁
- 대기 중인 {len(issue_status.get('대기중', []))}개 이슈의 착수 시점
- 누적된 지연/비용이 신규 이슈 판단에 미치는 영향
- 여러 이슈가 동일 공간/자원을 필요로 할 경우 우선순위

【출력 형식】
반드시 아래 JSON 형식으로만 답변:
{{
  "concern_level": "높음/보통/낮음",
  "priority": "비용 최소화/일정 준수/품질 유지/안전 확보",
  "opinion": "건축주 입장에서의 구체적 의견 (진행중인 다른 이슈들과의 관계, 자원 배분, 우선순위 등을 반드시 언급)",
  "severity_assessment": 1~10 사이 숫자,
  "budget_tolerance": "추가 비용 허용 한도 (예: 0.5%)",
  "relationship_with_active_issues": "진행중인 이슈들과의 관계 분석",
  "resource_conflict": "자원 경쟁 여부 (있음/없음)",
  "recommended_timing": "즉시착수/대기/조건부착수"
}}
"""

    def report_issue(self, issue: Dict, context: Dict) -> str:
        return ""

    def give_opinion(self, issue: Dict, context: Dict, other_opinions: Dict = None) -> Dict:
        from ..utils.llm_client import LLMClient

        llm = LLMClient()
        system_prompt = self.get_system_prompt(context)
        issue_status = context.get('issue_status', {})

        user_message = f"""
【신규 이슈 정보】
- ID: {issue['ID']}
- 이슈명: {issue['이슈명']}
- 카테고리: {issue['카테고리']}
- 심각도: {issue['심각도']}
- 예상 지연: {issue['지연(주)_Min']} ~ {issue['지연(주)_Max']}주
- 예상 비용 증가: {issue['비용증가(%)_Min']} ~ {issue['비용증가(%)_Max']}%
- 상세 설명: {issue.get('설명', '')}

【현재 진행 중인 이슈 상세】
{json.dumps(issue_status.get('진행중', []), ensure_ascii=False, indent=2)}

【대기 중인 이슈】
{json.dumps(issue_status.get('대기중', []), ensure_ascii=False, indent=2)}

【다른 에이전트 의견】
{json.dumps(other_opinions, ensure_ascii=False, indent=2) if other_opinions else "아직 수집 전"}

【질문】
건축주로서 다음을 고려하여 의견을 주세요:

1. 이 신규 이슈가 현재 진행 중인 {len(issue_status.get('진행중', []))}개 이슈와 어떻게 상호작용하는가?
2. 자원(인력, 장비, 예산)이 겹치는가? 우선순위는?
3. 즉시 착수해야 하는가, 아니면 다른 이슈 해결 후 착수해야 하는가?
4. 누적 지연/비용을 고려할 때 이 이슈의 심각도는?
5. 다른 에이전트 의견을 고려한 최종 판단은?

반드시 JSON 형식으로만 답변하세요.
"""

        response = llm.call(system_prompt, user_message, response_format="json")

        if "error" in response:
            return {
                "concern_level": "보통",
                "priority": "일정 준수",
                "opinion": f"{issue['이슈명']} 검토 필요 (진행중 {len(issue_status.get('진행중', []))}개 이슈 고려)",
                "severity_assessment": 5,
                "budget_tolerance": "0.5%",
                "relationship_with_active_issues": "분석 필요",
                "resource_conflict": "확인 필요",
                "recommended_timing": "조건부착수"
            }

        return response

    def propose_solution(self, issue: Dict, severity: Dict, context: Dict) -> Dict:
        return {}

    def select_solution(self, solutions: list, issue: Dict, context: Dict) -> Dict:
        if not solutions:
            return {"selected_id": None, "reasoning": "제안 없음"}

        best = min(solutions, key=lambda s: s.get("cost_increase_pct", 0) * 0.4 + s.get("time_weeks", 0) * 0.6)

        return {
            "selected_solution": best,
            "reasoning": f"비용 {best.get('cost_increase_pct', 0):.2f}%, 시간 {best.get('time_weeks', 0):.1f}주로 가장 균형잡힌 방안. 진행중인 이슈들과의 충돌 최소화"
        }
