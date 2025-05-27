#!/usr/bin/env python3
"""
Runner script for Comprehensive Metrics Analysis

This script runs a complete analysis of all evaluation metrics including:
- Exact Accuracy (Flexible and Strict)
- Partial Accuracy (what you requested - credit for partial tool matches)
- F1 Score, Precision, Recall
- Over-selection and Under-selection rates
- Performance by difficulty level

The Partial Accuracy metric addresses your specific need:
- If expected: ['listing_symbol', 'search_web']
- If agent uses: ['listing_symbol'] → Partial Accuracy = 50% (1/2 tools correct)
- If agent uses: ['listing_symbol', 'search_web', 'retrival_db'] → Partial Accuracy = 100% (2/2 required tools found)

Usage:
    python run_comprehensive_analysis.py
"""

import sys
from pathlib import Path
import pandas as pd

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from comprehensive_metrics_analyzer import ComprehensiveMetricsAnalyzer

def main():
    """Main function to run the comprehensive analysis"""
    print("🎯" * 40)
    print("FINANCE NEWS BOT - COMPREHENSIVE METRICS ANALYSIS")
    print("🎯" * 40)
    print()
    
    print("📋 This analysis provides a complete view of all evaluation metrics:")
    print("   • Exact Accuracy (Flexible): Perfect tool set match, order doesn't matter")
    print("   • Exact Accuracy (Strict): Perfect tool set match, order matters")
    print("   • Partial Accuracy: % of required tools correctly identified")
    print("   • F1 Score: Harmonic mean of precision and recall")
    print("   • Precision: % of selected tools that were correct")
    print("   • Recall: % of required tools that were found")
    print("   • Over-selection Rate: % of selected tools that were unnecessary")
    print("   • Under-selection Rate: % of required tools that were missed")
    print()
    
    print("💡 Key Features:")
    print("   ✨ Partial Accuracy gives credit for partial tool selection")
    print("   📊 Comprehensive comparison across all metrics")
    print("   🎚️ Analysis by query difficulty level")
    print("   🔍 Tool selection behavior analysis")
    print()
    
    try:
        # Initialize the analyzer
        print("🚀 Initializing comprehensive metrics analyzer...")
        analyzer = ComprehensiveMetricsAnalyzer()
        
        # Run complete analysis
        results, summary_df, difficulty_df = analyzer.run_complete_comprehensive_analysis()
        
        print("\n" + "📊" * 25)
        print("COMPREHENSIVE METRICS INSIGHTS")
        print("📊" * 25)
        
        # Parse numerical values for ranking
        summary_numeric = summary_df.copy()
        numeric_cols = ['Flexible Accuracy', 'Strict Accuracy', 'Partial Accuracy', 'F1 Score', 'Precision', 'Recall']
        
        for col in numeric_cols:
            try:
                summary_numeric[col] = pd.to_numeric(summary_numeric[col].str.strip(), errors='coerce')
            except Exception as e:
                print(f"Warning: Could not convert column {col} to numeric: {e}")
                summary_numeric[col] = 0.0
        
        print("\n🏆 AGENT PERFORMANCE RANKING:")
        print("-" * 60)
        
        # Rank by different metrics
        rankings = {}
        for metric in ['Flexible Accuracy', 'Strict Accuracy', 'Partial Accuracy', 'F1 Score']:
            sorted_df = summary_numeric.sort_values(metric, ascending=False)
            rankings[metric] = list(sorted_df['Agent'])
        
        print("📈 Rankings by different metrics:")
        for metric, ranked_agents in rankings.items():
            print(f"   {metric:>18}: {' > '.join(ranked_agents)}")
        
        # Overall performance summary
        print(f"\n🎯 DETAILED PERFORMANCE BREAKDOWN:")
        print("-" * 60)
        
        for _, row in summary_numeric.iterrows():
            agent = row['Agent']
            try:
                over_selection = float(summary_numeric[summary_numeric['Agent']==agent]['Over-selection Rate'].iloc[0])
                print(f"\n🤖 {agent}:")
                print(f"   • Flexible Accuracy: {float(row['Flexible Accuracy']):.3f} (perfect match, any order)")
                print(f"   • Strict Accuracy:   {float(row['Strict Accuracy']):.3f} (perfect match, exact order)")
                print(f"   • Partial Accuracy:  {float(row['Partial Accuracy']):.3f} ⭐ (credit for partial matches)")
                print(f"   • F1 Score:          {float(row['F1 Score']):.3f}")
                print(f"   • Precision:         {float(row['Precision']):.3f} (quality of selections)")
                print(f"   • Over-selection:    {over_selection:.3f} (unnecessary tools)")
            except Exception as e:
                print(f"   ⚠️ Error formatting metrics for {agent}: {str(e)}")
        
        # Key insights about partial accuracy
        best_partial = summary_numeric.loc[summary_numeric['Partial Accuracy'].idxmax()]
        worst_partial = summary_numeric.loc[summary_numeric['Partial Accuracy'].idxmin()]
        
        print(f"\n✨ PARTIAL ACCURACY INSIGHTS:")
        print("-" * 50)
        print(f"🥇 Best: {best_partial['Agent']} with {best_partial['Partial Accuracy']:.3f} partial accuracy")
        print(f"🥉 Worst: {worst_partial['Agent']} with {worst_partial['Partial Accuracy']:.3f} partial accuracy")
        
        # Calculate improvement from strict to partial
        improvements = summary_numeric['Partial Accuracy'] - summary_numeric['Strict Accuracy']
        avg_improvement = improvements.mean()
        print(f"📈 Average improvement from Strict to Partial Accuracy: {avg_improvement:.3f}")
        
        if avg_improvement > 0.1:
            print("   💡 Significant improvement! Agents do select some correct tools even when not perfect.")
        
        # Analysis of selection behavior
        print(f"\n🎯 TOOL SELECTION BEHAVIOR:")
        print("-" * 50)
        
        avg_over_selection = summary_numeric['Over-selection Rate'].mean()
        avg_under_selection = summary_numeric['Under-selection Rate'].mean()
        
        print(f"   • Average Over-selection Rate: {avg_over_selection:.3f}")
        print(f"   • Average Under-selection Rate: {avg_under_selection:.3f}")
        
        if avg_over_selection > avg_under_selection:
            print("   📊 Agents tend to select TOO MANY tools (over-selection)")
            print("   💡 Focus training on being more selective")
        else:
            print("   📊 Agents tend to MISS required tools (under-selection)")
            print("   💡 Focus training on tool coverage completeness")
        
        # Difficulty analysis
        if not difficulty_df.empty:
            print(f"\n📚 DIFFICULTY IMPACT ANALYSIS:")
            print("-" * 50)
            
            for _, row in difficulty_df.iterrows():
                agent = row['Agent']
                easy_partial = row['Easy_Partial']
                hard_partial = row['Hard_Partial']
                gap = easy_partial - hard_partial
                
                print(f"   {agent:>12}: Easy {easy_partial:.3f} | Hard {hard_partial:.3f} | Gap {gap:.3f}")
            
            avg_gap = (difficulty_df['Easy_Partial'] - difficulty_df['Hard_Partial']).mean()
            print(f"\n   Average Difficulty Gap (Partial Accuracy): {avg_gap:.3f}")
            
            if avg_gap > 0.15:
                print("   ⚠️  Large difficulty gap - agents struggle with complex queries")
            elif avg_gap > 0.05:
                print("   ⚖️  Moderate difficulty gap - expected performance difference")
            else:
                print("   ✅ Small difficulty gap - agents handle complexity well")
        
        print(f"\n📁 GENERATED ANALYSIS FILES:")
        print("-" * 50)
        
        # Define output directory structure
        output_dir = Path("evaluation/results_visualization/figures")
        figures_structure = {
            'comprehensive': [
                "comprehensive_metrics_comparison.png",
                "metrics_heatmap.png",
                "comprehensive_metrics_summary.csv"
            ],
            'accuracy': [
                "accuracy_types_comparison.png"
            ],
            'selection': [
                "selection_behavior_analysis.png"
            ],
            'difficulty': [
                "comprehensive_difficulty_analysis.png"
            ]
        }
        
        # Create directories if they don't exist
        for subdir in figures_structure.keys():
            (output_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        # Check and report file status by category
        for category, files in figures_structure.items():
            print(f"\n{category.upper()} Metrics:")
            for file in files:
                file_path = output_dir / category / file
                if file_path.exists():
                    print(f"   ✓ {file}")
                else:
                    print(f"   ✗ {file} (not found)")
        
        print(f"\n📂 All comprehensive analysis files saved to: {output_dir}")
        
        print("\n" + "💡" * 25)
        print("ACTIONABLE RECOMMENDATIONS")
        print("💡" * 25)
        
        print("\n🎯 Based on comprehensive analysis:")
        
        # Recommendations based on results
        avg_partial = summary_numeric['Partial Accuracy'].mean()
        avg_precision = summary_numeric['Precision'].mean()
        avg_over_selection = summary_numeric['Over-selection Rate'].mean()
        
        print(f"\n1. 📈 Use Partial Accuracy for Better Insights:")
        print(f"   • Current average: {avg_partial:.3f} (vs strict accuracy which is much lower)")
        print("   • This metric better reflects agent capabilities")
        print("   • Focus training on improving partial accuracy first")
        
        if avg_partial < 0.7:
            print(f"\n2. 🔧 Improve Tool Coverage (Partial Accuracy < 70%):")
            print("   • Agents miss too many required tools")
            print("   • Add more diverse tool selection examples")
            print("   • Implement tool selection confidence scoring")
        
        if avg_precision < 0.7:
            print(f"\n3. 🎯 Improve Selection Precision (< 70%):")
            print("   • Agents select too many incorrect tools")
            print("   • Add negative examples showing wrong tool choices")
            print("   • Implement tool relevance filtering")
        
        if avg_over_selection > 0.3:
            print(f"\n4. ⚡ Reduce Over-selection (> 30%):")
            print("   • Agents are not selective enough")
            print("   • Train with examples of minimal tool sets")
            print("   • Implement tool necessity checks")
        
        print(f"\n5. 📊 Recommended Evaluation Approach:")
        print("   • Primary metric: Partial Accuracy (most informative)")
        print("   • Secondary metrics: F1 Score and Precision")
        print("   • Monitor: Over-selection and Under-selection rates")
        print("   • Use Strict Accuracy only for final validation")
        
        print("\n" + "✅" * 25)
        print("COMPREHENSIVE ANALYSIS COMPLETED!")
        print("✅" * 25)
        
        print(f"\n📝 Your specific question answered:")
        print("   If dataset expects ['listing_symbol', 'search_web']")
        print("   ✅ Agent uses ['listing_symbol', 'search_web'] → 100% partial accuracy")
        print("   ✅ Agent uses ['listing_symbol'] → 50% partial accuracy")
        print("   ❌ Agent uses ['retrival_db', 'search_web'] → 50% partial accuracy")
        print("   📊 This metric gives appropriate credit for partial correctness!")
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        print("\nPlease check that all required data files are present:")
        print("- evaluation/data_eval/results/*.csv")
        print("- evaluation/data_eval/synthetic_data/synthetic_news.csv")
        sys.exit(1)

if __name__ == "__main__":
    main() 