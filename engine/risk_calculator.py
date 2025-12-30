"""
리스크 계산 엔진
- 확률 기반이 아닌 KPI + Severity 기반 리스크 계산
- resolution_level을 통한 해결 노력 반영
- 임계값 기반 발생 여부 결정 (확률 샘플링 없음)
"""
from typing import Dict, List
from data.data_models import IssueCard, KPISet


class RiskCalculator:
    """리스크 계산기"""

    # Severity 계수
    SEVERITY_FACTORS = {
        "S1": 1.0 / 3.0,  # 0.33
        "S2": 2.0 / 3.0,  # 0.67
        "S3": 1.0,        # 1.00
    }

    # 해결 노력 효과 계수 (0~1)
    K_RESOLVE = 0.6

    # 임계값 (공기→비용 전환 모델에 맞춰 조정)
    THRESHOLD_NONE = 0.20   # 이 값 미만: 발생하지 않음
    THRESHOLD_MINOR = 0.45  # 이 값 미만: 경미한 수준

    def __init__(self):
        pass

    @classmethod
    def compute_risk_index(cls, issue: IssueCard, kpi_values: Dict[str, float]) -> float:
        """
        이슈별 리스크 인덱스 계산

        Args:
            issue: 이슈 카드
            kpi_values: KPI 값 딕셔너리 (예: {"WD": 0.33, "CD": 0.11, ...})

        Returns:
            리스크 인덱스 (가중합)

        Note:
            AF, PL은 역방향 지표 (높을수록 품질 좋음 = 리스크 낮음)
            따라서 (1 - value)로 변환하여 계산
        """
        value = 0.0
        for kpi_key, weight in issue.kpi_weights.items():
            kpi_val = kpi_values.get(kpi_key, 0.0)

            # AF, PL은 역방향 지표: 높을수록 품질 좋음 = 리스크 낮음
            if kpi_key in ['AF', 'PL']:
                kpi_val = 1.0 - kpi_val

            value += kpi_val * weight
        return value

    @classmethod
    def compute_base_risk(cls, issue: IssueCard, kpi_values: Dict[str, float]) -> float:
        """
        기본 리스크 점수 계산

        Args:
            issue: 이슈 카드
            kpi_values: KPI 값 딕셔너리

        Returns:
            기본 리스크 점수
        """
        severity_factor = cls.SEVERITY_FACTORS.get(issue.severity, 0.67)
        risk_index = cls.compute_risk_index(issue, kpi_values)
        return severity_factor * risk_index

    @classmethod
    def compute_effective_risk(cls, base_risk: float, resolution_level: float) -> float:
        """
        해결 노력(resolution_level) 반영 후 실제 리스크 계산

        Args:
            base_risk: 기본 리스크 점수
            resolution_level: 해결 수준 (0.0 ~ 1.0)

        Returns:
            실제 리스크 점수
        """
        return base_risk * (1.0 - cls.K_RESOLVE * resolution_level)

    @classmethod
    def compute_impact_factor(cls, effective_risk: float) -> float:
        """
        리스크 점수 → 영향도 계산 (0.0 ~ 1.0)

        Args:
            effective_risk: 실제 리스크 점수

        Returns:
            영향도 (0.0: 영향 없음, 1.0: 최대 영향)
        """
        if effective_risk <= cls.THRESHOLD_NONE:
            return 0.0
        elif effective_risk >= cls.THRESHOLD_MINOR:
            return 1.0
        else:
            # 선형 보간
            return (effective_risk - cls.THRESHOLD_NONE) / (cls.THRESHOLD_MINOR - cls.THRESHOLD_NONE)

    @classmethod
    def compute_actual_impact(cls,
                               issue: IssueCard,
                               impact_factor: float) -> tuple[float, float]:
        """
        실제 지연/비용 계산

        현실적 모델: 공기 지연을 최소화하고 대신 비용으로 흡수
        (추가 인력, 야간 작업, 장비 추가 등으로 일정 준수)

        Args:
            issue: 이슈 카드
            impact_factor: 영향도 (0.0 ~ 1.0)

        Returns:
            (실제 지연(주), 실제 비용증가(%))
        """
        # 기본 계산
        base_delay_weeks = issue.delay_min_weeks + impact_factor * (issue.delay_max_weeks - issue.delay_min_weeks)
        base_cost_pct = issue.cost_min_pct + impact_factor * (issue.cost_max_pct - issue.cost_min_pct)

        # 공기 지연을 비용으로 전환하는 비율
        DELAY_TO_COST_RATIO = 0.75  # 지연의 75%를 비용으로 전환

        # 전환된 지연 (비용으로 흡수)
        absorbed_delay = base_delay_weeks * DELAY_TO_COST_RATIO

        # 실제 지연 (25%만 남김)
        actual_delay_weeks = base_delay_weeks * (1 - DELAY_TO_COST_RATIO)

        # 흡수된 지연을 비용으로 전환
        # 1주 지연 흡수 = 약 0.4% 비용 증가로 가정 (더 현실적으로)
        WEEK_TO_COST_CONVERSION = 0.4
        absorbed_cost = absorbed_delay * WEEK_TO_COST_CONVERSION

        # 최종 비용 (원래 비용 + 흡수된 지연 비용)
        actual_cost_pct = base_cost_pct + absorbed_cost

        # 최종 감쇠 적용 (여전히 과도한 영향 방지)
        DELAY_DAMPENING = 0.6   # 지연은 60% 적용 (더 줄임)
        COST_DAMPENING = 0.8    # 비용은 80% 적용 (더 높임)

        actual_delay_weeks *= DELAY_DAMPENING
        actual_cost_pct *= COST_DAMPENING

        return actual_delay_weeks, actual_cost_pct

    @classmethod
    def determine_status(cls, effective_risk: float) -> str:
        """
        리스크 점수 → 발생 상태 결정

        Args:
            effective_risk: 실제 리스크 점수

        Returns:
            "NONE" (발생 안 함), "MINOR" (경미), "MAJOR" (심각)
        """
        if effective_risk < cls.THRESHOLD_NONE:
            return "NONE"
        elif effective_risk < cls.THRESHOLD_MINOR:
            return "MINOR"
        else:
            return "MAJOR"

    @classmethod
    def evaluate_issue(cls,
                        issue: IssueCard,
                        kpi_values: Dict[str, float],
                        resolution_level: float = 0.5) -> dict:
        """
        이슈 종합 평가

        Args:
            issue: 이슈 카드
            kpi_values: KPI 값
            resolution_level: 해결 수준 (0.0 ~ 1.0)

        Returns:
            평가 결과 딕셔너리
        """
        # 1. 기본 리스크
        base_risk = cls.compute_base_risk(issue, kpi_values)

        # 2. 해결 노력 반영
        effective_risk = cls.compute_effective_risk(base_risk, resolution_level)

        # 3. 영향도
        impact_factor = cls.compute_impact_factor(effective_risk)

        # 4. 실제 지연/비용
        delay_weeks, cost_pct = cls.compute_actual_impact(issue, impact_factor)

        # 5. 상태
        status = cls.determine_status(effective_risk)

        # 이슈 객체 업데이트
        issue.base_risk = base_risk
        issue.resolution_level = resolution_level
        issue.effective_risk = effective_risk
        issue.impact_factor = impact_factor
        issue.actual_delay_weeks = delay_weeks
        issue.actual_cost_pct = cost_pct

        return {
            "issue_id": issue.issue_id,
            "base_risk": base_risk,
            "effective_risk": effective_risk,
            "impact_factor": impact_factor,
            "delay_weeks": delay_weeks,
            "cost_pct": cost_pct,
            "status": status
        }

    @classmethod
    def cap_total_delay(cls, total_delay_days: float, planned_duration_days: int,
                         max_shortening_ratio: float = 0.1) -> float:
        """
        전체 공기 단축 상한 적용

        Args:
            total_delay_days: 계산된 총 지연 (음수면 단축)
            planned_duration_days: 계획 공기 (일)
            max_shortening_ratio: 최대 단축 비율 (기본 10%)

        Returns:
            상한 적용된 지연 (일)
        """
        max_shortening_days = planned_duration_days * max_shortening_ratio

        if total_delay_days < -max_shortening_days:
            return -max_shortening_days

        return total_delay_days

    @classmethod
    def cap_total_cost(cls, total_cost_pct: float, max_saving_ratio: float = 0.2) -> float:
        """
        전체 비용 절감 상한 적용

        Args:
            total_cost_pct: 계산된 총 비용증가 (음수면 절감)
            max_saving_ratio: 최대 절감 비율 (기본 20%)

        Returns:
            상한 적용된 비용증가 (%)
        """
        max_saving_pct = max_saving_ratio * 100

        if total_cost_pct < -max_saving_pct:
            return -max_saving_pct

        return total_cost_pct
