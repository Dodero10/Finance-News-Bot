from langfuse.callback import CallbackHandler
from react_agent_graph import graph
from reflection_agent_graph import graph as reflection_graph
from rewoo_agent_graph import graph as rewoo_graph
from langchain_core.messages import HumanMessage
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

os.environ["LANGFUSE_PUBLIC_KEY"] = os.getenv("LANGFUSE_PUBLIC_KEY")
os.environ["LANGFUSE_SECRET_KEY"] = os.getenv("LANGFUSE_SECRET_KEY")
os.environ["LANGFUSE_HOST"] = os.getenv("LANGFUSE_HOST")

# Initialize Langfuse CallbackHandler for Langchain (tracing)
langfuse_handler = CallbackHandler()

async def main():
    test_query = "Cho tôi biết Thống kê thị trường trái phiếu doanh nghiệp riêng lẻ tháng 4/2025"
    
    print("==== TESTING REACT AGENT ====")
    # Test RAG with a query about corporate bonds
    result = await graph.ainvoke({
        "messages": [HumanMessage(content = test_query)]
    }, config={"callbacks": [langfuse_handler]})
    print("Results from ReAct Agent:", result)
    
    print("\n==== TESTING REFLECTION AGENT ====")
    # Test the same query with the reflection agent
    reflection_result = await reflection_graph.ainvoke({
        "messages": [HumanMessage(content = test_query)]
    }, config={"callbacks": [langfuse_handler]})
    print("Results from Reflection Agent:", reflection_result)
    
    print("\n==== TESTING REWOO AGENT ====")
    # Test the same query with the ReWOO agent
    rewoo_result = await rewoo_graph.ainvoke({
        "task": test_query
    }, config={"callbacks": [langfuse_handler]})
    print("Results from ReWOO Agent:", rewoo_result)

    # Uncomment to test stock history
    # result = await graph.ainvoke({
    #     "messages": [HumanMessage(content = "Bạn cho tôi biết lịch sử giá cổ phiếu công ty Công ty Cổ phần Xuất nhập khẩu Y tế Thành phố Hồ Chí Minh trong 2 tuần gần đây")]
    # }, config={"callbacks": [langfuse_handler]})
    # print("Results", result)

if __name__ == "__main__":
    asyncio.run(main())