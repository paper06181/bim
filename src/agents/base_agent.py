"""
에이전트 베이스 클래스
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseAgent(ABC):
    """에이전트 기본 클래스"""

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role

    @abstractmethod
    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        """시스템 프롬프트 생성"""
        pass

    @abstractmethod
    def report_issue(self, issue: Dict, context: Dict) -> str:
        """이슈 보고"""
        pass

    @abstractmethod
    def give_opinion(self, issue: Dict, context: Dict, other_opinions: Dict = None) -> Dict:
        """이슈에 대한 의견"""
        pass

    @abstractmethod
    def propose_solution(self, issue: Dict, severity: Dict, context: Dict) -> Dict:
        """해결 방안 제안"""
        pass

    def _format_context(self, context: Dict) -> str:
        """컨텍스트를 문자열로 포맷팅"""
        lines = []
        for key, value in context.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for k, v in value.items():
                    lines.append(f"  - {k}: {v}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)
