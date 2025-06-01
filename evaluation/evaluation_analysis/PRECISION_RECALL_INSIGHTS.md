# 🎯 PRECISION & RECALL INSIGHTS - HÀNH VI CHỌN TOOL

## 📊 Định nghĩa Metrics

- **Texp**: Danh sách tool kỳ vọng (từ ground truth)
- **Tact**: Danh sách tool Agent trả về

### 🔢 Công thức:
- **Precision** = |Texp ∩ Tact| / |Tact| - Tỉ lệ tool được chọn là cần thiết
- **Recall** = |Texp ∩ Tact| / |Texp| - Tỉ lệ tool cần thiết đã được tìm thấy  
- **F1** = 2 × (Precision × Recall) / (Precision + Recall)

---

## 🏆 RANKINGS

### 🎯 **PRECISION** (Cao → Thấp)
1. **ReWOO**: 98.78% ✅ Rất ít gọi tools thừa
2. **Reflexion**: 94.79% ✅ Rất ít gọi tools thừa  
3. **React**: 94.72% ✅ Rất ít gọi tools thừa
4. **Multi-Agent**: 63.62% ⚠️ Thường gọi tools thừa

### 🔍 **RECALL** (Cao → Thấp)
1. **Multi-Agent**: 96.18% ✅ Rất ít bỏ sót tools
2. **Reflexion**: 60.97% ⚠️ Thường bỏ sót tools cần thiết
3. **ReWOO**: 58.66% ⚠️ Thường bỏ sót tools cần thiết
4. **React**: 53.39% ⚠️ Thường bỏ sót tools cần thiết

---

## 💡 PHÂN TÍCH HÀNH VI

### 🤖 **ReWOO Agent**
- **Hành vi**: **Conservative Planner** 🎯
- **Precision cao nhất** (98.78%) - Gần như không bao giờ gọi thừa tools
- **Recall thấp** (58.66%) - Thường bỏ sót tools cần thiết
- **Tính cách**: Thận trọng, chỉ gọi tools khi chắc chắn cần thiết

### 🤖 **Multi-Agent**
- **Hành vi**: **Comprehensive Explorer** 🔍  
- **Recall cao nhất** (96.18%) - Rất ít bỏ sót tools cần thiết
- **Precision thấp nhất** (63.62%) - Thường gọi nhiều tools thừa
- **Tính cách**: Tích cực, thà gọi thừa còn hơn bỏ sót

### 🤖 **Reflexion Agent**
- **Hành vi**: **Balanced Corrector** ⚖️
- **Precision tốt** (94.79%) - Ít gọi thừa 
- **Recall trung bình** (60.97%) - Vẫn hay bỏ sót
- **Tính cách**: Cân bằng nhưng vẫn thiên về thận trọng

### 🤖 **React Agent**  
- **Hành vi**: **Reactive Minimalist** ⚡
- **Precision tốt** (94.72%) - Ít gọi thừa
- **Recall thấp nhất** (53.39%) - Bỏ sót nhiều nhất
- **Tính cách**: Phản ứng nhanh, tối giản, hay thiếu sót

---

## 📈 PATTERNS THEO ĐỘ KHÓ

### 🟢 **Câu DỄ**:
- **ReWOO**: Perfect precision (100%) nhưng recall thấp (61.76%)
- **Multi-Agent**: Recall perfect (100%) nhưng precision thấp (65.38%)
- **React & Reflexion**: Cân bằng hơn nhưng vẫn thiên về precision

### 🔴 **Câu KHÓ**:
- **Tất cả agents** đều giảm precision nhẹ
- **Multi-Agent** vẫn duy trì recall cao nhất (92.36%)
- **ReWOO** vẫn giữ precision cao nhất (97.56%)

---

## 🎯 TRADE-OFFS ANALYSIS

| Agent | Precision | Recall | Strategy | Use Case |
|-------|-----------|--------|----------|----------|
| **ReWOO** | 🟢 Cao | 🔴 Thấp | Conservative | Mission-critical, tránh false positives |
| **Multi-Agent** | 🔴 Thấp | 🟢 Cao | Aggressive | Exploratory analysis, tránh miss |
| **Reflexion** | 🟢 Cao | 🟡 Trung bình | Balanced | General purpose |
| **React** | 🟢 Cao | 🔴 Thấp | Minimalist | Quick responses |

---

## 🚀 PRACTICAL RECOMMENDATIONS

### 🎯 **Khi nào dùng từng agent:**

#### **Dùng ReWOO khi:**
- ✅ Cần độ chính xác cao (precision matters)
- ✅ Chi phí gọi tools cao  
- ✅ Chấp nhận được thiếu một số features
- ❌ Không phù hợp khi cần comprehensive coverage

#### **Dùng Multi-Agent khi:**
- ✅ Cần coverage đầy đủ (recall matters)
- ✅ Chi phí gọi tools thấp
- ✅ Chấp nhận được một số tools thừa
- ❌ Không phù hợp khi cần tiết kiệm resources

#### **Dùng Reflexion khi:**
- ✅ Cần cân bằng precision và recall
- ✅ Có thời gian cho self-correction
- ✅ Độ tin cậy là priority
- ❌ Không phù hợp khi cần speed

#### **Dùng React khi:**  
- ✅ Cần phản hồi nhanh
- ✅ Tác vụ đơn giản
- ✅ Precision quan trọng hơn recall
- ❌ Không phù hợp cho complex analysis

---

## 🔮 INSIGHTS QUAN TRỌNG

1. **Không có agent nào perfect** - Đều có trade-off giữa precision và recall

2. **Architecture complexity ≠ Performance** - React đơn giản nhưng precision cao

3. **Multi-Agent có potential lớn** - Recall xuất sắc nhưng cần cải thiện coordination

4. **Planning strategies khác nhau** tạo ra behavior patterns rõ rệt:
   - **Planning-first** (ReWOO) → High precision, low recall
   - **Multi-agent coordination** → High recall, low precision  
   - **Reactive** (React) → Fast but incomplete
   - **Self-correction** (Reflexion) → Balanced but slower

5. **F1 Score cao nhất** thuộc về **Multi-Agent** do recall vượt trội bù đắp cho precision thấp 