"""
5명 멀티 에이전트 회의 시스템
- 기존 5명 에이전트를 활용하되, resolution_level 결정에 집중
- JSON 형식으로 간결한 출력
- LLM 기반 의사결정
"""
import json
import os
from typing import List, Dict, Optional
from data.data_models import IssueCard, ProjectInfo, Case
from agents.owner_agent import OwnerAgent
from agents.designer_agent import DesignerAgent
from agents.contractor_agent import ContractorAgent
from agents.supervisor_agent import SupervisorAgent
from agents.bank_agent import BankAgent


class AgentMeetingSystem:
    """5명 에이전트 회의 시스템"""

    def __init__(self, use_llm: bool = True):
        """
        Args:
            use_llm: LLM 사용 여부 (False면 간단한 규칙 기반)
        """
        self.use_llm = use_llm
        self.agents = {
            'owner': OwnerAgent(use_llm=use_llm),
            'designer': DesignerAgent(use_llm=use_llm),
            'contractor': ContractorAgent(use_llm=use_llm),
            'supervisor': SupervisorAgent(use_llm=use_llm),
            'bank': BankAgent(use_llm=use_llm)
        }

    def conduct_meeting(self,
                        project: ProjectInfo,
                        issues: List[IssueCard],
                        segment: str,
                        family: str) -> Dict[str, float]:
        """
        이슈들에 대한 회의를 진행하고 resolution_level을 결정

        Args:
            project: 프로젝트 정보
            issues: 평가할 이슈 리스트
            segment: 공정률 구간 (예: "0-25", "25-75")
            family: "BIM" 또는 "TRAD"

        Returns:
            {issue_id: resolution_level} 딕셔너리
        """
        if not issues:
            return {}

        if self.use_llm:
            return self._conduct_llm_meeting(project, issues, segment, family)
        else:
            return self._conduct_rule_based_meeting(issues)

    def _conduct_llm_meeting(self,
                              project: ProjectInfo,
                              issues: List[IssueCard],
                              segment: str,
                              family: str) -> Dict[str, float]:
        """
        LLM 기반 회의 진행

        5명의 에이전트가 토론하여 각 이슈의 resolution_level을 결정
        이슈가 많을 경우 배치로 나눠서 처리
        """
        # 프롬프트 구성
        system_prompt = self._build_system_prompt(project, segment, family)

        # 이슈를 배치로 나눔 (한번에 15개씩 처리)
        BATCH_SIZE = 15
        all_resolutions = {}

        for i in range(0, len(issues), BATCH_SIZE):
            batch = issues[i:i+BATCH_SIZE]
            user_prompt = self._build_user_prompt(batch)

            # LLM 호출
            try:
                llm_response = self.agents['owner']._generate_llm_response(system_prompt, user_prompt)
                batch_resolutions = self._parse_llm_response(llm_response, batch)
                all_resolutions.update(batch_resolutions)
            except Exception as e:
                print(f"[경고] LLM 배치 {i//BATCH_SIZE + 1} 호출 실패, 규칙 기반으로 fallback: {e}")
                batch_resolutions = self._conduct_rule_based_meeting(batch)
                all_resolutions.update(batch_resolutions)

        return all_resolutions

    def _build_system_prompt(self, project: ProjectInfo, segment: str, family: str) -> str:
        """
        시스템 프롬프트 생성
        """
        family_desc = "BIM을 적용한" if family == "BIM" else "전통 방식(BIM 미적용)"

        prompt = f"""당신은 건설 프로젝트의 리스크 관리 회의를 주관하는 프로젝트 매니저입니다.

[프로젝트 정보]
- 프로젝트명: {project.project_name}
- 총 공기: {project.duration_days}일
- 기준 공사비: {project.base_cost:,.0f}원
- CASE: {project.case.case_id} (등급: {project.case.kpi_grade})
- 방식: {family_desc}
- 현재 공정률 구간: {segment}

[회의 참석자]
1. 건축주 (발주자): 예산과 일정에 민감, 투자 수익 극대화 목표
2. 설계사: 설계 품질과 기술적 해결에 집중
3. 시공사: 현장 실행 가능성과 공정 준수에 집중
4. 감리사: 품질 관리와 규정 준수에 집중
5. 금융사: 재무 건전성과 리스크 완화에 집중

[당신의 임무]
오늘 발생한 여러 이슈들을 **종합적으로 판단**하여, 각 이슈별로 **대응 수준(resolution_level)**을 결정하세요.
- 5명의 에이전트(건축주, 설계사, 시공사, 감리사, 금융사)가 토론한다고 가정
- **이슈 간 우선순위**를 고려하여 자원을 효율적으로 배분
- **여러 이슈가 동시 발생**했을 때 어떤 이슈에 집중할지 판단

[대응 수준 기준]
- **1.0 (적극 대응)**: 최우선 처리 필요. 심각도 S3이거나 프로젝트 전체에 큰 영향
  - 예: 구조 안전 문제, 법적 규제 위반, 공기 지연 10주 이상 예상
- **0.5 (일반 대응)**: 중요하지만 자원 제약으로 적정 수준 대응
  - 예: 심각도 S2, 공기 지연 3~10주, 비용 증가 5~15%
- **0.0 (최소 대응)**: 현재는 우선순위 낮음. 다른 이슈에 자원 집중
  - 예: 심각도 S1, 경미한 영향, 나중에 처리 가능

[종합 판단 기준]
1. **우선순위**: 심각도가 높고 영향이 큰 이슈부터 처리
2. **자원 제약**: 모든 이슈에 1.0을 줄 수 없음. 선택과 집중 필요
3. **연쇄 효과**: 한 이슈가 다른 이슈를 유발할 수 있는지 고려
4. **현재 공정률**: 공정률 {segment}에서 처리하기 적절한 이슈인지
5. **{family_desc} 환경**: BIM 사용 시 일부 이슈는 자동 탐지/해결 가능

**중요**: 여러 이슈가 동시 발생했을 때, 자원을 효율적으로 배분하세요.
예를 들어, 5개 이슈 중 2개는 1.0, 2개는 0.5, 1개는 0.0으로 차등 배분하는 것이 바람직합니다.

**반드시 유효한 JSON 형식으로만 출력하세요. 다른 설명이나 주석은 불필요합니다.**
**reason 필드는 생략하고 id와 resolution_level만 출력하세요.**

출력 형식:
{{
  "segment": "{segment}",
  "issues": [
    {{"id": "I-01", "resolution_level": 1.0}},
    {{"id": "I-02", "resolution_level": 0.5}},
    {{"id": "I-03", "resolution_level": 0.0}}
  ]
}}
"""
        return prompt

    def _build_user_prompt(self, issues: List[IssueCard]) -> str:
        """
        사용자 프롬프트 생성 (이슈 리스트)
        """
        lines = ["다음 이슈들에 대해 대응 수준을 결정해주세요:\n"]

        for idx, issue in enumerate(issues, 1):
            lines.append(f"{idx}. ID: {issue.issue_id}")
            lines.append(f"   이슈명: {issue.name}")
            lines.append(f"   심각도: {issue.severity}")
            lines.append(f"   카테고리: {issue.category}")
            lines.append(f"   지연: {issue.delay_min_weeks}~{issue.delay_max_weeks}주")
            lines.append(f"   비용증가: {issue.cost_min_pct}~{issue.cost_max_pct}%")
            lines.append(f"   기본 리스크 점수: {issue.base_risk:.3f}")
            lines.append("")

        return "\n".join(lines)

    def _parse_llm_response(self, llm_response: str, issues: List[IssueCard]) -> Dict[str, float]:
        """
        LLM 응답 파싱 (JSON 추출)
        """
        # JSON 블록 찾기
        try:
            # ```json ... ``` 블록 추출
            if "```json" in llm_response:
                start = llm_response.find("```json") + 7
                end = llm_response.find("```", start)
                json_str = llm_response[start:end].strip()
            elif "```" in llm_response:
                start = llm_response.find("```") + 3
                end = llm_response.find("```", start)
                json_str = llm_response[start:end].strip()
            else:
                # JSON 블록 없으면 전체를 JSON으로 시도
                json_str = llm_response.strip()

            # UTF-8 인코딩 보장 (한글 처리)
            json_str = json_str.encode('utf-8', errors='ignore').decode('utf-8')

            # JSON 파싱 시도 (strict=False로 느슨하게)
            data = json.loads(json_str, strict=False)
            resolutions = {}

            for item in data.get("issues", []):
                issue_id = item.get("id")
                resolution_level = item.get("resolution_level", 0.5)

                # 검증: 0, 0.5, 1.0만 허용
                if resolution_level not in [0.0, 0.5, 1.0]:
                    resolution_level = 0.5

                resolutions[issue_id] = resolution_level

            # 누락된 이슈는 0.5로 기본값
            for issue in issues:
                if issue.issue_id not in resolutions:
                    resolutions[issue.issue_id] = 0.5

            return resolutions

        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"[경고] JSON 파싱 실패: {e}")
            print(f"[디버그] JSON 문자열 (처음 1000자):")
            print(json_str[:1000] if 'json_str' in locals() else "N/A")
            print(f"[경고] Fallback - 규칙 기반 회의로 전환")
            return self._conduct_rule_based_meeting(issues)

    def _conduct_rule_based_meeting(self, issues: List[IssueCard]) -> Dict[str, float]:
        """
        규칙 기반 회의 (LLM 없이)

        개선된 휴리스틱:
        - 심각도(Severity)와 기본 리스크(base_risk)를 종합 평가
        - 카테고리별 중요도 고려
        - 더 세분화된 resolution_level 결정
        """
        resolutions = {}

        # 카테고리별 중요도 가중치
        critical_categories = ["설계", "시공", "안전", "구조"]

        for issue in issues:
            base_risk = issue.base_risk
            severity = issue.severity
            category = getattr(issue, 'category', '')

            # 카테고리 중요도 보너스
            category_bonus = 0.1 if any(cat in category for cat in critical_categories) else 0.0

            # 조정된 리스크 점수
            adjusted_risk = base_risk + category_bonus

            # Resolution level 결정 (더 세분화)
            if severity == "S3":
                # S3 (심각) - 높은 대응
                if adjusted_risk >= 0.5:
                    level = 1.0  # 적극 대응
                elif adjusted_risk >= 0.35:
                    level = 0.5  # 중간 대응
                else:
                    level = 0.5  # 기본 대응
            elif severity == "S2":
                # S2 (중간) - 중간 대응
                if adjusted_risk >= 0.45:
                    level = 1.0  # 높은 리스크는 적극 대응
                elif adjusted_risk >= 0.30:
                    level = 0.5  # 중간 대응
                else:
                    level = 0.5  # 기본 대응
            else:  # S1
                # S1 (경미) - 선택적 대응
                if adjusted_risk >= 0.40:
                    level = 0.5  # 중간 대응
                elif adjusted_risk >= 0.25:
                    level = 0.5  # 최소 대응
                else:
                    level = 0.0  # 대응 불필요

            resolutions[issue.issue_id] = level

        return resolutions


def test_meeting_system():
    """테스트 함수"""
    from data.excel_loader import get_loader
    from data.data_models import ProjectInfo

    print("=" * 80)
    print("에이전트 회의 시스템 테스트")
    print("=" * 80)

    # 데이터 로드
    loader = get_loader()

    # CASE 로드
    case = loader.load_case_from_matrix("도심", "상업지역", "중심상업지역", 800)
    print(f"\nCASE: {case}")

    # 프로젝트 정보
    project = ProjectInfo(
        project_name="테스트 프로젝트",
        duration_days=365,
        base_cost=5_000_000_000,
        case=case
    )

    # 이슈 로드 (BIM)
    issues = loader.load_issue_cards("BIM")
    print(f"총 이슈 수: {len(issues)}")

    # 첫 5개 이슈만 테스트
    test_issues = issues[:5]
    for issue in test_issues:
        from engine.risk_calculator import RiskCalculator
        calc = RiskCalculator()
        issue.base_risk = calc.compute_base_risk(issue, case.kpi_bim.values)

    # 회의 시스템 (LLM 없이 먼저 테스트)
    meeting_system = AgentMeetingSystem(use_llm=False)
    resolutions = meeting_system.conduct_meeting(project, test_issues, "0-25", "BIM")

    print("\n[회의 결과]")
    for issue_id, level in resolutions.items():
        issue = next(i for i in test_issues if i.issue_id == issue_id)
        print(f"  {issue_id}: {level:.1f} - {issue.name[:40]}")

    print("\n테스트 완료!")


if __name__ == "__main__":
    test_meeting_system()
