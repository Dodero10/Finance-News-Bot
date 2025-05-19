from datetime import UTC, datetime
from typing import Dict, List, Literal, cast

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from agents.configuration import Configuration
from agents.state import InputState, State
from agents.tools import TOOLS
from agents.utils import load_chat_model
from agents.prompts import REFLECTION_PROMPT
from dotenv import load_dotenv
from langfuse.callback import CallbackHandler
import os

load_dotenv()

langfuse_handler = CallbackHandler(
    secret_key=os.getenv("LANGFUSE_API_KEY"),
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    host=os.getenv("LANGFUSE_HOST"),
)


async def generate_agent(state: State) -> Dict[str, List[AIMessage]]:
    """Call the LLM to generate responses and tool calls.

    Args:
        state (State): The current state of the conversation.

    Returns:
        dict: A dictionary containing the model's response message.
    """
    configuration = Configuration(
        model="openai/gpt-4o-mini",
        system_prompt=REFLECTION_PROMPT,
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


async def reflect_on_response(state: State) -> Dict[str, List[AIMessage]]:
    """Call the LLM to reflect on previous responses and improve them.

    Args:
        state (State): The current state of the conversation.

    Returns:
        dict: A dictionary containing the reflection message.
    """
    configuration = Configuration(
        model="openai/gpt-4o-mini",
        system_prompt=REFLECTION_PROMPT,
    )
    reflect_prompt = configuration.system_prompt
    model = load_chat_model(configuration.model)

    reflection_messages = [state.messages[0]]

    for msg in state.messages[1:]:
        if msg.type == "ai":
            reflection_messages.append(HumanMessage(content=msg.content))
        elif msg.type == "human":
            reflection_messages.append(AIMessage(content=msg.content))
        elif msg.type == "tool":
            tool_content = f"Tool result from {msg.name}: {msg.content}"
            reflection_messages.append(HumanMessage(content=tool_content))

    response = await model.ainvoke(
        [{"role": "system", "content": reflect_prompt}, *reflection_messages]
    )

    return {"messages": [HumanMessage(content=response.content)]}


def route_model_output(state: State) -> Literal["__end__", "tools", "reflect"]:
    """Determine the next node based on the model's output.

    This function checks if the model's last message contains tool calls or if it should trigger reflection.

    Args:
        state (State): The current state of the conversation.

    Returns:
        str: The name of the next node to call ("__end__", "tools", or "reflect").
    """
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        return "generate"

    if last_message.tool_calls:
        return "tools"

    tool_calls_made = any(
        isinstance(msg, AIMessage) and msg.tool_calls
        for msg in state.messages[:-1]
    )

    if tool_calls_made:
        return "reflect"

    return "reflect"


def should_continue_after_reflection(state: State) -> Literal["__end__", "generate"]:
    """Determine whether to continue generation or end after reflection.

    Args:
        state (State): The current state of the conversation.

    Returns:
        str: The name of the next node to call ("__end__" or "generate").
    """
    # Find all reflection messages (human messages after the first one)
    reflection_messages = [
        msg for msg in state.messages
        # Not the initial user query
        if msg.type == "human" and msg != state.messages[0]
    ]

    # Count reflection cycles
    reflection_count = len(reflection_messages)

    # If we've gone through too many reflection cycles, end
    # Limiting to 2 reflection cycles (for a total of 3 responses)
    if reflection_count >= 2:
        return "__end__"

    # Otherwise, continue with generation
    return "generate"


builder = StateGraph(State, input=InputState, config_schema=Configuration)
builder.add_node("generate", generate_agent)
builder.add_node("reflect", reflect_on_response)
builder.add_node("tools", ToolNode(TOOLS))
builder.add_edge("__start__", "generate")
builder.add_edge("tools", "generate")
builder.add_conditional_edges(
    "generate",
    route_model_output,
)
builder.add_conditional_edges(
    "reflect",
    should_continue_after_reflection,
)
# Compile the builder into an executable graph
graph = builder.compile(name="Reflection Agent")