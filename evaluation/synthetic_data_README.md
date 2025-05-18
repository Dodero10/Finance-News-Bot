# Financial Synthetic Dataset Generator

This script generates synthetic financial conversation datasets for training AI assistants. It creates realistic user queries in Vietnamese about the stock market and specifies the appropriate tool calls needed to answer each query.

## Requirements

- Python 3.8+
- OpenAI API key
- Required Python packages (see requirements.txt)

## Setup

1. Clone this repository
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Usage

Run the script to generate a synthetic dataset:

```bash
python generate_finance_dataset.py
```

By default, this will:
- Generate 1 synthetic financial query
- Use the gpt-4.1-nano@evaluation model
- Save the dataset to `finance_synthetic_dataset.csv`

You can modify the script parameters in the `main()` function to generate more samples or use a different model.

## Output Format

The generated dataset follows this format:

| Column | Description |
|--------|-------------|
| id | Unique identifier for each entry |
| query | The user's question in Vietnamese |
| answers | JSON array of expected tool calls with their arguments |
| tools | Available tools with their descriptions and parameters |

Example:

```csv
id,query,answers,tools
0,"Cho tôi biết giá cổ phiếu VNM từ ngày 2023-05-01 đến 2023-05-15","[{""name"": ""history_price"", ""arguments"": {""symbol"": ""VNM"", ""source"": ""VCI"", ""start_date"": ""2023-05-01"", ""end_date"": ""2023-05-15"", ""interval"": ""1D""}}]","[{""name"": ""listing_symbol"", ""description"": ""..."", ""parameters"": {}}, ...]"
```

## Customization

You can modify the following aspects of the generator:
- Number of samples generated
- Stock symbols included in the dataset
- Date ranges for historical data
- Types of queries generated
- Available tools and their parameters

## License

[Include your license information here] 