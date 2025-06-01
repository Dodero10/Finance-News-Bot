# 📊 Evaluation Analysis - So sánh hiệu suất các Agent

## 🎯 Mục tiêu
Phân tích và so sánh hiệu suất của 4 kiến trúc agent khác nhau:
- **React Agent**: Kiến trúc ReAct cơ bản
- **ReWOO Agent**: Reasoning WithOut Observation  
- **Reflexion Agent**: Self-reflection capabilities
- **Multi-Agent**: Kiến trúc multi-agent tự đề xuất

## 📁 Cấu trúc thư mục

```
evaluation_analysis/
├── README.md                           # File hướng dẫn này
├── PRECISION_RECALL_INSIGHTS.md        # 🆕 Phân tích chi tiết Precision & Recall
├── run_comparison_analysis.py          # Script chính để chạy analysis
├── utils/
│   └── analysis_helper.py              # Các hàm hỗ trợ analysis
└── results/                            # Thư mục chứa tất cả kết quả
    ├── metrics/                        # Các file metrics riêng biệt
    │   ├── accuracy_results.csv        # Kết quả accuracy theo agent & độ khó
    │   ├── f1_score_results.csv        # Kết quả F1, precision, recall
    │   ├── tool_performance_results.csv # Tool precision, recall, fail rate
    │   └── summary_metrics.csv         # Tổng hợp tất cả metrics
    ├── visualizations/                 # Tất cả biểu đồ
    │   ├── accuracy_comparison.png     # So sánh accuracy
    │   ├── f1_score_comparison.png     # So sánh F1 score
    │   ├── precision_recall_analysis.png # 🆕 Biểu đồ riêng Precision & Recall
    │   ├── tool_metrics_heatmap.png    # Heatmap tool performance
    │   ├── difficulty_analysis.png     # Phân tích theo độ khó
    │   └── overall_dashboard.png       # Dashboard tổng quan (cập nhật)
    ├── rankings/                       # Xếp hạng và so sánh
    │   ├── accuracy_ranking.txt        # Xếp hạng accuracy
    │   ├── f1_score_ranking.txt        # Xếp hạng F1 score
    │   ├── precision_ranking.txt       # 🆕 Xếp hạng Precision riêng
    │   ├── recall_ranking.txt          # 🆕 Xếp hạng Recall riêng
    │   ├── tool_performance_ranking.txt # Xếp hạng tool performance
    │   └── overall_ranking.txt         # Xếp hạng tổng thể
    ├── detailed_reports/               # Báo cáo chi tiết
    │   ├── full_analysis_report.txt    # Báo cáo đầy đủ
    │   ├── executive_summary.txt       # Tóm tắt điều hành
    │   └── technical_details.txt       # Chi tiết kỹ thuật
    └── raw_data/                       # Dữ liệu thô
        ├── complete_results.csv        # Dữ liệu đầy đủ để phân tích thêm
        └── failed_cases_analysis.csv   # Phân tích các trường hợp thất bại
```

## 🚀 Cách sử dụng

### 1. Chạy analysis hoàn chỉnh
```bash
python run_comparison_analysis.py
```

### 2. Chạy chỉ phần tạo biểu đồ
```bash
python run_comparison_analysis.py --charts-only
```

### 3. Chạy chỉ phần tính metrics
```bash
python run_comparison_analysis.py --metrics-only
```

## 📊 Metrics được đánh giá

### 1. **Accuracy**
- **Định nghĩa**: Tỉ lệ agent gọi tools hoàn toàn đúng theo ground truth
- **Công thức**: `(Số câu gọi đúng hoàn toàn như ground truth) / Tổng số câu`
- **Giải thích**: Agent gọi đúng tất cả tools cần thiết và không gọi thừa
- **Ground Truth**: Dựa trên `synthetic_news.csv`

### 2. **F1 Score, Precision & Recall** 
- **Precision**: `|Texp ∩ Tact| / |Tact|` - Tỉ lệ tool được chọn là cần thiết
- **Recall**: `|Texp ∩ Tact| / |Texp|` - Tỉ lệ tool cần thiết đã được tìm thấy
- **F1 Score**: `2 * (Precision * Recall) / (Precision + Recall)` - Cân bằng P&R
- **Ground Truth**: Sử dụng dữ liệu từ `synthetic_news.csv`
- **Giải thích**: Đo hành vi chọn tool - agent có xu hướng gọi thừa hay bỏ sót

### 3. **Tool Performance**
- **Tool Precision**: Tỉ lệ tools được gọi đúng trong tổng số tools được gọi
- **Tool Recall**: Tỉ lệ tools cần thiết được gọi trong tổng số tools cần thiết  
- **Tool Fail Rate**: Tỉ lệ lỗi khi gọi tools

### 4. **Difficulty Analysis**
- So sánh hiệu suất giữa câu hỏi **dễ** và **khó**
- Đánh giá tính ổn định của agent

## 📈 Cách đọc kết quả

### 1. **Xem ranking nhanh**
- Mở file `results/rankings/overall_ranking.txt` 
- Xem agent nào xếp hạng cao nhất

### 2. **Xem báo cáo tóm tắt**
- Mở file `results/detailed_reports/executive_summary.txt`
- Có kết luận và khuyến nghị

### 3. **Xem biểu đồ**
- Mở các file PNG trong `results/visualizations/`
- `overall_dashboard.png` để xem tổng quan

### 4. **Phân tích sâu**
- Dùng file `results/raw_data/complete_results.csv` 
- Import vào Excel/Python để phân tích thêm

## 💡 Tips

- **Agent tốt nhất tổng thể**: Xem overall ranking
- **Agent ổn định nhất**: So sánh hiệu suất giữa câu dễ/khó  
- **Agent tin cậy nhất**: Xem tool fail rate thấp nhất
- **Agent phù hợp câu khó**: Xem hiệu suất riêng với câu khó

## 🔧 Tùy chỉnh

Để chỉnh sửa cách tính metrics hoặc thêm analysis mới:
1. Sửa file `utils/analysis_helper.py`
2. Thêm logic vào `run_comparison_analysis.py`

## 📞 Hỗ trợ

Nếu có vấn đề:
1. Kiểm tra file input data có đúng format không
2. Xem log errors trong terminal
3. Kiểm tra quyền ghi file trong thư mục results 