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
from src.agents.react_agent_graph import graph as react_graph
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

os.environ["LANGFUSE_PUBLIC_KEY"] = os.getenv("LANGFUSE_PUBLIC_KEY")
os.environ["LANGFUSE_SECRET_KEY"] = os.getenv("LANGFUSE_SECRET_KEY")
os.environ["LANGFUSE_HOST"] = os.getenv("LANGFUSE_HOST", "http://localhost:3000")

langfuse_handler = CallbackHandler()

INPUT_CSV = os.path.join(project_root, "evaluation", "data_eval", "synthetic_data", "synthetic_news.csv")
OUTPUT_CSV = os.path.join(project_root, "evaluation", "data_eval", "results", "react_agent_eval_results.csv")


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


async def eval_react_agent(queries):
    results = []
    for idx, query in enumerate(queries):
        print(f"Đang chạy đến dòng số {idx+1}/{len(queries)} trong dataset...")
        print(f"Query: {query}")
        try:
            result = await react_graph.ainvoke({
                "messages": [HumanMessage(content=query)]
            }, config={"callbacks": [langfuse_handler]})

            # Extract output
            output = ""
            if "messages" in result:
                messages = result["messages"]
                if messages:
                    # Get the last message which contains the final response
                    final_message = messages[-1]
                    if isinstance(final_message, AIMessage):
                        output = final_message.content
                tools = extract_tools(messages)
            else:
                output = str(result)
                tools = []
        except Exception as e:
            output = f"ERROR: {e}"
            tools = []
        results.append({
            "input": query,
            "output": output,
            "tools": ", ".join(tools)
        })
    return results


def write_results_csv(results, output_path):
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["input", "output", "tools"])
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    print(f"Results written to {output_path}")


def main():
    queries = read_queries(INPUT_CSV)
    results = asyncio.run(eval_react_agent(queries))
    write_results_csv(results, OUTPUT_CSV)

if __name__ == "__main__":
    main() 