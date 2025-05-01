"""
Tool Agent with RAG

This module implements a LangGraph-based tool agent that uses the Finance News RAG system
to provide financial information to users.
"""

import os
from typing import Dict, List, Any, TypedDict, Optional, Annotated, Tuple, Callable, Literal, Union
from enum import Enum
import json

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import GoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langchain_core.pydantic_v1 import BaseModel, Field
from finance_rag import FinanceNewsRAG

# Load environment variables
load_dotenv()

# Type definitions
class AgentState(TypedDict):
    """State for the tool agent workflow."""
    messages: List[Union[HumanMessage, AIMessage, ToolMessage, SystemMessage]]
    next: Optional[str]

# Define available tools
@tool
def search_financial_news(query: str) -> str:
    """
    Search for financial news information using the query provided.
    
    Args:
        query: The search query related to financial news or market information
        
    Returns:
        Relevant financial information based on the query
    """
    # This will be connected to our RAG system
    return "Placeholder for financial news search results"

class FinanceToolAgent:
    """
    Tool agent for financial information using LangGraph.
    
    This agent uses a RAG system to provide accurate and up-to-date
    financial information to users.
    """
    
    def __init__(
        self,
        google_api_key: Optional[str] = None,
        llm_model: str = "gemini-1.5-pro-latest",
        data_path: str = "data",
        rag_system: Optional[FinanceNewsRAG] = None
    ):
        """
        Initialize the Finance Tool Agent.
        
        Args:
            google_api_key: Google API key for Gemini
            llm_model: Model name for the LLM
            data_path: Path to the data directory
            rag_system: Pre-initialized RAG system (optional)
        """
        # Set API key from environment if not provided
        self.api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY in .env file or pass it as a parameter.")
        
        # Initialize LLM
        self.llm_model = llm_model
        self.llm = GoogleGenerativeAI(model=llm_model, google_api_key=self.api_key)
        
        # Initialize or use provided RAG system
        if rag_system is not None:
            self.rag = rag_system
        else:
            self.rag = FinanceNewsRAG(data_path=data_path, google_api_key=self.api_key)
            # Check if vector store is already initialized
            if not self.rag.vector_store:
                print("Vector store not initialized in RAG system. You need to call load_data() before using the agent.")
        
        # Available tools
        self.tools = [
            search_financial_news
        ]
        
        # Create state graph
        self.workflow = self._create_graph()
        
        # System message
        self.system_message = SystemMessage(
            content=(
                "You are a financial advisor assistant that helps users with information "
                "about financial markets, companies, and news. You have access to tools "
                "that can provide financial information. Use the tools whenever appropriate "
                "to give accurate and helpful responses."
            )
        )
    
    def _create_graph(self) -> StateGraph:
        """
        Create the LangGraph workflow for the tool agent.
        
        Returns:
            StateGraph: The configured workflow graph
        """
        # Create a new graph
        builder = StateGraph(AgentState)
        
        # Add nodes
        builder.add_node("agent", self.agent_node)
        builder.add_node("action", self.action_node)
        
        # Define edges
        builder.add_conditional_edges(
            "agent",
            lambda state: state["next"] if state.get("next") else END,
            {
                "action": "action",
                END: END
            }
        )
        builder.add_edge("action", "agent")
        
        # Set entry point
        builder.set_entry_point("agent")
        
        # Compile the graph
        return builder.compile()
    
    def agent_node(self, state: AgentState) -> AgentState:
        """
        Process user messages and decide on next actions.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with next action
        """
        # Get the system message and conversation history
        messages = [self.system_message] + state["messages"]
        
        # Create the prompt with tool descriptions
        tool_descriptions = "\n".join([
            f"{tool.name}: {tool.description}" for tool in self.tools
        ])
        
        tool_names = [tool.name for tool in self.tools]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a helpful financial assistant with access to the following tools:
            
{tool_descriptions}

To use a tool, respond with:
<tool>
    <tool_name>TOOL_NAME</tool_name>
    <parameters>
        <param_name>PARAM_VALUE</param_name>
        ...
    </parameters>
</tool>

Only respond with a tool call when you need to use a tool. Otherwise, respond directly to the user.
If you don't have enough information to use a tool, ask the user for more details.
"""),
            *messages
        ])
        
        # Generate a response
        response = self.llm.invoke(prompt)
        response_text = response.content
        
        # Check if the response contains a tool call
        # Simple parsing for demonstration, a more robust parser should be used in production
        if "<tool>" in response_text and "</tool>" in response_text:
            # Extract tool call
            tool_start = response_text.find("<tool>")
            tool_end = response_text.find("</tool>") + len("</tool>")
            tool_call = response_text[tool_start:tool_end]
            
            # Extract tool name
            tool_name_start = tool_call.find("<tool_name>") + len("<tool_name>")
            tool_name_end = tool_call.find("</tool_name>")
            tool_name = tool_call[tool_name_start:tool_name_end].strip()
            
            # Get parameters
            params_start = tool_call.find("<parameters>") + len("<parameters>")
            params_end = tool_call.find("</parameters>")
            params_text = tool_call[params_start:params_end].strip()
            
            # Parse parameters
            params = {}
            param_lines = params_text.strip().split("\n")
            for line in param_lines:
                line = line.strip()
                if "<" in line and ">" in line:
                    param_name_start = line.find("<") + 1
                    param_name_end = line.find(">")
                    param_value_start = line.find(">") + 1
                    param_value_end = line.rfind("<")
                    
                    param_name = line[param_name_start:param_name_end].strip()
                    param_value = line[param_value_start:param_value_end].strip()
                    
                    params[param_name] = param_value
            
            # Add the AI message to the state
            ai_message = AIMessage(content=response_text)
            
            # Update next state to action with tool info
            return {
                "messages": state["messages"] + [ai_message],
                "next": "action",
                "action": {
                    "tool": tool_name,
                    "parameters": params
                }
            }
        else:
            # No tool call, just a regular response
            ai_message = AIMessage(content=response_text)
            return {
                "messages": state["messages"] + [ai_message],
                "next": None  # End the conversation
            }
    
    def action_node(self, state: AgentState) -> AgentState:
        """
        Execute tools based on agent decisions.
        
        Args:
            state: Current agent state with action information
            
        Returns:
            Updated state with tool results
        """
        # Get the action from the state
        action = state.get("action", {})
        tool_name = action.get("tool", "")
        parameters = action.get("parameters", {})
        
        # Find the right tool
        tool_to_use = None
        for tool in self.tools:
            if tool.name == tool_name:
                tool_to_use = tool
                break
        
        # Execute the tool
        if tool_to_use:
            if tool_name == "search_financial_news":
                # Use the RAG system for financial news search
                query = parameters.get("query", "")
                rag_result = self.rag.query(query)
                result = rag_result.get("answer", "No information found")
            else:
                # Use the standard tool implementation
                result = tool_to_use(**parameters)
        else:
            result = f"Error: Tool '{tool_name}' not found"
        
        # Create a tool message with the result
        tool_message = ToolMessage(
            content=result,
            tool_call_id="1",  # Placeholder
            name=tool_name
        )
        
        # Update the state
        return {
            "messages": state["messages"] + [tool_message],
            "next": "agent"  # Continue the conversation
        }
    
    def invoke(self, message: str) -> List[Dict[str, Any]]:
        """
        Process a user message through the agent workflow.
        
        Args:
            message: User message
            
        Returns:
            List of messages in the conversation history
        """
        # Initialize state with user message
        state = {
            "messages": [HumanMessage(content=message)],
            "next": None
        }
        
        # Run the workflow
        final_state = self.workflow.invoke(state)
        
        # Return the messages
        return final_state["messages"] 