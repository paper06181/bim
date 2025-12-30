"""
매일 회의 로그 및 리포트 작성
"""
import os
from datetime import datetime
from typing import List, Dict

class DailyLogger:
    """일일 회의 로그 및 리포트 작성 클래스"""

    def __init__(self, output_dir: str = "output/daily_logs"):
        """
        Args:
            output_dir: 로그 저장 디렉토리
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.meeting_log = []
        self.daily_summary = []

    def log_daily_meeting(self, day: int, progress: float, segment: str,
                          issues: List, resolutions: Dict[str, float]):
        """
        매일 회의 내용 기록

        Args:
            day: 일자
            progress: 공정률
            segment: 공정률 구간
            issues: 처리한 이슈 리스트
            resolutions: 이슈별 resolution_level
        """
        if not issues:
            return

        log_entry = {
            'day': day,
            'progress': progress,
            'segment': segment,
            'issues_count': len(issues),
            'resolutions': resolutions
        }

        self.meeting_log.append(log_entry)

        # 콘솔 출력
        print(f"\n[Day {day}] 공정률: {progress*100:.1f}% (구간: {segment})")
        print(f"  처리 이슈: {len(issues)}개")

        # 주요 이슈 출력 (상위 3개)
        high_priority = sorted(issues, key=lambda x: x.base_risk, reverse=True)[:3]
        for issue in high_priority:
            res_level = resolutions.get(issue.issue_id, 0.5)
            print(f"    - {issue.issue_id}: {issue.name[:30]} "
                  f"(리스크={issue.base_risk:.3f}, 대응={res_level:.1f})")

    def log_daily_result(self, day: int, issues_occurred: int,
                        delay_today: float, cost_today: float):
        """
        매일 결과 기록

        Args:
            day: 일자
            issues_occurred: 발생한 이슈 수
            delay_today: 오늘 발생한 지연 (일)
            cost_today: 오늘 발생한 비용 증가 (%)
        """
        summary = {
            'day': day,
            'issues_occurred': issues_occurred,
            'delay': delay_today,
            'cost': cost_today
        }
        self.daily_summary.append(summary)

    def save_meeting_log(self, scenario_name: str):
        """
        회의 로그 파일 저장

        Args:
            scenario_name: 시나리오 이름 (예: "BIM_Applied")
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/meetings_{scenario_name}_{timestamp}.txt"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(f"매일 회의 로그 - {scenario_name}\n")
            f.write(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")

            for entry in self.meeting_log:
                f.write(f"\n[Day {entry['day']}] "
                       f"공정률: {entry['progress']*100:.1f}% "
                       f"(구간: {entry['segment']})\n")
                f.write(f"  처리 이슈 수: {entry['issues_count']}개\n")

                if entry['resolutions']:
                    f.write(f"  Resolution Levels:\n")
                    for issue_id, res_level in entry['resolutions'].items():
                        f.write(f"    - {issue_id}: {res_level:.2f}\n")

                f.write("\n" + "-"*80 + "\n")

        print(f"\n[로그 저장] {filename}")
        return filename

    def save_daily_report(self, scenario_name: str,
                         total_delay: float, total_cost: float):
        """
        일일 결과 리포트 저장

        Args:
            scenario_name: 시나리오 이름
            total_delay: 총 지연 (일)
            total_cost: 총 비용 증가 (%)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/report_{scenario_name}_{timestamp}.txt"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(f"일일 결과 리포트 - {scenario_name}\n")
            f.write(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")

            f.write(f"최종 결과:\n")
            f.write(f"  총 지연: {total_delay:.1f}일\n")
            f.write(f"  총 비용 증가: {total_cost:.2f}%\n")
            f.write(f"  총 처리 이슈: {sum(s['issues_occurred'] for s in self.daily_summary)}개\n\n")

            f.write(f"일별 상세:\n")
            f.write(f"{'Day':<6} {'이슈':<6} {'지연(일)':<12} {'비용(%)':<12}\n")
            f.write("-"*80 + "\n")

            for summary in self.daily_summary:
                if summary['issues_occurred'] > 0:
                    f.write(f"{summary['day']:<6} "
                           f"{summary['issues_occurred']:<6} "
                           f"{summary['delay']:<12.2f} "
                           f"{summary['cost']:<12.4f}\n")

        print(f"[리포트 저장] {filename}")
        return filename
