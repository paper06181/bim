# 빠른 참조 가이드

## 🚀 5분 안에 시작하기

### 1단계: 설치
```bash
pip install -r requirements.txt
```

### 2단계: API 키 설정 (선택 사항)
`.env` 파일에 OpenAI API 키 추가:
```
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini
```

> **Note**: API 키가 없어도 템플릿 모드로 작동합니다.

### 3단계: 실행
```bash
# 기본 비교 (BIM OFF vs ON)
python main.py --scenario compare

# 결과는 output/ 폴더에 자동 저장됩니다
```

---

## 📊 주요 명령어

### BIM ON/OFF 비교
```bash
python main.py --scenario compare --quality good
```
**출력**:
- `output/results/comparison_result_[timestamp].txt` - 비교 리포트
- `output/*.png` - 4종 그래프

### BIM만 실행
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

### 사용자 정의 BIM 품질
```bash
python main.py --quality custom --wd 0.5 --cd 0.2 --af 0.95 --pl 0.90
```

**지표 설명**:
- `--wd`: Warning Density (경고밀도, 낮을수록 좋음)
- `--cd`: Clash Density (충돌밀도, 낮을수록 좋음)
- `--af`: Attribute Fill (속성채움률, 0~1, 높을수록 좋음)
- `--pl`: Phase Link (공정연결률, 0~1, 높을수록 좋음)

### 템플릿 사용
```bash
# 사용 가능한 템플릿 확인
python main.py --list-templates

# 청담동 프로젝트
python main.py --template cheongdam --scenario compare
```

---

## 📁 출력 파일 구조

```
output/
├── results/
│   └── comparison_result_[timestamp].txt    # 비교 리포트
├── logs/
│   ├── simulation_log_BIM_OFF_[timestamp].txt
│   └── simulation_log_BIM_ON_[timestamp].txt
├── meetings/
│   ├── meetings_BIM_OFF_[timestamp].txt
│   └── meetings_BIM_ON_[timestamp].txt
├── timeline_comparison.png    # 공기 비교 그래프
├── issue_breakdown.png       # 이슈 분류 그래프
├── roi_analysis.png         # ROI 분석 그래프
└── comparison_bars.png      # 종합 비교 그래프
```

---

## 🎯 핵심 지표 해석

### 공사 기간
| 지연 일수 | 평가 |
|----------|------|
| 0~7일 | ⭐⭐⭐ 우수 |
| 8~30일 | ⭐⭐ 양호 |
| 31~60일 | ⭐ 보통 |
| 61일 이상 | ❌ 미흡 |

### 예산 초과
| 초과율 | 평가 |
|-------|------|
| 0~5% | ⭐⭐⭐ 우수 |
| 6~15% | ⭐⭐ 양호 |
| 16~30% | ⭐ 보통 |
| 31% 이상 | ❌ 미흡 |

### 이슈 탐지율
| BIM 품질 | 탐지율 |
|---------|-------|
| Excellent | 80~98% |
| Good | 60~80% |
| Average | 40~60% |
| Poor | 20~40% |
| OFF | 0~20% |

---

## 🔧 문제 해결

### Q1. API 키 오류
**증상**: `ValueError: OPENAI_API_KEY not found`
**해결**:
1. `.env` 파일 생성
2. API 키 입력: `OPENAI_API_KEY=sk-...`
3. 또는 템플릿 모드로 실행 (API 키 없이 작동)

### Q2. 벤치마크 파일 없음
**증상**: `FileNotFoundError: benchmark_data.json`
**해결**: 자동으로 기본값 사용됩니다 (정상 작동)

### Q3. 그래프 생성 오류
**증상**: 그래프 파일 생성 안 됨
**해결**: matplotlib 한글 폰트 확인
```bash
# 한글 폰트 테스트
python test_graph_font.py
```

### Q4. 시뮬레이션이 너무 느림
**증상**: 1시간 이상 걸림
**해결**:
```bash
# 간단 테스트만 실행
python test_quick.py

# 또는 quiet 모드
python main.py --scenario compare --quiet
```

---

## 💡 팁 & 트릭

### 빠른 테스트
```bash
# 기본 설정 테스트
python test_quick.py

# 결과: 5초 이내
```

### 반복 실험
```bash
# 10회 반복 (통계 분석용)
for i in {1..10}; do
    python main.py --scenario compare --quiet
done
```

### CSV 출력 (향후 지원)
```bash
# 결과를 CSV로 저장
python main.py --scenario compare --output results.csv
```

---

## 📚 추가 문서

- **상세 연구 문서**: [RESEARCH_DOCUMENTATION.md](RESEARCH_DOCUMENTATION.md)
- **개선 사항 요약**: [IMPROVEMENT_SUMMARY.md](IMPROVEMENT_SUMMARY.md)
- **시스템 매뉴얼**: [SYSTEM_MANUAL_NOTION.md](SYSTEM_MANUAL_NOTION.md)

---

## 🆘 도움이 필요하면

1. **GitHub Issues**: 버그 리포트 및 기능 제안
2. **이메일**: 프로젝트 담당자에게 문의
3. **문서**: `docs/` 폴더의 상세 문서 참조

---

**최종 업데이트**: 2025-01-20
**버전**: v2.0
