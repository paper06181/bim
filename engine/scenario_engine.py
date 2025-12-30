"""
시나리오 실행 엔진
- 전통 방식 기본, 전통 방식 강화, BIM 적용 시나리오 실행
- 공정률 구간별 이슈 평가
- 멀티 에이전트 회의를 통한 resolution_level 결정
"""
from typing import List, Dict, Optional
from data.data_models import (
    ProjectInfo, IssueCard, ScenarioResult,
    ComparisonResult
)
from engine.risk_calculator import RiskCalculator
from engine.agent_meeting import AgentMeetingSystem


class ScenarioEngine:
    """시나리오 실행 엔진"""

    # 공정률 구간 정의 (0-100은 별도 처리)
    PROGRESS_SEGMENTS = ["0-25", "25-75", "75-100"]

    def __init__(self, use_llm: bool = False, verbose: bool = True):
        """
        Args:
            use_llm: LLM 사용 여부
            verbose: 상세 로그 출력 여부
        """
        self.use_llm = use_llm
        self.verbose = verbose
        self.calculator = RiskCalculator()
        self.meeting_system = AgentMeetingSystem(use_llm=use_llm)

    def _is_in_segment(self, issue_segment: str, current_segment: str) -> bool:
        """
        이슈가 현재 구간에 속하는지 확인

        Args:
            issue_segment: 이슈의 공정률 구간 (예: "0-25", "25-75", "0-100")
            current_segment: 현재 처리 중인 구간 (예: "0-25")

        Returns:
            속하면 True
        """
        # 0-100은 첫 번째 구간(0-25)에만 포함
        if issue_segment == "0-100":
            return current_segment == "0-25"

        # 0-50은 0-25 구간에 포함
        if issue_segment == "0-50":
            return current_segment == "0-25"

        # 25-100은 25-75 구간에 포함
        if issue_segment == "25-100":
            return current_segment == "25-75"

        # 정확히 일치
        return issue_segment == current_segment

    def run_scenario(self,
                      project: ProjectInfo,
                      issues: List[IssueCard],
                      scenario_name: str,
                      family: str,
                      management_level: str = "basic") -> ScenarioResult:
        """
        시나리오 실행

        Args:
            project: 프로젝트 정보
            issues: 이슈 리스트 (family에 맞는 것)
            scenario_name: 시나리오 이름
            family: "BIM" 또는 "TRAD"
            management_level: "basic" (기본 관리) 또는 "enhanced" (강화된 관리)

        Returns:
            ScenarioResult
        """
        if self.verbose:
            print(f"\n{'='*80}")
            print(f"시나리오 실행: {scenario_name}")
            print(f"  Family: {family}")
            print(f"  Management: {management_level}")
            print(f"  이슈 수: {len(issues)}")
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

        # 공정률 구간별 처리
        processed_issues = set()  # 중복 처리 방지

        for segment in self.PROGRESS_SEGMENTS:
            if self.verbose:
                print(f"\n[공정률 구간: {segment}]")

            # 해당 구간의 이슈 필터링 (중복 제거)
            segment_issues = []
            for iss in issues:
                # 이미 처리된 이슈는 스킵
                if iss.issue_id in processed_issues:
                    continue

                # 해당 구간에 속하는지 확인
                if self._is_in_segment(iss.progress_segment, segment):
                    segment_issues.append(iss)
                    processed_issues.add(iss.issue_id)

            if not segment_issues:
                if self.verbose:
                    print(f"  (이슈 없음)")
                continue

            # 1. 기본 리스크 계산
            for issue in segment_issues:
                issue.base_risk = self.calculator.compute_base_risk(issue, kpi_values)

            # base_risk 높은 순으로 정렬 (상위 이슈 우선)
            segment_issues.sort(key=lambda x: x.base_risk, reverse=True)

            # 2. 회의 진행 (resolution_level 결정)
            # management_level에 따라 LLM 사용 여부 조정 가능
            # (여기서는 단순화: enhanced면 좀 더 적극적으로 대응)
            resolutions = self.meeting_system.conduct_meeting(
                project, segment_issues, segment, family
            )

            # management_level에 따라 resolution_level 조정
            if management_level == "enhanced":
                resolutions = {k: min(1.0, v + 0.3) for k, v in resolutions.items()}

            if self.verbose:
                print(f"  이슈 {len(segment_issues)}개 평가")

            # 3. 각 이슈 평가
            segment_delay = 0.0
            segment_cost = 0.0

            for issue in segment_issues:
                resolution_level = resolutions.get(issue.issue_id, 0.5)

                eval_result = self.calculator.evaluate_issue(
                    issue, kpi_values, resolution_level
                )

                # 발생한 이슈만 집계 (NONE은 제외)
                if eval_result["status"] != "NONE":
                    segment_delay += eval_result["delay_weeks"] * 7  # 주 -> 일
                    segment_cost += eval_result["cost_pct"]

                    if eval_result["status"] == "MAJOR":
                        issues_major += 1
                        issues_occurred += 1
                    elif eval_result["status"] == "MINOR":
                        issues_minor += 1
                        issues_occurred += 1

                if self.verbose and eval_result["status"] != "NONE":
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

            if self.verbose:
                print(f"  구간 합계: 지연={segment_delay:.1f}일, 비용={segment_cost:.2f}%")

        # 4. 상한 적용
        total_delay_days = self.calculator.cap_total_delay(total_delay_days, project.duration_days)
        total_cost_pct = self.calculator.cap_total_cost(total_cost_pct)

        # 5. 최종 결과
        result.total_delay_days = total_delay_days
        result.total_cost_pct = total_cost_pct
        result.actual_duration = project.duration_days + total_delay_days
        result.actual_cost = project.base_cost * (1.0 + total_cost_pct / 100.0)
        result.issues_evaluated = len(issues)
        result.issues_occurred = issues_occurred
        result.issues_minor = issues_minor
        result.issues_major = issues_major

        if self.verbose:
            print(f"\n[최종 결과]")
            print(f"  총 지연: {total_delay_days:.1f}일 ({total_delay_days/7:.1f}주)")
            print(f"  총 비용증가: {total_cost_pct:.2f}%")
            print(f"  최종 공기: {result.actual_duration:.0f}일")
            print(f"  최종 비용: {result.actual_cost:,.0f}원")
            print(f"  발생 이슈: {issues_occurred}개 (Major: {issues_major}, Minor: {issues_minor})")

        return result

    def compare_scenarios(self,
                           baseline: ScenarioResult,
                           comparison: ScenarioResult) -> ComparisonResult:
        """
        시나리오 비교

        Args:
            baseline: 기준 시나리오
            comparison: 비교 시나리오

        Returns:
            ComparisonResult
        """
        comp = ComparisonResult(baseline=baseline, comparison=comparison)
        comp.calculate_rewards()

        if self.verbose:
            print(f"\n{'='*80}")
            print(f"시나리오 비교: {baseline.scenario_name} vs {comparison.scenario_name}")
            print(f"{'='*80}")
            print(f"  지연 감소: {comp.delay_reduction_days:.1f}일 ({comp.delay_reduction_weeks:.1f}주)")
            print(f"  비용 감소: {comp.cost_reduction_pct:.2f}%")

            if comp.delay_reduction_days > 0:
                print(f"  [+] 공기 단축 효과 있음")
            else:
                print(f"  [-] 공기 증가")

            if comp.cost_reduction_pct > 0:
                print(f"  [+] 비용 절감 효과 있음")
            else:
                print(f"  [-] 비용 증가")

        return comp


def test_scenario_engine():
    """테스트 함수"""
    from data.excel_loader import get_loader
    from data.data_models import ProjectInfo

    print("=" * 80)
    print("시나리오 엔진 테스트")
    print("=" * 80)

    # 데이터 로드
    loader = get_loader()

    # CASE 로드
    case = loader.load_case_from_matrix("도심", "상업지역", "중심상업지역", 800)
    print(f"\nCASE: {case}")
    print(f"  BIM KPI: {case.kpi_bim}")
    print(f"  TRAD KPI: {case.kpi_trad}")

    # 프로젝트 정보
    project = ProjectInfo(
        project_name="테스트 프로젝트",
        duration_days=365,
        base_cost=5_000_000_000,
        case=case
    )

    # 이슈 로드
    issues_bim = loader.load_issue_cards("BIM")
    issues_trad = loader.load_issue_cards("TRAD")
    print(f"\n이슈 카드: BIM={len(issues_bim)}개, TRAD={len(issues_trad)}개")

    # 엔진 생성
    engine = ScenarioEngine(use_llm=False, verbose=True)

    # 시나리오 1: 전통 방식 기본
    print("\n" + "="*80)
    print("시나리오 1: 전통 방식 - 기본 관리")
    print("="*80)
    result_trad_basic = engine.run_scenario(
        project, issues_trad[:20], "전통 방식 (기본)", "TRAD", "basic"
    )

    # 시나리오 2: 전통 방식 강화
    print("\n" + "="*80)
    print("시나리오 2: 전통 방식 - 강화된 관리")
    print("="*80)
    result_trad_enhanced = engine.run_scenario(
        project, issues_trad[:20], "전통 방식 (강화)", "TRAD", "enhanced"
    )

    # 시나리오 3: BIM 적용
    print("\n" + "="*80)
    print("시나리오 3: BIM 적용")
    print("="*80)
    result_bim = engine.run_scenario(
        project, issues_bim[:20], "BIM 적용", "BIM", "enhanced"
    )

    # 비교 1: 전통 기본 vs 전통 강화
    comp1 = engine.compare_scenarios(result_trad_basic, result_trad_enhanced)

    # 비교 2: 전통 강화 vs BIM
    comp2 = engine.compare_scenarios(result_trad_enhanced, result_bim)

    print("\n테스트 완료!")


if __name__ == "__main__":
    test_scenario_engine()
