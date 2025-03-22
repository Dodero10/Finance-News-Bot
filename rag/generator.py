from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from rag.config import (
    OPENAI_API_KEY, GOOGLE_API_KEY,
    LLM_MODEL, GEMINI_MODEL, LLM_PROVIDER
)

def get_llm():
    """Get the appropriate LLM based on config."""
    if LLM_PROVIDER == "openai":
        return ChatOpenAI(
            model=LLM_MODEL,
            openai_api_key=OPENAI_API_KEY,
        )
    elif LLM_PROVIDER == "google":
        return ChatOpenAI(
            model=GEMINI_MODEL,
            openai_api_key=GOOGLE_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")

def format_context(documents):
    """Format retrieved documents into context with better handling of different chunk types."""
    context_parts = []
    
    for i, doc in enumerate(documents):
        metadata = doc['metadata']
        content = doc['content']
        chunk_type = metadata.get('chunk_type', 'unknown')
        
        # Format source information
        source_info = f"Title: {metadata.get('title', 'Unknown')}"
        if 'time_published' in metadata:
            source_info += f", Date: {metadata.get('time_published')}"
        
        # Handle different chunk types
        if chunk_type == 'paragraph':
            # Format paragraph with heading if available
            heading = metadata.get('heading', '')
            if heading and not content.startswith(heading):
                content = f"{heading}\n{content}"
                
            context_parts.append(
                f"Đoạn {i+1} (từ bài: {metadata.get('title', 'Unknown')}):\n{content}\n"
            )
            
        elif chunk_type == 'table':
            # Format table with caption
            caption = metadata.get('caption', 'Bảng dữ liệu')
            context_parts.append(
                f"Bảng {i+1} (từ bài: {metadata.get('title', 'Unknown')}):\n"
                f"Mô tả: {caption}\n{content}\n"
            )
            
        elif chunk_type == 'full_article':
            # Format full article
            context_parts.append(
                f"Bài viết đầy đủ {i+1}:\n{content}\n"
                f"Nguồn: {source_info}\n"
            )
            
        else:
            # Default format for other types
            context_parts.append(
                f"Tài liệu {i+1}:\n{content}\nNguồn: {source_info}\n"
            )
    
    return "\n\n".join(context_parts)

def generate_answer(query, documents):
    """Generate answer based on query and retrieved documents."""
    # Get LLM
    llm = get_llm()
    
    # Format context
    context = format_context(documents)
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_template(
        """Bạn là trợ lý AI chuyên về thông tin tài chính, trái phiếu và tin tức quốc tế.
        Dựa vào thông tin dưới đây, hãy trả lời câu hỏi của người dùng.
        
        THÔNG TIN:
        {context}
        
        CÂU HỎI: {query}
        
        Hãy trả lời một cách chính xác và đầy đủ dựa trên thông tin được cung cấp.
        Nếu thông tin không đủ để trả lời, hãy nói rằng bạn không có đủ thông tin.
        Trả lời bằng tiếng Việt, định dạng rõ ràng và dễ đọc.
        Nếu có thông tin từ bảng, hãy tham chiếu rõ ràng đến dữ liệu trong bảng.
        Nếu có thông tin từ nhiều nguồn, hãy tổng hợp thông tin từ tất cả các nguồn liên quan."""
    )
    
    # Generate response
    chain = prompt | llm
    response = chain.invoke({
        "context": context,
        "query": query
    })
    
    return response.content

def generate_answer_with_hybrid_search(query, collection_name="default", top_k=None):
    """Generate answer using hybrid search (combines paragraphs and tables)."""
    from rag.retriever import hybrid_search
    
    # Retrieve documents using hybrid search
    documents = hybrid_search(query, collection_name, top_k=top_k)
    
    # Generate answer
    return generate_answer(query, documents)

def generate_answer_with_context(query, collection_name="default", top_k=None):
    """Generate answer with full article context for better understanding."""
    from rag.retriever import retrieve_with_context
    
    # Retrieve documents with context
    documents = retrieve_with_context(query, collection_name, top_k=top_k)
    
    # Generate answer
    return generate_answer(query, documents)

def classify_query_type(query):
    """Classify the query to determine best retrieval strategy."""
    query_lower = query.lower()
    
    # Check for data/statistics queries (likely to need tables)
    data_keywords = ['bao nhiêu', 'số lượng', 'giá trị', 'thống kê', 'phần trăm', 
                   'bảng', 'biểu đồ', 'đợt', 'tỷ đồng', 'tỷ lệ']
    
    # Check for explanation/summary queries (likely to need paragraphs)
    explanation_keywords = ['giải thích', 'là gì', 'tại sao', 'lý do', 'đánh giá',
                          'nhận định', 'tổng quan', 'tóm tắt']
    
    # Count matches for each category
    data_score = sum(1 for kw in data_keywords if kw in query_lower)
    explanation_score = sum(1 for kw in explanation_keywords if kw in query_lower)
    
    # Determine query type and suggested retrieval method
    if data_score > explanation_score:
        return {
            'query_type': 'data',
            'suggested_method': 'retrieve_tables',
            'paragraph_weight': 0.3,
            'table_weight': 0.7
        }
    elif explanation_score > data_score:
        return {
            'query_type': 'explanation',
            'suggested_method': 'retrieve_paragraphs',
            'paragraph_weight': 0.8,
            'table_weight': 0.2
        }
    else:
        return {
            'query_type': 'general',
            'suggested_method': 'hybrid_search',
            'paragraph_weight': 0.5,
            'table_weight': 0.5
        }

def smart_generate_answer(query, collection_name="default", top_k=None):
    """Intelligently select the best retrieval strategy based on query type."""
    from rag.retriever import (
        retrieve_paragraphs, retrieve_tables, 
        hybrid_search, retrieve_with_context
    )
    
    # Classify query type
    query_info = classify_query_type(query)
    query_type = query_info['query_type']
    
    # Retrieve documents based on query type
    if query_type == 'data':
        # For data queries, prioritize tables but include some paragraphs
        table_results = retrieve_tables(query, collection_name, top_k=top_k or 3)
        paragraph_results = retrieve_paragraphs(query, collection_name, top_k=2)
        documents = table_results + paragraph_results
    
    elif query_type == 'explanation':
        # For explanation queries, prioritize paragraphs but include relevant tables
        paragraph_results = retrieve_paragraphs(query, collection_name, top_k=top_k or 4)
        table_results = retrieve_tables(query, collection_name, top_k=1)
        documents = paragraph_results + table_results
    
    else:
        # For general queries, use hybrid search with balanced weights
        documents = hybrid_search(
            query, 
            collection_name, 
            paragraph_weight=query_info['paragraph_weight'],
            table_weight=query_info['table_weight'],
            top_k=top_k
        )
    
    # Always add full article context for the most relevant chunk
    if documents and 'article_id' in documents[0]['metadata']:
        article_id = documents[0]['metadata']['article_id']
        from rag.retriever import retrieve_full_article
        
        full_article = retrieve_full_article(article_id, collection_name)
        if full_article:
            documents.append(full_article)
    
    # Generate answer
    return generate_answer(query, documents)
