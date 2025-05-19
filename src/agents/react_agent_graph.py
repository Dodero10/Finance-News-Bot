from datetime import UTC, datetime
from typing import Dict, List, Literal, cast

from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from src.agents.configuration import Configuration
from src.agents.state import InputState, State
from src.agents.tools import TOOLS
from src.agents.utils import load_chat_model
from src.agents.prompts import REACT_AGENT_PROMPT


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
