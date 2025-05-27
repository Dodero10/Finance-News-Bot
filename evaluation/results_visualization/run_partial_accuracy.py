#!/usr/bin/env python3
"""
Runner script for Partial Tool Accuracy Analysis

This script analyzes tool selection performance using partial matching:
- Partial Accuracy: Percentage of required tools correctly selected
- Tool Coverage: How well agents cover required tools
- Precision: Accuracy of selected tools
- Over-selection Rate: How often unnecessary tools are selected

The key difference from exact accuracy:
- If expected: ['listing_symbol', 'search_web']
- If agent uses: ['listing_symbol'] → Partial Accuracy = 50%
- If agent uses: ['listing_symbol', 'search_web', 'retrieval_db'] → Partial Accuracy = 100%, Precision = 67%

Usage:
    python run_partial_accuracy.py
"""

import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from partial_accuracy_analyzer import PartialAccuracyAnalyzer

def main():
    """Main function to run the partial accuracy analysis"""
    print("🎯" * 30)
    print("FINANCE NEWS BOT - PARTIAL TOOL ACCURACY ANALYSIS")
    print("🎯" * 30)
    print()
    
    print("📋 This analysis measures partial tool matching performance:")
    print("   • Partial Accuracy: % of required tools found")
    print("   • Tool Coverage: Same as partial accuracy")
    print("   • Precision: % of selected tools that were correct")
    print("   • Recall: % of required tools that were found")
    print("   • Over-selection Rate: % of selected tools that were unnecessary")
    print()
    
    print("💡 Key Insight:")
    print("   Unlike exact matching, agents get credit for partial tool selection.")
    print("   Example:")
    print("   - Expected: ['listing_symbol', 'search_web']")
    print("   - Agent uses: ['listing_symbol'] → Partial Accuracy = 50%")
    print("   - Agent uses: ['listing_symbol', 'search_web', 'retrieval_db'] → Partial Accuracy = 100%, Precision = 67%")
    print()
    
    try:
        # Initialize the analyzer
        print("🚀 Initializing partial accuracy analyzer...")
        analyzer = PartialAccuracyAnalyzer()
        
        # Run complete analysis
        results, summary_df, difficulty_df = analyzer.run_complete_partial_analysis()
        
        print("\n" + "📊" * 20)
        print("PARTIAL ACCURACY INSIGHTS")
        print("📊" * 20)
        
        # Parse numerical values from summary for comparison
        print("\n🎯 PARTIAL ACCURACY COMPARISON:")
        print("-" * 50)
        
        summary_numeric = summary_df.copy()
        numeric_cols = ['Partial Accuracy', 'Precision', 'Recall', 'Over-selection Rate']
        for col in numeric_cols:
            summary_numeric[col] = summary_numeric[col].astype(float)
        
        # Sort by partial accuracy
        summary_numeric = summary_numeric.sort_values('Partial Accuracy', ascending=False)
        
        for _, row in summary_numeric.iterrows():
            print(f"{row['Agent']:>12}: {row['Partial Accuracy']:.3f} partial accuracy | {row['Precision']:.3f} precision")
        
        # Calculate improvement over exact accuracy
        print(f"\n📈 IMPROVEMENT OVER EXACT ACCURACY:")
        print("-" * 50)
        print("   Partial accuracy is generally higher than exact accuracy because")
        print("   agents get credit for selecting some correct tools even if not perfect.")
        
        # Best and worst performing agents
        best_agent = summary_numeric.iloc[0]
        worst_agent = summary_numeric.iloc[-1]
        
        print(f"\n🏆 BEST PERFORMING AGENT:")
        print(f"   {best_agent['Agent']}: {best_agent['Partial Accuracy']:.3f} partial accuracy")
        print(f"   - Precision: {best_agent['Precision']:.3f} (tool selection quality)")
        print(f"   - Over-selection: {best_agent['Over-selection Rate']:.3f} (unnecessary tools)")
        
        print(f"\n🔍 AREAS FOR IMPROVEMENT:")
        print("-" * 40)
        
        # Identify common issues
        high_over_selection = summary_numeric[summary_numeric['Over-selection Rate'] > 0.3]
        low_precision = summary_numeric[summary_numeric['Precision'] < 0.7]
        low_partial_accuracy = summary_numeric[summary_numeric['Partial Accuracy'] < 0.7]
        
        if not high_over_selection.empty:
            print("⚠️  High over-selection (>30% unnecessary tools):")
            for _, row in high_over_selection.iterrows():
                print(f"   • {row['Agent']}: {row['Over-selection Rate']:.1%} over-selection rate")
        
        if not low_precision.empty:
            print("⚠️  Low precision (<70% correct tools):")
            for _, row in low_precision.iterrows():
                print(f"   • {row['Agent']}: {row['Precision']:.1%} precision")
        
        if not low_partial_accuracy.empty:
            print("⚠️  Low partial accuracy (<70% required tools found):")
            for _, row in low_partial_accuracy.iterrows():
                print(f"   • {row['Agent']}: {row['Partial Accuracy']:.1%} partial accuracy")
        
        # Difficulty analysis
        if not difficulty_df.empty:
            print(f"\n📚 DIFFICULTY IMPACT:")
            print("-" * 40)
            
            for _, row in difficulty_df.iterrows():
                easy_acc = row['Easy_Partial_Accuracy']
                hard_acc = row['Hard_Partial_Accuracy']
                gap = easy_acc - hard_acc
                
                print(f"{row['Agent']:>12}: Easy {easy_acc:.3f} | Hard {hard_acc:.3f} | Gap {gap:.3f}")
            
            avg_gap = (difficulty_df['Easy_Partial_Accuracy'] - difficulty_df['Hard_Partial_Accuracy']).mean()
            if avg_gap > 0.1:
                print(f"   ⚠️  Significant difficulty gap detected (avg: {avg_gap:.3f})")
            else:
                print(f"   ✅ Reasonable difficulty gap (avg: {avg_gap:.3f})")
        
        print(f"\n📁 GENERATED FILES:")
        print("-" * 40)
        
        # Define output directory structure
        output_dir = Path("evaluation/results_visualization/figures")
        figures_structure = {
            'partial': [
                "partial_accuracy_comparison.png",
                "tool_success_matrix.png",
                "partial_accuracy_summary.csv"
            ],
            'difficulty': [
                "partial_difficulty_analysis.png"
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
        
        print(f"\n📂 All analysis files saved to: {output_dir}")
        
        print("\n" + "💡" * 20)
        print("RECOMMENDATIONS")
        print("💡" * 20)
        
        print("\n🎯 Based on partial accuracy analysis:")
        
        # Recommendations based on results
        avg_partial_acc = summary_numeric['Partial Accuracy'].mean()
        avg_precision = summary_numeric['Precision'].mean() 
        avg_over_selection = summary_numeric['Over-selection Rate'].mean()
        
        if avg_partial_acc < 0.7:
            print("   1. 🔧 Improve Tool Coverage:")
            print("      • Focus on training agents to identify ALL required tools")
            print("      • Review tool selection patterns in training data")
        
        if avg_precision < 0.7:
            print("   2. 🎯 Improve Precision:")
            print("      • Reduce selection of unnecessary tools")
            print("      • Add negative examples in training")
        
        if avg_over_selection > 0.3:
            print("   3. ⚡ Reduce Over-selection:")
            print("      • Train agents to be more selective")
            print("      • Implement tool selection confidence thresholds")
        
        print("   4. 📊 Use Partial Accuracy for Training:")
        print("      • Partial accuracy provides better training signal than exact matching")
        print("      • Focus on improving tool coverage first, then precision")
        
        print("\n" + "✅" * 20)
        print("PARTIAL ACCURACY ANALYSIS COMPLETED!")
        print("✅" * 20)
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        print("\nPlease check that all required data files are present:")
        print("- evaluation/data_eval/results/*.csv")
        print("- evaluation/data_eval/synthetic_data/synthetic_news.csv")
        sys.exit(1)

if __name__ == "__main__":
    main() 