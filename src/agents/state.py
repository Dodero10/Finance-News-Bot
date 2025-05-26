"""Define the state structures for the agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence, Dict, Any, Optional, List, Tuple

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from langgraph.managed import IsLastStep
from typing_extensions import Annotated


@dataclass
class InputState:
    """Defines the input state for the agent, representing a narrower interface to the outside world.

    This class is used to define the initial state and structure of incoming data.
    """

    messages: Annotated[Sequence[AnyMessage], add_messages] = field(
        default_factory=list
    )
    """
    Messages tracking the primary execution state of the agent.

    Typically accumulates a pattern of:
    1. HumanMessage - user input
    2. AIMessage with .tool_calls - agent picking tool(s) to use to collect information
    3. ToolMessage(s) - the responses (or errors) from the executed tools
    4. AIMessage without .tool_calls - agent responding in unstructured format to the user
    5. HumanMessage - user responds with the next conversational turn

    Steps 2-5 may repeat as needed.

    The `add_messages` annotation ensures that new messages are merged with existing ones,
    updating by ID to maintain an "append-only" state unless a message with the same ID is provided.
    """


@dataclass
class State(InputState):
    """Represents the complete state of the agent, extending InputState with additional attributes.

    This class can be used to store any information needed throughout the agent's lifecycle.
    """

    is_last_step: IsLastStep = field(default=False)
    """
    Indicates whether the current step is the last one before the graph raises an error.

    This is a 'managed' variable, controlled by the state machine rather than user code.
    It is set to 'True' when the step count reaches recursion_limit - 1.
    """

    # Additional attributes can be added here as needed.
    # Common examples include:
    # retrieved_documents: List[Document] = field(default_factory=list)
    # extracted_entities: Dict[str, Any] = field(default_factory=dict)
    # api_connections: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReflexionState(State):
    """Extends the State class to include reflexion-specific attributes.
    
    This class adds fields for tracking the current draft answer, reflection on the answer,
    and search queries to improve the answer.
    """
    
    draft_answer: Optional[str] = None
    """The current draft answer that will be iteratively refined through reflection."""
    
    reflection: Optional[Dict[str, str]] = None
    """
    Reflection on the current draft answer, containing:
    - 'missing': What important information is missing from the answer
    - 'superfluous': What unnecessary information could be removed
    """
    
    search_queries: Optional[List[str]] = None
    """Additional search queries generated based on reflection to improve the answer."""
    
    references: Optional[List[str]] = None
    """Citations and references used to support the answer."""


@dataclass
class ReWOOState(State):
    """Extends the State class to include ReWOO-specific attributes.
    
    This class adds fields for tracking execution plans and results from tool calls.
    """
    
    task: Optional[str] = None
    """The original task or question to be answered."""
    
    plan_string: Optional[str] = None
    """The generated plan string containing all steps to be executed."""
    
    steps: List[Tuple[str, str, str, str]] = field(default_factory=list)
    """
    List of execution steps defined as tuples with these elements:
    - Plan description (what needs to be done)
    - Step name (identifier for this step, can be referenced in future steps)
    - Tool name (which tool to use)
    - Tool input (parameters for the tool)
    """
    
    results: Dict[str, str] = field(default_factory=dict)
    """
    Results from executed tool calls, where:
    - Key: Step name (identifier)
    - Value: Result content from tool execution
    """
    
    result: Optional[str] = None
    """The final answer after executing the plan and solving the task."""

