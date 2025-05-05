from langfuse.callback import CallbackHandler
from react_agent_graph import graph
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
    result = await graph.ainvoke({
        "messages": [HumanMessage(content = "Bạn cho tôi biết lịch sử giá cổ phiếu công ty Công ty Cổ phần Xuất nhập khẩu Y tế Thành phố Hồ Chí Minh trong 2 tuần gần đây")]
    }, config={"callbacks": [langfuse_handler]})
    print("Results", result)

asyncio.run(main())