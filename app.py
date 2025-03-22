from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from rag.retriever import retrieve_documents, retrieve_paragraphs, retrieve_tables, hybrid_search, retrieve_with_context
from rag.generator import generate_answer, smart_generate_answer, classify_query_type
from rag.utils import get_collection_stats, list_collections, compare_retrieval_methods
from rag.config import CHROMA_DB_PATH
import uvicorn

app = FastAPI(title="RAG API", description="API for Retrieval-Augmented Generation")

class QueryRequest(BaseModel):
    query: str
    collection: str = "default"
    top_k: int = 5
    retrieval_method: str = "smart"  # 'standard', 'paragraphs', 'tables', 'hybrid', 'context', 'smart'

class RagResponse(BaseModel):
    query: str
    answer: str
    documents: list
    query_analysis: dict = None

@app.post("/rag", response_model=RagResponse)
def rag_endpoint(request: QueryRequest):
    """RAG endpoint that retrieves documents and generates an answer."""
    try:
        documents = []
        query_analysis = None
        
        # Select retrieval method based on request
        if request.retrieval_method == "standard":
            documents = retrieve_documents(
                query=request.query,
                collection_name=request.collection,
                top_k=request.top_k
            )
            answer = generate_answer(request.query, documents)
            
        elif request.retrieval_method == "paragraphs":
            documents = retrieve_paragraphs(
                query=request.query,
                collection_name=request.collection,
                top_k=request.top_k
            )
            answer = generate_answer(request.query, documents)
            
        elif request.retrieval_method == "tables":
            documents = retrieve_tables(
                query=request.query,
                collection_name=request.collection,
                top_k=request.top_k
            )
            answer = generate_answer(request.query, documents)
            
        elif request.retrieval_method == "hybrid":
            documents = hybrid_search(
                query=request.query,
                collection_name=request.collection,
                top_k=request.top_k
            )
            answer = generate_answer(request.query, documents)
            
        elif request.retrieval_method == "context":
            documents = retrieve_with_context(
                query=request.query,
                collection_name=request.collection,
                top_k=request.top_k
            )
            answer = generate_answer(request.query, documents)
            
        elif request.retrieval_method == "smart":
            # Analyze query and use smart retrieval
            query_analysis = classify_query_type(request.query)
            answer = smart_generate_answer(
                query=request.query,
                collection_name=request.collection,
                top_k=request.top_k
            )
            # Get standard documents for comparison
            documents = retrieve_documents(
                query=request.query,
                collection_name=request.collection,
                top_k=request.top_k
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported retrieval method: {request.retrieval_method}")
        
        if not documents:
            return {
                "query": request.query,
                "answer": "Không tìm thấy thông tin liên quan.",
                "documents": [],
                "query_analysis": query_analysis
            }
        
        return {
            "query": request.query,
            "answer": answer,
            "documents": documents,
            "query_analysis": query_analysis
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/collections")
def get_collections():
    """Get list of available collections."""
    collections = list_collections(CHROMA_DB_PATH)
    return {"collections": collections}

@app.get("/collection-stats/{collection_name}")
def collection_stats(collection_name: str):
    """Get statistics about a collection."""
    stats = get_collection_stats(collection_name, CHROMA_DB_PATH)
    return stats

@app.post("/compare-methods")
def compare_methods(request: QueryRequest):
    """Compare retrieval methods for a query."""
    results = compare_retrieval_methods(
        query=request.query,
        collection_name=request.collection,
        top_k=request.top_k
    )
    return results

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
