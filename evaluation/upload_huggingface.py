import os
from huggingface_hub import HfApi
from dotenv import load_dotenv
import pathlib

load_dotenv()

# Or use the token from .env file
os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN")

api = HfApi(token=os.getenv("HF_TOKEN"))

# Get the absolute path to the current script
script_dir = pathlib.Path(__file__).parent.absolute()

# Use an absolute path to the CSV file
file_path = os.path.join(script_dir, "data_eval", "synthetic_news", "synthetic_news.csv")

# Check if the file exists
if not os.path.isfile(file_path):
    raise ValueError(f"File does not exist: {file_path}")
else:
    print(f"Found file: {file_path}")

print("Before upload")
# Upload the file
api.upload_file(
    path_or_fileobj=file_path,
    path_in_repo="synthetic_news.csv",
    repo_id="Dodero1305/Finance-News",
    repo_type="dataset",
    create_pr=True,  # Create a pull request instead of committing directly
)

print("File uploaded successfully.")
