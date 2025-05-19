from datetime import UTC, datetime
from typing import Dict, List, Literal, cast, Optional
import json

from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode

from src.agents.configuration import Configuration
from src.agents.state import InputState, ReflexionState
from src.agents.tools import TOOLS
from src.agents.utils import load_chat_model
from src.agents.prompts import REFLEXION_FIRST_RESPONDER_PROMPT, REFLEXION_REVISION_PROMPT

# Maximum number of reflective iterations
MAX_ITERATIONS = 3

async def first_responder_agent(state: ReflexionState) -> Dict[str, List[AIMessage]]:
    """Generate the initial draft answer with self-reflection and search queries.
    
    Args:
        state (ReflexionState): The current state of the conversation.
        
    Returns:
        dict: A dictionary containing the model's response message.
    """
    configuration = Configuration(
        model="openai/gpt-4o-mini",
        system_prompt=REFLEXION_FIRST_RESPONDER_PROMPT,
    )

    model = load_chat_model(configuration.model).bind_tools([
        {
            "name": "AnswerQuestion",
            "description": "Generate an answer to the user's question with reflection",
            "parameters": {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "Your comprehensive answer to the user's question"
                    },
                    "reflection": {
                        "type": "object",
                        "properties": {
                            "missing": {
                                "type": "string",
                                "description": "What important information is missing from your answer"
                            },
                            "superfluous": {
                                "type": "string", 
                                "description": "What unnecessary information could be removed from your answer"
                            }
                        },
                        "required": ["missing", "superfluous"]
                    },
                    "search_queries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Search queries to find information to improve your answer"
                    }
                },
                "required": ["answer", "reflection", "search_queries"]
            }
        }
    ])
    
    system_message = configuration.system_prompt
    
    response = cast(
        AIMessage,
        await model.ainvoke(
            [{"role": "system", "content": system_message}, *state.messages]
        ),
    )
    
    # Extract information from the tool call
    if response.tool_calls and len(response.tool_calls) > 0:
        tool_call = response.tool_calls[0]
        if tool_call["name"] == "AnswerQuestion":
            args = tool_call["args"]
            # Store the draft answer, reflection, and search queries in the state
            state.draft_answer = args.get("answer")
            state.reflection = args.get("reflection")
            state.search_queries = args.get("search_queries")
    
    return {"messages": [response]}


async def revision_agent(state: ReflexionState) -> Dict[str, List[AIMessage]]:
    """Refine the answer based on reflection and new information.
    
    Args:
        state (ReflexionState): The current state of the conversation.
        
    Returns:
        dict: A dictionary containing the model's response message.
    """
    configuration = Configuration(
        model="openai/gpt-4o-mini",
        system_prompt=REFLEXION_REVISION_PROMPT,
    )
    
    model = load_chat_model(configuration.model).bind_tools([
        {
            "name": "ReviseAnswer",
            "description": "Revise the answer to the user's question based on reflection and new information",
            "parameters": {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "Your revised, comprehensive answer to the user's question"
                    },
                    "reflection": {
                        "type": "object",
                        "properties": {
                            "missing": {
                                "type": "string",
                                "description": "What important information is missing from your revised answer"
                            },
                            "superfluous": {
                                "type": "string", 
                                "description": "What unnecessary information could be removed from your revised answer"
                            }
                        },
                        "required": ["missing", "superfluous"]
                    },
                    "search_queries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Additional search queries to further improve your answer"
                    },
                    "references": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Citations supporting your answer"
                    }
                },
                "required": ["answer", "reflection", "search_queries", "references"]
            }
        }
    ])
    
    system_message = configuration.system_prompt
    
    response = cast(
        AIMessage,
        await model.ainvoke(
            [{"role": "system", "content": system_message}, *state.messages]
        ),
    )
    
    # Extract information from the tool call
    if response.tool_calls and len(response.tool_calls) > 0:
        tool_call = response.tool_calls[0]
        if tool_call["name"] == "ReviseAnswer":
            args = tool_call["args"]
            # Update the state with the revised answer, reflection, and search queries
            state.draft_answer = args.get("answer")
            state.reflection = args.get("reflection")
            state.search_queries = args.get("search_queries")
            state.references = args.get("references")
    
    return {"messages": [response]}


async def run_queries(state: ReflexionState) -> Dict[str, List[ToolMessage]]:
    """Execute search queries to gather additional information using available tools.
    
    Args:
        state (ReflexionState): The current state containing search queries.
        
    Returns:
        dict: A dictionary containing tool messages with search results.
    """
    tool_messages = []
    
    # Get the search queries from the state
    search_queries = state.search_queries or []
    
    # Import all necessary tools
    from src.agents.tools import search_web, retrival_vector_db, listing_symbol, history_price, time_now
    import asyncio
    import re
    
    for query in search_queries:
        # Parse the query to determine which tool to use
        tool_to_use = "search_web"  # Default tool
        
        # Simple heuristic to determine the appropriate tool based on keywords in the query
        if re.search(r'finance|news|financial|stock|market', query, re.IGNORECASE):
            tool_to_use = "retrival_vector_db"
        elif re.search(r'symbol|ticker|company|stock code', query, re.IGNORECASE):
            tool_to_use = "listing_symbol"
        elif re.search(r'price history|historical price|stock price|chart', query, re.IGNORECASE):
            # For history_price we need more parameters, so we'll use a simplified approach here
            # In a real implementation, we would need better NLP to extract parameters
            tool_to_use = "search_web"  # Fallback for now
        elif re.search(r'time|date|current time', query, re.IGNORECASE):
            tool_to_use = "time_now"
        
        # Execute the appropriate tool
        result = None
        try:
            if tool_to_use == "search_web":
                result = await search_web(query)
            elif tool_to_use == "retrival_vector_db":
                result = await retrival_vector_db(query)
            elif tool_to_use == "listing_symbol":
                result = listing_symbol()
            elif tool_to_use == "time_now":
                result = time_now()
            
            # Create a ToolMessage with the result
            if result is not None:
                tool_message = ToolMessage(
                    tool_call_id=f"{tool_to_use}_{hash(query)}",
                    content=json.dumps(result),
                    name=tool_to_use
                )
                tool_messages.append(tool_message)
                
        except Exception as e:
            # Handle any errors in tool execution
            error_message = {
                "error": str(e),
                "query": query,
                "tool": tool_to_use
            }
            error_tool_message = ToolMessage(
                tool_call_id=f"error_{hash(query)}",
                content=json.dumps(error_message),
                name="error"
            )
            tool_messages.append(error_tool_message)
    
    return {"messages": tool_messages}


def route_output(state: ReflexionState) -> Literal["revise", END]:
    """Determine the next node based on the current iteration count.
    
    Args:
        state (ReflexionState): The current state of the conversation.
        
    Returns:
        str: The name of the next node to call ("revise" or "__end__").
    """
    # Count the iterations by counting AIMessages with tool calls
    iteration_count = 0
    for message in state.messages:
        if isinstance(message, AIMessage) and message.tool_calls:
            if any(tool_call["name"] == "ReviseAnswer" for tool_call in message.tool_calls):
                iteration_count += 1
    
    # If we've reached the maximum number of iterations, end the process
    if iteration_count >= MAX_ITERATIONS:
        return END
    
    # Otherwise, continue revising
    return "revise"


# Create the builder for the Reflexion agent graph
builder = StateGraph(ReflexionState, input=InputState, config_schema=Configuration)

# Add nodes to the graph
builder.add_node("draft", first_responder_agent)
builder.add_node("tools", ToolNode(TOOLS))
builder.add_node("revise", revision_agent)

# Add edges to define the workflow
builder.add_edge("__start__", "draft")
builder.add_edge("draft", "tools")
builder.add_edge("tools", "revise")

# Add conditional edge to determine when to stop revising
builder.add_conditional_edges(
    "revise",
    route_output,
    {
        "revise": "tools",
        END: END
    }
)

# Compile the graph
graph = builder.compile(name="Reflexion Agent")
