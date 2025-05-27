#!/usr/bin/env python3
"""
Runner script for Finance News Bot Metrics Analysis

This script runs a comprehensive analysis of evaluation metrics including:
- Flexible Accuracy (Exact Match Tool Call)
- F1 Score
- Precision and Recall
- Performance by query difficulty

Usage:
    python run_metrics_analysis.py
"""

import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from metrics_analyzer import MetricsAnalyzer

def main():
    """Main function to run the metrics analysis"""
    print("=" * 60)
    print("Finance News Bot - Metrics Analysis")
    print("=" * 60)
    print()
    
    try:
        # Initialize the analyzer
        print("Initializing metrics analyzer...")
        analyzer = MetricsAnalyzer()
        
        # Run complete analysis
        results, summary_df = analyzer.run_complete_analysis()
        
        print("\n" + "=" * 60)
        print("ANALYSIS RESULTS SUMMARY")
        print("=" * 60)
        
        # Display key findings
        print("\n📊 Key Findings:")
        print("-" * 40)
        
        # Find best performing agent for each metric
        best_flexible_accuracy = max(results.items(), key=lambda x: x[1]['flexible_accuracy'])
        best_f1 = max(results.items(), key=lambda x: x[1]['f1_score'])
        best_precision = max(results.items(), key=lambda x: x[1]['precision'])
        best_recall = max(results.items(), key=lambda x: x[1]['recall'])
        
        agent_names = {
            'multi_agent': 'Multi-Agent',
            'rewoo': 'ReWOO',
            'reflexion': 'Reflexion',
            'react': 'ReAct'
        }
        
        print(f"🎯 Best Flexible Accuracy: {agent_names.get(best_flexible_accuracy[0], best_flexible_accuracy[0])} ({best_flexible_accuracy[1]['flexible_accuracy']:.4f})")
        print(f"🎯 Best F1 Score: {agent_names.get(best_f1[0], best_f1[0])} ({best_f1[1]['f1_score']:.4f})")
        print(f"🎯 Best Precision: {agent_names.get(best_precision[0], best_precision[0])} ({best_precision[1]['precision']:.4f})")
        print(f"🎯 Best Recall: {agent_names.get(best_recall[0], best_recall[0])} ({best_recall[1]['recall']:.4f})")
        
        # Calculate averages
        avg_flexible_accuracy = sum(r['flexible_accuracy'] for r in results.values()) / len(results)
        avg_f1 = sum(r['f1_score'] for r in results.values()) / len(results)
        
        print(f"\n📈 Average Performance:")
        print(f"   • Average Flexible Accuracy: {avg_flexible_accuracy:.4f}")
        print(f"   • Average F1 Score: {avg_f1:.4f}")
        
        print("\n📁 Generated Files:")
        print("-" * 40)
        
        # Define output directories
        output_dirs = {
            'accuracy': Path("evaluation/results_visualization/figures/accuracy"),
            'f1_score': Path("evaluation/results_visualization/figures/f1_score"),
            'partial': Path("evaluation/results_visualization/figures/partial"),
            'difficulty': Path("evaluation/results_visualization/figures/difficulty"),
            'comprehensive': Path("evaluation/results_visualization/figures/comprehensive")
        }
        
        # Define expected files in each directory
        expected_files = {
            'accuracy': ["flexible_accuracy_comparison.png"],
            'f1_score': ["f1_score_comparison.png"],
            'difficulty': ["difficulty_based_performance.png"],
            'comprehensive': ["comprehensive_metrics.png", "metrics_heatmap.png", "metrics_summary.csv"]
        }
        
        # Check and report file status
        for dir_name, files in expected_files.items():
            print(f"\n{dir_name.upper()} Metrics:")
            for file in files:
                file_path = output_dirs[dir_name] / file
                if file_path.exists():
                    print(f"   ✓ {file}")
                else:
                    print(f"   ✗ {file} (not found)")
        
        print("\n" + "=" * 60)
        print("Analysis completed successfully! 🎉")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        print("\nPlease check that all required data files are present:")
        print("- evaluation/data_eval/results/*.csv")
        print("- evaluation/data_eval/synthetic_data/synthetic_news.csv")
        sys.exit(1)

if __name__ == "__main__":
    main() 