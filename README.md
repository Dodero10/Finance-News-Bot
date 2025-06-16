# Bot Tin Tức Tài Chính

Hệ thống phân tích tin tức tài chính Việt Nam được hỗ trợ bởi AI sử dụng kiến trúc đa agent **LangGraph** với pipeline RAG toàn diện cho việc trả lời câu hỏi tài chính thông minh.

## 🌟 Tính Năng Chính

### 🤖 **Kiến Trúc Đa Agent**
- **Agent Giám Sát**: Định tuyến nhiệm vụ và điều phối thông minh
- **Agent Nghiên Cứu**: Tìm kiếm web và truy xuất tin tức dựa trên RAG  
- **Agent Tài Chính**: Dữ liệu và phân tích thị trường chứng khoán Việt Nam

### 📈 **Tích Hợp Dữ Liệu Tài Chính Việt Nam**
- Dữ liệu thị trường chứng khoán Việt Nam thời gian thực qua **vnstock**
- Phân tích giá lịch sử với nhiều nguồn dữ liệu (VCI, TCBS, MSN)
- Danh sách công ty và chỉ số tài chính
- Tìm kiếm và theo dõi mã chứng khoán

### 🛠️ **Bộ Công Cụ Toàn Diện**
- **Tìm Kiếm Web**: Thông tin thời gian thực qua Tavily Search
- **Cơ Sở Dữ Liệu Vector**: Tìm kiếm ngữ nghĩa qua kho tin tức tài chính
- **Dữ Liệu Cổ Phiếu**: Lịch sử giá, thông tin công ty, mã thị trường
- **Dịch Vụ Thời Gian**: Hỗ trợ múi giờ Việt Nam

### 📊 **Framework Đánh Giá Mạnh Mẽ**
- Tạo dữ liệu tổng hợp để kiểm thử
- Đánh giá đa chỉ số (độ chính xác, precision, recall, F1)
- So sánh và phân tích hiệu suất agent
- Công cụ benchmark toàn diện

## 🚀 Bắt Đầu Nhanh

### Yêu Cầu Tiên Quyết
- Python 3.11+
- API keys cho các nhà cung cấp LLM (khuyến nghị OpenAI)
- Thiết lập cơ sở dữ liệu vector ChromaDB

### Cài Đặt

1. **Clone repository**
   ```bash
   git clone https://github.com/Dodero10/Finance-News-Bot.git
   cd Finance-News-Bot
   ```

2. **Cài đặt dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Thiết lập môi trường**
   ```bash
   cp .env.example .env
   # Thêm API keys vào .env:
   # OPENAI_API_KEY=your_openai_key
   # TAVILY_API_KEY=your_tavily_key
   # LANGFUSE_PUBLIC_KEY=your_langfuse_key (tùy chọn)
   # LANGFUSE_SECRET_KEY=your_langfuse_secret (tùy chọn)
   ```

### Chạy Hệ Thống

#### **LangGraph Server (Khuyến Nghị)**
```bash
langgraph dev
```
Lệnh này khởi động LangGraph development server với tất cả agents có sẵn.

#### **Chạy Agent Riêng Lẻ**
```bash
# Hệ Thống Đa Agent
python -m src.agents.multi_agent
```

## 🎯 Các Agent Có Sẵn

### **Hệ Thống Đa Agent** (Chính)
Hệ thống phối hợp với các agent chuyên biệt cho phân tích tài chính toàn diện:
- Định tuyến nhiệm vụ thông minh dựa trên loại câu hỏi
- Khả năng xử lý song song
- Tổng hợp thông tin giữa các agent
- Quản lý workflow thích ứng

### **ReAct Agent** 
Agent Lý luận và Hành động với tích hợp công cụ để giải quyết vấn đề từng bước.

### **ReWOO Agent**
Agent Lý luận Không Quan sát cho việc lập kế hoạch và thực thi hiệu quả.

### **Reflexion Agent**
Agent tự sửa lỗi học từ phản hồi và cải thiện câu trả lời.

## 🛠️ Công Cụ & Khả Năng

### **Công Cụ Nghiên Cứu**
- `search_web`: Tìm kiếm web thời gian thực qua Tavily
- `retrival_vector_db`: Tìm kiếm ngữ nghĩa qua tin tức tài chính Việt Nam

### **Công Cụ Tài Chính**  
- `listing_symbol`: Tra cứu mã chứng khoán Việt Nam
- `history_price`: Dữ liệu giá lịch sử (nhiều nguồn)
- `time_now`: Tiện ích múi giờ Việt Nam


