#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script chính để chạy analysis so sánh các agent và lưu kết quả có tổ chức
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import seaborn as sns
import numpy as np
from datetime import datetime

# Import helper functions
from utils.analysis_helper import (
    AgentAnalyzer, 
    create_folder_structure,
    save_metrics_separately,
    create_individual_rankings,
    save_detailed_reports,
    save_failed_cases_analysis
)

def create_visualization_charts(results_df, base_path="evaluation_analysis/results/visualizations"):
    """Tạo tất cả biểu đồ và lưu riêng biệt"""
    base_path = Path(base_path)
    
    # Style setup
    plt.style.use('seaborn-v0_8')
    colors = {'React': '#FF6B6B', 'ReWOO': '#4ECDC4', 'Reflexion': '#45B7D1', 'Multi-Agent': '#96CEB4'}
    
    # 1. Accuracy Comparison
    fig, ax = plt.subplots(figsize=(12, 8))
    accuracy_pivot = results_df.pivot(index='Agent', columns='Difficulty', values='Accuracy')
    accuracy_pivot.plot(kind='bar', ax=ax, color=['#FF9999', '#FF6666'], width=0.8)
    ax.set_title('So sánh Accuracy theo Agent và Độ khó', fontsize=16, fontweight='bold', pad=20)
    ax.set_ylabel('Accuracy', fontsize=12)
    ax.set_xlabel('Agent', fontsize=12)
    ax.legend(title='Độ khó', title_fontsize=12, fontsize=11)
    ax.tick_params(axis='x', rotation=45)
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for container in ax.containers:
        ax.bar_label(container, fmt='%.3f', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(base_path / "accuracy_comparison.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. F1 Score Comparison
    fig, ax = plt.subplots(figsize=(12, 8))
    f1_pivot = results_df.pivot(index='Agent', columns='Difficulty', values='F1_Score')
    f1_pivot.plot(kind='bar', ax=ax, color=['#99CCFF', '#6699FF'], width=0.8)
    ax.set_title('So sánh F1 Score theo Agent và Độ khó', fontsize=16, fontweight='bold', pad=20)
    ax.set_ylabel('F1 Score', fontsize=12)
    ax.set_xlabel('Agent', fontsize=12)
    ax.legend(title='Độ khó', title_fontsize=12, fontsize=11)
    ax.tick_params(axis='x', rotation=45)
    ax.grid(axis='y', alpha=0.3)
    
    for container in ax.containers:
        ax.bar_label(container, fmt='%.3f', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(base_path / "f1_score_comparison.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. Tool Performance Heatmap
    fig, ax = plt.subplots(figsize=(12, 8))
    summary = results_df.groupby('Agent')[['Accuracy', 'F1_Score', 'Precision', 'Recall']].mean()
    summary['Tool_Success_Rate'] = 1 - results_df.groupby('Agent')['Tool_Fail_Rate'].mean()
    
    sns.heatmap(summary.T, annot=True, fmt='.3f', cmap='RdYlGn', 
                ax=ax, cbar_kws={'label': 'Score'}, square=True)
    ax.set_title('Heatmap Hiệu suất Tool theo Agent', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Agent', fontsize=12)
    ax.set_ylabel('Metrics', fontsize=12)
    
    plt.tight_layout()
    plt.savefig(base_path / "tool_metrics_heatmap.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. Difficulty Analysis
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Accuracy by difficulty
    easy_data = results_df[results_df['Difficulty'] == 'dễ']
    hard_data = results_df[results_df['Difficulty'] == 'khó']
    
    x = np.arange(len(easy_data))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, easy_data['Accuracy'], width, label='Dễ', color='lightgreen', alpha=0.8)
    bars2 = ax1.bar(x + width/2, hard_data['Accuracy'], width, label='Khó', color='lightcoral', alpha=0.8)
    
    ax1.set_xlabel('Agent', fontsize=12)
    ax1.set_ylabel('Accuracy', fontsize=12)
    ax1.set_title('Accuracy theo Độ khó', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(easy_data['Agent'], rotation=45)
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax1.annotate(f'{height:.3f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)
    
    # F1 Score by difficulty
    bars3 = ax2.bar(x - width/2, easy_data['F1_Score'], width, label='Dễ', color='lightblue', alpha=0.8)
    bars4 = ax2.bar(x + width/2, hard_data['F1_Score'], width, label='Khó', color='orange', alpha=0.8)
    
    ax2.set_xlabel('Agent', fontsize=12)
    ax2.set_ylabel('F1 Score', fontsize=12) 
    ax2.set_title('F1 Score theo Độ khó', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(easy_data['Agent'], rotation=45)
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)
    
    for bars in [bars3, bars4]:
        for bar in bars:
            height = bar.get_height()
            ax2.annotate(f'{height:.3f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(base_path / "difficulty_analysis.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    # 5. Overall Dashboard (4-panel view)
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Dashboard Tổng quan - So sánh hiệu suất các Agent', fontsize=18, fontweight='bold')
    
    # Panel 1: Accuracy
    ax = axes[0, 0]
    accuracy_pivot.plot(kind='bar', ax=ax, color=['#FF9999', '#FF6666'])
    ax.set_title('Accuracy', fontweight='bold')
    ax.set_ylabel('Score')
    ax.tick_params(axis='x', rotation=45)
    ax.legend(title='Độ khó')
    
    # Panel 2: F1 Score
    ax = axes[0, 1]
    f1_pivot.plot(kind='bar', ax=ax, color=['#99CCFF', '#6699FF'])
    ax.set_title('F1 Score', fontweight='bold')
    ax.set_ylabel('Score')
    ax.tick_params(axis='x', rotation=45)
    ax.legend(title='Độ khó')
    
    # Panel 3: Tool Fail Rate
    ax = axes[1, 0]
    fail_rate_pivot = results_df.pivot(index='Agent', columns='Difficulty', values='Tool_Fail_Rate')
    fail_rate_pivot.plot(kind='bar', ax=ax, color=['#FFB366', '#FF8C42'])
    ax.set_title('Tool Fail Rate (Thấp hơn = Tốt hơn)', fontweight='bold')
    ax.set_ylabel('Fail Rate')
    ax.tick_params(axis='x', rotation=45)
    ax.legend(title='Độ khó')
    
    # Panel 4: Overall Heatmap
    ax = axes[1, 1]
    overview_data = results_df.groupby('Agent')[['Accuracy', 'F1_Score']].mean()
    overview_data['Tool_Success'] = 1 - results_df.groupby('Agent')['Tool_Fail_Rate'].mean()
    sns.heatmap(overview_data.T, annot=True, fmt='.3f', cmap='RdYlGn', ax=ax)
    ax.set_title('Tổng quan (Cao hơn = Tốt hơn)', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(base_path / "overall_dashboard.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"📊 Created all visualizations in {base_path}")

def create_technical_details_report(results_df, analyzer, base_path="evaluation_analysis/results/detailed_reports"):
    """Tạo báo cáo chi tiết kỹ thuật"""
    base_path = Path(base_path)
    
    with open(base_path / "technical_details.txt", 'w', encoding='utf-8') as f:
        f.write("🔧 BÁO CÁO CHI TIẾT KỸ THUẬT\n")
        f.write("="*50 + "\n\n")
        
        f.write("📊 PHƯƠNG PHÁP TÍNH TOÁN:\n")
        f.write("-" * 30 + "\n")
        f.write("1. ACCURACY:\n")
        f.write("   - Công thức: (Số câu có failed_tools_count = 0) / Tổng số câu\n")
        f.write("   - Ý nghĩa: Tỉ lệ agent gọi tools hoàn toàn đúng, không có lỗi\n\n")
        
        f.write("2. F1 SCORE:\n")
        f.write("   - Dựa trên ground truth từ synthetic_news.csv\n")
        f.write("   - TP: Tools được gọi đúng và cần thiết\n")
        f.write("   - FP: Tools được gọi nhưng không cần thiết (thừa)\n")
        f.write("   - FN: Tools cần thiết nhưng không được gọi (thiếu)\n")
        f.write("   - Precision = TP / (TP + FP)\n")
        f.write("   - Recall = TP / (TP + FN)\n")
        f.write("   - F1 = 2 * (Precision * Recall) / (Precision + Recall)\n\n")
        
        f.write("3. TOOL FAIL RATE:\n")
        f.write("   - Công thức: (Số câu có failed_tools_count > 0) / Tổng số câu có gọi tools\n")
        f.write("   - Ý nghĩa: Tỉ lệ lỗi khi agent thực thi tools\n\n")
        
        f.write("📈 THỐNG KÊ CHI TIẾT:\n")
        f.write("-" * 30 + "\n")
        
        # Chi tiết theo agent
        for agent in results_df['Agent'].unique():
            agent_data = results_df[results_df['Agent'] == agent]
            f.write(f"\n🤖 {agent}:\n")
            
            for difficulty in ['dễ', 'khó']:
                diff_data = agent_data[agent_data['Difficulty'] == difficulty]
                if len(diff_data) > 0:
                    row = diff_data.iloc[0]
                    f.write(f"   📝 Câu {difficulty}:\n")
                    f.write(f"      - Số mẫu: {row['Sample_Count']}\n")
                    f.write(f"      - Accuracy: {row['Accuracy']:.4f} ({row['Accuracy']*100:.2f}%)\n")
                    f.write(f"      - F1 Score: {row['F1_Score']:.4f}\n")
                    f.write(f"      - Precision: {row['Precision']:.4f}\n")
                    f.write(f"      - Recall: {row['Recall']:.4f}\n")
                    f.write(f"      - Tool Fail Rate: {row['Tool_Fail_Rate']:.4f} ({row['Tool_Fail_Rate']*100:.2f}%)\n")
        
        f.write(f"\n📋 GROUND TRUTH INFORMATION:\n")
        f.write("-" * 30 + "\n")
        f.write(f"Số lượng ground truth queries: {len(analyzer.ground_truth_tools)}\n")
        f.write("Tools được sử dụng trong ground truth:\n")
        all_tools = set()
        for tools in analyzer.ground_truth_tools.values():
            all_tools.update(tools)
        for tool in sorted(all_tools):
            f.write(f"   - {tool}\n")

def create_full_analysis_report(results_df, base_path="evaluation_analysis/results/detailed_reports"):
    """Tạo báo cáo phân tích đầy đủ"""
    base_path = Path(base_path)
    
    with open(base_path / "full_analysis_report.txt", 'w', encoding='utf-8') as f:
        f.write("📊 BÁO CÁO PHÂN TÍCH ĐẦY ĐỦ - SO SÁNH HIỆU SUẤT CÁC AGENT\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"📅 Thời gian tạo báo cáo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("📋 TỔNG QUAN DỮ LIỆU:\n")
        f.write("-" * 40 + "\n")
        total_samples = results_df['Sample_Count'].sum()
        agents_count = len(results_df['Agent'].unique())
        f.write(f"• Tổng số mẫu đánh giá: {total_samples}\n")
        f.write(f"• Số agent được so sánh: {agents_count}\n")
        f.write(f"• Số độ khó: {len(results_df['Difficulty'].unique())}\n")
        f.write(f"• Metrics đánh giá: Accuracy, F1 Score, Precision, Recall, Tool Fail Rate\n\n")
        
        f.write("📊 BẢNG KẾT QUẢ CHI TIẾT:\n")
        f.write("-" * 40 + "\n")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.float_format', '{:.4f}'.format)
        f.write(results_df.to_string(index=False))
        f.write("\n\n")
        
        f.write("📈 PHÂN TÍCH THEO AGENT:\n")
        f.write("-" * 40 + "\n")
        summary = results_df.groupby('Agent').agg({
            'Accuracy': ['mean', 'std'],
            'F1_Score': ['mean', 'std'],
            'Tool_Fail_Rate': ['mean', 'std']
        }).round(4)
        
        for agent in summary.index:
            f.write(f"\n🤖 {agent}:\n")
            f.write(f"   • Accuracy: {summary.loc[agent, ('Accuracy', 'mean')]:.4f} ± {summary.loc[agent, ('Accuracy', 'std')]:.4f}\n")
            f.write(f"   • F1 Score: {summary.loc[agent, ('F1_Score', 'mean')]:.4f} ± {summary.loc[agent, ('F1_Score', 'std')]:.4f}\n")
            f.write(f"   • Tool Fail Rate: {summary.loc[agent, ('Tool_Fail_Rate', 'mean')]:.4f} ± {summary.loc[agent, ('Tool_Fail_Rate', 'std')]:.4f}\n")
        
        f.write("\n📊 PHÂN TÍCH THEO ĐỘ KHÓ:\n")
        f.write("-" * 40 + "\n")
        
        for difficulty in ['dễ', 'khó']:
            diff_data = results_df[results_df['Difficulty'] == difficulty]
            f.write(f"\n📝 Câu {difficulty}:\n")
            f.write(f"   • Accuracy trung bình: {diff_data['Accuracy'].mean():.4f}\n")
            f.write(f"   • F1 Score trung bình: {diff_data['F1_Score'].mean():.4f}\n")
            f.write(f"   • Tool Fail Rate trung bình: {diff_data['Tool_Fail_Rate'].mean():.4f}\n")
            f.write(f"   • Agent tốt nhất (Accuracy): {diff_data.loc[diff_data['Accuracy'].idxmax(), 'Agent']}\n")
            f.write(f"   • Agent tốt nhất (F1): {diff_data.loc[diff_data['F1_Score'].idxmax(), 'Agent']}\n")

def main():
    parser = argparse.ArgumentParser(description='Chạy analysis so sánh các agent')
    parser.add_argument('--charts-only', action='store_true', help='Chỉ tạo biểu đồ')
    parser.add_argument('--metrics-only', action='store_true', help='Chỉ tính metrics')
    args = parser.parse_args()
    
    print("🚀 BẮT ĐẦU ANALYSIS SO SÁNH CÁC AGENT")
    print("="*50)
    
    # Tạo cấu trúc thư mục
    print("\n📁 Tạo cấu trúc thư mục...")
    create_folder_structure()
    
    # Initialize analyzer
    analyzer = AgentAnalyzer("data_eval/results")
    
    # Load data
    print("\n📥 Loading dữ liệu...")
    if not analyzer.load_agent_data():
        print("❌ Không thể load dữ liệu agent!")
        return
    
    if not analyzer.load_ground_truth("data_eval/synthetic_data/synthetic_news.csv"):
        print("❌ Không thể load ground truth!")
        return
    
    # Analyze by difficulty
    print("\n🔍 Phân tích theo độ khó...")
    results_df = analyzer.analyze_by_difficulty()
    failed_cases_df = analyzer.analyze_failed_cases()
    
    if not args.charts_only:
        # Save metrics separately
        print("\n💾 Lưu metrics...")
        save_metrics_separately(results_df)
        
        # Create rankings
        print("\n🏆 Tạo rankings...")
        create_individual_rankings(results_df)
        
        # Save raw data
        print("\n💿 Lưu raw data...")
        results_df.to_csv("evaluation_analysis/results/raw_data/complete_results.csv", index=False)
        save_failed_cases_analysis(failed_cases_df)
        
        # Create detailed reports
        print("\n📄 Tạo báo cáo chi tiết...")
        save_detailed_reports(results_df, failed_cases_df)
        create_technical_details_report(results_df, analyzer)
        create_full_analysis_report(results_df)
    
    if not args.metrics_only:
        # Create visualizations
        print("\n📊 Tạo biểu đồ...")
        create_visualization_charts(results_df)
    
    print(f"\n✅ HOÀN THÀNH! Tất cả kết quả đã được lưu trong thư mục evaluation_analysis/results/")
    print("\n📋 Cách xem kết quả:")
    print("   • Xem ranking nhanh: evaluation_analysis/results/rankings/overall_ranking.txt")
    print("   • Xem báo cáo tóm tắt: evaluation_analysis/results/detailed_reports/executive_summary.txt")
    print("   • Xem biểu đồ: evaluation_analysis/results/visualizations/")
    print("   • Dữ liệu để phân tích thêm: evaluation_analysis/results/raw_data/complete_results.csv")
    
    return results_df

if __name__ == "__main__":
    results = main() 