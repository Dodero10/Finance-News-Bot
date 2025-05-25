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
from src.agents.rewoo_agent_graph import graph as rewoo_graph
from langchain_core.messages import HumanMessage, AIMessage

# Load environment variables
load_dotenv()

os.environ["LANGFUSE_PUBLIC_KEY"] = os.getenv("LANGFUSE_PUBLIC_KEY")
os.environ["LANGFUSE_SECRET_KEY"] = os.getenv("LANGFUSE_SECRET_KEY")
os.environ["LANGFUSE_HOST"] = os.getenv("LANGFUSE_HOST", "http://localhost:3000")

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


def extract_tools_from_rewoo(result):
    """Extract tools used from ReWOO agent result structure"""
    tools = set()
    
    # Extract tools from steps (planned tools)
    if "steps" in result:
        for step in result["steps"]:
            if len(step) >= 3:  # (plan_desc, step_name, tool, tool_input)
                tool_name = step[2]
                tools.add(tool_name)
    
    # Also check messages for any tool calls
    if "messages" in result:
        for msg in result["messages"]:
            if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    if isinstance(tool_call, dict) and "name" in tool_call:
                        tools.add(tool_call["name"])
                    elif hasattr(tool_call, "name"):
                        tools.add(tool_call.name)
            # ToolMessage with .name (if any)
            if hasattr(msg, "name") and getattr(msg, "name", None):
                tools.add(getattr(msg, "name"))
    
    return list(tools)


async def eval_rewoo_agent(queries):
    results = []
    for idx, query in enumerate(queries):
        print(f"Đang chạy đến dòng số {idx+1}/{len(queries)} trong dataset...")
        print(f"Query: {query}")
        try:
            # ReWOO agent expects messages format like other agents
            result = await rewoo_graph.ainvoke({
                "messages": [HumanMessage(content=query)]
            }, config={"callbacks": [langfuse_handler]})

            # Extract output - ReWOO has different output structure
            output = ""
            if "result" in result:
                # ReWOO stores final answer in 'result' field
                output = result["result"]
            elif "messages" in result and result["messages"]:
                # Fallback to last message
                final_message = result["messages"][-1]
                if isinstance(final_message, AIMessage):
                    output = final_message.content
            else:
                output = str(result)
                
            # Extract tools used from ReWOO specific structure
            tools = extract_tools_from_rewoo(result)
            
        except Exception as e:
            output = f"ERROR: {e}"
            tools = []
            print(f"Error processing query {idx+1}: {e}")
            
        results.append({
            "input": query,
            "output": output,
            "tools": ", ".join(tools)
        })
        print(f"Completed query {idx+1}/{len(queries)}")
        print("-" * 50)
    return results


def write_results_csv(results, output_path):
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["input", "output", "tools"])
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