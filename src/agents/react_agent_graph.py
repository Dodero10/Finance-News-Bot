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
    """Call the LLM powering our "agent".

    This function prepares the prompt, initializes the model, and processes the response.

    Args:
        state (State): The current state of the conversation.
        config (RunnableConfig): Configuration for the model run.

    Returns:
        dict: A dictionary containing the model's response message.
    """
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
    """Determine the next node based on the model's output.

    This function checks if the model's last message contains tool calls.

    Args:
        state (State): The current state of the conversation.

    Returns:
        str: The name of the next node to call ("__end__" or "tools").
    """
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
        )
    # If there is no tool call, then we finish
    if not last_message.tool_calls:
        return "__end__"
    # Otherwise we execute the requested actions
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
    initial_state = InputState(
        messages=[
            HumanMessage(content="Hôm nay có tin tức tài chính gì hot ở Việt Nam không?")
        ]
    )
    result = await graph.ainvoke(initial_state, config={"callbacks": [langfuse_handler]})
    
    print("\nInput:")
    print("------")
    for msg in initial_state.messages:
        print(f"User: {msg.content}")
    
    print("\nOutput:")
    print("-------")
    # The result is a dictionary with 'messages' key
    if 'messages' in result:
        # Get only the last message which contains the final response
        messages = result['messages']
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, 'content'):
                print(f"AI: {last_message.content}")
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                print("\nTool Calls:")
                for tool_call in last_message.tool_calls:
                    print(f"- Tool: {tool_call.function.name}")
                    print(f"  Arguments: {tool_call.function.arguments}")
    else:
        print("No messages in result")
        print("Result structure:", result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
