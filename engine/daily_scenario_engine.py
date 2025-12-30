"""
일 단위 시나리오 실행 엔진
- 매일 공정률 계산
- 해당 일자에 발생 가능한 이슈 체크
- 매일 리스크 평가 및 처리
"""
from typing import List, Dict, Optional
from data.data_models import (
    ProjectInfo, IssueCard, ScenarioResult,
    ComparisonResult
)
from engine.risk_calculator import RiskCalculator
from engine.agent_meeting import AgentMeetingSystem
from utils.daily_logger import DailyLogger


class DailyScenarioEngine:
    """일 단위 시나리오 실행 엔진"""

    def __init__(self, use_llm: bool = False, verbose: bool = True, enable_logging: bool = True):
        """
        Args:
            use_llm: LLM 사용 여부
            verbose: 상세 로그 출력 여부
            enable_logging: 매일 로그 저장 여부
        """
        self.use_llm = use_llm
        self.verbose = verbose
        self.enable_logging = enable_logging
        self.calculator = RiskCalculator()
        self.meeting_system = AgentMeetingSystem(use_llm=use_llm)
        self.logger = DailyLogger() if enable_logging else None

    def _calculate_progress(self, current_day: int, total_days: int) -> float:
        """
        현재 공정률 계산 (선형 가정)

        Args:
            current_day: 현재 일수 (1부터 시작)
            total_days: 전체 공기

        Returns:
            공정률 (0.0 ~ 1.0)
        """
        return current_day / total_days

    def _get_segment_for_progress(self, progress: float) -> str:
        """
        공정률에 해당하는 구간 반환

        Args:
            progress: 공정률 (0.0 ~ 1.0)

        Returns:
            구간 문자열 ("0-25", "25-75", "75-100")
        """
        progress_pct = progress * 100
        if progress_pct < 25:
            return "0-25"
        elif progress_pct < 75:
            return "25-75"
        else:
            return "75-100"

    def _is_issue_in_segment(self, issue: IssueCard, segment: str) -> bool:
        """
        이슈가 해당 구간에 속하는지 확인

        Args:
            issue: 이슈 카드
            segment: 구간 ("0-25", "25-75", "75-100")

        Returns:
            속하면 True
        """
        issue_seg = issue.progress_segment

        # 0-100은 모든 구간
        if issue_seg == "0-100":
            return True

        # 0-50은 0-25 구간
        if issue_seg == "0-50":
            return segment == "0-25"

        # 25-100은 25-75, 75-100 구간
        if issue_seg == "25-100":
            return segment in ["25-75", "75-100"]

        # 정확히 일치
        return issue_seg == segment

    def run_scenario(self,
                      project: ProjectInfo,
                      issues: List[IssueCard],
                      scenario_name: str,
                      family: str,
                      management_level: str = "basic") -> ScenarioResult:
        """
        일 단위 시나리오 실행

        Args:
            project: 프로젝트 정보
            issues: 이슈 리스트
            scenario_name: 시나리오 이름
            family: "BIM" 또는 "TRAD"
            management_level: "basic" 또는 "enhanced"

        Returns:
            ScenarioResult
        """
        if self.verbose:
            print(f"\n{'='*80}")
            print(f"일 단위 시나리오 실행: {scenario_name}")
            print(f"  Family: {family}")
            print(f"  Management: {management_level}")
            print(f"  이슈 수: {len(issues)}개")
            print(f"  총 공기: {project.duration_days}일")
            print(f"{'='*80}")

        # KPI 값 선택
        if family == "BIM":
            kpi_values = project.case.kpi_bim.values
        else:
            kpi_values = project.case.kpi_trad.values

        # 결과 객체
        result = ScenarioResult(
            scenario_name=scenario_name,
            family=family,
            management_level=management_level
        )

        total_delay_days = 0.0
        total_cost_pct = 0.0
        issues_occurred = 0
        issues_minor = 0
        issues_major = 0

        # 이슈별 기본 리스크 계산
        for issue in issues:
            issue.base_risk = self.calculator.compute_base_risk(issue, kpi_values)

        # 처리된 이슈 추적 (이슈별로 한번만 처리)
        processed_issues = set()

        # 구간별 이슈 수집
        segment_issues_dict = {"0-25": [], "25-75": [], "75-100": []}

        for issue in issues:
            if self._is_issue_in_segment(issue, "0-25"):
                segment_issues_dict["0-25"].append(issue)
            if self._is_issue_in_segment(issue, "25-75"):
                segment_issues_dict["25-75"].append(issue)
            if self._is_issue_in_segment(issue, "75-100"):
                segment_issues_dict["75-100"].append(issue)

        if self.verbose:
            print(f"\n일 단위 시뮬레이션 시작...")
            print(f"  0-25% 구간: {len(segment_issues_dict['0-25'])}개 이슈")
            print(f"  25-75% 구간: {len(segment_issues_dict['25-75'])}개 이슈")
            print(f"  75-100% 구간: {len(segment_issues_dict['75-100'])}개 이슈")

        # 일 단위 시뮬레이션 - 매일 회의하고 해당 공정률의 이슈 처리
        for day in range(1, project.duration_days + 1):
            # 현재 공정률 및 구간
            progress = self._calculate_progress(day, project.duration_days)
            segment = self._get_segment_for_progress(progress)

            # 오늘 처리할 이슈들 (해당 구간에 속하고 아직 처리 안된 이슈)
            daily_issues = []
            for issue in segment_issues_dict[segment]:
                if issue.issue_id not in processed_issues:
                    daily_issues.append(issue)

            # 이슈 처리
            if daily_issues:
                # 리스크 정렬
                daily_issues.sort(key=lambda x: x.base_risk, reverse=True)

                # 매일 회의 진행 (LLM 또는 규칙 기반)
                if self.use_llm:
                    resolutions = self.meeting_system.conduct_meeting(
                        project, daily_issues, segment, family
                    )
                else:
                    resolutions = self.meeting_system._conduct_rule_based_meeting(daily_issues)

                # Management level 조정
                if management_level == "enhanced":
                    resolutions = {k: min(1.0, v + 0.3) for k, v in resolutions.items()}

                # 매일 회의 로그 기록
                if self.logger:
                    self.logger.log_daily_meeting(day, progress, segment, daily_issues, resolutions)

                # 오늘 발생한 이슈 카운트
                day_issues_occurred = 0
                day_delay = 0.0
                day_cost = 0.0

                for issue in daily_issues:
                    resolution_level = resolutions.get(issue.issue_id, 0.5)

                    eval_result = self.calculator.evaluate_issue(
                        issue, kpi_values, resolution_level
                    )

                    # 발생한 이슈만 집계
                    if eval_result["status"] != "NONE":
                        delay_today = eval_result["delay_weeks"] * 7
                        cost_today = eval_result["cost_pct"]

                        total_delay_days += delay_today
                        total_cost_pct += cost_today

                        day_delay += delay_today
                        day_cost += cost_today
                        day_issues_occurred += 1

                        if eval_result["status"] == "MAJOR":
                            issues_major += 1
                            issues_occurred += 1
                        elif eval_result["status"] == "MINOR":
                            issues_minor += 1
                            issues_occurred += 1

                        if self.verbose:
                            print(f"[Day {day:3d}, {progress*100:5.1f}%] {issue.issue_id}: {eval_result['status']:5s} | "
                                  f"R={eval_result['effective_risk']:.3f} | "
                                  f"지연={eval_result['delay_weeks']:.1f}주, "
                                  f"비용={eval_result['cost_pct']:.2f}%")

                    # 처리 완료 표시
                    processed_issues.add(issue.issue_id)

                # 매일 결과 로그 기록
                if self.logger and day_issues_occurred > 0:
                    self.logger.log_daily_result(day, day_issues_occurred, day_delay, day_cost)

        # 구간별 결과 저장
        for seg in ["0-25", "25-75", "75-100"]:
            result.segment_results[seg] = {
                "delay_days": 0.0,  # 일 단위에서는 구간별 합계 생략
                "cost_pct": 0.0,
                "issues_count": len(segment_issues_dict[seg])
            }

        # 상한 적용
        total_delay_days = self.calculator.cap_total_delay(total_delay_days, project.duration_days)
        total_cost_pct = self.calculator.cap_total_cost(total_cost_pct)

        # 최종 결과
        result.total_delay_days = total_delay_days
        result.total_cost_pct = total_cost_pct
        result.actual_duration = project.duration_days + total_delay_days
        result.actual_cost = project.base_cost * (1.0 + total_cost_pct / 100.0)
        result.issues_evaluated = len(issues)
        result.issues_occurred = issues_occurred
        result.issues_minor = issues_minor
        result.issues_major = issues_major

        # EVMS 통합 - 일정 지연을 비용으로 완전 흡수
        result.apply_evms_integration(project.duration_days, project.base_cost)

        if self.verbose:
            print(f"\n[최종 결과]")
            print(f"  총 지연: {total_delay_days:.1f}일 ({total_delay_days/7:.1f}주)")
            print(f"  직접 비용증가: {total_cost_pct:.2f}%")
            print(f"  지연 환산 비용: {result.delay_cost_equivalent:,.0f}원 ({result.delay_cost_equivalent/100000000:.2f}억원)")
            print(f"  ─────────────────────────────────────")
            print(f"  통합 총 비용: {result.integrated_total_cost:,.0f}원 ({result.integrated_total_cost/100000000:.2f}억원)")
            print(f"  통합 비용 증가율: {result.integrated_cost_pct:.2f}%")
            print(f"  ─────────────────────────────────────")
            print(f"  최종 공기: {result.actual_duration:.0f}일")
            print(f"  최종 비용: {result.actual_cost:,.0f}원")
            print(f"  발생 이슈: {issues_occurred}개 (Major: {issues_major}, Minor: {issues_minor})")

        # 로그 저장
        if self.logger:
            self.logger.save_meeting_log(scenario_name)
            self.logger.save_daily_report(scenario_name, total_delay_days, total_cost_pct)

        return result

    def _process_segment_issues(self,
                                  segment_issues: List[IssueCard],
                                  segment: str,
                                  family: str,
                                  management_level: str,
                                  kpi_values: Dict[str, float],
                                  result: ScenarioResult,
                                  total_delay_days: float,
                                  total_cost_pct: float,
                                  issues_occurred: int,
                                  issues_minor: int,
                                  issues_major: int) -> tuple:
        """
        구간 이슈 처리

        Returns:
            (total_delay_days, total_cost_pct, issues_occurred, issues_minor, issues_major)
        """
        if not segment_issues:
            return total_delay_days, total_cost_pct, issues_occurred, issues_minor, issues_major

        # 리스크 높은 순으로 정렬
        segment_issues.sort(key=lambda x: x.base_risk, reverse=True)

        # 회의 진행 (resolution_level 결정)
        # Note: project 인자가 필요하지만 여기선 간략화
        resolutions = self.meeting_system._conduct_rule_based_meeting(segment_issues)

        # Management level 조정
        if management_level == "enhanced":
            resolutions = {k: min(1.0, v + 0.3) for k, v in resolutions.items()}

        # 각 이슈 평가
        segment_delay = 0.0
        segment_cost = 0.0

        for issue in segment_issues:
            resolution_level = resolutions.get(issue.issue_id, 0.5)

            eval_result = self.calculator.evaluate_issue(
                issue, kpi_values, resolution_level
            )

            # 발생한 이슈만 집계
            if eval_result["status"] != "NONE":
                segment_delay += eval_result["delay_weeks"] * 7
                segment_cost += eval_result["cost_pct"]

                if eval_result["status"] == "MAJOR":
                    issues_major += 1
                    issues_occurred += 1
                elif eval_result["status"] == "MINOR":
                    issues_minor += 1
                    issues_occurred += 1

                if self.verbose:
                    print(f"    {issue.issue_id}: {eval_result['status']:5s} | "
                          f"R={eval_result['effective_risk']:.3f} | "
                          f"지연={eval_result['delay_weeks']:.1f}주, "
                          f"비용={eval_result['cost_pct']:.2f}%")

        total_delay_days += segment_delay
        total_cost_pct += segment_cost

        # 구간별 결과 저장
        result.segment_results[segment] = {
            "delay_days": segment_delay,
            "cost_pct": segment_cost,
            "issues_count": len(segment_issues)
        }

        if self.verbose and segment_delay > 0:
            print(f"  구간 합계: 지연={segment_delay:.1f}일, 비용={segment_cost:.2f}%")

        return total_delay_days, total_cost_pct, issues_occurred, issues_minor, issues_major
