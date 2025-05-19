from datetime import UTC, datetime
from typing import Dict, List, Literal, cast, Tuple, Optional
import re

from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.agents.configuration import Configuration
from src.agents.state import InputState, ReWOOState
from src.agents.tools import TOOLS
from src.agents.utils import load_chat_model
from src.agents.prompts import REWOO_PLANNER_PROMPT, REWOO_SOLVER_PROMPT


async def planner(state: ReWOOState) -> Dict:
    """Create a plan for solving the task.
    
    Args:
        state (ReWOOState): The current state of the agent.
        
    Returns:
        Dict: Updated state with plan and steps.
    """
    # Extract task from the user's message
    if not state.task and state.messages:
        for message in reversed(state.messages):
            if isinstance(message, HumanMessage):
                state.task = message.content
                break
    
    # Configure the planner
    configuration = Configuration(
        model="openai/gpt-4o-mini",
        system_prompt=REWOO_PLANNER_PROMPT,
    )
    
    # Load the model
    model = load_chat_model(configuration.model)
    
    # Generate plan
    response = cast(
        AIMessage,
        await model.ainvoke(
            [
                {"role": "system", "content": configuration.system_prompt},
                {"role": "user", "content": state.task}
            ]
        ),
    )
    
    # Parse the plan
    plan_string = response.content
    
    # Extract steps using regex
    steps = []
    pattern = r"Plan: (.*?)\n#(E\d+) = (\w+)\[(.*?)\]"
    matches = re.findall(pattern, plan_string, re.DOTALL)
    
    for match in matches:
        plan_desc, step_name, tool_name, tool_input = match
        steps.append((plan_desc.strip(), f"#{step_name}", tool_name, tool_input.strip()))
    
    # Update state with plan
    return {
        "plan_string": plan_string,
        "steps": steps,
        "messages": [AIMessage(content=f"I've created a plan to solve your question:\n\n{plan_string}")]
    }


async def executor(state: ReWOOState) -> Dict:
    """Execute the current tool in the plan.
    
    Args:
        state (ReWOOState): The current state.
        
    Returns:
        Dict: Updated state with new results.
    """
    # Find how many results we've already collected
    result_count = len(state.results) if state.results else 0
    
    # If we've completed all steps or have no steps, we're done
    if not state.steps or result_count >= len(state.steps):
        return {"messages": [AIMessage(content="All steps executed.")]}
    
    # Get the current step details
    plan_desc, step_name, tool_name, tool_input = state.steps[result_count]
    
    # Replace any references to previous results in the tool input
    results = state.results or {}
    for k, v in results.items():
        if isinstance(v, str):
            tool_input = tool_input.replace(k, v)
    
    # Find the tool to execute
    tool_to_use = None
    for tool in TOOLS:
        if tool.__name__ == tool_name:
            tool_to_use = tool
            break
    
    if not tool_to_use:
        error_message = f"Tool '{tool_name}' not found."
        return {"messages": [AIMessage(content=error_message)]}
    
    # Execute the tool
    try:
        result = await tool_to_use(tool_input)
        result_str = str(result)
        
        # Update results
        updated_results = dict(results)
        updated_results[step_name] = result_str
        
        return {
            "results": updated_results,
            "messages": [
                AIMessage(content=f"Executed step {result_count + 1}: {step_name} using {tool_name}"),
                ToolMessage(content=result_str, tool_call_id=f"step_{result_count + 1}", name=tool_name)
            ]
        }
    except Exception as e:
        error_message = f"Error executing tool '{tool_name}': {str(e)}"
        return {"messages": [AIMessage(content=error_message)]}


async def solver(state: ReWOOState) -> Dict:
    """Generate the final answer based on the plan and collected evidence.
    
    Args:
        state (ReWOOState): The current state with all tool results.
        
    Returns:
        Dict: Updated state with final result.
    """
    # Generate a formatted plan string with all steps and results
    plan = ""
    for plan_desc, step_name, tool_name, tool_input in state.steps:
        # Add formatted step to plan
        result_value = state.results.get(step_name, "No result") if state.results else "No result"
        plan += f"Plan: {plan_desc}\n{step_name} = {tool_name}[{tool_input}]\nEvidence from {tool_name}: {result_value}\n\n"
    
    # Configure the solver
    configuration = Configuration(
        model="openai/gpt-4o-mini",
        system_prompt=REWOO_SOLVER_PROMPT,
    )
    
    # Load the model
    model = load_chat_model(configuration.model)
    
    # Format the prompt for the solver
    prompt = REWOO_SOLVER_PROMPT.format(plan=plan, task=state.task or "Unknown task")
    
    # Generate solution
    response = cast(
        AIMessage,
        await model.ainvoke(
            [
                {"role": "system", "content": prompt},
            ]
        ),
    )
    
    final_answer = response.content
    
    return {
        "result": final_answer,
        "messages": [AIMessage(content=final_answer)]
    }


def router(state: ReWOOState) -> Literal["solver", "executor"]:
    """Route to the next node based on the state.
    
    Args:
        state (ReWOOState): The current state.
        
    Returns:
        str: The next node to execute.
    """
    # Find how many results we've already collected
    result_count = len(state.results) if state.results else 0
    
    # If we've completed all steps or have no steps, move to solver
    if not state.steps or result_count >= len(state.steps):
        return "solver"
    
    # Otherwise, continue executing steps
    return "executor"


# Build the graph
builder = StateGraph(ReWOOState, input=InputState)
builder.add_node("planner", planner)
builder.add_node("executor", executor)
builder.add_node("solver", solver)

# Add edges
builder.add_edge("__start__", "planner")
builder.add_edge("planner", "executor")
builder.add_edge("solver", "__end__")

# Add conditional edge
builder.add_conditional_edges(
    "executor",
    router,
    {
        "solver": "solver",
        "executor": "executor"
    }
)

# Compile the graph
graph = builder.compile(name="ReWOO Agent")
