"""
보상 및 페널티 시스템
건설 프로젝트의 성과 기반 인센티브/디스인센티브 구조
"""
from typing import Dict, Tuple
from dataclasses import dataclass


@dataclass
class IncentiveConfig:
    """인센티브 설정"""
    # 공기 관련
    early_completion_bonus_per_day: float = 1000000.0  # 조기 완료 보너스 (원/일)
    delay_penalty_per_day: float = 1500000.0           # 지연 페널티 (원/일)
    max_bonus_days: int = 30                           # 최대 보너스 적용 일수
    max_penalty_days: int = 60                         # 최대 페널티 적용 일수

    # 비용 관련
    cost_savings_share_rate: float = 0.5              # 비용 절감 분배율 (50%)
    cost_overrun_penalty_rate: float = 0.3            # 비용 초과 페널티율 (30%)

    # 품질 관련
    quality_bonus_threshold: float = 0.9               # 품질 보너스 기준 (90% 이상)
    quality_bonus_amount: float = 50000000.0           # 품질 보너스 금액 (5천만원)
    quality_penalty_threshold: float = 0.6             # 품질 페널티 기준 (60% 미만)
    quality_penalty_amount: float = 30000000.0         # 품질 페널티 금액 (3천만원)


class IncentiveSystem:
    """보상 및 페널티 계산 시스템"""

    def __init__(self, config: IncentiveConfig = None):
        """
        Args:
            config: 인센티브 설정 (None이면 기본값 사용)
        """
        self.config = config if config else IncentiveConfig()

    def calculate_schedule_incentive(self,
                                     planned_duration: int,
                                     actual_duration: float) -> Tuple[float, str]:
        """
        공기 관련 인센티브/페널티 계산

        Args:
            planned_duration: 계획 공기 (일)
            actual_duration: 실제 공기 (일)

        Returns:
            (금액, 설명) - 양수=보너스, 음수=페널티
        """
        delay_days = actual_duration - planned_duration

        if delay_days < 0:
            # 조기 완료 - 보너스
            early_days = min(abs(delay_days), self.config.max_bonus_days)
            bonus = early_days * self.config.early_completion_bonus_per_day
            desc = f"조기 완료 보너스 ({early_days:.0f}일)"
            return bonus, desc
        elif delay_days > 0:
            # 지연 - 페널티
            penalty_days = min(delay_days, self.config.max_penalty_days)
            penalty = -penalty_days * self.config.delay_penalty_per_day
            desc = f"지연 페널티 ({penalty_days:.0f}일)"
            return penalty, desc
        else:
            return 0.0, "정시 완료"

    def calculate_cost_incentive(self,
                                 planned_cost: float,
                                 actual_cost: float) -> Tuple[float, str]:
        """
        비용 관련 인센티브/페널티 계산

        Args:
            planned_cost: 계획 비용 (원)
            actual_cost: 실제 비용 (원)

        Returns:
            (금액, 설명) - 양수=보너스, 음수=페널티
        """
        cost_diff = planned_cost - actual_cost

        if cost_diff > 0:
            # 비용 절감 - 보너스 (절감액의 일정 비율)
            bonus = cost_diff * self.config.cost_savings_share_rate
            desc = f"비용 절감 보너스 (절감액의 {self.config.cost_savings_share_rate*100:.0f}%)"
            return bonus, desc
        elif cost_diff < 0:
            # 비용 초과 - 페널티
            penalty = cost_diff * self.config.cost_overrun_penalty_rate
            desc = f"비용 초과 페널티 (초과액의 {self.config.cost_overrun_penalty_rate*100:.0f}%)"
            return penalty, desc
        else:
            return 0.0, "예산 준수"

    def calculate_quality_incentive(self,
                                    issue_detection_rate: float,
                                    issues_occurred: int,
                                    issues_evaluated: int) -> Tuple[float, str]:
        """
        품질 관련 인센티브/페널티 계산

        Args:
            issue_detection_rate: 이슈 탐지율 (0~1)
            issues_occurred: 발생한 이슈 수
            issues_evaluated: 평가한 이슈 수

        Returns:
            (금액, 설명) - 양수=보너스, 음수=페널티
        """
        # 이슈 발생률로 품질 평가 (낮을수록 좋음)
        if issues_evaluated > 0:
            issue_occurrence_rate = issues_occurred / issues_evaluated
            quality_score = 1.0 - issue_occurrence_rate
        else:
            quality_score = 1.0

        if quality_score >= self.config.quality_bonus_threshold:
            bonus = self.config.quality_bonus_amount
            desc = f"우수 품질 보너스 (품질점수: {quality_score*100:.1f}%)"
            return bonus, desc
        elif quality_score < self.config.quality_penalty_threshold:
            penalty = -self.config.quality_penalty_amount
            desc = f"품질 미달 페널티 (품질점수: {quality_score*100:.1f}%)"
            return penalty, desc
        else:
            return 0.0, f"품질 기준 충족 (품질점수: {quality_score*100:.1f}%)"

    def calculate_total_incentive(self,
                                  planned_duration: int,
                                  actual_duration: float,
                                  planned_cost: float,
                                  actual_cost: float,
                                  issues_occurred: int,
                                  issues_evaluated: int) -> Dict[str, any]:
        """
        전체 인센티브/페널티 계산

        Args:
            planned_duration: 계획 공기 (일)
            actual_duration: 실제 공기 (일)
            planned_cost: 계획 비용 (원)
            actual_cost: 실제 비용 (원)
            issues_occurred: 발생한 이슈 수
            issues_evaluated: 평가한 이슈 수

        Returns:
            인센티브 상세 정보 딕셔너리
        """
        # 각 항목별 계산
        schedule_amt, schedule_desc = self.calculate_schedule_incentive(
            planned_duration, actual_duration
        )

        cost_amt, cost_desc = self.calculate_cost_incentive(
            planned_cost, actual_cost
        )

        quality_amt, quality_desc = self.calculate_quality_incentive(
            0.0,  # detection_rate는 별도 계산 필요
            issues_occurred,
            issues_evaluated
        )

        # 총합
        total_incentive = schedule_amt + cost_amt + quality_amt

        return {
            'schedule_incentive': schedule_amt,
            'schedule_desc': schedule_desc,
            'cost_incentive': cost_amt,
            'cost_desc': cost_desc,
            'quality_incentive': quality_amt,
            'quality_desc': quality_desc,
            'total_incentive': total_incentive,
            'is_bonus': total_incentive > 0,
            'is_penalty': total_incentive < 0
        }

    def generate_incentive_report(self, incentive_result: Dict) -> str:
        """
        인센티브 보고서 생성

        Args:
            incentive_result: calculate_total_incentive 결과

        Returns:
            포맷팅된 보고서 문자열
        """
        report = f"""
{'='*80}
보상 및 페널티 내역
{'='*80}

[공기 인센티브]
  금액: {incentive_result['schedule_incentive']:>15,.0f}원
  설명: {incentive_result['schedule_desc']}

[비용 인센티브]
  금액: {incentive_result['cost_incentive']:>15,.0f}원
  설명: {incentive_result['cost_desc']}

[품질 인센티브]
  금액: {incentive_result['quality_incentive']:>15,.0f}원
  설명: {incentive_result['quality_desc']}

{'─'*80}
[총 인센티브]
  금액: {incentive_result['total_incentive']:>15,.0f}원
  구분: {'보너스 지급' if incentive_result['is_bonus'] else '페널티 부과' if incentive_result['is_penalty'] else '인센티브 없음'}
{'='*80}
"""
        return report
