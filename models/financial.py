"""
금융 비용 계산
"""

from config.project_config import ProjectConfig

class FinancialCalculator:
    """금융 비용 계산기"""
    
    @staticmethod
    def calculate_financial_cost(project, delay_weeks):
        """지연에 따른 금융 비용 계산"""
        delay_days = delay_weeks * 7
        delay_months = delay_days / 30
        
        loan_amount = project.budget * ProjectConfig.PF_RATIO
        base_rate = ProjectConfig.BASE_INTEREST_RATE
        
        rate_increase_bp = FinancialCalculator.get_rate_increase(delay_months)
        rate_increase = rate_increase_bp / 10000
        
        additional_interest = loan_amount * rate_increase * (delay_days / 365)
        
        daily_indirect = project.budget * ProjectConfig.DAILY_INDIRECT_COST_RATIO
        additional_indirect = daily_indirect * delay_days
        
        total_financial_cost = additional_interest + additional_indirect
        
        new_rate = base_rate + rate_increase
        
        return {
            'interest_increase': additional_interest,
            'indirect_cost': additional_indirect,
            'total_financial_cost': total_financial_cost,
            'rate_increase_bp': rate_increase_bp,
            'new_interest_rate': new_rate,
            'delay_months': delay_months
        }
    
    @staticmethod
    def get_rate_increase(delay_months):
        """
        지연 개월수에 따른 금리 인상 (bp)
        연속적인 보간으로 개선 (2.5개월 등 실수 값 반영)
        """
        if delay_months < 1:
            return 0
        elif delay_months < 2:
            # 1~2개월: 0bp (유예기간)
            return 0
        elif delay_months < 4:
            # 2~4개월: 0 → 20bp (선형 증가)
            return int((delay_months - 2) / 2 * 20)
        elif delay_months < 7:
            # 4~7개월: 20 → 50bp (선형 증가)
            return int(20 + (delay_months - 4) / 3 * 30)
        else:
            # 7개월 이상: 50 → 100bp (선형 증가, 최대 100bp)
            return min(100, int(50 + (delay_months - 7) / 3 * 50))
    
    @staticmethod
    def update_project_interest_rate(project, financial_result):
        """프로젝트 금리 업데이트"""
        if financial_result['rate_increase_bp'] > 0:
            project.current_interest_rate = financial_result['new_interest_rate']
            project.interest_rate_increases.append({
                'day': project.current_day,
                'delay_months': financial_result['delay_months'],
                'increase_bp': financial_result['rate_increase_bp'],
                'new_rate': financial_result['new_interest_rate']
            })