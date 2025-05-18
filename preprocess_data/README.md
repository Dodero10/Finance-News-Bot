# Image Processor for JSON Content

This module processes images found in JSON article content by:
1. Extracting images from markdown content
2. Using Google's Gemini model to parse the image content
3. Storing the parsed image data as metadata
4. Replacing image references in the content with placeholders

## Requirements

- Python 3.7+
- Required packages:
  - langchain_core
  - langchain_google_genai
  - httpx
  - python-dotenv

## Setup

1. Create a `.env` file in the project root with your Google API key:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

2. Install required packages:
   ```
   pip install langchain_core langchain_google_genai httpx python-dotenv
   ```

## Usage

### Using the CLI script

```bash
python process_images.py --input data/test.json --output data/processed_test.json
```

Or use the short form:

```bash
python process_images.py -i data/test.json -o data/processed_test.json
```

### Using the module in your code

```python
from image_processor import process_json_file

# Process a JSON file
input_file = "path/to/input.json"
output_file = "path/to/output.json"
processed_data = process_json_file(input_file, output_file)
```

## Output Format

The processed JSON will include a `metadata` field for each article with an `images` array containing:

```json
"metadata": {
  "images": [
    {
      "id": 1,
      "url": "original_image_url",
      "caption": "original_caption",
      "parsed_content": "text extracted from the image by Gemini"
    }
  ]
}
```

The original image markdown in the content `![caption](url)` will be replaced with `[IMAGE: caption]`. 