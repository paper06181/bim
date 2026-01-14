"""
프로젝트 컨텍스트 정의
에이전트 회의에 필요한 모든 프로젝트 정보를 관리
"""

import math
from dataclasses import dataclass, field
from typing import Dict, Literal


@dataclass
class ProjectContext:
    """프로젝트 전체 컨텍스트"""

    # ===== 기본 입력 정보 =====
    location: Literal["도심", "외곽"]
    floor_area_ratio: int  # 용적율 (%)
    total_area: float  # 연면적 (㎡)
    total_budget: float  # 총 공사비 (억원)
    planned_duration_days: int  # 계획 공기 (일수)
    building_type: Literal["상업", "주거", "공업", "복합"]
    ground_roughness: Literal["A", "B", "C", "D"]
    method: Literal["BIM", "TRADITIONAL"]

    # ===== 케이스 및 KPI (자동 설정) =====
    case: str = ""  # A, B, C, D
    kpi_values: Dict[str, float] = field(default_factory=dict)

    # ===== 파생 정보 (자동 계산) =====
    target_days: int = 0  # 목표 공기 (계획의 90%, 정수)
    buffer_days: int = 0  # 버퍼 기간
    daily_finance_cost: float = 0.0  # 일일 금융비용 (만원)
    daily_material_cost: float = 0.0  # 일일 자재비 (만원)
    daily_labor_cost: float = 0.0  # 일일 인건비 (만원)

    # ===== 위험도 계수 =====
    urban_density: float = 1.0  # 도심 밀집도
    scale_factor: float = 1.0  # 규모 계수
    complexity_factor: float = 1.0  # 복잡도 계수

    # ===== 에이전트별 컨텍스트 =====
    owner_context: Dict = field(default_factory=dict)
    designer_context: Dict = field(default_factory=dict)
    contractor_context: Dict = field(default_factory=dict)
    supervisor_context: Dict = field(default_factory=dict)
    financier_context: Dict = field(default_factory=dict)

    def __post_init__(self):
        """초기화 후 자동 계산"""
        self._calculate_derived_values()
        self._build_agent_contexts()

    def _calculate_derived_values(self):
        """파생 정보 계산"""
        # 공기 계산 (계획 공기를 그대로 목표로 사용)
        self.target_days = self.planned_duration_days
        self.buffer_days = int(self.target_days * 0.1)  # 10% 버퍼

        # 비용 계산 (억원 → 만원)
        total_budget_man_won = self.total_budget * 10000

        # 일일 금융비용 (연 4% 이자 가정)
        annual_interest_rate = 0.04
        self.daily_finance_cost = (
            total_budget_man_won * annual_interest_rate / 365
        )

        # 일일 자재비 (총 공사비의 40%)
        self.daily_material_cost = (total_budget_man_won * 0.4) / self.target_days

        # 일일 인건비 (총 공사비의 30%)
        self.daily_labor_cost = (total_budget_man_won * 0.3) / self.target_days

        # 위험도 계수
        self.urban_density = 1.3 if self.location == "도심" else 1.0

        # 규모 계수 (로그 스케일)
        self.scale_factor = max(1.0, math.log(self.total_area / 1000, 2) / 2)

        # 복잡도 계수
        complexity_map = {
            "상업": 1.2,
            "주거": 1.0,
            "공업": 0.9,
            "복합": 1.5,
        }
        self.complexity_factor = complexity_map.get(self.building_type, 1.0)

    def _build_agent_contexts(self):
        """에이전트별 맥락 정보 구성"""
        # 건축주
        self.owner_context = {
            "예산민감도": "높음" if self.total_budget < 30 else "보통",
            "일정압박도": "높음" if self.planned_duration_days < 360 else "보통",
            "금융부담_일일": f"{self.daily_finance_cost:.1f}만원",
            "우선순위": "비용" if self.total_budget < 30 else "일정",
        }

        # 설계사
        self.designer_context = {
            "프로젝트규모": f"{self.total_area:,.0f}㎡",
            "설계난이도": "높음" if self.floor_area_ratio > 80 else "보통",
            "협업복잡도": "높음" if self.building_type == "복합" else "보통",
            "BIM활용": self.method == "BIM",
        }

        # 시공사
        self.contractor_context = {
            "현장접근성": "제한적" if self.location == "도심" else "양호",
            "작업공간": "협소" if self.location == "도심" else "충분",
            "민원위험도": "높음" if self.location == "도심" else "낮음",
            "공법": self.method,
        }

        # 감리사
        self.supervisor_context = {
            "검사강도": "높음" if self.floor_area_ratio > 70 else "보통",
            "품질기준": "상" if self.building_type in ["상업", "복합"] else "중",
        }

        # 금융사
        dscr = 1.5 if self.total_budget > 50 else 1.2  # 간단한 DSCR 추정
        self.financier_context = {
            "리스크등급": "A" if dscr > 1.4 else "B",
            "DSCR": dscr,
            "금리": "4.0%" if dscr > 1.4 else "4.5%",
        }

    def get_progress_rate(self, current_day: int) -> float:
        """현재 진행률 계산"""
        return current_day / self.target_days if self.target_days > 0 else 0

    def get_remaining_days(self, current_day: int) -> int:
        """남은 일수"""
        return max(0, self.target_days - current_day)

    def to_summary_dict(self) -> dict:
        """요약 정보 딕셔너리로 반환"""
        return {
            "기본정보": {
                "위치": self.location,
                "용적율": f"{self.floor_area_ratio}%",
                "연면적": f"{self.total_area:,.0f}㎡",
                "총공사비": f"{self.total_budget:.1f}억원",
                "계획공기": f"{self.planned_duration_days}일",
                "목표공기": f"{self.target_days}일",
                "용도": self.building_type,
                "공법": self.method,
            },
            "케이스정보": {
                "케이스": self.case,
                "KPI": self.kpi_values,
            },
            "비용정보": {
                "일일금융비용": f"{self.daily_finance_cost:.1f}만원",
                "일일자재비": f"{self.daily_material_cost:.1f}만원",
                "일일인건비": f"{self.daily_labor_cost:.1f}만원",
            },
            "위험계수": {
                "도심밀집도": self.urban_density,
                "규모계수": f"{self.scale_factor:.2f}",
                "복잡도계수": self.complexity_factor,
            },
        }
