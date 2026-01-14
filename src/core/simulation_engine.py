"""
시뮬레이션 엔진
매일 시뮬레이션을 실행하고 회의를 진행
"""

import random
import json
from typing import Dict, List
from pathlib import Path
from datetime import datetime

from ..config.project_context import ProjectContext
from ..config.case_mapping import determine_case, get_kpi_values
from ..data.issue_cards import get_issues_by_method, filter_issues_by_progress
from .issue_manager import IssueManager
from .agent_meeting import AgentMeeting
from .probability_calculator import calculate_issue_probability


class ConstructionSimulation:
    """건설 시뮬레이션 엔진"""

    def __init__(self, project_info: Dict, method: str = "BIM"):
        """
        시뮬레이션 초기화

        Args:
            project_info: 프로젝트 기본 정보
            method: "BIM" 또는 "TRADITIONAL"
        """
        # 프로젝트 컨텍스트 생성
        self.method = method

        # 케이스 결정
        case = determine_case(
            project_info["location"], project_info["floor_area_ratio"]
        )

        # KPI 값 가져오기
        kpi_values = get_kpi_values(case, method)

        # 프로젝트 컨텍스트 생성
        self.context = ProjectContext(
            location=project_info["location"],
            floor_area_ratio=project_info["floor_area_ratio"],
            total_area=project_info["total_area"],
            total_budget=project_info["total_budget"],
            planned_duration_days=project_info["planned_duration_days"],
            building_type=project_info["building_type"],
            ground_roughness=project_info.get("ground_roughness", "C"),
            method=method,
            case=case,
            kpi_values=kpi_values,
        )

        # 이슈 관리
        self.issue_manager = IssueManager()
        self.all_issues = get_issues_by_method(method)

        # 시뮬레이션 상태
        self.current_day = 0
        self.daily_logs = []

        # 누적 지표
        self.total_delay_days = 0
        self.total_cost_increase_pct = 0

    def run_simulation(self, output_dir: str = "results") -> Dict:
        """
        전체 시뮬레이션 실행

        Returns:
            시뮬레이션 결과 요약
        """
        print(f"\n{'='*60}")
        print(f"건설 시뮬레이션 시작")
        print(f"공법: {self.method}")
        print(f"케이스: {self.context.case}")
        print(f"목표 공기: {self.context.target_days}일")
        print(f"{'='*60}\n")

        for day in range(1, self.context.target_days + 1):
            self.current_day = day
            progress_rate = self.context.get_progress_rate(day)

            # 1. 오늘 발생 가능한 이슈 필터링
            candidate_issues = filter_issues_by_progress(self.all_issues, progress_rate)

            # 2. 발생 여부 판단
            occurred_issues = self.check_issue_occurrence(candidate_issues)

            # 3. 이슈 상태 업데이트
            status_changes = self.issue_manager.update_all_issues(day)

            # 4. 회의 진행 (새 이슈 또는 진행 중 이슈가 있을 때)
            active_issues = self.issue_manager.get_active_issues()
            if occurred_issues or active_issues:
                meeting_result = self.conduct_meeting(occurred_issues, active_issues)
                self.daily_logs.append(meeting_result)

                # 새 이슈 등록
                for discussion in meeting_result.get("discussions", []):
                    if discussion.get("type") == "신규":
                        # 이슈 매니저에 추가
                        issue_data = next(
                            (i for i in occurred_issues if i["ID"] == discussion["issue_id"]),
                            None
                        )
                        if issue_data:
                            self.issue_manager.add_issue(
                                issue_data,
                                discussion["severity"],
                                discussion["selected"],
                                day
                            )

            # 진행 상황 출력 (10일마다)
            if day % 10 == 0:
                print(f"Day {day}/{self.context.target_days} ({progress_rate*100:.1f}%) - "
                      f"이슈: {len(active_issues)}개 진행 중")

        # 시뮬레이션 종료
        print(f"\n{'='*60}")
        print("시뮬레이션 완료")
        print(f"{'='*60}\n")

        # 결과 요약
        summary = self.generate_summary()

        # 결과 저장
        self.save_results(output_dir, summary)

        return summary

    def check_issue_occurrence(self, candidates: List[Dict]) -> List[Dict]:
        """
        이슈 발생 여부 판단

        Args:
            candidates: 후보 이슈 목록

        Returns:
            실제 발생한 이슈 목록
        """
        occurred = []

        for issue in candidates:
            # 이미 발생한 이슈는 제외
            if issue["ID"] in self.issue_manager.occurred_issue_ids:
                continue

            # 확률 계산
            prob = calculate_issue_probability(
                issue, self.context.kpi_values, self.method
            )

            # 발생 여부 (난수)
            if random.random() < prob:
                occurred.append(issue)

        return occurred

    def conduct_meeting(
        self, new_issues: List[Dict], active_issues: List
    ) -> Dict:
        """
        에이전트 회의 진행

        Args:
            new_issues: 새로 발생한 이슈
            active_issues: 현재 진행 중인 이슈

        Returns:
            회의 로그
        """
        # 프로젝트 컨텍스트 준비
        meeting_context = {
            "current_day": self.current_day,
            "progress_rate": self.context.get_progress_rate(self.current_day),
            "project_summary": self.context.to_summary_dict()["기본정보"],
            "kpi_values": self.context.kpi_values,
            "daily_finance_cost": f"{self.context.daily_finance_cost:.1f}만원",
            "cumulative": {
                "total_delay_days": self.total_delay_days,
                "total_cost_overrun": self.total_cost_increase_pct,
            },
        }

        # 회의 실행
        meeting = AgentMeeting(
            date=self.current_day,
            project_context=meeting_context,
            new_issues=new_issues,
            active_issues=active_issues,
            method=self.method,
        )

        result = meeting.run()

        # 누적 지표 업데이트
        for discussion in result.get("discussions", []):
            if discussion.get("type") == "신규":
                severity = discussion.get("severity", {})
                self.total_delay_days += severity.get("final_delay_weeks", 0) * 7
                self.total_cost_increase_pct += severity.get("final_cost_increase_pct", 0)

        return result

    def generate_summary(self) -> Dict:
        """시뮬레이션 결과 요약"""
        issue_summary = self.issue_manager.get_summary()

        return {
            "프로젝트정보": self.context.to_summary_dict(),
            "시뮬레이션결과": {
                "목표공기": f"{self.context.target_days}일",
                "실제소요": f"{self.context.target_days + int(self.total_delay_days)}일",
                "누적지연": f"{self.total_delay_days:.1f}일",
                "누적비용증가": f"{self.total_cost_increase_pct:.2f}%",
                "총이슈수": issue_summary["전체이슈수"],
                "해결완료": issue_summary["해결완료"],
                "진행중": issue_summary["해결중"],
            },
            "이슈상세": issue_summary,
        }

    def save_results(self, output_dir: str, summary: Dict):
        """결과 저장 - 로그와 결과 분리"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 1. logs/ 폴더에 전체 회의 로그 저장 (1개 파일)
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        meeting_log_file = log_dir / f"{self.method.lower()}_meetings_{timestamp}.json"
        meeting_log_data = {
            "시뮬레이션정보": {
                "공법": self.method,
                "시작일": timestamp,
                "총일수": len(self.daily_logs),
            },
            "회의로그": self.daily_logs
        }
        with open(meeting_log_file, "w", encoding="utf-8") as f:
            json.dump(meeting_log_data, f, ensure_ascii=False, indent=2)

        print(f"\n회의 로그 저장 완료: {meeting_log_file}")
        print(f"  - 총 {len(self.daily_logs)}일치 회의 기록")

        # 2. logs/ 폴더에 이슈 목록 저장
        issues_file = log_dir / f"{self.method.lower()}_issues_{timestamp}.json"
        issues_data = {
            "총이슈수": len(self.issue_manager.all_issues),
            "이슈목록": [issue.to_dict() for issue in self.issue_manager.all_issues]
        }
        with open(issues_file, "w", encoding="utf-8") as f:
            json.dump(issues_data, f, ensure_ascii=False, indent=2)

        print(f"이슈 목록 저장 완료: {issues_file}")
        print(f"  - 총 {len(self.issue_manager.all_issues)}개 이슈")

        # 3. results/ 폴더에 요약 결과만 저장
        result_dir = Path(output_dir)
        result_dir.mkdir(exist_ok=True)

        result_file = result_dir / f"summary_{self.method}_{timestamp}.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"결과 요약 저장 완료: {result_file}\n")

        return timestamp  # 타임스탬프 반환 (비교 리포트용)
