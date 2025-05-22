import os
import sys
from datetime import UTC, datetime
from typing import Dict, List, Literal, cast

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from langfuse import Langfuse
from langfuse.callback import CallbackHandler   

from src.agents.configuration import Configuration
from src.agents.state import InputState, State
from src.agents.tools import TOOLS
from src.agents.utils import load_chat_model
from src.agents.prompts import REACT_AGENT_PROMPT



# Load environment variables
load_dotenv()

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_API_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

langfuse_handler = CallbackHandler()

async def react_agent(state: State) -> Dict[str, List[AIMessage]]:

    configuration = Configuration(
        model="openai/gpt-4o-mini",
        system_prompt=REACT_AGENT_PROMPT,
    )

    model = load_chat_model(configuration.model).bind_tools(TOOLS)
    system_message = configuration.system_prompt

    response = cast(
        AIMessage,
        await model.ainvoke(
            [{"role": "system", "content": system_message}, *state.messages]
        ),
    )

    if state.is_last_step and response.tool_calls:
        return {
            "messages": [
                AIMessage(
                    id=response.id,
                    content="Sorry, I could not find an answer to your question in the specified number of steps.",
                )
            ]
        }

    return {"messages": [response]}


def route_model_output(state: State) -> Literal["__end__", "tools"]:

    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
        )

    if not last_message.tool_calls:
        return "__end__"

    return "tools"


builder = StateGraph(State, input=InputState, config_schema=Configuration)

builder.add_node(react_agent)
builder.add_node("tools", ToolNode(TOOLS))
builder.add_edge("__start__", "react_agent")
builder.add_edge("tools", "react_agent")
builder.add_conditional_edges(
    "react_agent",
    route_model_output,
)
# Compile the builder into an executable graph
graph = builder.compile(name="ReAct Agent")

async def main():
    test_query = "Tin tức về giá cả cổ phiếu của công ty FPT trong tuần vừa qua"
    
    # Print the input query
    print("\n=== INPUT ===")
    print(f"User: {test_query}")
    
    # Get final result using invoke instead of stream
    result = await graph.ainvoke({
        "messages": [HumanMessage(content=test_query)]
    }, config={"callbacks": [langfuse_handler]})
    
    print("\n=== FINAL OUTPUT ===")
    
    # Access the final message in the result
    if "messages" in result:
        messages = result["messages"]
        if messages:
            # Get the last message which contains the final response
            final_message = messages[-1]
            if isinstance(final_message, AIMessage):
                print(f"AI: {final_message.content}")
                
    # Show tools used during the conversation
    tool_messages = [msg for msg in result.get("messages", []) 
                    if hasattr(msg, "name") and getattr(msg, "name", None)]
    
    if tool_messages:
        print("\n=== TOOLS USED ===")
        for i, msg in enumerate(tool_messages, 1):
            print(f"{i}. {msg.name}")
    else:
        print("\nNo tools were used in this interaction.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())