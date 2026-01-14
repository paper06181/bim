"""
이슈 발생 확률 계산
KPI 지표와 가중치를 기반으로 실제 발생 확률 계산
"""

from typing import Dict
from ..config.case_mapping import normalize_kpi_value


def calculate_issue_probability(
    issue: Dict, kpi_values: Dict[str, float], method: str
) -> float:
    """
    이슈 발생 확률 계산

    Args:
        issue: 이슈 정보 (ID, 기본발생확률, 가중치 포함)
        kpi_values: 실제 지표값 {WD: 0.33, CD: 0.22, ...}
        method: "BIM" 또는 "TRADITIONAL"

    Returns:
        최종 발생 확률 (0.0 ~ 1.0)
    """
    base_prob = issue["발생확률(%)"] / 100.0  # 기본 발생률
    weights = issue.get("가중치", {})

    # 각 KPI의 위험도 점수 계산
    risk_scores = []
    for kpi_name, kpi_value in kpi_values.items():
        if kpi_name in weights and weights[kpi_name] > 0:
            # KPI 정규화 (0~1, 높을수록 위험)
            normalized = normalize_kpi_value(kpi_name, kpi_value, method)

            # 가중치 적용
            weighted_score = normalized * weights[kpi_name]
            risk_scores.append(weighted_score)

    # 전체 위험도
    if risk_scores:
        total_risk = sum(risk_scores) / sum(weights.values())
    else:
        total_risk = 0.5  # 기본값

    # 최종 확률 = 기본 확률 × (1 + 위험도 조정)
    # 위험도가 높을수록 확률 증가
    multiplier = 1.0 + (total_risk - 0.5) * 0.8  # -0.4 ~ +0.4 범위 조정

    if method == "TRADITIONAL":
        # 전통 방식은 위험 증폭 (1.2배)
        multiplier *= 1.2

    final_prob = base_prob * multiplier

    # 최대 95%, 최소 1%로 제한
    return max(0.01, min(0.95, final_prob))
