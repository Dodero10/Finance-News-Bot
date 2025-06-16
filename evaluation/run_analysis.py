#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script chạy phân tích và lưu kết quả
"""

import sys
import os
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

# Import class từ file analysis
sys.path.append(str(Path(__file__).parent))
from compare_agents_visualization import AgentEvaluator

def save_results_to_file(results_df, evaluator, output_dir):
    """Lưu kết quả phân tích vào file text"""
    
    results_file = output_dir / "analysis_results.txt"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        f.write("PHÂN TÍCH SO SÁNH CÁC AGENT THEO ĐỘ KHÓ\n")
        f.write("="*80 + "\n\n")
        
        f.write("CÁC METRICS ĐƯỢC ĐÁNH GIA:\n")
        f.write("- Accuracy: Tỉ lệ agent gọi tools hoàn toàn đúng (failed_tools_count = 0)\n")
        f.write("- F1 Score: Điểm F1 dựa trên việc gọi tool thành công\n")
        f.write("- Tool Fail Rate: Tỉ lệ gọi tool thất bại\n\n")
        
        f.write("BẢNG KẾT QUẢ CHI TIẾT:\n")
        f.write("-" * 80 + "\n")
        f.write(results_df.to_string(index=False))
        f.write("\n\n")
        
        f.write("TỔNG KẾT THEO AGENT (Trung bình):\n")
        f.write("-" * 80 + "\n")
        summary = results_df.groupby('Agent').agg({
            'Accuracy': 'mean',
            'F1_Score': 'mean',
            'Precision': 'mean',
            'Recall': 'mean',
            'Tool_Precision': 'mean',
            'Tool_Recall': 'mean',
            'Tool_Fail_Rate': 'mean',
            'Sample_Count': 'sum'
        }).round(3)
        f.write(summary.to_string())
        f.write("\n\n")
        
        f.write("XẾP HẠNG THEO METRICS:\n")
        f.write("-" * 80 + "\n")
        
        f.write("1. ACCURACY (cao nhất -> thấp nhất):\n")
        accuracy_ranking = summary.sort_values('Accuracy', ascending=False)
        for i, (agent, row) in enumerate(accuracy_ranking.iterrows(), 1):
            f.write(f"{i}. {agent}: {row['Accuracy']:.3f}\n")
        
        f.write("\n2. F1 SCORE (cao nhất -> thấp nhất):\n")
        f1_ranking = summary.sort_values('F1_Score', ascending=False)
        for i, (agent, row) in enumerate(f1_ranking.iterrows(), 1):
            f.write(f"{i}. {agent}: {row['F1_Score']:.3f}\n")
        
        f.write("\n3. TOOL SUCCESS RATE (thấp nhất fail rate -> cao nhất):\n")
        tool_ranking = summary.sort_values('Tool_Fail_Rate', ascending=True)
        for i, (agent, row) in enumerate(tool_ranking.iterrows(), 1):
            success_rate = 1 - row['Tool_Fail_Rate']
            f.write(f"{i}. {agent}: {success_rate:.3f} (fail rate: {row['Tool_Fail_Rate']:.3f})\n")
        
        f.write("\n\nKẾT LUẬN:\n")
        f.write("-" * 80 + "\n")
        
        # Tìm agent tốt nhất
        best_accuracy = accuracy_ranking.index[0]
        best_f1 = f1_ranking.index[0]
        best_tool = tool_ranking.index[0]
        
        f.write(f"- Agent tốt nhất về Accuracy: {best_accuracy} ({accuracy_ranking.loc[best_accuracy, 'Accuracy']:.3f})\n")
        f.write(f"- Agent tốt nhất về F1 Score: {best_f1} ({f1_ranking.loc[best_f1, 'F1_Score']:.3f})\n")
        f.write(f"- Agent ít lỗi tool nhất: {best_tool} (success rate: {1-tool_ranking.loc[best_tool, 'Tool_Fail_Rate']:.3f})\n")
        
        # Phân tích theo độ khó
        f.write("\nPHÂN TÍCH THEO ĐỘ KHÓ:\n")
        for difficulty in ['dễ', 'khó']:
            f.write(f"\nCâu hỏi {difficulty}:\n")
            diff_data = results_df[results_df['Difficulty'] == difficulty]
            diff_summary = diff_data.groupby('Agent')[['Accuracy', 'F1_Score', 'Tool_Fail_Rate']].mean()
            
            f.write(f"- Accuracy cao nhất: {diff_summary['Accuracy'].idxmax()} ({diff_summary['Accuracy'].max():.3f})\n")
            f.write(f"- F1 Score cao nhất: {diff_summary['F1_Score'].idxmax()} ({diff_summary['F1_Score'].max():.3f})\n")
            f.write(f"- Tool fail rate thấp nhất: {diff_summary['Tool_Fail_Rate'].idxmin()} ({diff_summary['Tool_Fail_Rate'].min():.3f})\n")

def create_readme(output_dir):
    """Tạo file README để giải thích kết quả"""
    readme_file = output_dir / "README.md"
    
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write("# Kết quả So sánh các Agent\n\n")
        
        f.write("## Cấu trúc thư mục\n\n")
        f.write("```\n")
        f.write("evaluation/results_visualization/figures/comprehensive/\n")
        f.write("├── README.md                          # File này - hướng dẫn đọc kết quả\n")
        f.write("├── analysis_results.txt               # Kết quả phân tích chi tiết dạng text\n")
        f.write("├── detailed_results.csv               # Dữ liệu chi tiết dạng CSV\n")
        f.write("├── agent_comparison_overview.png      # Biểu đồ tổng quan so sánh 4 metrics\n")
        f.write("└── agent_comparison_detailed.png      # Biểu đồ chi tiết theo độ khó\n")
        f.write("```\n\n")
        
        f.write("## Các Agent được đánh giá\n\n")
        f.write("1. **React Agent**: Kiến trúc ReAct cơ bản\n")
        f.write("2. **ReWOO Agent**: Kiến trúc ReWOO (Reasoning WithOut Observation)\n")
        f.write("3. **Reflexion Agent**: Kiến trúc Reflexion với khả năng self-reflection\n")
        f.write("4. **Multi-Agent**: Kiến trúc multi-agent do bạn đề xuất\n\n")
        
        f.write("## Metrics đánh giá\n\n")
        f.write("### 1. Accuracy\n")
        f.write("- **Định nghĩa**: Tỉ lệ agent gọi tools hoàn toàn đúng\n")
        f.write("- **Công thức**: (Số câu có failed_tools_count = 0) / Tổng số câu\n")
        f.write("- **Giải thích**: Đo lường khả năng gọi tool chính xác của agent\n\n")
        
        f.write("### 2. F1 Score\n")
        f.write("- **Định nghĩa**: Điểm F1 dựa trên việc gọi tool thành công\n")
        f.write("- **Công thức**: 2 * (Precision * Recall) / (Precision + Recall)\n")
        f.write("- **Giải thích**: Cân bằng giữa precision và recall trong việc sử dụng tools\n\n")
        
        f.write("### 3. Tool Fail Rate\n")
        f.write("- **Định nghĩa**: Tỉ lệ gọi tool thất bại\n")
        f.write("- **Công thức**: (Số câu có failed_tools_count > 0) / Tổng số câu có gọi tool\n")
        f.write("- **Giải thích**: Đo lường độ tin cậy khi sử dụng tools (thấp hơn = tốt hơn)\n\n")
        
        f.write("## Cách đọc kết quả\n\n")
        f.write("### Biểu đồ Overview (agent_comparison_overview.png)\n")
        f.write("- **Góc trên trái**: Accuracy theo độ khó\n")
        f.write("- **Góc trên phải**: F1 Score theo độ khó\n")
        f.write("- **Góc dưới trái**: Tool Fail Rate theo độ khó\n")
        f.write("- **Góc dưới phải**: Heatmap tổng quan (màu xanh = tốt, màu đỏ = kém)\n\n")
        
        f.write("### Biểu đồ Detailed (agent_comparison_detailed.png)\n")
        f.write("- So sánh trực tiếp giữa câu hỏi dễ và khó cho từng metric\n")
        f.write("- Cột xanh: Câu hỏi dễ\n")
        f.write("- Cột cam: Câu hỏi khó\n\n")
        
        f.write("## Files kết quả\n\n")
        f.write("### analysis_results.txt\n")
        f.write("- Chứa toàn bộ kết quả phân tích dạng text\n")
        f.write("- Bảng xếp hạng theo từng metric\n")
        f.write("- Kết luận và nhận xét\n\n")
        
        f.write("### detailed_results.csv\n")
        f.write("- Dữ liệu chi tiết để phân tích thêm\n")
        f.write("- Có thể import vào Excel/Python để xử lý thêm\n\n")
        
        f.write("## Cách hiểu kết quả\n\n")
        f.write("1. **Agent tốt nhất tổng thể**: Xem xếp hạng trung bình các metrics\n")
        f.write("2. **Agent ổn định nhất**: Agent có hiệu suất đều giữa câu dễ và khó\n")
        f.write("3. **Agent phù hợp câu khó**: Xem hiệu suất riêng với difficulty = 'khó'\n")
        f.write("4. **Agent đáng tin cậy nhất**: Agent có Tool Fail Rate thấp nhất\n")

def main():
    print("Bắt đầu phân tích và tạo biểu đồ...")
    
    # Đường dẫn đến folder chứa file kết quả
    data_path = Path("evaluation/data_eval/results")
    
    # Tạo evaluator
    evaluator = AgentEvaluator(data_path)
    
    # Phân tích theo độ khó
    print("Đang phân tích dữ liệu...")
    results_df = evaluator.analyze_by_difficulty()
    
    # Tạo thư mục output
    output_dir = Path("evaluation/results_visualization/figures/comprehensive")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Đang tạo biểu đồ...")
    # Tạo biểu đồ so sánh
    fig1 = evaluator.create_comparison_plots(results_df)
    
    # Tạo biểu đồ chi tiết
    fig2 = evaluator.create_detailed_comparison(results_df)
    
    # Lưu biểu đồ
    fig1.savefig(output_dir / "agent_comparison_overview.png", dpi=300, bbox_inches='tight')
    fig2.savefig(output_dir / "agent_comparison_detailed.png", dpi=300, bbox_inches='tight')
    
    print("Đang lưu kết quả...")
    # Lưu kết quả vào file
    save_results_to_file(results_df, evaluator, output_dir)
    
    # Lưu CSV
    results_df.to_csv(output_dir / "detailed_results.csv", index=False, encoding='utf-8')
    
    # Tạo README
    create_readme(output_dir)
    
    print(f"\n✅ HOÀN THÀNH! Kết quả đã được lưu tại:")
    print(f"📁 {output_dir}")
    print(f"\n📋 Các file đã tạo:")
    print(f"   📄 README.md - Hướng dẫn đọc kết quả")
    print(f"   📄 analysis_results.txt - Kết quả phân tích chi tiết")
    print(f"   📄 detailed_results.csv - Dữ liệu chi tiết")
    print(f"   🖼️ agent_comparison_overview.png - Biểu đồ tổng quan")
    print(f"   🖼️ agent_comparison_detailed.png - Biểu đồ chi tiết")
    
    # In tóm tắt nhanh
    print(f"\n📊 TÓM TẮT NHANH:")
    summary = results_df.groupby('Agent').agg({
        'Accuracy': 'mean',
        'F1_Score': 'mean',
        'Precision': 'mean', 
        'Recall': 'mean',
        'Tool_Precision': 'mean',
        'Tool_Recall': 'mean',
        'Tool_Fail_Rate': 'mean'
    }).round(3)
    
    print("\n🎯 XẾP HẠNG ACCURACY:")
    for i, (agent, row) in enumerate(summary.sort_values('Accuracy', ascending=False).iterrows(), 1):
        print(f"   {i}. {agent}: {row['Accuracy']:.3f}")
    
    print("\n🎯 XẾP HẠNG F1 SCORE:")
    for i, (agent, row) in enumerate(summary.sort_values('F1_Score', ascending=False).iterrows(), 1):
        print(f"   {i}. {agent}: {row['F1_Score']:.3f} (P: {row['Precision']:.3f}, R: {row['Recall']:.3f})")
    
    print("\n🎯 XẾP HẠNG TOOL PRECISION:")
    for i, (agent, row) in enumerate(summary.sort_values('Tool_Precision', ascending=False).iterrows(), 1):
        print(f"   {i}. {agent}: {row['Tool_Precision']:.3f}")
    
    print("\n🎯 XẾP HẠNG TOOL RECALL:")
    for i, (agent, row) in enumerate(summary.sort_values('Tool_Recall', ascending=False).iterrows(), 1):
        print(f"   {i}. {agent}: {row['Tool_Recall']:.3f}")
    
    print("\n🎯 XẾP HẠNG TOOL SUCCESS (thấp fail rate = tốt):")
    for i, (agent, row) in enumerate(summary.sort_values('Tool_Fail_Rate', ascending=True).iterrows(), 1):
        success_rate = 1 - row['Tool_Fail_Rate']
        print(f"   {i}. {agent}: {success_rate:.3f}")
    
    return results_df

if __name__ == "__main__":
    results = main() 