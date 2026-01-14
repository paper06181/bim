"""
시공사 에이전트 - GPT API 연동
"""

from .base_agent import BaseAgent
from typing import Dict, Any
import json


class ContractorAgent(BaseAgent):
    def __init__(self, method: str):
        super().__init__(name="시공사", role="현장소장")
        self.method = method

    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        project_summary = context.get("project_summary", {})
        cumulative = context.get("cumulative", {})
        issue_status = context.get('issue_status', {})
        kpi_values = context.get('kpi_values', {})

        bim_specific = f"""
【BIM 현장 도구 및 지표】
- 4D 시뮬레이션으로 공정 검토
- 3D 모델 기반 간섭(Clash) 사전 확인
- 태블릿으로 현장-모델 실시간 비교
- 모바일 기반 즉시 보고 시스템

【현재 BIM 품질 지표】
- WD (Warning Density): {kpi_values.get('WD', 'N/A')} (경고 밀도, 낮을수록 양호)
- CD (Clash Density): {kpi_values.get('CD', 'N/A')} (간섭 밀도, 낮을수록 양호)
- AF (Attribute Fill): {kpi_values.get('AF', 'N/A')}% (속성 입력률, 높을수록 양호)
- PL (Process Link): {kpi_values.get('PL', 'N/A')}% (공정 연계율, 높을수록 양호)

【BIM 현장의 장점】
- 사전 간섭 확인으로 재시공 감소
- 정확한 물량 산출로 자재 낭비 최소화
- 공정별 3D 시각화로 작업자 이해도 향상
""" if self.method == "BIM" else f"""
【전통 방식 현장 환경】
- 2D 도면 기반 작업 지시
- 종이 도면 + 수기 체크리스트
- 현장 변경 사항 즉시 반영 어려움
- 간섭 발견은 시공 단계에서 직접 확인

【현재 전통 방식 지표】
- RR (Rework Rate): {kpi_values.get('RR', 'N/A')}% (재시공률, 낮을수록 양호)
- SR (Schedule Variance): {kpi_values.get('SR', 'N/A')}% (일정 편차, 낮을수록 양호)
- CR (Communication Rate): {kpi_values.get('CR', 'N/A')} (의사소통 빈도, 높을수록 양호)
- FC (Field Change): {kpi_values.get('FC', 'N/A')} (현장 변경 건수, 낮을수록 양호)

【전통 방식의 제약】
- 도면 해석 오류로 재시공 발생 가능
- 현장 변경 사항 도면 반영 시차
- 간섭은 시공 중 발견되어 긴급 대응 필요
"""

        return f"""당신은 건설 프로젝트의 시공사 현장소장입니다.

【현재 프로젝트 상황】
- 총 공사비: {project_summary.get('총공사비', 'N/A')}
- 목표 공기: {project_summary.get('목표공기', 'N/A')}
- 현재 진행률: {context.get('progress_rate', 0) * 100:.1f}%
- 경과일: Day {context.get('current_day', 0)}

【누적 현황】
- 누적 지연: {cumulative.get('total_delay_days', 0):.1f}일
- 누적 비용 초과: {cumulative.get('total_cost_overrun', 0):.2f}%
- 일일 인건비 압박: {context.get('daily_labor_cost', 'N/A')}

【진행 중인 이슈 현황】
- 해결 완료: {len(issue_status.get('해결완료', []))}개
- 진행 중: {len(issue_status.get('진행중', []))}개 ← 현장 자원 분산 중
- 대기 중: {len(issue_status.get('대기중', []))}개

{bim_specific}

【시공사 현장소장의 주요 관심사】
1. 현장 작업 공간 확보 (진행중인 이슈들과 공간 간섭 여부)
2. 인력/장비 자원 가용성 (현재 {len(issue_status.get('진행중', []))}개 이슈에 투입 중)
3. 안전 리스크 (동시 작업 시 안전사고 위험도)
4. 공정 순서 준수 (선행 작업 완료 여부)
5. 자재 조달 및 보관 (현장 야적 공간, 입고 일정)
6. 날씨/계절 영향 (우기, 동절기 작업 제약)
7. 하도급 업체 스케줄 조율

【현장 의사결정 원칙】
1. 안전사고 위험이 있으면 무조건 작업 중단 또는 대기
2. 여러 이슈가 동일 작업 공간을 필요로 하면 순차 진행
3. 인력/장비가 부족하면 우선순위 높은 이슈에 집중
4. 선행 공정이 완료되지 않았으면 후속 작업 대기
5. 현장 변경은 즉시 건축주/감리에 보고 후 승인받아 진행
6. 품질 저하 우려 시 일정보다 품질 우선 (재시공 비용 더 큼)

【반드시 고려해야 할 현장 요소】
- 현재 진행중인 {len(issue_status.get('진행중', []))}개 이슈와의 작업 공간 중복 여부
- 이미 투입된 인력/장비와 신규 이슈의 자원 경쟁
- 하도급 업체의 타 현장 일정 (즉시 투입 가능 여부)
- 자재 발주~입고 리드타임 (긴급 발주 시 비용 증가)
- 날씨 제약 (우천, 강풍, 혹한 시 작업 불가 공종)
- 민원 요소 (소음, 분진 발생 시간대 제약)

【출력 형식】
반드시 아래 JSON 형식으로만 답변:
{{
  "field_assessment": "현장 실행 가능성 평가 (작업 공간, 자원, 안전 측면)",
  "severity_assessment": 1~10 사이 숫자,
  "opinion": "시공사 의견 (진행중인 다른 이슈들과의 현장 간섭, 자원 분배, 작업 순서를 반드시 언급)",
  "impact_on_schedule": "일정 영향도 (즉시영향/단기영향/장기영향)",
  "resource_conflict_detail": "구체적인 자원 충돌 내용 (인력/장비/공간)",
  "space_interference": "작업 공간 간섭 여부 (있음/없음/부분적)",
  "safety_risk": "안전 리스크 수준 (높음/보통/낮음)",
  "recommended_sequence": "작업 순서 제안 (즉시착수/대기후착수/병렬진행가능)",
  "subcontractor_availability": "하도급 투입 가능 여부"
}}
"""

    def report_issue(self, issue: Dict, context: Dict) -> str:
        if issue.get("발생단계") in ["시공", "준공"]:
            return f"현장에서 {issue['이슈명']} 발견"
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
- 발생단계: {issue.get('발생단계', 'N/A')}
- 예상 지연: {issue['지연(주)_Min']} ~ {issue['지연(주)_Max']}주
- 예상 비용 증가: {issue['비용증가(%)_Min']} ~ {issue['비용증가(%)_Max']}%
- 상세 설명: {issue.get('설명', '')}

【현재 진행 중인 현장 이슈 상세】
{json.dumps(issue_status.get('진행중', []), ensure_ascii=False, indent=2)}

【대기 중인 이슈】
{json.dumps(issue_status.get('대기중', []), ensure_ascii=False, indent=2)}

【다른 에이전트 의견】
{json.dumps(other_opinions, ensure_ascii=False, indent=2) if other_opinions else "아직 수집 전"}

【질문】
시공사 현장소장으로서 다음을 고려하여 의견을 주세요:

1. 이 신규 이슈가 현재 진행 중인 {len(issue_status.get('진행중', []))}개 이슈와 현장에서 어떻게 간섭하는가?
   - 작업 공간이 겹치는가? (예: 동일 층, 동일 구역)
   - 같은 인력/장비를 필요로 하는가?
   - 동시 작업 시 안전사고 위험이 있는가?

2. 자원(인력, 장비, 자재) 투입이 가능한가?
   - 현재 진행중인 이슈들에 이미 투입된 자원은?
   - 추가 인력/장비 확보가 필요한가?
   - 하도급 업체를 즉시 투입할 수 있는가?

3. 작업 순서상 즉시 착수 가능한가?
   - 선행 공정이 완료되었는가?
   - 다른 이슈 해결 후에 착수해야 하는가?
   - 병렬 작업이 가능한가?

4. 현장 실행 가능성은? (날씨, 계절, 민원 등)
   - 우천/동절기 등 날씨 제약이 있는가?
   - 소음/분진 민원으로 작업 시간대가 제한되는가?
   - 자재 입고 리드타임은 얼마나 걸리는가?

5. 다른 에이전트(건축주 등)의 의견을 고려한 현장 입장의 최종 판단은?

반드시 JSON 형식으로만 답변하세요.
"""

        response = llm.call(system_prompt, user_message, response_format="json")

        if "error" in response:
            return {
                "field_assessment": f"{issue['이슈명']} 현장 검토 필요 (진행중 {len(issue_status.get('진행중', []))}개 이슈 고려)",
                "severity_assessment": 6,
                "opinion": "시공사 검토 중",
                "impact_on_schedule": "확인 필요",
                "resource_conflict_detail": "분석 필요",
                "space_interference": "확인 필요",
                "safety_risk": "평가 필요",
                "recommended_sequence": "조건부착수",
                "subcontractor_availability": "확인 필요"
            }

        return response

    def propose_solution(self, issue: Dict, severity: Dict, context: Dict) -> Dict:
        delay_max = issue.get("지연(주)_Max", 2)
        cost_max = issue.get("비용증가(%)_Max", 0.5)

        return {
            "solutions": [
                {
                    "option_id": "SOL-C1",
                    "proposer": "시공사",
                    "description": "정상 공정",
                    "time_weeks": delay_max * 0.8,
                    "cost_increase_pct": cost_max * 0.6,
                    "quality_impact": "높음",
                    "risk_level": "낮음"
                },
                {
                    "option_id": "SOL-C2",
                    "proposer": "시공사",
                    "description": "인력증투 신속처리",
                    "time_weeks": delay_max * 0.5,
                    "cost_increase_pct": cost_max * 1.2,
                    "quality_impact": "보통",
                    "risk_level": "보통"
                }
            ],
            "recommendation": "SOL-C1",
            "reasoning": "품질 확보"
        }
