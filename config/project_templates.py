"""
다양한 프로젝트 유형 템플릿
"""


class ProjectTemplates:
    """프로젝트 유형별 템플릿"""

    # 1. 청담동 근린생활시설 (기본값)
    CHEONGDAM_COMMERCIAL = {
        'name': '청담동 근린생활시설 신축공사',
        'location': '서울특별시 강남구 청담동 2-2',
        'building_type': '근린생활시설',
        'gfa': 883.5,  # ㎡
        'budget': 2_030_000_000,  # 원
        'duration': 360,  # 일
        'phase_durations': {
            '설계': 90,
            '입찰': 20,
            '시공': 300,
            '준공': 20
        },
        'pf_ratio': 0.7,
        'base_interest_rate': 0.055
    }

    @classmethod
    def get_template(cls, template_name):
        """템플릿 반환"""
        templates = {
            'cheongdam': cls.CHEONGDAM_COMMERCIAL
        }
        return templates.get(template_name, cls.CHEONGDAM_COMMERCIAL)

    @classmethod
    def list_templates(cls):
        """사용 가능한 템플릿 목록"""
        return {
            'cheongdam': '청담동 근린생활시설 (883㎡, 20.3억, 12개월)'
        }

    @classmethod
    def print_template_info(cls, template_name):
        """템플릿 정보 출력"""
        template = cls.get_template(template_name)
        print(f"\n{'='*70}")
        print(f"프로젝트 템플릿: {template['name']}")
        print(f"{'='*70}")
        print(f"위치: {template['location']}")
        print(f"건물 유형: {template['building_type']}")
        print(f"연면적: {template['gfa']:,}㎡")
        print(f"예산: {template['budget']:,}원 ({template['budget']/1e8:.1f}억)")
        print(f"공기: {template['duration']}일 ({template['duration']//30}개월)")
        print(f"PF 비율: {template['pf_ratio']*100:.0f}%")
        print(f"기본 금리: {template['base_interest_rate']*100:.2f}%")
        print(f"{'='*70}\n")
