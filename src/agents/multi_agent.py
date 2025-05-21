from typing import Any, Dict, List, Literal, Tuple, Union, cast
from datetime import UTC, datetime

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from src.agents.configuration import Configuration
from src.agents.state import InputState, State
from src.agents.tools import TOOLS, retrival_vector_db, search_web
from src.agents.utils import load_chat_model

# Define specialized tool groups
SEARCH_TOOLS = [search_web, retrival_vector_db]
OTHER_TOOLS = [tool for tool in TOOLS if tool not in SEARCH_TOOLS]

# Define prompts for each agent
SUPERVISOR_PROMPT = """You are the supervisor of a multi-agent system designed to answer finance-related questions.
You coordinate two specialized agents:
1. A Search Agent that can search the web and query a vector database for financial news
2. A Tools Agent that can access financial data and tools

Your job is to:
1. Understand the user's question and determine which agent(s) to call
2. Delegate tasks to the appropriate agent(s)
3. Synthesize the information from both agents into a complete, accurate response
4. Provide the final answer to the user's question

Be concise in your interactions with the specialized agents, giving them clear instructions.
When providing the final answer to the user, be informative, accurate, and helpful.
"""

SEARCH_AGENT_PROMPT = """You are a Search Agent specialized in finding information from the web and a finance news vector database.
Your role is to find relevant information about finance topics when requested by the supervisor.

You have access to two tools:
1. search_web - Find general information from the web
2. retrival_vector_db - Search specifically in a financial news vector database

Provide factual, reliable information from your searches without opinions or speculation.
Focus on gathering the most relevant information to answer the supervisor's request.
"""

TOOLS_AGENT_PROMPT = """You are a Tools Agent specialized in using financial data tools.
Your role is to gather and analyze financial data when requested by the supervisor.

You have access to these tools:
- listing_symbol - Get listing symbols with company names
- history_price - Retrieve historical price data for stocks
- time_now - Get the current time in Vietnam

Provide factual data and analysis based on the tools available.
Focus on gathering the precise information requested by the supervisor.
"""

# Helper functions to extend the State with additional information
def add_supervisor_messages(state: State, supervisor_messages: List[BaseMessage]) -> State:
    """Add supervisor messages to the state"""
    if "supervisor_messages" not in state.metadata:
        state.metadata["supervisor_messages"] = []
    state.metadata["supervisor_messages"].extend(supervisor_messages)
    return state

def add_search_agent_messages(state: State, messages: List[BaseMessage]) -> State:
    """Add search agent messages to the state"""
    if "search_agent_messages" not in state.metadata:
        state.metadata["search_agent_messages"] = []
    state.metadata["search_agent_messages"].extend(messages)
    return state

def add_tools_agent_messages(state: State, messages: List[BaseMessage]) -> State:
    """Add tools agent messages to the state"""
    if "tools_agent_messages" not in state.metadata:
        state.metadata["tools_agent_messages"] = []
    state.metadata["tools_agent_messages"].extend(messages)
    return state

def get_messages(state: State, key: str) -> List[BaseMessage]:
    """Get messages from state metadata by key"""
    return state.metadata.get(key, [])

async def supervisor(state: State) -> Dict[str, Union[List[AIMessage], str]]:
    """The supervisor agent that coordinates the specialized agents."""
    configuration = Configuration(
        model="openai/gpt-4o-mini",
        system_prompt=SUPERVISOR_PROMPT,
    )
    model = load_chat_model(configuration.model)
    
    # Use all messages in the conversation for context
    messages_for_model = [SystemMessage(content=SUPERVISOR_PROMPT)]
    
    # Add user messages from the main conversation
    for message in state.messages:
        if isinstance(message, HumanMessage):
            messages_for_model.append(message)
    
    # Add any responses from specialized agents
    supervisor_messages = get_messages(state, "supervisor_messages")
    for message in supervisor_messages:
        messages_for_model.append(message)
    
    # Check if we have responses from specialized agents
    search_agent_messages = get_messages(state, "search_agent_messages")
    tools_agent_messages = get_messages(state, "tools_agent_messages")
    
    has_search_response = any(isinstance(msg, ToolMessage) for msg in search_agent_messages)
    has_tools_response = any(isinstance(msg, ToolMessage) for msg in tools_agent_messages)
    
    # If both agents have responded or there are no agent responses yet, determine which to call
    if (not supervisor_messages) or (has_search_response and has_tools_response):
        # If this is first call or both agents have provided responses
        response = await model.ainvoke(messages_for_model)
        
        # Check if the supervisor wants to call agents or provide final answer
        content = response.content.lower() if response.content else ""
        
        if "search agent" in content and not has_search_response:
            # Update state with supervisor's message and indicate next agent
            state = add_supervisor_messages(state, [response])
            return {"messages": state.messages, "next": "search_agent"}
        elif "tools agent" in content and not has_tools_response:
            # Update state with supervisor's message and indicate next agent
            state = add_supervisor_messages(state, [response])
            return {"messages": state.messages, "next": "tools_agent"}
        else:
            # Provide final answer
            return {
                "messages": [*state.messages, AIMessage(content=response.content)],
                "next": "__end__"
            }
    
    # If only one agent has responded, call the other agent
    if has_search_response and not has_tools_response:
        return {"messages": state.messages, "next": "tools_agent"}
    elif has_tools_response and not has_search_response:
        return {"messages": state.messages, "next": "search_agent"}
    
    # Default case - should not reach here
    return {"messages": state.messages, "next": "supervisor"}

async def search_agent(state: State) -> Dict[str, List[BaseMessage]]:
    """Agent that uses web search and RAG tools."""
    configuration = Configuration(
        model="openai/gpt-4o-mini",
        system_prompt=SEARCH_AGENT_PROMPT,
    )
    
    model = load_chat_model(configuration.model).bind_tools(SEARCH_TOOLS)
    
    # Build messages for this agent
    messages = [SystemMessage(content=SEARCH_AGENT_PROMPT)]
    
    # Add the latest supervisor message as context for this agent
    supervisor_messages = [msg for msg in get_messages(state, "supervisor_messages") if isinstance(msg, AIMessage)]
    if supervisor_messages:
        latest_supervisor_message = supervisor_messages[-1]
        messages.append(HumanMessage(content=latest_supervisor_message.content))
    
    # Get the initial user query as fallback
    if not supervisor_messages and state.messages:
        user_messages = [msg for msg in state.messages if isinstance(msg, HumanMessage)]
        if user_messages:
            messages.append(HumanMessage(content=user_messages[-1].content))
    
    response = await model.ainvoke(messages)
    
    # Update state with search agent's response
    state = add_search_agent_messages(state, [response])
    
    return {"messages": state.messages}

async def tools_agent(state: State) -> Dict[str, List[BaseMessage]]:
    """Agent that uses financial data tools."""
    configuration = Configuration(
        model="openai/gpt-4o-mini",
        system_prompt=TOOLS_AGENT_PROMPT,
    )
    
    model = load_chat_model(configuration.model).bind_tools(OTHER_TOOLS)
    
    # Build messages for this agent
    messages = [SystemMessage(content=TOOLS_AGENT_PROMPT)]
    
    # Add the latest supervisor message as context for this agent
    supervisor_messages = [msg for msg in get_messages(state, "supervisor_messages") if isinstance(msg, AIMessage)]
    if supervisor_messages:
        latest_supervisor_message = supervisor_messages[-1]
        messages.append(HumanMessage(content=latest_supervisor_message.content))
    
    # Get the initial user query as fallback
    if not supervisor_messages and state.messages:
        user_messages = [msg for msg in state.messages if isinstance(msg, HumanMessage)]
        if user_messages:
            messages.append(HumanMessage(content=user_messages[-1].content))
    
    response = await model.ainvoke(messages)
    
    # Update state with tools agent's response
    state = add_tools_agent_messages(state, [response])
    
    return {"messages": state.messages}

def route_supervisor_output(state: State) -> str:
    """Determine the next node based on the supervisor's decision."""
    return state.metadata.get("next", "supervisor")

# Build the multi-agent graph
builder = StateGraph(State, input=InputState, config_schema=Configuration)
builder.add_node("supervisor", supervisor)
builder.add_node("search_agent", search_agent)
builder.add_node("tools_agent", tools_agent)

# Define the edges
builder.add_edge("__start__", "supervisor")
builder.add_edge("search_agent", "supervisor")
builder.add_edge("tools_agent", "supervisor")
builder.add_conditional_edges(
    "supervisor",
    route_supervisor_output
)

# Compile the graph
multi_agent_graph = builder.compile(name="Finance News Multi-Agent")

# Function to run the multi-agent system
async def run_multi_agent(query: str) -> List[BaseMessage]:
    """Run the multi-agent system with a user query."""
    input_state = InputState(messages=[HumanMessage(content=query)])
    result = await multi_agent_graph.ainvoke(input_state)
    return result.messages
