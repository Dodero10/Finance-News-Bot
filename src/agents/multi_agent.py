import os
import sys
from datetime import UTC, datetime
from typing import Dict, List, Literal, cast, Optional
from dataclasses import dataclass, field

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from langfuse import Langfuse
from langfuse.callback import CallbackHandler   

from src.agents.configuration import Configuration
from src.agents.state import InputState, State
from src.agents.tools import search_web, retrival_vector_db, listing_symbol, history_price, time_now
from src.agents.utils import load_chat_model
from src.agents.prompts import SUPERVISOR_PROMPT, RESEARCH_AGENT_PROMPT, FINANCE_AGENT_PROMPT, SYNTHESIS_AGENT_PROMPT

# Load environment variables
load_dotenv()

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_API_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

langfuse_handler = CallbackHandler()

# Define agent names
RESEARCH_AGENT = "research_agent"
FINANCE_AGENT = "finance_agent"
SUPERVISOR = "supervisor"
SYNTHESIS_AGENT = "synthesis_agent"

# Define tools for each agent
RESEARCH_TOOLS = [search_web, retrival_vector_db]
FINANCE_TOOLS = [listing_symbol, history_price, time_now]

@dataclass
class MultiAgentState(State):
    """Extended state for multi-agent coordination."""
    current_agent: Optional[str] = None
    task_completed: bool = False
    agents_used: set = field(default_factory=set)

class RouteResponse(BaseModel):
    """Response model for supervisor routing decisions."""
    next_agent: Literal["research_agent", "finance_agent", "synthesis_agent", "FINISH"] = Field(
        description="The next agent to route to, synthesis_agent to combine results, or FINISH if complete"
    )
    reasoning: str = Field(
        description="Brief explanation of why this choice was made"
    )

async def supervisor_node(state: MultiAgentState) -> Dict[str, any]:
    """Supervisor node that routes tasks to appropriate agents."""
    
    configuration = Configuration(
        model="openai/gpt-4o-mini",
        system_prompt=SUPERVISOR_PROMPT,
    )
    
    model = load_chat_model(configuration.model)
    structured_llm = model.with_structured_output(RouteResponse)
    
    # Get agents already used from state
    agents_used = getattr(state, 'agents_used', set())
    
    # Format messages for the prompt
    messages_str = "\n".join([
        f"{getattr(msg, 'type', type(msg).__name__)}: {getattr(msg, 'content', '')}" for msg in state.messages
    ])
    
    # Add context about which agents have been used
    agent_status = f"\nĐã sử dụng agents: {', '.join(agents_used) if agents_used else 'Chưa có agent nào'}"
    
    # Enhanced supervisor prompt with synthesis strategy
    enhanced_prompt = SUPERVISOR_PROMPT + """

SYNTHESIS STRATEGY:
- "synthesis_agent": 
  * Khi đã thu thập đủ thông tin từ các chuyên gia (research_agent VÀ/HOẶC finance_agent)
  * Cần tổng hợp và kết hợp thông tin để đưa ra câu trả lời hoàn chỉnh
  * BẮT BUỘC sử dụng khi có thông tin từ nhiều agents cần được tích hợp
  * Chỉ sử dụng SAU KHI đã có đủ thông tin cần thiết

QUY TẮC MỚI:
1. Nếu đã có thông tin từ CẢ research_agent VÀ finance_agent → PHẢI chọn "synthesis_agent"
2. Nếu có thông tin từ 1 agent và đủ để trả lời → có thể chọn "synthesis_agent" hoặc "FINISH"
3. CHỈ chọn "FINISH" khi câu hỏi rất đơn giản và không cần tổng hợp

"""
    
    prompt = enhanced_prompt.format(messages=messages_str + agent_status)
    
    response = await structured_llm.ainvoke([
        {"role": "system", "content": prompt}
    ])
    
    # Add supervisor response to messages
    supervisor_message = AIMessage(
        content=f"[SUPERVISOR] Routing to {response.next_agent}. Reasoning: {response.reasoning}",
        name=SUPERVISOR
    )
    
    return {
        "messages": [supervisor_message],
        "current_agent": response.next_agent,
        "task_completed": response.next_agent == "FINISH",
        "agents_used": agents_used
    }

async def research_agent_node(state: MultiAgentState) -> Dict[str, any]:
    """Research agent that handles web search and RAG queries."""
    
    configuration = Configuration(
        model="openai/gpt-4o-mini",
        system_prompt=RESEARCH_AGENT_PROMPT,
    )
    
    model = load_chat_model(configuration.model).bind_tools(RESEARCH_TOOLS)
    
    # Get the latest user message as the task
    user_messages = [msg for msg in state.messages if isinstance(msg, HumanMessage)]
    task = getattr(user_messages[-1], 'content', 'No task specified') if user_messages else "No task specified"
    
    system_message = RESEARCH_AGENT_PROMPT.format(task=task)
    
    response = cast(
        AIMessage,
        await model.ainvoke([
            {"role": "system", "content": system_message},
            *state.messages
        ])
    )
    
    response.name = RESEARCH_AGENT
    
    if state.is_last_step and hasattr(response, 'tool_calls') and response.tool_calls:
        return {
            "messages": [
                AIMessage(
                    content="[RESEARCH AGENT] Xin lỗi, tôi không thể hoàn thành nhiệm vụ trong số bước giới hạn.",
                    name=RESEARCH_AGENT
                )
            ]
        }
    
    return {
        "messages": [response],
        "agents_used": state.agents_used | {RESEARCH_AGENT}
    }

async def finance_agent_node(state: MultiAgentState) -> Dict[str, any]:
    """Finance agent that handles stock data and financial tools."""
    
    configuration = Configuration(
        model="openai/gpt-4o-mini", 
        system_prompt=FINANCE_AGENT_PROMPT,
    )
    
    model = load_chat_model(configuration.model).bind_tools(FINANCE_TOOLS)
    
    # Get the latest user message as the task
    user_messages = [msg for msg in state.messages if isinstance(msg, HumanMessage)]
    task = getattr(user_messages[-1], 'content', 'No task specified') if user_messages else "No task specified"
    
    system_message = FINANCE_AGENT_PROMPT.format(task=task)
    
    response = cast(
        AIMessage,
        await model.ainvoke([
            {"role": "system", "content": system_message},
            *state.messages
        ])
    )
    
    response.name = FINANCE_AGENT
    
    if state.is_last_step and hasattr(response, 'tool_calls') and response.tool_calls:
        return {
            "messages": [
                AIMessage(
                    content="[FINANCE AGENT] Xin lỗi, tôi không thể hoàn thành nhiệm vụ trong số bước giới hạn.",
                    name=FINANCE_AGENT
                )
            ]
        }
    
    return {
        "messages": [response],
        "agents_used": state.agents_used | {FINANCE_AGENT}
    }

async def synthesis_agent_node(state: MultiAgentState) -> Dict[str, any]:
    """Synthesis agent that combines results from all previous agents."""
    
    configuration = Configuration(
        model="openai/gpt-4o-mini",
        system_prompt=SYNTHESIS_AGENT_PROMPT,
    )
    
    model = load_chat_model(configuration.model)
    
    # Extract original user query
    user_messages = [msg for msg in state.messages if isinstance(msg, HumanMessage)]
    original_query = getattr(user_messages[-1], 'content', 'No query specified') if user_messages else "No query specified"
    
    # Collect results from specialized agents (exclude supervisor and tool messages)
    agent_results = []
    
    for msg in state.messages:
        if isinstance(msg, AIMessage) and hasattr(msg, 'name'):
            # Include content from research and finance agents (exclude tool calls)
            if msg.name in [RESEARCH_AGENT, FINANCE_AGENT]:
                # Skip messages that are just tool calls
                if not (hasattr(msg, 'tool_calls') and msg.tool_calls):
                    content = getattr(msg, 'content', '')
                    if content.strip():  # Only include non-empty content
                        agent_results.append(f"=== {msg.name.upper()} ===\n{content}")
        elif hasattr(msg, 'name') and msg.name in ['search_web', 'retrival_vector_db', 'listing_symbol', 'history_price', 'time_now']:
            # Include tool results for context
            tool_result = getattr(msg, 'content', '')
            if tool_result and len(str(tool_result)) > 50:  # Only include substantial tool results
                agent_results.append(f"=== TOOL: {msg.name.upper()} ===\n{str(tool_result)[:500]}...")
    
    # Format the synthesis prompt
    agent_results_text = "\n\n".join(agent_results) if agent_results else "Không có thông tin từ các chuyên gia."
    
    synthesis_prompt = SYNTHESIS_AGENT_PROMPT.format(
        agent_results=agent_results_text,
        original_query=original_query
    )
    
    response = cast(
        AIMessage,
        await model.ainvoke([
            {"role": "system", "content": synthesis_prompt}
        ])
    )
    
    response.name = SYNTHESIS_AGENT
    
    return {
        "messages": [response],
        "agents_used": state.agents_used | {SYNTHESIS_AGENT}
    }

def route_after_supervisor(state: MultiAgentState) -> str:
    """Route to the next agent based on supervisor's decision."""
    
    if state.task_completed:
        return END
    elif state.current_agent == "research_agent":
        return RESEARCH_AGENT
    elif state.current_agent == "finance_agent":
        return FINANCE_AGENT
    elif state.current_agent == "synthesis_agent":
        return SYNTHESIS_AGENT
    else:
        return END

def route_after_agent(state: MultiAgentState) -> str:
    """Route back to supervisor after agent completes its task."""
    
    last_message = state.messages[-1]
    
    # If agent used tools, continue with tool execution
    if isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    
    # Otherwise, go back to supervisor for next decision
    return SUPERVISOR

def route_after_tools(state: MultiAgentState) -> str:
    """Route after tools execution."""
    
    # Determine which agent the tools belonged to based on the last AI message
    last_ai_message = None
    for msg in reversed(state.messages):
        if isinstance(msg, AIMessage) and hasattr(msg, 'name'):
            last_ai_message = msg
            break
    
    if last_ai_message and last_ai_message.name == RESEARCH_AGENT:
        return RESEARCH_AGENT
    elif last_ai_message and last_ai_message.name == FINANCE_AGENT:
        return FINANCE_AGENT
    elif last_ai_message and last_ai_message.name == SYNTHESIS_AGENT:
        return SYNTHESIS_AGENT
    
    # Fallback to supervisor
    return SUPERVISOR

# Build the graph directly (similar to react_agent_graph.py)
builder = StateGraph(MultiAgentState, input=InputState, config_schema=Configuration)

builder.add_node(SUPERVISOR, supervisor_node)
builder.add_node(RESEARCH_AGENT, research_agent_node)
builder.add_node(FINANCE_AGENT, finance_agent_node)
builder.add_node(SYNTHESIS_AGENT, synthesis_agent_node)
builder.add_node("tools", ToolNode(RESEARCH_TOOLS + FINANCE_TOOLS))

builder.add_edge("__start__", SUPERVISOR)

builder.add_conditional_edges(
    SUPERVISOR,
    route_after_supervisor,
    {
        RESEARCH_AGENT: RESEARCH_AGENT,
        FINANCE_AGENT: FINANCE_AGENT,
        SYNTHESIS_AGENT: SYNTHESIS_AGENT,
        END: END
    }
)

builder.add_conditional_edges(
    RESEARCH_AGENT,
    route_after_agent,
    {
        "tools": "tools",
        SUPERVISOR: SUPERVISOR
    }
)

builder.add_conditional_edges(
    FINANCE_AGENT,
    route_after_agent,
    {
        "tools": "tools", 
        SUPERVISOR: SUPERVISOR
    }
)

builder.add_conditional_edges(
    SYNTHESIS_AGENT,
    route_after_agent,
    {
        "tools": "tools",
        SUPERVISOR: SUPERVISOR
    }
)

builder.add_conditional_edges(
    "tools",
    route_after_tools,
    {
        RESEARCH_AGENT: RESEARCH_AGENT,
        FINANCE_AGENT: FINANCE_AGENT,
        SYNTHESIS_AGENT: SYNTHESIS_AGENT,
        SUPERVISOR: SUPERVISOR
    }
)

# Compile the builder into an executable graph
graph = builder.compile(name="Multi-Agent Finance System")

async def main():
    """Test the multi-agent system with detailed logging."""
    
    test_queries = [
        "Tin tức mới nhất về công ty cổ phần công nghệ FPT và giá trị cổ phiếu trong ngày hôm nay",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"TEST CASE {i}")
        print('='*80)
        
        # Print INPUT
        print("\n=== 📥 INPUT ===")
        print(f"User: {query}")
        
        try:
            result = await graph.ainvoke({
                "messages": [HumanMessage(content=query)]
            }, config={"callbacks": [langfuse_handler]})
            
            # Print AGENT WORKFLOW
            print("\n=== 🔄 AGENT WORKFLOW ===")
            if "messages" in result:
                workflow_steps = []
                for idx, msg in enumerate(result["messages"]):
                    if hasattr(msg, 'name') and msg.name in [SUPERVISOR, RESEARCH_AGENT, FINANCE_AGENT, SYNTHESIS_AGENT]:
                        content = getattr(msg, 'content', '')
                        content_preview = content[:150] + "..." if len(str(content)) > 150 else str(content)
                        workflow_steps.append(f"Step {idx+1} - {msg.name.upper()}: {content_preview}")
                
                for step in workflow_steps:
                    print(step)
            
            # Print TOOLS USED
            print("\n=== 🔧 TOOLS USED ===")
            if "messages" in result:
                tool_calls = []
                tool_results = []
                
                for msg in result["messages"]:
                    # Collect tool calls
                    if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            agent_name = getattr(msg, 'name', 'Unknown Agent')
                            tool_calls.append({
                                'agent': agent_name,
                                'tool': tool_call['name'],
                                'args': tool_call.get('args', {})
                            })
                    
                    # Collect tool results
                    if hasattr(msg, 'name') and msg.name in ['search_web', 'retrival_vector_db', 'listing_symbol', 'history_price', 'time_now']:
                        tool_results.append({
                            'tool': msg.name,
                            'result_preview': str(msg.content)[:300] + "..." if len(str(msg.content)) > 300 else str(msg.content)
                        })
                
                if tool_calls:
                    print("Tool Calls:")
                    for idx, tool_call in enumerate(tool_calls, 1):
                        print(f"  {idx}. Agent: {tool_call['agent']} | Tool: {tool_call['tool']}")
                        print(f"     Args: {tool_call['args']}")
                else:
                    print("No tools were called in this interaction.")
                
                if tool_results:
                    print("\nTool Results:")
                    for idx, tool_result in enumerate(tool_results, 1):
                        print(f"  {idx}. {tool_result['tool']}:")
                        print(f"     {tool_result['result_preview']}")
            
            # Print FINAL OUTPUT
            print("\n=== 📤 FINAL OUTPUT ===")
            if "messages" in result:
                final_messages = result["messages"]
                # Get the last meaningful response (not supervisor routing)
                final_response = None
                for msg in reversed(final_messages):
                    if isinstance(msg, AIMessage) and hasattr(msg, 'name'):
                        if msg.name in [RESEARCH_AGENT, FINANCE_AGENT, SYNTHESIS_AGENT] and not (hasattr(msg, 'tool_calls') and msg.tool_calls):
                            final_response = msg
                            break
                    elif isinstance(msg, AIMessage) and not hasattr(msg, 'name') and not (hasattr(msg, 'tool_calls') and msg.tool_calls):
                        final_response = msg
                        break
                
                if final_response:
                    final_content = getattr(final_response, 'content', '')
                    print(f"AI: {final_content}")
                else:
                    print("No final response found.")
                    
                # Print all messages for debugging
                print("\n=== 🔍 ALL MESSAGES (DEBUG) ===")
                for idx, msg in enumerate(final_messages):
                    # Safely get message type and name
                    msg_name = getattr(msg, 'name', None)
                    msg_type_attr = getattr(msg, 'type', None)
                    
                    if msg_name:
                        msg_type = f"[{msg_name.upper()}]"
                    elif msg_type_attr:
                        msg_type = f"[{msg_type_attr.upper()}]"
                    else:
                        msg_type = f"[{type(msg).__name__.upper()}]"
                    
                    content = getattr(msg, 'content', '')
                    content_preview = content[:100] + "..." if len(str(content)) > 100 else str(content)
                    tool_info = f" | Tools: {len(msg.tool_calls)}" if hasattr(msg, 'tool_calls') and msg.tool_calls else ""
                    print(f"  {idx+1}. {msg_type}: {content_preview}{tool_info}")
            
            # Log agent workflow for debugging
            if "messages" in result:
                agents_used = set()
                for msg in result["messages"]:
                    if hasattr(msg, 'name') and msg.name in [SUPERVISOR, RESEARCH_AGENT, FINANCE_AGENT, SYNTHESIS_AGENT]:
                        agents_used.add(msg.name)
                print(f"Agents used: {', '.join(agents_used)}")
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*80)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 