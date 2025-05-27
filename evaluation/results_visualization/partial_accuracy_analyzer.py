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

class PartialAccuracyAnalyzer:
    """
    Analyzer for partial tool accuracy where agents get credit for selecting
    some correct tools even if not a perfect match.
    
    Metrics:
    - Partial Accuracy: Percentage of required tools correctly selected
    - Tool Coverage: Percentage of required tools that were found
    - Over-selection Rate: How often unnecessary tools are selected
    """
    
    def __init__(self, results_dir: str = "evaluation/data_eval/results", 
                 synthetic_dir: str = "evaluation/data_eval/synthetic_data",
                 output_dir: str = "evaluation/results_visualization/figures"):
        """Initialize the partial accuracy analyzer"""
        self.results_path = Path(results_dir)
        self.synthetic_path = Path(synthetic_dir)
        self.output_dir = Path(output_dir)
        
        # Create output directories
        for subdir in ['partial', 'difficulty']:
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
            
            print("Data loaded successfully for partial accuracy analysis!")
                
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

    def calculate_partial_metrics(self, expected_tools: List[str], actual_tools: List[str]) -> Dict[str, float]:
        """
        Calculate partial accuracy metrics
        
        Args:
            expected_tools: Tools that should be used
            actual_tools: Tools that were actually used
            
        Returns:
            Dictionary with partial accuracy metrics
        """
        expected_set = set(expected_tools)
        actual_set = set(actual_tools)
        
        # Handle edge cases
        if len(expected_set) == 0 and len(actual_set) == 0:
            return {
                'partial_accuracy': 1.0,
                'tool_coverage': 1.0,
                'precision': 1.0,
                'recall': 1.0,
                'over_selection_rate': 0.0,
                'correct_tools': 0,
                'total_expected': 0,
                'total_actual': 0
            }
        
        if len(expected_set) == 0:
            return {
                'partial_accuracy': 0.0,
                'tool_coverage': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'over_selection_rate': 1.0,
                'correct_tools': 0,
                'total_expected': 0,
                'total_actual': len(actual_set)
            }
        
        # Calculate intersections
        correct_tools = len(expected_set.intersection(actual_set))
        
        # Partial Accuracy: Percentage of expected tools found
        partial_accuracy = correct_tools / len(expected_set)
        
        # Tool Coverage: Same as partial accuracy (what percentage of required tools were found)
        tool_coverage = partial_accuracy
        
        # Precision: Of the tools selected, how many were correct
        precision = correct_tools / len(actual_set) if len(actual_set) > 0 else 0.0
        
        # Recall: Of the required tools, how many were found
        recall = correct_tools / len(expected_set)
        
        # Over-selection Rate: How many unnecessary tools were selected
        extra_tools = len(actual_set - expected_set)
        over_selection_rate = extra_tools / len(actual_set) if len(actual_set) > 0 else 0.0
        
        return {
            'partial_accuracy': partial_accuracy,
            'tool_coverage': tool_coverage,
            'precision': precision,
            'recall': recall,
            'over_selection_rate': over_selection_rate,
            'correct_tools': correct_tools,
            'total_expected': len(expected_set),
            'total_actual': len(actual_set)
        }

    def analyze_agent_partial_performance(self, agent_name: str) -> Dict[str, Any]:
        """Analyze partial performance of a specific agent"""
        agent_data = self.results_data[agent_name]
        
        # Merge with synthetic data
        merged_data = pd.merge(
            self.synthetic_data, 
            agent_data, 
            left_on='query', 
            right_on='input', 
            how='inner'
        )
        
        print(f"\n📊 Analyzing {agent_name} partial accuracy...")
        
        # Initialize metrics lists
        partial_accuracies = []
        tool_coverages = []
        precisions = []
        recalls = []
        over_selection_rates = []
        
        detailed_results = []
        
        for idx, row in merged_data.iterrows():
            expected_tools = self.parse_tools_string(row['tools_x'])
            actual_tools = self.parse_tools_string(row['tools_y'])
            
            # Calculate partial metrics
            metrics = self.calculate_partial_metrics(expected_tools, actual_tools)
            
            partial_accuracies.append(metrics['partial_accuracy'])
            tool_coverages.append(metrics['tool_coverage'])
            precisions.append(metrics['precision'])
            recalls.append(metrics['recall'])
            over_selection_rates.append(metrics['over_selection_rate'])
            
            detailed_results.append({
                'query': row['query'],
                'difficulty': row['difficulty'],
                'expected_tools': expected_tools,
                'actual_tools': actual_tools,
                'partial_accuracy': metrics['partial_accuracy'],
                'tool_coverage': metrics['tool_coverage'],
                'precision': metrics['precision'],
                'recall': metrics['recall'],
                'over_selection_rate': metrics['over_selection_rate'],
                'correct_tools': metrics['correct_tools'],
                'total_expected': metrics['total_expected'],
                'total_actual': metrics['total_actual']
            })
        
        # Calculate averages
        return {
            'agent': agent_name,
            'total_queries': len(merged_data),
            'avg_partial_accuracy': np.mean(partial_accuracies),
            'avg_tool_coverage': np.mean(tool_coverages),
            'avg_precision': np.mean(precisions),
            'avg_recall': np.mean(recalls),
            'avg_over_selection_rate': np.mean(over_selection_rates),
            'partial_accuracies': partial_accuracies,
            'tool_coverages': tool_coverages,
            'precisions': precisions,
            'recalls': recalls,
            'over_selection_rates': over_selection_rates,
            'detailed_results': detailed_results,
            'merged_data': merged_data
        }

    def analyze_all_agents_partial(self) -> Dict[str, Dict[str, Any]]:
        """Analyze partial performance of all agents"""
        all_results = {}
        
        for agent_name in self.results_data.keys():
            all_results[agent_name] = self.analyze_agent_partial_performance(agent_name)
        
        return all_results

    def plot_partial_accuracy_comparison(self, results: Dict[str, Dict[str, Any]]):
        """Plot partial accuracy comparison across agents"""
        agents = list(results.keys())
        agent_labels = [self.agent_names.get(agent, agent) for agent in agents]
        
        partial_accuracies = [results[agent]['avg_partial_accuracy'] for agent in agents]
        tool_coverages = [results[agent]['avg_tool_coverage'] for agent in agents]
        precisions = [results[agent]['avg_precision'] for agent in agents]
        over_selection_rates = [results[agent]['avg_over_selection_rate'] for agent in agents]
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Partial Accuracy
        bars1 = ax1.bar(agent_labels, partial_accuracies, color='lightblue', alpha=0.8)
        ax1.set_title('Partial Accuracy\n(% of Required Tools Found)', fontweight='bold')
        ax1.set_ylabel('Score')
        ax1.set_ylim(0, 1.0)
        ax1.grid(axis='y', alpha=0.3)
        
        for bar, acc in zip(bars1, partial_accuracies):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{acc:.3f}', ha='center', va='bottom', fontweight='bold')
        
        # Tool Coverage
        bars2 = ax2.bar(agent_labels, tool_coverages, color='lightgreen', alpha=0.8)
        ax2.set_title('Tool Coverage\n(Same as Partial Accuracy)', fontweight='bold')
        ax2.set_ylabel('Score')
        ax2.set_ylim(0, 1.0)
        ax2.grid(axis='y', alpha=0.3)
        
        for bar, cov in zip(bars2, tool_coverages):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{cov:.3f}', ha='center', va='bottom', fontweight='bold')
        
        # Precision
        bars3 = ax3.bar(agent_labels, precisions, color='orange', alpha=0.8)
        ax3.set_title('Precision\n(% of Selected Tools that were Correct)', fontweight='bold')
        ax3.set_ylabel('Score')
        ax3.set_ylim(0, 1.0)
        ax3.grid(axis='y', alpha=0.3)
        
        for bar, prec in zip(bars3, precisions):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{prec:.3f}', ha='center', va='bottom', fontweight='bold')
        
        # Over-selection Rate
        bars4 = ax4.bar(agent_labels, over_selection_rates, color='lightcoral', alpha=0.8)
        ax4.set_title('Over-selection Rate\n(% of Selected Tools that were Unnecessary)', fontweight='bold')
        ax4.set_ylabel('Rate')
        ax4.set_ylim(0, 1.0)
        ax4.grid(axis='y', alpha=0.3)
        
        for bar, rate in zip(bars4, over_selection_rates):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{rate:.3f}', ha='center', va='bottom', fontweight='bold')
        
        plt.suptitle('Partial Tool Accuracy Analysis', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'partial' / 'partial_accuracy_comparison.png', bbox_inches='tight')
        plt.close()

    def create_tool_success_matrix(self, results: Dict[str, Dict[str, Any]]):
        """Create a matrix showing success rate for each tool across agents"""
        
        # Collect all tools and their success rates
        tool_success_data = {}
        
        for agent_name, agent_results in results.items():
            agent_label = self.agent_names.get(agent_name, agent_name)
            tool_success_data[agent_label] = {}
            
            # Count successes for each tool
            tool_counts = {}
            tool_successes = {}
            
            for result in agent_results['detailed_results']:
                expected_tools = result['expected_tools']
                actual_tools = result['actual_tools']
                
                for tool in expected_tools:
                    if tool not in tool_counts:
                        tool_counts[tool] = 0
                        tool_successes[tool] = 0
                    
                    tool_counts[tool] += 1
                    if tool in actual_tools:
                        tool_successes[tool] += 1
            
            # Calculate success rates
            for tool in tool_counts:
                success_rate = tool_successes[tool] / tool_counts[tool]
                tool_success_data[agent_label][tool] = success_rate
        
        # Get all unique tools
        all_tools = set()
        for agent_data in tool_success_data.values():
            all_tools.update(agent_data.keys())
        all_tools = sorted(list(all_tools))
        
        # Create matrix
        matrix_data = []
        for agent in tool_success_data.keys():
            row = [tool_success_data[agent].get(tool, 0) for tool in all_tools]
            matrix_data.append(row)
        
        matrix_data = np.array(matrix_data)
        
        # Create heatmap
        plt.figure(figsize=(12, 8))
        sns.heatmap(matrix_data, 
                   xticklabels=all_tools,
                   yticklabels=list(tool_success_data.keys()),
                   annot=True, 
                   fmt='.2f',
                   cmap='RdYlGn',
                   vmin=0, vmax=1,
                   cbar_kws={'label': 'Success Rate'})
        
        plt.title('Tool Success Rate Matrix\n(How often each tool is correctly identified when needed)', 
                 fontsize=14, fontweight='bold')
        plt.xlabel('Tools')
        plt.ylabel('Agents')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'partial' / 'tool_success_matrix.png', bbox_inches='tight')
        plt.close()

    def analyze_difficulty_partial_performance(self, results: Dict[str, Dict[str, Any]]):
        """Analyze partial performance by difficulty level"""
        difficulty_data = []
        
        for agent_name, agent_results in results.items():
            agent_label = self.agent_names.get(agent_name, agent_name)
            
            # Group by difficulty
            easy_results = [r for r in agent_results['detailed_results'] if r['difficulty'] == 'dễ']
            hard_results = [r for r in agent_results['detailed_results'] if r['difficulty'] == 'khó']
            
            # Calculate averages for each difficulty
            easy_partial_acc = np.mean([r['partial_accuracy'] for r in easy_results]) if easy_results else 0
            hard_partial_acc = np.mean([r['partial_accuracy'] for r in hard_results]) if hard_results else 0
            
            easy_precision = np.mean([r['precision'] for r in easy_results]) if easy_results else 0
            hard_precision = np.mean([r['precision'] for r in hard_results]) if hard_results else 0
            
            easy_over_selection = np.mean([r['over_selection_rate'] for r in easy_results]) if easy_results else 0
            hard_over_selection = np.mean([r['over_selection_rate'] for r in hard_results]) if hard_results else 0
            
            difficulty_data.append({
                'Agent': agent_label,
                'Easy_Partial_Accuracy': easy_partial_acc,
                'Hard_Partial_Accuracy': hard_partial_acc,
                'Easy_Precision': easy_precision,
                'Hard_Precision': hard_precision,
                'Easy_Over_Selection': easy_over_selection,
                'Hard_Over_Selection': hard_over_selection
            })
        
        df_difficulty = pd.DataFrame(difficulty_data)
        
        # Create comparison plots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        x = np.arange(len(df_difficulty['Agent']))
        width = 0.35
        
        # Partial Accuracy by Difficulty
        bars1 = ax1.bar(x - width/2, df_difficulty['Easy_Partial_Accuracy'], width, 
                       label='Easy Queries', color='lightgreen', alpha=0.8)
        bars2 = ax1.bar(x + width/2, df_difficulty['Hard_Partial_Accuracy'], width,
                       label='Hard Queries', color='orange', alpha=0.8)
        
        ax1.set_title('Partial Accuracy by Query Difficulty', fontweight='bold')
        ax1.set_ylabel('Partial Accuracy')
        ax1.set_xticks(x)
        ax1.set_xticklabels(df_difficulty['Agent'])
        ax1.legend()
        ax1.set_ylim(0, 1.0)
        ax1.grid(axis='y', alpha=0.3)
        
        # Add value labels
        for bar, acc in zip(bars1, df_difficulty['Easy_Partial_Accuracy']):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{acc:.2f}', ha='center', va='bottom', fontsize=9)
        for bar, acc in zip(bars2, df_difficulty['Hard_Partial_Accuracy']):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{acc:.2f}', ha='center', va='bottom', fontsize=9)
        
        # Precision by Difficulty
        bars3 = ax2.bar(x - width/2, df_difficulty['Easy_Precision'], width, 
                       label='Easy Queries', color='lightblue', alpha=0.8)
        bars4 = ax2.bar(x + width/2, df_difficulty['Hard_Precision'], width,
                       label='Hard Queries', color='purple', alpha=0.8)
        
        ax2.set_title('Precision by Query Difficulty', fontweight='bold')
        ax2.set_ylabel('Precision')
        ax2.set_xticks(x)
        ax2.set_xticklabels(df_difficulty['Agent'])
        ax2.legend()
        ax2.set_ylim(0, 1.0)
        ax2.grid(axis='y', alpha=0.3)
        
        # Add value labels
        for bar, prec in zip(bars3, df_difficulty['Easy_Precision']):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{prec:.2f}', ha='center', va='bottom', fontsize=9)
        for bar, prec in zip(bars4, df_difficulty['Hard_Precision']):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{prec:.2f}', ha='center', va='bottom', fontsize=9)
        
        # Over-selection by Difficulty
        bars5 = ax3.bar(x - width/2, df_difficulty['Easy_Over_Selection'], width, 
                       label='Easy Queries', color='pink', alpha=0.8)
        bars6 = ax3.bar(x + width/2, df_difficulty['Hard_Over_Selection'], width,
                       label='Hard Queries', color='red', alpha=0.8)
        
        ax3.set_title('Over-selection Rate by Query Difficulty', fontweight='bold')
        ax3.set_ylabel('Over-selection Rate')
        ax3.set_xticks(x)
        ax3.set_xticklabels(df_difficulty['Agent'])
        ax3.legend()
        ax3.set_ylim(0, 1.0)
        ax3.grid(axis='y', alpha=0.3)
        
        # Add value labels
        for bar, rate in zip(bars5, df_difficulty['Easy_Over_Selection']):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{rate:.2f}', ha='center', va='bottom', fontsize=9)
        for bar, rate in zip(bars6, df_difficulty['Hard_Over_Selection']):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{rate:.2f}', ha='center', va='bottom', fontsize=9)
        
        # Hide the fourth subplot
        ax4.set_visible(False)
        
        plt.suptitle('Partial Performance Analysis by Query Difficulty', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'difficulty' / 'partial_difficulty_analysis.png', bbox_inches='tight')
        plt.close()
        
        return df_difficulty

    def generate_partial_accuracy_summary(self, results: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
        """Generate summary table for partial accuracy metrics"""
        summary_data = []
        
        for agent_name, agent_results in results.items():
            summary_data.append({
                'Agent': self.agent_names.get(agent_name, agent_name),
                'Total Queries': agent_results['total_queries'],
                'Partial Accuracy': f"{agent_results['avg_partial_accuracy']:.4f}",
                'Tool Coverage': f"{agent_results['avg_tool_coverage']:.4f}",
                'Precision': f"{agent_results['avg_precision']:.4f}",
                'Recall': f"{agent_results['avg_recall']:.4f}",
                'Over-selection Rate': f"{agent_results['avg_over_selection_rate']:.4f}"
            })
        
        summary_df = pd.DataFrame(summary_data)
        
        # Save to CSV
        summary_df.to_csv(self.output_dir / 'partial' / 'partial_accuracy_summary.csv', index=False)
        
        return summary_df

    def run_complete_partial_analysis(self):
        """Run complete partial accuracy analysis"""
        print("🎯 Starting Partial Tool Accuracy Analysis...")
        print("=" * 50)
        
        # Analyze all agents
        results = self.analyze_all_agents_partial()
        
        # Generate summary table
        print("\n📊 Generating partial accuracy summary...")
        summary_df = self.generate_partial_accuracy_summary(results)
        print("\nPartial Accuracy Summary:")
        print(summary_df.to_string(index=False))
        
        # Generate visualizations
        print("\n📈 Creating visualizations...")
        self.plot_partial_accuracy_comparison(results)
        print("✓ Partial accuracy comparison saved")
        
        self.create_tool_success_matrix(results)
        print("✓ Tool success matrix saved")
        
        difficulty_df = self.analyze_difficulty_partial_performance(results)
        print("✓ Difficulty-based partial analysis saved")
        
        print(f"\n📁 All partial accuracy analysis files saved to: {self.output_dir}")
        print("✅ Partial accuracy analysis complete!")
        
        return results, summary_df, difficulty_df

if __name__ == "__main__":
    # Run partial accuracy analysis
    analyzer = PartialAccuracyAnalyzer()
    results, summary, difficulty = analyzer.run_complete_partial_analysis() 