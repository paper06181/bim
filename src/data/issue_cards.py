"""
이슈 카드 데이터베이스
엑셀에서 추출한 90개 이슈 데이터 로드
"""

import json
from pathlib import Path
from typing import List, Dict


def load_issues_from_json() -> tuple:
    """JSON 파일에서 이슈 데이터 로드"""
    data_dir = Path(__file__).parent

    # BIM 이슈
    with open(data_dir / 'bim_issues_raw.json', 'r', encoding='utf-8') as f:
        bim_raw = json.load(f)

    # 전통 이슈
    with open(data_dir / 'traditional_issues_raw.json', 'r', encoding='utf-8') as f:
        trad_raw = json.load(f)

    # 데이터 정규화
    bim_issues = normalize_issues(bim_raw, "BIM")
    trad_issues = normalize_issues(trad_raw, "TRADITIONAL")

    return bim_issues, trad_issues


def normalize_issues(raw_data: List[Dict], method: str) -> List[Dict]:
    """
    원시 데이터를 정규화된 형식으로 변환

    Args:
        raw_data: 엑셀에서 추출한 원시 데이터
        method: "BIM" 또는 "TRADITIONAL"

    Returns:
        정규화된 이슈 목록
    """
    normalized = []

    for issue in raw_data:
        # NaN 값 처리
        def get_val(key, default=0):
            val = issue.get(key, default)
            if val != val:  # NaN 체크 (NaN은 자기 자신과 같지 않음)
                return default
            return val

        # 가중치 키 정규화
        if method == "BIM":
            weights = {
                "WD": get_val("WD\n가중치", 0),
                "CD": get_val("CD\n가중치", 0),
                "AF": get_val("AF\n가중치", 0),
                "PL": get_val("PL\n가중치", 0),
            }
        else:  # TRADITIONAL
            weights = {
                "RR": get_val("RR\n가중치", 0),
                "SR": get_val("SR\n가중치", 0),
                "CR": get_val("CR\n가중치", 0),
                "FC": get_val("FC\n가중치", 0),
            }

        normalized_issue = {
            "ID": str(get_val("ID", "")),
            "이슈명": str(get_val("이슈명", "")),
            "카테고리": str(get_val("카테고리", "")),
            "발생단계": str(get_val("발생단계", "")),
            "공정률": str(get_val("공정률", "0-25")),
            "심각도": str(get_val("심각도", "S2")),
            "발생확률(%)": float(get_val("발생확률\n(%)", 10)),
            "지연(주)_Min": float(get_val("지연(주)\nMin", 1)),
            "지연(주)_Max": float(get_val("지연(주)\nMax", 2)),
            "비용증가(%)_Min": float(get_val("비용증가(%)\nMin", 0.1)),
            "비용증가(%)_Max": float(get_val("비용증가(%)\nMax", 0.5)),
            "가중치": weights,
            "설명": str(get_val("상세설명", "")),
            "탐지율(%)": float(get_val("이슈탐지율\n(%)", 50)),
        }

        normalized.append(normalized_issue)

    return normalized


# 전역 변수로 로드
BIM_ISSUES, TRADITIONAL_ISSUES = load_issues_from_json()


def get_issues_by_method(method: str) -> List[Dict]:
    """공법에 따른 이슈 목록 반환"""
    if method == "BIM":
        return BIM_ISSUES
    elif method == "TRADITIONAL":
        return TRADITIONAL_ISSUES
    else:
        raise ValueError(f"Invalid method: {method}")


def get_issue_by_id(issue_id: str, method: str) -> Dict:
    """ID로 이슈 검색"""
    issues = get_issues_by_method(method)
    for issue in issues:
        if issue["ID"] == issue_id:
            return issue
    raise ValueError(f"Issue not found: {issue_id}")


def filter_issues_by_progress(issues: List[Dict], progress_rate: float) -> List[Dict]:
    """
    공정률에 해당하는 이슈만 필터링

    Args:
        issues: 전체 이슈 목록
        progress_rate: 현재 공정률 (0.0 ~ 1.0)

    Returns:
        해당 공정률 범위의 이슈 목록
    """
    filtered = []
    progress_pct = progress_rate * 100

    for issue in issues:
        range_str = issue["공정률"]
        try:
            parts = range_str.split("-")
            min_p = int(parts[0])
            max_p = int(parts[1])

            if min_p <= progress_pct <= max_p:
                filtered.append(issue)
        except:
            # 파싱 실패 시 무시
            continue

    return filtered
