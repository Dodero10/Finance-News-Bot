from typing import Any, Callable, List, Optional, cast
from langchain_tavily import TavilySearch 
from agents.configuration import Configuration
from vnstock import Listing, Quote, Company, Finance, Trading, Screener, Vnstock
from typing_extensions import Literal
from datetime import datetime
import pytz
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import os
from langchain_core.documents import Document
import asyncio
from src.rag.embedding_utils import retrieve_from_db


async def search_web(query: str) -> Optional[dict[str, Any]]:
    """Search for general web results.

    This function performs a search using the Tavily search engine, which is designed
    to provide comprehensive, accurate, and trusted results. It's particularly useful
    for answering questions about current events.
    
    Args:
        query: The search query to find information.
    """
    configuration = Configuration.from_context()
    wrapped = TavilySearch(max_results=configuration.max_search_results)
    return cast(dict[str, Any], await wrapped.ainvoke({"query": query}))

async def retrival_vector_db(query: str) -> Optional[dict[str, Any]]:
    """
    Search based on the RAG news from ChromaDB vector database.
    
    This function performs a semantic search on financial news articles 
    that have been stored in a vector database. It returns the most relevant
    articles based on the query, including their content and metadata.
    
    Args:
        query: The search query to find relevant finance news articles.
    """
    try:
        configuration = Configuration.from_context()
        
        def perform_retrieval():
            max_results = configuration.max_search_results
            
            chunks = retrieve_from_db(
                query=query,
                db_path="finance_news_vector_db",
                collection_name="finance_news",
                n_results=max_results,
                return_formatted=False
            )
            
            results = []
            for chunk in chunks:
                result = {
                    "content": chunk["content"],
                    "metadata": chunk["metadata"]
                }
                results.append(result)
            
            return {
                "query": query,
                "results": results,
                "source": "finance_news_vector_db"
            }
        
        return await asyncio.to_thread(perform_retrieval)
        
    except Exception as e:
        return {
            "query": query,
            "results": [],
            "error": str(e)
        }


### Tools from vnstock
def listing_symbol():
    """Get listing symbol about stock wth company name"""
    listing = Listing()
    return listing.all_symbols()


IntervalType = Literal['1m', '5m', '15m', '30m', '1H', '1D', '1W', '1M']
SourceType = Literal['VCI', 'TCBS', 'MSN']

def history_price(symbol: str, source: SourceType, start_date: str, end_date: str, interval: IntervalType) -> Optional[dict[str, Any]]:
    """
    Retrieve historical price data for a given stock symbol.
    
    Args:
        symbol: The stock symbol to retrieve data for.
        source: The source from which to retrieve the data. Default is 'VCI'.
        start_date: The start date for the historical data. Example: 2025-04-01
        end_date: The end date for the historical data. Example: 2025-04-01
        interval: The interval for the historical data. Default is '1D'.
    """
    quote = Quote(symbol=symbol, source=source)
    history_prices = quote.history(start=start_date, end=end_date, interval=interval)
    return history_prices

def time_now() -> Optional[dict[str, Any]]:
    """
    Get the current time in Vietnam.
    """
    vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    current_time = datetime.now(vietnam_tz).strftime('%Y-%m-%d %H:%M:%S')
    return {"current_time": current_time}


TOOLS: List[Callable[..., Any]] = [search_web, retrival_vector_db, listing_symbol, history_price, time_now]