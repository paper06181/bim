"""
일 단위 시나리오 실행 엔진 V2
- 구간 나누지 않고 매일 이슈 발생 확률 체크
- 발생한 이슈들을 LLM이 한번에 종합 판단
- 더 현실적인 시뮬레이션
"""
import random
from typing import List, Dict, Optional
from data.data_models import (
    ProjectInfo, IssueCard, ScenarioResult,
    ComparisonResult
)
from engine.risk_calculator import RiskCalculator
from engine.agent_meeting import AgentMeetingSystem
from utils.daily_logger import DailyLogger


class DailyScenarioEngineV2:
    """일 단위 시나리오 실행 엔진 V2 - 확률 기반"""

    def __init__(self, use_llm: bool = False, verbose: bool = True, enable_logging: bool = True, random_seed: int = None):
        """
        Args:
            use_llm: LLM 사용 여부
            verbose: 상세 로그 출력 여부
            enable_logging: 매일 로그 저장 여부
            random_seed: 랜덤 시드 (재현성)
        """
        self.use_llm = use_llm
        self.verbose = verbose
        self.enable_logging = enable_logging
        self.calculator = RiskCalculator()
        self.meeting_system = AgentMeetingSystem(use_llm=use_llm)
        self.logger = DailyLogger() if enable_logging else None

        if random_seed is not None:
            random.seed(random_seed)

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

    def _should_issue_occur(self, issue: IssueCard, progress: float, kpi_values: Dict[str, float]) -> bool:
        """
        이슈 발생 여부 결정 (확률 기반)

        Args:
            issue: 이슈 카드
            progress: 현재 공정률 (0.0 ~ 1.0)
            kpi_values: KPI 값

        Returns:
            발생하면 True
        """
        # 이슈의 발생 구간 체크
        if not self._is_in_progress_range(issue, progress):
            return False

        # 기본 발생 확률: base_risk를 직접 사용
        # base_risk는 이미 0~1 사이 값 (KPI 가중치 반영됨)
        base_prob = issue.base_risk * 0.3  # 전체 기간 중 30% 확률로 조정

        # 심각도에 따른 가중치
        severity_multiplier = {
            'S1': 0.8,   # 낮음 - 덜 자주 발생
            'S2': 1.0,   # 보통
            'S3': 1.2    # 높음 - 더 자주 발생
        }
        multiplier = severity_multiplier.get(issue.severity, 1.0)

        final_prob = base_prob * multiplier

        # 일일 발생 확률로 변환 (전체 기간 동안 분산)
        daily_prob = final_prob / 365.0

        return random.random() < daily_prob

    def _is_in_progress_range(self, issue: IssueCard, progress: float) -> bool:
        """
        이슈가 현재 공정률 범위에 속하는지 확인

        Args:
            issue: 이슈 카드
            progress: 현재 공정률 (0.0 ~ 1.0)

        Returns:
            속하면 True
        """
        seg = issue.progress_segment

        if seg == "0-100":
            return True
        elif seg == "0-50":
            return progress < 0.5
        elif seg == "25-100":
            return progress >= 0.25
        elif seg == "0-25":
            return progress < 0.25
        elif seg == "25-75":
            return 0.25 <= progress < 0.75
        elif seg == "75-100":
            return progress >= 0.75
        else:
            return True

    def run_scenario(self,
                      project: ProjectInfo,
                      issues: List[IssueCard],
                      scenario_name: str,
                      family: str,
                      management_level: str = "basic") -> ScenarioResult:
        """
        일 단위 시나리오 실행 (확률 기반)

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
            print(f"일 단위 시나리오 실행 V2 (확률 기반): {scenario_name}")
            print(f"  Family: {family}")
            print(f"  Management: {management_level}")
            print(f"  이슈 풀: {len(issues)}개")
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

        # 처리된 이슈 추적 (이슈별로 한번만 발생)
        processed_issues = set()

        # 일 단위 시뮬레이션
        if self.verbose:
            print(f"\n일 단위 시뮬레이션 시작 (매일 확률 기반 이슈 발생)...")

        for day in range(1, project.duration_days + 1):
            # 현재 공정률
            progress = self._calculate_progress(day, project.duration_days)

            # 오늘 발생한 이슈들 체크
            daily_issues = []
            for issue in issues:
                if issue.issue_id not in processed_issues:
                    # 확률적으로 발생 여부 결정
                    if self._should_issue_occur(issue, progress, kpi_values):
                        daily_issues.append(issue)
                        processed_issues.add(issue.issue_id)

            # 발생한 이슈가 있으면 LLM 회의 진행
            if daily_issues:
                if self.verbose:
                    print(f"\n[Day {day}, {progress*100:5.1f}%] 발생 이슈: {len(daily_issues)}개")

                # LLM이 모든 발생 이슈를 한번에 종합 판단
                if self.use_llm:
                    resolutions = self.meeting_system.conduct_meeting(
                        project, daily_issues, f"{int(progress*100)}%", family
                    )
                else:
                    resolutions = self.meeting_system._conduct_rule_based_meeting(daily_issues)

                # Management level 조정
                if management_level == "enhanced":
                    resolutions = {k: min(1.0, v + 0.3) for k, v in resolutions.items()}

                # 매일 회의 로그 기록
                if self.logger:
                    self.logger.log_daily_meeting(day, progress, f"{int(progress*100)}%", daily_issues, resolutions)

                # 오늘 발생한 이슈 처리
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
                            print(f"  → {issue.issue_id}: {eval_result['status']:5s} | "
                                  f"R={eval_result['effective_risk']:.3f} | "
                                  f"지연={eval_result['delay_weeks']:.1f}주, "
                                  f"비용={eval_result['cost_pct']:.2f}%")

                # 매일 결과 로그 기록
                if self.logger and day_issues_occurred > 0:
                    self.logger.log_daily_result(day, day_issues_occurred, day_delay, day_cost)

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
