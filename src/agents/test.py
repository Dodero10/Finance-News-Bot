import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, project_root)

from langfuse.callback import CallbackHandler
from src.agents.react_agent_graph import graph as react_graph
from src.agents.reflection_agent_graph import graph as reflection_graph
from src.agents.rewoo_agent_graph import graph as rewoo_graph
from src.agents.reflexion_agent_graph import graph as reflexion_graph
from src.agents.multi_agent import multi_agent_graph
from langchain_core.messages import HumanMessage
import asyncio
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

    async for s in react_graph.astream({
        "messages": [HumanMessage(content=test_query)]
    }, config={"callbacks": [langfuse_handler]}):
        print(s)
        print("--------------------------------")
    
    # print("\n==== TESTING REFLECTION AGENT ====")
    # # Test the same query with the reflection agent
    # reflection_result = await reflection_graph.ainvoke({
    #     "messages": [HumanMessage(content = test_query)]
    # }, config={"callbacks": [langfuse_handler]})
    # print("Results from Reflection Agent:", reflection_result)
    
    # print("\n==== TESTING REWOO AGENT ====")
    # # Test the same query with the ReWOO agent
    # rewoo_result = await rewoo_graph.ainvoke({
    #     "task": test_query
    # }, config={"callbacks": [langfuse_handler]})
    # print("Results from ReWOO Agent:", rewoo_result)

    # print("\n==== TESTING REFLEXION AGENT ====")
    # # Test the same query with the ReWOO agent
    # reflexion_result = await reflexion_graph.ainvoke({
    #     "task": test_query
    # }, config={"callbacks": [langfuse_handler]})
    # print("Results from Reflexion Agent:", reflexion_result)    

    # print("\n==== TESTING MULTI AGENT ====")
    # multi_agent_result = await multi_agent_graph.ainvoke({
    #     "task": test_query
    # }, config={"callbacks": [langfuse_handler]})
    # print("Results from Multi Agent:", multi_agent_result)

    # Uncomment to test stock history
    # result = await graph.ainvoke({
    #     "messages": [HumanMessage(content = "Bạn cho tôi biết lịch sử giá cổ phiếu công ty Công ty Cổ phần Xuất nhập khẩu Y tế Thành phố Hồ Chí Minh trong 2 tuần gần đây")]
    # }, config={"callbacks": [langfuse_handler]})
    # print("Results", result)

if __name__ == "__main__":
    asyncio.run(main())