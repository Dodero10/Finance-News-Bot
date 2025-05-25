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

# Define tools for each agent
RESEARCH_TOOLS = [search_web, retrival_vector_db]
FINANCE_TOOLS = [listing_symbol, history_price, time_now]

@dataclass
class MultiAgentState(State):
    """Extended state for multi-agent coordination."""
    current_agent: Optional[str] = None
    task_completed: bool = False

class RouteResponse(BaseModel):
    """Response model for supervisor routing decisions."""
    next_agent: Literal["research_agent", "finance_agent", "FINISH"] = Field(
        description="The next agent to route to or FINISH if complete"
    )
    reasoning: str = Field(
        description="Brief explanation of why this choice was made"
    )

# Supervisor prompt
SUPERVISOR_PROMPT = """Bạn là một supervisor quản lý hai agent chuyên biệt để trả lời các câu hỏi về tài chính và tin tức:

RESEARCH AGENT:
- Chuyên về tìm kiếm thông tin web và tin tức tài chính từ cơ sở dữ liệu vector
- Có thể tìm kiếm tin tức mới nhất, thông tin công ty, sự kiện thị trường
- Sử dụng tools: search_web, retrival_vector_db

FINANCE AGENT:  
- Chuyên về dữ liệu tài chính cụ thể của cổ phiếu Việt Nam
- Có thể lấy danh sách mã cổ phiếu, lịch sử giá chính xác từ sàn giao dịch, thời gian hiện tại
- Sử dụng tools: listing_symbol, history_price, time_now

QUYỀN ƯU TIÊN ROUTING:
1. Nếu câu hỏi có từ khóa về "giá cổ phiếu", "giá trị cổ phiếu", "lịch sử giá", "dữ liệu tài chính" → BẮT BUỘC phải sử dụng FINANCE AGENT
2. Nếu câu hỏi có từ khóa về "tin tức", "thông tin công ty", "sự kiện" → sử dụng RESEARCH AGENT trước
3. Nếu câu hỏi yêu cầu CẢ HAI loại thông tin → phải sử dụng CẢ HAI agent theo thứ tự: RESEARCH AGENT trước, sau đó FINANCE AGENT

STRATEGY SELECTION:
- "research_agent": Khi cần tin tức, thông tin tổng quát VÀ chưa có agent nào chạy
- "finance_agent": Khi cần dữ liệu tài chính cụ thể HOẶC đã có tin tức từ research_agent nhưng chưa có dữ liệu giá chính xác
- "FINISH": CHỈ KHI đã có đầy đủ cả tin tức VÀ dữ liệu tài chính (nếu câu hỏi yêu cầu cả hai)

QUAN TRỌNG: 
- Nếu người dùng hỏi về "giá cổ phiếu hôm nay" hoặc "giá trị cổ phiếu trong ngày" → BẮT BUỘC phải có dữ liệu từ FINANCE AGENT
- Không được FINISH nếu chưa có dữ liệu tài chính chính xác khi người dùng yêu cầu

Lịch sử cuộc hội thoại:
{messages}

Hãy quyết định bước tiếp theo và giải thích lý do."""

# Research agent prompt
RESEARCH_AGENT_PROMPT = """Bạn là Research Agent chuyên về tìm kiếm và phân tích thông tin tài chính.

KHẢ NĂNG CỦA BẠN:
- Tìm kiếm thông tin web tổng quát về tài chính, kinh tế
- Truy xuất tin tức tài chính từ cơ sở dữ liệu vector chuyên biệt
- Phân tích và tổng hợp thông tin từ nhiều nguồn

TOOLS AVAILABLE:
- search_web: Tìm kiếm thông tin web tổng quát
- retrival_vector_db: Tìm kiếm tin tức tài chính từ database vector

HƯỚNG DẪN:
1. Bắt buộc phải sử dụng tools retrival_vector_db trước để tìm thông tin, rồi khi có thông tin liên quan hay không cũng phải sử dụng tools search_web.
2. Sử dụng retrival_vector_db TRƯỚC cho các câu hỏi về tin tức tài chính Việt Nam
3. Sử dụng search_web cho thông tin tổng quát hoặc khi cần thông tin mới nhất
4. Tổng hợp thông tin một cách rõ ràng và có cấu trúc
5. Trích dẫn nguồn thông tin khi có thể
6. Trả lời bằng tiếng Việt
7. Chỉ hỗ trợ các nhiệm vụ nghiên cứu, KHÔNG làm toán

Nhiệm vụ hiện tại: {task}"""

# Finance agent prompt  
FINANCE_AGENT_PROMPT = """Bạn là Finance Agent chuyên về dữ liệu cổ phiếu và thị trường tài chính Việt Nam.

KHẢ NĂNG CỦA BẠN:
- Lấy danh sách mã cổ phiếu và thông tin công ty
- Truy xuất lịch sử giá cổ phiếu chính xác từ sàn giao dịch
- Cung cấp thông tin thời gian hiện tại
- Phân tích dữ liệu giá và xu hướng

TOOLS AVAILABLE:
- listing_symbol: Lấy danh sách tất cả mã cổ phiếu
- history_price: Lấy lịch sử giá cổ phiếu (cần symbol, source, start_date, end_date, interval)
- time_now: Lấy thời gian hiện tại ở Việt Nam

HƯỚNG DẪN THỰC HIỆN:
1. LUÔN sử dụng time_now để lấy thời gian hiện tại trước
2. Sử dụng listing_symbol để tìm mã cổ phiếu chính xác (ví dụ: FPT)
3. Sử dụng history_price để lấy dữ liệu giá mới nhất:
   - source: 'VCI' (khuyến nghị cao nhất)
   - interval: '1D' cho giá ngày
   - start_date và end_date: sử dụng ngày hiện tại hoặc vài ngày gần đây
   - Định dạng ngày: YYYY-MM-DD
4. Phân tích dữ liệu và đưa ra thông tin chi tiết về:
   - Giá hiện tại
   - Thay đổi so với phiên trước
   - Khối lượng giao dịch
   - Xu hướng giá
5. Trả lời bằng tiếng Việt với số liệu cụ thể và chính xác

QUAN TRỌNG:
- BẮT BUỘC phải lấy dữ liệu giá thực tế từ tools, KHÔNG được đoán hoặc sử dụng thông tin từ agent khác
- Nếu không tìm thấy mã cổ phiếu, hãy thử các biến thể (FPT, FPTS, etc.)

Nhiệm vụ hiện tại: {task}"""

async def supervisor_node(state: MultiAgentState) -> Dict[str, any]:
    """Supervisor node that routes tasks to appropriate agents."""
    
    configuration = Configuration(
        model="openai/gpt-4o-mini",
        system_prompt=SUPERVISOR_PROMPT,
    )
    
    model = load_chat_model(configuration.model)
    structured_llm = model.with_structured_output(RouteResponse)
    
    # Format messages for the prompt
    messages_str = "\n".join([
        f"{getattr(msg, 'type', type(msg).__name__)}: {getattr(msg, 'content', '')}" for msg in state.messages
    ])
    
    prompt = SUPERVISOR_PROMPT.format(messages=messages_str)
    
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
        "task_completed": response.next_agent == "FINISH"
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
    
    return {"messages": [response]}

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
    
    return {"messages": [response]}

def route_after_supervisor(state: MultiAgentState) -> str:
    """Route to the next agent based on supervisor's decision."""
    
    if state.task_completed:
        return END
    elif state.current_agent == "research_agent":
        return RESEARCH_AGENT
    elif state.current_agent == "finance_agent":
        return FINANCE_AGENT
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
    
    # Fallback to supervisor
    return SUPERVISOR

# Build the graph directly (similar to react_agent_graph.py)
builder = StateGraph(MultiAgentState, input=InputState, config_schema=Configuration)

builder.add_node(SUPERVISOR, supervisor_node)
builder.add_node(RESEARCH_AGENT, research_agent_node)
builder.add_node(FINANCE_AGENT, finance_agent_node)
builder.add_node("tools", ToolNode(RESEARCH_TOOLS + FINANCE_TOOLS))

builder.add_edge("__start__", SUPERVISOR)

builder.add_conditional_edges(
    SUPERVISOR,
    route_after_supervisor,
    {
        RESEARCH_AGENT: RESEARCH_AGENT,
        FINANCE_AGENT: FINANCE_AGENT,
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
    "tools",
    route_after_tools,
    {
        RESEARCH_AGENT: RESEARCH_AGENT,
        FINANCE_AGENT: FINANCE_AGENT,
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
                    if hasattr(msg, 'name') and msg.name in [SUPERVISOR, RESEARCH_AGENT, FINANCE_AGENT]:
                        content = getattr(msg, 'content', '')
                        content_preview = content[:150] + "..." if len(str(content)) > 150 else str(content)
                        workflow_steps.append(f"Step {idx+1} - {msg.name.upper()}: {content_preview}")
                
                for step in workflow_steps:
                    print(step)
            
            # Print TOOLS USED
            print("\n=== 🛠️ TOOLS USED ===")
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
                        if msg.name in [RESEARCH_AGENT, FINANCE_AGENT] and not (hasattr(msg, 'tool_calls') and msg.tool_calls):
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
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*80)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 