"""
Individual Metric Visualizations for Agent Performance Analysis
Creates separate figures for each metric: Accuracy, Precision, Recall, F1 Score
Each figure has: Overall performance + Performance by difficulty
"""

import sys
import matplotlib
matplotlib.use('Agg')
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
        """Setup professional academic styling with larger fonts"""
        plt.rcParams.update({
            'font.family': 'serif',
            'font.serif': ['Times New Roman', 'DejaVu Serif', 'Bitstream Vera Serif'],
            'font.size': 14,  # Increased from 11
            'axes.titlesize': 16,  # Increased from 12
            'axes.labelsize': 14,  # Increased from 11
            'xtick.labelsize': 13,  # Increased from 10
            'ytick.labelsize': 13,  # Increased from 10
            'legend.fontsize': 13,  # Increased from 10
            'figure.titlesize': 18,  # Increased from 14
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

    def create_accuracy_overall(self, results_df, save_path):
        """Overall Accuracy Performance - Separate Image"""
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        overall_accuracy = results_df.groupby('Agent')['Accuracy'].mean()
        agents = overall_accuracy.index
        x_pos = np.arange(len(agents))
        
        bars = ax.bar(x_pos, overall_accuracy, 
                       color=[self.colors[agent] for agent in agents],
                     alpha=0.8, edgecolor='black', linewidth=0.8)
        
        ax.set_title('Overall Accuracy Performance Across Agent Architectures', 
                    fontweight='bold', pad=25, fontsize=18)
        ax.set_ylabel('Accuracy Score', fontsize=16)
        ax.set_xlabel('Agent Architecture', fontsize=16)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(agents, fontsize=14)
        ax.set_ylim(0, max(overall_accuracy) * 1.2)
        
        # Add value labels with larger font
        for bar, val in zip(bars, overall_accuracy):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(overall_accuracy) * 0.02,
                   f'{val:.3f}', ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(save_path / "accuracy_overall.png", dpi=300, bbox_inches='tight')
        plt.close()

    def create_accuracy_by_difficulty(self, results_df, save_path):
        """Accuracy by Difficulty - Separate Image"""
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        # Fix alignment issues
        agents = results_df['Agent'].unique()
        difficulty_data = results_df.pivot_table(
            index='Agent', 
            columns='Difficulty', 
            values='Accuracy',
            fill_value=0
        )
        
        # Ensure columns exist and are in the right order
        if 'dễ' not in difficulty_data.columns:
            difficulty_data['dễ'] = 0
        if 'khó' not in difficulty_data.columns:
            difficulty_data['khó'] = 0
            
        # Reorder columns and align with agent order
        difficulty_data = difficulty_data.reindex(agents, fill_value=0)
        difficulty_data = difficulty_data[['dễ', 'khó']]
        
        x = np.arange(len(agents))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, difficulty_data['dễ'], width,
                       label='Easy Queries (Dễ)', color=self.colors['easy'],
                      alpha=0.8, edgecolor='black', linewidth=0.8)
        bars2 = ax.bar(x + width/2, difficulty_data['khó'], width,
                       label='Hard Queries (Khó)', color=self.colors['hard'],
                      alpha=0.8, edgecolor='black', linewidth=0.8)
        
        ax.set_title('Accuracy Performance by Query Difficulty', 
                    fontweight='bold', pad=25, fontsize=18)
        ax.set_ylabel('Accuracy Score', fontsize=16)
        ax.set_xlabel('Agent Architecture', fontsize=16)
        ax.set_xticks(x)
        ax.set_xticklabels(agents, fontsize=14)
        ax.legend(loc='upper left', fontsize=13)
        
        # Dynamic y-limit
        max_val = max(difficulty_data.max())
        ax.set_ylim(0, max_val * 1.25)
        
        # Add value labels with larger font
        for i, (easy_val, hard_val) in enumerate(zip(difficulty_data['dễ'], difficulty_data['khó'])):
            if easy_val > 0:
                ax.text(x[i] - width/2, easy_val + max_val * 0.02,
                       f'{easy_val:.3f}', ha='center', va='bottom', fontsize=11)
            if hard_val > 0:
                ax.text(x[i] + width/2, hard_val + max_val * 0.02,
                       f'{hard_val:.3f}', ha='center', va='bottom', fontsize=11)
        
        plt.tight_layout()
        plt.savefig(save_path / "accuracy_by_difficulty.png", dpi=300, bbox_inches='tight')
        plt.close()

    def create_precision_overall(self, results_df, save_path):
        """Overall Precision Performance - Separate Image"""
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        overall_precision = results_df.groupby('Agent')['Precision'].mean()
        agents = overall_precision.index
        x_pos = np.arange(len(agents))
        
        bars = ax.bar(x_pos, overall_precision,
                       color=[self.colors[agent] for agent in agents],
                     alpha=0.8, edgecolor='black', linewidth=0.8)
        
        ax.set_title('Overall Precision Performance Across Agent Architectures', 
                    fontweight='bold', pad=25, fontsize=18)
        ax.set_ylabel('Precision Score', fontsize=16)
        ax.set_xlabel('Agent Architecture', fontsize=16)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(agents, fontsize=14)
        ax.set_ylim(0, min(1.1, max(overall_precision) * 1.15))
        
        # Add value labels with larger font
        for bar, val in zip(bars, overall_precision):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.03,
                   f'{val:.3f}', ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(save_path / "precision_overall.png", dpi=300, bbox_inches='tight')
        plt.close()

    def create_precision_by_difficulty(self, results_df, save_path):
        """Precision by Difficulty - Separate Image"""
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        agents = results_df['Agent'].unique()
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
        
        bars1 = ax.bar(x - width/2, difficulty_data['dễ'], width,
                      label='Easy Queries (Dễ)', color=self.colors['easy'],
                      alpha=0.8, edgecolor='black', linewidth=0.8)
        bars2 = ax.bar(x + width/2, difficulty_data['khó'], width,
                      label='Hard Queries (Khó)', color=self.colors['hard'],
                      alpha=0.8, edgecolor='black', linewidth=0.8)
        
        ax.set_title('Precision Performance by Query Difficulty', 
                    fontweight='bold', pad=25, fontsize=18)
        ax.set_ylabel('Precision Score', fontsize=16)
        ax.set_xlabel('Agent Architecture', fontsize=16)
        ax.set_xticks(x)
        ax.set_xticklabels(agents, fontsize=14)
        ax.legend(loc='upper left', fontsize=13)
        
        # Dynamic y-limit with more space for labels
        max_val = max(difficulty_data.max())
        if max_val > 0.85:  # If values are high, need more space for labels
            ax.set_ylim(0, min(1.2, max_val * 1.25))
        else:
            ax.set_ylim(0, min(1.1, max_val * 1.15))
        
        # Add value labels with better positioning to avoid overlap
        label_offset = max_val * 0.04 if max_val > 0.8 else 0.03
        for i, (easy_val, hard_val) in enumerate(zip(difficulty_data['dễ'], difficulty_data['khó'])):
            if easy_val > 0:
                # Check if label would go beyond chart area
                label_y = easy_val + label_offset
                if label_y < ax.get_ylim()[1] * 0.95:  # Only show if within 95% of chart height
                    ax.text(x[i] - width/2, label_y,
                           f'{easy_val:.3f}', ha='center', va='bottom', fontsize=10)
            if hard_val > 0:
                # Check if label would go beyond chart area
                label_y = hard_val + label_offset
                if label_y < ax.get_ylim()[1] * 0.95:  # Only show if within 95% of chart height
                    ax.text(x[i] + width/2, label_y,
                           f'{hard_val:.3f}', ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        plt.savefig(save_path / "precision_by_difficulty.png", dpi=300, bbox_inches='tight')
        plt.close()

    def create_recall_overall(self, results_df, save_path):
        """Overall Recall Performance - Separate Image"""
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        overall_recall = results_df.groupby('Agent')['Recall'].mean()
        agents = overall_recall.index
        x_pos = np.arange(len(agents))
        
        bars = ax.bar(x_pos, overall_recall,
                       color=[self.colors[agent] for agent in agents],
                     alpha=0.8, edgecolor='black', linewidth=0.8)
        
        ax.set_title('Overall Recall Performance Across Agent Architectures', 
                    fontweight='bold', pad=25, fontsize=18)
        ax.set_ylabel('Recall Score', fontsize=16)
        ax.set_xlabel('Agent Architecture', fontsize=16)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(agents, fontsize=14)
        ax.set_ylim(0, min(1.1, max(overall_recall) * 1.15))
        
        # Add value labels with larger font
        for bar, val in zip(bars, overall_recall):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.03,
                   f'{val:.3f}', ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(save_path / "recall_overall.png", dpi=300, bbox_inches='tight')
        plt.close()

    def create_recall_by_difficulty(self, results_df, save_path):
        """Recall by Difficulty - Separate Image"""
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        agents = results_df['Agent'].unique()
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
        
        bars1 = ax.bar(x - width/2, difficulty_data['dễ'], width,
                      label='Easy Queries (Dễ)', color=self.colors['easy'],
                      alpha=0.8, edgecolor='black', linewidth=0.8)
        bars2 = ax.bar(x + width/2, difficulty_data['khó'], width,
                      label='Hard Queries (Khó)', color=self.colors['hard'],
                      alpha=0.8, edgecolor='black', linewidth=0.8)
        
        ax.set_title('Recall Performance by Query Difficulty', 
                    fontweight='bold', pad=25, fontsize=18)
        ax.set_ylabel('Recall Score', fontsize=16)
        ax.set_xlabel('Agent Architecture', fontsize=16)
        ax.set_xticks(x)
        ax.set_xticklabels(agents, fontsize=14)
        ax.legend(loc='upper right', fontsize=13)
        
        # Dynamic y-limit with more space for labels
        max_val = max(difficulty_data.max())
        if max_val > 0.85:  # If values are high, need more space for labels
            ax.set_ylim(0, min(1.2, max_val * 1.25))
        else:
            ax.set_ylim(0, min(1.1, max_val * 1.15))
        
        # Add value labels with better positioning to avoid overlap
        label_offset = max_val * 0.04 if max_val > 0.8 else 0.03
        for i, (easy_val, hard_val) in enumerate(zip(difficulty_data['dễ'], difficulty_data['khó'])):
            if easy_val > 0:
                # Check if label would go beyond chart area
                label_y = easy_val + label_offset
                if label_y < ax.get_ylim()[1] * 0.95:  # Only show if within 95% of chart height
                    ax.text(x[i] - width/2, label_y,
                           f'{easy_val:.3f}', ha='center', va='bottom', fontsize=10)
            if hard_val > 0:
                # Check if label would go beyond chart area
                label_y = hard_val + label_offset
                if label_y < ax.get_ylim()[1] * 0.95:  # Only show if within 95% of chart height
                    ax.text(x[i] + width/2, label_y,
                           f'{hard_val:.3f}', ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        plt.savefig(save_path / "recall_by_difficulty.png", dpi=300, bbox_inches='tight')
        plt.close()

    def create_f1_overall(self, results_df, save_path):
        """Overall F1 Score Performance - Separate Image"""
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        overall_f1 = results_df.groupby('Agent')['F1_Score'].mean()
        agents = overall_f1.index
        x_pos = np.arange(len(agents))
        
        bars = ax.bar(x_pos, overall_f1,
                       color=[self.colors[agent] for agent in agents],
                     alpha=0.8, edgecolor='black', linewidth=0.8)
        
        ax.set_title('Overall F1 Score Performance Across Agent Architectures', 
                    fontweight='bold', pad=25, fontsize=18)
        ax.set_ylabel('F1 Score', fontsize=16)
        ax.set_xlabel('Agent Architecture', fontsize=16)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(agents, fontsize=14)
        ax.set_ylim(0, max(overall_f1) * 1.2)
        
        # Add value labels with larger font
        for bar, val in zip(bars, overall_f1):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(overall_f1) * 0.03,
                   f'{val:.3f}', ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(save_path / "f1_overall.png", dpi=300, bbox_inches='tight')
        plt.close()

    def create_f1_by_difficulty(self, results_df, save_path):
        """F1 Score by Difficulty - Separate Image"""
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        agents = results_df['Agent'].unique()
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
        
        bars1 = ax.bar(x - width/2, difficulty_data['dễ'], width,
                       label='Easy Queries (Dễ)', color=self.colors['easy'],
                      alpha=0.8, edgecolor='black', linewidth=0.8)
        bars2 = ax.bar(x + width/2, difficulty_data['khó'], width,
                       label='Hard Queries (Khó)', color=self.colors['hard'],
                      alpha=0.8, edgecolor='black', linewidth=0.8)
        
        ax.set_title('F1 Score Performance by Query Difficulty', 
                    fontweight='bold', pad=25, fontsize=18)
        ax.set_ylabel('F1 Score', fontsize=16)
        ax.set_xlabel('Agent Architecture', fontsize=16)
        ax.set_xticks(x)
        ax.set_xticklabels(agents, fontsize=14)
        ax.legend(loc='upper left', fontsize=13)
        
        # Dynamic y-limit
        max_val = max(difficulty_data.max())
        ax.set_ylim(0, max_val * 1.2)
        
        # Add value labels with larger font
        for i, (easy_val, hard_val) in enumerate(zip(difficulty_data['dễ'], difficulty_data['khó'])):
            if easy_val > 0:
                ax.text(x[i] - width/2, easy_val + max_val * 0.02,
                       f'{easy_val:.3f}', ha='center', va='bottom', fontsize=11)
            if hard_val > 0:
                ax.text(x[i] + width/2, hard_val + max_val * 0.02,
                       f'{hard_val:.3f}', ha='center', va='bottom', fontsize=11)
        
        plt.tight_layout()
        plt.savefig(save_path / "f1_by_difficulty.png", dpi=300, bbox_inches='tight')
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
    
    # Generate individual metric analyses - Now as separate images
    print("🎯 Creating Accuracy Visualizations...")
    visualizer.create_accuracy_overall(results_df, save_path)
    visualizer.create_accuracy_by_difficulty(results_df, save_path)
    
    print("🔍 Creating Precision Visualizations...")
    visualizer.create_precision_overall(results_df, save_path)
    visualizer.create_precision_by_difficulty(results_df, save_path)
    
    print("📝 Creating Recall Visualizations...")
    visualizer.create_recall_overall(results_df, save_path)
    visualizer.create_recall_by_difficulty(results_df, save_path)
    
    print("⚖️ Creating F1 Score Visualizations...")
    visualizer.create_f1_overall(results_df, save_path)
    visualizer.create_f1_by_difficulty(results_df, save_path)
    
    print(f"✅ All individual metric visualizations saved to: {save_path}")
    print("\n📋 Generated Files:")
    
    # List all files
    for png_file in sorted(save_path.glob("*.png")):
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
    
    # Generate figure descriptions - Updated for separate images
    descriptions_file = save_path / "figure_descriptions.txt"
    with open(descriptions_file, 'w', encoding='utf-8') as f:
        f.write("FIGURE DESCRIPTIONS\n")
        f.write("="*30 + "\n\n")
        
        f.write("ACCURACY VISUALIZATIONS:\n")
        f.write("accuracy_overall.png: Overall accuracy across all queries\n")
        f.write("accuracy_by_difficulty.png: Accuracy comparison between easy vs hard queries\n\n")
        
        f.write("PRECISION VISUALIZATIONS:\n")
        f.write("precision_overall.png: Overall precision across all queries\n")
        f.write("precision_by_difficulty.png: Precision comparison between easy vs hard queries\n\n")
        
        f.write("RECALL VISUALIZATIONS:\n")
        f.write("recall_overall.png: Overall recall across all queries\n")
        f.write("recall_by_difficulty.png: Recall comparison between easy vs hard queries\n\n")
        
        f.write("F1 SCORE VISUALIZATIONS:\n")
        f.write("f1_overall.png: Overall F1 score across all queries\n")
        f.write("f1_by_difficulty.png: F1 score comparison between easy vs hard queries\n\n")
        
        f.write("INTERPRETATION:\n")
        f.write("- Accuracy: Percentage of queries with perfect tool selection\n")
        f.write("- Precision: Proportion of selected tools that were relevant\n")
        f.write("- Recall: Proportion of relevant tools successfully identified\n")
        f.write("- F1 Score: Harmonic mean of precision and recall\n")
    
    print(f"📋 Figure descriptions saved to: {descriptions_file}")

if __name__ == "__main__":
    main() 