import os
from dotenv import load_dotenv
from strands import Agent
from strands.models.openai import OpenAIModel
from strands_tools import image_reader

load_dotenv()

model = OpenAIModel(
    client_args={
        "api_key": os.getenv("GROQ_API_KEY"),
        "base_url": "https://api.groq.com/openai/v1",
    },
    model_id="qwen/qwen3.8-27b",
)

agent = Agent(model=model, tools=[image_reader])

response = agent(
    "Look at the image at ./sample_receipt.png and tell me the vendor, amount, and date on it."
)

print(response)