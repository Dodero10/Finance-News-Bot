#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper functions cho analysis agent evaluation
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import ast
import json

# Thiết lập font cho tiếng Việt
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

class AgentAnalyzer:
    def __init__(self, data_path="data_eval/results"):
        self.data_path = Path(data_path)
        self.agents_data = {}
        self.ground_truth_tools = {}
        
    def load_agent_data(self):
        """Load dữ liệu từ các file CSV kết quả evaluation"""
        agent_files = {
            'React': 'react_agent_eval_results.csv',
            'ReWOO': 'rewoo_agent_eval_results.csv', 
            'Reflexion': 'reflexion_agent_eval_results.csv',
            'Multi-Agent': 'multi_agent_eval_results.csv'
        }
        
        for agent_name, filename in agent_files.items():
            file_path = self.data_path / filename
            if file_path.exists():
                df = pd.read_csv(file_path)
                self.agents_data[agent_name] = df
                print(f"✅ Loaded {len(df)} records for {agent_name}")
            else:
                print(f"❌ File not found: {file_path}")
                
        return len(self.agents_data) > 0
    
    def load_ground_truth(self, synthetic_path="data_eval/synthetic_data/synthetic_news.csv"):
        """Load ground truth tools từ synthetic_news.csv"""
        synthetic_path = Path(synthetic_path)
        if not synthetic_path.exists():
            print(f"❌ Ground truth file not found: {synthetic_path}")
            return False
            
        df_truth = pd.read_csv(synthetic_path)
        for _, row in df_truth.iterrows():
            query = row['query']
            tools_str = row['tools']
            try:
                tools_list = ast.literal_eval(tools_str)
                self.ground_truth_tools[query] = set(tools_list)
            except:
                # Fallback parsing
                tools_clean = tools_str.strip("[]'\"").replace("'", "").replace('"', '')
                tools_list = [t.strip() for t in tools_clean.split(',') if t.strip()]
                self.ground_truth_tools[query] = set(tools_list)
        
        print(f"✅ Loaded ground truth for {len(self.ground_truth_tools)} queries")
        return True
    
    def parse_tools_used(self, tools_str):
        """Parse chuỗi tools thành set"""
        if pd.isna(tools_str) or tools_str.strip() == '':
            return set()
        
        tools = set()
        for tool in str(tools_str).split(','):
            tool = tool.strip()
            if tool:
                tools.add(tool)
        return tools
    
    def get_required_tools(self, query):
        """Lấy tools cần thiết từ ground truth"""
        if query in self.ground_truth_tools:
            return self.ground_truth_tools[query]
        
        # Tìm similar query
        for gt_query, gt_tools in self.ground_truth_tools.items():
            if query.strip() == gt_query.strip():
                return gt_tools
        
        return set()
    
    def calculate_accuracy(self, df):
        """Tính accuracy - tỉ lệ gọi tools hoàn toàn đúng dựa trên ground truth"""
        correct_count = 0
        total_questions = len(df)
        
        for _, row in df.iterrows():
            required_tools = self.get_required_tools(row['input'])
            used_tools = self.parse_tools_used(row['tools'])
            
            # Loại bỏ failed tools khỏi used_tools
            if row['failed_tools_count'] > 0 and not pd.isna(row['failed_tools']):
                failed_tools = self.parse_tools_used(row['failed_tools'])
                used_tools = used_tools - failed_tools
            
            # Kiểm tra xem có gọi đúng hoàn toàn không
            if used_tools == required_tools:
                correct_count += 1
        
        return correct_count / total_questions if total_questions > 0 else 0
    
    def calculate_f1_metrics(self, df):
        """
        Tính F1, Precision, Recall dựa trên ground truth từ synthetic_news.csv
        
        Precision = |Texp ∩ Tact| / |Tact| - Tỉ lệ tool được chọn là cần thiết
        Recall = |Texp ∩ Tact| / |Texp| - Tỉ lệ tool cần thiết đã được tìm thấy
        F1 = 2 * (Precision * Recall) / (Precision + Recall)
        """
        tp = fp = fn = 0
        
        for _, row in df.iterrows():
            # Lấy tools cần thiết từ ground truth (Texp)
            required_tools = self.get_required_tools(row['input'])
            # Lấy tools agent đã gọi (Tact)
            used_tools = self.parse_tools_used(row['tools'])
            
            # Loại bỏ failed tools khỏi Tact
            if row['failed_tools_count'] > 0 and not pd.isna(row['failed_tools']):
                failed_tools = self.parse_tools_used(row['failed_tools'])
                used_tools = used_tools - failed_tools
            
            # Tính TP, FP, FN
            tp += len(required_tools & used_tools)  # Tools đúng (gọi đúng và cần thiết)
            fp += len(used_tools - required_tools)  # Tools thừa (gọi nhưng không cần)
            fn += len(required_tools - used_tools)  # Tools thiếu (cần nhưng không gọi)
        
        # Tính metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return f1, precision, recall
    
    def calculate_tool_fail_rate(self, df):
        """Tính tỉ lệ gọi tool fail"""
        df_with_tools = df[df['tools'].notna() & (df['tools'].str.strip() != '')]
        if len(df_with_tools) == 0:
            return 0
        
        failed_calls = len(df_with_tools[df_with_tools['failed_tools_count'] > 0])
        return failed_calls / len(df_with_tools)
    
    def analyze_by_difficulty(self):
        """Phân tích metrics theo độ khó"""
        results = []
        
        for agent_name, df in self.agents_data.items():
            for difficulty in ['dễ', 'khó']:
                df_filtered = df[df['difficulty'] == difficulty]
                
                if len(df_filtered) > 0:
                    accuracy = self.calculate_accuracy(df_filtered)
                    f1, precision, recall = self.calculate_f1_metrics(df_filtered)
                    tool_fail_rate = self.calculate_tool_fail_rate(df_filtered)
                    
                    results.append({
                        'Agent': agent_name,
                        'Difficulty': difficulty,
                        'Accuracy': accuracy,
                        'F1_Score': f1,
                        'Precision': precision,
                        'Recall': recall,
                        'Tool_Fail_Rate': tool_fail_rate,
                        'Sample_Count': len(df_filtered)
                    })
        
        return pd.DataFrame(results)
    
    def analyze_failed_cases(self):
        """Phân tích các trường hợp thất bại"""
        failed_cases = []
        
        for agent_name, df in self.agents_data.items():
            failed_df = df[df['failed_tools_count'] > 0]
            
            for _, row in failed_df.iterrows():
                failed_cases.append({
                    'Agent': agent_name,
                    'Query': row['input'][:100] + '...' if len(row['input']) > 100 else row['input'],
                    'Difficulty': row['difficulty'],
                    'Failed_Tools': row['failed_tools'],
                    'Failed_Count': row['failed_tools_count'],
                    'All_Tools': row['tools']
                })
        
        return pd.DataFrame(failed_cases)

def create_folder_structure(base_path="results"):
    """Tạo cấu trúc thư mục"""
    base_path = Path(base_path)
    
    folders = [
        "metrics",
        "visualizations", 
        "rankings",
        "detailed_reports",
        "raw_data"
    ]
    
    for folder in folders:
        folder_path = base_path / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created folder: {folder_path}")

def save_metrics_separately(results_df, base_path="results/metrics"):
    """Lưu từng metric vào file riêng"""
    base_path = Path(base_path)
    
    # 1. Accuracy results
    accuracy_df = results_df[['Agent', 'Difficulty', 'Accuracy', 'Sample_Count']].copy()
    accuracy_df.to_csv(base_path / "accuracy_results.csv", index=False)
    
    # 2. F1 Score results
    f1_df = results_df[['Agent', 'Difficulty', 'F1_Score', 'Precision', 'Recall', 'Sample_Count']].copy()
    f1_df.to_csv(base_path / "f1_score_results.csv", index=False)
    
    # 3. Tool performance
    tool_df = results_df[['Agent', 'Difficulty', 'Tool_Fail_Rate', 'Sample_Count']].copy()
    tool_df['Tool_Success_Rate'] = 1 - tool_df['Tool_Fail_Rate']
    tool_df.to_csv(base_path / "tool_performance_results.csv", index=False)
    
    # 4. Summary metrics
    results_df.to_csv(base_path / "summary_metrics.csv", index=False)
    
    print(f"💾 Saved metrics to {base_path}")

def create_individual_rankings(results_df, base_path="results/rankings"):
    """Tạo file ranking riêng cho từng metric"""
    base_path = Path(base_path)
    
    summary = results_df.groupby('Agent').agg({
        'Accuracy': 'mean',
        'F1_Score': 'mean',
        'Precision': 'mean',
        'Recall': 'mean', 
        'Tool_Fail_Rate': 'mean'
    }).round(4)
    
    # Accuracy ranking
    with open(base_path / "accuracy_ranking.txt", 'w', encoding='utf-8') as f:
        f.write("🎯 XẾP HẠNG ACCURACY (Cao nhất → Thấp nhất)\n")
        f.write("="*50 + "\n\n")
        for i, (agent, row) in enumerate(summary.sort_values('Accuracy', ascending=False).iterrows(), 1):
            f.write(f"{i}. {agent}: {row['Accuracy']:.4f} ({row['Accuracy']*100:.2f}%)\n")
    
    # F1 Score ranking  
    with open(base_path / "f1_score_ranking.txt", 'w', encoding='utf-8') as f:
        f.write("🎯 XẾP HẠNG F1 SCORE (Cao nhất → Thấp nhất)\n")
        f.write("="*50 + "\n\n")
        for i, (agent, row) in enumerate(summary.sort_values('F1_Score', ascending=False).iterrows(), 1):
            f.write(f"{i}. {agent}: {row['F1_Score']:.4f}\n")
            f.write(f"   - Precision: {row['Precision']:.4f}\n")
            f.write(f"   - Recall: {row['Recall']:.4f}\n\n")
    
    # Precision ranking
    with open(base_path / "precision_ranking.txt", 'w', encoding='utf-8') as f:
        f.write("🎯 XẾP HẠNG PRECISION (Cao nhất → Thấp nhất)\n")
        f.write("="*50 + "\n")
        f.write("📊 Precision = |Texp ∩ Tact| / |Tact|\n")
        f.write("💡 Tỉ lệ tool được chọn là cần thiết (ít gọi thừa)\n\n")
        for i, (agent, row) in enumerate(summary.sort_values('Precision', ascending=False).iterrows(), 1):
            f.write(f"{i}. {agent}: {row['Precision']:.4f} ({row['Precision']*100:.2f}%)\n")
            if row['Precision'] < 0.7:
                f.write("   ⚠️  Thường gọi tools thừa\n")
            elif row['Precision'] > 0.9:
                f.write("   ✅ Rất ít gọi tools thừa\n")
            f.write("\n")
    
    # Recall ranking
    with open(base_path / "recall_ranking.txt", 'w', encoding='utf-8') as f:
        f.write("🎯 XẾP HẠNG RECALL (Cao nhất → Thấp nhất)\n")
        f.write("="*50 + "\n")
        f.write("📊 Recall = |Texp ∩ Tact| / |Texp|\n")
        f.write("💡 Tỉ lệ tool cần thiết đã được tìm thấy (ít bỏ sót)\n\n")
        for i, (agent, row) in enumerate(summary.sort_values('Recall', ascending=False).iterrows(), 1):
            f.write(f"{i}. {agent}: {row['Recall']:.4f} ({row['Recall']*100:.2f}%)\n")
            if row['Recall'] < 0.7:
                f.write("   ⚠️  Thường bỏ sót tools cần thiết\n")
            elif row['Recall'] > 0.9:
                f.write("   ✅ Rất ít bỏ sót tools\n")
            f.write("\n")
    
    # Tool performance ranking
    with open(base_path / "tool_performance_ranking.txt", 'w', encoding='utf-8') as f:
        f.write("🎯 XẾP HẠNG TOOL PERFORMANCE (Thấp fail rate → Cao fail rate)\n")
        f.write("="*60 + "\n\n")
        for i, (agent, row) in enumerate(summary.sort_values('Tool_Fail_Rate', ascending=True).iterrows(), 1):
            success_rate = 1 - row['Tool_Fail_Rate']
            f.write(f"{i}. {agent}:\n")
            f.write(f"   - Success Rate: {success_rate:.4f} ({success_rate*100:.2f}%)\n")
            f.write(f"   - Fail Rate: {row['Tool_Fail_Rate']:.4f} ({row['Tool_Fail_Rate']*100:.2f}%)\n\n")
    
    # Overall ranking (tổng hợp)
    with open(base_path / "overall_ranking.txt", 'w', encoding='utf-8') as f:
        f.write("🏆 XẾP HẠNG TỔNG THỂ\n")
        f.write("="*30 + "\n\n")
        
        # Tính điểm tổng hợp (normalized)
        normalized = summary.copy()
        normalized['Accuracy_norm'] = normalized['Accuracy'] / normalized['Accuracy'].max()
        normalized['F1_norm'] = normalized['F1_Score'] / normalized['F1_Score'].max()
        normalized['Tool_norm'] = (1 - normalized['Tool_Fail_Rate']) / (1 - normalized['Tool_Fail_Rate']).max()
        normalized['Overall_Score'] = (normalized['Accuracy_norm'] + normalized['F1_norm'] + normalized['Tool_norm']) / 3
        
        for i, (agent, row) in enumerate(normalized.sort_values('Overall_Score', ascending=False).iterrows(), 1):
            f.write(f"{i}. {agent}: {row['Overall_Score']:.4f}\n")
            f.write(f"   - Accuracy: {summary.loc[agent, 'Accuracy']:.4f}\n")
            f.write(f"   - F1 Score: {summary.loc[agent, 'F1_Score']:.4f}\n")
            f.write(f"   - Tool Success: {1-summary.loc[agent, 'Tool_Fail_Rate']:.4f}\n\n")
    
    print(f"📊 Created rankings in {base_path}")

def save_detailed_reports(results_df, failed_cases_df, base_path="results/detailed_reports"):
    """Tạo các báo cáo chi tiết"""
    base_path = Path(base_path)
    
    summary = results_df.groupby('Agent').agg({
        'Accuracy': 'mean',
        'F1_Score': 'mean',
        'Precision': 'mean',
        'Recall': 'mean',
        'Tool_Fail_Rate': 'mean',
        'Sample_Count': 'sum'
    }).round(4)
    
    # Executive Summary
    with open(base_path / "executive_summary.txt", 'w', encoding='utf-8') as f:
        f.write("📋 TÓM TẮT ĐIỀU HÀNH - ĐÁNH GIÁ HIỆU SUẤT AGENT\n")
        f.write("="*60 + "\n\n")
        
        best_accuracy = summary['Accuracy'].idxmax()
        best_f1 = summary['F1_Score'].idxmax() 
        best_tool = summary['Tool_Fail_Rate'].idxmin()
        
        f.write("🏆 KẾT QUẢ CHÍNH:\n")
        f.write(f"• Agent tốt nhất về Accuracy: {best_accuracy} ({summary.loc[best_accuracy, 'Accuracy']:.3f})\n")
        f.write(f"• Agent tốt nhất về F1 Score: {best_f1} ({summary.loc[best_f1, 'F1_Score']:.3f})\n")
        f.write(f"• Agent tin cậy nhất (ít lỗi): {best_tool} ({(1-summary.loc[best_tool, 'Tool_Fail_Rate']):.3f})\n\n")
        
        f.write("📊 THỐNG KÊ TỔNG QUAN:\n")
        f.write(f"• Tổng số câu hỏi đánh giá: {results_df['Sample_Count'].sum()//2} (mỗi agent)\n")
        f.write(f"• Số agent được đánh giá: {len(summary)}\n")
        f.write(f"• Accuracy trung bình: {summary['Accuracy'].mean():.3f}\n")
        f.write(f"• F1 Score trung bình: {summary['F1_Score'].mean():.3f}\n")
        f.write(f"• Tool Success Rate trung bình: {(1-summary['Tool_Fail_Rate']).mean():.3f}\n\n")
        
        f.write("💡 KHUYẾN NGHỊ:\n")
        if best_accuracy == best_f1 == best_tool:
            f.write(f"• {best_accuracy} là lựa chọn tốt nhất cho tất cả metrics\n")
        else:
            f.write(f"• Để accuracy cao: Chọn {best_accuracy}\n")
            f.write(f"• Để cân bằng precision/recall: Chọn {best_f1}\n") 
            f.write(f"• Để ít lỗi nhất: Chọn {best_tool}\n")
    
    print(f"📄 Created detailed reports in {base_path}")

def save_failed_cases_analysis(failed_cases_df, base_path="results/raw_data"):
    """Lưu phân tích các trường hợp thất bại"""
    base_path = Path(base_path)
    failed_cases_df.to_csv(base_path / "failed_cases_analysis.csv", index=False)
    print(f"❌ Saved failed cases analysis to {base_path}/failed_cases_analysis.csv") 