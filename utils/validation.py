"""
결과 검증
"""

import json

class ResultValidator:
    """결과 검증기"""

    def __init__(self, benchmark_file='data/benchmark_data.json'):
        """벤치마크 데이터 로드"""
        try:
            with open(benchmark_file, 'r', encoding='utf-8') as f:
                self.benchmark = json.load(f)
        except FileNotFoundError:
            print(f"[Warning] 벤치마크 파일을 찾을 수 없습니다: {benchmark_file}")
            print("[Warning] 기본 벤치마크 값을 사용합니다.")
            self.benchmark = self._get_default_benchmark()
    
    def validate_results(self, metrics, scenario_type):
        """
        결과 검증
        
        Args:
            metrics: 시뮬레이션 결과 지표
            scenario_type: 'traditional' 또는 'bim'
        
        Returns:
            검증 결과 딕셔너리
        """
        validation_result = {
            'valid': True,
            'warnings': [],
            'details': {}
        }
        
        budget_overrun = metrics['budget_overrun_rate']
        schedule_delay = metrics['schedule_delay_rate']
        
        benchmark = self.benchmark['industry_average'][scenario_type]
        val_range = self.benchmark['validation_range']
        
        validation_result['details']['budget_overrun'] = self._validate_metric(
            budget_overrun,
            benchmark['budget_overrun'],
            val_range['budget_overrun_min'],
            val_range['budget_overrun_max'],
            '예산 초과율'
        )
        
        validation_result['details']['schedule_delay'] = self._validate_metric(
            schedule_delay,
            benchmark['schedule_delay'],
            val_range['schedule_delay_min'],
            val_range['schedule_delay_max'],
            '일정 지연률'
        )
        
        if not validation_result['details']['budget_overrun']['in_range']:
            validation_result['valid'] = False
            validation_result['warnings'].append(
                f"예산 초과율이 허용 범위를 벗어났습니다: {budget_overrun*100:.1f}%"
            )
        
        if not validation_result['details']['schedule_delay']['in_range']:
            validation_result['valid'] = False
            validation_result['warnings'].append(
                f"일정 지연률이 허용 범위를 벗어났습니다: {schedule_delay*100:.1f}%"
            )
        
        return validation_result
    
    def _validate_metric(self, actual, benchmark, min_val, max_val, metric_name):
        """개별 지표 검증"""
        in_range = min_val <= actual <= max_val
        deviation = abs(actual - benchmark) / benchmark * 100 if benchmark > 0 else 0
        
        return {
            'metric_name': metric_name,
            'actual': actual,
            'benchmark': benchmark,
            'min_allowed': min_val,
            'max_allowed': max_val,
            'in_range': in_range,
            'deviation_percent': deviation
        }
    
    def _get_default_benchmark(self):
        """기본 벤치마크 데이터 (파일 없을 시 사용)"""
        return {
            "industry_average": {
                "traditional": {
                    "budget_overrun": 0.22,
                    "schedule_delay": 0.23,
                    "rfi_count": 150,
                    "rework_rate": 0.12,
                    "description": "업계 평균 전통 방식 (기본값)"
                },
                "bim": {
                    "budget_overrun": 0.08,
                    "schedule_delay": 0.10,
                    "rfi_count": 60,
                    "rework_rate": 0.05,
                    "description": "업계 평균 BIM 적용 (기본값)"
                }
            },
            "validation_range": {
                "budget_overrun_min": 0.0,
                "budget_overrun_max": 0.50,
                "schedule_delay_min": 0.0,
                "schedule_delay_max": 0.50,
                "description": "허용 범위 확대 (연구용)"
            }
        }

    def print_validation_report(self, validation_result):
        """검증 보고서 출력"""
        print(f"\n{'='*60}")
        print("결과 검증 보고서")
        print(f"{'='*60}")
        
        print(f"\n전체 검증: {'통과' if validation_result['valid'] else '실패'}")
        
        for metric_key, detail in validation_result['details'].items():
            print(f"\n{detail['metric_name']}:")
            print(f"  실제값: {detail['actual']*100:.2f}%")
            print(f"  벤치마크: {detail['benchmark']*100:.2f}%")
            print(f"  허용 범위: {detail['min_allowed']*100:.2f}% ~ {detail['max_allowed']*100:.2f}%")
            print(f"  범위 내: {'예' if detail['in_range'] else '아니오'}")
            print(f"  편차: {detail['deviation_percent']:.1f}%")
        
        if validation_result['warnings']:
            print(f"\n경고:")
            for warning in validation_result['warnings']:
                print(f"  - {warning}")
        
        print(f"\n{'='*60}\n")

def validate_results(metrics, scenario_type):
    """결과 검증 함수 (편의 함수)"""
    validator = ResultValidator()
    return validator.validate_results(metrics, scenario_type)