#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Individual Metric Visualizations for Agent Performance Analysis
Creates separate figures for each metric: Accuracy, Precision, Recall, F1 Score
Each figure has: Overall performance + Performance by difficulty
"""

import sys
import matplotlib
matplotlib.use('Agg')  # For server environments
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Import helper functions
from utils.analysis_helper import AgentAnalyzer

class IndividualMetricVisualizer:
    def __init__(self):
        """Initialize visualizer with professional settings"""
        self.setup_academic_style()
        self.colors = self.get_academic_colors()
        
    def setup_academic_style(self):
        """Setup professional academic styling"""
        plt.rcParams.update({
            'font.family': 'serif',
            'font.serif': ['Times New Roman', 'DejaVu Serif', 'Bitstream Vera Serif'],
            'font.size': 11,
            'axes.titlesize': 12,
            'axes.labelsize': 11,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 10,
            'figure.titlesize': 14,
            'figure.dpi': 300,
            'savefig.dpi': 300,
            'savefig.bbox': 'tight',
            'savefig.pad_inches': 0.1,
            'axes.linewidth': 0.8,
            'grid.linewidth': 0.5,
            'lines.linewidth': 1.5,
            'patch.linewidth': 0.5,
            'xtick.major.width': 0.8,
            'ytick.major.width': 0.8,
            'xtick.minor.width': 0.6,
            'ytick.minor.width': 0.6,
            'axes.grid': True,
            'grid.alpha': 0.3,
            'axes.axisbelow': True
        })
        plt.style.use('seaborn-v0_8-whitegrid')
        
    def get_academic_colors(self):
        """Professional color palette for academic publications"""
        return {
            'React': '#2E5984',        # Professional blue
            'ReWOO': '#8B4A91',        # Professional purple  
            'Reflexion': '#C15A5A',    # Professional red
            'Multi-Agent': '#4A7C59',  # Professional green
            'easy': '#7FB069',         # Light green for easy
            'hard': '#D73027',         # Red for hard
            'grid': '#CCCCCC',         # Light gray for grid
            'text': '#2F2F2F'          # Dark gray for text
        }

    def create_accuracy_analysis(self, results_df, save_path):
        """Accuracy Analysis: Overall + By Difficulty"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))  # Increased figure size more
        
        # Panel A: Overall Accuracy
        overall_accuracy = results_df.groupby('Agent')['Accuracy'].mean()
        agents = overall_accuracy.index
        x_pos = np.arange(len(agents))
        
        bars1 = ax1.bar(x_pos, overall_accuracy, 
                       color=[self.colors[agent] for agent in agents],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax1.set_title('(A) Overall Accuracy Performance', fontweight='bold', loc='left', pad=20)
        ax1.set_ylabel('Accuracy Score')
        ax1.set_xlabel('Agent Architecture')
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(agents, rotation=0, ha='center')  # Horizontal labels
        ax1.set_ylim(0, max(overall_accuracy) * 1.2)  # Dynamic y-limit with margin
        
        # Add value labels with better positioning
        for bar, val in zip(bars1, overall_accuracy):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(overall_accuracy) * 0.02,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Panel B: Accuracy by Difficulty - Fix alignment issues
        # Ensure all agents have data for both difficulties
        difficulty_data = results_df.pivot_table(
            index='Agent', 
            columns='Difficulty', 
            values='Accuracy',
            fill_value=0  # Fill missing values with 0
        )
        
        # Ensure columns exist and are in the right order
        if 'dễ' not in difficulty_data.columns:
            difficulty_data['dễ'] = 0
        if 'khó' not in difficulty_data.columns:
            difficulty_data['khó'] = 0
            
        # Reorder columns and align with agent order
        difficulty_data = difficulty_data.reindex(agents, fill_value=0)
        difficulty_data = difficulty_data[['dễ', 'khó']]  # Ensure column order
        
        x = np.arange(len(agents))
        width = 0.35
        
        bars2 = ax2.bar(x - width/2, difficulty_data['dễ'], width,
                       label='Easy Queries (Dễ)', color=self.colors['easy'],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        bars3 = ax2.bar(x + width/2, difficulty_data['khó'], width,
                       label='Hard Queries (Khó)', color=self.colors['hard'],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax2.set_title('(B) Accuracy by Query Difficulty', fontweight='bold', loc='left', pad=20)
        ax2.set_ylabel('Accuracy Score')
        ax2.set_xlabel('Agent Architecture')
        ax2.set_xticks(x)
        ax2.set_xticklabels(agents, rotation=0, ha='center')  # Horizontal labels
        ax2.legend(loc='upper left', bbox_to_anchor=(0.02, 0.98))  # Position legend to avoid overlap
        
        # Dynamic y-limit
        max_val = max(difficulty_data.max())
        ax2.set_ylim(0, max_val * 1.25)
        
        # Add value labels with better spacing and smaller font
        for i, (easy_val, hard_val) in enumerate(zip(difficulty_data['dễ'], difficulty_data['khó'])):
            if easy_val > 0:  # Only show label if value exists
                ax2.text(x[i] - width/2, easy_val + max_val * 0.02,
                        f'{easy_val:.3f}', ha='center', va='bottom', fontsize=8)
            if hard_val > 0:  # Only show label if value exists
                ax2.text(x[i] + width/2, hard_val + max_val * 0.02,
                        f'{hard_val:.3f}', ha='center', va='bottom', fontsize=8)
        
        plt.suptitle('Accuracy Performance Analysis Across Agent Architectures',
                    fontsize=14, fontweight='bold', y=0.95)
        plt.tight_layout(rect=[0, 0, 1, 0.92])  # Adjusted for horizontal labels
        plt.savefig(save_path / "accuracy_analysis.png", dpi=300, bbox_inches='tight')
        plt.close()

    def create_precision_analysis(self, results_df, save_path):
        """Precision Analysis: Overall + By Difficulty"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))  # Increased figure size more
        
        # Panel A: Overall Precision
        overall_precision = results_df.groupby('Agent')['Precision'].mean()
        agents = overall_precision.index
        x_pos = np.arange(len(agents))
        
        bars1 = ax1.bar(x_pos, overall_precision,
                       color=[self.colors[agent] for agent in agents],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax1.set_title('(A) Overall Precision Performance', fontweight='bold', loc='left', pad=20)
        ax1.set_ylabel('Precision Score')
        ax1.set_xlabel('Agent Architecture')
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(agents, rotation=0, ha='center')  # Horizontal labels
        ax1.set_ylim(0, min(1.1, max(overall_precision) * 1.15))  # Dynamic with max of 1.1
        
        # Add value labels with better positioning
        for bar, val in zip(bars1, overall_precision):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.03,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Panel B: Precision by Difficulty - Fix alignment issues
        difficulty_data = results_df.pivot_table(
            index='Agent', 
            columns='Difficulty', 
            values='Precision',
            fill_value=0
        )
        
        # Ensure columns exist and are in the right order
        if 'dễ' not in difficulty_data.columns:
            difficulty_data['dễ'] = 0
        if 'khó' not in difficulty_data.columns:
            difficulty_data['khó'] = 0
            
        # Reorder and align with agent order
        difficulty_data = difficulty_data.reindex(agents, fill_value=0)
        difficulty_data = difficulty_data[['dễ', 'khó']]
        
        x = np.arange(len(agents))
        width = 0.35
        
        bars2 = ax2.bar(x - width/2, difficulty_data['dễ'], width,
                       label='Easy Queries (Dễ)', color=self.colors['easy'],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        bars3 = ax2.bar(x + width/2, difficulty_data['khó'], width,
                       label='Hard Queries (Khó)', color=self.colors['hard'],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax2.set_title('(B) Precision by Query Difficulty', fontweight='bold', loc='left', pad=20)
        ax2.set_ylabel('Precision Score')
        ax2.set_xlabel('Agent Architecture')
        ax2.set_xticks(x)
        ax2.set_xticklabels(agents, rotation=0, ha='center')  # Horizontal labels
        ax2.legend(loc='upper left', bbox_to_anchor=(0.02, 0.98))
        
        # Dynamic y-limit
        max_val = max(difficulty_data.max())
        ax2.set_ylim(0, min(1.1, max_val * 1.15))
        
        # Add value labels with better spacing
        for i, (easy_val, hard_val) in enumerate(zip(difficulty_data['dễ'], difficulty_data['khó'])):
            if easy_val > 0:
                ax2.text(x[i] - width/2, easy_val + 0.03,
                        f'{easy_val:.3f}', ha='center', va='bottom', fontsize=8)
            if hard_val > 0:
                ax2.text(x[i] + width/2, hard_val + 0.03,
                        f'{hard_val:.3f}', ha='center', va='bottom', fontsize=8)
        
        plt.suptitle('Precision Performance Analysis Across Agent Architectures',
                    fontsize=14, fontweight='bold', y=0.95)
        plt.tight_layout(rect=[0, 0, 1, 0.92])
        plt.savefig(save_path / "precision_analysis.png", dpi=300, bbox_inches='tight')
        plt.close()

    def create_recall_analysis(self, results_df, save_path):
        """Recall Analysis: Overall + By Difficulty"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))  # Increased figure size more
        
        # Panel A: Overall Recall
        overall_recall = results_df.groupby('Agent')['Recall'].mean()
        agents = overall_recall.index
        x_pos = np.arange(len(agents))
        
        bars1 = ax1.bar(x_pos, overall_recall,
                       color=[self.colors[agent] for agent in agents],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax1.set_title('(A) Overall Recall Performance', fontweight='bold', loc='left', pad=20)
        ax1.set_ylabel('Recall Score')
        ax1.set_xlabel('Agent Architecture')
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(agents, rotation=0, ha='center')  # Horizontal labels
        ax1.set_ylim(0, min(1.1, max(overall_recall) * 1.15))
        
        # Add value labels with better positioning
        for bar, val in zip(bars1, overall_recall):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.03,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Panel B: Recall by Difficulty - Fix alignment issues
        difficulty_data = results_df.pivot_table(
            index='Agent', 
            columns='Difficulty', 
            values='Recall',
            fill_value=0
        )
        
        # Ensure columns exist and are in the right order
        if 'dễ' not in difficulty_data.columns:
            difficulty_data['dễ'] = 0
        if 'khó' not in difficulty_data.columns:
            difficulty_data['khó'] = 0
            
        # Reorder and align with agent order
        difficulty_data = difficulty_data.reindex(agents, fill_value=0)
        difficulty_data = difficulty_data[['dễ', 'khó']]
        
        x = np.arange(len(agents))
        width = 0.35
        
        bars2 = ax2.bar(x - width/2, difficulty_data['dễ'], width,
                       label='Easy Queries (Dễ)', color=self.colors['easy'],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        bars3 = ax2.bar(x + width/2, difficulty_data['khó'], width,
                       label='Hard Queries (Khó)', color=self.colors['hard'],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax2.set_title('(B) Recall by Query Difficulty', fontweight='bold', loc='left', pad=20)
        ax2.set_ylabel('Recall Score')
        ax2.set_xlabel('Agent Architecture')
        ax2.set_xticks(x)
        ax2.set_xticklabels(agents, rotation=0, ha='center')  # Horizontal labels
        
        # Dynamic y-limit
        max_val = max(difficulty_data.max())
        ax2.set_ylim(0, min(1.1, max_val * 1.15))
        
        # Position legend to avoid overlap - move to upper right for recall
        ax2.legend(loc='upper right', bbox_to_anchor=(0.98, 0.98))
        
        # Add value labels with better spacing
        for i, (easy_val, hard_val) in enumerate(zip(difficulty_data['dễ'], difficulty_data['khó'])):
            if easy_val > 0:
                ax2.text(x[i] - width/2, easy_val + 0.03,
                        f'{easy_val:.3f}', ha='center', va='bottom', fontsize=8)
            if hard_val > 0:
                ax2.text(x[i] + width/2, hard_val + 0.03,
                        f'{hard_val:.3f}', ha='center', va='bottom', fontsize=8)
        
        plt.suptitle('Recall Performance Analysis Across Agent Architectures',
                    fontsize=14, fontweight='bold', y=0.95)
        plt.tight_layout(rect=[0, 0, 1, 0.92])
        plt.savefig(save_path / "recall_analysis.png", dpi=300, bbox_inches='tight')
        plt.close()

    def create_f1_analysis(self, results_df, save_path):
        """F1 Score Analysis: Overall + By Difficulty"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))  # Increased figure size more
        
        # Panel A: Overall F1 Score
        overall_f1 = results_df.groupby('Agent')['F1_Score'].mean()
        agents = overall_f1.index
        x_pos = np.arange(len(agents))
        
        bars1 = ax1.bar(x_pos, overall_f1,
                       color=[self.colors[agent] for agent in agents],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax1.set_title('(A) Overall F1 Score Performance', fontweight='bold', loc='left', pad=20)
        ax1.set_ylabel('F1 Score')
        ax1.set_xlabel('Agent Architecture')
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(agents, rotation=0, ha='center')  # Horizontal labels
        ax1.set_ylim(0, max(overall_f1) * 1.2)
        
        # Add value labels with better positioning
        for bar, val in zip(bars1, overall_f1):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(overall_f1) * 0.03,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Panel B: F1 Score by Difficulty - Fix alignment issues
        difficulty_data = results_df.pivot_table(
            index='Agent', 
            columns='Difficulty', 
            values='F1_Score',
            fill_value=0
        )
        
        # Ensure columns exist and are in the right order
        if 'dễ' not in difficulty_data.columns:
            difficulty_data['dễ'] = 0
        if 'khó' not in difficulty_data.columns:
            difficulty_data['khó'] = 0
            
        # Reorder and align with agent order
        difficulty_data = difficulty_data.reindex(agents, fill_value=0)
        difficulty_data = difficulty_data[['dễ', 'khó']]
        
        x = np.arange(len(agents))
        width = 0.35
        
        bars2 = ax2.bar(x - width/2, difficulty_data['dễ'], width,
                       label='Easy Queries (Dễ)', color=self.colors['easy'],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        bars3 = ax2.bar(x + width/2, difficulty_data['khó'], width,
                       label='Hard Queries (Khó)', color=self.colors['hard'],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax2.set_title('(B) F1 Score by Query Difficulty', fontweight='bold', loc='left', pad=20)
        ax2.set_ylabel('F1 Score')
        ax2.set_xlabel('Agent Architecture')
        ax2.set_xticks(x)
        ax2.set_xticklabels(agents, rotation=0, ha='center')  # Horizontal labels
        ax2.legend(loc='upper left', bbox_to_anchor=(0.02, 0.98))
        
        # Dynamic y-limit
        max_val = max(difficulty_data.max())
        ax2.set_ylim(0, max_val * 1.2)
        
        # Add value labels with better spacing
        for i, (easy_val, hard_val) in enumerate(zip(difficulty_data['dễ'], difficulty_data['khó'])):
            if easy_val > 0:
                ax2.text(x[i] - width/2, easy_val + max_val * 0.02,
                        f'{easy_val:.3f}', ha='center', va='bottom', fontsize=8)
            if hard_val > 0:
                ax2.text(x[i] + width/2, hard_val + max_val * 0.02,
                        f'{hard_val:.3f}', ha='center', va='bottom', fontsize=8)
        
        plt.suptitle('F1 Score Performance Analysis Across Agent Architectures',
                    fontsize=14, fontweight='bold', y=0.95)
        plt.tight_layout(rect=[0, 0, 1, 0.92])
        plt.savefig(save_path / "f1_analysis.png", dpi=300, bbox_inches='tight')
        plt.close()

def main():
    """Main function to generate individual metric visualizations"""
    print("🎯 Generating Individual Metric Visualizations...")
    
    # Initialize components
    analyzer = AgentAnalyzer("../evaluation/data_eval/results")
    visualizer = IndividualMetricVisualizer()
    
    # Load data
    if not analyzer.load_agent_data():
        print("❌ Failed to load agent data")
        return
        
    if not analyzer.load_ground_truth("../evaluation/data_eval/synthetic_data/synthetic_news.csv"):
        print("❌ Failed to load ground truth")
        return
    
    # Analyze data
    print("📊 Analyzing agent performance...")
    results_df = analyzer.analyze_by_difficulty()
    
    # Create output directory
    save_path = Path("results/individual_metrics")
    save_path.mkdir(parents=True, exist_ok=True)
    
    # Generate individual metric analyses
    print("🎯 Creating Accuracy Analysis...")
    visualizer.create_accuracy_analysis(results_df, save_path)
    
    print("🔍 Creating Precision Analysis...")
    visualizer.create_precision_analysis(results_df, save_path)
    
    print("📝 Creating Recall Analysis...")
    visualizer.create_recall_analysis(results_df, save_path)
    
    print("⚖️ Creating F1 Score Analysis...")
    visualizer.create_f1_analysis(results_df, save_path)
    
    print(f"✅ All individual metric visualizations saved to: {save_path}")
    print("\n📋 Generated Files:")
    
    # List all files
    for png_file in save_path.glob("*.png"):
        print(f"   📊 {png_file.name}")
    
    # Generate metrics summary
    summary_file = save_path / "metrics_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("INDIVIDUAL METRIC ANALYSIS SUMMARY\n")
        f.write("="*50 + "\n\n")
        
        # Overall summary
        overall_summary = results_df.groupby('Agent').agg({
            'Accuracy': 'mean',
            'Precision': 'mean',
            'Recall': 'mean',
            'F1_Score': 'mean'
        }).round(4)
        
        f.write("OVERALL PERFORMANCE SUMMARY:\n")
        f.write("-"*30 + "\n")
        for agent in overall_summary.index:
            f.write(f"{agent}:\n")
            f.write(f"  Accuracy:  {overall_summary.loc[agent, 'Accuracy']:.3f}\n")
            f.write(f"  Precision: {overall_summary.loc[agent, 'Precision']:.3f}\n")
            f.write(f"  Recall:    {overall_summary.loc[agent, 'Recall']:.3f}\n")
            f.write(f"  F1 Score:  {overall_summary.loc[agent, 'F1_Score']:.3f}\n\n")
        
        # Difficulty breakdown
        f.write("PERFORMANCE BY DIFFICULTY:\n")
        f.write("-"*30 + "\n")
        
        easy_summary = results_df[results_df['Difficulty'] == 'dễ'].groupby('Agent').agg({
            'Accuracy': 'mean', 'Precision': 'mean', 'Recall': 'mean', 'F1_Score': 'mean'
        }).round(4)
        
        hard_summary = results_df[results_df['Difficulty'] == 'khó'].groupby('Agent').agg({
            'Accuracy': 'mean', 'Precision': 'mean', 'Recall': 'mean', 'F1_Score': 'mean'
        }).round(4)
        
        f.write("EASY QUERIES (Dễ):\n")
        for agent in easy_summary.index:
            f.write(f"{agent}: Acc={easy_summary.loc[agent, 'Accuracy']:.3f}, ")
            f.write(f"P={easy_summary.loc[agent, 'Precision']:.3f}, ")
            f.write(f"R={easy_summary.loc[agent, 'Recall']:.3f}, ")
            f.write(f"F1={easy_summary.loc[agent, 'F1_Score']:.3f}\n")
        
        f.write("\nHARD QUERIES (Khó):\n")
        for agent in hard_summary.index:
            f.write(f"{agent}: Acc={hard_summary.loc[agent, 'Accuracy']:.3f}, ")
            f.write(f"P={hard_summary.loc[agent, 'Precision']:.3f}, ")
            f.write(f"R={hard_summary.loc[agent, 'Recall']:.3f}, ")
            f.write(f"F1={hard_summary.loc[agent, 'F1_Score']:.3f}\n")
        
        # Rankings
        f.write("\n" + "="*50 + "\n")
        f.write("RANKINGS BY METRIC:\n")
        f.write("="*50 + "\n")
        
        for metric in ['Accuracy', 'Precision', 'Recall', 'F1_Score']:
            ranking = overall_summary.sort_values(metric, ascending=False)
            f.write(f"\n{metric.upper()} RANKING:\n")
            f.write("-" * 20 + "\n")
            for i, (agent, score) in enumerate(ranking[metric].items(), 1):
                f.write(f"{i}. {agent}: {score:.3f}\n")
    
    print(f"📝 Metrics summary saved to: {summary_file}")
    
    # Generate figure descriptions
    descriptions_file = save_path / "figure_descriptions.txt"
    with open(descriptions_file, 'w', encoding='utf-8') as f:
        f.write("FIGURE DESCRIPTIONS\n")
        f.write("="*30 + "\n\n")
        
        f.write("accuracy_analysis.png:\n")
        f.write("  - Panel A: Overall accuracy across all queries\n")
        f.write("  - Panel B: Accuracy comparison between easy vs hard queries\n")
        f.write("  - Shows percentage of queries with perfect tool selection\n\n")
        
        f.write("precision_analysis.png:\n")
        f.write("  - Panel A: Overall precision across all queries\n")
        f.write("  - Panel B: Precision comparison between easy vs hard queries\n")
        f.write("  - Shows proportion of selected tools that were relevant\n\n")
        
        f.write("recall_analysis.png:\n")
        f.write("  - Panel A: Overall recall across all queries\n")
        f.write("  - Panel B: Recall comparison between easy vs hard queries\n")
        f.write("  - Shows proportion of relevant tools successfully identified\n\n")
        
        f.write("f1_analysis.png:\n")
        f.write("  - Panel A: Overall F1 score across all queries\n")
        f.write("  - Panel B: F1 score comparison between easy vs hard queries\n")
        f.write("  - Shows harmonic mean of precision and recall\n\n")
    
    print(f"📋 Figure descriptions saved to: {descriptions_file}")

if __name__ == "__main__":
    main() 