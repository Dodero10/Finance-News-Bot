import os
import sys
import csv
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add project root to sys.path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, project_root)

from langfuse.callback import CallbackHandler
from src.agents.multi_agent import graph as multi_agent_graph
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

os.environ["LANGFUSE_PUBLIC_KEY"] = os.getenv("LANGFUSE_PUBLIC_KEY")
os.environ["LANGFUSE_SECRET_KEY"] = os.getenv("LANGFUSE_SECRET_KEY")
os.environ["LANGFUSE_HOST"] = os.getenv("LANGFUSE_HOST", "http://localhost:3000")
tag = ['multi_agent']

langfuse_handler = CallbackHandler()

INPUT_CSV = os.path.join(project_root, "evaluation", "data_eval", "synthetic_data", "synthetic_news.csv")
OUTPUT_CSV = os.path.join(project_root, "evaluation", "data_eval", "results", "multi_agent_eval_results.csv")

# Agent names from multi_agent.py
RESEARCH_AGENT = "research_agent"
FINANCE_AGENT = "finance_agent"
SUPERVISOR = "supervisor"
SYNTHESIS_AGENT = "synthesis_agent"


def read_queries(csv_path):
    queries = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            queries.append(row["query"])
    return queries


def extract_tools_and_failures_from_multi_agent(result):
    """Extract both successful and failed tool calls from Multi-Agent system result structure"""
    successful_tools = set()
    failed_tools = []
    
    if "messages" in result:
        for msg in result["messages"]:
            # AIMessage with tool_calls (OpenAI format)
            if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    if isinstance(tool_call, dict) and "name" in tool_call:
                        # Only add actual tool names, not agent names
                        if tool_call["name"] in ['search_web', 'retrival_vector_db', 'listing_symbol', 'history_price', 'time_now']:
                            successful_tools.add(tool_call["name"])
                    elif hasattr(tool_call, "name"):
                        # Only add actual tool names, not agent names
                        if tool_call.name in ['search_web', 'retrival_vector_db', 'listing_symbol', 'history_price', 'time_now']:
                            successful_tools.add(tool_call.name)
            
            # Check for invalid_tool_calls (failed tool calls)
            if isinstance(msg, AIMessage) and hasattr(msg, "invalid_tool_calls") and msg.invalid_tool_calls:
                for invalid_tool_call in msg.invalid_tool_calls:
                    if isinstance(invalid_tool_call, dict):
                        tool_name = invalid_tool_call.get("name", "unknown_tool")
                        error_msg = invalid_tool_call.get("error", "Unknown error")
                        failed_tools.append(f"{tool_name}: {error_msg}")
                    elif hasattr(invalid_tool_call, "name"):
                        tool_name = getattr(invalid_tool_call, "name", "unknown_tool")
                        error_msg = getattr(invalid_tool_call, "error", "Unknown error")
                        failed_tools.append(f"{tool_name}: {error_msg}")
            
            # ToolMessage with error status (LangGraph format)
            if hasattr(msg, "name") and getattr(msg, "name", None):
                # Only add actual tool names, not agent names
                if msg.name in ['search_web', 'retrival_vector_db', 'listing_symbol', 'history_price', 'time_now']:
                    successful_tools.add(getattr(msg, "name"))
                    
                    # Check for error status in ToolMessage
                    if hasattr(msg, "status") and getattr(msg, "status") == "error":
                        tool_name = getattr(msg, "name")
                        error_content = getattr(msg, "content", "Unknown error")
                        failed_tools.append(f"{tool_name}: {error_content}")
                        # Remove from successful tools if it failed
                        successful_tools.discard(tool_name)
            
            # Check for ToolMessage with error in additional_kwargs
            if (hasattr(msg, "additional_kwargs") and 
                isinstance(getattr(msg, "additional_kwargs"), dict) and 
                "error" in getattr(msg, "additional_kwargs")):
                tool_name = getattr(msg, "name", "unknown_tool")
                error_info = getattr(msg, "additional_kwargs")["error"]
                if isinstance(error_info, dict):
                    error_msg = error_info.get("message", str(error_info))
                else:
                    error_msg = str(error_info)
                failed_tools.append(f"{tool_name}: {error_msg}")
                # Remove from successful tools if it failed
                successful_tools.discard(tool_name)
    
    return list(successful_tools), failed_tools


def extract_final_output_from_multi_agent(result):
    """Extract the final meaningful output from multi-agent system"""
    if "messages" not in result:
        return str(result)
    
    final_messages = result["messages"]
    if not final_messages:
        return ""
    
    # Get the last meaningful response (not supervisor routing)
    final_response = None
    for msg in reversed(final_messages):
        if isinstance(msg, AIMessage) and hasattr(msg, 'name'):
            # Skip supervisor messages and tool call messages
            if (msg.name in [RESEARCH_AGENT, FINANCE_AGENT, SYNTHESIS_AGENT] and 
                not (hasattr(msg, 'tool_calls') and msg.tool_calls)):
                final_response = msg
                break
        elif isinstance(msg, AIMessage) and not hasattr(msg, 'name'):
            # Generic AI message without tool calls
            if not (hasattr(msg, 'tool_calls') and msg.tool_calls):
                final_response = msg
                break
    
    if final_response:
        return getattr(final_response, 'content', '')
    else:
        # Fallback to last message
        return getattr(final_messages[-1], 'content', str(final_messages[-1]))


async def eval_multi_agent(queries):
    results = []
    for idx, query in enumerate(queries):
        print(f"Đang chạy đến dòng số {idx+1}/{len(queries)} trong dataset...")
        print(f"Query: {query}")
        try:
            # Multi-agent expects messages format
            result = await multi_agent_graph.ainvoke({
                "messages": [HumanMessage(content=query)]
            }, config={"callbacks": [langfuse_handler], "tags": tag})

            # Extract output - Multi-agent has complex message structure
            output = extract_final_output_from_multi_agent(result)
                
            # Extract both successful and failed tools from Multi-agent specific structure
            successful_tools, failed_tools = extract_tools_and_failures_from_multi_agent(result)
            
            # Log agent workflow for debugging
            if "messages" in result:
                agents_used = set()
                for msg in result["messages"]:
                    if hasattr(msg, 'name') and msg.name in [SUPERVISOR, RESEARCH_AGENT, FINANCE_AGENT, SYNTHESIS_AGENT]:
                        agents_used.add(msg.name)
                print(f"Agents used: {', '.join(agents_used)}")
            
        except Exception as e:
            output = f"ERROR: {e}"
            successful_tools = []
            failed_tools = []
            print(f"Error processing query {idx+1}: {e}")
            
        results.append({
            "input": query,
            "output": output,
            "tools": ", ".join(successful_tools),
            "failed_tools": ", ".join(failed_tools) if failed_tools else "",
            "failed_tools_count": len(failed_tools)
        })
        print(f"Completed query {idx+1}/{len(queries)}")
        print("-" * 50)
    return results


def write_results_csv(results, output_path):
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["input", "output", "tools", "failed_tools", "failed_tools_count"])
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    print(f"Results written to {output_path}")


def main():
    print("Starting Multi-Agent System Evaluation...")
    queries = read_queries(INPUT_CSV)
    print(f"Loaded {len(queries)} queries from {INPUT_CSV}")
    
    results = asyncio.run(eval_multi_agent(queries))
    write_results_csv(results, OUTPUT_CSV)
    
    print("Evaluation completed!")

if __name__ == "__main__":
    main() 