"""
matplotlib 기반 그래프 시각화
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from pathlib import Path


class GraphVisualizer:
    """그래프 시각화 클래스"""

    def __init__(self):
        """초기화 및 한글 폰트 설정"""
        # 한글 폰트 설정 (Windows)
        self._setup_korean_font()

        # 기본 스타일
        plt.style.use('seaborn-v0_8-darkgrid')

        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)

    def _setup_korean_font(self):
        """한글 폰트 설정 (Windows 환경)"""
        import os
        import warnings

        # matplotlib 폰트 캐시 강제 삭제 (한글 폰트 인식 문제 해결)
        import matplotlib
        cache_dir = matplotlib.get_cachedir()
        cache_file = os.path.join(cache_dir, 'fontlist-v330.json')
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
            except:
                pass

        # 폰트 매니저 리로드
        fm._load_fontmanager(try_read_cache=False)

        # Windows에서 사용 가능한 한글 폰트 목록 (우선순위)
        korean_fonts = [
            'Malgun Gothic',
            'NanumGothic',
            'NanumBarunGothic',
            'Gulim',
            'Dotum',
            'Batang',
            'Gungsuh'
        ]

        # 시스템에 설치된 폰트 목록
        available_fonts = set([f.name for f in fm.fontManager.ttflist])

        # 사용 가능한 한글 폰트 찾기
        selected_font = None
        for font in korean_fonts:
            if font in available_fonts:
                selected_font = font
                break

        if selected_font:
            # 폰트 설정 (여러 방법 동시 적용)
            plt.rcParams['font.family'] = selected_font
            plt.rcParams['font.sans-serif'] = [selected_font]
            plt.rcParams['axes.unicode_minus'] = False

            # Glyph missing 경고 숨기기
            warnings.filterwarnings('ignore', category=UserWarning,
                                  message='.*Glyph.*missing from current font.*')

            print(f"[INFO] Korean font set: {selected_font}")
        else:
            # 폰트를 찾지 못한 경우
            print("[WARNING] No Korean font found. Korean text may not display correctly.")
            print("[INFO] Please install: Malgun Gothic or NanumGothic")
            plt.rcParams['axes.unicode_minus'] = False

    def plot_comparison_bars(self, metrics_off, metrics_on, save_path=None):
        """BIM ON/OFF 비교 막대 그래프"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('BIM 적용 효과 비교 분석', fontsize=16, fontweight='bold')

        # 1. 공사 지연 비교
        ax1 = axes[0, 0]
        delays = [metrics_off['delay_weeks'], metrics_on['delay_weeks']]
        colors = ['#ff6b6b', '#51cf66']
        bars1 = ax1.bar(['BIM OFF', 'BIM ON'], delays, color=colors, alpha=0.7, edgecolor='black')
        ax1.set_ylabel('지연 (주)', fontsize=12)
        ax1.set_title('공사 지연 비교', fontsize=13, fontweight='bold')
        ax1.grid(axis='y', alpha=0.3)

        # 값 표시
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}주',
                    ha='center', va='bottom', fontsize=11, fontweight='bold')

        # 2. 예산 초과율 비교
        ax2 = axes[0, 1]
        overruns = [metrics_off['budget_overrun_rate']*100, metrics_on['budget_overrun_rate']*100]
        bars2 = ax2.bar(['BIM OFF', 'BIM ON'], overruns, color=colors, alpha=0.7, edgecolor='black')
        ax2.set_ylabel('예산 초과율 (%)', fontsize=12)
        ax2.set_title('예산 초과율 비교', fontsize=13, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)

        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%',
                    ha='center', va='bottom', fontsize=11, fontweight='bold')

        # 3. 이슈 탐지율 비교
        ax3 = axes[1, 0]
        detection = [metrics_off['detection_rate']*100, metrics_on['detection_rate']*100]
        bars3 = ax3.bar(['BIM OFF', 'BIM ON'], detection, color=colors, alpha=0.7, edgecolor='black')
        ax3.set_ylabel('탐지율 (%)', fontsize=12)
        ax3.set_title('이슈 탐지율 비교', fontsize=13, fontweight='bold')
        ax3.grid(axis='y', alpha=0.3)
        ax3.set_ylim(0, 100)

        for bar in bars3:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%',
                    ha='center', va='bottom', fontsize=11, fontweight='bold')

        # 4. 총 비용 증가 비교
        ax4 = axes[1, 1]
        costs = [metrics_off['cost_increase']/1e8, metrics_on['cost_increase']/1e8]
        bars4 = ax4.bar(['BIM OFF', 'BIM ON'], costs, color=colors, alpha=0.7, edgecolor='black')
        ax4.set_ylabel('비용 증가 (억원)', fontsize=12)
        ax4.set_title('총 비용 증가 비교', fontsize=13, fontweight='bold')
        ax4.grid(axis='y', alpha=0.3)

        for bar in bars4:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}억',
                    ha='center', va='bottom', fontsize=11, fontweight='bold')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"\n그래프 저장: {save_path}")
        else:
            save_path = self.output_dir / "comparison_bars.png"
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"\n그래프 저장: {save_path}")

        plt.close()
        return save_path

    def plot_roi_analysis(self, metrics_off, metrics_on, bim_cost=50_000_000, save_path=None):
        """BIM 투자 ROI 분석 그래프"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle('BIM 투자 ROI 분석', fontsize=16, fontweight='bold')

        # 1. 비용 분석
        cost_saved = metrics_off['cost_increase'] - metrics_on['cost_increase']
        roi = (cost_saved - bim_cost) / bim_cost * 100

        categories = ['BIM OFF\n총비용', 'BIM ON\n총비용', 'BIM\n투자비', '절감액']
        values = [
            metrics_off['cost_increase']/1e8,
            metrics_on['cost_increase']/1e8,
            bim_cost/1e8,
            cost_saved/1e8
        ]
        colors_bar = ['#ff6b6b', '#51cf66', '#ffd43b', '#339af0']

        bars = ax1.bar(categories, values, color=colors_bar, alpha=0.7, edgecolor='black')
        ax1.set_ylabel('금액 (억원)', fontsize=12)
        ax1.set_title('비용 분석', fontsize=13, fontweight='bold')
        ax1.grid(axis='y', alpha=0.3)

        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}억',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

        # 2. ROI 원형 그래프
        if roi > 0:
            roi_display = min(roi, 500)  # 최대 500%로 제한 (시각화)
            colors_pie = ['#339af0', '#e9ecef']
            explode = (0.1, 0)

            ax2.pie([roi_display, 100],
                   labels=[f'ROI\n{roi:.0f}%', '투자'],
                   colors=colors_pie,
                   autopct='%1.0f%%',
                   explode=explode,
                   startangle=90,
                   textprops={'fontsize': 12, 'fontweight': 'bold'})
            ax2.set_title(f'투자 수익률 (ROI: {roi:.1f}%)', fontsize=13, fontweight='bold')
        else:
            ax2.text(0.5, 0.5, f'ROI: {roi:.1f}%\n(손실)',
                    ha='center', va='center', fontsize=20, fontweight='bold', color='red',
                    transform=ax2.transAxes)
            ax2.set_title('투자 수익률', fontsize=13, fontweight='bold')
            ax2.axis('off')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"그래프 저장: {save_path}")
        else:
            save_path = self.output_dir / "roi_analysis.png"
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"그래프 저장: {save_path}")

        plt.close()
        return save_path

    def plot_timeline(self, metrics_off, metrics_on, save_path=None):
        """공정 타임라인 비교"""
        fig, ax = plt.subplots(figsize=(12, 6))

        planned = 360  # 계획 일수
        actual_off = metrics_off['actual_duration']
        actual_on = metrics_on['actual_duration']

        # 막대 그래프
        y_pos = [0, 1, 2]
        durations = [planned, actual_off, actual_on]
        colors = ['#868e96', '#ff6b6b', '#51cf66']
        labels = ['계획 공기', 'BIM OFF 실제', 'BIM ON 실제']

        bars = ax.barh(y_pos, durations, color=colors, alpha=0.7, edgecolor='black', height=0.6)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=12)
        ax.set_xlabel('공사 기간 (일)', fontsize=12)
        ax.set_title('공사 기간 비교', fontsize=14, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)

        # 값 표시
        for i, (bar, duration) in enumerate(zip(bars, durations)):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f'{duration:.0f}일',
                   ha='left', va='center', fontsize=11, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

        # 계획 대비 지연 표시
        delay_off = actual_off - planned
        delay_on = actual_on - planned

        ax.text(planned + delay_off/2, 1, f'+{delay_off:.0f}일\n({metrics_off["delay_weeks"]:.1f}주)',
               ha='center', va='center', fontsize=10, color='darkred', fontweight='bold')
        ax.text(planned + delay_on/2, 2, f'+{delay_on:.0f}일\n({metrics_on["delay_weeks"]:.1f}주)',
               ha='center', va='center', fontsize=10, color='darkgreen', fontweight='bold')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"그래프 저장: {save_path}")
        else:
            save_path = self.output_dir / "timeline_comparison.png"
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"그래프 저장: {save_path}")

        plt.close()
        return save_path

    def plot_issue_breakdown(self, metrics_off, metrics_on, save_path=None):
        """이슈 발생/탐지 분석"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle('이슈 발생 및 탐지 분석', fontsize=16, fontweight='bold')

        # 1. BIM OFF 이슈 분석
        ax1 = axes[0]
        detected_off = metrics_off['detected_count']
        missed_off = metrics_off['missed_count']

        colors1 = ['#51cf66', '#ff6b6b']
        explode1 = (0.05, 0.05)
        sizes1 = [detected_off, missed_off]
        labels1 = [f'탐지\n{detected_off}건', f'미탐지\n{missed_off}건']

        ax1.pie(sizes1, labels=labels1, colors=colors1, autopct='%1.1f%%',
               explode=explode1, startangle=90,
               textprops={'fontsize': 11, 'fontweight': 'bold'})
        ax1.set_title(f'BIM OFF 이슈 탐지\n(총 {metrics_off["issues_count"]}건)',
                     fontsize=13, fontweight='bold')

        # 2. BIM ON 이슈 분석
        ax2 = axes[1]
        detected_on = metrics_on['detected_count']
        missed_on = metrics_on['missed_count']

        colors2 = ['#339af0', '#ffa94d']
        explode2 = (0.05, 0.05)
        sizes2 = [detected_on, missed_on]
        labels2 = [f'탐지\n{detected_on}건', f'미탐지\n{missed_on}건']

        ax2.pie(sizes2, labels=labels2, colors=colors2, autopct='%1.1f%%',
               explode=explode2, startangle=90,
               textprops={'fontsize': 11, 'fontweight': 'bold'})
        ax2.set_title(f'BIM ON 이슈 탐지\n(총 {metrics_on["issues_count"]}건)',
                     fontsize=13, fontweight='bold')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"그래프 저장: {save_path}")
        else:
            save_path = self.output_dir / "issue_breakdown.png"
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"그래프 저장: {save_path}")

        plt.close()
        return save_path

    def generate_all_graphs(self, metrics_off, metrics_on, bim_cost=50_000_000):
        """모든 그래프 생성"""
        print("\n" + "="*70)
        print("그래프 생성 중...")
        print("="*70)

        paths = []

        # 1. 비교 막대 그래프
        path1 = self.plot_comparison_bars(metrics_off, metrics_on)
        paths.append(path1)

        # 2. ROI 분석
        path2 = self.plot_roi_analysis(metrics_off, metrics_on, bim_cost)
        paths.append(path2)

        # 3. 타임라인 비교
        path3 = self.plot_timeline(metrics_off, metrics_on)
        paths.append(path3)

        # 4. 이슈 분석
        path4 = self.plot_issue_breakdown(metrics_off, metrics_on)
        paths.append(path4)

        print("\n" + "="*70)
        print(f"총 {len(paths)}개 그래프 생성 완료!")
        print("="*70 + "\n")

        return paths
