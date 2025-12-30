"""
EVMS (Earned Value Management System) 구현
비용과 기간을 통합하여 프로젝트 성과를 측정
"""
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EVMSMetrics:
    """EVMS 주요 지표"""
    # 기본 값들
    planned_value: float = 0.0          # PV (Planned Value) - 계획 가치
    earned_value: float = 0.0           # EV (Earned Value) - 획득 가치
    actual_cost: float = 0.0            # AC (Actual Cost) - 실제 비용

    # 분산 (Variance)
    cost_variance: float = 0.0          # CV = EV - AC
    schedule_variance: float = 0.0      # SV = EV - PV

    # 성과 지수 (Performance Index)
    cost_performance_index: float = 1.0  # CPI = EV / AC
    schedule_performance_index: float = 1.0  # SPI = EV / PV

    # 예측 지표
    estimate_at_completion: float = 0.0  # EAC - 완료 시점 예상 비용
    estimate_to_complete: float = 0.0    # ETC - 완료까지 필요한 비용
    variance_at_completion: float = 0.0  # VAC = BAC - EAC
    to_complete_performance_index: float = 1.0  # TCPI

    def calculate_derived_metrics(self, budget_at_completion: float):
        """파생 지표 계산"""
        # 분산
        self.cost_variance = self.earned_value - self.actual_cost
        self.schedule_variance = self.earned_value - self.planned_value

        # 성과 지수
        if self.actual_cost > 0:
            self.cost_performance_index = self.earned_value / self.actual_cost
        else:
            self.cost_performance_index = 1.0

        if self.planned_value > 0:
            self.schedule_performance_index = self.earned_value / self.planned_value
        else:
            self.schedule_performance_index = 1.0

        # 완료 시점 예측 (CPI 기반)
        if self.cost_performance_index > 0:
            self.estimate_at_completion = budget_at_completion / self.cost_performance_index
        else:
            self.estimate_at_completion = budget_at_completion

        self.estimate_to_complete = self.estimate_at_completion - self.actual_cost
        self.variance_at_completion = budget_at_completion - self.estimate_at_completion

        # TCPI (남은 작업의 목표 성과 지수)
        remaining_work = budget_at_completion - self.earned_value
        remaining_budget = budget_at_completion - self.actual_cost
        if remaining_budget > 0 and remaining_work > 0:
            self.to_complete_performance_index = remaining_work / remaining_budget
        else:
            self.to_complete_performance_index = 1.0


@dataclass
class EVMSSnapshot:
    """특정 시점의 EVMS 스냅샷"""
    day: int
    date: str
    progress_percent: float
    metrics: EVMSMetrics
    notes: str = ""


class EVMSTracker:
    """EVMS 추적 및 관리 시스템"""

    def __init__(self,
                 budget_at_completion: float,
                 planned_duration: int):
        """
        Args:
            budget_at_completion: 총 예산 (BAC)
            planned_duration: 계획 공기 (일)
        """
        self.budget_at_completion = budget_at_completion  # BAC
        self.planned_duration = planned_duration
        self.snapshots: List[EVMSSnapshot] = []

    def calculate_planned_value(self, current_day: int) -> float:
        """
        현재 일자의 계획 가치 (PV) 계산
        선형 가정: PV = BAC * (current_day / planned_duration)

        Args:
            current_day: 현재 일수

        Returns:
            PV 값
        """
        if current_day >= self.planned_duration:
            return self.budget_at_completion

        progress = current_day / self.planned_duration
        return self.budget_at_completion * progress

    def calculate_earned_value(self,
                               actual_progress: float,
                               current_day: int) -> float:
        """
        획득 가치 (EV) 계산
        EV = BAC * actual_progress

        Args:
            actual_progress: 실제 진행률 (0.0 ~ 1.0)
            current_day: 현재 일수

        Returns:
            EV 값
        """
        # 실제 진행률 기반 EV 계산
        return self.budget_at_completion * actual_progress

    def add_snapshot(self,
                    current_day: int,
                    actual_progress: float,
                    actual_cost_to_date: float,
                    notes: str = "") -> EVMSMetrics:
        """
        현재 시점의 EVMS 스냅샷 추가

        Args:
            current_day: 현재 일수
            actual_progress: 실제 진행률 (0.0 ~ 1.0)
            actual_cost_to_date: 현재까지의 실제 비용
            notes: 메모

        Returns:
            계산된 EVMSMetrics
        """
        metrics = EVMSMetrics()

        # 기본 값 계산
        metrics.planned_value = self.calculate_planned_value(current_day)
        metrics.earned_value = self.calculate_earned_value(actual_progress, current_day)
        metrics.actual_cost = actual_cost_to_date

        # 파생 지표 계산
        metrics.calculate_derived_metrics(self.budget_at_completion)

        # 스냅샷 저장
        snapshot = EVMSSnapshot(
            day=current_day,
            date=datetime.now().strftime("%Y-%m-%d"),
            progress_percent=actual_progress * 100,
            metrics=metrics,
            notes=notes
        )
        self.snapshots.append(snapshot)

        return metrics

    def integrate_cost_schedule(self,
                                total_delay_days: float,
                                total_cost_increase_pct: float) -> Dict[str, float]:
        """
        비용과 기간을 EVMS 프레임워크로 통합

        기간 지연을 비용으로 환산하여 통합 성과 지표 산출

        Args:
            total_delay_days: 총 지연 일수
            total_cost_increase_pct: 총 비용 증가율 (%)

        Returns:
            통합 성과 지표
        """
        # 실제 공기 및 비용
        actual_duration = self.planned_duration + total_delay_days
        actual_cost = self.budget_at_completion * (1.0 + total_cost_increase_pct / 100.0)

        # 프로젝트 완료 시점 기준 EVMS 계산
        final_metrics = EVMSMetrics()
        final_metrics.planned_value = self.budget_at_completion
        final_metrics.earned_value = self.budget_at_completion  # 완료됨
        final_metrics.actual_cost = actual_cost

        final_metrics.calculate_derived_metrics(self.budget_at_completion)

        # 기간 지연을 비용으로 환산
        # 가정: 1일 지연 = 계획 일비용 * 1일
        daily_planned_cost = self.budget_at_completion / self.planned_duration
        delay_cost_equivalent = total_delay_days * daily_planned_cost

        # 통합 비용 = 실제 비용 + 지연 환산 비용
        integrated_cost = actual_cost + delay_cost_equivalent

        # 통합 CPI (비용과 일정을 모두 고려)
        integrated_cpi = self.budget_at_completion / integrated_cost if integrated_cost > 0 else 1.0

        return {
            'actual_duration': actual_duration,
            'actual_cost': actual_cost,
            'delay_cost_equivalent': delay_cost_equivalent,
            'integrated_cost': integrated_cost,
            'cost_variance': final_metrics.cost_variance,
            'schedule_variance_days': total_delay_days,
            'cost_performance_index': final_metrics.cost_performance_index,
            'schedule_performance_index': (self.planned_duration / actual_duration if actual_duration > 0 else 1.0),
            'integrated_performance_index': integrated_cpi,
            'estimate_at_completion': final_metrics.estimate_at_completion,
            'variance_at_completion': final_metrics.variance_at_completion
        }

    def generate_evms_report(self, integrated_metrics: Dict) -> str:
        """
        EVMS 보고서 생성

        Args:
            integrated_metrics: integrate_cost_schedule 결과

        Returns:
            포맷팅된 보고서 문자열
        """
        report = f"""
{'='*100}
EVMS (Earned Value Management System) 성과 보고서
{'='*100}

[기준 정보 (Baseline)]
  - 예산 (BAC)          : {self.budget_at_completion:>20,.0f}원 ({self.budget_at_completion/100000000:>8.2f}억원)
  - 계획 공기 (PD)      : {self.planned_duration:>20}일

[실제 성과 (Actual Performance)]
  - 실제 비용 (AC)      : {integrated_metrics['actual_cost']:>20,.0f}원 ({integrated_metrics['actual_cost']/100000000:>8.2f}억원)
  - 실제 공기 (AD)      : {integrated_metrics['actual_duration']:>20.1f}일

[비용 분산 (Cost Variance)]
  - CV                  : {integrated_metrics['cost_variance']:>20,.0f}원 ({integrated_metrics['cost_variance']/100000000:>8.2f}억원)
  - 상태                : {'예산 절감' if integrated_metrics['cost_variance'] > 0 else '예산 초과' if integrated_metrics['cost_variance'] < 0 else '예산 준수'}

[일정 분산 (Schedule Variance)]
  - SV (일수)           : {integrated_metrics['schedule_variance_days']:>20.1f}일
  - 상태                : {'조기 완료' if integrated_metrics['schedule_variance_days'] < 0 else '지연 발생' if integrated_metrics['schedule_variance_days'] > 0 else '정시 완료'}

[성과 지수 (Performance Indices)]
  - CPI (비용)          : {integrated_metrics['cost_performance_index']:>20.4f}
  - SPI (일정)          : {integrated_metrics['schedule_performance_index']:>20.4f}

{'─'*100}
[통합 성과 분석 (Integrated Analysis)]
{'─'*100}

  일정 지연의 비용 환산
  - 지연 일수           : {integrated_metrics['schedule_variance_days']:>20.1f}일
  - 환산 비용           : {integrated_metrics['delay_cost_equivalent']:>20,.0f}원 ({integrated_metrics['delay_cost_equivalent']/100000000:>8.2f}억원)

  통합 비용 (실제비용 + 지연환산비용)
  - 통합 총비용         : {integrated_metrics['integrated_cost']:>20,.0f}원 ({integrated_metrics['integrated_cost']/100000000:>8.2f}억원)
  - 통합 CPI            : {integrated_metrics['integrated_performance_index']:>20.4f}

  예측 지표
  - EAC (완료 예상 비용): {integrated_metrics['estimate_at_completion']:>20,.0f}원 ({integrated_metrics['estimate_at_completion']/100000000:>8.2f}억원)
  - VAC (완료시점 분산) : {integrated_metrics['variance_at_completion']:>20,.0f}원 ({integrated_metrics['variance_at_completion']/100000000:>8.2f}억원)

{'─'*100}
[성과 평가 (Performance Assessment)]
{'─'*100}

  CPI 평가: """

        cpi = integrated_metrics['cost_performance_index']
        if cpi >= 1.0:
            report += f"우수 (1.0 이상) - 비용 효율적으로 프로젝트 수행"
        elif cpi >= 0.9:
            report += f"양호 (0.9~1.0) - 비용이 소폭 초과되었으나 관리 가능 수준"
        else:
            report += f"미흡 (0.9 미만) - 비용 초과가 심각, 개선 조치 필요"

        report += f"\n\n  SPI 평가: "
        spi = integrated_metrics['schedule_performance_index']
        if spi >= 1.0:
            report += f"우수 (1.0 이상) - 일정을 준수하거나 앞당김"
        elif spi >= 0.9:
            report += f"양호 (0.9~1.0) - 일정이 소폭 지연되었으나 관리 가능 수준"
        else:
            report += f"미흡 (0.9 미만) - 일정 지연이 심각, 개선 조치 필요"

        report += f"\n\n  통합 CPI 평가: "
        icpi = integrated_metrics['integrated_performance_index']
        if icpi >= 1.0:
            report += f"우수 (1.0 이상) - 비용과 일정 모두 목표 달성"
        elif icpi >= 0.9:
            report += f"양호 (0.9~1.0) - 전반적으로 관리 가능한 수준"
        else:
            report += f"미흡 (0.9 미만) - 비용과 일정 모두 개선 필요"

        report += f"""

{'='*100}
EVMS 보고서 끝
{'='*100}
"""
        return report

    def get_latest_metrics(self) -> EVMSMetrics:
        """가장 최근 EVMS 지표 반환"""
        if self.snapshots:
            return self.snapshots[-1].metrics
        else:
            return EVMSMetrics()

    def get_trend_analysis(self) -> Dict:
        """트렌드 분석 (CPI, SPI 추세)"""
        if len(self.snapshots) < 2:
            return {'trend': 'insufficient_data'}

        first = self.snapshots[0].metrics
        latest = self.snapshots[-1].metrics

        return {
            'cpi_trend': 'improving' if latest.cost_performance_index > first.cost_performance_index else 'declining',
            'spi_trend': 'improving' if latest.schedule_performance_index > first.schedule_performance_index else 'declining',
            'cpi_change': latest.cost_performance_index - first.cost_performance_index,
            'spi_change': latest.schedule_performance_index - first.schedule_performance_index
        }
