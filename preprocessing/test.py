# Read the json file
import json

with open('data/processed_test.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(data[1]['metadata']['images'][2]['parsed_content'])
