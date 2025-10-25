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
        """현재 단계에서 발생 가능한 이슈 확인"""
        current_phase = project.current_phase
        triggered = []

        # 시드 기반으로 동일한 난수 시퀀스 보장 (BIM ON/OFF 비교용)
        if self.random_seed is not None:
            # 현재 날짜를 기반으로 시드 재설정하여 각 날짜마다 동일한 난수 생성
            random.seed(self.random_seed + project.current_day)

        for issue in self.pending_issues[:]:
            if self._should_trigger(issue, project):
                triggered.append(issue)
                self.triggered_issues.append(issue)
                self.pending_issues.remove(issue)

        return triggered
    
    def _should_trigger(self, issue, project):
        """이슈 발생 여부 판단"""
        issue_phase = issue['phase']
        current_phase = project.current_phase

        if issue_phase != current_phase:
            return False

        occurrence_probability = self._get_occurrence_probability(issue)

        return random.random() < occurrence_probability

    def _get_occurrence_probability(self, issue):
        """
        이슈 발생 확률 계산 (개별 확률 사용)

        각 이슈마다 occurrence_rate (일별 발생 확률) 사용
        BIM 적용 여부와 관계없이 이슈는 동일하게 발생
        (BIM은 조기 탐지만 가능, 발생 자체는 막지 못함)
        """
        # 이슈별 기본 발생 확률 (일별)
        # BIM 여부와 무관하게 동일한 확률로 발생
        base_prob = issue.get('occurrence_rate', 0.01)  # 기본 1% / 일

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