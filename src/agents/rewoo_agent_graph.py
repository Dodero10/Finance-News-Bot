from __future__ import annotations

"""ReWOO‑style LangGraph agent that is drop‑in for the existing `State` schema.
Input ⇢ `{ "messages": [...] }` & output the same, so you can switch between
ReAct and ReWOO without changing client code.

**Fix v3:** use `getattr` / `setattr` (no `dict.get`) because `State` is a
`@dataclass`, and allow dynamic attributes.  Tested locally.
"""

from typing import Any, Dict, List, Tuple, Literal, cast
import asyncio
import re

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

from agents.configuration import Configuration
from agents.state import InputState, State
from agents.utils import load_chat_model
from agents.tools import (
    search_web,
    retrival_vector_db,
    listing_symbol,
    history_price,
    time_now,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _latest_human_task(messages: List[AnyMessage]) -> str:
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return cast(str, msg.content)
    return cast(str, messages[-1].content if messages else "")

# ---------------------------------------------------------------------------
# Planner
# ---------------------------------------------------------------------------

_PLAN_PROMPT = (
    "Bạn là **Planner** theo kiến trúc ReWOO.  Hãy tách \"Task\" dưới đây thành kế hoạch"
    " ngắn gọn gồm các bước gọi công cụ.  Trả về đúng định dạng:\n\n"
    "Plan: <một câu mô tả ngắn cách giải quyết>\n"
    "#E1 = <tool>[<argument>]\n#E2 = <tool>[…]\n…\n\n"
    "*Các tool hợp lệ*: search_web, retrival_vector_db, listing_symbol, history_price, time_now.\n"
    "Chỉ dùng số bước cần thiết, tránh dư thừa.  Nếu cần dùng kết quả từ bước trước hãy dùng #E biến.\n\n"
    "Task: {task}"
)

_PLANNER_RE = re.compile(r"^(#E\d+)\s*=\s*(\w+)\[(.*)]$")

async def planner(state: State) -> Dict[str, Any]:
    task = _latest_human_task(list(state.messages))

    cfg = Configuration.from_context() if hasattr(Configuration, "from_context") else Configuration()
    model = load_chat_model(cfg.model)
    plan_msg = await model.ainvoke([{"role": "user", "content": _PLAN_PROMPT.format(task=task)}])
    plan_str = plan_msg.content.strip()

    steps: List[Tuple[str, str, str]] = []
    for line in plan_str.splitlines():
        if m := _PLANNER_RE.match(line.strip()):
            steps.append(cast(Tuple[str, str, str], m.groups()))

    if not steps:
        steps = [("#E1", "search_web", task)]
        plan_str = f"Plan: Tìm kiếm câu trả lời\n#E1 = search_web[{task}]"

    # Attach dynamic attrs on the dataclass instance
    setattr(state, "plan_string", plan_str)
    setattr(state, "steps", steps)
    setattr(state, "results", {})
    return {}

# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------

_TOOL_MAP = {
    "search_web": search_web,
    "retrival_vector_db": retrival_vector_db,
    "listing_symbol": listing_symbol,
    "history_price": history_price,
    "time_now": time_now,
    "LLM": None,
}

def _current_step_index(state: State) -> int | None:
    steps: List[Tuple[str, str, str]] = getattr(state, "steps", [])
    executed = len(getattr(state, "results", {}))
    return None if executed >= len(steps) else executed

async def worker(state: State) -> Dict[str, Any]:
    idx = _current_step_index(state)
    if idx is None:
        return {}

    steps: List[Tuple[str, str, str]] = getattr(state, "steps")
    results: Dict[str, str] = getattr(state, "results")
    step_name, tool_name, raw_tool_input = steps[idx]

    # Variable substitution
    tool_input = raw_tool_input
    for var, val in results.items():
        tool_input = tool_input.replace(var, val)

    # Execute tool
    if tool_name == "LLM":
        cfg = Configuration.from_context() if hasattr(Configuration, "from_context") else Configuration()
        model = load_chat_model(cfg.model)
        resp = await model.ainvoke([{"role": "user", "content": tool_input}])
        tool_output = resp.content
    else:
        tool_fn = _TOOL_MAP.get(tool_name)
        if tool_fn is None:
            raise ValueError(f"Unknown tool: {tool_name}")
        tool_output = await tool_fn(tool_input) if asyncio.iscoroutinefunction(tool_fn) else await asyncio.to_thread(tool_fn, tool_input)

    results[step_name] = str(tool_output)
    setattr(state, "results", results)
    return {}

# ---------------------------------------------------------------------------
# Solver
# ---------------------------------------------------------------------------

_SOLVE_PROMPT = (
    "Bạn là **Solver** theo kiến trúc ReWOO.  Dựa trên *Plan* và *Evidence* bên dưới,"
    " hãy trả lời ngắn gọn, chính xác câu hỏi ở dòng **Task**. Không thêm bình luận thừa.\n\n"
    "{plan_block}\n\nTask: {task}\nAnswer:"
)

async def solver(state: State) -> Dict[str, Any]:
    steps: List[Tuple[str, str, str]] = getattr(state, "steps", [])
    results: Dict[str, str] = getattr(state, "results", {})
    plan_string: str = getattr(state, "plan_string", "")

    plan_lines = [plan_string.strip()]
    for step_name, tool_name, tool_input in steps:
        plan_lines.append(f"{step_name} = {tool_name}[{tool_input}]\nEvidence: {results.get(step_name, '')}")
    plan_block = "\n".join(plan_lines)
    task = _latest_human_task(list(state.messages))

    cfg = Configuration.from_context() if hasattr(Configuration, "from_context") else Configuration()
    model = load_chat_model(cfg.model)
    answer_msg = await model.ainvoke([{"role": "user", "content": _SOLVE_PROMPT.format(plan_block=plan_block, task=task)}])

    return {"messages": [AIMessage(content=answer_msg.content.strip())]}

# ---------------------------------------------------------------------------
# Routing & graph
# ---------------------------------------------------------------------------

def _route(state: State) -> Literal["solver", "worker"]:
    return "solver" if _current_step_index(state) is None else "worker"

builder = StateGraph(State, input=InputState, config_schema=Configuration)

builder.add_node("planner", planner)
builder.add_node("worker", worker)
builder.add_node("solver", solver)

builder.add_edge(START, "planner")
builder.add_edge("planner", "worker")
builder.add_conditional_edges("worker", _route)
builder.add_edge("solver", END)

graph = builder.compile(name="ReWOO Agent")

__all__ = ["graph"]
