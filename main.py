"""
건설 시뮬레이션 메인 실행 파일
"""

import random
import json
from pathlib import Path
from src.core.simulation_engine import ConstructionSimulation


def load_project_config():
    """project_config.json 파일에서 프로젝트 정보 로드"""
    config_file = Path(__file__).parent / "project_config.json"

    if not config_file.exists():
        raise FileNotFoundError(
            f"프로젝트 설정 파일을 찾을 수 없습니다: {config_file}\n"
            f"project_config.json 파일을 생성해주세요."
        )

    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    # 시뮬레이션에 필요한 정보만 추출
    project_info = {
        "location": config["location"],
        "floor_area_ratio": config["용적률"],
        "total_area": config["연면적_제곱미터"],
        "total_budget": config["총공사비_억원"],
        "planned_duration_days": config["계획공기_일수"],
        "building_type": config.get("building_type", "상업"),
        "ground_roughness": config.get("ground_roughness", "C"),
    }

    print(f"\n프로젝트 정보 로드 완료: {config['프로젝트명']}")
    print(f"  위치: {config['위치']}")
    print(f"  연면적: {config['연면적_제곱미터']}㎡ ({config['연면적_평']}평)")
    print(f"  총공사비: {config['총공사비_억원']}억원")
    print(f"  계획공기: {config['계획공기_개월']}개월 ({config['계획공기_일수']}일)")

    return project_info


def run_bim_simulation():
    """BIM 방식 시뮬레이션"""
    project_info = load_project_config()

    print("\n" + "=" * 70)
    print("BIM 방식 시뮬레이션")
    print("=" * 70)

    sim = ConstructionSimulation(project_info, method="BIM")
    result = sim.run_simulation(output_dir="results")

    print("\n【시뮬레이션 결과 요약】")
    print(f"목표 공기: {result['시뮬레이션결과']['목표공기']}")
    print(f"실제 소요: {result['시뮬레이션결과']['실제소요']}")
    print(f"누적 지연: {result['시뮬레이션결과']['누적지연']}")
    print(f"비용 증가: {result['시뮬레이션결과']['누적비용증가']}")
    print(f"총 이슈: {result['시뮬레이션결과']['총이슈수']}개")
    print(f"해결 완료: {result['시뮬레이션결과']['해결완료']}개")

    return result


def run_traditional_simulation():
    """전통 방식 시뮬레이션"""
    project_info = load_project_config()

    print("\n" + "=" * 70)
    print("전통 방식 시뮬레이션")
    print("=" * 70)

    sim = ConstructionSimulation(project_info, method="TRADITIONAL")
    result = sim.run_simulation(output_dir="results")

    print("\n【시뮬레이션 결과 요약】")
    print(f"목표 공기: {result['시뮬레이션결과']['목표공기']}")
    print(f"실제 소요: {result['시뮬레이션결과']['실제소요']}")
    print(f"누적 지연: {result['시뮬레이션결과']['누적지연']}")
    print(f"비용 증가: {result['시뮬레이션결과']['누적비용증가']}")
    print(f"총 이슈: {result['시뮬레이션결과']['총이슈수']}개")
    print(f"해결 완료: {result['시뮬레이션결과']['해결완료']}개")

    return result


def compare_results(bim_result, trad_result):
    """BIM vs 전통 방식 비교 및 리포트 저장"""
    import json
    from pathlib import Path
    from datetime import datetime

    print("\n" + "=" * 70)
    print("BIM vs 전통 방식 비교")
    print("=" * 70)

    bim_delay = float(bim_result['시뮬레이션결과']['누적지연'].replace('일', ''))
    trad_delay = float(trad_result['시뮬레이션결과']['누적지연'].replace('일', ''))

    bim_cost = float(bim_result['시뮬레이션결과']['누적비용증가'].replace('%', ''))
    trad_cost = float(trad_result['시뮬레이션결과']['누적비용증가'].replace('%', ''))

    bim_issues = bim_result['시뮬레이션결과']['총이슈수']
    trad_issues = trad_result['시뮬레이션결과']['총이슈수']

    print(f"\n【일정 비교】")
    print(f"  BIM:  {bim_delay:.1f}일 지연")
    print(f"  전통: {trad_delay:.1f}일 지연")
    print(f"  개선: {trad_delay - bim_delay:.1f}일 단축 ({(1 - bim_delay/trad_delay)*100:.1f}%)")

    print(f"\n【비용 비교】")
    print(f"  BIM:  {bim_cost:.2f}% 증가")
    print(f"  전통: {trad_cost:.2f}% 증가")
    print(f"  개선: {trad_cost - bim_cost:.2f}%p 절감")

    print(f"\n【이슈 발생 비교】")
    print(f"  BIM:  {bim_issues}개 발생")
    print(f"  전통: {trad_issues}개 발생")
    print(f"  개선: {trad_issues - bim_issues}개 감소 ({(1 - bim_issues/trad_issues)*100:.1f}%)")

    # 비교 리포트 저장
    comparison_report = {
        "시뮬레이션정보": {
            "실행일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "프로젝트": bim_result['프로젝트정보']['기본정보'],
        },
        "BIM방식": {
            "목표공기": bim_result['시뮬레이션결과']['목표공기'],
            "실제소요": bim_result['시뮬레이션결과']['실제소요'],
            "누적지연_일": bim_delay,
            "비용증가_퍼센트": bim_cost,
            "총이슈수": bim_issues,
            "해결완료": bim_result['시뮬레이션결과']['해결완료'],
        },
        "전통방식": {
            "목표공기": trad_result['시뮬레이션결과']['목표공기'],
            "실제소요": trad_result['시뮬레이션결과']['실제소요'],
            "누적지연_일": trad_delay,
            "비용증가_퍼센트": trad_cost,
            "총이슈수": trad_issues,
            "해결완료": trad_result['시뮬레이션결과']['해결완료'],
        },
        "BIM개선효과": {
            "일정단축_일": round(trad_delay - bim_delay, 1),
            "일정개선율_퍼센트": round((1 - bim_delay/trad_delay)*100, 1),
            "비용절감_퍼센트포인트": round(trad_cost - bim_cost, 2),
            "비용개선율_퍼센트": round((1 - bim_cost/trad_cost)*100, 1) if trad_cost > 0 else 0,
            "이슈감소_개수": trad_issues - bim_issues,
            "이슈개선율_퍼센트": round((1 - bim_issues/trad_issues)*100, 1),
        }
    }

    # results/ 폴더에 비교 리포트 저장
    result_dir = Path("results")
    result_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = result_dir / f"comparison_report_{timestamp}.json"

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(comparison_report, f, ensure_ascii=False, indent=2)

    print(f"\n비교 리포트 저장 완료: {report_file}")


def main():
    """메인 함수"""
    # 랜덤 시드 설정 (재현성)
    random.seed(42)

    print("\n" + "=" * 70)
    print("건설 시뮬레이션 프로그램")
    print("BIM vs 전통 방식 비교 분석")
    print("=" * 70)

    # 1. BIM 시뮬레이션
    bim_result = run_bim_simulation()

    # 2. 전통 방식 시뮬레이션
    trad_result = run_traditional_simulation()

    # 3. 비교 분석
    compare_results(bim_result, trad_result)

    print("\n" + "=" * 70)
    print("시뮬레이션 완료!")
    print("\n생성된 파일:")
    print("  - logs/bim_meetings_YYYYMMDD_HHMMSS.json (BIM 회의 로그)")
    print("  - logs/bim_issues_YYYYMMDD_HHMMSS.json (BIM 이슈 목록)")
    print("  - logs/traditional_meetings_YYYYMMDD_HHMMSS.json (전통 회의 로그)")
    print("  - logs/traditional_issues_YYYYMMDD_HHMMSS.json (전통 이슈 목록)")
    print("  - results/comparison_report_YYYYMMDD_HHMMSS.json (비교 리포트)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
