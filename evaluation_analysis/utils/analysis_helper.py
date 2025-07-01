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