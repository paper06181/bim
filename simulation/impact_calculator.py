"""
이슈 영향도 계산 (핵심 로직)
"""

import random
from models.bim_quality import BIMQuality
from models.financial import FinancialCalculator
from simulation.negotiation_system import NegotiationSystem

class ImpactCalculator:
    """이슈 영향도 계산기"""

    def __init__(self):
        """협상 시스템 초기화"""
        self.negotiation_system = NegotiationSystem()

    def calculate_impact(self, issue, project):
        """이슈의 최종 영향 계산"""
        # 긍정적 이슈는 별도 처리
        if issue.get('is_positive', False):
            return self._calculate_positive_impact(issue, project)

        # 부정적 이슈는 기존 로직
        if not project.bim_enabled:
            return self._calculate_traditional_impact(
                issue, project
            )
        else:
            return self._calculate_bim_impact(
                issue, project
            )

    def _calculate_traditional_impact(self, issue, project):
        """전통 방식 영향 계산 (협상 시스템 사용)"""
        # 협상을 통해 최종 지연/비용 결정
        negotiation_result = self.negotiation_system.negotiate(
            issue, project, detected=False
        )

        actual_delay = negotiation_result['delay_weeks']
        actual_cost = negotiation_result['cost_increase']

        # 추가 불확실성 (전통 방식은 예측이 어려움)
        uncertainty_multiplier = random.uniform(1.0, 1.15)
        actual_delay *= uncertainty_multiplier
        actual_cost *= uncertainty_multiplier

        financial_cost = FinancialCalculator.calculate_financial_cost(
            project, actual_delay
        )

        if financial_cost['rate_increase_bp'] > 0:
            FinancialCalculator.update_project_interest_rate(project, financial_cost)

        return {
            'issue_id': issue['id'],
            'issue_name': issue['name'],
            'delay_weeks': actual_delay,
            'cost_increase': actual_cost,
            'detected': False,
            'detection_phase': None,
            'bim_effectiveness': 0.0,
            'detection_probability': 0.0,
            'financial_cost': financial_cost,
            'negotiation_summary': negotiation_result['negotiation_summary']
        }

    def _calculate_bim_impact(self, issue, project):
        """BIM 적용 시 영향 계산 (진짜 조기 탐지 로직)"""
        # BIM 효과성 및 탐지 확률 계산
        bim_effectiveness = BIMQuality.calculate_effectiveness(
            issue['id'],
            project.bim_quality
        )

        detection_prob = BIMQuality.calculate_detection_probability(
            issue,
            bim_effectiveness
        )

        # 조기 탐지 성공 여부 결정
        detected = random.random() < detection_prob

        # origin_phase: 이슈가 발생한 단계 (현재)
        # phase: 미탐지 시 문제가 드러나는 단계 (나중)
        origin_phase = issue.get('origin_phase', issue['phase'])
        impact_phase = issue['phase']  # 미탐지 시 발현 단계
        detection_phase = issue['bim_effect']['detection_phase']

        if detected and detection_phase:
            # ✅ 조기 탐지 성공!
            # origin_phase에서 바로 발견하여 해결
            # 예: 설계 단계에서 간섭 발견 → 도면만 수정

            # 협상 (조기 탐지로 건축주 협상력 UP)
            negotiation_result = self.negotiation_system.negotiate(
                issue, project, detected=True
            )

            # 조기 탐지 절감 효과 (단계별)
            reduction_by_phase = {
                '설계': {'delay': 0.90, 'cost': 0.85},      # 설계에서 발견 → 90% 지연, 85% 비용 절감
                '발주': {'delay': 0.70, 'cost': 0.75},      # 발주에서 발견 → 70% 지연, 75% 비용 절감
                '시공초기': {'delay': 0.50, 'cost': 0.60},  # 시공 초기 → 50% 지연, 60% 비용 절감
                '시공중기': {'delay': 0.30, 'cost': 0.40},  # 시공 중기 → 30% 지연, 40% 비용 절감
                '시공후기': {'delay': 0.10, 'cost': 0.15}   # 시공 후기 → 10% 지연, 15% 비용 절감
            }

            reduction = reduction_by_phase.get(
                detection_phase,
                {'delay': 0.5, 'cost': 0.6}
            )

            # BIM 품질 보너스 (최대 15% 추가 절감)
            quality_bonus = bim_effectiveness * 0.10

            # 최종 절감률
            final_delay_reduction = min(0.95, reduction['delay'] + quality_bonus)
            final_cost_reduction = min(0.95, reduction['cost'] + quality_bonus)

            # 협상된 값에 절감 적용
            base_delay = negotiation_result['delay_weeks']
            base_cost = negotiation_result['cost_increase']

            actual_delay = base_delay * (1.0 - final_delay_reduction)
            actual_cost = base_cost * (1.0 - final_cost_reduction)

            # 조기 탐지로 지연이 매우 짧아짐 (최소값 보장)
            actual_delay = max(0.1, actual_delay)  # 최소 0.1주
            actual_cost = max(base_cost * 0.05, actual_cost)  # 최소 5%

            financial_cost = FinancialCalculator.calculate_financial_cost(
                project, actual_delay
            )

            if financial_cost['rate_increase_bp'] > 0:
                FinancialCalculator.update_project_interest_rate(project, financial_cost)

            return {
                'issue_id': issue['id'],
                'issue_name': issue['name'],
                'delay_weeks': actual_delay,
                'cost_increase': actual_cost,
                'detected': True,
                'detection_phase': detection_phase,
                'bim_effectiveness': bim_effectiveness,
                'detection_probability': detection_prob,
                'financial_cost': financial_cost,
                'negotiation_summary': negotiation_result['negotiation_summary'],
                'early_detection': True,  # 조기 탐지 플래그
                'savings': {
                    'delay_avoided': base_delay - actual_delay,
                    'cost_avoided': base_cost - actual_cost
                }
            }

        else:
            # ❌ 조기 탐지 실패 또는 탐지 불가능
            # origin_phase에서 발견 못함 → 나중에 impact_phase에서 터짐
            # 예: 설계 오류를 못 찾음 → 시공 중 발견 → 재작업

            # 협상 (미탐지로 시공사 입장 강화)
            negotiation_result = self.negotiation_system.negotiate(
                issue, project, detected=False
            )

            actual_delay = negotiation_result['delay_weeks']
            actual_cost = negotiation_result['cost_increase']

            # BIM 있어도 미탐지면 불확실성 추가
            uncertainty_multiplier = random.uniform(1.05, 1.15)
            actual_delay *= uncertainty_multiplier
            actual_cost *= uncertainty_multiplier

            financial_cost = FinancialCalculator.calculate_financial_cost(
                project, actual_delay
            )

            if financial_cost['rate_increase_bp'] > 0:
                FinancialCalculator.update_project_interest_rate(project, financial_cost)

            return {
                'issue_id': issue['id'],
                'issue_name': issue['name'],
                'delay_weeks': actual_delay,
                'cost_increase': actual_cost,
                'detected': False,
                'detection_phase': None,
                'bim_effectiveness': bim_effectiveness,
                'detection_probability': detection_prob,
                'financial_cost': financial_cost,
                'negotiation_summary': negotiation_result['negotiation_summary'],
                'early_detection': False  # 조기 탐지 실패
            }

    def _calculate_positive_impact(self, issue, project):
        """긍정적 이슈 영향 계산 (공기 단축, 비용 절감)"""
        # 긍정적 이슈는 BIM 사용 시에만 발생 (issue_manager에서 필터링됨)
        # delay_weeks_min/max는 음수값 (단축)
        # cost_increase_min/max는 음수값 (절감)

        delay_reduction = random.uniform(
            abs(issue['delay_weeks_min']),
            abs(issue['delay_weeks_max'])
        )
        cost_reduction = random.uniform(
            abs(issue['cost_increase_min']),
            abs(issue['cost_increase_max'])
        )

        # BIM 품질에 따라 효과 보정
        bim_effectiveness = BIMQuality.calculate_effectiveness(
            issue['id'],
            project.bim_quality
        )

        # BIM 품질이 높을수록 긍정적 효과 증대 (최대 20% 보너스)
        quality_bonus = 1.0 + (bim_effectiveness * 0.20)
        delay_reduction *= quality_bonus
        cost_reduction *= quality_bonus

        # 긍정적 영향은 음수로 반환 (공기 단축, 비용 절감)
        return {
            'issue_id': issue['id'],
            'issue_name': issue['name'],
            'delay_weeks': -delay_reduction,  # 음수 = 공기 단축
            'cost_increase': -cost_reduction,  # 음수 = 비용 절감
            'detected': True,  # 긍정적 이슈는 항상 "탐지됨"으로 간주
            'detection_phase': issue['bim_effect'].get('detection_phase'),
            'bim_effectiveness': bim_effectiveness,
            'detection_probability': 1.0,  # 긍정적 이슈는 100% 적용
            'financial_cost': {
                'financial_cost_increase': 0.0,
                'rate_increase_bp': 0,
                'reason': '긍정적 효과 - 금융비용 없음'
            },
            'negotiation_summary': f"긍정적 효과: {issue['name']} 적용",
            'early_detection': True,
            'is_positive': True,
            'savings': {
                'delay_avoided': delay_reduction,
                'cost_avoided': cost_reduction
            }
        }
