# Finance News Bot - Metrics Analysis Documentation

## 1. Metrics Explanation

### 1.1 Accuracy Metrics

#### Flexible Accuracy (Order-Agnostic)
- **Definition**: Đo lường độ chính xác của việc chọn tool mà không quan tâm đến thứ tự
- **Công thức**: `Flexible Accuracy = 1 if set(expected) == set(actual) else 0`
- **Ví dụ**:
  ```
  Expected: ['listing_symbol', 'search_web']
  Agent: ['search_web', 'listing_symbol'] → Accuracy = 1.0 (100%)
  ```

#### Strict Accuracy (Order-Sensitive)
- **Definition**: Đo lường độ chính xác của việc chọn tool có tính đến thứ tự
- **Công thức**: `Strict Accuracy = 1 if expected == actual else 0`
- **Ví dụ**:
  ```
  Expected: ['listing_symbol', 'search_web']
  Agent: ['search_web', 'listing_symbol'] → Accuracy = 0.0 (0%)
  ```

#### Partial Accuracy
- **Definition**: Đo lường tỷ lệ tool được chọn đúng, cho phép đúng một phần
- **Công thức**: `Partial Accuracy = len(expected ∩ actual) / len(expected)`
- **Ví dụ**:
  ```
  Expected: ['listing_symbol', 'search_web']
  Agent: ['listing_symbol'] → Accuracy = 0.5 (50%)
  Agent: ['listing_symbol', 'search_web', 'time_now'] → Accuracy = 1.0 (100%)
  ```

### 1.2 Tool Selection Metrics

#### Precision
- **Definition**: Tỷ lệ tool được chọn chính xác trong số tool được chọn
- **Công thức**: `Precision = len(expected ∩ actual) / len(actual)`
- **Ví dụ**:
  ```
  Expected: ['listing_symbol', 'search_web']
  Agent: ['listing_symbol', 'time_now'] → Precision = 0.5 (50%)
  ```

#### Recall
- **Definition**: Tỷ lệ tool cần thiết được tìm thấy
- **Công thức**: `Recall = len(expected ∩ actual) / len(expected)`
- **Ví dụ**:
  ```
  Expected: ['listing_symbol', 'search_web']
  Agent: ['listing_symbol', 'time_now'] → Recall = 0.5 (50%)
  ```

#### F1 Score
- **Definition**: Trung bình điều hòa của Precision và Recall
- **Công thức**: `F1 = 2 * (Precision * Recall) / (Precision + Recall)`

### 1.3 Error Analysis Metrics

#### Over-selection Rate
- **Definition**: Tỷ lệ tool được chọn không cần thiết
- **Công thức**: `Over-selection = len(actual - expected) / len(actual)`
- **Ví dụ**:
  ```
  Expected: ['listing_symbol']
  Agent: ['listing_symbol', 'time_now'] → Over-selection = 0.5 (50%)
  ```

#### Under-selection Rate
- **Definition**: Tỷ lệ tool cần thiết bị bỏ sót
- **Công thức**: `Under-selection = len(expected - actual) / len(expected)`
- **Ví dụ**:
  ```
  Expected: ['listing_symbol', 'search_web']
  Agent: ['listing_symbol'] → Under-selection = 0.5 (50%)
  ```

## 2. Hướng Dẫn Sử Dụng

### 2.1 Cấu Trúc Thư Mục
```
evaluation/results_visualization/figures/
├── accuracy/
│   └── accuracy_types_comparison.png
├── comprehensive/
│   ├── comprehensive_metrics_comparison.png
│   ├── metrics_heatmap.png
│   └── comprehensive_metrics_summary.csv
├── difficulty/
│   ├── comprehensive_difficulty_analysis.png
│   └── partial_difficulty_analysis.png
├── partial/
│   ├── partial_accuracy_comparison.png
│   ├── tool_success_matrix.png
│   └── partial_accuracy_summary.csv
└── selection/
    └── selection_behavior_analysis.png
```

### 2.2 Các File Phân Tích

#### 1. Phân Tích Cơ Bản
```bash
python run_metrics_analysis.py
```
- **Input**: Dữ liệu từ `data_eval/results/` và `data_eval/synthetic_data/`
- **Output**: 
  - `accuracy/accuracy_types_comparison.png`: So sánh các loại accuracy
  - `comprehensive/comprehensive_metrics_comparison.png`: Biểu đồ tổng hợp các metrics
  - `comprehensive/metrics_summary.csv`: Bảng tổng hợp kết quả

#### 2. Phân Tích Partial Accuracy
```bash
python run_partial_accuracy.py
```
- **Input**: Giống phân tích cơ bản
- **Output**:
  - `partial/partial_accuracy_comparison.png`: So sánh partial accuracy giữa các agent
  - `partial/tool_success_matrix.png`: Ma trận thành công của từng tool
  - `partial/partial_accuracy_summary.csv`: Bảng tổng hợp partial accuracy

#### 3. Phân Tích Toàn Diện
```bash
python run_comprehensive_analysis.py
```
- **Input**: Giống phân tích cơ bản
- **Output**:
  - Tất cả các file từ các phân tích trước
  - `selection/selection_behavior_analysis.png`: Phân tích hành vi chọn tool
  - `difficulty/comprehensive_difficulty_analysis.png`: Phân tích theo độ khó

### 2.3 Ý Nghĩa Các File Kết Quả

#### Biểu Đồ So Sánh (Comparison Charts)
- `accuracy_types_comparison.png`: So sánh 3 loại accuracy (Flexible, Strict, Partial)
- `comprehensive_metrics_comparison.png`: So sánh tất cả metrics cho mỗi agent
- `partial_accuracy_comparison.png`: Chi tiết về partial accuracy và precision

#### Ma Trận và Heatmap
- `tool_success_matrix.png`: Tỷ lệ thành công của từng tool với từng agent
- `metrics_heatmap.png`: Heatmap tổng hợp tất cả metrics

#### Phân Tích Theo Độ Khó
- `comprehensive_difficulty_analysis.png`: So sánh performance trên câu hỏi dễ/khó
- `partial_difficulty_analysis.png`: Chi tiết partial accuracy theo độ khó

#### File CSV Tổng Hợp
- `comprehensive_metrics_summary.csv`: Tổng hợp tất cả metrics cho mỗi agent
- `partial_accuracy_summary.csv`: Chi tiết về partial accuracy và tool selection

### 2.4 Giải Thích Kết Quả

#### Đánh Giá Performance
| Mức Độ | Partial Accuracy | F1 Score | Ý Nghĩa |
|--------|-----------------|-----------|----------|
| Xuất sắc | > 0.85 | > 0.85 | Sẵn sàng production |
| Tốt | 0.70-0.85 | 0.70-0.85 | Cần cải thiện nhỏ |
| Trung bình | 0.55-0.70 | 0.55-0.70 | Cần training thêm |
| Kém | < 0.55 | < 0.55 | Cần thiết kế lại |

#### Pattern Thường Gặp
1. **High Partial, Low Exact**: Agent hiểu được tools cần dùng nhưng chọn thừa
2. **Low Partial**: Agent bỏ sót nhiều tools quan trọng
3. **High Over-selection**: Agent chọn quá nhiều tools không cần thiết

## 3. Troubleshooting

### 3.1 Lỗi Thường Gặp
1. **FileNotFoundError**: Kiểm tra đường dẫn data trong `data_eval/`
2. **ValueError**: Kiểm tra format của tools trong file CSV
3. **MemoryError**: Giảm DPI của plots hoặc xử lý theo batch

### 3.2 Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Dependencies

### Core Requirements
```bash
pip install pandas numpy matplotlib seaborn scikit-learn pathlib ast
```

### Specific Versions (tested)
```
pandas>=1.5.0
numpy>=1.21.0
matplotlib>=3.5.0
seaborn>=0.11.0
scikit-learn>=1.1.0
```

### Installation
```bash
# Install requirements
pip install -r requirements.txt

# Or install individually
pip install pandas numpy matplotlib seaborn scikit-learn
```

## 💡 Best Practices & Recommendations

### 1. Choosing the Right Metric

| Use Case | Recommended Metric | Why |
|----------|-------------------|-----|
| **Training feedback** | Partial Accuracy | Provides gradient for learning |
| **Model comparison** | F1 Score | Balances precision and recall |
| **Production readiness** | Flexible Accuracy | Real-world tool matching |

### 2. Analysis Workflow

```
1. Start with Basic Analysis (Section 4.3 requirements)
   ↓
2. Run Partial Accuracy (Better insights)
   ↓
3. If accuracy is low → Deep Dive Analysis
   ↓
4. For complete picture → Comprehensive Analysis
```

### 3. Interpreting Results for Thesis

**For Section 4.3.1 (Accuracy):**
- Report Flexible Accuracy for exact matches
- Use Partial Accuracy for additional insights
- Analyze performance by difficulty level

**For Section 4.3.2 (F1 Score):**
- Report overall F1 Score
- Include Precision and Recall breakdown
- Analyze performance by difficulty level

### 4. Common Patterns

**High Partial Accuracy, Low Flexible Accuracy:**
- Agents understand required tools but select extras
- Focus on precision improvement

**Low Partial Accuracy:**
- Agents miss required tools
- Focus on coverage improvement

**High Over-selection Rate:**
- Agents are not selective enough
- Implement tool necessity filtering

## 🔗 Integration with Thesis

### Section 4.3.1 Example Text
```
The accuracy evaluation was conducted using both flexible and strict matching criteria. 
Flexible accuracy (order-agnostic) achieved X.XX for the best-performing agent, while 
strict accuracy (order-sensitive) was Y.YY. Additionally, partial accuracy analysis 
revealed that agents successfully identified Z.ZZ% of required tools on average, 
indicating room for improvement in tool coverage.
```

### Section 4.3.2 Example Text
```
F1 scores ranged from A.AA to B.BB across the four agent architectures, with 
Multi-Agent achieving the highest score of C.CC. The precision-recall analysis 
revealed that agents generally maintained higher precision (D.DD average) than 
recall (E.EE average), suggesting conservative tool selection behavior.
```

## 📝 Output Files Reference

### Summary Tables
- `metrics_summary.csv` - Basic metrics for all agents
- `partial_accuracy_summary.csv` - Partial accuracy metrics
- `comprehensive_metrics_summary.csv` - All metrics combined

### Visualizations
- `*_comparison.png` - Bar charts comparing agents
- `*_difficulty_analysis.png` - Performance by query difficulty
- `tool_success_matrix.png` - Heatmap of tool success rates
- `selection_behavior_analysis.png` - Over/under-selection patterns

### Reports
- `accuracy_analysis_report.txt` - Detailed text analysis of errors and patterns

## 🆘 Support

### Getting Help
1. Check this README for your specific use case
2. Look at the generated output files for insights
3. Run debug mode for detailed error information
4. Check data format requirements

### Contributing
Feel free to extend the analysis tools for your specific needs:
1. Add new metrics in the `calculate_all_metrics` function
2. Create new visualization functions
3. Extend difficulty analysis for more granular categories

---

**Last Updated:** [Current Date]  
**Version:** 2.0  
**Compatible with:** Finance News Bot Evaluation Framework v1.0 