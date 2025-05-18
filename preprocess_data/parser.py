from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import base64, httpx, os
from dotenv import load_dotenv

load_dotenv()

# Initialize the model
model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=os.getenv("GOOGLE_API_KEY"))

# Download and encode the image
image_data = base64.b64encode(httpx.get("https://image.tinnhanhchungkhoan.vn/w640/Uploaded/2025/wpxlcdjwi/2025_03_16/1-5394-555.png").content).decode("utf-8")

# Create a message with the image
message = HumanMessage(
    content=[
        {"type": "text", "text": "Parse image and return the content in markdown format"},
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
        },
    ],
)

# Invoke the model with the message
response = model.invoke([message])

# Print the model's response
print(response.content)