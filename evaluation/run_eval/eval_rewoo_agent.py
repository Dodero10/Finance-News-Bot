import os
import sys
import csv
import asyncio
from pathlib import Path
from dotenv import load_dotenv

project_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, project_root)

from langfuse.callback import CallbackHandler
from src.agents.rewoo_agent_graph import graph as rewoo_graph
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

os.environ["LANGFUSE_PUBLIC_KEY"] = os.getenv("LANGFUSE_PUBLIC_KEY")
os.environ["LANGFUSE_SECRET_KEY"] = os.getenv("LANGFUSE_SECRET_KEY")
os.environ["LANGFUSE_HOST"] = os.getenv("LANGFUSE_HOST", "http://localhost:3000")
tag = ['rewoo_agent']

langfuse_handler = CallbackHandler()

INPUT_CSV = os.path.join(project_root, "evaluation", "data_eval", "synthetic_data", "synthetic_news.csv")
OUTPUT_CSV = os.path.join(project_root, "evaluation", "data_eval", "results", "rewoo_agent_eval_results.csv")


def read_queries(csv_path):
    queries = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            queries.append(row["query"])
    return queries


def extract_tools_and_failures_from_rewoo(result):
    """Extract both successful and failed tool calls from ReWOO agent result structure"""
    successful_tools = set()
    failed_tools = []
    
    if "steps" in result:
        for step in result["steps"]:
            if len(step) >= 3:  # (plan_desc, step_name, tool, tool_input)
                tool_name = step[2]
                successful_tools.add(tool_name)
    
    if "results" in result:
        for step_name, step_result in result["results"].items():
            if isinstance(step_result, str):
                if "Error executing" in step_result or "Error:" in step_result:
                    if "Error executing" in step_result:
                        parts = step_result.split("Error executing ")
                        if len(parts) > 1:
                            tool_name = parts[1].split(":")[0].strip()
                            error_msg = step_result.split(":", 1)[1].strip() if ":" in step_result else "Unknown error"
                            failed_tools.append(f"{tool_name}: {error_msg}")
                            successful_tools.discard(tool_name)
                    elif step_result.startswith("Error:"):
                        error_msg = step_result.replace("Error:", "").strip()
                        failed_tools.append(f"unknown_tool: {error_msg}")
    
    if "messages" in result:
        for msg in result["messages"]:
            if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    if isinstance(tool_call, dict) and "name" in tool_call:
                        successful_tools.add(tool_call["name"])
                    elif hasattr(tool_call, "name"):
                        successful_tools.add(tool_call.name)
            
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
            
            if hasattr(msg, "name") and getattr(msg, "name", None):
                successful_tools.add(getattr(msg, "name"))
                
                if hasattr(msg, "status") and getattr(msg, "status") == "error":
                    tool_name = getattr(msg, "name")
                    error_content = getattr(msg, "content", "Unknown error")
                    failed_tools.append(f"{tool_name}: {error_content}")
                    successful_tools.discard(tool_name)
            
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
                successful_tools.discard(tool_name)
    
    return list(successful_tools), failed_tools


async def eval_rewoo_agent(queries):
    results = []
    for idx, query in enumerate(queries):
        print(f"Đang chạy đến dòng số {idx+1}/{len(queries)} trong dataset...")
        print(f"Query: {query}")
        try:
            result = await rewoo_graph.ainvoke({
                "messages": [HumanMessage(content=query)]
            }, config={"callbacks": [langfuse_handler], "tags": tag})

            output = ""
            if "result" in result:
                output = result["result"]
            elif "messages" in result and result["messages"]:
                final_message = result["messages"][-1]
                if isinstance(final_message, AIMessage):
                    output = final_message.content
            else:
                output = str(result)
                
            successful_tools, failed_tools = extract_tools_and_failures_from_rewoo(result)
            
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
    print("Starting ReWOO Agent Evaluation...")
    queries = read_queries(INPUT_CSV)
    print(f"Loaded {len(queries)} queries from {INPUT_CSV}")
    
    results = asyncio.run(eval_rewoo_agent(queries))
    write_results_csv(results, OUTPUT_CSV)
    
    print("Evaluation completed!")

if __name__ == "__main__":
    main() 