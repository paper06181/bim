# BIM 효과 정량화 시뮬레이션 (개선 버전)

건설 프로젝트에서 BIM 적용 효과를 정량화하는 멀티 에이전트 시뮬레이션 시스템입니다.

## 주요 개선 사항

### 1. 데이터 기반 아키텍처
- **엑셀 기반 데이터 관리**: 모든 KPI, CASE, 이슈카드 데이터를 엑셀에서 직접 로드
- **하드코딩 제거**: 데이터 변경 시 코드 수정 불필요
- **유연한 CASE 시스템**: 용도지역, 용적률 등에 따른 KPI 자동 선택

### 2. 새로운 리스크 모델
- **확률 제거**: 기존 확률 기반 시스템 대신 **KPI + Severity 기반** 결정론적 모델
- **Resolution Level**: 회의를 통한 대응 수준(0.0 ~ 1.0) 결정
- **임계값 기반**: THRESHOLD_NONE(0.15), THRESHOLD_MINOR(0.35)를 통한 발생 여부 판정

### 3. 멀티 에이전트 회의 시스템
- **5명 에이전트**: 건축주, 설계사, 시공사, 감리사, 금융사
- **JSON 기반 출력**: 깔끔한 resolution_level 결정
- **LLM 옵션**: LLM 사용 또는 규칙 기반 선택 가능

### 4. 3가지 시나리오 비교
1. **전통 방식 (기본 관리)**: BIM 미적용, 기본 수준 관리
2. **전통 방식 (강화 관리)**: BIM 미적용, 강화된 리스크 관리
3. **BIM 적용**: BIM 사용, 강화된 관리

## 설치

```bash
# 가상환경 활성화
.venv\Scripts\activate

# 필요한 패키지 설치
pip install openpyxl matplotlib pandas
```

## 사용법

### 기본 실행
```bash
python main_new.py
```

### 옵션
```bash
# LLM 기반 에이전트 회의 사용 (API 키 필요)
python main_new.py --llm

# 간략한 출력 (상세 로그 숨김)
python main_new.py --quiet

# 조합
python main_new.py --llm --quiet
```

## 프로젝트 구조

```
construction_simulation/
├── data/
│   ├── data_models.py        # 데이터 모델 (KPISet, Case, IssueCard, etc.)
│   ├── excel_loader.py       # 엑셀 데이터 로더
│   └── __init__.py
├── engine/
│   ├── risk_calculator.py    # 리스크 계산 엔진
│   ├── agent_meeting.py      # 5명 에이전트 회의 시스템
│   ├── scenario_engine.py    # 시나리오 실행 엔진
│   └── __init__.py
├── agents/                    # 기존 에이전트 (재활용)
│   ├── owner_agent.py
│   ├── designer_agent.py
│   ├── contractor_agent.py
│   ├── supervisor_agent.py
│   └── bank_agent.py
├── output/
│   └── results/               # 비교 리포트 저장
├── main_new.py                # 새 메인 실행 스크립트
├── BIM 효과 정량화를 위한 멀티 에이전트 시뮬레이션 연구.xlsx  # 데이터
└── README_NEW.md              # 이 파일
```

## 데이터 모델

### KPISet
```python
# BIM 적용 KPI
{
    "WD": 0.49,   # Warning Density (경고밀도)
    "CD": 0.17,   # Clash Density (충돌밀도)
    "AF": 0.25,   # Attribute Fill Rate (속성 채움률)
    "PL": 0.13    # Planning Linkage Rate (공정 연계도)
}

# 전통 방식 KPI
{
    "RR": 0.54,   # Rework Ratio (재시공률)
    "SR": 2.48,   # Safety Risk Occurrence Rate (안전사고 발생률)
    "CR": 1.32,   # Construction Delay Ratio (공정 지연률)
    "FC": 0.00    # Frequency of Change Order (설계 변경 빈도)
}
```

### 리스크 계산 공식

1. **기본 리스크 점수**
   ```
   base_risk = severity_factor * Σ(KPI_value * weight)

   severity_factor = {
       "S1": 0.33,
       "S2": 0.67,
       "S3": 1.00
   }
   ```

2. **실제 리스크 (resolution_level 반영)**
   ```
   effective_risk = base_risk * (1 - 0.6 * resolution_level)
   ```

3. **영향도 계산**
   ```
   if effective_risk < 0.15:
       impact_factor = 0.0  (발생 안 함)
   elif effective_risk >= 0.35:
       impact_factor = 1.0  (최대 영향)
   else:
       impact_factor = 선형 보간
   ```

4. **실제 지연/비용**
   ```
   delay_weeks = delay_min + impact_factor * (delay_max - delay_min)
   cost_pct = cost_min + impact_factor * (cost_max - cost_min)
   ```

## 결과 해석

### 출력 파일
- `output/results/bim_comparison_YYYYMMDD_HHMMSS.txt`

### 주요 지표
- **실제 공기**: 계획 공기 + 지연 일수
- **실제 비용**: 기준 공사비 × (1 + 비용증가율/100)
- **발생 이슈 수**: Major/Minor/None으로 분류
- **공기 단축/비용 절감**: 시나리오 간 차이

## 시나리오별 특징

### 전통 방식 (기본)
- RR/SR/CR/FC 기반 KPI
- resolution_level: 규칙 기반 (S3 → 1.0, S2 → 0.5, S1 → 0.0)
- 관리 수준: 기본

### 전통 방식 (강화)
- 동일한 KPI
- resolution_level: 규칙 기반 + 0.3 boost
- 관리 수준: 강화 (리스크를 더 적극적으로 대응)

### BIM 적용
- WD/CD/AF/PL 기반 KPI (모델 품질 중심)
- resolution_level: 규칙 기반 + 0.3 boost
- 관리 수준: 강화

## 확장 가능성

### 1. CASE 매트릭스 개선
현재는 간단한 휴리스틱으로 등급을 결정하지만, 엑셀의 CASE 시트를 완전히 파싱하여 정확한 매칭 가능

### 2. LLM 에이전트 활성화
`--llm` 옵션으로 OpenAI API를 통한 실제 에이전트 대화 가능
(환경변수 OPENAI_API_KEY 설정 필요)

### 3. 그래프 시각화
기존 `reports/graph_visualizer.py` 재활용하여 막대그래프, 타임라인 등 생성 가능

### 4. 상세 회의록
`engine/agent_meeting.py`에서 회의 내용을 파일로 저장하는 기능 추가 가능

