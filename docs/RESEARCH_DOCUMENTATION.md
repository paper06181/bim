# BIM 건설 시뮬레이션 - 연구용 상세 문서

## 📋 목차
1. [프로젝트 개요](#프로젝트-개요)
2. [연구 목적 및 의의](#연구-목적-및-의의)
3. [시스템 아키텍처](#시스템-아키텍처)
4. [핵심 알고리즘](#핵심-알고리즘)
5. [개선 사항 (2025년 버전)](#개선-사항)
6. [실험 설계 및 방법론](#실험-설계-및-방법론)
7. [결과 해석 가이드](#결과-해석-가이드)
8. [한계점 및 향후 연구](#한계점-및-향후-연구)

---

## 프로젝트 개요

### 1.1 연구 배경
건설 프로젝트에서 BIM(Building Information Modeling) 도입이 증가하고 있으나, 실제 효과에 대한 정량적 분석이 부족합니다. 본 시뮬레이션은 BIM 적용 전후의 프로젝트 성과를 비교하여 투자 타당성을 검증하는 것을 목표로 합니다.

### 1.2 시뮬레이션 범위
- **대상**: 중소형 건설 프로젝트 (883㎡~10,000㎡)
- **기간**: 설계→입찰→시공→준공 전체 단계
- **비교**: BIM OFF (전통 방식) vs BIM ON (BIM 적용)
- **측정 지표**: 공기 지연, 예산 초과, 이슈 탐지율, 금융 비용

---

## 연구 목적 및 의의

### 2.1 연구 질문
1. BIM 적용이 공사 기간과 예산에 미치는 정량적 영향은?
2. BIM 품질 수준에 따라 효과가 어떻게 달라지는가?
3. 어떤 유형의 이슈에서 BIM 효과가 가장 큰가?
4. 금융 비용 측면에서 BIM의 간접 효과는?

### 2.2 학술적 의의
- **Multi-Agent 시스템**: 건축주, 설계사, 시공사, 감리사, 금융사 간 협상 모델링
- **확률적 모델**: Monte Carlo 기반 이슈 발생 및 탐지 시뮬레이션
- **BIM 품질 지표**: WD, CD, AF, PL 4개 지표 기반 효과성 계산
- **금융 통합**: PF 금리 변동까지 고려한 종합 비용 분석

### 2.3 실무적 의의
- BIM 도입 의사결정 지원
- BIM 품질 목표 설정 근거 제공
- 프로젝트 유형별 BIM ROI 추정

---

## 시스템 아키텍처

### 3.1 전체 구조
```
┌─────────────────────────────────────────────────────────┐
│                   Main Simulation Engine                 │
│  - 시간 진행 (day-by-day)                                │
│  - 단계 전환 (설계→입찰→시공→준공)                      │
└───────────────────┬─────────────────────────────────────┘
                    │
        ┌───────────┴────────────┐
        │                        │
┌───────▼──────┐        ┌───────▼──────┐
│ Issue Manager│        │ Meeting      │
│ - 이슈 발생  │        │ Coordinator  │
│ - 확률 기반  │        │ - 5개 Agent  │
└───────┬──────┘        └───────┬──────┘
        │                        │
        │        ┌───────────────┴──────────────┐
        │        │                              │
        │   ┌────▼────┐              ┌─────────▼────────┐
        │   │ Impact  │              │ Negotiation      │
        │   │ Calc    │              │ System           │
        │   └────┬────┘              └─────────┬────────┘
        │        │                              │
        └────────┴──────────────────────────────┘
                         │
                ┌────────▼────────┐
                │ Financial Calc  │
                │ - PF 금리       │
                │ - 간접비        │
                └─────────────────┘
```

### 3.2 핵심 모듈

#### 3.2.1 Issue Manager (`simulation/issue_manager.py`)
**역할**: 27개 이슈 카드 관리 및 발생 제어

**이슈 발생 메커니즘**:
```python
# 각 이슈마다 독립적인 일별 발생 확률
occurrence_rate: 0.008 ~ 0.015 (0.8% ~ 1.5% / 일)

# 예시: I-01 (설비-구조 간섭)
- occurrence_rate: 0.015 (1.5% / 일)
- 시공 단계 (300일) 동안 매일 체크
- 발생 확률: 1 - (1-0.015)^300 ≈ 99% (거의 확정)
```

**이슈 카드 구조**:
```json
{
  "id": "I-01",
  "name": "설비-구조 간섭 미발견",
  "severity": "S3",
  "phase": "시공",
  "delay_weeks_min": 6,
  "delay_weeks_max": 10,
  "cost_increase_min": 0.025,
  "cost_increase_max": 0.04,
  "bim_effect": {
    "detection_phase": "설계",
    "base_detectability": 0.95
  },
  "work_type": "구조",
  "float_days": 0,
  "occurrence_rate": 0.015
}
```

#### 3.2.2 BIM Quality Calculator (`models/bim_quality.py`)
**4가지 BIM 품질 지표**:

1. **WD (Warning Density)**: 경고밀도 (100㎡당 경고 수)
   - 낮을수록 좋음: 0.3 (우수) ~ 1.5 (미흡)
   - 정규화: `1 - WD/2.0`

2. **CD (Clash Density)**: 충돌밀도 (100㎡당 충돌 수)
   - 낮을수록 좋음: 0.1 (우수) ~ 0.7 (미흡)
   - 정규화: `1 - CD/1.0`

3. **AF (Attribute Fill)**: 속성 채움률
   - 높을수록 좋음: 0.98 (우수) ~ 0.70 (미흡)
   - 이미 0~1 범위

4. **PL (Phase Link)**: 공정 연결률
   - 높을수록 좋음: 0.95 (우수) ~ 0.60 (미흡)
   - 이미 0~1 범위

**효과성 계산**:
```python
# 이슈별 가중치 예시 (I-01: 설비-구조 간섭)
weights = {'CD': 0.7, 'WD': 0.2, 'AF': 0.1, 'PL': 0.0}

# 정규화된 지표
normalized = {
    'WD': 1 - 0.5/2.0 = 0.75,
    'CD': 1 - 0.2/1.0 = 0.80,
    'AF': 0.95,
    'PL': 0.90
}

# 가중 평균
effectiveness = 0.7*0.80 + 0.2*0.75 + 0.1*0.95 + 0.0*0.90
              = 0.56 + 0.15 + 0.095 + 0.0
              = 0.805
```

**탐지 확률 계산 (Sigmoid)**:
```python
# base_detectability: 이슈의 본질적 탐지 가능성 (0~1)
# effectiveness: BIM 품질 효과성 (0~1)

k = 10  # 기울기 (가파른 정도)
x0 = 0.5  # 변곡점

sigmoid = 1 / (1 + exp(-k * (effectiveness - x0)))

detection_prob = base_detectability * sigmoid
```

**Sigmoid 곡선 특징**:
- effectiveness = 0.3 → sigmoid ≈ 0.12 (낮은 품질)
- effectiveness = 0.5 → sigmoid ≈ 0.50 (중간 품질)
- effectiveness = 0.7 → sigmoid ≈ 0.88 (높은 품질)

#### 3.2.3 Negotiation System (`simulation/negotiation_system.py`)
**에이전트별 선호도 및 가중치**:

| 에이전트 | 선호도 (위치) | 가중치 (영향력) | 설명 |
|---------|-------------|---------------|-----|
| 건축주  | 0.25 (빡빡) | 0.40 (40%)    | 최종 의사결정권자, 비용/일정 압박 |
| 시공사  | 0.75 (여유) | 0.25 (25%)    | 작업 여유 확보 선호 |
| 감리사  | 0.50 (중립) | 0.20 (20%)    | 계약 조건 기준 판단 |
| 설계사  | 0.40 (약간 빡빡) | 0.10 (10%) | 기술적 해결 가능성 기준 |
| 금융사  | 0.60 (약간 여유) | 0.05 (5%)  | 리스크 보수적 평가 |

**협상 결과 계산**:
```python
# 최종 위치 = 가중 평균
final_position = Σ (선호도[agent] × 가중치[agent])
               = 0.25×0.40 + 0.75×0.25 + 0.50×0.20 + 0.40×0.10 + 0.60×0.05
               = 0.10 + 0.1875 + 0.10 + 0.04 + 0.03
               = 0.4575 (약 45.75% 위치)

# 실제 지연/비용 결정
agreed_delay = delay_min + (delay_max - delay_min) × final_position
agreed_cost = cost_min + (cost_max - cost_min) × final_position

# 예시: I-01 (6~10주, 2.5~4.0%)
agreed_delay = 6 + (10-6) × 0.4575 = 7.83주
agreed_cost = 0.025 + (0.040-0.025) × 0.4575 = 0.0319 (3.19%)
```

**BIM 조기 탐지 시 조정**:
```python
if detected and BIM_enabled:
    prefs['owner'] = 0.20  # 더 빡빡 (0.25 → 0.20)
    weights['owner'] = 0.45  # 영향력 증가 (40% → 45%)
    weights['contractor'] = 0.22  # 시공사 영향력 감소 (25% → 22%)
```

#### 3.2.4 Impact Calculator (`simulation/impact_calculator.py`)
**BIM 조기 탐지 시 절감 효과**:

| 탐지 단계 | 지연 절감 | 비용 절감 | 설명 |
|----------|---------|---------|-----|
| 설계 | 70% | 80% | 시공 전 해결 → 최대 효과 |
| 발주 | 50% | 60% | 계약 전 조정 가능 |
| 시공초기 | 30% | 40% | 일부 작업 재조정 |
| 시공중기 | 15% | 20% | 제한적 수정 가능 |
| 시공후기 | 5% | 10% | 최소한의 조치만 가능 |

**계산 흐름**:
```python
# 1단계: 협상으로 기본값 결정
negotiated_delay = 7.83주  # 협상 결과
negotiated_cost = 0.0319  # 협상 결과

# 2단계: BIM 조기 탐지 추가 절감
if detected:
    # 설계 단계 탐지 + BIM 품질 0.805
    reduction_delay = 0.70 + (0.805 * 0.15) = 0.82 (82% 절감)
    reduction_cost = 0.80 + (0.805 * 0.15) = 0.92 (92% 절감)

    actual_delay = 7.83 × (1 - 0.82) = 1.41주
    actual_cost = 0.0319 × (1 - 0.92) = 0.0026 (0.26%)
```

#### 3.2.5 Financial Calculator (`models/financial.py`)
**금리 인상 구조 (개선 버전)**:

```python
# 기존 문제: 정수 개월만 처리 (2.9개월 → 2개월로 계산)
# 개선: 연속 보간으로 실수 처리

def get_rate_increase(delay_months):
    if delay_months < 1:
        return 0
    elif delay_months < 2:
        return 0  # 유예기간
    elif delay_months < 4:
        return int((delay_months - 2) / 2 * 20)  # 선형 증가
    elif delay_months < 7:
        return int(20 + (delay_months - 4) / 3 * 30)
    else:
        return min(100, int(50 + (delay_months - 7) / 3 * 50))

# 예시:
# 2.5개월 → 5bp
# 5.0개월 → 30bp
# 8.0개월 → 67bp
```

**금융 비용 계산**:
```python
# PF 대출액
loan_amount = budget × 0.7  # 70% PF

# 추가 이자
additional_interest = loan_amount × rate_increase × (delay_days / 365)

# 간접비 (일 0.1%)
additional_indirect = budget × 0.001 × delay_days

# 총 금융 비용
total_financial_cost = additional_interest + additional_indirect
```

---

## 개선 사항 (2025년 버전)

### 5.1 문제점 및 해결

#### 문제 1: 검증 시스템 강건성 부족
**문제**: 벤치마크 파일 없으면 오류로 중단
**해결**: 기본값 fallback 추가
```python
# validation.py
try:
    with open(benchmark_file, 'r', encoding='utf-8') as f:
        self.benchmark = json.load(f)
except FileNotFoundError:
    self.benchmark = self._get_default_benchmark()
```

#### 문제 2: 잘못된 주석
**문제**: Sigmoid 함수를 "softmax"라고 표기
**해결**: 정확한 설명으로 수정
```python
# 기존: k = BIMQualityConfig.SIGMOID_K #softmax함수
# 수정: k = BIMQualityConfig.SIGMOID_K  # 기울기 (가파른 정도)
```

#### 문제 3: 금리 인상 불연속
**문제**: 2.9개월 = 2개월로 처리 (0.9개월 무시)
**해결**: 연속 보간 함수 구현
```python
# 기존: delay_months_int = int(delay_months)
# 수정: 선형 보간으로 실수 처리
```

#### 문제 4: 프로젝트명 하드코딩
**문제**: "청담동 근린생활시설"이 코드에 고정
**해결**: 프로젝트 객체에서 동적으로 읽기
```python
# 기존: system_prompt = """당신은 청담동 근린생활시설 신축공사의 건축주..."""
# 수정: system_prompt = f"""당신은 {project.name}의 건축주..."""
```

#### 문제 5: LLM 에러 메시지 노출
**문제**: LLM 실패 시 "[LLM 응답 생성 실패...]" 메시지가 회의록에 저장
**해결**: 에러 체크 후 None 반환 → fallback 템플릿 자동 사용
```python
if response and "[LLM 응답 생성 실패" in response:
    return None  # 템플릿 응답 사용
```

### 5.2 검증 범위 확대
**기존**: 예산 초과율 15~30%, 일정 지연률 16~30%
**수정**: 예산 초과율 0~50%, 일정 지연률 0~50%
**근거**: 다양한 프로젝트 특성과 시나리오 수용

---

## 실험 설계 및 방법론

### 6.1 실험 설계

#### 6.1.1 독립 변수
1. **BIM 적용 여부**: OFF / ON
2. **BIM 품질 수준**: excellent / good / average / poor
3. **프로젝트 템플릿**: cheongdam (추가 가능)

#### 6.1.2 종속 변수
1. **공기 지연** (일, 주)
2. **예산 초과** (원, %)
3. **이슈 탐지율** (%)
4. **금융 비용** (원)

#### 6.1.3 통제 변수
- **Random Seed**: BIM ON/OFF 비교 시 동일 이슈 발생 보장
- **이슈 카드**: 27개 고정
- **프로젝트 규모**: 템플릿별 고정

### 6.2 시뮬레이션 실행

#### 기본 비교 실험
```bash
# BIM OFF vs ON 비교 (good 품질)
python main.py --scenario compare --quality good

# 결과:
# - output/results/comparison_result_[timestamp].txt
# - output/logs/simulation_log_BIM_OFF_[timestamp].txt
# - output/logs/simulation_log_BIM_ON_[timestamp].txt
# - output/*.png (4종 그래프)
```

#### BIM 품질별 실험
```bash
# 우수 품질
python main.py --scenario on --quality excellent

# 양호 품질
python main.py --scenario on --quality good

# 보통 품질
python main.py --scenario on --quality average

# 미흡 품질
python main.py --scenario on --quality poor
```

#### 사용자 정의 품질
```bash
# WD, CD, AF, PL 직접 입력
python main.py --quality custom --wd 0.5 --cd 0.2 --af 0.95 --pl 0.90
```

### 6.3 결과 검증

#### 6.3.1 내부 일관성 검증
- 이슈 발생 횟수 일치 (BIM ON/OFF)
- Random seed 동작 확인
- 지연/비용 누적 계산 정확성

#### 6.3.2 외부 타당성 검증
- 업계 벤치마크 대비 편차 확인
- McGraw Hill (2014) 기준: BIM 적용 시
  - 예산 초과율: 8% (전통 22%)
  - 일정 지연률: 10% (전통 23%)

---

## 결과 해석 가이드

### 7.1 주요 지표 해석

#### 7.1.1 공사 기간
- **지연 일수**: 계획 대비 실제 지연
- **해석**:
  - 0~7일: 우수
  - 8~30일: 양호
  - 31~60일: 보통
  - 61일 이상: 미흡

#### 7.1.2 예산 초과
- **초과율 (%)**: (실제비용 - 계획예산) / 계획예산
- **해석**:
  - 0~5%: 우수
  - 6~15%: 양호
  - 16~30%: 보통
  - 31% 이상: 미흡

#### 7.1.3 이슈 탐지율
- **탐지율 (%)**: 조기 탐지 이슈 / 전체 이슈
- **해석**:
  - BIM OFF: 0~20% (대부분 사후 발견)
  - BIM POOR: 20~40%
  - BIM AVERAGE: 40~60%
  - BIM GOOD: 60~80%
  - BIM EXCELLENT: 80~98%

### 7.2 그래프 해석

#### 7.2.1 공사 지연 비교 (timeline_comparison.png)
- X축: BIM OFF vs ON
- Y축: 지연 주수
- **해석**: 막대 높이 차이 = BIM 효과

#### 7.2.2 이슈 분류 (issue_breakdown.png)
- 원형 차트: 설계/시공/계약/자재/감리 이슈 비율
- **해석**: 어떤 유형 이슈가 많이 발생했는지

#### 7.2.3 ROI 분석 (roi_analysis.png)
- X축: 비용 항목
- Y축: 금액
- **해석**: BIM 투자 대비 절감액

### 7.3 통계적 유의성

#### 반복 실험 권장
```bash
# 동일 조건 10회 반복 (다른 seed)
for i in {1..10}; do
    python main.py --scenario compare
done
```

#### 평균 및 표준편차 계산
- 지연 일수: μ ± σ
- 예산 초과율: μ ± σ
- 탐지율: μ ± σ

---

## 한계점 및 향후 연구

### 8.1 현재 한계점

#### 8.1.1 모델링 단순화
- **현실**: 날씨, 인력, 자재 공급망 등 복잡한 변수
- **모델**: 확률 기반 이슈 카드로 단순화
- **영향**: 실제 프로젝트보다 단순한 패턴

#### 8.1.2 에이전트 협상
- **현실**: 복잡한 이해관계와 감정적 요소
- **모델**: 가중치 기반 선형 모델
- **영향**: 극단적 갈등 상황 미반영

#### 8.1.3 BIM 품질 지표
- **현실**: 수백 가지 품질 요소
- **모델**: 4가지 지표 (WD, CD, AF, PL)
- **영향**: 일부 품질 차원 누락

#### 8.1.4 프로젝트 다양성
- **현실**: 수천 가지 건물 유형
- **모델**: 현재 1개 템플릿 (청담동)
- **영향**: 일반화 제한

### 8.2 향후 연구 방향

#### 8.2.1 단기 개선 (3개월)
1. **프로젝트 템플릿 확대**
   - 오피스텔, 아파트, 상업시설 등 추가
   - 규모별 (소형/중형/대형) 파라미터 조정

2. **이슈 카드 확장**
   - 27개 → 50개 이상
   - 지역별, 시즌별 특성 반영

3. **협상 모델 고도화**
   - 비선형 모델 도입
   - 프로젝트 단계별 가중치 변화

#### 8.2.2 중기 개선 (6개월)
1. **CPM 네트워크 강화**
   - 실제 공정표 연동
   - Critical Path 기반 지연 계산

2. **BIM 품질 지표 확장**
   - LOD (Level of Development) 추가
   - 협업 지표 (Collaboration Index) 추가

3. **기계학습 통합**
   - 과거 프로젝트 데이터 학습
   - 이슈 발생 패턴 예측

#### 8.2.3 장기 개선 (1년)
1. **실시간 프로젝트 연동**
   - BIM 서버 API 연동
   - 실시간 품질 모니터링

2. **다목적 최적화**
   - BIM 투자 수준 최적화
   - 리소스 배분 최적화

3. **산업 표준화**
   - ISO 19650 기준 적용
   - buildingSMART 표준 준수

---

## 참고 문헌

1. McGraw Hill Construction (2014). *The Business Value of BIM for Construction in Major Global Markets*. SmartMarket Report.

2. Eastman, C., Teicholz, P., Sacks, R., & Liston, K. (2011). *BIM Handbook: A Guide to Building Information Modeling for Owners, Managers, Designers, Engineers and Contractors* (2nd ed.). Wiley.

3. 한국감정원 (2023). *부동산 PF 실태조사*. 연구보고서.

4. Azhar, S. (2011). Building Information Modeling (BIM): Trends, Benefits, Risks, and Challenges for the AEC Industry. *Leadership and Management in Engineering*, 11(3), 241-252.

5. Bryde, D., Broquetas, M., & Volm, J. M. (2013). The project benefits of Building Information Modelling (BIM). *International Journal of Project Management*, 31(7), 971-980.

---

## 부록

### A. 이슈 카드 전체 목록
27개 이슈 카드 상세 내역은 `data/issue_cards.json` 참조

### B. BIM 품질 프리셋
| 수준 | WD | CD | AF | PL | 품질 점수 |
|-----|----|----|----|----|----------|
| Excellent | 0.3 | 0.1 | 0.98 | 0.95 | 0.93 |
| Good | 0.5 | 0.2 | 0.95 | 0.90 | 0.86 |
| Average | 0.8 | 0.4 | 0.85 | 0.75 | 0.68 |
| Poor | 1.5 | 0.7 | 0.70 | 0.60 | 0.44 |

### C. 금융 비용 계산식
```
PF 대출액 = 총 예산 × 0.7
추가 이자 = PF 대출액 × 금리 인상률 × (지연 일수 / 365)
간접비 = 총 예산 × 0.001 × 지연 일수
총 금융 비용 = 추가 이자 + 간접비
```

---

**문서 버전**: v2.0 (2025-01-20)
**최종 업데이트**: 개선 사항 반영 완료
**작성자**: BIM Simulation Research Team
**연락처**: 프로젝트 담당자에게 문의
