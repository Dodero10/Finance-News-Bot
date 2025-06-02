#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Academic-style visualizations for Agent Performance Analysis
Suitable for scientific reports and publications
"""

import sys
import matplotlib
matplotlib.use('Agg')  # For server environments
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Import helper functions
from utils.analysis_helper import AgentAnalyzer

class AcademicVisualizer:
    def __init__(self):
        """Initialize academic-style visualizer with professional settings"""
        self.setup_academic_style()
        self.colors = self.get_academic_colors()
        
    def setup_academic_style(self):
        """Setup professional academic styling"""
        # Font settings for academic papers
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
        
        # Set style
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
    
    def create_figure_1_accuracy_comparison(self, results_df, save_path):
        """
        Figure 1: Accuracy Performance Comparison Across Agent Architectures
        Professional 2x2 subplot layout
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # Prepare data
        summary = results_df.groupby('Agent').agg({
            'Accuracy': 'mean',
            'F1_Score': 'mean', 
            'Precision': 'mean',
            'Recall': 'mean'
        }).round(4)
        
        agents = summary.index
        x_pos = np.arange(len(agents))
        
        # Panel A: Accuracy
        bars_acc = ax1.bar(x_pos, summary['Accuracy'], 
                          color=[self.colors[agent] for agent in agents],
                          alpha=0.8, edgecolor='black', linewidth=0.5)
        ax1.set_title('(A) Accuracy Performance', fontweight='bold', loc='left')
        ax1.set_ylabel('Accuracy Score')
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(agents, rotation=0)
        ax1.set_ylim(0, 0.5)
        
        # Add value labels
        for bar, val in zip(bars_acc, summary['Accuracy']):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Panel B: F1 Score  
        bars_f1 = ax2.bar(x_pos, summary['F1_Score'],
                         color=[self.colors[agent] for agent in agents], 
                         alpha=0.8, edgecolor='black', linewidth=0.5)
        ax2.set_title('(B) F1 Score Performance', fontweight='bold', loc='left')
        ax2.set_ylabel('F1 Score')
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(agents, rotation=0)
        ax2.set_ylim(0, 0.8)
        
        for bar, val in zip(bars_f1, summary['F1_Score']):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Panel C: Precision
        bars_prec = ax3.bar(x_pos, summary['Precision'],
                           color=[self.colors[agent] for agent in agents],
                           alpha=0.8, edgecolor='black', linewidth=0.5)
        ax3.set_title('(C) Precision Performance', fontweight='bold', loc='left')
        ax3.set_ylabel('Precision Score')
        ax3.set_xticks(x_pos)
        ax3.set_xticklabels(agents, rotation=0)
        ax3.set_ylim(0, 1.05)
        
        for bar, val in zip(bars_prec, summary['Precision']):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Panel D: Recall
        bars_rec = ax4.bar(x_pos, summary['Recall'],
                          color=[self.colors[agent] for agent in agents],
                          alpha=0.8, edgecolor='black', linewidth=0.5)
        ax4.set_title('(D) Recall Performance', fontweight='bold', loc='left')
        ax4.set_ylabel('Recall Score')
        ax4.set_xticks(x_pos)
        ax4.set_xticklabels(agents, rotation=0)
        ax4.set_ylim(0, 1.05)
        
        for bar, val in zip(bars_rec, summary['Recall']):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Overall title
        fig.suptitle('Performance Comparison of Agent Architectures in Financial Question Answering',
                    fontsize=14, fontweight='bold', y=0.95)
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.90)
        plt.savefig(save_path / "figure_1_performance_comparison.png")
        plt.close()
        
    def create_figure_2_difficulty_analysis(self, results_df, save_path):
        """
        Figure 2: Performance Analysis by Query Difficulty
        Side-by-side comparison with error bars
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Prepare data by difficulty
        easy_data = results_df[results_df['Difficulty'] == 'dễ'].set_index('Agent')
        hard_data = results_df[results_df['Difficulty'] == 'khó'].set_index('Agent')
        
        agents = easy_data.index
        x = np.arange(len(agents))
        width = 0.35
        
        # Panel A: Accuracy by Difficulty
        bars1 = ax1.bar(x - width/2, easy_data['Accuracy'], width, 
                       label='Easy Queries', color=self.colors['easy'], 
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        bars2 = ax1.bar(x + width/2, hard_data['Accuracy'], width,
                       label='Hard Queries', color=self.colors['hard'],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax1.set_title('(A) Accuracy by Query Difficulty', fontweight='bold', loc='left')
        ax1.set_ylabel('Accuracy Score')
        ax1.set_xlabel('Agent Architecture')
        ax1.set_xticks(x)
        ax1.set_xticklabels(agents, rotation=0)
        ax1.legend(loc='upper right')
        ax1.set_ylim(0, 0.6)
        
        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2, height + 0.01,
                        f'{height:.3f}', ha='center', va='bottom', fontsize=9)
        
        # Panel B: F1 Score by Difficulty  
        bars3 = ax2.bar(x - width/2, easy_data['F1_Score'], width,
                       label='Easy Queries', color=self.colors['easy'],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        bars4 = ax2.bar(x + width/2, hard_data['F1_Score'], width,
                       label='Hard Queries', color=self.colors['hard'],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax2.set_title('(B) F1 Score by Query Difficulty', fontweight='bold', loc='left')
        ax2.set_ylabel('F1 Score')
        ax2.set_xlabel('Agent Architecture')
        ax2.set_xticks(x)
        ax2.set_xticklabels(agents, rotation=0)
        ax2.legend(loc='upper right')
        ax2.set_ylim(0, 0.9)
        
        for bars in [bars3, bars4]:
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2, height + 0.01,
                        f'{height:.3f}', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(save_path / "figure_2_difficulty_analysis.png")
        plt.close()
        
    def create_figure_3_precision_recall_trade_off(self, results_df, save_path):
        """
        Figure 3: Precision-Recall Trade-off Analysis
        Scatter plot with agent behavior classification
        """
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))
        
        # Calculate average precision and recall
        summary = results_df.groupby('Agent').agg({
            'Precision': 'mean',
            'Recall': 'mean',
            'Accuracy': 'mean'
        }).round(4)
        
        # Create scatter plot
        for agent in summary.index:
            precision = summary.loc[agent, 'Precision']
            recall = summary.loc[agent, 'Recall']
            accuracy = summary.loc[agent, 'Accuracy']
            
            ax.scatter(precision, recall, 
                      color=self.colors[agent], 
                      s=accuracy*1000,  # Size proportional to accuracy
                      alpha=0.7, 
                      edgecolors='black', 
                      linewidth=1.5,
                      label=f'{agent} (Acc: {accuracy:.3f})')
        
        # Add quadrant lines
        ax.axhline(y=0.7, color='gray', linestyle='--', alpha=0.5)
        ax.axvline(x=0.8, color='gray', linestyle='--', alpha=0.5)
        
        # Quadrant labels
        ax.text(0.65, 0.95, 'High Recall\nLow Precision', 
                ha='center', va='center', fontsize=10, 
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        ax.text(0.95, 0.95, 'High Recall\nHigh Precision', 
                ha='center', va='center', fontsize=10,
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
        ax.text(0.95, 0.3, 'Low Recall\nHigh Precision', 
                ha='center', va='center', fontsize=10,
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        ax.text(0.65, 0.3, 'Low Recall\nLow Precision', 
                ha='center', va='center', fontsize=10,
                bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))
        
        ax.set_xlabel('Precision Score')
        ax.set_ylabel('Recall Score')
        ax.set_title('Precision-Recall Trade-off Analysis\n(Bubble size indicates Accuracy)', 
                    fontweight='bold')
        ax.legend(loc='lower left')
        ax.set_xlim(0.5, 1.02)
        ax.set_ylim(0.2, 1.02)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path / "figure_3_precision_recall_tradeoff.png")
        plt.close()
        
    def create_figure_4_performance_heatmap(self, results_df, save_path):
        """
        Figure 4: Comprehensive Performance Heatmap
        Academic-style correlation matrix
        """
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))
        
        # Prepare data for heatmap
        summary = results_df.groupby('Agent').agg({
            'Accuracy': 'mean',
            'F1_Score': 'mean',
            'Precision': 'mean', 
            'Recall': 'mean'
        }).round(4)
        
        # Add derived metrics
        summary['Tool_Success_Rate'] = 1 - results_df.groupby('Agent')['Tool_Fail_Rate'].mean()
        
        # Rename columns for better display
        summary.columns = ['Accuracy', 'F1 Score', 'Precision', 'Recall', 'Tool Success Rate']
        
        # Create heatmap
        sns.heatmap(summary.T, 
                   annot=True, 
                   fmt='.3f',
                   cmap='RdYlGn',
                   vmin=0, vmax=1,
                   cbar_kws={'label': 'Performance Score'},
                   square=True,
                   linewidths=0.5,
                   ax=ax)
        
        ax.set_title('Comprehensive Performance Matrix of Agent Architectures',
                    fontweight='bold', pad=20)
        ax.set_xlabel('Agent Architecture')
        ax.set_ylabel('Performance Metrics')
        
        # Rotate x-axis labels
        plt.xticks(rotation=0)
        plt.yticks(rotation=0)
        
        plt.tight_layout()
        plt.savefig(save_path / "figure_4_performance_heatmap.png")
        plt.close()
        
    def create_figure_5_agent_ranking(self, results_df, save_path):
        """
        Figure 5: Overall Agent Ranking with Confidence Intervals
        Horizontal bar chart with ranking
        """
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        # Calculate weighted overall score
        weights = {'Accuracy': 0.3, 'F1_Score': 0.25, 'Precision': 0.2, 'Recall': 0.25}
        
        summary = results_df.groupby('Agent').agg({
            'Accuracy': 'mean',
            'F1_Score': 'mean',
            'Precision': 'mean',
            'Recall': 'mean'
        })
        
        # Calculate overall score
        overall_scores = []
        for agent in summary.index:
            score = sum(weights[metric] * summary.loc[agent, metric] for metric in weights.keys())
            overall_scores.append(score)
        
        summary['Overall_Score'] = overall_scores
        summary_sorted = summary.sort_values('Overall_Score', ascending=True)
        
        # Create horizontal bar chart
        y_pos = np.arange(len(summary_sorted))
        bars = ax.barh(y_pos, summary_sorted['Overall_Score'],
                      color=[self.colors[agent] for agent in summary_sorted.index],
                      alpha=0.8, edgecolor='black', linewidth=0.5)
        
        # Add value labels
        for i, (bar, score) in enumerate(zip(bars, summary_sorted['Overall_Score'])):
            ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height()/2,
                   f'{score:.3f}', ha='left', va='center', fontsize=11, fontweight='bold')
        
        # Add ranking numbers
        for i, agent in enumerate(summary_sorted.index):
            rank = len(summary_sorted) - i
            ax.text(0.01, i, f'#{rank}', ha='left', va='center', 
                   fontsize=12, fontweight='bold', color='white')
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(summary_sorted.index)
        ax.set_xlabel('Overall Performance Score')
        ax.set_title('Overall Agent Architecture Ranking\n(Weighted Score: Accuracy=30%, F1=25%, Precision=20%, Recall=25%)',
                    fontweight='bold')
        ax.set_xlim(0, max(summary_sorted['Overall_Score']) * 1.15)
        
        # Add score breakdown table
        breakdown_text = "Performance Breakdown:\n"
        for agent in reversed(summary_sorted.index):
            acc = summary.loc[agent, 'Accuracy']
            f1 = summary.loc[agent, 'F1_Score'] 
            prec = summary.loc[agent, 'Precision']
            rec = summary.loc[agent, 'Recall']
            breakdown_text += f"{agent}: A={acc:.3f}, F1={f1:.3f}, P={prec:.3f}, R={rec:.3f}\n"
        
        ax.text(0.75, 0.95, breakdown_text, transform=ax.transAxes, 
               fontsize=9, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(save_path / "figure_5_overall_ranking.png")
        plt.close()

    def create_accuracy_analysis(self, results_df, save_path):
        """
        Individual Accuracy Analysis: Overall + By Difficulty
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Panel A: Overall Accuracy
        overall_accuracy = results_df.groupby('Agent')['Accuracy'].mean()
        agents = overall_accuracy.index
        x_pos = np.arange(len(agents))
        
        bars1 = ax1.bar(x_pos, overall_accuracy, 
                       color=[self.colors[agent] for agent in agents],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax1.set_title('(A) Overall Accuracy Performance', fontweight='bold', loc='left')
        ax1.set_ylabel('Accuracy Score')
        ax1.set_xlabel('Agent Architecture')
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(agents, rotation=0)
        ax1.set_ylim(0, 0.5)
        
        # Add value labels
        for bar, val in zip(bars1, overall_accuracy):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Panel B: Accuracy by Difficulty
        easy_data = results_df[results_df['Difficulty'] == 'dễ'].set_index('Agent')
        hard_data = results_df[results_df['Difficulty'] == 'khó'].set_index('Agent')
        
        x = np.arange(len(agents))
        width = 0.35
        
        bars2 = ax2.bar(x - width/2, easy_data['Accuracy'], width,
                       label='Easy Queries', color=self.colors['easy'],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        bars3 = ax2.bar(x + width/2, hard_data['Accuracy'], width,
                       label='Hard Queries', color=self.colors['hard'],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax2.set_title('(B) Accuracy by Query Difficulty', fontweight='bold', loc='left')
        ax2.set_ylabel('Accuracy Score')
        ax2.set_xlabel('Agent Architecture')
        ax2.set_xticks(x)
        ax2.set_xticklabels(agents, rotation=0)
        ax2.legend(loc='upper right')
        ax2.set_ylim(0, 0.6)
        
        # Add value labels
        for bars in [bars2, bars3]:
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2, height + 0.01,
                        f'{height:.3f}', ha='center', va='bottom', fontsize=9)
        
        plt.suptitle('Accuracy Performance Analysis Across Agent Architectures',
                    fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(save_path / "accuracy_analysis.png")
        plt.close()

    def create_precision_analysis(self, results_df, save_path):
        """
        Individual Precision Analysis: Overall + By Difficulty
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Panel A: Overall Precision
        overall_precision = results_df.groupby('Agent')['Precision'].mean()
        agents = overall_precision.index
        x_pos = np.arange(len(agents))
        
        bars1 = ax1.bar(x_pos, overall_precision,
                       color=[self.colors[agent] for agent in agents],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax1.set_title('(A) Overall Precision Performance', fontweight='bold', loc='left')
        ax1.set_ylabel('Precision Score')
        ax1.set_xlabel('Agent Architecture')
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(agents, rotation=0)
        ax1.set_ylim(0, 1.05)
        
        # Add value labels
        for bar, val in zip(bars1, overall_precision):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Panel B: Precision by Difficulty
        easy_data = results_df[results_df['Difficulty'] == 'dễ'].set_index('Agent')
        hard_data = results_df[results_df['Difficulty'] == 'khó'].set_index('Agent')
        
        x = np.arange(len(agents))
        width = 0.35
        
        bars2 = ax2.bar(x - width/2, easy_data['Precision'], width,
                       label='Easy Queries', color=self.colors['easy'],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        bars3 = ax2.bar(x + width/2, hard_data['Precision'], width,
                       label='Hard Queries', color=self.colors['hard'],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax2.set_title('(B) Precision by Query Difficulty', fontweight='bold', loc='left')
        ax2.set_ylabel('Precision Score')
        ax2.set_xlabel('Agent Architecture')
        ax2.set_xticks(x)
        ax2.set_xticklabels(agents, rotation=0)
        ax2.legend(loc='upper right')
        ax2.set_ylim(0, 1.05)
        
        # Add value labels
        for bars in [bars2, bars3]:
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2, height + 0.02,
                        f'{height:.3f}', ha='center', va='bottom', fontsize=9)
        
        plt.suptitle('Precision Performance Analysis Across Agent Architectures',
                    fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(save_path / "precision_analysis.png")
        plt.close()

    def create_recall_analysis(self, results_df, save_path):
        """
        Individual Recall Analysis: Overall + By Difficulty
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Panel A: Overall Recall
        overall_recall = results_df.groupby('Agent')['Recall'].mean()
        agents = overall_recall.index
        x_pos = np.arange(len(agents))
        
        bars1 = ax1.bar(x_pos, overall_recall,
                       color=[self.colors[agent] for agent in agents],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax1.set_title('(A) Overall Recall Performance', fontweight='bold', loc='left')
        ax1.set_ylabel('Recall Score')
        ax1.set_xlabel('Agent Architecture')
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(agents, rotation=0)
        ax1.set_ylim(0, 1.05)
        
        # Add value labels
        for bar, val in zip(bars1, overall_recall):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Panel B: Recall by Difficulty
        easy_data = results_df[results_df['Difficulty'] == 'dễ'].set_index('Agent')
        hard_data = results_df[results_df['Difficulty'] == 'khó'].set_index('Agent')
        
        x = np.arange(len(agents))
        width = 0.35
        
        bars2 = ax2.bar(x - width/2, easy_data['Recall'], width,
                       label='Easy Queries', color=self.colors['easy'],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        bars3 = ax2.bar(x + width/2, hard_data['Recall'], width,
                       label='Hard Queries', color=self.colors['hard'],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax2.set_title('(B) Recall by Query Difficulty', fontweight='bold', loc='left')
        ax2.set_ylabel('Recall Score')
        ax2.set_xlabel('Agent Architecture')
        ax2.set_xticks(x)
        ax2.set_xticklabels(agents, rotation=0)
        ax2.legend(loc='upper right')
        ax2.set_ylim(0, 1.05)
        
        # Add value labels
        for bars in [bars2, bars3]:
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2, height + 0.02,
                        f'{height:.3f}', ha='center', va='bottom', fontsize=9)
        
        plt.suptitle('Recall Performance Analysis Across Agent Architectures',
                    fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(save_path / "recall_analysis.png")
        plt.close()

    def create_f1_analysis(self, results_df, save_path):
        """
        Individual F1 Score Analysis: Overall + By Difficulty
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Panel A: Overall F1 Score
        overall_f1 = results_df.groupby('Agent')['F1_Score'].mean()
        agents = overall_f1.index
        x_pos = np.arange(len(agents))
        
        bars1 = ax1.bar(x_pos, overall_f1,
                       color=[self.colors[agent] for agent in agents],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax1.set_title('(A) Overall F1 Score Performance', fontweight='bold', loc='left')
        ax1.set_ylabel('F1 Score')
        ax1.set_xlabel('Agent Architecture')
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(agents, rotation=0)
        ax1.set_ylim(0, 0.8)
        
        # Add value labels
        for bar, val in zip(bars1, overall_f1):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Panel B: F1 Score by Difficulty
        easy_data = results_df[results_df['Difficulty'] == 'dễ'].set_index('Agent')
        hard_data = results_df[results_df['Difficulty'] == 'khó'].set_index('Agent')
        
        x = np.arange(len(agents))
        width = 0.35
        
        bars2 = ax2.bar(x - width/2, easy_data['F1_Score'], width,
                       label='Easy Queries', color=self.colors['easy'],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        bars3 = ax2.bar(x + width/2, hard_data['F1_Score'], width,
                       label='Hard Queries', color=self.colors['hard'],
                       alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax2.set_title('(B) F1 Score by Query Difficulty', fontweight='bold', loc='left')
        ax2.set_ylabel('F1 Score')
        ax2.set_xlabel('Agent Architecture')
        ax2.set_xticks(x)
        ax2.set_xticklabels(agents, rotation=0)
        ax2.legend(loc='upper right')
        ax2.set_ylim(0, 0.9)
        
        # Add value labels
        for bars in [bars2, bars3]:
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2, height + 0.01,
                        f'{height:.3f}', ha='center', va='bottom', fontsize=9)
        
        plt.suptitle('F1 Score Performance Analysis Across Agent Architectures',
                    fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(save_path / "f1_analysis.png")
        plt.close()

def main():
    """Main function to generate all academic visualizations"""
    print("🎨 Generating Academic-Style Visualizations...")
    
    # Initialize components
    analyzer = AgentAnalyzer("../evaluation/data_eval/results")
    visualizer = AcademicVisualizer()
    
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
    save_path = Path("results/visualizations")
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
    
    # Generate combined figures (optional)
    print("🎯 Creating Figure 1: Performance Comparison...")
    visualizer.create_figure_1_accuracy_comparison(results_df, save_path)
    
    print("📈 Creating Figure 2: Difficulty Analysis...")
    visualizer.create_figure_2_difficulty_analysis(results_df, save_path)
    
    print("🎪 Creating Figure 3: Precision-Recall Trade-off...")
    visualizer.create_figure_3_precision_recall_trade_off(results_df, save_path)
    
    print("🔥 Creating Figure 4: Performance Heatmap...")
    visualizer.create_figure_4_performance_heatmap(results_df, save_path)
    
    print("🏆 Creating Figure 5: Overall Ranking...")
    visualizer.create_figure_5_agent_ranking(results_df, save_path)
    
    print(f"✅ All academic visualizations saved to: {save_path}")
    print("\n📋 Generated Files:")
    
    # List individual metric files first
    print("\n🎯 Individual Metric Analyses:")
    individual_files = ['accuracy_analysis.png', 'precision_analysis.png', 'recall_analysis.png', 'f1_analysis.png']
    for file_name in individual_files:
        file_path = save_path / file_name
        if file_path.exists():
            print(f"   - {file_name}")
    
    print("\n📊 Combined Figures:")
    for png_file in save_path.glob("figure_*.png"):
        print(f"   - {png_file.name}")
    
    # Generate updated captions file
    captions_file = save_path / "figure_captions.txt"
    with open(captions_file, 'w', encoding='utf-8') as f:
        f.write("FIGURE CAPTIONS FOR ACADEMIC PAPER\n")
        f.write("="*50 + "\n\n")
        
        f.write("INDIVIDUAL METRIC ANALYSES:\n")
        f.write("-"*30 + "\n\n")
        
        f.write("Accuracy Analysis. Performance comparison across agent architectures for accuracy metric.\n")
        f.write("(A) Overall accuracy performance showing percentage of queries with perfect tool selection.\n")
        f.write("(B) Accuracy performance by query difficulty, comparing easy vs hard queries.\n\n")
        
        f.write("Precision Analysis. Performance comparison across agent architectures for precision metric.\n")
        f.write("(A) Overall precision performance showing proportion of selected tools that were relevant.\n")
        f.write("(B) Precision performance by query difficulty, comparing easy vs hard queries.\n\n")
        
        f.write("Recall Analysis. Performance comparison across agent architectures for recall metric.\n")
        f.write("(A) Overall recall performance showing proportion of relevant tools successfully identified.\n")
        f.write("(B) Recall performance by query difficulty, comparing easy vs hard queries.\n\n")
        
        f.write("F1 Score Analysis. Performance comparison across agent architectures for F1 score metric.\n")
        f.write("(A) Overall F1 score performance showing harmonic mean of precision and recall.\n")
        f.write("(B) F1 score performance by query difficulty, comparing easy vs hard queries.\n\n")
        
        f.write("COMBINED FIGURES:\n")
        f.write("-"*30 + "\n\n")
        
        f.write("Figure 1. Performance Comparison of Agent Architectures in Financial Question Answering.\n")
        f.write("(A) Accuracy performance showing the percentage of queries answered with correct tool selection.\n")
        f.write("(B) F1 Score representing the harmonic mean of precision and recall.\n") 
        f.write("(C) Precision indicating the proportion of selected tools that were relevant.\n")
        f.write("(D) Recall showing the proportion of relevant tools that were successfully identified.\n\n")
        
        f.write("Figure 2. Performance Analysis by Query Difficulty.\n")
        f.write("Comparison of (A) accuracy and (B) F1 score performance between easy and hard queries across different agent architectures.\n\n")
        
        f.write("Figure 3. Precision-Recall Trade-off Analysis.\n")
        f.write("Scatter plot showing the relationship between precision and recall for each agent architecture. ")
        f.write("Bubble size indicates accuracy performance. Quadrants represent different behavioral patterns.\n\n")
        
        f.write("Figure 4. Comprehensive Performance Matrix of Agent Architectures.\n")
        f.write("Heatmap visualization of all performance metrics across agent architectures. ")
        f.write("Color intensity represents performance level (green = high, red = low).\n\n")
        
        f.write("Figure 5. Overall Agent Architecture Ranking.\n")
        f.write("Horizontal bar chart showing weighted overall performance scores. ")
        f.write("Weights: Accuracy (30%), F1 Score (25%), Precision (20%), Recall (25%). ")
        f.write("Performance breakdown for each agent is provided in the legend.\n")
    
    print(f"📝 Figure captions saved to: {captions_file}")

if __name__ == "__main__":
    main() 