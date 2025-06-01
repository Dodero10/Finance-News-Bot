# 📊 EVALUATION ANALYSIS - SO SÁNH HIỆU SUẤT CÁC AGENT

## 🎯 Tổng quan

Folder này chứa **phân tích toàn diện** về hiệu suất của 4 kiến trúc agent AI trong việc xử lý các câu hỏi tài chính:

| Agent | Kiến trúc | Đặc điểm |
|-------|-----------|----------|
| **React** | ReAct (Reason + Act) | Kiến trúc cơ bản, phản ứng nhanh |
| **ReWOO** | Reasoning Without Observation | Lập kế hoạch trước, thực thi sau |
| **Reflexion** | Self-reflection | Tự đánh giá và sửa lỗi |
| **Multi-Agent** | Đa agent phối hợp | Nhiều agent chuyên biệt |

## 🏆 Kết quả chính

### **Xếp hạng tổng thể:**
1. **Multi-Agent** (100.0%) - Accuracy và Recall xuất sắc
2. **ReWOO** (90.24%) - Precision tuyệt vời, ổn định cao  
3. **Reflexion** (87.06%) - Cân bằng tốt, tin cậy cao
4. **React** (77.59%) - Đơn giản nhưng kém hiệu quả nhất

### **Chi tiết từng metric:**

#### 🎯 **Accuracy (Perfect Tool Match):**
1. **Multi-Agent**: 44.28% - Chính xác nhất
2. **ReWOO**: 33.46% - Khá tốt
3. **Reflexion**: 28.94% - Trung bình 
4. **React**: 19.90% - Kém nhất

#### 📊 **F1 Score (Cân bằng tổng thể):**
1. **Multi-Agent**: 76.58% - Balanced tốt nhất
2. **Reflexion**: 74.07% - Rất tốt
3. **ReWOO**: 73.58% - Tốt
4. **React**: 67.97% - Kém nhất

#### 🎯 **Precision (Ít gọi tools thừa):**
1. **ReWOO**: 98.78% - Tuyệt vời, rất ít waste
2. **Reflexion**: 94.79% - Rất tốt
3. **React**: 94.72% - Rất tốt  
4. **Multi-Agent**: 63.62% - Kém, hay gọi thừa

#### 🔍 **Recall (Ít bỏ sót tools):**
1. **Multi-Agent**: 96.18% - Xuất sắc, rất ít miss
2. **Reflexion**: 60.97% - Trung bình
3. **ReWOO**: 58.66% - Trung bình
4. **React**: 53.39% - Kém, hay bỏ sót

### **Behavioral Patterns:**
- 🤖 **Multi-Agent**: "Comprehensive Explorer" - High recall, low precision (calls many tools, rarely misses)
- 🎯 **ReWOO**: "Conservative Planner" - High precision, medium recall (careful tool selection)
- ⚖️ **Reflexion**: "Balanced Performer" - Good overall balance across metrics
- ⚡ **React**: "Simple Minimalist" - Consistent but limited performance

## 📁 Cấu trúc thư mục

```
evaluation_analysis/
├── 🏠 MAIN_README.md                   # Overview tổng quan (file này)
├── 🔧 TECHNICAL_GUIDE.md               # Hướng dẫn kỹ thuật chi tiết
├── 📊 METRICS_EXPLAINED.md             # Giải thích các metrics  
├── 🎯 PRECISION_RECALL_INSIGHTS.md     # Phân tích hành vi chọn tools
├── ⚡ QUICK_RESULTS.md                  # Kết quả nhanh cho decision makers
├── 🚀 run_comparison_analysis.py       # Script chính
├── 🔧 utils/analysis_helper.py         # Functions hỗ trợ
└── 📊 results/                         # Tất cả kết quả phân tích
    ├── 📈 metrics/                     # Raw metrics data (CSV)
    ├── 📊 visualizations/              # Charts và graphs (PNG) 
    ├── 🏆 rankings/                    # Xếp hạng từng metric (TXT)
    ├── 📋 detailed_reports/            # Báo cáo chi tiết (TXT)
    └── 💾 raw_data/                    # Complete dataset (CSV)
```

## 🚀 Quick Start

### **1. Chạy phân tích hoàn chỉnh:**
```bash
cd evaluation_analysis
python run_comparison_analysis.py
```

### **2. Xem kết quả nhanh:**
```bash
# Xếp hạng tổng thể
cat results/rankings/overall_ranking.txt

# Accuracy ranking
cat results/rankings/accuracy_ranking.txt

# Precision vs Recall trade-offs
cat results/rankings/precision_ranking.txt
cat results/rankings/recall_ranking.txt
```

### **3. Xem visualization:**
- **Tổng quan**: `results/visualizations/overall_dashboard.png`
- **Precision/Recall**: `results/visualizations/precision_recall_analysis.png`
- **Theo độ khó**: `results/visualizations/difficulty_analysis.png`

## 📖 Documentation Guide

### 🎯 **Bạn muốn gì?** → **Đọc file nào?**

| Mục đích | File đề xuất |
|----------|--------------|
| 🏆 **Agent nào tốt nhất?** | `QUICK_RESULTS.md` |
| 🔧 **Customize analysis** | `TECHNICAL_GUIDE.md` |
| 📊 **Hiểu các metrics** | `METRICS_EXPLAINED.md` |
| 🎯 **Hành vi chọn tools** | `PRECISION_RECALL_INSIGHTS.md` |
| 📈 **Raw data analysis** | `results/raw_data/complete_results.csv` |

## 📊 Metrics Overview

Tất cả metrics **dựa hoàn toàn trên ground truth** từ `../evaluation/data_eval/synthetic_data/synthetic_news.csv`:

| Metric | Công thức | Ý nghĩa |
|--------|-----------|---------|
| **Accuracy** | `Perfect matches / Total questions` | Tỉ lệ trả lời hoàn hảo (tools match 100%) |
| **Precision** | `\|Texp ∩ Tact\| / \|Tact\|` | Tỉ lệ tools gọi đúng (ít thừa) |
| **Recall** | `\|Texp ∩ Tact\| / \|Texp\|` | Tỉ lệ tools cần thiết được gọi (ít sót) |
| **F1 Score** | `2 × P × R / (P + R)` | Cân bằng Precision/Recall |

## 💡 Key Insights

### **🎯 Trade-offs quan trọng:**

1. **Multi-Agent**: Accuracy cao nhất (44%) nhưng precision thấp (64%) 
   - ✅ Rất ít bỏ sót tools (recall 96%)
   - ❌ Hay gọi thừa tools (precision thấp)
   - 🎯 **Phù hợp**: Khi cần comprehensive analysis, không ngại cost

2. **ReWOO**: Precision tuyệt vời (99%) nhưng recall thấp (59%)
   - ✅ Gần như không gọi thừa tools 
   - ❌ Hay bỏ sót tools cần thiết
   - 🎯 **Phù hợp**: Khi cần tiết kiệm resources, chấp nhận miss info

3. **Reflexion**: Cân bằng tốt, tin cậy cao
   - ⚖️ Tất cả metrics ở mức khá tốt
   - 🎯 **Phù hợp**: Production environment cần ổn định

4. **React**: Đơn giản nhưng hiệu suất thấp nhất mọi metric
   - 🎯 **Phù hợp**: Prototyping, MVP nhanh

## 🔄 Update & Maintenance

### **Chạy lại với dữ liệu mới:**
1. Đặt files mới vào `../evaluation/data_eval/results/`
2. Chạy: `python run_comparison_analysis.py`
3. Kết quả tự động cập nhật trong `results/`

### **Thêm metrics mới:**
1. Sửa `utils/analysis_helper.py`
2. Cập nhật `run_comparison_analysis.py`
3. Chạy lại analysis

## 📞 Troubleshooting

| Lỗi | Nguyên nhân | Giải pháp |
|-----|-------------|-----------|
| `File not found` | Sai đường dẫn data | Kiểm tra `../evaluation/data_eval/` |
| `No charts created` | Lỗi matplotlib | Kiểm tra backend setting |
| `Empty results` | Không load được data | Xem log loading trong terminal |

## 🎯 Recommendations

### **🏆 Cho accuracy cao nhất:**
→ **Chọn Multi-Agent** - 44.28% accuracy, best overall performance

### **💰 Cho cost optimization:**
→ **Chọn ReWOO** - 98.78% precision, minimal tool waste

### **⚖️ Cho production balance:**
→ **Chọn Reflexion** - Stable across all metrics, reliable

### **⚡ Cho prototyping nhanh:**
→ **Chọn React** - Simple architecture, easy to implement

### **🔍 Cho comprehensive analysis:**
→ **Chọi Multi-Agent** - 96.18% recall, minimal information loss

---

*📊 **Dataset**: 184 câu hỏi/agent | **Accuracy trung bình**: 31.6% | **F1 Score trung bình**: 73.1%*

*📚 Để hiểu sâu hơn, đọc các file documentation chuyên biệt trong thư mục này.* 