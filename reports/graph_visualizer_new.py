"""
matplotlib 기반 그래프 시각화 - 한글 폰트 직접 로드 방식
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from pathlib import Path
import os
import warnings


class GraphVisualizer:
    """그래프 시각화 클래스"""

    def __init__(self):
        """초기화 및 한글 폰트 설정"""
        # 한글 폰트 설정 (직접 TTF 파일 로드)
        self._setup_korean_font_direct()

        # 기본 스타일
        plt.style.use('seaborn-v0_8-darkgrid')

        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)

    def _setup_korean_font_direct(self):
        """한글 폰트 직접 로드 - TTF 파일 경로 지정"""
        # 경고 메시지 전부 숨기기
        warnings.filterwarnings('ignore')

        # Windows 폰트 경로
        font_path = r'C:\Windows\Fonts\malgun.ttf'

        if os.path.exists(font_path):
            # 폰트 파일 직접 등록
            font_prop = fm.FontProperties(fname=font_path)

            # matplotlib 전역 설정
            plt.rcParams['font.family'] = font_prop.get_name()
            plt.rcParams['axes.unicode_minus'] = False

            print(f"[INFO] Korean font loaded directly: {font_path}")
        else:
            print("[ERROR] Malgun Gothic font file not found!")
            print("[INFO] Trying fallback fonts...")

            # 대체 폰트
            for font_name in ['Malgun Gothic', 'Gulim', 'Batang', 'Dotum']:
                try:
                    plt.rcParams['font.family'] = font_name
                    plt.rcParams['axes.unicode_minus'] = False
                    print(f"[INFO] Using fallback font: {font_name}")
                    return
                except:
                    continue

    def plot_comparison_bars(self, metrics_off, metrics_on, save_path=None):
        """BIM ON/OFF 비교 막대 그래프"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # 한글 폰트 직접 지정 (추가 보장)
        font_path = r'C:\Windows\Fonts\malgun.ttf'
        if os.path.exists(font_path):
            font_prop = fm.FontProperties(fname=font_path)
        else:
            font_prop = fm.FontProperties()

        fig.suptitle('BIM 적용 효과 비교 분석', fontproperties=font_prop, fontsize=16, fontweight='bold')

        # 1. 공사 지연 비교
        ax1 = axes[0, 0]
        delays = [metrics_off['delay_weeks'], metrics_on['delay_weeks']]
        colors = ['#ff6b6b', '#51cf66']
        bars1 = ax1.bar(['BIM OFF', 'BIM ON'], delays, color=colors, alpha=0.7, edgecolor='black')
        ax1.set_ylabel('지연 (주)', fontproperties=font_prop, fontsize=12)
        ax1.set_title('공사 지연 비교', fontproperties=font_prop, fontsize=13, fontweight='bold')
        ax1.grid(axis='y', alpha=0.3)

        # 값 표시
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}주',
                    ha='center', va='bottom', fontproperties=font_prop, fontsize=11, fontweight='bold')

        # 2. 예산 초과율 비교
        ax2 = axes[0, 1]
        overruns = [metrics_off['budget_overrun_rate']*100, metrics_on['budget_overrun_rate']*100]
        bars2 = ax2.bar(['BIM OFF', 'BIM ON'], overruns, color=colors, alpha=0.7, edgecolor='black')
        ax2.set_ylabel('예산 초과율 (%)', fontproperties=font_prop, fontsize=12)
        ax2.set_title('예산 초과율 비교', fontproperties=font_prop, fontsize=13, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)

        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%',
                    ha='center', va='bottom', fontproperties=font_prop, fontsize=11, fontweight='bold')

        # 3. 이슈 탐지율 비교
        ax3 = axes[1, 0]
        detection = [metrics_off['detection_rate']*100, metrics_on['detection_rate']*100]
        bars3 = ax3.bar(['BIM OFF', 'BIM ON'], detection, color=colors, alpha=0.7, edgecolor='black')
        ax3.set_ylabel('탐지율 (%)', fontproperties=font_prop, fontsize=12)
        ax3.set_title('이슈 탐지율 비교', fontproperties=font_prop, fontsize=13, fontweight='bold')
        ax3.grid(axis='y', alpha=0.3)
        ax3.set_ylim(0, 100)

        for bar in bars3:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%',
                    ha='center', va='bottom', fontproperties=font_prop, fontsize=11, fontweight='bold')

        # 4. 총 비용 증가 비교
        ax4 = axes[1, 1]
        costs = [metrics_off['cost_increase']/1e8, metrics_on['cost_increase']/1e8]
        bars4 = ax4.bar(['BIM OFF', 'BIM ON'], costs, color=colors, alpha=0.7, edgecolor='black')
        ax4.set_ylabel('비용 증가 (억원)', fontproperties=font_prop, fontsize=12)
        ax4.set_title('총 비용 증가 비교', fontproperties=font_prop, fontsize=13, fontweight='bold')
        ax4.grid(axis='y', alpha=0.3)

        for bar in bars4:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}억',
                    ha='center', va='bottom', fontproperties=font_prop, fontsize=11, fontweight='bold')

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
