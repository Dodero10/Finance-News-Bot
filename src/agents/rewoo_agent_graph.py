import os
import sys
import re
from datetime import UTC, datetime
from typing import Dict, List, Literal, cast, Optional, Tuple, Any

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from langfuse import Langfuse
from langfuse.callback import CallbackHandler   

from src.agents.configuration import Configuration
from src.agents.state import InputState, ReWOOState
from src.agents.tools import TOOLS
from src.agents.utils import load_chat_model
from src.agents.prompts import REWOO_PLANNER_PROMPT, REWOO_SOLVER_PROMPT

load_dotenv()

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_API_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

langfuse_handler = CallbackHandler()

# Regex to match expressions of the form Plan: ... #E... = Tool[...]
REGEX_PATTERN = r"Plan:\s*(.+?)\s*(#E\d+)\s*=\s*(\w+)\s*\[([^\]]+)\]"

# Tool mapping for execution
TOOL_MAP = {
    "search_web": "search_web",
    "retrival_vector_db": "retrival_vector_db", 
    "listing_symbol": "listing_symbol",
    "history_price": "history_price",
    "time_now": "time_now"
}

async def get_plan(state: ReWOOState) -> Dict[str, Any]:
    """
    Planner node that generates execution plan for the task.
    
    Takes the task from state and creates a multi-step plan using the planner LLM.
    Returns the steps and plan string to be stored in state.
    """
    configuration = Configuration(
        model="openai/gpt-4o-mini",
        system_prompt=REWOO_PLANNER_PROMPT,
    )

    model = load_chat_model(configuration.model)
    
    task = state.task
    if not task and state.messages:
        for msg in reversed(state.messages):
            if isinstance(msg, HumanMessage):
                task = msg.content
                break
    
    if not task:
        raise ValueError("No task found in state")

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", REWOO_PLANNER_PROMPT),
        ("user", "Task: {task}")
    ])
    
    planner = prompt_template | model
    result = await planner.ainvoke({"task": task})
    
    matches = re.findall(REGEX_PATTERN, result.content, re.DOTALL)
    
    steps = []
    for match in matches:
        plan_desc, step_name, tool, tool_input = match
        steps.append((plan_desc.strip(), step_name.strip(), tool.strip(), tool_input.strip()))
    
    return {
        "task": task,
        "steps": steps, 
        "plan_string": result.content,
        "results": {}
    }


def _get_current_task(state: ReWOOState) -> Optional[int]:
    """Helper function to determine which step to execute next."""
    if not state.results:
        return 1
    if len(state.results) == len(state.steps):
        return None 
    else:
        return len(state.results) + 1


async def tool_execution(state: ReWOOState) -> Dict[str, Any]:
    """
    Worker node that executes the tools according to the plan.
    
    Executes one step at a time, substituting variables from previous results.
    """
    _step = _get_current_task(state)
    if _step is None:
        return {"results": state.results}
    
    steps = state.steps
    if _step > len(steps):
        return {"results": state.results}
    
    _, step_name, tool, tool_input = steps[_step - 1]
    
    _results = state.results
    
    for k, v in _results.items():
        tool_input = tool_input.replace(k, str(v))
    
    try:
        if tool in TOOL_MAP:
            from src.agents.tools import (
                search_web, retrival_vector_db, listing_symbol, 
                history_price, time_now
            )
            
            if tool == "search_web":
                result = await search_web(tool_input)
            elif tool == "retrival_vector_db":
                result = await retrival_vector_db(tool_input)
            elif tool == "listing_symbol":
                result = listing_symbol()
            elif tool == "history_price":
                params = [p.strip() for p in tool_input.split(',')]
                if len(params) >= 5:
                    result = history_price(params[0], params[1], params[2], params[3], params[4])
                else:
                    result = f"Error: history_price requires 5 parameters, got {len(params)}"
            elif tool == "time_now":
                result = time_now()
            else:
                result = f"Unknown tool: {tool}"
        else:
            result = f"Tool '{tool}' not found in available tools"
    
    except Exception as e:
        result = f"Error executing {tool}: {str(e)}"
    
    updated_results = _results.copy()
    updated_results[step_name] = str(result)
    
    return {"results": updated_results}


async def solve(state: ReWOOState) -> Dict[str, Any]:
    """
    Solver node that generates the final answer based on plan and results.
    
    Takes the complete plan and all tool execution results to generate
    a comprehensive answer to the original task.
    """
    configuration = Configuration(
        model="openai/gpt-4o-mini",
        system_prompt=REWOO_SOLVER_PROMPT,
    )

    model = load_chat_model(configuration.model)
    
    plan = ""
    steps = state.steps
    results = state.results
    
    for _plan, step_name, tool, tool_input in steps:
        for k, v in results.items():
            tool_input = tool_input.replace(k, str(v))
            step_name = step_name.replace(k, str(v))
        
        plan += f"Plan: {_plan}\n{step_name} = {tool}[{tool_input}]\n"
        
        if step_name in results:
            plan += f"Result: {results[step_name]}\n\n"
    
    solver_prompt = REWOO_SOLVER_PROMPT.format(
        plan=plan,
        task=state.task or ""
    )
    
    result = await model.ainvoke([{"role": "user", "content": solver_prompt}])
    
    final_message = AIMessage(content=result.content)
    
    return {
        "result": result.content,
        "messages": [final_message]
    }


def _route(state: ReWOOState) -> Literal["tool", "solve"]:
    _step = _get_current_task(state)
    if _step is None:
        # We have executed all tasks
        return "solve"
    else:
        # We are still executing tasks, loop back to the "tool" node
        return "tool"


builder = StateGraph(ReWOOState, input=InputState, config_schema=Configuration)

builder.add_node("plan", get_plan)
builder.add_node("tool", tool_execution) 
builder.add_node("solve", solve)
builder.add_edge("__start__", "plan")
builder.add_edge("plan", "tool")
builder.add_edge("solve", "__end__")
builder.add_conditional_edges("tool", _route)
graph = builder.compile(name="ReWOO Agent")


async def main():
    """Test function for the ReWOO agent."""
    test_query = "Thông tin về diễn biến giá cổ phiếu VCB trong tuần vừa qua"
    
    print("\n=== INPUT ===")
    print(f"User: {test_query}")
    
    result = await graph.ainvoke({
        "messages": [HumanMessage(content=test_query)]
    }, config={"callbacks": [langfuse_handler]})
    
    print("\n=== PLAN ===")
    if "plan_string" in result:
        print(result["plan_string"])
    
    print("\n=== EXECUTION RESULTS ===")
    if "results" in result:
        for step_name, step_result in result["results"].items():
            print(f"{step_name}: {step_result[:200]}..." if len(str(step_result)) > 200 else f"{step_name}: {step_result}")
    
    print("\n=== FINAL OUTPUT ===")
    if "result" in result:
        print(f"AI: {result['result']}")
    elif "messages" in result and result["messages"]:
        final_message = result["messages"][-1]
        if isinstance(final_message, AIMessage):
            print(f"AI: {final_message.content}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
