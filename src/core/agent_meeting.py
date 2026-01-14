"""
에이전트 회의 시스템 - 이슈 현황 통합
"""

from typing import Dict, List, Any
from ..agents.owner_agent import OwnerAgent
from ..agents.contractor_agent import ContractorAgent
from ..config.case_mapping import normalize_kpi_value
import random


class AgentMeeting:
    def __init__(self, date: int, project_context: Dict, new_issues: List[Dict], active_issues: List, method: str):
        self.date = date
        self.context = project_context
        self.new_issues = new_issues
        self.active_issues = active_issues
        self.method = method

        self.agents = {
            "건축주": OwnerAgent(),
            "시공사": ContractorAgent(method),
        }

    def run(self) -> Dict:
        """회의 진행 - 이슈 현황 통합"""

        # ===== 1. 이슈 현황 정리 =====
        issue_status = {
            "해결완료": [],
            "진행중": [
                {
                    "ID": getattr(issue, 'id', 'N/A'),
                    "이름": getattr(issue, 'name', str(issue)),
                    "진행률": f"{getattr(issue, 'progress', 0):.0f}%",
                    "카테고리": getattr(issue, 'category', 'N/A')
                }
                for issue in self.active_issues
            ],
            "대기중": []
        }

        # 컨텍스트에 이슈 현황 추가
        self.context['issue_status'] = issue_status

        log = {
            "day": self.date,
            "progress_rate": self.context.get("progress_rate", 0),
            "issue_status_summary": issue_status,  # <<< 추가
            "discussions": [],
            "decisions": [],
            "summary": {},
        }

        # ===== 2. 신규 이슈 검토 =====
        for issue in self.new_issues:
            discussion = self.discuss_new_issue(issue)
            log["discussions"].append(discussion)

        # ===== 3. 진행 중 이슈 검토 =====
        for issue in self.active_issues:
            if hasattr(issue, 'status') and issue.status == "해결중":
                update = self.review_active_issue(issue)
                log["discussions"].append(update)

        # ===== 4. 요약 =====
        log["summary"] = self.generate_summary()

        return log

    def discuss_new_issue(self, issue: Dict) -> Dict:
        """신규 이슈 토론"""

        reporter = self.agents.get("시공사")
        report = reporter.report_issue(issue, self.context)

        # 각 에이전트 의견 수렴
        opinions = {}
        for name, agent in self.agents.items():
            opinion = agent.give_opinion(issue, self.context, opinions)  # 이전 의견 전달
            opinions[name] = opinion

        # 심각도 평가
        severity = self.evaluate_severity(issue, opinions)

        # 해결 방안 논의
        solutions = []
        for name, agent in self.agents.items():
            if hasattr(agent, "propose_solution"):
                sol_result = agent.propose_solution(issue, severity, self.context)
                if "solutions" in sol_result:
                    for sol in sol_result["solutions"]:
                        sol["agent"] = name
                        solutions.append(sol)

        # 건축주 최종 선택
        owner = self.agents["건축주"]
        selected = owner.select_solution(solutions, issue, self.context)

        return {
            "issue_id": issue["ID"],
            "issue_name": issue["이슈명"],
            "type": "신규",
            "report": report,
            "opinions": opinions,
            "severity": severity,
            "solutions": solutions,
            "selected": selected,
            "reasoning": self.generate_reasoning(issue, opinions, selected),
        }

    def evaluate_severity(self, issue: Dict, opinions: Dict) -> Dict:
        """심각도 평가"""

        weights = {
            "건축주": 0.5,
            "시공사": 0.5,
        }

        weighted_score = 0
        for agent_name, opinion in opinions.items():
            score = opinion.get("severity_assessment", 5)
            weight = weights.get(agent_name, 0.1)
            weighted_score += score * weight

        kpi_adjustment = self.calculate_kpi_based_severity(issue)

        min_delay = issue["지연(주)_Min"]
        max_delay = issue["지연(주)_Max"]
        min_cost = issue["비용증가(%)_Min"]
        max_cost = issue["비용증가(%)_Max"]

        severity_ratio = weighted_score / 10

        final_delay_weeks = min_delay + (max_delay - min_delay) * severity_ratio
        final_cost_pct = min_cost + (max_cost - min_cost) * severity_ratio

        final_delay_weeks *= 1 + (kpi_adjustment * 0.2)
        final_cost_pct *= 1 + (kpi_adjustment * 0.2)

        return {
            "agent_consensus": weighted_score,
            "kpi_impact": kpi_adjustment,
            "final_delay_weeks": round(final_delay_weeks, 1),
            "final_cost_increase_pct": round(final_cost_pct, 2),
        }

    def calculate_kpi_based_severity(self, issue: Dict) -> float:
        """KPI 기반 심각도 조정"""

        kpi_values = self.context.get("kpi_values", {})
        weights = issue.get("가중치", {})

        if self.method == "BIM":
            normalized_scores = []
            for kpi_name, kpi_value in kpi_values.items():
                if kpi_name in weights and weights[kpi_name] > 0:
                    norm_val = normalize_kpi_value(kpi_name, kpi_value, "BIM")
                    weighted_score = norm_val * weights[kpi_name]
                    normalized_scores.append(weighted_score)

            avg_risk = sum(normalized_scores) / len(normalized_scores) if normalized_scores else 0.5
            return (avg_risk - 0.5) * 2

        else:
            normalized_scores = []
            for kpi_name, kpi_value in kpi_values.items():
                if kpi_name in weights and weights[kpi_name] > 0:
                    norm_val = normalize_kpi_value(kpi_name, kpi_value, "TRADITIONAL")
                    weighted_score = norm_val * weights[kpi_name]
                    normalized_scores.append(weighted_score)

            avg_risk = sum(normalized_scores) / len(normalized_scores) if normalized_scores else 0.5
            return (avg_risk - 0.5) * 2

    def review_active_issue(self, issue) -> Dict:
        """진행 중인 이슈 검토"""
        return {
            "issue_id": issue.id,
            "issue_name": issue.name,
            "type": "진행중",
            "status": issue.status,
            "progress": f"{issue.progress:.1f}%",
            "note": f"{issue.duration_worked}일째 작업 중",
        }

    def generate_summary(self) -> Dict:
        """회의 요약"""
        return {
            "new_issues_count": len(self.new_issues),
            "active_issues_count": len(self.active_issues),
            "key_decisions": len(self.new_issues),
        }

    def generate_reasoning(self, issue: Dict, opinions: Dict, selected: Dict) -> str:
        """의사결정 근거 생성"""
        return f"{issue['이슈명']}에 대해 {len(opinions)}명의 에이전트가 논의. " \
               f"선택된 방안: {selected.get('reasoning', '균형잡힌 결정')}"
