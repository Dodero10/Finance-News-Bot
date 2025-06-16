import pandas as pd
import json
import random
from datetime import datetime, timedelta
import pytz
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def get_vietnam_time():
    vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    current_time = datetime.now(vietnam_tz).strftime('%Y-%m-%d %H:%M:%S')
    return current_time

def random_date(start_date, end_date):
    delta = end_date - start_date
    random_days = random.randrange(delta.days)
    return start_date + timedelta(days=random_days)

def format_date(date):
    return date.strftime("%Y-%m-%d")

# Load stock symbols and company names
def load_stock_data(csv_file="evaluation/data_eval/list_symbol_organ_name.csv"):
    df = pd.read_csv(csv_file)
    # Filter out rows where the organ name is empty
    df = df[df['organ_name'].notna() & (df['organ_name'] != '')]
    return df

# Define tool descriptions
def get_tools_description():
    tools_description = [
        {
            "name": "listing_symbol",
            "description": "Get listing symbol about stock with company name",
            "parameters": {}
        },
        {
            "name": "history_price",
            "description": "Retrieve historical price data for a given stock symbol",
            "parameters": {
                "symbol": {
                    "description": "The stock symbol to retrieve data for",
                    "type": "str"
                },
                "source": {
                    "description": "The source from which to retrieve the data (VCI, TCBS, MSN)",
                    "type": "str",
                    "default": "VCI"
                },
                "start_date": {
                    "description": "The start date for the historical data (YYYY-MM-DD)",
                    "type": "str"
                },
                "end_date": {
                    "description": "The end date for the historical data (YYYY-MM-DD)",
                    "type": "str"
                },
                "interval": {
                    "description": "The interval for the historical data (1m, 5m, 15m, 30m, 1H, 1D, 1W, 1M)",
                    "type": "str",
                    "default": "1D"
                }
            }
        },
        {
            "name": "time_now",
            "description": "Get the current time in Vietnam",
            "parameters": {}
        }
    ]
    return tools_description


def get_query_types():
    query_types = [
        # Simple queries for one stock over a specific period
        "single_stock_history",
        
        # Queries for comparing multiple stocks
        "compare_stocks",
        
        # Queries about time
        "current_time",
        
        # Queries for listing all stocks
        "list_all_stocks",
        
        # Queries for stock with different intervals (daily, weekly, monthly, etc.)
        "interval_data",
        
        # Queries combining listing and history
        "combined_listing_history",
        
        # Queries for a company by name rather than symbol
        "company_name_lookup",
        
        # Queries for stock data with specific source
        "specific_source",
        
        # Queries asking for short timeframes (days)
        "short_timeframe",
        
        # Queries asking for long timeframes (months, year)
        "long_timeframe"
    ]
    return query_types

# Generate prompts for different types of financial queries
def generate_query_prompts(symbols_df, num_samples=10):
    prompts = []
    tools = get_tools_description()
    query_types = get_query_types()
    
    # Generate end date (today) and start date (2 years ago)
    end_date = datetime.today()
    start_date = end_date - timedelta(days=730)  # 2 years back to allow for longer ranges
    
    # Ensure we use a good mix of query types
    selected_query_types = []
    for i in range(num_samples):
        if i < len(query_types):
            # For the first batch, use each type once to ensure diversity
            selected_query_types.append(query_types[i])
        else:
            # After covering all types once, choose randomly
            selected_query_types.append(random.choice(query_types))
    
    for i in range(num_samples):
        query_type = selected_query_types[i]
        
        # Configure parameters based on query type
        if query_type == "compare_stocks":
            # Select 2-3 stocks for comparison
            num_symbols = random.randint(2, 3)
            timeframe = "short" if random.random() < 0.5 else "long"
        elif query_type == "single_stock_history":
            # Just one stock
            num_symbols = 1
            timeframe = "medium"
        elif query_type == "current_time":
            # Time query doesn't need stocks
            num_symbols = 0
            timeframe = "none"
        elif query_type == "list_all_stocks":
            # Listing doesn't need specific stocks
            num_symbols = 0
            timeframe = "none"
        elif query_type == "interval_data":
            # One stock with focus on interval
            num_symbols = 1
            timeframe = "short" if random.random() < 0.7 else "medium"
        elif query_type == "combined_listing_history":
            # One stock but will require both tools
            num_symbols = 1
            timeframe = "medium"
        elif query_type == "company_name_lookup":
            # One stock, focus on company name
            num_symbols = 1
            timeframe = "none"
        elif query_type == "specific_source":
            # One stock, focus on data source
            num_symbols = 1
            timeframe = "medium"
        elif query_type == "short_timeframe":
            # One stock, short timeframe
            num_symbols = 1
            timeframe = "short"
        elif query_type == "long_timeframe":
            # One stock, long timeframe
            num_symbols = 1
            timeframe = "long"
        else:
            # Default
            num_symbols = 1
            timeframe = "medium"
        
        # Select random symbols if needed
        if num_symbols > 0:
            selected_symbols = symbols_df.sample(num_symbols)
        else:
            # For queries that don't need specific stocks, still provide context
            selected_symbols = pd.DataFrame()
        
        # Generate date range appropriate for the timeframe
        if timeframe == "short":
            # 1-14 days
            random_duration = random.randint(1, 14)
            random_end = random_date(end_date - timedelta(days=30), end_date)
            random_start = random_end - timedelta(days=random_duration)
        elif timeframe == "medium":
            # 15-60 days
            random_duration = random.randint(15, 60)
            random_end = random_date(end_date - timedelta(days=90), end_date)
            random_start = random_end - timedelta(days=random_duration)
        elif timeframe == "long":
            # 61-365 days
            random_duration = random.randint(61, 365)
            random_end = end_date - timedelta(days=random.randint(0, 30))
            random_start = random_end - timedelta(days=random_duration)
        else:
            # No timeframe needed (e.g., for current time queries)
            random_start = end_date - timedelta(days=30)
            random_end = end_date
        
        formatted_start = format_date(random_start)
        formatted_end = format_date(random_end)
        
        # Create context
        if not selected_symbols.empty:
            symbol_contexts = []
            for _, row in selected_symbols.iterrows():
                symbol_contexts.append(f"Symbol: {row['symbol']}, Company: {row['organ_name']}")
            
            context = {
                "symbols": selected_symbols.to_dict('records'),
                "date_range": {
                    "start_date": formatted_start,
                    "end_date": formatted_end
                },
                "current_time": get_vietnam_time(),
                "query_type": query_type
            }
        else:
            context = {
                "symbols": [],
                "date_range": {
                    "start_date": formatted_start,
                    "end_date": formatted_end
                },
                "current_time": get_vietnam_time(),
                "query_type": query_type
            }
        
        prompts.append({
            "context": context,
            "tools": tools
        })
    
    return prompts

# Generate synthetic dataset using OpenAI
def generate_synthetic_dataset(prompts, model="gpt-4.1-nano"):
    dataset = []
    
    for i, prompt_data in enumerate(prompts):
        context = prompt_data["context"]
        tools_data = prompt_data["tools"]
        query_type = context.get("query_type", "general")
        
        # Build the prompt for OpenAI
        system_prompt = """You are an AI assistant that helps generate synthetic financial data for training another AI.
        Your task is to create realistic user queries about Vietnamese stocks and specify which tools should be called to answer them.
        
        For each query, you need to:
        1. Generate a natural Vietnamese financial question that a user might ask
        2. Determine which tools need to be called to answer the question
        3. Specify the parameters for each tool call
        
        The output should be in JSON format with the following structure:
        {
            "query": "User's question in Vietnamese",
            "answers": [
                {
                    "name": "tool_name",
                    "arguments": {
                        "param1": "value1",
                        "param2": "value2"
                    }
                }
            ]
        }
        
        Do not include any explanations, just return the JSON.
        """
        
        # Create a more specific user prompt based on query type
        additional_instruction = ""
        if query_type == "compare_stocks":
            additional_instruction = "Create a question that asks to compare multiple stocks over the given period. The answer should call history_price for each stock."
        elif query_type == "current_time":
            additional_instruction = "Create a question that asks about the current time in Vietnam. The answer should call the time_now tool."
        elif query_type == "list_all_stocks":
            additional_instruction = "Create a question that asks for a list of all available stocks. The answer should call the listing_symbol tool."
        elif query_type == "interval_data":
            additional_instruction = "Create a question that specifically asks for data with a non-default interval (not '1D'). The answer should use a different interval parameter like '1W', '1M', etc."
        elif query_type == "combined_listing_history":
            additional_instruction = "Create a question that would require both listing_symbol and history_price tools."
        elif query_type == "company_name_lookup":
            additional_instruction = "Create a question that refers to the company by name rather than by stock symbol. The answer should first determine the symbol."
        elif query_type == "specific_source":
            additional_instruction = "Create a question that specifically asks for data from a non-default source. The answer should use a different source parameter like 'TCBS' or 'MSN'."
        elif query_type == "short_timeframe":
            additional_instruction = "Create a question about very recent stock data (days). The answer should use a short date range."
        elif query_type == "long_timeframe":
            additional_instruction = "Create a question about long-term stock data (months or year). The answer should use a long date range."
        
        user_prompt = f"""Generate a synthetic financial query and tool calls based on the following context:

Available Stocks:
{json.dumps(context['symbols'], ensure_ascii=False, indent=2)}

Date Range: {context['date_range']['start_date']} to {context['date_range']['end_date']}
Current Time: {context['current_time']}

Available Tools:
{json.dumps(tools_data, ensure_ascii=False, indent=2)}

{additional_instruction}

Create a question that would require using one or more of these tools. The question should be in Vietnamese and related to the stock market, stock prices, or company information.
"""

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Add to dataset
            dataset.append({
                "id": i,
                "query": result["query"],
                "answers": json.dumps(result["answers"], ensure_ascii=False),
                "tools": json.dumps(tools_data, ensure_ascii=False)
            })
            
            print(f"Generated sample {i+1}/{len(prompts)} - Type: {query_type}")
            
        except Exception as e:
            print(f"Error generating sample {i+1}: {str(e)}")
    
    return dataset

# Save dataset to CSV
def save_dataset(dataset, filename="finance_synthetic_dataset.csv"):
    df = pd.DataFrame(dataset)
    df.to_csv(filename, index=False)
    print(f"Dataset saved to {filename}")
    return df

# Main function
def main():
    print("Loading stock data...")
    symbols_df = load_stock_data()
    
    print("Generating query prompts...")
    prompts = generate_query_prompts(symbols_df, num_samples=10)
    
    print("Generating synthetic dataset using gpt-4.1-nano.")
    dataset = generate_synthetic_dataset(prompts, model="gpt-4.1-nano")
    
    print("Saving dataset...")
    df = save_dataset(dataset)
    
    # Display the generated dataset
    print("\nGenerated Dataset Sample:")
    pd.set_option('display.max_colwidth', None)
    print(df)

if __name__ == "__main__":
    main() 