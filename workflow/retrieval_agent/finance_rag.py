"""
Finance News RAG System

This module implements a naive Retrieval-Augmented Generation (RAG) system
for finance news data using LangGraph.
"""

import json
import os
from typing import Dict, List, Any, TypedDict, Optional

import numpy as np
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_google_genai import GoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.embeddings import Embeddings
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langgraph.graph import END, StateGraph

# Type definitions for state
class RAGState(TypedDict):
    """State for the RAG workflow."""
    question: str
    context: List[Dict[str, Any]]
    generation: Optional[str]
    search_queries: Optional[List[str]]
    documents: Optional[List[Dict[str, Any]]]
    answer: Optional[str]


class FinanceNewsRAG:
    """
    Finance News RAG system using LangGraph for orchestration.
    
    This class implements a naive RAG system for financial news data,
    with a focus on modularity and clean separation of concerns.
    """
    
    def __init__(
        self, 
        data_path: str = "data",
        google_api_key: Optional[str] = None,
        embedding_model: str = "models/embedding-001",
        llm_model: str = "gemini-1.5-pro-latest"
    ):
        """
        Initialize the Finance News RAG system.
        
        Args:
            data_path: Path to the directory containing JSON data files
            google_api_key: Google API key for Gemini
            embedding_model: Model name for embeddings
            llm_model: Model name for the LLM
        """
        # Set API key from environment if not provided
        self.api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY in .env file or pass it as a parameter.")
            
        # Initialize models
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.embeddings = GoogleGenerativeAIEmbeddings(model=embedding_model)
        self.llm = GoogleGenerativeAI(model=llm_model, google_api_key=self.api_key)
        
        # Set data path and initialize vector store
        self.data_path = data_path
        self.vector_store = None
        
        # Create state graph
        self.workflow = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        """
        Create the LangGraph workflow for RAG.
        
        Returns:
            StateGraph: The configured workflow graph
        """
        # Create a new graph
        builder = StateGraph(RAGState)
        
        # Add nodes to the graph
        builder.add_node("generate_search_queries", self.generate_search_queries)
        builder.add_node("retrieve_documents", self.retrieve_documents)
        builder.add_node("generate_answer", self.generate_answer)
        
        # Define the edges
        builder.add_edge("generate_search_queries", "retrieve_documents")
        builder.add_edge("retrieve_documents", "generate_answer")
        builder.add_edge("generate_answer", END)
        
        # Set the entry point
        builder.set_entry_point("generate_search_queries")
        
        # Compile the graph
        return builder.compile()
    
    def load_data(self, json_files: List[str] = None) -> int:
        """
        Load JSON news data and create a vector store.
        
        Args:
            json_files: List of JSON filenames to load (default: all .json files in data_path)
            
        Returns:
            int: Number of documents loaded into the vector store
        """
        if json_files is None:
            json_files = [f for f in os.listdir(self.data_path) if f.endswith('.json')]
        
        documents = []
        for file_name in json_files:
            file_path = os.path.join(self.data_path, file_name)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    # Check if the file contains a JSON array or a single object
                    content = f.read()
                    if content.strip().startswith('['):
                        data = json.loads(content)
                    else:
                        data = [json.loads(content)]
                    
                    # Process each article
                    for article in data:
                        # Create document with content and metadata
                        document = {
                            "id": article.get("url", "").split("/")[-1].split(".")[0],
                            "content": article.get("content", ""),
                            "title": article.get("title", ""),
                            "summary": article.get("summary", ""),
                            "tags": article.get("tags", []),
                            "author": article.get("author", ""),
                            "time_published": article.get("time_published", ""),
                            "url": article.get("url", ""),
                        }
                        documents.append(document)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        # Create vector store from documents
        texts = [doc["content"] for doc in documents]
        metadatas = [{k: v for k, v in doc.items() if k != "content"} for doc in documents]
        
        # Filter complex metadata to ensure compatibility with ChromaDB
        # Create a custom function to filter complex metadata from dictionaries
        def filter_complex_metadata_dict(metadata_dict):
            filtered_dict = {}
            for key, value in metadata_dict.items():
                # Only include simple types (strings, numbers, booleans)
                if isinstance(value, (str, int, float, bool)) or value is None:
                    filtered_dict[key] = value
            return filtered_dict
            
        filtered_metadatas = [filter_complex_metadata_dict(metadata) for metadata in metadatas]
        
        print("Texts: ", texts)
        print("Filtered Metadatas: ", filtered_metadatas)

        print(f"Creating vector store with {len(texts)} documents")
        self.vector_store = Chroma.from_texts(
            texts=texts,
            collection_name="finance_news",
            persist_directory="finance_news_vector_db",
            embedding=self.embeddings,
            metadatas=filtered_metadatas
        )
        
        print(f"Vector store created with {len(texts)} documents")
        return len(texts)
    
    def generate_search_queries(self, state: RAGState) -> RAGState:
        """
        Generate search queries from the user question.
        
        Args:
            state: Current state containing the user question
            
        Returns:
            Updated state with search queries
        """
        # Create prompt template for query generation
        template = """
        Based on the user question, generate up to 3 search queries that would help retrieve 
        relevant financial news articles. The queries should be diverse and focus on different aspects
        of the question to maximize the chance of finding relevant information.
        
        User question: {question}
        
        Generate exactly 3 search queries, one per line.
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()
        
        # Generate search queries
        output = chain.invoke({"question": state["question"]})
        search_queries = [q.strip() for q in output.split("\n") if q.strip()]
        
        # Update state
        return {**state, "search_queries": search_queries}
    
    def retrieve_documents(self, state: RAGState) -> RAGState:
        """
        Retrieve relevant documents using the search queries.
        
        Args:
            state: Current state with search queries
            
        Returns:
            Updated state with retrieved documents
        """
        if not self.vector_store:
            raise ValueError("Vector store not initialized. Call load_data() first.")
        
        all_docs = []
        for query in state["search_queries"]:
            docs = self.vector_store.similarity_search(query, k=3)
            for doc in docs:
                # Convert LangChain document to dict
                doc_dict = {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                # Only add if not already in the list
                if doc_dict not in all_docs:
                    all_docs.append(doc_dict)
        
        # Update state
        return {**state, "documents": all_docs}
    
    def generate_answer(self, state: RAGState) -> RAGState:
        """
        Generate an answer based on the retrieved documents and user question.
        
        Args:
            state: Current state with retrieved documents
            
        Returns:
            Updated state with generated answer
        """
        # Format context from documents
        context_parts = []
        for i, doc in enumerate(state["documents"]):
            context = f"Document {i+1}:\n"
            context += f"Title: {doc['metadata'].get('title', 'N/A')}\n"
            context += f"Content: {doc['content']}\n"
            context_parts.append(context)
        
        context_str = "\n\n".join(context_parts)
        
        # Create prompt for answer generation
        template = """
        You are a financial news assistant. Answer the user's question based on the 
        retrieved financial news articles provided below.
        
        Retrieved articles:
        {context}
        
        User question: {question}
        
        Provide a concise and informative answer based only on the information in the retrieved articles.
        If the articles don't contain relevant information to answer the question, state that clearly.
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()
        
        # Generate answer
        answer = chain.invoke({
            "context": context_str,
            "question": state["question"]
        })
        
        # Update state
        return {**state, "answer": answer}
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Run the RAG workflow for a user question.
        
        Args:
            question: User question
            
        Returns:
            Final state with answer and related information
        """
        # Check if vector store is initialized
        if not self.vector_store:
            raise ValueError("Vector store not initialized. Call load_data() first.")
        
        # Initialize state
        initial_state: RAGState = {
            "question": question,
            "context": [],
            "generation": None,
            "search_queries": None,
            "documents": None,
            "answer": None
        }
        
        # Run the workflow
        final_state = self.workflow.invoke(initial_state)
        return final_state 
    
if __name__ == "__main__":
    rag = FinanceNewsRAG(data_path="data_test")
    rag.load_data()
    print(rag.query("What is the latest news on the stock market?"))
