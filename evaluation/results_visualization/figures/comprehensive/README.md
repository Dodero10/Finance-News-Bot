# Kết quả So sánh các Agent

## Cấu trúc thư mục

```
evaluation/results_visualization/figures/comprehensive/
├── README.md                          # File này - hướng dẫn đọc kết quả
├── analysis_results.txt               # Kết quả phân tích chi tiết dạng text
├── detailed_results.csv               # Dữ liệu chi tiết dạng CSV
├── agent_comparison_overview.png      # Biểu đồ tổng quan so sánh 4 metrics
└── agent_comparison_detailed.png      # Biểu đồ chi tiết theo độ khó
```

## Các Agent được đánh giá

1. **React Agent**: Kiến trúc ReAct cơ bản
2. **ReWOO Agent**: Kiến trúc ReWOO (Reasoning WithOut Observation)
3. **Reflexion Agent**: Kiến trúc Reflexion với khả năng self-reflection
4. **Multi-Agent**: Kiến trúc multi-agent do bạn đề xuất

## Metrics đánh giá

### 1. Accuracy
- **Định nghĩa**: Tỉ lệ agent gọi tools hoàn toàn đúng
- **Công thức**: (Số câu có failed_tools_count = 0) / Tổng số câu
- **Giải thích**: Đo lường khả năng gọi tool chính xác của agent

### 2. F1 Score
- **Định nghĩa**: Điểm F1 dựa trên việc gọi tool thành công
- **Công thức**: 2 * (Precision * Recall) / (Precision + Recall)
- **Giải thích**: Cân bằng giữa precision và recall trong việc sử dụng tools

### 3. Tool Fail Rate
- **Định nghĩa**: Tỉ lệ gọi tool thất bại
- **Công thức**: (Số câu có failed_tools_count > 0) / Tổng số câu có gọi tool
- **Giải thích**: Đo lường độ tin cậy khi sử dụng tools (thấp hơn = tốt hơn)

## Cách đọc kết quả

### Biểu đồ Overview (agent_comparison_overview.png)
- **Góc trên trái**: Accuracy theo độ khó
- **Góc trên phải**: F1 Score theo độ khó
- **Góc dưới trái**: Tool Fail Rate theo độ khó
- **Góc dưới phải**: Heatmap tổng quan (màu xanh = tốt, màu đỏ = kém)

### Biểu đồ Detailed (agent_comparison_detailed.png)
- So sánh trực tiếp giữa câu hỏi dễ và khó cho từng metric
- Cột xanh: Câu hỏi dễ
- Cột cam: Câu hỏi khó

## Files kết quả

### analysis_results.txt
- Chứa toàn bộ kết quả phân tích dạng text
- Bảng xếp hạng theo từng metric
- Kết luận và nhận xét

### detailed_results.csv
- Dữ liệu chi tiết để phân tích thêm
- Có thể import vào Excel/Python để xử lý thêm

## Cách hiểu kết quả

1. **Agent tốt nhất tổng thể**: Xem xếp hạng trung bình các metrics
2. **Agent ổn định nhất**: Agent có hiệu suất đều giữa câu dễ và khó
3. **Agent phù hợp câu khó**: Xem hiệu suất riêng với difficulty = 'khó'
4. **Agent đáng tin cậy nhất**: Agent có Tool Fail Rate thấp nhất
