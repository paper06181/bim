"""
시뮬레이션 메인 엔진
"""

from pathlib import Path
from datetime import datetime
from .issue_manager import IssueManager
from .meeting_coordinator import MeetingCoordinator
from .impact_calculator import ImpactCalculator
from config.project_config import ProjectConfig

class SimulationEngine:
    """시뮬레이션 엔진"""

    def __init__(self, project, agents, save_logs=True, random_seed=None):
        """
        Args:
            project: Project 인스턴스
            agents: 에이전트 딕셔너리
            save_logs: 시뮬레이션 로그 자동 저장 여부
            random_seed: 랜덤 시드 (비교 시 동일 이슈 발생)
        """
        self.project = project
        self.agents = agents
        self.issue_manager = IssueManager(random_seed=random_seed)

        # BIM 상태를 MeetingCoordinator에 전달
        bim_status = "BIM_ON" if project.bim_enabled else "BIM_OFF"
        self.meeting_coordinator = MeetingCoordinator(agents, save_meetings=save_logs, bim_status=bim_status)
        self.impact_calculator = ImpactCalculator()

        self.simulation_log = []
        self.save_logs = save_logs

        # 로그 저장 폴더 생성
        if self.save_logs:
            self.logs_dir = Path("output/logs")
            self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def run(self, verbose=True):
        """시뮬레이션 실행"""
        print(f"\n{'='*70}")
        print(f"시뮬레이션 시작: {self.project.name}")
        print(f"BIM 적용: {'ON' if self.project.bim_enabled else 'OFF'}")
        print(f"{'='*70}\n")
        
        for phase_name, duration in ProjectConfig.PHASE_DURATIONS.items():
            if verbose:
                print(f"\n[{phase_name} 단계 시작]")
            
            for day_in_phase in range(duration):
                self.project.advance_day()
                
                triggered_issues = self.issue_manager.check_and_trigger_issues(self.project)
                
                for issue in triggered_issues:
                    self._process_issue(issue, verbose)
                
                if self.project.current_day % 30 == 0 and verbose:
                    self._periodic_review()
            
            if verbose:
                print(f"[{phase_name} 단계 완료]\n")
        
        metrics = self.project.calculate_final_metrics()

        if verbose:
            print(f"\n{'='*70}")
            print("시뮬레이션 완료")
            print(f"{'='*70}")
            print(self.project.get_summary())

        # 로그 및 회의록 저장
        if self.save_logs:
            self._save_simulation_log()
            self.meeting_coordinator.save_all_meetings_to_file(self.project.name)

        return metrics
    
    def _process_issue(self, issue, verbose):
        """이슈 처리 프로세스"""
        if verbose:
            print(f"\n>>> 이슈 발생: {issue['name']} (Day {self.project.current_day})")
        
        initial_meeting = self.meeting_coordinator.conduct_meeting(
            issue, self.project, None
        )
        
        if verbose:
            self.meeting_coordinator.print_meeting(initial_meeting)
        
        impact_result = self.impact_calculator.calculate_impact(issue, self.project)
        
        decision_meeting = self.meeting_coordinator.conduct_meeting(
            issue, self.project, impact_result
        )
        
        if verbose:
            self.meeting_coordinator.print_meeting(decision_meeting)
            self._print_impact_summary(impact_result)
        
        self.project.apply_impact(impact_result)
        
        self.simulation_log.append({
            'day': self.project.current_day,
            'issue': issue,
            'impact': impact_result,
            'initial_meeting': initial_meeting,
            'decision_meeting': decision_meeting
        })
    
    def _print_impact_summary(self, impact_result):
        """영향 요약 출력"""
        print(f"\n--- 영향 요약 ---")
        print(f"지연: {impact_result['delay_weeks']:.2f}주")
        print(f"비용 증가: {impact_result['cost_increase']*100:.2f}%")
        print(f"탐지 여부: {'예' if impact_result['detected'] else '아니오'}")

        if impact_result['detected']:
            print(f"탐지 단계: {impact_result['detection_phase']}")
            print(f"BIM 효과성: {impact_result['bim_effectiveness']:.2f}")
            if 'savings' in impact_result:
                print(f"절감 효과:")
                print(f"  - 지연 회피: {impact_result['savings']['delay_avoided']:.2f}주")
                print(f"  - 비용 회피: {impact_result['savings']['cost_avoided']*100:.2f}%")

        if impact_result.get('financial_cost'):
            fc = impact_result['financial_cost']
            if fc['rate_increase_bp'] > 0:
                print(f"금리 인상: +{fc['rate_increase_bp']}bp → {fc['new_interest_rate']*100:.2f}%")
            print(f"금융 비용 세부:")
            print(f"  - 추가 이자: {fc.get('interest_increase', 0):,.0f}원")
            print(f"  - 간접비: {fc.get('indirect_cost', 0):,.0f}원")
            print(f"  - 지체상금: {fc.get('penalty_amount', 0):,.0f}원")
            print(f"  - 총액: {fc['total_financial_cost']:,.0f}원")

        print(f"--- 영향 요약 끝 ---\n")
    
    def _periodic_review(self):
        """정기 검토"""
        print(f"\n{'*'*60}")
        print(f"정기 검토 - Day {self.project.current_day}")
        print(f"{'*'*60}")
        
        metrics = self.project.calculate_final_metrics()
        print(f"누적 지연: {metrics['delay_weeks']:.1f}주")
        print(f"누적 비용 증가: {metrics['cost_increase']:,.0f}원 ({metrics['budget_overrun_rate']*100:.1f}%)")
        print(f"발생 이슈: {metrics['issues_count']}건")
        print(f"탐지율: {metrics['detection_rate']*100:.1f}%")
        
        bank_review = self.agents['bank'].periodic_review(self.project)
        print(bank_review)
        print(f"{'*'*60}\n")
    
    def get_simulation_log(self):
        """시뮬레이션 로그 반환"""
        return self.simulation_log

    def _save_simulation_log(self):
        """시뮬레이션 로그를 파일로 저장"""
        bim_status = "BIM_ON" if self.project.bim_enabled else "BIM_OFF"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"simulation_log_{bim_status}_{timestamp}.txt"
        filepath = self.logs_dir / filename

        content = []
        content.append("="*80)
        content.append(f"시뮬레이션 로그")
        content.append(f"프로젝트: {self.project.name}")
        content.append(f"BIM 적용: {'ON' if self.project.bim_enabled else 'OFF'}")
        content.append(f"생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append("="*80)
        content.append("")

        # 프로젝트 요약
        content.append("## 프로젝트 요약")
        content.append(self.project.get_summary())
        content.append("")

        # 이슈별 상세 로그
        content.append("="*80)
        content.append(f"발생 이슈 상세 로그 (총 {len(self.simulation_log)}건)")
        content.append("="*80)
        content.append("")

        for idx, log_entry in enumerate(self.simulation_log, 1):
            issue = log_entry['issue']
            impact = log_entry['impact']
            day = log_entry['day']

            content.append(f"[이슈 #{idx}] {issue['name']} ({issue['id']})")
            content.append(f"발생 시점: Day {day} ({self.project.current_phase})")
            content.append(f"심각도: {issue['severity']}")
            content.append("")

            content.append("### 영향 분석")
            content.append(f"  - 탐지 여부: {'예' if impact['detected'] else '아니오'}")
            content.append(f"  - 지연: {impact['delay_weeks']:.2f}주 ({impact['delay_weeks']*7:.1f}일)")
            content.append(f"  - 비용 증가: {impact['cost_increase']:,.0f}원")

            if impact['detected']:
                content.append(f"  - 탐지 단계: {impact['detection_phase']}")
                content.append(f"  - BIM 효과성: {impact.get('bim_effectiveness', 0):.2f}")

            if impact.get('financial_cost'):
                fc = impact['financial_cost']
                content.append(f"  - 금리 인상: +{fc['rate_increase_bp']}bp")
                content.append(f"  - 신규 금리: {fc['new_interest_rate']*100:.2f}%")
                content.append(f"  - 추가 이자: {fc.get('interest_increase', 0):,.0f}원")
                content.append(f"  - 간접비: {fc.get('indirect_cost', 0):,.0f}원")
                content.append(f"  - 지체상금: {fc.get('penalty_amount', 0):,.0f}원")
                content.append(f"  - 총 금융비용: {fc['total_financial_cost']:,.0f}원")

            # 협상 결과 추가
            if impact.get('negotiation_summary'):
                content.append("")
                content.append("### 협상 결과")
                content.append(f"  {impact['negotiation_summary']}")

            content.append("")

            # 초기 회의 내용
            initial_meeting = log_entry['initial_meeting']
            content.append("### 초기 회의 (문제 인식)")
            for conv in initial_meeting['conversations']:
                content.append(f"  {conv}")
            content.append("")

            # 의사결정 회의 내용
            decision_meeting = log_entry['decision_meeting']
            content.append("### 의사결정 회의 (해결 방안)")
            for conv in decision_meeting['conversations']:
                content.append(f"  {conv}")
            content.append("")

            content.append("-"*80)
            content.append("")

        # 최종 통계
        metrics = self.project.calculate_final_metrics()
        content.append("="*80)
        content.append("최종 통계")
        content.append("="*80)
        content.append(f"총 공사 기간: {metrics['actual_duration']:.1f}일 (계획: {metrics['planned_duration']}일)")
        content.append(f"지연: {metrics['delay_days']:.1f}일 ({metrics['delay_weeks']:.1f}주)")
        content.append(f"최종 비용: {metrics['actual_cost']:,.0f}원")
        content.append(f"예산 초과: {metrics['cost_increase']:,.0f}원 ({metrics['budget_overrun_rate']*100:.1f}%)")
        content.append(f"발생 이슈: {metrics['issues_count']}건")
        content.append(f"탐지된 이슈: {metrics['detected_count']}건")
        content.append(f"탐지율: {metrics['detection_rate']*100:.1f}%")
        content.append("")
        content.append("="*80)

        # 파일 저장
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))

        print(f"[로그 저장] {filepath}")
        return filepath