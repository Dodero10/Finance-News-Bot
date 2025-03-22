from rag.retriever import hybrid_search

# Truy vấn của bạn
query = "Theo Bản tin thị trường trái phiếu doanh nghiệp riêng lẻ tháng 2/2025 từ HNX cho biết gì"

# Lấy top 10 kết quả (kết hợp từ đoạn văn và bảng)
results = hybrid_search(
    query=query,
    collection_name="trai_phieu",
    paragraph_weight=1,  # Trọng số cho đoạn văn
    table_weight=0,      # Trọng số cho bảng
    top_k=10
)

# In kết quả
for i, doc in enumerate(results):
    print(f"\nKết quả #{i+1} (score: {doc['score']}):")
    print(f"Loại: {doc['metadata'].get('chunk_type', 'Không xác định')}")
    print(f"Tiêu đề: {doc['metadata'].get('title', 'Không có tiêu đề')}")
    print(f"Nội dung: {doc['content'][:200]}...")
