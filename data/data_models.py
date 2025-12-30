"""
새로운 데이터 모델 정의
- 확률 기반이 아닌 KPI 기반 리스크 모델
- resolution_level을 통한 의사결정 반영
"""
from typing import Dict, Optional, Literal
from dataclasses import dataclass, field


@dataclass
class KPISet:
    """KPI 값 세트 (BIM 또는 전통 방식)"""
    family: Literal["BIM", "TRAD"]
    values: Dict[str, float]  # 예: {"WD": 0.33, "CD": 0.11, ...} 또는 {"RR": 0.20, ...}

    def get_kpi_value(self, kpi_name: str) -> float:
        """특정 KPI 값 가져오기"""
        return self.values.get(kpi_name, 0.0)

    def __repr__(self):
        kpi_str = ', '.join(f"{k}={v:.2f}" for k, v in self.values.items())
        return f"KPISet({self.family}: {kpi_str})"


@dataclass
class Case:
    """프로젝트 CASE 정보"""
    case_id: str               # 예: "중심상업지역 A"
    kpi_grade: str             # A, B, C, D
    kpi_bim: KPISet            # BIM 적용 시 KPI (WD, CD, AF, PL)
    kpi_trad: KPISet           # 전통 방식 KPI (RR, SR, CR, FC)

    # 프로젝트 메타데이터
    location_type: Optional[str] = None      # 도심/외곽
    zoning: Optional[str] = None             # 상업지역, 주거지역 등
    detailed_zoning: Optional[str] = None    # 중심상업지역, 제1종 일반주거지역 등
    far: Optional[float] = None              # 용적률 (%)
    bcr: Optional[float] = None              # 건폐율 (%)

    def __repr__(self):
        return f"Case({self.case_id}, Grade={self.kpi_grade})"


@dataclass
class IssueCard:
    """이슈 카드 (BIM 적용 또는 미적용)"""
    issue_id: str                    # I-01 ~ I-90
    name: str                        # 이슈명
    category: str                    # 계획, 설계, 입찰, 시공 등
    severity: Literal["S1", "S2", "S3"]  # 심각도
    phase: str                       # 발생단계 (기획/발주, 설계 등)
    delay_min_weeks: float           # 지연 최소값 (주)
    delay_max_weeks: float           # 지연 최대값 (주)
    cost_min_pct: float              # 비용증가 최소값 (%)
    cost_max_pct: float              # 비용증가 최대값 (%)
    description: str                 # 상세설명
    kpi_weights: Dict[str, float]    # KPI 가중치 (WD/CD/AF/PL 또는 RR/SR/CR/FC)
    progress_segment: str            # 공정률 구간 (0-25, 25-75, 75-100, 0-100 등)
    family: Literal["BIM", "TRAD"]   # BIM 적용 여부

    # 계산에 사용되는 필드들 (시뮬레이션 중 설정됨)
    base_risk: float = 0.0           # 기본 리스크 점수
    resolution_level: float = 0.5    # 회의에서 결정된 해결수준 (0.0 ~ 1.0)
    effective_risk: float = 0.0      # resolution_level 반영 후 리스크
    impact_factor: float = 0.0       # 실제 영향도 (0.0 ~ 1.0)
    actual_delay_weeks: float = 0.0  # 실제 지연 (주)
    actual_cost_pct: float = 0.0     # 실제 비용증가 (%)

    def __repr__(self):
        return f"IssueCard({self.issue_id}: {self.name[:30]}, {self.severity}, {self.family})"


@dataclass
class ProjectInfo:
    """프로젝트 기본 정보"""
    project_name: str                # 프로젝트 이름
    duration_days: int               # 총 공기 (일)
    base_cost: float                 # 기준 공사비 (원)
    case: Case                       # 선택된 CASE

    # 옵션
    description: Optional[str] = None

    def __repr__(self):
        return f"ProjectInfo({self.project_name}, {self.duration_days}일, {self.base_cost:,.0f}원)"


@dataclass
class ScenarioResult:
    """시나리오 실행 결과 (EVMS 통합)"""
    scenario_name: str               # 시나리오 이름
    family: Literal["BIM", "TRAD"]   # BIM 적용 여부
    management_level: str            # 관리 수준 (basic, enhanced)

    # 전체 결과
    total_delay_days: float = 0.0
    total_cost_pct: float = 0.0
    actual_duration: float = 0.0
    actual_cost: float = 0.0

    # EVMS 통합 결과 (일정을 비용으로 흡수)
    delay_cost_equivalent: float = 0.0    # 일정 지연의 비용 환산액
    integrated_total_cost: float = 0.0    # 통합 총 비용 (실제비용 + 지연환산비용)
    integrated_cost_pct: float = 0.0      # 통합 비용 증가율

    # 이슈별 상세 결과
    issues_evaluated: int = 0
    issues_occurred: int = 0         # 실제 발생한 이슈 수
    issues_minor: int = 0            # 경미한 이슈
    issues_major: int = 0            # 심각한 이슈

    # 공정률 구간별 결과 (선택적)
    segment_results: Dict[str, dict] = field(default_factory=dict)

    def apply_evms_integration(self, planned_duration: int, base_cost: float):
        """
        EVMS를 적용하여 일정 지연을 비용으로 통합

        Args:
            planned_duration: 계획 공기 (일)
            base_cost: 기준 공사비 (원)
        """
        # 일일 계획 비용 = 총 예산 / 계획 공기
        daily_planned_cost = base_cost / planned_duration

        # 지연을 비용으로 환산
        self.delay_cost_equivalent = self.total_delay_days * daily_planned_cost

        # 통합 총 비용 = 실제 비용 + 지연 환산 비용
        self.integrated_total_cost = self.actual_cost + self.delay_cost_equivalent

        # 통합 비용 증가율
        self.integrated_cost_pct = ((self.integrated_total_cost - base_cost) / base_cost) * 100.0

    def __repr__(self):
        return f"ScenarioResult({self.scenario_name}: 지연={self.total_delay_days:.1f}일, 통합비용증가={self.integrated_cost_pct:.2f}%)"


@dataclass
class ComparisonResult:
    """시나리오 간 비교 결과 (EVMS 통합)"""
    baseline: ScenarioResult         # 기준 시나리오
    comparison: ScenarioResult       # 비교 시나리오

    # 일정 지표 (참고용)
    delay_reduction_days: float = 0.0    # 지연 감소 (양수=개선)
    delay_reduction_weeks: float = 0.0

    # 통합 비용 지표 (EVMS - 일정이 비용으로 흡수됨)
    integrated_cost_reduction: float = 0.0       # 통합 비용 절감액 (원)
    integrated_cost_reduction_pct: float = 0.0   # 통합 비용 절감률 (%)

    # 기존 비용 지표 (참고용)
    cost_reduction_pct: float = 0.0      # 직접 비용 감소 (양수=개선)

    def calculate_rewards(self):
        """보상/페널티 계산 (EVMS 통합)"""
        # 일정 지표
        self.delay_reduction_days = self.baseline.total_delay_days - self.comparison.total_delay_days
        self.delay_reduction_weeks = self.delay_reduction_days / 7.0

        # 직접 비용 지표
        self.cost_reduction_pct = self.baseline.total_cost_pct - self.comparison.total_cost_pct

        # 통합 비용 지표 (EVMS - 핵심 지표)
        self.integrated_cost_reduction = self.baseline.integrated_total_cost - self.comparison.integrated_total_cost
        self.integrated_cost_reduction_pct = self.baseline.integrated_cost_pct - self.comparison.integrated_cost_pct

    def __repr__(self):
        return f"Comparison({self.baseline.scenario_name} vs {self.comparison.scenario_name}: 통합비용절감={self.integrated_cost_reduction/100000000:.2f}억원)"
