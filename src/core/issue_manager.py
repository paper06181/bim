"""
이슈 관리 시스템
이슈의 발생, 진행, 해결 상태를 추적
"""

from typing import List, Dict, Set, Literal, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class IssueRecord:
    """이슈 기록"""

    # 기본 정보
    id: str
    name: str
    category: str
    stage: str
    detected_day: int

    # 심각도 및 영향
    severity: str  # S1, S2, S3
    estimated_delay_days: float
    estimated_cost_increase_pct: float
    actual_delay_days: float = 0
    actual_cost_increase_pct: float = 0

    # 상태 관리
    status: Literal["대기중", "해결중", "보류", "해결완료"] = "대기중"
    priority: Literal["높음", "보통", "낮음"] = "보통"
    progress: float = 0.0  # 0~100%

    # 일정 추적
    started_day: Optional[int] = None
    completed_day: Optional[int] = None
    duration_worked: int = 0  # 실제 작업한 일수

    # 의존성 및 관계
    dependencies: List[str] = field(default_factory=list)  # 선행되어야 할 이슈 ID
    blocking: List[str] = field(default_factory=list)  # 이 이슈가 막고 있는 이슈 ID
    correlated_issues: List[Dict] = field(default_factory=list)  # 상관관계 있는 이슈들

    # 해결 방안
    selected_solution: Dict = field(default_factory=dict)

    # 일일 업데이트
    daily_updates: List[Dict] = field(default_factory=list)

    def update_progress(self, current_day: int, note: str = ""):
        """진행도 업데이트"""
        if self.status == "해결중":
            self.duration_worked += 1

            # 진행률 계산 (예상 일수 기반)
            if self.estimated_delay_days > 0:
                self.progress = min(
                    100.0, (self.duration_worked / self.estimated_delay_days) * 100
                )

            # 일일 기록
            self.daily_updates.append(
                {
                    "day": current_day,
                    "progress": self.progress,
                    "status": self.status,
                    "note": note,
                }
            )

            # 완료 체크
            if self.progress >= 100:
                self.status = "해결완료"
                self.completed_day = current_day
                self.actual_delay_days = self.duration_worked
                self.actual_cost_increase_pct = self.estimated_cost_increase_pct

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "ID": self.id,
            "이슈명": self.name,
            "카테고리": self.category,
            "발생일": self.detected_day,
            "상태": self.status,
            "우선순위": self.priority,
            "진행률": f"{self.progress:.1f}%",
            "심각도": self.severity,
            "예상지연": f"{self.estimated_delay_days:.1f}일",
            "실제지연": f"{self.actual_delay_days:.1f}일",
            "비용증가": f"{self.actual_cost_increase_pct:.2f}%",
            "시작일": self.started_day,
            "완료일": self.completed_day,
            "작업일수": self.duration_worked,
        }


class IssueManager:
    """이슈 관리 매니저"""

    def __init__(self):
        self.issues_by_status: Dict[str, List[IssueRecord]] = {
            "대기중": [],
            "해결중": [],
            "보류": [],
            "해결완료": [],
        }

        self.occurred_issue_ids: Set[str] = set()  # 이미 발생한 이슈 (중복 방지)
        self.all_issues: List[IssueRecord] = []  # 전체 이슈 기록

    def add_issue(
        self,
        issue_data: Dict,
        severity_assessment: Dict,
        selected_solution: Dict,
        current_day: int,
    ) -> IssueRecord:
        """
        새로운 이슈 추가

        Args:
            issue_data: 이슈 기본 정보
            severity_assessment: 에이전트 회의로 결정된 심각도
            selected_solution: 선택된 해결 방안
            current_day: 현재 일자

        Returns:
            생성된 IssueRecord
        """
        issue_record = IssueRecord(
            id=issue_data["ID"],
            name=issue_data["이슈명"],
            category=issue_data["카테고리"],
            stage=issue_data["발생단계"],
            detected_day=current_day,
            severity=issue_data["심각도"],
            estimated_delay_days=severity_assessment.get("final_delay_weeks", 1) * 7,
            estimated_cost_increase_pct=severity_assessment.get(
                "final_cost_increase_pct", 0.1
            ),
            selected_solution=selected_solution,
        )

        # 발생 기록
        self.occurred_issue_ids.add(issue_data["ID"])
        self.all_issues.append(issue_record)

        # 즉시 시작 가능 여부 체크
        if self._can_start_immediately(issue_record):
            issue_record.status = "해결중"
            issue_record.started_day = current_day
            self.issues_by_status["해결중"].append(issue_record)
        else:
            issue_record.status = "대기중"
            self.issues_by_status["대기중"].append(issue_record)

        return issue_record

    def update_all_issues(self, current_day: int) -> List[Dict]:
        """
        모든 이슈 상태 업데이트

        Returns:
            상태 변화가 있었던 이슈 목록
        """
        status_changes = []

        # 1. 해결 중인 이슈 진척
        for issue in self.issues_by_status["해결중"][:]:
            old_status = issue.status
            old_progress = issue.progress

            issue.update_progress(current_day, "정상 진행 중")

            if issue.status == "해결완료":
                # 해결 완료로 이동
                self.issues_by_status["해결중"].remove(issue)
                self.issues_by_status["해결완료"].append(issue)

                status_changes.append(
                    {
                        "issue_id": issue.id,
                        "issue_name": issue.name,
                        "change": "해결완료",
                        "note": f"{issue.duration_worked}일 소요",
                    }
                )

                # 블로킹된 이슈 해제
                self._unblock_dependent_issues(issue, current_day)

        # 2. 대기 중인 이슈 → 해결 중으로 전환 가능 여부
        for issue in self.issues_by_status["대기중"][:]:
            if self._can_start_now(issue):
                issue.status = "해결중"
                issue.started_day = current_day
                self.issues_by_status["대기중"].remove(issue)
                self.issues_by_status["해결중"].append(issue)

                status_changes.append(
                    {
                        "issue_id": issue.id,
                        "issue_name": issue.name,
                        "change": "착수",
                        "note": "선행 이슈 해결 완료",
                    }
                )

        return status_changes

    def _can_start_immediately(self, issue: IssueRecord) -> bool:
        """즉시 시작 가능 여부"""
        # 의존성 체크
        if issue.dependencies:
            return False

        # 동시 진행 가능한 이슈 수 제한 (예: 최대 5개)
        if len(self.issues_by_status["해결중"]) >= 5:
            return False

        return True

    def _can_start_now(self, issue: IssueRecord) -> bool:
        """지금 시작 가능 여부"""
        # 의존성 체크 - 모든 선행 이슈가 완료되었는지
        for dep_id in issue.dependencies:
            dep_issue = self._find_issue_by_id(dep_id)
            if dep_issue and dep_issue.status != "해결완료":
                return False

        # 동시 진행 제한
        if len(self.issues_by_status["해결중"]) >= 5:
            return False

        return True

    def _unblock_dependent_issues(self, completed_issue: IssueRecord, current_day: int):
        """완료된 이슈에 의해 블로킹된 이슈들 해제"""
        for blocked_id in completed_issue.blocking:
            blocked_issue = self._find_issue_by_id(blocked_id)
            if blocked_issue and blocked_issue.status == "대기중":
                # 의존성 제거
                if completed_issue.id in blocked_issue.dependencies:
                    blocked_issue.dependencies.remove(completed_issue.id)

    def _find_issue_by_id(self, issue_id: str) -> Optional[IssueRecord]:
        """ID로 이슈 찾기"""
        for issue in self.all_issues:
            if issue.id == issue_id:
                return issue
        return None

    def analyze_correlations(
        self, new_issues: List[Dict], active_issues: List[IssueRecord]
    ) -> List[Dict]:
        """
        이슈 간 상관관계 분석

        Args:
            new_issues: 새로 발생한 이슈 데이터
            active_issues: 현재 활성 이슈

        Returns:
            상관관계 목록
        """
        correlations = []

        # 새 이슈 + 활성 이슈 결합
        all_current = []

        # 새 이슈를 임시 레코드로 변환
        for issue in new_issues:
            all_current.append(
                {
                    "id": issue["ID"],
                    "name": issue["이슈명"],
                    "category": issue["카테고리"],
                    "stage": issue["발생단계"],
                    "progress_range": issue["공정률"],
                }
            )

        # 활성 이슈
        for issue in active_issues:
            all_current.append(
                {
                    "id": issue.id,
                    "name": issue.name,
                    "category": issue.category,
                    "stage": issue.stage,
                    "progress_range": None,
                }
            )

        # 모든 쌍에 대해 상관관계 계산
        for i, issue1 in enumerate(all_current):
            for issue2 in all_current[i + 1 :]:
                correlation = self._check_correlation(issue1, issue2)
                if correlation["type"] != "독립":
                    correlations.append(correlation)

        return correlations

    def _check_correlation(self, issue1: Dict, issue2: Dict) -> Dict:
        """두 이슈 간 상관관계 판단"""
        # 카테고리 기반 상관도
        category_correlation_map = {
            ("설계", "시공"): 0.7,
            ("시공", "시공"): 0.6,
            ("자재", "시공"): 0.8,
            ("설계", "설계"): 0.5,
            ("품질", "시공"): 0.6,
            ("안전", "시공"): 0.7,
            ("행정", "설계"): 0.4,
        }

        cat1 = issue1["category"]
        cat2 = issue2["category"]
        cat_pair = tuple(sorted([cat1, cat2]))

        base_correlation = category_correlation_map.get(cat_pair, 0.2)

        # 관계 유형 결정
        if base_correlation > 0.7:
            relation_type = "강한 의존"
            effect = f"{issue1['name']} 미해결 시 {issue2['name']} 심각도 +30%"
            recommendation = f"{issue1['name']}을 우선 해결 후 {issue2['name']} 착수 권장"
        elif base_correlation > 0.5:
            relation_type = "약한 의존"
            effect = f"{issue1['name']} 미해결 시 {issue2['name']} 심각도 +15%"
            recommendation = f"가능하면 {issue1['name']} 먼저 해결"
        elif base_correlation > 0.3:
            relation_type = "간섭"
            effect = "동시 처리 시 효율 -20%"
            recommendation = "별도 팀으로 병렬 처리 권장"
        else:
            relation_type = "독립"
            effect = "영향 없음"
            recommendation = "독립적 처리 가능"

        return {
            "type": relation_type,
            "issue1_id": issue1["id"],
            "issue2_id": issue2["id"],
            "issue1_name": issue1["name"],
            "issue2_name": issue2["name"],
            "correlation_score": base_correlation,
            "effect": effect,
            "recommendation": recommendation,
        }

    def get_active_issues(self) -> List[IssueRecord]:
        """현재 활성 이슈 (해결 중 + 대기 중)"""
        return self.issues_by_status["해결중"] + self.issues_by_status["대기중"]

    def get_summary(self) -> Dict:
        """전체 요약 정보"""
        total_delay = sum(issue.actual_delay_days for issue in self.all_issues)
        total_cost = sum(issue.actual_cost_increase_pct for issue in self.all_issues)

        return {
            "전체이슈수": len(self.all_issues),
            "대기중": len(self.issues_by_status["대기중"]),
            "해결중": len(self.issues_by_status["해결중"]),
            "보류": len(self.issues_by_status["보류"]),
            "해결완료": len(self.issues_by_status["해결완료"]),
            "누적지연(일)": total_delay,
            "누적비용증가(%)": total_cost,
        }
