from typing import Any, Callable, List, Optional, cast
from langchain_tavily import TavilySearch 
from react_agent.configuration import Configuration
from vnstock import Listing, Quote, Company, Finance, Trading, Screener, Vnstock
from typing_extensions import Literal
from datetime import datetime
import pytz


async def search(query: str) -> Optional[dict[str, Any]]:
    """Search for general web results.

    This function performs a search using the Tavily search engine, which is designed
    to provide comprehensive, accurate, and trusted results. It's particularly useful
    for answering questions about current events.
    """
    configuration = Configuration.from_context()
    wrapped = TavilySearch(max_results=configuration.max_search_results)
    return cast(dict[str, Any], await wrapped.ainvoke({"query": query}))


async def retrival_vector_db(query: str) -> Optional[dict[str, Any]]:
    """
    Search based on the RAG news
    """
    pass


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
        symbol (str): The stock symbol to retrieve data for.
        source (SourceType): The source from which to retrieve the data. Default is 'VCI'.
        start_date (str): The start date for the historical data. Example: 2025-04-01
        end_date (str): The end date for the historical data. Example: 2025-04-01
        interval (IntervalType): The interval for the historical data. Default is '1D'.

    Returns:
        Optional[dict[str, Any]]: A dictionary containing historical price data, or None if not found.
    """
    quote = Quote(symbol=symbol, source=source)
    history_prices = quote.history(start=start_date, end=end_date, interval=interval)
    return history_prices

def time_now() -> Optional[dict[str, Any]]:
    """
    Get the current time in Vietnam.
    
    Returns:
        Optional[dict[str, Any]]: A dictionary containing the current time in Vietnam.
    """
    vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    current_time = datetime.now(vietnam_tz).strftime('%Y-%m-%d %H:%M:%S')
    return {"current_time": current_time}


TOOLS: List[Callable[..., Any]] = [search, retrival_vector_db, listing_symbol, history_price, time_now]