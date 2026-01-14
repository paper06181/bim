"""
케이스 및 KPI 매핑 설정
프로젝트 정보(위치 × 용적률)를 기반으로 케이스를 결정하고 KPI 값을 할당
"""

# BIM 방식 KPI 값 (케이스별: A, B, C, D)
# WD: 경고밀도 (Warning Density) - 높을수록 위험
# CD: 충돌밀도 (Clash Density) - 높을수록 위험
# AF: 속성 채움률 (Attribute Fill Rate) - 낮을수록 위험 (역전 지표)
# PL: 공정 연계도 (Planning Linkage Rate) - 낮을수록 위험 (역전 지표)
BIM_KPI_VALUES = {
    "A": {"WD": 0.5, "CD": 0.17, "AF": 24.75, "PL": 13.2},
    "B": {"WD": 0.33, "CD": 0.11, "AF": 16.5, "PL": 8.8},
    "C": {"WD": 0.23, "CD": 0.08, "AF": 11.25, "PL": 6.0},
    "D": {"WD": 0.15, "CD": 0.05, "AF": 7.5, "PL": 4.0},
}

# 전통 방식 KPI 값 (케이스별: A, B, C, D)
# RR: 재시공률 (Rework Ratio) - 높을수록 위험
# SR: 안전사고 발생률 (Safety Risk Occurrence Rate) - 높을수록 위험
# CR: 공정 지연률 (Construction Delay Ratio) - 높을수록 위험
# FC: 설계 변경 빈도 (Frequency of Change Order) - 높을수록 위험
TRADITIONAL_KPI_VALUES = {
    "A": {"RR": 0.2, "SR": 0.54, "CR": 2.48, "FC": 1.32},
    "B": {"RR": 0.13, "SR": 0.36, "CR": 1.65, "FC": 0.88},
    "C": {"RR": 0.09, "SR": 0.25, "CR": 1.13, "FC": 0.6},
    "D": {"RR": 0.06, "SR": 0.17, "CR": 0.75, "FC": 0.4},
}

# 케이스 설명
CASE_DESCRIPTIONS = {
    "A": "도심 고밀도 (고층 밀집, 복잡도 최고)",
    "B": "도심 중밀도 또는 외곽 고밀도 (중층 건물)",
    "C": "도심 저밀도 또는 외곽 중밀도 (저층 건물)",
    "D": "외곽 저밀도 (평지, 장애물 거의 없음)",
}


def determine_case(location: str, floor_area_ratio: int) -> str:
    """
    프로젝트 정보를 기반으로 케이스 결정

    Args:
        location: 위치 ("도심" 또는 "외곽")
        floor_area_ratio: 용적율 (%)

    Returns:
        케이스 (A, B, C, D)

    로직:
        도심 + 용적율 >= 80  → A (고밀도)
        도심 + 용적율 >= 60  → B (중밀도)
        도심 + 용적율 < 60   → C (저밀도)
        외곽 + 용적율 >= 70  → B (고밀도)
        외곽 + 용적율 >= 50  → C (중밀도)
        외곽 + 용적율 < 50   → D (저밀도)
    """
    if location == "도심":
        if floor_area_ratio >= 80:
            return "A"
        elif floor_area_ratio >= 60:
            return "B"
        else:
            return "C"

    elif location == "외곽":
        if floor_area_ratio >= 70:
            return "B"
        elif floor_area_ratio >= 50:
            return "C"
        else:
            return "D"

    else:
        raise ValueError(
            f"Invalid location: '{location}'. Must be '도심' or '외곽'"
        )


def get_kpi_values(case: str, method: str) -> dict:
    """
    케이스와 공법에 따라 KPI 값 반환

    Args:
        case: 케이스 (A, B, C, D)
        method: 공법 ("BIM" 또는 "TRADITIONAL")

    Returns:
        KPI 값 딕셔너리
    """
    if method == "BIM":
        if case not in BIM_KPI_VALUES:
            raise ValueError(f"Invalid case: {case}")
        return BIM_KPI_VALUES[case].copy()

    elif method == "TRADITIONAL":
        if case not in TRADITIONAL_KPI_VALUES:
            raise ValueError(f"Invalid case: {case}")
        return TRADITIONAL_KPI_VALUES[case].copy()

    else:
        raise ValueError(f"Invalid method: {method}. Must be 'BIM' or 'TRADITIONAL'")


# KPI 정규화 파라미터 (확률 계산 시 사용)
KPI_NORMALIZATION = {
    "BIM": {
        "WD": {"max": 0.5, "direction": "lower_better"},   # 낮을수록 좋음
        "CD": {"max": 0.3, "direction": "lower_better"},   # 낮을수록 좋음
        "AF": {"max": 30.0, "direction": "higher_better"},  # 높을수록 좋음 (역전 지표)
        "PL": {"max": 15.0, "direction": "higher_better"},  # 높을수록 좋음 (역전 지표)
    },
    "TRADITIONAL": {
        "RR": {"max": 0.25, "direction": "lower_better"},  # 낮을수록 좋음
        "SR": {"max": 0.6, "direction": "lower_better"},   # 낮을수록 좋음
        "CR": {"max": 3.0, "direction": "lower_better"},   # 낮을수록 좋음
        "FC": {"max": 1.5, "direction": "lower_better"},   # 낮을수록 좋음
    }
}


def normalize_kpi_value(kpi_name: str, value: float, method: str) -> float:
    """
    KPI 값을 0~1 범위로 정규화

    Args:
        kpi_name: KPI 이름
        value: 실제 KPI 값
        method: 공법 ("BIM" 또는 "TRADITIONAL")

    Returns:
        정규화된 값 (0~1, 값이 클수록 위험도 높음)
    """
    norm_params = KPI_NORMALIZATION[method][kpi_name]
    max_val = norm_params["max"]
    direction = norm_params["direction"]

    # 최대값으로 나누기
    normalized = min(value / max_val, 1.0)

    # 방향에 따라 조정
    if direction == "higher_better":
        # 높을수록 좋은 경우 → 낮을수록 위험
        normalized = 1.0 - normalized

    return normalized
