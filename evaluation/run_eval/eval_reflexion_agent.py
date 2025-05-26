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
from src.agents.reflexion_agent_graph import graph as reflexion_graph
from langchain_core.messages import HumanMessage, AIMessage

# Load environment variables
load_dotenv()

os.environ["LANGFUSE_PUBLIC_KEY"] = os.getenv("LANGFUSE_PUBLIC_KEY")
os.environ["LANGFUSE_SECRET_KEY"] = os.getenv("LANGFUSE_SECRET_KEY")
os.environ["LANGFUSE_HOST"] = os.getenv("LANGFUSE_HOST", "http://localhost:3000")

langfuse_handler = CallbackHandler()

INPUT_CSV = os.path.join(project_root, "evaluation", "data_eval", "synthetic_data", "synthetic_news.csv")
OUTPUT_CSV = os.path.join(project_root, "evaluation", "data_eval", "results", "reflexion_agent_eval_results.csv")


def read_queries(csv_path):
    queries = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            queries.append(row["query"])
    return queries


def extract_tools(messages):
    tools = set()
    for msg in messages:
        # AIMessage with tool_calls (OpenAI format)
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


async def eval_reflexion_agent(queries):
    results = []
    for idx, query in enumerate(queries):
        print(f"Đang chạy đến dòng số {idx+1}/{len(queries)} trong dataset...")
        print(f"Query: {query}")
        try:
            result = await reflexion_graph.ainvoke({
                "messages": [HumanMessage(content=query)]
            }, config={"callbacks": [langfuse_handler]})

            # Extract output - for reflexion agent, get the last non-reflection message
            output = ""
            if "messages" in result:
                messages = result["messages"]
                if messages:
                    # Get the last non-reflection message which contains the final response
                    final_message = None
                    for msg in reversed(messages):
                        if isinstance(msg, AIMessage) and not msg.additional_kwargs.get("reflection"):
                            final_message = msg
                            break
                    
                    if final_message:
                        output = final_message.content
                    else:
                        # Fallback to last message if no non-reflection message found
                        output = messages[-1].content if messages else ""
                        
                tools = extract_tools(messages)
            else:
                output = str(result)
                tools = []
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
    print("Starting Reflexion Agent Evaluation...")
    queries = read_queries(INPUT_CSV)
    print(f"Loaded {len(queries)} queries from {INPUT_CSV}")
    
    results = asyncio.run(eval_reflexion_agent(queries))
    write_results_csv(results, OUTPUT_CSV)
    
    print("Evaluation completed!")

if __name__ == "__main__":
    main() 