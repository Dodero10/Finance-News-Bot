#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phân tích và so sánh các agent theo độ khó
Tính accuracy, F1 score và tỉ lệ gọi tool fail
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import re

# Thiết lập font để hỗ trợ tiếng Việt
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

class AgentEvaluator:
    def __init__(self, data_path):
        self.data_path = Path(data_path)
        self.agents_data = {}
        self.ground_truth_tools = {}
        self.load_data()
        self.load_ground_truth()
    
    def load_data(self):
        """Load dữ liệu từ các file CSV"""
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
                print(f"Loaded {len(df)} records for {agent_name}")
            else:
                print(f"File not found: {file_path}")
    
    def load_ground_truth(self):
        """Load ground truth tools từ synthetic_news.csv"""
        synthetic_path = Path("evaluation/data_eval/synthetic_data/synthetic_news.csv")
        if synthetic_path.exists():
            df_truth = pd.read_csv(synthetic_path)
            for _, row in df_truth.iterrows():
                query = row['query']
                tools_str = row['tools']
                # Parse tools từ string format ['tool1', 'tool2'] thành set
                try:
                    import ast
                    tools_list = ast.literal_eval(tools_str)
                    self.ground_truth_tools[query] = set(tools_list)
                except:
                    # Fallback parsing
                    tools_clean = tools_str.strip("[]'\"").replace("'", "").replace('"', '')
                    tools_list = [t.strip() for t in tools_clean.split(',') if t.strip()]
                    self.ground_truth_tools[query] = set(tools_list)
            print(f"Loaded ground truth for {len(self.ground_truth_tools)} queries")
        else:
            print(f"Ground truth file not found: {synthetic_path}")
    
    def calculate_accuracy(self, df):
        """
        Tính accuracy - agent gọi tools hoàn toàn đúng
        Accuracy = (số câu có failed_tools_count = 0) / tổng số câu
        """
        total_questions = len(df)
        correct_tool_calls = len(df[df['failed_tools_count'] == 0])
        return correct_tool_calls / total_questions if total_questions > 0 else 0
    
    def determine_required_tools(self, row):
        """
        Xác định tools cần thiết dựa trên ground truth từ synthetic_news.csv
        """
        query = row['input']
        
        # Tìm exact match trước
        if query in self.ground_truth_tools:
            return self.ground_truth_tools[query]
        
        # Nếu không tìm thấy exact match, tìm similar query
        for gt_query, gt_tools in self.ground_truth_tools.items():
            if query.strip() == gt_query.strip():
                return gt_tools
        
        # Fallback: trả về empty set nếu không tìm thấy
        print(f"Warning: No ground truth found for query: {query[:50]}...")
        return set()
    
    def parse_tools_used(self, tools_str):
        """
        Parse chuỗi tools thành set
        """
        if pd.isna(tools_str) or tools_str.strip() == '':
            return set()
        
        # Tách các tools bằng dấu phẩy và làm sạch
        tools = set()
        for tool in str(tools_str).split(','):
            tool = tool.strip()
            if tool:
                tools.add(tool)
        return tools
    
    def calculate_f1_score(self, df):
        """
        Tính F1 score chính xác dựa trên việc so sánh tools được gọi với tools cần thiết
        
        TP: Tools được gọi đúng và cần thiết
        FP: Tools được gọi nhưng không cần thiết hoặc gọi thừa
        FN: Tools cần thiết nhưng không được gọi
        """
        df_copy = df.copy()
        
        tp = 0  # True Positive
        fp = 0  # False Positive  
        fn = 0  # False Negative
        
        for idx, row in df_copy.iterrows():
            required_tools = self.determine_required_tools(row)
            used_tools = self.parse_tools_used(row['tools'])
            
            # Loại bỏ tools bị failed
            if row['failed_tools_count'] > 0 and not pd.isna(row['failed_tools']):
                failed_tools = self.parse_tools_used(row['failed_tools'])
                used_tools = used_tools - failed_tools
            
            # Tính TP, FP, FN
            tp_for_row = len(required_tools & used_tools)  # Tools đúng và cần thiết
            fp_for_row = len(used_tools - required_tools)  # Tools gọi thừa
            fn_for_row = len(required_tools - used_tools)  # Tools cần thiết nhưng không gọi
            
            tp += tp_for_row
            fp += fp_for_row
            fn += fn_for_row
        
        # Tính Precision, Recall và F1
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return f1, precision, recall
    
    def calculate_tool_fail_rate(self, df):
        """
        Tính tỉ lệ gọi tool fail
        Tool fail rate = số câu có failed_tools_count > 0 / tổng số câu có gọi tool
        """
        df_with_tools = df[df['tools'].notna() & (df['tools'].str.strip() != '')]
        if len(df_with_tools) == 0:
            return 0
        
        failed_calls = len(df_with_tools[df_with_tools['failed_tools_count'] > 0])
        return failed_calls / len(df_with_tools)
    
    def calculate_tool_precision_recall(self, df):
        """
        Tính precision và recall riêng cho tool usage
        """
        total_correct_tools = 0
        total_used_tools = 0
        total_required_tools = 0
        
        df_copy = df.copy()
        
        for idx, row in df_copy.iterrows():
            required_tools = self.determine_required_tools(row)
            used_tools = self.parse_tools_used(row['tools'])
            
            # Loại bỏ tools bị failed
            if row['failed_tools_count'] > 0 and not pd.isna(row['failed_tools']):
                failed_tools = self.parse_tools_used(row['failed_tools'])
                used_tools = used_tools - failed_tools
            
            correct_tools = len(required_tools & used_tools)
            
            total_correct_tools += correct_tools
            total_used_tools += len(used_tools)
            total_required_tools += len(required_tools)
        
        precision = total_correct_tools / total_used_tools if total_used_tools > 0 else 0
        recall = total_correct_tools / total_required_tools if total_required_tools > 0 else 0
        
        return precision, recall
    
    def analyze_by_difficulty(self):
        """Phân tích các metrics theo độ khó"""
        results = []
        
        for agent_name, df in self.agents_data.items():
            for difficulty in ['dễ', 'khó']:
                df_filtered = df[df['difficulty'] == difficulty]
                
                if len(df_filtered) > 0:
                    accuracy = self.calculate_accuracy(df_filtered)
                    f1_score, precision, recall = self.calculate_f1_score(df_filtered)
                    tool_fail_rate = self.calculate_tool_fail_rate(df_filtered)
                    tool_precision, tool_recall = self.calculate_tool_precision_recall(df_filtered)
                    
                    results.append({
                        'Agent': agent_name,
                        'Difficulty': difficulty,
                        'Accuracy': accuracy,
                        'F1_Score': f1_score,
                        'Precision': precision,
                        'Recall': recall,
                        'Tool_Precision': tool_precision,
                        'Tool_Recall': tool_recall,
                        'Tool_Fail_Rate': tool_fail_rate,
                        'Sample_Count': len(df_filtered)
                    })
        
        return pd.DataFrame(results)
    
    def create_comparison_plots(self, results_df):
        """Tạo biểu đồ so sánh"""
        # Thiết lập style
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('So sánh hiệu suất các Agent theo độ khó', fontsize=16, fontweight='bold')
        
        # Màu sắc cho các agent
        colors = {'React': '#FF6B6B', 'ReWOO': '#4ECDC4', 'Reflexion': '#45B7D1', 'Multi-Agent': '#96CEB4'}
        
        # 1. Accuracy comparison
        ax1 = axes[0, 0]
        accuracy_pivot = results_df.pivot(index='Agent', columns='Difficulty', values='Accuracy')
        accuracy_pivot.plot(kind='bar', ax=ax1, color=[colors.get(agent, '#999999') for agent in accuracy_pivot.index])
        ax1.set_title('Accuracy theo độ khó', fontweight='bold')
        ax1.set_ylabel('Accuracy')
        ax1.set_xlabel('Agent')
        ax1.legend(title='Độ khó')
        ax1.tick_params(axis='x', rotation=45)
        
        # Thêm giá trị lên bar
        for container in ax1.containers:
            ax1.bar_label(container, fmt='%.3f', fontsize=9)
        
        # 2. F1 Score comparison  
        ax2 = axes[0, 1]
        f1_pivot = results_df.pivot(index='Agent', columns='Difficulty', values='F1_Score')
        f1_pivot.plot(kind='bar', ax=ax2, color=[colors.get(agent, '#999999') for agent in f1_pivot.index])
        ax2.set_title('F1 Score theo độ khó', fontweight='bold')
        ax2.set_ylabel('F1 Score')
        ax2.set_xlabel('Agent')
        ax2.legend(title='Độ khó')
        ax2.tick_params(axis='x', rotation=45)
        
        # Thêm giá trị lên bar
        for container in ax2.containers:
            ax2.bar_label(container, fmt='%.3f', fontsize=9)
        
        # 3. Tool Fail Rate comparison
        ax3 = axes[1, 0]
        fail_rate_pivot = results_df.pivot(index='Agent', columns='Difficulty', values='Tool_Fail_Rate')
        fail_rate_pivot.plot(kind='bar', ax=ax3, color=[colors.get(agent, '#999999') for agent in fail_rate_pivot.index])
        ax3.set_title('Tỉ lệ gọi Tool thất bại theo độ khó', fontweight='bold')
        ax3.set_ylabel('Tool Fail Rate')
        ax3.set_xlabel('Agent')
        ax3.legend(title='Độ khó')
        ax3.tick_params(axis='x', rotation=45)
        
        # Thêm giá trị lên bar
        for container in ax3.containers:
            ax3.bar_label(container, fmt='%.3f', fontsize=9)
        
        # 4. Overall comparison (heatmap)
        ax4 = axes[1, 1]
        
        # Tạo dữ liệu cho heatmap (trung bình của các metrics)
        heatmap_data = results_df.groupby('Agent')[['Accuracy', 'F1_Score']].mean()
        # Invert Tool_Fail_Rate để cao hơn = tốt hơn
        heatmap_data['Tool_Success_Rate'] = 1 - results_df.groupby('Agent')['Tool_Fail_Rate'].mean()
        
        sns.heatmap(heatmap_data.T, annot=True, fmt='.3f', cmap='RdYlGn', 
                   ax=ax4, cbar_kws={'label': 'Score'})
        ax4.set_title('Tổng quan hiệu suất (cao hơn = tốt hơn)', fontweight='bold')
        ax4.set_xlabel('Agent')
        ax4.set_ylabel('Metrics')
        
        plt.tight_layout()
        return fig
    
    def create_detailed_comparison(self, results_df):
        """Tạo biểu đồ so sánh chi tiết"""
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        metrics = ['Accuracy', 'F1_Score', 'Tool_Fail_Rate']
        metric_labels = ['Accuracy', 'F1 Score', 'Tỉ lệ Tool thất bại']
        
        for i, (metric, label) in enumerate(zip(metrics, metric_labels)):
            ax = axes[i]
            
            # Tạo grouped bar chart
            easy_data = results_df[results_df['Difficulty'] == 'dễ']
            hard_data = results_df[results_df['Difficulty'] == 'khó']
            
            x = np.arange(len(easy_data))
            width = 0.35
            
            bars1 = ax.bar(x - width/2, easy_data[metric], width, label='Dễ', alpha=0.8)
            bars2 = ax.bar(x + width/2, hard_data[metric], width, label='Khó', alpha=0.8)
            
            ax.set_xlabel('Agent')
            ax.set_ylabel(label)
            ax.set_title(f'{label} theo Agent và độ khó')
            ax.set_xticks(x)
            ax.set_xticklabels(easy_data['Agent'], rotation=45)
            ax.legend()
            
            # Thêm giá trị lên bar
            for bars in [bars1, bars2]:
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f'{height:.3f}',
                               xy=(bar.get_x() + bar.get_width() / 2, height),
                               xytext=(0, 3),
                               textcoords="offset points",
                               ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        return fig
    
    def print_summary_table(self, results_df):
        """In bảng tổng kết"""
        print("\n" + "="*80)
        print("BẢNG TỔNG KẾT HIỆU SUẤT CÁC AGENT")
        print("="*80)
        
        # Format và in bảng
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.float_format', '{:.3f}'.format)
        
        print(results_df.to_string(index=False))
        
        print("\n" + "="*80)
        print("TỔNG KẾT THEO AGENT (Trung bình)")
        print("="*80)
        
        summary = results_df.groupby('Agent').agg({
            'Accuracy': 'mean',
            'F1_Score': 'mean', 
            'Tool_Fail_Rate': 'mean',
            'Sample_Count': 'sum'
        }).round(3)
        
        print(summary.to_string())
        
        # Xếp hạng
        print("\n" + "="*80)
        print("XẾP HẠNG THEO METRICS")
        print("="*80)
        
        print("Accuracy (cao nhất -> thấp nhất):")
        accuracy_ranking = summary.sort_values('Accuracy', ascending=False)
        for i, (agent, row) in enumerate(accuracy_ranking.iterrows(), 1):
            print(f"{i}. {agent}: {row['Accuracy']:.3f}")
        
        print("\nF1 Score (cao nhất -> thấp nhất):")
        f1_ranking = summary.sort_values('F1_Score', ascending=False)
        for i, (agent, row) in enumerate(f1_ranking.iterrows(), 1):
            print(f"{i}. {agent}: {row['F1_Score']:.3f}")
        
        print("\nTool Success Rate (thấp nhất tool fail rate -> cao nhất):")
        tool_ranking = summary.sort_values('Tool_Fail_Rate', ascending=True)
        for i, (agent, row) in enumerate(tool_ranking.iterrows(), 1):
            success_rate = 1 - row['Tool_Fail_Rate']
            print(f"{i}. {agent}: {success_rate:.3f} (fail rate: {row['Tool_Fail_Rate']:.3f})")

def main():
    # Đường dẫn đến folder chứa file kết quả
    data_path = Path("evaluation/data_eval/results")
    
    # Tạo evaluator
    evaluator = AgentEvaluator(data_path)
    
    # Phân tích theo độ khó
    results_df = evaluator.analyze_by_difficulty()
    
    # In bảng tổng kết
    evaluator.print_summary_table(results_df)
    
    # Tạo biểu đồ so sánh
    fig1 = evaluator.create_comparison_plots(results_df)
    
    # Tạo biểu đồ chi tiết
    fig2 = evaluator.create_detailed_comparison(results_df)
    
    # Lưu biểu đồ
    output_dir = Path("evaluation/results_visualization/figures/comprehensive")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    fig1.savefig(output_dir / "agent_comparison_overview.png", dpi=300, bbox_inches='tight')
    fig2.savefig(output_dir / "agent_comparison_detailed.png", dpi=300, bbox_inches='tight')
    
    print(f"\nBiểu đồ đã được lưu tại: {output_dir}")
    
    # Hiển thị biểu đồ
    plt.show()
    
    return results_df

if __name__ == "__main__":
    results = main() 