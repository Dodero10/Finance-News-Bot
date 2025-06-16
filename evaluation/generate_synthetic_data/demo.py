import os
import json
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def display_example():
    """Display an example of what the generated dataset looks like."""
    try:
        # Check if the example file exists
        if os.path.exists("example_output.csv"):
            df = pd.read_csv("example_output.csv")
            print("\n=== Example of Generated Dataset ===\n")
            
            # Display each row in a readable format
            for _, row in df.iterrows():
                print(f"ID: {row['id']}")
                print(f"Query: {row['query']}")
                
                # Parse and display the answers
                answers = json.loads(row['answers'])
                print("Tool Calls:")
                for tool_call in answers:
                    print(f"  - Tool: {tool_call['name']}")
                    print(f"    Arguments: {json.dumps(tool_call.get('arguments', {}), indent=6, ensure_ascii=False)}")
                
                print("\n" + "-"*50 + "\n")
        else:
            print("Example file not found. Run the generator first to create the dataset.")
    
    except Exception as e:
        print(f"Error displaying example: {str(e)}")

def run_generator():
    """Run the generator script to create a new dataset."""
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n⚠️ WARNING: OPENAI_API_KEY not found in environment variables.")
        print("Please set your OpenAI API key in a .env file or environment variable.")
        return
    
    try:
        print("\n=== Running Synthetic Dataset Generator ===\n")
        print("Using model: gpt-4.1-nano@evaluation")
        from generate_finance_dataset import main
        main()
    except ImportError:
        print("Could not import the generator. Make sure generate_finance_dataset.py exists.")
    except Exception as e:
        print(f"Error running generator: {str(e)}")

if __name__ == "__main__":
    # Check if OpenAI API key exists
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n⚠️ No OpenAI API key found. Showing example output only.")
        display_example()
    else:
        # Ask user if they want to generate new data or just see examples
        choice = input("Do you want to generate new data using gpt-4.1-nano@evaluation (y) or just see example output (n)? [y/n]: ")
        if choice.lower() == 'y':
            run_generator()
        else:
            display_example() 