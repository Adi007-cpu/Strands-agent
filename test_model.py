import os
from dotenv import load_dotenv
from strands import Agent
from strands.models.openai import OpenAIModel

load_dotenv()
print('GROQ KEY:', repr(os.getenv('GROQ_API_KEY')))
model = OpenAIModel(
    client_args={
        "api_key": os.environ.get("GROQ_API_KEY"),
        "base_url": "https://api.groq.com/openai/v1",
    },
    model_id="qwen/qwen3.8-27b",
)

agent = Agent(model=model, callback_handler=None)
response = agent("Hello, are you working?")
print(response) 