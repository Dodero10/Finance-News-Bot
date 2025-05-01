"""
Example usage of Finance Tool Agent with RAG

This script demonstrates how to use the Finance Tool Agent with RAG
for answering financial questions.
"""

from dotenv import load_dotenv
import os
import sys
from finance_rag import FinanceNewsRAG
from tool_agent import FinanceToolAgent

def main():
    """Run a simple example of the Finance Tool Agent with RAG."""
    
    # Load environment variables
    load_dotenv()
    
    # Check if data directory exists and has JSON files
    data_path = "data"
    if not os.path.exists(data_path):
        print(f"Error: Data directory '{data_path}' does not exist")
        sys.exit(1)
    
    json_files = [f for f in os.listdir(data_path) if f.endswith('.json')]
    if not json_files:
        print(f"Error: No JSON files found in '{data_path}' directory")
        sys.exit(1)
    
    # Initialize RAG system and load data
    rag = FinanceNewsRAG(data_path=data_path)
    print(f"Loading financial news data from {len(json_files)} JSON files...")
    print(f"Files to process: {', '.join(json_files)}")
    
    try:
        num_docs = rag.load_data(json_files)
        print(f"Successfully loaded {num_docs} documents into the vector store")
        
        if num_docs == 0:
            print("No documents were loaded. Check your JSON files for proper content.")
            sys.exit(1)
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)
    
    # Initialize tool agent with the loaded RAG system
    print("Initializing tool agent...")
    agent = FinanceToolAgent(data_path=data_path, rag_system=rag)
    
    # Sample questions to test
    questions = [
        "What are the latest trends in bond markets?",
        "How are Vietnamese bond funds performing?",
        "What is happening with Vingroup's investments?",
        "What is the outlook for trái phiếu in 2025?",
    ]
    
    # Process each question
    for i, question in enumerate(questions):
        print(f"\n\n=== Question {i+1}: {question} ===\n")
        
        # Process the question through the agent
        messages = agent.invoke(question)
        
        # Print the conversation
        for j, msg in enumerate(messages):
            role = "User" if j == 0 else "Assistant" if msg.type == "ai" else "Tool"
            print(f"{role}: {msg.content}")
            
            # If it's a tool message, add a separator
            if msg.type == "tool":
                print("---")
    
    # Interactive mode
    print("\n\n=== Interactive Mode ===")
    print("Type 'exit' to quit")
    
    while True:
        # Get user input
        user_input = input("\nYou: ")
        if user_input.lower() == "exit":
            break
        
        # Process the user input
        messages = agent.invoke(user_input)
        
        # Print assistant and tool responses
        for msg in messages[1:]:  # Skip the user message
            role = "Assistant" if msg.type == "ai" else "Tool"
            print(f"{role}: {msg.content}")

if __name__ == "__main__":
    main() 