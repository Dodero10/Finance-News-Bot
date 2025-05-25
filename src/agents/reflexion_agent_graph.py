import os
import sys
from datetime import UTC, datetime
from typing import Dict, List, Literal, cast

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
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
from src.agents.prompts import REFLEXION_FIRST_RESPONDER_PROMPT, REFLEXION_REVISION_PROMPT

# Load environment variables
load_dotenv()

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_API_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

langfuse_handler = CallbackHandler()

# Updated Vietnamese prompts for reflector
REFLEXION_REFLECTOR_PROMPT = """Bạn là một chuyên gia đánh giá chất lượng phản hồi về tin tức tài chính.

Đánh giá phản hồi dựa trên:
1. Tính chính xác của thông tin
2. Mức độ liên quan đến câu hỏi của người dùng
3. Tính đầy đủ của câu trả lời
4. Việc sử dụng công cụ và nguồn thông tin phù hợp
5. Tính rõ ràng và cấu trúc

Nếu phản hồi có vấn đề, hãy đưa ra phản hồi cụ thể về:
- Thông tin nào còn thiếu
- Điều gì có thể được cải thiện
- Hành động cụ thể nào nên thực hiện để có câu trả lời tốt hơn

Nếu phản hồi đã đủ tốt, chỉ cần trả lời "Phản hồi này đã đạt yêu cầu."

Phản hồi cần đánh giá: {response}
Câu hỏi của người dùng: {query}"""

REFLEXION_ACTOR_REFLECT_PROMPT = """Bạn là một trợ lý AI chuyên nghiệp về tài chính Việt Nam. Bạn đã đưa ra phản hồi trước đó nhưng nhận được góp ý để cải thiện.

Câu hỏi gốc: {query}
Phản hồi trước đó của bạn: {previous_response}
Góp ý cải thiện: {reflection}

Dựa trên góp ý, hãy đưa ra phản hồi được cải thiện. Sử dụng các công cụ có sẵn để thu thập thêm thông tin nếu cần."""


async def reflexion_actor(state: State) -> Dict[str, List[AIMessage]]:
    """Main actor that generates responses using tools"""
    configuration = Configuration(
        model="openai/gpt-4o-mini",
        system_prompt=REFLEXION_FIRST_RESPONDER_PROMPT,
    )

    model = load_chat_model(configuration.model).bind_tools(TOOLS)
    
    response = cast(
        AIMessage,
        await model.ainvoke(
            [{"role": "system", "content": configuration.system_prompt}, *state.messages]
        ),
    )

    if state.is_last_step and response.tool_calls:
        return {
            "messages": [
                AIMessage(
                    id=response.id,
                    content="Xin lỗi, tôi không thể tìm được câu trả lời cho câu hỏi của bạn trong số bước được chỉ định.",
                )
            ]
        }

    return {"messages": [response]}


async def reflexion_reflector(state: State) -> Dict[str, List[AIMessage]]:
    """Reflector that evaluates the actor's response"""
    configuration = Configuration(
        model="openai/gpt-4o-mini",
        system_prompt="Bạn là một trợ lý hữu ích đánh giá các phản hồi.",
    )

    model = load_chat_model(configuration.model)
    
    # Get the original query and the last response
    user_query = ""
    last_ai_response = ""
    
    for message in state.messages:
        if isinstance(message, HumanMessage):
            user_query = message.content
        elif isinstance(message, AIMessage) and not hasattr(message, 'name'):
            last_ai_response = message.content
    
    reflection_prompt = REFLEXION_REFLECTOR_PROMPT.format(
        response=last_ai_response,
        query=user_query
    )
    
    response = cast(
        AIMessage,
        await model.ainvoke([{"role": "user", "content": reflection_prompt}])
    )
    
    # Add reflection metadata to track this as a reflection
    response.additional_kwargs["reflection"] = True
    
    return {"messages": [response]}


async def reflexion_actor_reflect(state: State) -> Dict[str, List[AIMessage]]:
    """Actor that improves response based on reflection"""
    configuration = Configuration(
        model="openai/gpt-4o-mini",
        system_prompt=REFLEXION_REVISION_PROMPT,
    )

    model = load_chat_model(configuration.model).bind_tools(TOOLS)
    
    # Extract original query, previous response, and reflection
    user_query = ""
    previous_response = ""
    reflection = ""
    
    for message in state.messages:
        if isinstance(message, HumanMessage):
            user_query = message.content
        elif isinstance(message, AIMessage):
            if message.additional_kwargs.get("reflection"):
                reflection = message.content
            else:
                previous_response = message.content
    
    improve_prompt = REFLEXION_ACTOR_REFLECT_PROMPT.format(
        query=user_query,
        previous_response=previous_response,
        reflection=reflection
    )
    
    response = cast(
        AIMessage,
        await model.ainvoke([{"role": "user", "content": improve_prompt}])
    )

    if state.is_last_step and response.tool_calls:
        return {
            "messages": [
                AIMessage(
                    id=response.id,
                    content="Xin lỗi, tôi không thể tìm được câu trả lời cho câu hỏi của bạn trong số bước được chỉ định.",
                )
            ]
        }

    return {"messages": [response]}


def route_after_actor(state: State) -> Literal["tools", "reflector"]:
    """Route after actor - if tool calls exist, go to tools, otherwise go to reflector"""
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
        )

    if last_message.tool_calls:
        return "tools"
    
    return "reflector"


def route_after_reflector(state: State) -> Literal["__end__", "actor_reflect"]:
    """Route after reflector - if reflection says satisfactory, end, otherwise improve"""
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
        )
    
    # Count how many reflections we've done to prevent infinite loops
    reflection_count = sum(1 for msg in state.messages 
                          if isinstance(msg, AIMessage) and msg.additional_kwargs.get("reflection"))
    
    # Limit to maximum 2 reflection cycles
    if reflection_count >= 2:
        return "__end__"
    
    # Check if the reflection indicates the response is satisfactory (Vietnamese keywords)
    reflection_content = last_message.content.lower()
    if ("đạt yêu cầu" in reflection_content or 
        "đủ tốt" in reflection_content or 
        "thỏa mãn" in reflection_content or
        "satisfactory" in reflection_content):
        return "__end__"
    
    return "actor_reflect"


def route_after_actor_reflect(state: State) -> Literal["reflector", "tools"]:
    """Route after actor reflect - if tool calls exist, go to tools, otherwise go to reflector for re-evaluation"""
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
        )

    if last_message.tool_calls:
        return "tools"
    
    return "reflector"


# Build the reflexion graph
builder = StateGraph(State, input=InputState, config_schema=Configuration)

# Add nodes
builder.add_node("actor", reflexion_actor)
builder.add_node("tools", ToolNode(TOOLS))
builder.add_node("reflector", reflexion_reflector)
builder.add_node("actor_reflect", reflexion_actor_reflect)

# Add edges
builder.add_edge("__start__", "actor")

# Add conditional edges
builder.add_conditional_edges(
    "actor",
    route_after_actor,
)

builder.add_conditional_edges(
    "reflector", 
    route_after_reflector,
)

builder.add_conditional_edges(
    "actor_reflect",
    route_after_actor_reflect,
)

# Tool routing - tools always go back to the node that called them
def route_from_tools(state: State) -> Literal["actor", "actor_reflect"]:
    """Route from tools back to the appropriate actor node"""
    # Check recent messages to see which actor node we came from
    messages = state.messages
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        if isinstance(msg, AIMessage) and msg.tool_calls:
            # Look at the context to determine which actor called tools
            # If we have a reflection in recent messages, we're in actor_reflect mode
            for j in range(i - 1, max(-1, i - 10), -1):
                if isinstance(messages[j], AIMessage) and messages[j].additional_kwargs.get("reflection"):
                    return "actor_reflect"
            return "actor"
    return "actor"  # Default fallback

builder.add_conditional_edges(
    "tools",
    route_from_tools,
)

# Compile the graph
graph = builder.compile(name="Reflexion Agent")


async def main():
    test_query = "Tin tức về giá cả cổ phiếu của công ty FPT trong tuần vừa qua"
    
    # Print the input query
    print("\n=== INPUT ===")
    print(f"User: {test_query}")
    
    # Get final result using invoke
    result = await graph.ainvoke({
        "messages": [HumanMessage(content=test_query)]
    }, config={"callbacks": [langfuse_handler]})
    
    print("\n=== FINAL OUTPUT ===")
    
    # Access the final message in the result
    if "messages" in result:
        messages = result["messages"]
        if messages:
            # Get the last non-reflection message which contains the final response
            final_message = None
            for msg in reversed(messages):
                if isinstance(msg, AIMessage) and not msg.additional_kwargs.get("reflection"):
                    final_message = msg
                    break
            
            if final_message:
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
