"""
결과 보고서 생성
"""
from datetime import datetime
from typing import Optional

class ReportGenerator:
    """보고서 생성기"""
    
    @staticmethod
    def generate_comparison_report(metrics_off, metrics_on):
        """BIM ON/OFF 비교 보고서"""
        report = f"""
{'='*80}
BIM 적용 효과 비교 보고서
{'='*80}

1. 공사 기간
{'─'*80}
구분              | 계획(일)  | 실제(일)  | 지연(일)  | 지연률
{'─'*80}
BIM OFF          | {metrics_off['planned_duration']:7.0f}   | {metrics_off['actual_duration']:7.1f}   | {metrics_off['delay_days']:7.1f}   | {metrics_off['schedule_delay_rate']*100:5.1f}%
BIM ON           | {metrics_on['planned_duration']:7.0f}   | {metrics_on['actual_duration']:7.1f}   | {metrics_on['delay_days']:7.1f}   | {metrics_on['schedule_delay_rate']*100:5.1f}%
{'─'*80}
개선 효과        | -        | {metrics_off['actual_duration']-metrics_on['actual_duration']:7.1f}일 단축 | {metrics_off['delay_days']-metrics_on['delay_days']:7.1f}일 감소 | {(metrics_off['schedule_delay_rate']-metrics_on['schedule_delay_rate'])*100:5.1f}%p

2. 공사 비용
{'─'*80}
구분              | 계획(억원) | 실제(억원) | 초과(억원) | 초과율
{'─'*80}
BIM OFF          | {metrics_off['planned_budget']/100000000:7.1f}    | {metrics_off['actual_cost']/100000000:7.1f}    | {metrics_off['cost_increase']/100000000:7.1f}    | {metrics_off['budget_overrun_rate']*100:5.1f}%
BIM ON           | {metrics_on['planned_budget']/100000000:7.1f}    | {metrics_on['actual_cost']/100000000:7.1f}    | {metrics_on['cost_increase']/100000000:7.1f}    | {metrics_on['budget_overrun_rate']*100:5.1f}%
{'─'*80}
절감 효과        | -         | -         | {(metrics_off['cost_increase']-metrics_on['cost_increase'])/100000000:7.1f}억원 | {(metrics_off['budget_overrun_rate']-metrics_on['budget_overrun_rate'])*100:5.1f}%p

3. 비용 세부 내역
{'─'*80}
구분              | 직접비용(억원) | 금융비용(억원) | 합계(억원)
{'─'*80}
BIM OFF          | {metrics_off['direct_cost_increase']/100000000:11.2f}      | {metrics_off['financial_cost']/100000000:11.2f}      | {metrics_off['cost_increase']/100000000:8.2f}
BIM ON           | {metrics_on['direct_cost_increase']/100000000:11.2f}      | {metrics_on['financial_cost']/100000000:11.2f}      | {metrics_on['cost_increase']/100000000:8.2f}
{'─'*80}
절감             | {(metrics_off['direct_cost_increase']-metrics_on['direct_cost_increase'])/100000000:11.2f}      | {(metrics_off['financial_cost']-metrics_on['financial_cost'])/100000000:11.2f}      | {(metrics_off['cost_increase']-metrics_on['cost_increase'])/100000000:8.2f}

4. 이슈 관리
{'─'*80}
구분              | 발생(건) | 탐지(건) | 미탐지(건) | 탐지율
{'─'*80}
BIM OFF          | {metrics_off['issues_count']:6}   | {metrics_off['detected_count']:6}   | {metrics_off['missed_count']:8}   | {metrics_off['detection_rate']*100:5.1f}%
BIM ON           | {metrics_on['issues_count']:6}   | {metrics_on['detected_count']:6}   | {metrics_on['missed_count']:8}   | {metrics_on['detection_rate']*100:5.1f}%
{'─'*80}
개선             | {metrics_off['issues_count']-metrics_on['issues_count']:6}   | +{metrics_on['detected_count']-metrics_off['detected_count']:5}   | {metrics_off['missed_count']-metrics_on['missed_count']:8}   | +{(metrics_on['detection_rate']-metrics_off['detection_rate'])*100:5.1f}%p

5. 금융 지표
{'─'*80}
구분              | 최종 금리
{'─'*80}
BIM OFF          | {metrics_off['final_interest_rate']*100:6.2f}%
BIM ON           | {metrics_on['final_interest_rate']*100:6.2f}%
{'─'*80}
차이             | {(metrics_off['final_interest_rate']-metrics_on['final_interest_rate'])*10000:6.0f}bp

{'='*80}
핵심 요약
{'='*80}
BIM 적용을 통한 개선 효과:
- 공사 기간: {metrics_off['delay_days']-metrics_on['delay_days']:.1f}일 단축 ({(1-metrics_on['schedule_delay_rate']/metrics_off['schedule_delay_rate'])*100 if metrics_off['schedule_delay_rate'] > 0 else 0:.1f}% 개선)
- 공사 비용: {(metrics_off['cost_increase']-metrics_on['cost_increase'])/100000000:.2f}억원 절감 ({(1-metrics_on['budget_overrun_rate']/metrics_off['budget_overrun_rate'])*100 if metrics_off['budget_overrun_rate'] > 0 else 0:.1f}% 개선)
- 이슈 탐지율: {(metrics_on['detection_rate']-metrics_off['detection_rate'])*100:.1f}%p 향상
- 금리 인상 억제: {(metrics_off['final_interest_rate']-metrics_on['final_interest_rate'])*10000:.0f}bp 절감
{'='*80}
"""
        return report
    
    @staticmethod
    def generate_single_report(metrics, scenario_name):
        """단일 시나리오 보고서"""
        report = f"""
{'='*70}
{scenario_name} 시나리오 결과 보고서
{'='*70}

1. 프로젝트 개요
  - 프로젝트명: 청담동 근린생활시설 신축공사
  - 계획 예산: {metrics['planned_budget']/100000000:.1f}억원
  - 계획 공기: {metrics['planned_duration']}일

2. 최종 결과
  - 실제 공기: {metrics['actual_duration']:.0f}일
  - 지연: {metrics['delay_days']:.0f}일 ({metrics['delay_weeks']:.1f}주)
  - 지연률: {metrics['schedule_delay_rate']*100:.1f}%
  
  - 실제 비용: {metrics['actual_cost']/100000000:.2f}억원
  - 초과: {metrics['cost_increase']/100000000:.2f}억원
  - 초과율: {metrics['budget_overrun_rate']*100:.1f}%

3. 비용 세부
  - 직접 비용 증가: {metrics['direct_cost_increase']/100000000:.2f}억원
  - 금융 비용: {metrics['financial_cost']/100000000:.2f}억원

4. 이슈 통계
  - 발생: {metrics['issues_count']}건
  - 탐지: {metrics['detected_count']}건
  - 미탐지: {metrics['missed_count']}건
  - 탐지율: {metrics['detection_rate']*100:.1f}%

5. 금융
  - 최종 금리: {metrics['final_interest_rate']*100:.2f}%

{'='*70}
"""
        return report

    @staticmethod
    def generate_detailed_comparison_report(comparison, project_info):
        """
        상세 비교 보고서 생성

        Args:
            comparison: ComparisonResult 객체
            project_info: ProjectInfo 객체

        Returns:
            str: 상세 텍스트 보고서
        """
        baseline = comparison.baseline
        comp = comparison.comparison
        case = project_info.case

        # 타임스탬프
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""
{'='*100}
BIM 효과 정량화 시뮬레이션 결과 보고서
{'='*100}
생성일시: {timestamp}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 프로젝트 개요
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

프로젝트명     : {project_info.project_name}
케이스 ID      : {case.case_id}
KPI 등급       : {case.kpi_grade}

[케이스 상세 정보]
  - 입지 유형   : {case.location_type if case.location_type else 'N/A'}
  - 용도지역    : {case.zoning if case.zoning else 'N/A'}
  - 세부지역    : {case.detailed_zoning if case.detailed_zoning else 'N/A'}
  - 용적률      : {case.far if case.far else 'N/A'}%
  - 건폐율      : {case.bcr if case.bcr else 'N/A'}%

[프로젝트 기준값]
  - 계획 공기   : {project_info.duration_days}일
  - 계획 예산   : {project_info.base_cost:,}원 ({project_info.base_cost/100000000:.1f}억원)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2. 사용된 KPI 지표
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[전통 방식 (TRAD) KPI 지표]
"""
        # TRAD KPI 출력
        for kpi_name, kpi_value in case.kpi_trad.values.items():
            kpi_desc = {
                'RR': '재작업률 (Rework Rate)',
                'SR': '일정 신뢰도 (Schedule Reliability)',
                'CR': '의사소통 효율 (Communication Efficiency)',
                'FC': '현장 조정 능력 (Field Coordination)'
            }.get(kpi_name, kpi_name)
            report += f"  - {kpi_desc:40s} : {kpi_value:.4f}\n"

        report += f"""
[BIM 적용 방식 (BIM) KPI 지표]
"""
        # BIM KPI 출력
        for kpi_name, kpi_value in case.kpi_bim.values.items():
            kpi_desc = {
                'WD': '경고 밀도 (Warning Density)',
                'CD': '충돌 밀도 (Clash Density)',
                'AF': '속성 완성도 (Attribute Fill)',
                'PL': '공정 연계도 (Phase Link)'
            }.get(kpi_name, kpi_name)
            report += f"  - {kpi_desc:40s} : {kpi_value:.4f}\n"

        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3. 시뮬레이션 결과 비교
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[공사 기간 비교]
{'─'*100}
{'구분':<20} {'계획(일)':>12} {'실제(일)':>12} {'지연(일)':>12} {'지연율':>12}
{'─'*100}
{baseline.scenario_name:<20} {project_info.duration_days:>12} {baseline.actual_duration:>12.1f} {baseline.total_delay_days:>12.1f} {(baseline.total_delay_days/project_info.duration_days*100):>11.2f}%
{comp.scenario_name:<20} {project_info.duration_days:>12} {comp.actual_duration:>12.1f} {comp.total_delay_days:>12.1f} {(comp.total_delay_days/project_info.duration_days*100):>11.2f}%
{'─'*100}
{'개선 효과':<20} {'-':>12} {(baseline.actual_duration - comp.actual_duration):>11.1f}일 {comparison.delay_reduction_days:>11.1f}일 {((baseline.total_delay_days - comp.total_delay_days)/project_info.duration_days*100):>11.2f}%p
{'─'*100}

[공사 비용 비교 - 직접 비용]
{'─'*100}
{'구분':<20} {'계획(억원)':>14} {'실제(억원)':>14} {'증가(억원)':>14} {'증가율':>12}
{'─'*100}
{baseline.scenario_name:<20} {project_info.base_cost/100000000:>14.2f} {baseline.actual_cost/100000000:>14.2f} {(baseline.actual_cost - project_info.base_cost)/100000000:>14.2f} {baseline.total_cost_pct:>11.2f}%
{comp.scenario_name:<20} {project_info.base_cost/100000000:>14.2f} {comp.actual_cost/100000000:>14.2f} {(comp.actual_cost - project_info.base_cost)/100000000:>14.2f} {comp.total_cost_pct:>11.2f}%
{'─'*100}
{'절감 효과':<20} {'-':>14} {(baseline.actual_cost - comp.actual_cost)/100000000:>13.2f}억 {((baseline.actual_cost - project_info.base_cost) - (comp.actual_cost - project_info.base_cost))/100000000:>13.2f}억 {comparison.cost_reduction_pct:>11.2f}%p
{'─'*100}

[총 비용 비교 - EVMS 통합 (직접비용 + 지연손실)]
{'─'*100}
{'구분':<20} {'기준공사비':>14} {'직접비용':>12} {'지연손실':>12} {'통합총비용':>14} {'통합증가율':>12}
{'─'*100}
{baseline.scenario_name:<20} {project_info.base_cost/100000000:>13.2f}억 {baseline.actual_cost/100000000:>11.2f}억 {baseline.delay_cost_equivalent/100000000:>11.2f}억 {baseline.integrated_total_cost/100000000:>13.2f}억 {baseline.integrated_cost_pct:>11.2f}%
{comp.scenario_name:<20} {project_info.base_cost/100000000:>13.2f}억 {comp.actual_cost/100000000:>11.2f}억 {comp.delay_cost_equivalent/100000000:>11.2f}억 {comp.integrated_total_cost/100000000:>13.2f}억 {comp.integrated_cost_pct:>11.2f}%
{'─'*100}
{'BIM 절감 효과':<20} {'-':>14} {(baseline.actual_cost - comp.actual_cost)/100000000:>10.2f}억 {(baseline.delay_cost_equivalent - comp.delay_cost_equivalent)/100000000:>10.2f}억 {comparison.integrated_cost_reduction/100000000:>12.2f}억 {comparison.integrated_cost_reduction_pct:>11.2f}%p
{'─'*100}

[EVMS 통합 비용 설명]
- 기준공사비: 프로젝트 계획 공사비
- 직접비용: 이슈 발생으로 인한 실제 비용 증가 (재작업, 추가 자재 등)
- 지연손실: 공기 지연으로 인한 기회비용 = 지연일수 × (기준공사비 / 계획공기)
  * 예: 50억 프로젝트, 365일 계획 → 1일 지연 = 약 1,370만원 손실
- 통합총비용 = 직접비용 + 지연손실 (EVMS 핵심 지표)
- BIM 효과: 전통 방식 대비 통합 비용 절감액 (직접비용 절감 + 지연 단축 효과)

[이슈 관리 비교]
{'─'*100}
{'구분':<20} {'평가 이슈':>12} {'발생 이슈':>12} {'Major':>10} {'Minor':>10} {'발생율':>12}
{'─'*100}
{baseline.scenario_name:<20} {baseline.issues_evaluated:>12} {baseline.issues_occurred:>12} {baseline.issues_major:>10} {baseline.issues_minor:>10} {(baseline.issues_occurred/baseline.issues_evaluated*100 if baseline.issues_evaluated > 0 else 0):>11.2f}%
{comp.scenario_name:<20} {comp.issues_evaluated:>12} {comp.issues_occurred:>12} {comp.issues_major:>10} {comp.issues_minor:>10} {(comp.issues_occurred/comp.issues_evaluated*100 if comp.issues_evaluated > 0 else 0):>11.2f}%
{'─'*100}
{'개선 효과':<20} {'-':>12} {baseline.issues_occurred - comp.issues_occurred:>11}건 {baseline.issues_major - comp.issues_major:>9}건 {baseline.issues_minor - comp.issues_minor:>9}건 {((baseline.issues_occurred - comp.issues_occurred)/baseline.issues_evaluated*100 if baseline.issues_evaluated > 0 else 0):>11.2f}%p
{'─'*100}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4. 핵심 성과 지표 (KPI)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[공기 단축 효과]
  - 절대값     : {comparison.delay_reduction_days:.1f}일 ({comparison.delay_reduction_weeks:.2f}주)
  - 개선율     : {(comparison.delay_reduction_days/baseline.total_delay_days*100 if baseline.total_delay_days > 0 else 0):.2f}%
  - 계획 대비  : {(comparison.delay_reduction_days/project_info.duration_days*100):.2f}%

[비용 절감 효과 - 직접 비용]
  - 절대값     : {(baseline.actual_cost - comp.actual_cost)/100000000:.2f}억원
  - 절감율     : {comparison.cost_reduction_pct:.2f}%p
  - 금액       : {baseline.actual_cost - comp.actual_cost:,.0f}원

[EVMS 통합 비용 절감 효과 - 일정 지연 포함]
  - 지연환산비용 절감 : {(baseline.delay_cost_equivalent - comp.delay_cost_equivalent)/100000000:.2f}억원
  - 통합 비용 절감   : {comparison.integrated_cost_reduction/100000000:.2f}억원
  - 통합 절감율      : {comparison.integrated_cost_reduction_pct:.2f}%p
  - 통합 절감 금액   : {comparison.integrated_cost_reduction:,.0f}원

[이슈 감소 효과]
  - 발생 감소  : {baseline.issues_occurred - comp.issues_occurred}건
  - Major 감소 : {baseline.issues_major - comp.issues_major}건
  - Minor 감소 : {baseline.issues_minor - comp.issues_minor}건

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5. 결론
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BIM 적용을 통한 개선 효과:

✓ 공사 기간 : {comparison.delay_reduction_days:.1f}일 단축
             ({(comparison.delay_reduction_days/baseline.total_delay_days*100 if baseline.total_delay_days > 0 else 0):.1f}% 개선)

✓ 직접 비용 : {(baseline.actual_cost - comp.actual_cost)/100000000:.2f}억원 절감
             ({comparison.cost_reduction_pct:.2f}%p 개선)

✓✓ EVMS 통합 비용 (일정+비용) : {comparison.integrated_cost_reduction/100000000:.2f}억원 절감
                              ({comparison.integrated_cost_reduction_pct:.2f}%p 개선)
                              ※ 일정 지연을 비용으로 환산하여 통합 평가

✓ 이슈 관리 : {baseline.issues_occurred - comp.issues_occurred}건 감소
             (Major {baseline.issues_major - comp.issues_major}건, Minor {baseline.issues_minor - comp.issues_minor}건 감소)

{'='*100}
보고서 끝
{'='*100}
"""
        return report