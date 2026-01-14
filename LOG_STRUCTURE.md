# 회의 로그 및 결과 저장 구조

## 📁 파일 저장 구조

시뮬레이션 실행 시 다음과 같이 파일이 생성됩니다:

```
construction_simulation/
├── logs/                                           # 회의 로그 및 이슈 저장
│   ├── bim_meetings_20260114_153000.json          # BIM 전체 회의 로그 (1개 파일)
│   ├── bim_issues_20260114_153000.json            # BIM 이슈 목록 (1개 파일)
│   ├── traditional_meetings_20260114_160000.json  # 전통 전체 회의 로그 (1개 파일)
│   └── traditional_issues_20260114_160000.json    # 전통 이슈 목록 (1개 파일)
│
└── results/                                        # 결과 요약
    └── comparison_report_20260114_160000.json     # 비교 리포트 (간결)
```

**특징**:
- 각 시뮬레이션(BIM/전통)당 **2개 파일만 생성** (회의 로그 + 이슈 목록)
- 전체 공기(360일) 동안의 모든 회의를 **1개 파일**에 저장
- 타임스탬프로 실행 시점 구분

---

## 📊 1. 회의 로그 파일 (`logs/bim_meetings_YYYYMMDD_HHMMSS.json`)

### 개요
- **목적**: 전체 공기 동안 매일 진행되는 GPT 에이전트 회의를 상세 기록
- **파일 개수**: 시뮬레이션 1회당 1개 파일
- **파일 크기**: 약 1.3~1.4MB (360일 기준)
- **내용**: 매일의 진행률, 이슈 현황, GPT 의견, 해결 방안, 최종 결정

### 전체 구조

```json
{
  "시뮬레이션정보": {
    "공법": "BIM",
    "시작일": "20260114_153000",
    "총일수": 360,
    "프로젝트": {
      "위치": "도심",
      "용적률": "80%",
      "연면적": "883.5㎡",
      "총공사비": "20.3억원",
      "계획공기": "360일",
      "케이스": "A"
    }
  },
  "회의로그": [
    {
      "day": 0,
      "progress_rate": 0.0,
      "issue_status_summary": {...},
      "discussions": [...]
    },
    {
      "day": 1,
      "progress_rate": 0.0028,
      "issue_status_summary": {...},
      "discussions": [...]
    },
    ...
    (360일치 회의 기록)
  ]
}
```

### 매일 회의 구조

각 날짜별 회의는 다음 정보를 포함합니다:

```json
{
  "day": 0,
  "progress_rate": 0.0,
  "issue_status_summary": {
    "해결완료": [],
    "진행중": [
      {
        "ID": "I-03",
        "이름": "기초 철근 간섭",
        "진행률": "25%",
        "카테고리": "설계"
      }
    ],
    "대기중": []
  },
  "discussions": [
    {
      "issue_id": "I-20",
      "issue_name": "외부마감재 색상 계획 변경",
      "category": "설계",
      "type": "신규",
      "report": "",
      "opinions": {
        "건축주": {...},
        "시공사": {...}
      },
      "severity": {...},
      "solutions": [...],
      "selected": {...}
    }
  ]
}
```

### 건축주 GPT 의견 구조

```json
"건축주": {
  "concern_level": "높음",                    // 우려 수준: 높음/보통/낮음
  "priority": "일정 준수",                    // 우선순위: 비용 최소화/일정 준수/품질 유지/안전 확보
  "opinion": "이 신규 이슈는 현재 진행 중인 이슈가 없으므로 자원 경쟁은 없으나, 예상 지연이 1.0 ~ 3.0주로 일정에 큰 영향을 끼칠 수 있다. 현재 누적 지연이 0.0일이므로 일정 압박은 낮지만, 초기 단계에서 지연이 발생하면 후반부에 영향을 미칠 수 있다. 따라서 신속한 대응이 필요하다고 판단된다.",
  "severity_assessment": 7,                   // 심각도 평가 (1~10)
  "budget_tolerance": "1.5%",                 // 추가 비용 허용 한도
  "relationship_with_active_issues": "현재 진행 중인 이슈가 없으므로 상호작용은 없음.",
  "resource_conflict": "없음",                // 자원 경쟁 여부
  "recommended_timing": "즉시착수"            // 추천 착수 시점: 즉시착수/대기/조건부착수
}
```

**건축주 GPT의 역할**:
- 비용과 일정 중심의 의사결정
- 현재 진행 중인 이슈와의 **자원 경쟁** 분석
- 누적 지연 상황 고려
- 즉시 착수 vs 대기 vs 조건부 착수 판단

### 시공사 GPT 의견 구조

```json
"시공사": {
  "field_assessment": "현장 실행 가능성 평가가 양호하다고 판단됩니다. 신규 이슈이므로 현재 진행 중인 이슈와의 간섭이 없으며, 자재 조달 및 인력 배치 측면에서도 문제가 없습니다.",
  "severity_assessment": 7,                   // 심각도 평가 (1~10)
  "opinion": "신규 이슈는 현재 진행 중인 다른 이슈와의 현장 간섭 없음, 자원 투입도 가능합니다. 다만 예상 지연이 1.0 ~ 3.0주로 상당히 길기 때문에, 일정을 고려하여 인력 증투 옵션도 검토할 필요가 있습니다.",
  "impact_on_schedule": "단기영향",          // 일정 영향: 단기영향/중장기영향
  "resource_conflict_detail": "현재 진행 중인 이슈가 없으므로 자원 충돌 없음. 필요 인력 및 자재를 즉시 투입할 수 있습니다.",
  "space_interference": "없음",              // 공간 간섭: 없음 / 30% / 50% 등
  "safety_risk": "낮음",                     // 안전 리스크: 높음/보통/낮음
  "recommended_sequence": "즉시착수",        // 작업 순서: 즉시착수/선행이슈_완료후/병렬처리
  "subcontractor_availability": "하도급 업체 즉시 투입 가능"  // 하도급 가용성
}
```

**시공사 GPT의 역할**:
- 현장 실행 가능성 중심 평가
- **공간 간섭** 분석 (같은 구역에서 동시 작업 불가)
- **자원 충돌** 분석 (인력/자재 중복 투입 여부)
- 작업 순서 및 하도급 업체 가용성 평가
- 해결 방안 제안 (정상 공정 vs 인력 증투)

### 심각도 평가 구조

```json
"severity": {
  "agent_consensus": 7.0,                    // 에이전트 합의 심각도 (평균)
  "kpi_impact": -0.695,                      // KPI 영향도 (-1 ~ +1)
  "final_delay_weeks": 2.1,                  // 최종 예상 지연 (주)
  "final_cost_increase_pct": 0.49            // 최종 예상 비용 증가율 (%)
}
```

### 해결 방안 구조

시공사가 2가지 옵션 제안:

```json
"solutions": [
  {
    "option_id": "SOL-C1",
    "proposer": "시공사",
    "description": "정상 공정",
    "time_weeks": 2.4,                       // 소요 시간 (주)
    "cost_increase_pct": 0.9,                // 비용 증가율 (%)
    "quality_impact": "높음",                 // 품질 영향: 높음/보통/낮음
    "risk_level": "낮음"                      // 리스크: 높음/보통/낮음
  },
  {
    "option_id": "SOL-C2",
    "proposer": "시공사",
    "description": "인력증투 신속처리",
    "time_weeks": 1.5,                       // 정상 공정보다 40% 단축
    "cost_increase_pct": 1.8,                // 비용은 2배
    "quality_impact": "보통",
    "risk_level": "보통"
  }
]
```

**옵션 1 (정상 공정)**:
- 시간: 원래 예상대로
- 비용: 최소
- 품질: 높음
- 리스크: 낮음

**옵션 2 (인력 증투)**:
- 시간: 약 60% 단축
- 비용: 약 2배
- 품질: 보통
- 리스크: 보통

### 최종 선택 구조

```json
"selected": {
  "selected_solution": {
    "option_id": "SOL-C2",
    "description": "인력증투 신속처리",
    "time_weeks": 1.5,
    "cost_increase_pct": 1.8
  },
  "selection_rationale": "초기 단계이므로 일정 지연을 최소화하는 것이 중요하다고 판단하여 인력 증투 옵션을 선택함. 비용은 증가하나 후반부 일정 압박을 방지할 수 있음."
}
```

---

## 📋 2. 이슈 목록 파일 (`logs/bim_issues_YYYYMMDD_HHMMSS.json`)

### 개요
- **목적**: 전체 이슈의 상태, 진행률, 일일 업데이트 히스토리 저장
- **파일 개수**: 시뮬레이션 1회당 1개 파일
- **내용**: 각 이슈의 발생~해결 전체 과정 추적

### 전체 구조

```json
{
  "총이슈수": 76,
  "이슈목록": [
    {
      "id": "I-20",
      "name": "외부마감재 색상 계획 변경",
      "category": "설계",
      "severity": "중",
      "stage": "설계",
      "status": "해결완료",
      "progress": 100.0,
      "occurred_day": 0,
      "resolved_day": 15,
      "initial_severity": {...},
      "selected_solution": {...},
      "daily_updates": [...],
      "dependencies": [],
      "blocking": []
    },
    ...
  ]
}
```

### 개별 이슈 구조

```json
{
  "id": "I-20",
  "name": "외부마감재 색상 계획 변경",
  "category": "설계",
  "severity": "중",                          // 높음/중/낮음
  "stage": "설계",                           // 설계/시공/준공
  "status": "해결완료",                      // 해결완료/해결중/대기중/보류
  "progress": 100.0,                         // 진행률 (0~100%)
  "occurred_day": 0,                         // 발생일
  "resolved_day": 15,                        // 해결일 (해결 전이면 null)
  "initial_severity": {
    "agent_consensus": 7.0,
    "final_delay_weeks": 2.1,
    "final_cost_increase_pct": 0.49
  },
  "selected_solution": {
    "option_id": "SOL-C2",
    "description": "인력증투 신속처리",
    "time_weeks": 1.5,
    "cost_increase_pct": 1.8
  },
  "daily_updates": [
    {
      "day": 0,
      "progress": 0,
      "status": "해결중",
      "note": "신규 이슈 발생"
    },
    {
      "day": 1,
      "progress": 6.67,
      "status": "해결중",
      "note": "진행 중"
    },
    {
      "day": 2,
      "progress": 13.33,
      "status": "해결중",
      "note": "진행 중"
    },
    ...
    {
      "day": 15,
      "progress": 100.0,
      "status": "해결완료",
      "note": "해결 완료"
    }
  ],
  "dependencies": [],                        // 선행 이슈 ID 목록
  "blocking": []                             // 후행 이슈 ID 목록 (이 이슈가 막고 있는)
}
```

### 일일 업데이트 (daily_updates)

각 이슈는 매일 진행률이 업데이트됩니다:

```json
{
  "day": 5,
  "progress": 33.33,
  "status": "해결중",
  "note": "진행 중"
}
```

- **progress**: 0 → 100으로 증가
- **status**: 해결중 → 해결완료
- **note**: 특이사항 기록

---

## 📈 3. 비교 리포트 파일 (`results/comparison_report_YYYYMMDD_HHMMSS.json`)

### 개요
- **목적**: BIM vs 전통 방식 비교 결과만 간결하게 요약
- **파일 개수**: 1회 실행당 1개 (BIM + 전통 비교)
- **내용**: 일정, 비용, 이슈 개수 비교

### 전체 구조

```json
{
  "시뮬레이션정보": {
    "실행일시": "2026-01-14 16:00:00",
    "프로젝트": {
      "위치": "도심",
      "용적률": "80%",
      "연면적": "883.5㎡",
      "총공사비": "20.3억원",
      "계획공기": "360일",
      "케이스": "A"
    }
  },
  "BIM방식": {
    "목표공기": "360일",
    "실제소요": "488일",
    "누적지연_일": 128.8,
    "비용증가_퍼센트": 6.21,
    "총이슈수": 76,
    "해결완료": 75
  },
  "전통방식": {
    "목표공기": "360일",
    "실제소요": "524일",
    "누적지연_일": 164.1,
    "비용증가_퍼센트": 10.93,
    "총이슈수": 85,
    "해결완료": 84
  },
  "BIM개선효과": {
    "일정단축_일": 35.3,
    "일정개선율_퍼센트": 21.5,
    "비용절감_퍼센트포인트": 4.72,
    "비용개선율_퍼센트": 43.2,
    "이슈감소_개수": 9,
    "이슈개선율_퍼센트": 10.6
  }
}
```

### 비교 지표

#### 일정 비교
- **누적지연_일**: 목표 공기 대비 실제 지연 일수
- **일정단축_일**: 전통 방식 대비 BIM 단축 일수
- **일정개선율**: (전통지연 - BIM지연) / 전통지연 × 100

#### 비용 비교
- **비용증가_퍼센트**: 계획 대비 비용 증가율
- **비용절감_퍼센트포인트**: 전통 방식 대비 BIM 절감 %p
- **비용개선율**: (전통증가 - BIM증가) / 전통증가 × 100

#### 이슈 비교
- **총이슈수**: 전체 공기 동안 발생한 이슈 개수
- **이슈감소_개수**: 전통 방식 대비 BIM 감소 개수
- **이슈개선율**: (전통이슈 - BIM이슈) / 전통이슈 × 100

---

## 🎯 로그 활용 방법

### 1. 매일 회의 분석

**회의 로그 파일**에서 특정 날짜의 회의 내용 확인:

```python
import json

with open("logs/bim_meetings_20260114_153000.json", "r") as f:
    data = json.load(f)

# 50일차 회의 확인
day_50 = [log for log in data["회의로그"] if log["day"] == 50][0]
print(f"진행률: {day_50['progress_rate'] * 100:.1f}%")
print(f"진행중 이슈: {len(day_50['issue_status_summary']['진행중'])}개")
```

### 2. 특정 이슈 추적

**이슈 목록 파일**에서 특정 이슈의 전체 히스토리 확인:

```python
with open("logs/bim_issues_20260114_153000.json", "r") as f:
    data = json.load(f)

# ID가 "I-20"인 이슈 찾기
issue = [i for i in data["이슈목록"] if i["id"] == "I-20"][0]
print(f"이슈명: {issue['name']}")
print(f"발생일: {issue['occurred_day']}")
print(f"해결일: {issue['resolved_day']}")
print(f"소요일: {issue['resolved_day'] - issue['occurred_day']}일")
```

### 3. GPT 의견 분석

**회의 로그**에서 GPT가 어떤 판단을 내렸는지 확인:

```python
# 특정 이슈에 대한 건축주 의견
discussion = day_50["discussions"][0]
owner_opinion = discussion["opinions"]["건축주"]
print(f"우려 수준: {owner_opinion['concern_level']}")
print(f"자원 경쟁: {owner_opinion['resource_conflict']}")
print(f"추천 타이밍: {owner_opinion['recommended_timing']}")
```

### 4. 비교 분석

**비교 리포트**로 BIM 효과 한눈에 확인:

```python
with open("results/comparison_report_20260114_160000.json", "r") as f:
    data = json.load(f)

bim_effect = data["BIM개선효과"]
print(f"일정 단축: {bim_effect['일정단축_일']}일 ({bim_effect['일정개선율_퍼센트']}%)")
print(f"비용 절감: {bim_effect['비용절감_퍼센트포인트']}%p ({bim_effect['비용개선율_퍼센트']}%)")
```

---

## 🚀 실행 방법

```bash
python main.py
```

**생성되는 파일**:

```
logs/bim_meetings_20260114_153000.json          # BIM 회의 로그 (~1.4MB)
logs/bim_issues_20260114_153000.json            # BIM 이슈 목록
logs/traditional_meetings_20260114_160000.json  # 전통 회의 로그 (~1.5MB)
logs/traditional_issues_20260114_160000.json    # 전통 이슈 목록
results/comparison_report_20260114_160000.json  # 비교 리포트
```

---

## 📌 요약

### 로그 파일 특징

1. **회의 로그** (`bim_meetings_*.json`)
   - 전체 공기 360일간 모든 회의 기록
   - 매일 GPT 의견 전문 포함
   - 자원 경쟁, 공간 간섭 분석 포함
   - 해결 방안 제안 및 선택 과정 기록

2. **이슈 목록** (`bim_issues_*.json`)
   - 각 이슈의 발생~해결 전체 과정
   - 일일 진행률 업데이트 히스토리
   - 선택된 해결 방안 기록

3. **비교 리포트** (`comparison_report_*.json`)
   - BIM vs 전통 방식 비교 결과만 간결하게
   - 일정, 비용, 이슈 개수 비교
   - 개선 효과 정량화

### 활용 방안

- **연구 분석**: 회의 로그에서 GPT 의사결정 패턴 분석
- **프로젝트 관리**: 이슈 목록에서 병목 구간 파악
- **성과 보고**: 비교 리포트로 BIM 도입 효과 입증
