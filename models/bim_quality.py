"""
BIM 품질 지표 계산
"""

import math
from config.bim_quality_config import BIMQualityConfig

class BIMQuality:
    """BIM 품질 지표 관리"""
    
    @staticmethod
    def normalize_metrics(bim_quality):
        """BIM 품질 지표 정규화 (0~1)"""
        normalized = {}
        
        if bim_quality['warning_density'] is not None:
            normalized['WD'] = max(0, min(1, 1 - bim_quality['warning_density'] / 20.0))
        else:
            normalized['WD'] = 0

        if bim_quality['clash_density'] is not None:
            normalized['CD'] = max(0, min(1, 1 - bim_quality['clash_density'] / 50.0))
        else:
            normalized['CD'] = 0
        
        normalized['AF'] = bim_quality['attribute_fill'] if bim_quality['attribute_fill'] else 0
        normalized['PL'] = bim_quality['phase_link'] if bim_quality['phase_link'] else 0
        
        return normalized
    
    @staticmethod
    def calculate_effectiveness(issue_id, bim_quality):
        """이슈별 BIM 효과성 계산"""
        weights = BIMQualityConfig.ISSUE_METRIC_WEIGHTS.get(
            issue_id, 
            BIMQualityConfig.DEFAULT_WEIGHTS
        )
        
        normalized = BIMQuality.normalize_metrics(bim_quality)
        
        effectiveness = sum(normalized[k] * weights[k] for k in weights)
        
        return max(0, min(1, effectiveness))
    
    @staticmethod
    def calculate_detection_probability(issue, bim_effectiveness):
        """탐지 확률 계산 (Sigmoid 함수)"""
        base_detectability = issue['bim_effect']['base_detectability']
        
        if base_detectability == 0:
            return 0.0
        
        # Sigmoid 함수 파라미터
        k = BIMQualityConfig.SIGMOID_K  # 기울기 (가파른 정도)
        x0 = BIMQualityConfig.SIGMOID_X0  # 변곡점 (중간값)

        # Sigmoid 함수: S자 곡선으로 0~1 사이 확률 반환
        sigmoid = 1 / (1 + math.exp(-k * (bim_effectiveness - x0)))
        
        detection_prob = base_detectability * sigmoid
        
        return min(BIMQualityConfig.MAX_DETECTION_PROB, detection_prob)
    
    @staticmethod
    def get_quality_score(bim_quality):
        """전체 BIM 품질 점수 (0~1)"""
        normalized = BIMQuality.normalize_metrics(bim_quality)
        
        score = (
            normalized['WD'] * 0.25 +
            normalized['CD'] * 0.30 +
            normalized['AF'] * 0.25 +
            normalized['PL'] * 0.20
        )
        
        return score
    
    @staticmethod
    def get_quality_level(bim_quality):
        """품질 등급 판정"""
        score = BIMQuality.get_quality_score(bim_quality)
        
        if score >= 0.85:
            return "우수"
        elif score >= 0.70:
            return "양호"
        elif score >= 0.50:
            return "보통"
        else:
            return "미흡"