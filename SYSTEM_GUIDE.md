# 건설 시뮬레이션 시스템 완전 가이드


1. [5단계로 이해하는 전체 흐름](#1-5단계로-이해하는-전체-흐름)
2. [1단계: 프로젝트 정보 입력](#2-1단계-프로젝트-정보-입력)
3. [2단계: 케이스 결정 및 KPI 할당](#3-2단계-케이스-결정-및-kpi-할당)
4. [3단계: 매일 이슈 체크](#4-3단계-매일-이슈-체크)
5. [4단계: GPT 회의 진행](#5-4단계-gpt-회의-진행)
6. [5단계: 결과 저장 및 비교](#6-5단계-결과-저장-및-비교)
7. [코드 구조 및 주요 파일](#7-코드-구조-및-주요-파일)
8. [문제 해결 가이드](#8-문제-해결-가이드)

---

## 1. 5단계로 이해하는 전체 흐름

### 전체 과정 요약

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 1단계: 프로젝트 정보 입력
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
project_config.json 파일 읽기
→ 위치, 용적률, 연면적, 예산, 공기 등

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 2단계: 케이스 결정 및 KPI 할당
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
위치 × 용적률 → 케이스 (A/B/C/D)
케이스 → KPI 값 자동 할당
  BIM: WD/CD/AF/PL
  전통: RR/SR/CR/FC

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 3단계: 매일 이슈 체크 (Day 1 → Day 360)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3-1. 오늘 발생 가능한 이슈 필터링 (공정률 기준)
3-2. KPI 기반 확률 계산
3-3. 랜덤 추첨으로 이슈 발생 여부 결정
3-4. 진행 중인 이슈 진행률 업데이트

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 4단계: GPT 회의 진행 (신규 또는 진행 중 이슈가 있을 때)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4-1. 건축주 GPT 의견 수렴 (자원 경쟁, 착수 시점 분석)
4-2. 시공사 GPT 의견 수렴 (공간 간섭, 작업 순서 분석)
4-3. 심각도 평가 (지연 주수, 비용 증가율 계산)
4-4. 해결 방안 제안 (정상 공정 vs 인력 증투)
4-5. 건축주 최종 선택
4-6. 지연/비용 누적

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 5단계: 결과 저장 및 비교
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BIM 방식 완료 → 전통 방식 실행 → 비교 분석
logs/ : 전체 회의 로그, 이슈 목록 저장
results/ : 비교 리포트 저장
```

---

## 2. 1단계: 프로젝트 정보 입력

### 어떤 파일을 읽나?

**`project_config.json`** 파일을 읽습니다.

```json
{
  "프로젝트명": "청담동 근린생활시설 신축공사",
  "위치": "서울특별시 강남구 청담동 2-2",
  "location": "도심",
  "용도": "근린생활시설",
  "building_type": "상업",
  "연면적_제곱미터": 883.5,
  "연면적_평": 267.23,
  "총공사비_억원": 20.3,
  "계획공기_개월": 12,
  "계획공기_일수": 360,
  "용적률": 80,
  "ground_roughness": "C"
}
```

### 어떤 정보가 필요한가?

시뮬레이션에 **필수로 필요한 정보**:

| 항목 | 의미 | 예시 |
|------|------|------|
| **location** | 위치 (도심/외곽) | "도심" |
| **용적률** | 용적률 (%) | 80 |
| **연면적_제곱미터** | 건물 크기 | 883.5 |
| **총공사비_억원** | 예산 | 20.3 |
| **계획공기_일수** | 목표 공기 | 360일 |
| **building_type** | 용도 | "상업" |
| **ground_roughness** | 지형 | "C" |

### 코드는 어디에?

**파일**: `main.py` → `load_project_config()` 함수

```python
def load_project_config():
    config_file = Path(__file__).parent / "project_config.json"

    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    project_info = {
        "location": config["location"],
        "floor_area_ratio": config["용적률"],
        "total_area": config["연면적_제곱미터"],
        "total_budget": config["총공사비_억원"],
        "planned_duration_days": config["계획공기_일수"],
        "building_type": config.get("building_type", "상업"),
        "ground_roughness": config.get("ground_roughness", "C"),
    }

    return project_info
```

---

## 3. 2단계: 케이스 결정 및 KPI 할당

### 케이스란 무엇인가?

프로젝트의 **복잡도 등급**을 A, B, C, D 4단계로 나눈 것입니다.

- **케이스 A**: 도심 고밀도 → 가장 위험 높음
- **케이스 B**: 도심 중밀도 또는 외곽 고밀도
- **케이스 C**: 도심 저밀도 또는 외곽 중밀도
- **케이스 D**: 외곽 저밀도 → 가장 위험 낮음

### 케이스는 어떻게 결정되나?

**입력**: 위치 (도심/외곽) + 용적률 (%)
**출력**: 케이스 (A/B/C/D)

**파일**: `src/config/case_mapping.py` → `determine_case()` 함수

```python
def determine_case(location: str, floor_area_ratio: int) -> str:
    if location == "도심":
        if floor_area_ratio >= 80:
            return "A"  # 도심 고밀도
        elif floor_area_ratio >= 60:
            return "B"  # 도심 중밀도
        else:
            return "C"  # 도심 저밀도

    elif location == "외곽":
        if floor_area_ratio >= 70:
            return "B"  # 외곽 고밀도
        elif floor_area_ratio >= 50:
            return "C"  # 외곽 중밀도
        else:
            return "D"  # 외곽 저밀도
```

**청담동 프로젝트 예시**:
```
location = "도심"
floor_area_ratio = 80

→ 케이스 A (도심 고밀도)
```

### KPI란 무엇인가?

**KPI (Key Performance Indicator)**: 프로젝트의 위험도를 측정하는 **핵심 지표**

#### BIM 방식 KPI (4개)

| KPI | 이름 | 의미 | 값이 크면? |
|-----|------|------|-----------|
| **WD** | 경고밀도 | BIM 모델의 경고 개수/㎡ | 위험 ↑ |
| **CD** | 충돌밀도 | 간섭 탐지 개수/㎡ | 위험 ↑ |
| **AF** | 속성 채움률 | 속성 정보 완성도(%) | 위험 ↓ |
| **PL** | 공정 연계도 | 공정 연계 비율(%) | 위험 ↓ |

#### 전통 방식 KPI (4개)

| KPI | 이름 | 의미 | 값이 크면? |
|-----|------|------|-----------|
| **RR** | 재시공률 | 재작업 비율(%) | 위험 ↑ |
| **SR** | 안전사고 발생률 | 사고 건수/100명 | 위험 ↑ |
| **CR** | 공정 지연률 | 지연 비율(%) | 위험 ↑ |
| **FC** | 설계 변경 빈도 | 변경 건수/월 | 위험 ↑ |

### KPI 값은 어떻게 할당되나?

**케이스에 따라 자동으로** 할당됩니다.

**파일**: `src/config/case_mapping.py` → `get_kpi_values()` 함수

```python
BIM_KPI_VALUES = {
    "A": {"WD": 0.5,  "CD": 0.17, "AF": 24.75, "PL": 13.2},
    "B": {"WD": 0.33, "CD": 0.11, "AF": 16.5,  "PL": 8.8},
    "C": {"WD": 0.23, "CD": 0.08, "AF": 11.25, "PL": 6.0},
    "D": {"WD": 0.15, "CD": 0.05, "AF": 7.5,   "PL": 4.0},
}

TRADITIONAL_KPI_VALUES = {
    "A": {"RR": 0.2,  "SR": 0.54, "CR": 2.48, "FC": 1.32},
    "B": {"RR": 0.13, "SR": 0.36, "CR": 1.65, "FC": 0.88},
    "C": {"RR": 0.09, "SR": 0.25, "CR": 1.13, "FC": 0.6},
    "D": {"RR": 0.06, "SR": 0.17, "CR": 0.75, "FC": 0.4},
}

def get_kpi_values(case: str, method: str) -> dict:
    if method == "BIM":
        return BIM_KPI_VALUES[case].copy()
    elif method == "TRADITIONAL":
        return TRADITIONAL_KPI_VALUES[case].copy()
```

**청담동 프로젝트 (케이스 A)의 KPI**:
```
BIM 방식:
  WD = 0.5
  CD = 0.17
  AF = 24.75
  PL = 13.2

전통 방식:
  RR = 0.2
  SR = 0.54
  CR = 2.48
  FC = 1.32
```

**⚠️ 중요**: 이 KPI 값들은 실제 엑셀 데이터에서 추출한 것으로, **절대로 임의로 변경하면 안 됩니다!**

### 어디서 실행되나?

**파일**: `src/core/simulation_engine.py` → `__init__()` 함수

```python
class ConstructionSimulation:
    def __init__(self, project_info: Dict, method: str = "BIM"):
        # 1. 케이스 결정
        case = determine_case(
            project_info["location"],
            project_info["floor_area_ratio"]
        )

        # 2. KPI 할당
        kpi_values = get_kpi_values(case, method)

        # 3. ProjectContext 생성
        self.context = ProjectContext(
            location=project_info["location"],
            floor_area_ratio=project_info["floor_area_ratio"],
            ...
            case=case,
            kpi_values=kpi_values,
        )
```

---

## 4. 3단계: 매일 이슈 체크

### 매일 무엇을 하나?

**360일 동안 매일 반복**:

```python
for day in range(1, 361):  # 1일 ~ 360일
    # 3-1. 오늘 발생 가능한 이슈 필터링
    # 3-2. KPI 기반 확률 계산
    # 3-3. 랜덤 추첨으로 발생 여부 결정
    # 3-4. 진행 중인 이슈 진행률 업데이트
    # 3-5. 회의 진행 (신규 또는 진행 중 이슈가 있으면)
```

### 3-1. 오늘 발생 가능한 이슈 필터링

**왜 필터링하나?**
이슈마다 **발생 가능한 공정률 범위**가 정해져 있습니다.

예시:
- "설계 변경 요청" → 공정률 0~25% (설계 단계)
- "현장 착오 시공" → 공정률 25~75% (시공 단계)
- "준공 검사 지적" → 공정률 75~100% (마감 단계)

**파일**: `src/data/issue_cards.py` → `filter_issues_by_progress()` 함수

```python
def filter_issues_by_progress(issues: List[Dict], progress_rate: float) -> List[Dict]:
    filtered = []
    progress_pct = progress_rate * 100  # 0.35 → 35%

    for issue in issues:
        range_str = issue["공정률"]  # "25-75"
        min_p, max_p = map(int, range_str.split("-"))

        if min_p <= progress_pct <= max_p:
            filtered.append(issue)

    return filtered
```

**예시**:
```
Day 126 → 공정률 35% (126/360)

"0-25" 범위 이슈: ❌ 제외 (이미 지나감)
"25-75" 범위 이슈: ✅ 포함
"75-100" 범위 이슈: ❌ 제외 (아직 안 됨)
```

### 3-2. KPI 기반 확률 계산

**이슈마다 기본 발생확률이 있습니다**:
```json
{
  "ID": "B006",
  "이슈명": "현장 착오 시공",
  "발생확률(%)": 18,
  "가중치": {
    "WD": 0.3,
    "CD": 0.4,
    "AF": 0.2,
    "PL": 0.1
  }
}
```

**KPI 값을 이용해서 최종 확률을 계산합니다**.

**파일**: `src/core/probability_calculator.py` → `calculate_issue_probability()` 함수

#### Step 1: KPI 정규화 (0~1 범위로)

```python
# WD (경고밀도) - 낮을수록 좋음
WD 실제값 = 0.5
WD 최대값 = 0.5
normalized_WD = min(0.5 / 0.5, 1.0) = 1.0  # 매우 위험

# CD (충돌밀도) - 낮을수록 좋음
CD 실제값 = 0.17
CD 최대값 = 0.3
normalized_CD = min(0.17 / 0.3, 1.0) = 0.567  # 중간 위험

# AF (속성 채움률) - 높을수록 좋음 (역전 지표)
AF 실제값 = 24.75
AF 최대값 = 30.0
normalized_AF = min(24.75 / 30.0, 1.0) = 0.825
→ 1.0 - 0.825 = 0.175  # 역전 (높으면 안전)

# PL (공정 연계도) - 높을수록 좋음 (역전 지표)
PL 실제값 = 13.2
PL 최대값 = 15.0
normalized_PL = min(13.2 / 15.0, 1.0) = 0.88
→ 1.0 - 0.88 = 0.12  # 역전
```

#### Step 2: 가중치 적용

```python
가중치: WD=0.3, CD=0.4, AF=0.2, PL=0.1

WD 기여 = 1.0 × 0.3 = 0.3
CD 기여 = 0.567 × 0.4 = 0.227
AF 기여 = 0.175 × 0.2 = 0.035
PL 기여 = 0.12 × 0.1 = 0.012

total_risk = (0.3 + 0.227 + 0.035 + 0.012) / (0.3 + 0.4 + 0.2 + 0.1)
           = 0.574 / 1.0
           = 0.574
```

#### Step 3: 최종 확률 계산

```python
기본 확률 = 18% = 0.18

multiplier = 1.0 + (total_risk - 0.5) × 0.8
           = 1.0 + (0.574 - 0.5) × 0.8
           = 1.0 + 0.059
           = 1.059

# 전통 방식이면 × 1.2 추가 (위험 증폭)
if method == "TRADITIONAL":
    multiplier *= 1.2

final_prob = 0.18 × 1.059 = 0.191 (19.1%)

# 최소 1%, 최대 95%로 제한
final_prob = max(0.01, min(0.95, final_prob))
```

**결과**: 기본 18% → 최종 19.1%

### 3-3. 랜덤 추첨으로 발생 여부 결정

**파일**: `src/core/simulation_engine.py` → `check_issue_occurrence()` 함수

```python
for issue in candidate_issues:
    # 확률 계산
    prob = calculate_issue_probability(issue, kpi_values, method)

    # 랜덤 추첨
    if random.random() < prob:
        occurred.append(issue)  # 발생!
```

**예시**:
```
최종 확률 = 19.1%
random.random() = 0.15  # 0~1 사이 랜덤
0.15 < 0.191 → True → 발생!
```

### 3-4. 진행 중인 이슈 진행률 업데이트

**이미 발생한 이슈들은 매일 진행률이 올라갑니다**.

**파일**: `src/core/issue_manager.py` → `update_all_issues()` 함수

```python
for issue in self.active_issues:
    # 일일 증가량 = 100 / (해결 주수 × 7일)
    daily_increment = 100 / (issue.time_weeks * 7)

    issue.progress += daily_increment

    if issue.progress >= 100:
        issue.progress = 100
        issue.status = "해결완료"
```

**예시**:
```
이슈: "현장 착오 시공"
해결 주수: 2.5주 = 17.5일
일일 증가량: 100 / 17.5 = 5.71%

Day 1: 5.71%
Day 2: 11.42%
Day 3: 17.13%
...
Day 18: 100% → 해결완료!
```

---

## 5. 4단계: GPT 회의 진행

### 언제 회의를 하나?

1. **신규 이슈가 발생했을 때**
2. **진행 중인 이슈가 있을 때**

**파일**: `src/core/simulation_engine.py` → `run_simulation()` 함수

```python
active_issues = self.issue_manager.get_active_issues()

if occurred_issues or active_issues:
    # 회의 진행
    meeting_result = self.conduct_meeting(occurred_issues, active_issues)
```

### 회의는 어떻게 진행되나?

**파일**: `src/core/agent_meeting.py` → `AgentMeeting.run()` 함수

```
┌────────────────────────────────────────────┐
│ 1. 건축주 GPT 의견 수렴                      │
│    - 우려 수준, 우선순위                     │
│    - 자원 경쟁 분석 (진행 중 이슈와 충돌?)    │
│    - 추천 착수 시점 (즉시/대기/조건부)        │
└─────────────────┬──────────────────────────┘
                  ▼
┌────────────────────────────────────────────┐
│ 2. 시공사 GPT 의견 수렴                      │
│    - 현장 평가                               │
│    - 공간 간섭 분석 (같은 구역 작업 중복?)   │
│    - 작업 순서 제안                          │
│    - 하도급 가용성                           │
└─────────────────┬──────────────────────────┘
                  ▼
┌────────────────────────────────────────────┐
│ 3. 심각도 평가                              │
│    - 건축주 + 시공사 평가 평균              │
│    - 최종 지연 주수 계산                    │
│    - 최종 비용 증가율 계산                  │
└─────────────────┬──────────────────────────┘
                  ▼
┌────────────────────────────────────────────┐
│ 4. 시공사가 해결 방안 2가지 제안            │
│    - 옵션 1: 정상 공정                      │
│    - 옵션 2: 인력 증투                      │
└─────────────────┬──────────────────────────┘
                  ▼
┌────────────────────────────────────────────┐
│ 5. 건축주가 최종 선택                       │
│    - 프로젝트 상황 고려하여 결정            │
└────────────────────────────────────────────┘
```

### 4-1. 건축주 GPT 의견

**파일**: `src/agents/owner_agent.py` → `get_system_prompt()` 함수

**GPT에게 주는 프롬프트 예시**:

```
당신은 건설 프로젝트의 건축주(발주자)입니다.

【프로젝트 현황】
- 총 공사비: 20.3억원
- 계획 공기: 360일
- 진행률: 35%
- 누적 지연: 15.2일
- 일일 금융 비용: 22.2만원

【현재 진행 중인 이슈】 ⚠️ 중요!
1. I-03 "기초 철근 간섭" (진행률 45%, 필요 인력 5명, 작업 공간 A구역)
2. I-08 "우기 장마 영향" (진행률 20%, 필요 인력 3명, 작업 공간 외부)

【신규 이슈】
I-25 "외부마감재 색상 변경"
- 예상 지연: 1.0~3.0주
- 예상 비용: 0.2~0.8%
- 필요 인력: 4명
- 작업 공간: A구역

【반드시 분석할 것】
1. 진행 중인 이슈와 자원 경쟁이 있는가?
   - 인력: I-03이 5명 쓰는데, 신규가 4명 필요 → 중복!
   - 공간: I-03이 A구역 쓰는데, 신규도 A구역 → 간섭!

2. 지금 착수하는 것이 적절한가?
   - 즉시착수: 자원 충돌 없음
   - 대기: 자원 충돌이 심함, 다른 이슈 완료 대기
   - 조건부착수: I-03이 55% 넘으면 착수

【출력 형식】
JSON 형식으로:
{
  "concern_level": "높음",
  "opinion": "I-03과 작업 공간 A구역이 중복되고, 인력도 4명 필요하여...",
  "severity_assessment": 8,
  "resource_conflict": "인력 4명 중복, 공간 A구역 간섭",
  "recommended_timing": "조건부착수"
}
```

**GPT 응답 예시**:

```json
{
  "concern_level": "높음",
  "priority": "일정 준수",
  "opinion": "신규 이슈는 I-03과 작업 공간(A구역)에서 100% 중복되며, 필요 인력도 4명으로 현재 5명 투입 중인 I-03과 충돌합니다. I-03이 45% 진행 중이므로 약 10일 후 완료 예상됩니다. 동시 착수 시 효율이 떨어지므로 I-03 완료 후 착수를 권장합니다.",
  "severity_assessment": 8,
  "budget_tolerance": "1.0%",
  "relationship_with_active_issues": "I-03과 강한 충돌",
  "resource_conflict": "인력 4명 중복, 공간 100% 간섭",
  "recommended_timing": "조건부착수"
}
```

### 4-2. 시공사 GPT 의견

**파일**: `src/agents/contractor_agent.py` → `get_system_prompt()` 함수

**GPT에게 주는 프롬프트 예시**:

```
당신은 현장 시공사입니다.

【현장 상황】
- 위치: 도심 (작업 공간 협소)
- 공법: BIM

【현재 진행 중인 이슈】
1. I-03 "기초 철근 간섭"
   - 필요 인력: 5명
   - 작업 공간: A구역
   - 남은 기간: 1.0주

【신규 이슈】
I-25 "외부마감재 색상 변경"
- 필요 인력: 4명
- 작업 공간: A구역

【분석할 것】
1. 공간 간섭: A구역이 같음 → 동시 작업 불가!
2. 자원 충돌: 인력 9명 필요 (5+4), 현재 8명만 가용
3. 작업 순서: I-03 완료 후 착수 권장

【출력 형식】
{
  "field_assessment": "현장 평가",
  "opinion": "A구역 공간 중복으로 동시 작업 불가...",
  "space_interference": "100%",
  "recommended_sequence": "선행이슈_완료후"
}
```

### 4-3. 심각도 평가

**파일**: `src/core/agent_meeting.py` → `_calculate_severity()` 함수

```python
# 1. 에이전트 평가 평균
owner_score = 8
contractor_score = 7
consensus = (8 + 7) / 2 = 7.5

# 2. 최종 지연 주수
delay_min = 1.0주
delay_max = 3.0주
final_delay = 1.0 + (3.0 - 1.0) × (7.5 / 10)
            = 1.0 + 2.0 × 0.75
            = 2.5주

# 3. 최종 비용 증가율
cost_min = 0.2%
cost_max = 0.8%
final_cost = 0.2 + (0.8 - 0.2) × (7.5 / 10)
           = 0.2 + 0.6 × 0.75
           = 0.65%
```

### 4-4. 해결 방안 제안

**시공사가 2가지 옵션 제안**:

```python
# 옵션 1: 정상 공정
{
  "option_id": "SOL-C1",
  "description": "정상 공정",
  "time_weeks": 2.5,        # 심각도 평가 결과 그대로
  "cost_increase_pct": 0.65,
  "quality_impact": "높음",
  "risk_level": "낮음"
}

# 옵션 2: 인력 증투
{
  "option_id": "SOL-C2",
  "description": "인력증투 신속처리",
  "time_weeks": 2.5 × 0.6 = 1.5,      # 40% 단축
  "cost_increase_pct": 0.65 × 2 = 1.3, # 2배
  "quality_impact": "보통",
  "risk_level": "보통"
}
```

### 4-5. 건축주 최종 선택

**파일**: `src/agents/owner_agent.py` → `select_solution()` 함수

```python
# 간단한 선택 로직 (실제로는 LLM 호출 가능)
if 누적지연 > 30일:
    selected = 옵션 2  # 인력 증투
elif 예산여유 < 5%:
    selected = 옵션 1  # 정상 공정
else:
    # 비용과 시간의 가중합
    score1 = 2.5 × 0.6 + 0.65 × 0.4 = 1.76
    score2 = 1.5 × 0.6 + 1.3 × 0.4 = 1.42
    selected = 옵션 2 (score가 낮음)
```

### 4-6. 지연/비용 누적

**파일**: `src/core/simulation_engine.py` → `conduct_meeting()` 함수

```python
# 선택된 방안의 값을 누적
selected_solution = discussion["selected"]["selected_solution"]

self.total_delay_days += selected_solution["time_weeks"] × 7
self.total_cost_increase_pct += selected_solution["cost_increase_pct"]
```

**예시**:
```
선택: 옵션 2 (인력 증투)
time_weeks = 1.5주 = 10.5일
cost_increase_pct = 1.3%

누적 지연: 15.2일 + 10.5일 = 25.7일
누적 비용: 3.5% + 1.3% = 4.8%
```

---

## 6. 5단계: 결과 저장 및 비교

### 무엇을 저장하나?

**3가지 파일**:

1. **회의 로그** (`logs/bim_meetings_YYYYMMDD_HHMMSS.json`)
   - 360일 동안의 모든 회의 기록
   - GPT 의견 전문 포함
   - 파일 크기: 약 1.3~1.4MB

2. **이슈 목록** (`logs/bim_issues_YYYYMMDD_HHMMSS.json`)
   - 각 이슈의 발생~해결 전체 과정
   - 일일 진행률 히스토리

3. **비교 리포트** (`results/comparison_report_YYYYMMDD_HHMMSS.json`)
   - BIM vs 전통 비교 결과만 간결하게

**파일**: `src/core/simulation_engine.py` → `save_results()` 함수

### BIM vs 전통 비교

**파일**: `main.py` → `compare_results()` 함수

```python
# 1. BIM 시뮬레이션 실행
bim_result = run_bim_simulation()

# 2. 전통 방식 시뮬레이션 실행
trad_result = run_traditional_simulation()

# 3. 비교
bim_delay = 25.7일
trad_delay = 35.3일
개선 = 35.3 - 25.7 = 9.6일 (27.2%)

bim_cost = 4.8%
trad_cost = 7.2%
개선 = 7.2 - 4.8 = 2.4%p (33.3%)
```

---

## 7. 코드 구조 및 주요 파일

### 실행 순서

```
1. main.py
   ↓
2. load_project_config()
   ↓
3. ConstructionSimulation.__init__()
   → determine_case()
   → get_kpi_values()
   → ProjectContext 생성
   ↓
4. run_simulation()
   → for day in range(1, 361):
       → filter_issues_by_progress()
       → check_issue_occurrence()
         → calculate_issue_probability()
       → update_all_issues()
       → conduct_meeting()
         → AgentMeeting.run()
           → owner_agent.give_opinion()
           → contractor_agent.give_opinion()
           → _calculate_severity()
           → _propose_solutions()
           → owner_agent.select_solution()
   ↓
5. save_results()
   ↓
6. compare_results()
```

### 주요 파일 및 함수

| 파일 | 주요 함수 | 역할 |
|------|----------|------|
| `main.py` | `load_project_config()` | 프로젝트 정보 로드 |
| | `run_bim_simulation()` | BIM 시뮬레이션 실행 |
| | `compare_results()` | BIM vs 전통 비교 |
| `src/config/case_mapping.py` | `determine_case()` | 케이스 결정 (A/B/C/D) |
| | `get_kpi_values()` | KPI 값 조회 |
| | `normalize_kpi_value()` | KPI 정규화 |
| `src/config/project_context.py` | `ProjectContext` | 프로젝트 컨텍스트 관리 |
| `src/core/simulation_engine.py` | `run_simulation()` | 전체 시뮬레이션 루프 |
| | `check_issue_occurrence()` | 이슈 발생 판단 |
| | `conduct_meeting()` | 회의 진행 |
| `src/core/probability_calculator.py` | `calculate_issue_probability()` | 확률 계산 |
| `src/core/agent_meeting.py` | `AgentMeeting.run()` | 회의 실행 |
| `src/core/issue_manager.py` | `update_all_issues()` | 진행률 업데이트 |
| `src/agents/owner_agent.py` | `give_opinion()` | 건축주 의견 |
| | `select_solution()` | 최종 선택 |
| `src/agents/contractor_agent.py` | `give_opinion()` | 시공사 의견 |
| `src/data/issue_cards.py` | `get_issues_by_method()` | 이슈 목록 로드 |
| | `filter_issues_by_progress()` | 공정률 필터링 |

