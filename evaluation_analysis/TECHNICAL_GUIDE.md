# 🔧 TECHNICAL GUIDE - Hướng dẫn kỹ thuật chi tiết

## 🎯 Mục đích

Guide này dành cho developers muốn:
- 🔍 **Hiểu cách script hoạt động**
- ⚙️ **Customize phân tích**
- 🐛 **Debug và troubleshoot**
- 📊 **Thêm metrics mới**
- 🔧 **Modify visualization**

## 🏗️ Kiến trúc hệ thống

### **Core Components:**

```
run_comparison_analysis.py     # Entry point chính
├── AgentAnalyzer             # Class chính xử lý data
├── create_visualization_charts()   # Tạo tất cả biểu đồ
├── create_technical_details_report()  # Báo cáo kỹ thuật
└── main()                    # Orchestrator chính

utils/analysis_helper.py       # Helper functions
├── AgentAnalyzer class       # Data processing & metrics
├── create_folder_structure() # Setup directories
├── save_metrics_separately() # Export CSV files
├── create_individual_rankings() # Generate rankings
└── save_detailed_reports()   # Create reports
```

### **Data Flow:**

```
../evaluation/data_eval/results/*.csv
    ↓ [AgentAnalyzer.load_agent_data()]
Agent Data (4 DataFrames)
    ↓ [load_ground_truth()]
+ Ground Truth (synthetic_news.csv)
    ↓ [analyze_by_difficulty()]
Results DataFrame
    ↓ [Parallel Processing]
├── save_metrics_separately() → results/metrics/*.csv
├── create_visualization_charts() → results/visualizations/*.png
├── create_individual_rankings() → results/rankings/*.txt
└── save_detailed_reports() → results/detailed_reports/*.txt
```

## 🚀 Cách sử dụng Script

### **1. Chạy analysis đầy đủ:**
```bash
cd evaluation_analysis
python run_comparison_analysis.py
```

### **2. Chỉ tạo charts:**
```bash
python run_comparison_analysis.py --charts-only
```

### **3. Chỉ tính metrics:**
```bash
python run_comparison_analysis.py --metrics-only
```

## 📊 Metrics Implementation Details

### **1. Accuracy (NEW - Ground Truth Based)**
```python
def calculate_accuracy(self, df):
    """Perfect match với ground truth"""
    correct_count = 0
    for _, row in df.iterrows():
        required_tools = self.get_required_tools(row['input'])  # Texp
        used_tools = self.parse_tools_used(row['tools'])        # Tact
        
        # Remove failed tools
        if row['failed_tools_count'] > 0:
            failed_tools = self.parse_tools_used(row['failed_tools'])
            used_tools = used_tools - failed_tools
        
        if used_tools == required_tools:  # Perfect match
            correct_count += 1
    
    return correct_count / len(df)
```

### **2. Precision & Recall**
```python
def calculate_f1_metrics(self, df):
    """Dựa trên ground truth từ synthetic_news.csv"""
    tp = fp = fn = 0
    
    for _, row in df.iterrows():
        required_tools = self.get_required_tools(row['input'])  # Texp
        used_tools = self.parse_tools_used(row['tools'])        # Tact (no failed)
        
        tp += len(required_tools & used_tools)  # Correct tools
        fp += len(used_tools - required_tools)  # Extra tools  
        fn += len(required_tools - used_tools)  # Missing tools
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return f1, precision, recall
```

### **3. Tool Fail Rate (Unchanged)**
```python
def calculate_tool_fail_rate(self, df):
    """Tỉ lệ execution failures"""
    df_with_tools = df[df['tools'].notna() & (df['tools'].str.strip() != '')]
    if len(df_with_tools) == 0:
        return 0
    
    failed_calls = len(df_with_tools[df_with_tools['failed_tools_count'] > 0])
    return failed_calls / len(df_with_tools)
```

## 🔧 Customization Guide

### **1. Thêm metric mới:**

**Bước 1:** Thêm function trong `AgentAnalyzer`:
```python
def calculate_your_metric(self, df):
    """Your custom metric"""
    # Your logic here
    return metric_value
```

**Bước 2:** Cập nhật `analyze_by_difficulty()`:
```python
your_metric = self.calculate_your_metric(df_filtered)

results.append({
    'Agent': agent_name,
    'Difficulty': difficulty,
    'Your_Metric': your_metric,  # Add this line
    # ... existing fields
})
```

**Bước 3:** Cập nhật visualization và reports theo nhu cầu.

### **2. Thêm visualization mới:**

**Trong `create_visualization_charts()`:**
```python
# Your new chart
fig, ax = plt.subplots(figsize=(12, 8))
# Your plotting logic
plt.savefig(base_path / "your_chart.png", dpi=300, bbox_inches='tight')
plt.close()
```

### **3. Customize file paths:**

**Trong `run_comparison_analysis.py`:**
```python
# Change data paths
analyzer = AgentAnalyzer("your/custom/path")
analyzer.load_ground_truth("your/ground_truth.csv")

# Change output paths
create_visualization_charts(results_df, "your/output/path")
```

## 📁 File Structure Details

### **Input Files (Required):**
```
../evaluation/data_eval/results/
├── react_agent_eval_results.csv      # React agent results
├── rewoo_agent_eval_results.csv      # ReWOO agent results  
├── reflexion_agent_eval_results.csv  # Reflexion agent results
└── multi_agent_eval_results.csv      # Multi-agent results

../evaluation/data_eval/synthetic_data/
└── synthetic_news.csv                # Ground truth labels
```

### **Expected CSV Format:**
```csv
input,difficulty,output,tools,failed_tools,failed_tools_count
"Query text","dễ|khó","Response","tool1,tool2","failed_tool",1
```

### **Output Structure:**
```
results/
├── metrics/                    # Structured data
│   ├── accuracy_results.csv   # Accuracy by agent/difficulty
│   ├── f1_score_results.csv   # P/R/F1 by agent/difficulty
│   ├── tool_performance_results.csv  # Tool metrics
│   └── summary_metrics.csv    # All metrics combined
├── visualizations/             # PNG charts
│   ├── accuracy_comparison.png
│   ├── f1_score_comparison.png
│   ├── precision_recall_analysis.png  # NEW
│   ├── difficulty_analysis.png
│   ├── tool_metrics_heatmap.png
│   └── overall_dashboard.png
├── rankings/                   # Text rankings
│   ├── accuracy_ranking.txt
│   ├── f1_score_ranking.txt
│   ├── precision_ranking.txt   # NEW
│   ├── recall_ranking.txt      # NEW
│   ├── tool_performance_ranking.txt
│   └── overall_ranking.txt
├── detailed_reports/           # Analysis reports
│   ├── executive_summary.txt
│   ├── technical_details.txt
│   └── full_analysis_report.txt
└── raw_data/                   # Complete datasets
    ├── complete_results.csv
    └── failed_cases_analysis.csv
```

## 🐛 Debugging & Troubleshooting

### **Common Issues:**

#### **1. Data Loading Errors:**
```python
# Debug data loading
analyzer = AgentAnalyzer("../evaluation/data_eval/results")
print(f"Found {len(analyzer.agents_data)} agents")
for agent, df in analyzer.agents_data.items():
    print(f"{agent}: {len(df)} records")
```

#### **2. Ground Truth Mismatch:**
```python
# Check ground truth loading
analyzer.load_ground_truth("../evaluation/data_eval/synthetic_data/synthetic_news.csv")
print(f"Ground truth queries: {len(analyzer.ground_truth_tools)}")

# Check query matching
for query in df['input'].head(5):
    required = analyzer.get_required_tools(query)
    print(f"Query: {query[:50]}...")
    print(f"Required tools: {required}")
```

#### **3. Visualization Errors:**
```python
# Debug matplotlib
import matplotlib
print(f"Backend: {matplotlib.get_backend()}")

# Force non-interactive backend
matplotlib.use('Agg')
```

#### **4. Performance Issues:**
```python
# Profile slow operations
import time

start = time.time()
results_df = analyzer.analyze_by_difficulty()
print(f"Analysis took {time.time() - start:.2f} seconds")
```

### **Validation Checks:**

```python
# Validate results
def validate_results(results_df):
    # Check completeness
    expected_agents = ['React', 'ReWOO', 'Reflexion', 'Multi-Agent']
    expected_difficulties = ['dễ', 'khó']
    
    for agent in expected_agents:
        for diff in expected_difficulties:
            subset = results_df[(results_df['Agent'] == agent) & 
                              (results_df['Difficulty'] == diff)]
            assert len(subset) == 1, f"Missing {agent} - {diff}"
    
    # Check metric ranges
    assert results_df['Accuracy'].between(0, 1).all()
    assert results_df['Precision'].between(0, 1).all()
    assert results_df['Recall'].between(0, 1).all()
    assert results_df['F1_Score'].between(0, 1).all()
    
    print("✅ All validation checks passed!")
```

## 🔄 Development Workflow

### **1. Making Changes:**
```bash
# 1. Edit code
vim utils/analysis_helper.py

# 2. Test changes
python run_comparison_analysis.py --metrics-only

# 3. Full test
python run_comparison_analysis.py

# 4. Validate outputs
ls -la results/
```

### **2. Adding New Features:**
1. **Plan the feature** - Define inputs/outputs
2. **Implement core logic** - Add to `AgentAnalyzer`
3. **Update main script** - Integrate into workflow
4. **Add visualization** - If needed
5. **Test thoroughly** - Validate with real data
6. **Document changes** - Update this guide

### **3. Performance Optimization:**
```python
# Use pandas vectorization
df['metric'] = df.apply(lambda row: calculate_metric(row), axis=1)

# Better: Vectorized operations
df['metric'] = vectorized_calculate_metric(df)

# Memory efficient processing
for chunk in pd.read_csv('large_file.csv', chunksize=1000):
    process_chunk(chunk)
```

## 📚 Dependencies

### **Required Packages:**
```python
pandas>=1.5.0          # Data processing
matplotlib>=3.6.0       # Plotting
seaborn>=0.12.0         # Statistical visualization  
numpy>=1.24.0           # Numerical operations
pathlib                 # Path handling (built-in)
argparse                # CLI arguments (built-in)
ast                     # String parsing (built-in)
```

### **Installation:**
```bash
pip install pandas matplotlib seaborn numpy
```

## 🎯 Best Practices

1. **Always validate data before processing**
2. **Use relative paths for portability**
3. **Add error handling for edge cases**
4. **Document new metrics clearly**
5. **Test with different data sizes**
6. **Keep backup of original data**
7. **Use descriptive variable names**
8. **Add type hints for clarity**

---

*🔧 Để thêm features mới hoặc fix bugs, follow workflow này và update documentation tương ứng.* 