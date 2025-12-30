"""
이슈 발생 및 관리
"""

import json
import random
from config.project_config import ProjectConfig

class IssueManager:
    """이슈 카드 관리"""

    def __init__(self, issue_file='data/issue_cards.json', random_seed=None):
        """이슈 카드 로드

        Args:
            issue_file: 이슈 카드 JSON 파일 경로
            random_seed: 랜덤 시드 (비교 시뮬레이션 시 동일한 이슈 발생 보장)
        """
        with open(issue_file, 'r', encoding='utf-8') as f:
            self.all_issues = json.load(f)

        self.triggered_issues = []
        self.pending_issues = self.all_issues.copy()
        self.random_seed = random_seed
    
    def check_and_trigger_issues(self, project):
        """현재 단계에서 발생 가능한 이슈 확인 (origin_phase 기반)"""
        current_phase = project.current_phase
        triggered = []

        # 시드 기반으로 동일한 난수 시퀀스 보장 (BIM ON/OFF 비교용)
        if self.random_seed is not None:
            # 현재 날짜를 기반으로 시드 재설정하여 각 날짜마다 동일한 난수 생성
            random.seed(self.random_seed + project.current_day)

        for issue in self.pending_issues[:]:
            # origin_phase에서 이슈 발생 (원인이 만들어지는 시점)
            if self._should_trigger(issue, project):
                triggered.append(issue)
                self.triggered_issues.append(issue)
                self.pending_issues.remove(issue)

        return triggered
    
    def _should_trigger(self, issue, project):
        """이슈 발생 여부 판단 (origin_phase 기반)"""
        # origin_phase에서 이슈가 발생 (근본 원인이 만들어지는 시점)
        origin_phase = issue.get('origin_phase', issue['phase'])
        current_phase = project.current_phase

        # 현재 단계가 origin_phase와 일치할 때만 발생 가능
        if origin_phase != current_phase:
            return False

        occurrence_probability = self._get_occurrence_probability(issue, project)

        return random.random() < occurrence_probability

    def _get_occurrence_probability(self, issue, project=None):
        """
        이슈 발생 확률 계산 (개별 확률 사용)

        각 이슈마다 occurrence_rate (일별 발생 확률) 사용
        - 부정적 이슈: BIM prevention_effect로 발생 확률 감소 가능
        - 긍정적 이슈: BIM 사용 시 occurrence_rate가 적용 확률 (BIM OFF는 0)
        """
        base_prob = issue.get('occurrence_rate', 0.01)
        is_positive = issue.get('is_positive', False)

        # 긍정적 이슈는 BIM 사용 시에만 발생
        if is_positive:
            if project and project.bim_enabled:
                return min(1.0, base_prob)
            else:
                return 0.0  # BIM OFF일 때 긍정적 이슈는 발생하지 않음

        # 부정적 이슈: BIM prevention_effect로 발생 확률 감소
        if project and project.bim_enabled:
            prevention_effect = issue.get('bim_effect', {}).get('prevention_effect', 0.0)
            # prevention_effect만큼 발생 확률 감소
            adjusted_prob = base_prob * (1 - prevention_effect)
            return min(1.0, adjusted_prob)

        return min(1.0, base_prob)
    
    def get_issue_by_id(self, issue_id):
        """ID로 이슈 찾기"""
        for issue in self.all_issues:
            if issue['id'] == issue_id:
                return issue
        return None
    
    def get_issues_by_category(self, category):
        """카테고리별 이슈 조회"""
        return [i for i in self.all_issues if i['category'] == category]
    
    def get_remaining_count(self):
        """남은 이슈 수"""
        return len(self.pending_issues)
    
    def get_triggered_count(self):
        """발생한 이슈 수"""
        return len(self.triggered_issues)

    def filter_issues_by_building_type(self, building_config):
        """
        건축물 특성에 따라 이슈 필터링

        Args:
            building_config: dict with keys: height, location, purpose, scale
        """
        filtered_issues = []

        for issue in self.all_issues:
            filters = issue.get('building_type_filters', {})

            # 필터가 없으면 모든 건축물에 적용
            if not filters:
                filtered_issues.append(issue)
                continue

            # 모든 조건이 매치되어야 함
            match = True
            for key, value in building_config.items():
                if key in filters:
                    if value not in filters[key]:
                        match = False
                        break

            if match:
                filtered_issues.append(issue)

        return filtered_issues

    def get_positive_issues(self):
        """긍정적 이슈만 반환"""
        return [i for i in self.all_issues if i.get('is_positive', False)]

    def get_negative_issues(self):
        """부정적 이슈만 반환"""
        return [i for i in self.all_issues if not i.get('is_positive', False)]