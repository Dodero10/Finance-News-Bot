import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import ast
from collections import Counter
from typing import List, Dict, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

class ComprehensiveMetricsAnalyzer:
    """
    Comprehensive analyzer that combines all types of accuracy metrics:
    - Exact Accuracy (Flexible and Strict)
    - Partial Accuracy
    - F1 Score
    - Precision/Recall
    - Tool-level analysis
    """
    
    def __init__(self, results_dir: str = "evaluation/data_eval/results", 
                 synthetic_dir: str = "evaluation/data_eval/synthetic_data",
                 output_dir: str = "evaluation/results_visualization/figures"):
        """Initialize the comprehensive metrics analyzer"""
        self.results_path = Path(results_dir)
        self.synthetic_path = Path(synthetic_dir)
        self.output_dir = Path(output_dir)
        
        # Create output directories
        for subdir in ['comprehensive', 'accuracy', 'selection', 'difficulty']:
            (self.output_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        # Set style for visualizations
        sns.set_theme(style="whitegrid")
        plt.rcParams['figure.figsize'] = [12, 8]
        plt.rcParams['figure.dpi'] = 300
        
        # Load data
        self.load_data()
        
        # Agent names
        self.agent_names = {
            'multi_agent': 'Multi-Agent',
            'rewoo': 'ReWOO',
            'reflexion': 'Reflexion',
            'react': 'ReAct'
        }

    def load_data(self):
        """Load all required data files"""
        try:
            self.results_data = {}
            self.results_data['multi_agent'] = pd.read_csv(self.results_path / "multi_agent_eval_results.csv")
            self.results_data['rewoo'] = pd.read_csv(self.results_path / "rewoo_agent_eval_results.csv")
            self.results_data['reflexion'] = pd.read_csv(self.results_path / "reflexion_agent_eval_results.csv")
            self.results_data['react'] = pd.read_csv(self.results_path / "react_agent_eval_results.csv")
            self.synthetic_data = pd.read_csv(self.synthetic_path / "synthetic_news.csv")
            
            print("Data loaded successfully for comprehensive metrics analysis!")
                
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            raise

    def parse_tools_string(self, tools_str: str) -> List[str]:
        """Parse tools string into a list of tools"""
        if pd.isna(tools_str) or tools_str == '':
            return []
        
        try:
            tools_str = str(tools_str).strip()
            
            # Remove outer quotes if present
            if tools_str.startswith('"') and tools_str.endswith('"'):
                tools_str = tools_str[1:-1]
            if tools_str.startswith("'") and tools_str.endswith("'"):
                tools_str = tools_str[1:-1]
            
            # Try to evaluate as Python literal
            try:
                tools_list = ast.literal_eval(tools_str)
                if isinstance(tools_list, list):
                    return [str(tool).strip("'\"") for tool in tools_list]
            except:
                pass
            
            # Fallback: manual parsing
            tools_str = tools_str.strip("[]")
            tools = [tool.strip("'\" ") for tool in tools_str.split(",")]
            return [tool for tool in tools if tool and tool != '']
            
        except Exception as e:
            print(f"Error parsing tools string '{tools_str}': {e}")
            return []

    def calculate_all_metrics(self, expected_tools: List[str], actual_tools: List[str]) -> Dict[str, float]:
        """
        Calculate all types of metrics for a single prediction
        
        Args:
            expected_tools: Tools that should be used
            actual_tools: Tools that were actually used
            
        Returns:
            Dictionary with all metrics
        """
        expected_set = set(expected_tools)
        actual_set = set(actual_tools)
        
        # Exact Accuracy - Flexible (order doesn't matter)
        flexible_accuracy = 1.0 if expected_set == actual_set else 0.0
        
        # Exact Accuracy - Strict (order matters)
        strict_accuracy = 1.0 if expected_tools == actual_tools else 0.0
        
        # Partial Accuracy (percentage of required tools found)
        if len(expected_set) == 0:
            partial_accuracy = 1.0 if len(actual_set) == 0 else 0.0
        else:
            correct_tools = len(expected_set.intersection(actual_set))
            partial_accuracy = correct_tools / len(expected_set)
        
        # Precision, Recall, F1
        if len(expected_set) == 0 and len(actual_set) == 0:
            precision = recall = f1_score = 1.0
        elif len(expected_set) == 0:
            precision = recall = f1_score = 0.0
        elif len(actual_set) == 0:
            precision = recall = f1_score = 0.0
        else:
            intersection = len(expected_set.intersection(actual_set))
            precision = intersection / len(actual_set)
            recall = intersection / len(expected_set)
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Over-selection rate
        if len(actual_set) == 0:
            over_selection_rate = 0.0
        else:
            extra_tools = len(actual_set - expected_set)
            over_selection_rate = extra_tools / len(actual_set)
        
        # Under-selection rate
        if len(expected_set) == 0:
            under_selection_rate = 0.0
        else:
            missing_tools = len(expected_set - actual_set)
            under_selection_rate = missing_tools / len(expected_set)
        
        return {
            'flexible_accuracy': flexible_accuracy,
            'strict_accuracy': strict_accuracy,
            'partial_accuracy': partial_accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'over_selection_rate': over_selection_rate,
            'under_selection_rate': under_selection_rate,
            'expected_tools_count': len(expected_set),
            'actual_tools_count': len(actual_set),
            'correct_tools_count': len(expected_set.intersection(actual_set)),
            'extra_tools_count': len(actual_set - expected_set),
            'missing_tools_count': len(expected_set - actual_set)
        }

    def evaluate_agent_comprehensive(self, agent_name: str) -> Dict[str, Any]:
        """Comprehensively evaluate an agent's performance"""
        agent_data = self.results_data[agent_name]
        
        # Merge with synthetic data
        merged_data = pd.merge(
            self.synthetic_data, 
            agent_data, 
            left_on='query', 
            right_on='input', 
            how='inner'
        )
        
        print(f"\n📊 Comprehensively evaluating {agent_name}...")
        
        # Initialize lists for all metrics
        all_metrics = []
        detailed_results = []
        
        for idx, row in merged_data.iterrows():
            expected_tools = self.parse_tools_string(row['tools_x'])
            actual_tools = self.parse_tools_string(row['tools_y'])
            
            # Calculate all metrics
            metrics = self.calculate_all_metrics(expected_tools, actual_tools)
            all_metrics.append(metrics)
            
            detailed_results.append({
                'query': row['query'],
                'difficulty': row['difficulty'],
                'expected_tools': expected_tools,
                'actual_tools': actual_tools,
                **metrics
            })
        
        # Calculate average metrics
        avg_metrics = {}
        for key in all_metrics[0].keys():
            avg_metrics[f'avg_{key}'] = np.mean([m[key] for m in all_metrics])
        
        return {
            'agent': agent_name,
            'total_queries': len(merged_data),
            **avg_metrics,
            'detailed_results': detailed_results,
            'merged_data': merged_data
        }

    def analyze_all_agents_comprehensive(self) -> Dict[str, Dict[str, Any]]:
        """Analyze all agents comprehensively"""
        all_results = {}
        
        for agent_name in self.results_data.keys():
            all_results[agent_name] = self.evaluate_agent_comprehensive(agent_name)
        
        return all_results

    def create_comprehensive_comparison_chart(self, results: Dict[str, Dict[str, Any]]):
        """Create a comprehensive comparison chart of all metrics"""
        agents = list(results.keys())
        agent_labels = [self.agent_names.get(agent, agent) for agent in agents]
        
        # Extract metrics
        metrics_data = {
            'Flexible Accuracy': [results[agent]['avg_flexible_accuracy'] for agent in agents],
            'Strict Accuracy': [results[agent]['avg_strict_accuracy'] for agent in agents],
            'Partial Accuracy': [results[agent]['avg_partial_accuracy'] for agent in agents],
            'F1 Score': [results[agent]['avg_f1_score'] for agent in agents],
            'Precision': [results[agent]['avg_precision'] for agent in agents],
            'Recall': [results[agent]['avg_recall'] for agent in agents]
        }
        
        # Create subplots
        fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2, figsize=(16, 18))
        
        # Colors for each metric
        colors = ['lightblue', 'lightgreen', 'orange', 'lightcoral', 'purple', 'gold']
        
        # Plot each metric
        axes = [ax1, ax2, ax3, ax4, ax5, ax6]
        metric_names = list(metrics_data.keys())
        
        for i, (ax, metric_name, color) in enumerate(zip(axes, metric_names, colors)):
            values = metrics_data[metric_name]
            bars = ax.bar(agent_labels, values, color=color, alpha=0.8)
            
            ax.set_title(f'{metric_name}', fontweight='bold', fontsize=12)
            ax.set_ylabel('Score')
            ax.set_ylim(0, 1.0)
            ax.grid(axis='y', alpha=0.3)
            
            # Add value labels
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                       f'{val:.3f}', ha='center', va='bottom', fontweight='bold', fontsize=10)
        
        plt.suptitle('Comprehensive Metrics Comparison - Finance News Bot', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'comprehensive' / 'comprehensive_metrics_comparison.png', bbox_inches='tight')
        plt.close()

    def create_accuracy_types_comparison(self, results: Dict[str, Dict[str, Any]]):
        """Compare different types of accuracy metrics"""
        agents = list(results.keys())
        agent_labels = [self.agent_names.get(agent, agent) for agent in agents]
        
        flexible_acc = [results[agent]['avg_flexible_accuracy'] for agent in agents]
        strict_acc = [results[agent]['avg_strict_accuracy'] for agent in agents]
        partial_acc = [results[agent]['avg_partial_accuracy'] for agent in agents]
        
        x = np.arange(len(agent_labels))
        width = 0.25
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        bars1 = ax.bar(x - width, flexible_acc, width, label='Flexible Accuracy', color='lightblue', alpha=0.8)
        bars2 = ax.bar(x, strict_acc, width, label='Strict Accuracy', color='orange', alpha=0.8)
        bars3 = ax.bar(x + width, partial_acc, width, label='Partial Accuracy', color='lightgreen', alpha=0.8)
        
        # Add value labels
        for bars, values in [(bars1, flexible_acc), (bars2, strict_acc), (bars3, partial_acc)]:
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                       f'{val:.3f}', ha='center', va='bottom', fontweight='bold', fontsize=9)
        
        ax.set_title('Comparison of Different Accuracy Types', fontsize=14, fontweight='bold')
        ax.set_ylabel('Accuracy Score')
        ax.set_xlabel('Agent')
        ax.set_xticks(x)
        ax.set_xticklabels(agent_labels)
        ax.legend()
        ax.set_ylim(0, 1.0)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'accuracy' / 'accuracy_types_comparison.png', bbox_inches='tight')
        plt.close()

    def create_selection_behavior_analysis(self, results: Dict[str, Dict[str, Any]]):
        """Analyze over-selection and under-selection behavior"""
        agents = list(results.keys())
        agent_labels = [self.agent_names.get(agent, agent) for agent in agents]
        
        over_selection = [results[agent]['avg_over_selection_rate'] for agent in agents]
        under_selection = [results[agent]['avg_under_selection_rate'] for agent in agents]
        
        x = np.arange(len(agent_labels))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        bars1 = ax.bar(x - width/2, over_selection, width, label='Over-selection Rate', color='lightcoral', alpha=0.8)
        bars2 = ax.bar(x + width/2, under_selection, width, label='Under-selection Rate', color='lightsalmon', alpha=0.8)
        
        # Add value labels
        for bars, values in [(bars1, over_selection), (bars2, under_selection)]:
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                       f'{val:.3f}', ha='center', va='bottom', fontweight='bold', fontsize=10)
        
        ax.set_title('Tool Selection Behavior Analysis', fontsize=14, fontweight='bold')
        ax.set_ylabel('Rate')
        ax.set_xlabel('Agent')
        ax.set_xticks(x)
        ax.set_xticklabels(agent_labels)
        ax.legend()
        ax.set_ylim(0, max(max(over_selection), max(under_selection)) + 0.1)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'selection' / 'selection_behavior_analysis.png', bbox_inches='tight')
        plt.close()

    def generate_comprehensive_summary_table(self, results: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
        """Generate comprehensive summary table"""
        summary_data = []
        
        for agent_name, agent_results in results.items():
            summary_data.append({
                'Agent': self.agent_names.get(agent_name, agent_name),
                'Total Queries': agent_results['total_queries'],
                'Flexible Accuracy': f"{agent_results['avg_flexible_accuracy']:.4f}",
                'Strict Accuracy': f"{agent_results['avg_strict_accuracy']:.4f}",
                'Partial Accuracy': f"{agent_results['avg_partial_accuracy']:.4f}",
                'F1 Score': f"{agent_results['avg_f1_score']:.4f}",
                'Precision': f"{agent_results['avg_precision']:.4f}",
                'Recall': f"{agent_results['avg_recall']:.4f}",
                'Over-selection Rate': f"{agent_results['avg_over_selection_rate']:.4f}",
                'Under-selection Rate': f"{agent_results['avg_under_selection_rate']:.4f}"
            })
        
        summary_df = pd.DataFrame(summary_data)
        
        # Save to CSV
        summary_df.to_csv(self.output_dir / 'comprehensive' / 'comprehensive_metrics_summary.csv', index=False)
        
        return summary_df

    def analyze_difficulty_impact_comprehensive(self, results: Dict[str, Dict[str, Any]]):
        """Analyze comprehensive metrics by difficulty"""
        difficulty_data = []
        
        for agent_name, agent_results in results.items():
            agent_label = self.agent_names.get(agent_name, agent_name)
            
            # Group by difficulty
            easy_results = [r for r in agent_results['detailed_results'] if r['difficulty'] == 'dễ']
            hard_results = [r for r in agent_results['detailed_results'] if r['difficulty'] == 'khó']
            
            # Calculate averages for each difficulty
            metrics_by_difficulty = {}
            
            for difficulty, results_subset in [('Easy', easy_results), ('Hard', hard_results)]:
                if results_subset:
                    metrics_by_difficulty[f'{difficulty}_Flexible'] = np.mean([r['flexible_accuracy'] for r in results_subset])
                    metrics_by_difficulty[f'{difficulty}_Strict'] = np.mean([r['strict_accuracy'] for r in results_subset])
                    metrics_by_difficulty[f'{difficulty}_Partial'] = np.mean([r['partial_accuracy'] for r in results_subset])
                    metrics_by_difficulty[f'{difficulty}_F1'] = np.mean([r['f1_score'] for r in results_subset])
                else:
                    metrics_by_difficulty[f'{difficulty}_Flexible'] = 0
                    metrics_by_difficulty[f'{difficulty}_Strict'] = 0
                    metrics_by_difficulty[f'{difficulty}_Partial'] = 0
                    metrics_by_difficulty[f'{difficulty}_F1'] = 0
            
            difficulty_data.append({
                'Agent': agent_label,
                **metrics_by_difficulty
            })
        
        df_difficulty = pd.DataFrame(difficulty_data)
        
        # Create visualization
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        x = np.arange(len(df_difficulty['Agent']))
        width = 0.35
        
        # Flexible Accuracy
        bars1 = ax1.bar(x - width/2, df_difficulty['Easy_Flexible'], width, 
                       label='Easy', color='lightgreen', alpha=0.8)
        bars2 = ax1.bar(x + width/2, df_difficulty['Hard_Flexible'], width,
                       label='Hard', color='orange', alpha=0.8)
        ax1.set_title('Flexible Accuracy by Difficulty')
        ax1.set_xticks(x)
        ax1.set_xticklabels(df_difficulty['Agent'])
        ax1.legend()
        ax1.set_ylim(0, 1.0)
        
        # Strict Accuracy
        bars3 = ax2.bar(x - width/2, df_difficulty['Easy_Strict'], width, 
                       label='Easy', color='lightblue', alpha=0.8)
        bars4 = ax2.bar(x + width/2, df_difficulty['Hard_Strict'], width,
                       label='Hard', color='purple', alpha=0.8)
        ax2.set_title('Strict Accuracy by Difficulty')
        ax2.set_xticks(x)
        ax2.set_xticklabels(df_difficulty['Agent'])
        ax2.legend()
        ax2.set_ylim(0, 1.0)
        
        # Partial Accuracy
        bars5 = ax3.bar(x - width/2, df_difficulty['Easy_Partial'], width, 
                       label='Easy', color='gold', alpha=0.8)
        bars6 = ax3.bar(x + width/2, df_difficulty['Hard_Partial'], width,
                       label='Hard', color='red', alpha=0.8)
        ax3.set_title('Partial Accuracy by Difficulty')
        ax3.set_xticks(x)
        ax3.set_xticklabels(df_difficulty['Agent'])
        ax3.legend()
        ax3.set_ylim(0, 1.0)
        
        # F1 Score
        bars7 = ax4.bar(x - width/2, df_difficulty['Easy_F1'], width, 
                       label='Easy', color='pink', alpha=0.8)
        bars8 = ax4.bar(x + width/2, df_difficulty['Hard_F1'], width,
                       label='Hard', color='brown', alpha=0.8)
        ax4.set_title('F1 Score by Difficulty')
        ax4.set_xticks(x)
        ax4.set_xticklabels(df_difficulty['Agent'])
        ax4.legend()
        ax4.set_ylim(0, 1.0)
        
        plt.suptitle('Comprehensive Metrics by Query Difficulty', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'difficulty' / 'comprehensive_difficulty_analysis.png', bbox_inches='tight')
        plt.close()
        
        return df_difficulty

    def run_complete_comprehensive_analysis(self):
        """Run complete comprehensive analysis"""
        print("🎯 Starting Comprehensive Metrics Analysis...")
        print("=" * 60)
        
        # Analyze all agents
        results = self.analyze_all_agents_comprehensive()
        
        # Generate summary table
        print("\n📊 Generating comprehensive summary...")
        summary_df = self.generate_comprehensive_summary_table(results)
        print("\nComprehensive Metrics Summary:")
        print(summary_df.to_string(index=False))
        
        # Generate visualizations
        print("\n📈 Creating comprehensive visualizations...")
        self.create_comprehensive_comparison_chart(results)
        print("✓ Comprehensive metrics comparison saved")
        
        self.create_accuracy_types_comparison(results)
        print("✓ Accuracy types comparison saved")
        
        self.create_selection_behavior_analysis(results)
        print("✓ Selection behavior analysis saved")
        
        difficulty_df = self.analyze_difficulty_impact_comprehensive(results)
        print("✓ Comprehensive difficulty analysis saved")
        
        print(f"\n📁 All comprehensive analysis files saved to: {self.output_dir}")
        print("✅ Comprehensive metrics analysis complete!")
        
        return results, summary_df, difficulty_df

    def plot_metrics_heatmap(self, results: Dict[str, Dict[str, Any]]):
        """Create a heatmap of all metrics"""
        # ... existing code ...
        plt.tight_layout()
        plt.savefig(self.output_dir / 'comprehensive' / 'metrics_heatmap.png', bbox_inches='tight')
        plt.close()

if __name__ == "__main__":
    # Run comprehensive analysis
    analyzer = ComprehensiveMetricsAnalyzer()
    results, summary, difficulty = analyzer.run_complete_comprehensive_analysis() 