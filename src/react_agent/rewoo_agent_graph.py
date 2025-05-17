from datetime import UTC, datetime
from typing import Dict, List, TypedDict, Optional, Literal, Tuple, cast, Any, Union

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode

from react_agent.configuration import Configuration
from react_agent.state import InputState, State
from react_agent.tools import TOOLS
from react_agent.utils import load_chat_model
from dotenv import load_dotenv
from langfuse.callback import CallbackHandler
import os

load_dotenv()

langfuse_handler = CallbackHandler(
    secret_key=os.getenv("LANGFUSE_API_KEY"),
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    host=os.getenv("LANGFUSE_HOST"),
)

class ReWOO(TypedDict):
    """The state object for the ReWOO agent."""
    task: str
    steps: Optional[List[Tuple[str, str, str, str]]]
    results: Optional[Dict[str, str]]
    result: Optional[str]

async def get_plan(state: ReWOO) -> Dict:
    """Generate a plan for solving the task.

    Args:
        state (ReWOO): The current state of the conversation.

    Returns:
        dict: A dictionary containing the plan with steps to execute.
    """
    configuration = Configuration.from_context()
    
    plan_prompt = """Solve the following task or problem as efficiently as possible. 
    Create a plan with step-by-step approach to solve it correctly. 
    For each step, specify what tool to use. You have access to these tools:

    1. LLM - Use the large language model when you need to reason, analyze, or generate content based on accumulated information.
    2. websearch - Use web search when you need real-time or specific information that might not be in your knowledge base.

    For each step, you create will have this format:
    Plan: [explanation of what to do in this step]
    [variable_name] = [tool][tool_input]

    Use descriptive variable names starting with # (like #E1, #E2) to store results.
    You can reference previous step results in your tool inputs.

    Task: {task}
    """
    
    llm = load_chat_model(configuration.llm)
    task = state["task"]
    
    prompt = plan_prompt.format(task=task)
    result = await llm.ainvoke(prompt)
    
    # Parse the plan from the LLM response
    plan_string = result.content
    
    # Extract steps from the plan
    steps = []
    for line in plan_string.split("\n"):
        if "=" in line and ("[" in line and "]" in line):
            parts = line.split("=")
            step_name = parts[0].strip()
            tool_parts = parts[1].strip()
            tool = tool_parts.split("[")[0].strip()
            tool_input = tool_parts[tool_parts.find("[")+1:tool_parts.rfind("]")]
            
            # Try to find the corresponding "Plan:" line
            plan_line = ""
            for prev_line in plan_string.split("\n"):
                if prev_line.strip().startswith("Plan:") and plan_string.find(prev_line) < plan_string.find(line):
                    plan_line = prev_line.replace("Plan:", "").strip()
                    break
            
            steps.append((plan_line, step_name, tool, tool_input))
    
    return {"steps": steps, "plan_string": plan_string}

def _get_current_task(state: ReWOO) -> Optional[Tuple[str, str, str, str]]:
    """Get the next step that needs to be executed.

    Args:
        state (ReWOO): The current state

    Returns:
        Optional[Tuple]: The next step to execute, or None if all steps are done
    """
    steps = state.get("steps", [])
    if not steps:
        return None
    
    results = state.get("results", {})
    
    # Find the first step whose results are not in the results dictionary
    for step in steps:
        _, step_name, _, _ = step
        if step_name not in results:
            return step
    
    return None

async def tool_execution(state: ReWOO) -> Dict:
    """Execute the next tool in the plan.

    Args:
        state (ReWOO): The current state of the conversation.

    Returns:
        dict: A dictionary containing the updated results.
    """
    configuration = Configuration.from_context()
    llm = load_chat_model(configuration.llm)
    
    _step = _get_current_task(state)
    if _step is None:
        return {"results": state.get("results", {})}
    
    _plan, step_name, tool, tool_input = _step
    _results = state.get("results", {}) if "results" in state else {}
    
    # Replace placeholders with actual values from results
    for k, v in _results.items():
        tool_input = tool_input.replace(k, v)
    
    # Execute the tool
    if tool == "websearch":
        from langchain_community.utilities import TavilySearchAPIWrapper
        search = TavilySearchAPIWrapper()
        try:
            result = search.run(tool_input)
        except Exception as e:
            result = str(e)
    elif tool == "LLM":
        result = await llm.ainvoke(tool_input)
        result = str(result)
    else:
        raise ValueError(f"Unknown tool: {tool}")
    
    # Update results
    _results[step_name] = str(result)
    return {"results": _results}

async def solve(state: ReWOO) -> Dict:
    """Solve the task using the evidence collected.

    Args:
        state (ReWOO): The current state of the conversation.

    Returns:
        dict: A dictionary containing the final result.
    """
    configuration = Configuration.from_context()
    llm = load_chat_model(configuration.llm)
    
    solve_prompt = """Solve the following task or problem. To solve the problem, we have made step-by-step Plan and \
retrieved corresponding Evidence to each Plan. Use them with caution since long evidence might \
contain irrelevant information.

{plan}

Now solve the question or task according to provided Evidence above. Respond with the answer
directly with no extra words.

Task: {task}
Response:"""
    
    plan = ""
    for _plan, step_name, tool, tool_input in state["steps"]:
        _results = (state["results"] or {}) if "results" in state else {}
        for k, v in _results.items():
            tool_input = tool_input.replace(k, v)
            if step_name in _results:
                plan += f"Plan: {_plan}\n{step_name} = {tool}[{tool_input}]\nEvidence: {_results[step_name]}\n\n"
    
    prompt = solve_prompt.format(plan=plan, task=state["task"])
    result = await llm.ainvoke(prompt)
    
    return {"result": result.content}

def _route(state: ReWOO) -> Literal["solve", "tool"]:
    """Route to the next node based on the current state.

    Args:
        state (ReWOO): The current state

    Returns:
        str: The name of the next node to call
    """
    _step = _get_current_task(state)
    if _step is None:
        # We have executed all tasks
        return "solve"
    else:
        # We are still executing tasks, loop back to the "tool" node
        return "tool"

# Build the graph
graph = StateGraph(ReWOO)
graph.add_node("plan", get_plan)
graph.add_node("tool", tool_execution)
graph.add_node("solve", solve)

# Define the edges
graph.add_edge(START, "plan")
graph.add_edge("plan", "tool")
graph.add_conditional_edges("tool", _route)
graph.add_edge("solve", END)

# Compile the graph
def create_graph():
    """Create the ReWOO agent graph."""
    return graph.compile()
