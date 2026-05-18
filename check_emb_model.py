# Create a temporary script to list available models
# save as check_models.py

from google import genai
import os

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# List all available models
for model in client.models.list():
    print(f"Model: {model.name}")
    print(f"Supported actions: {model.supported_actions}")
    print("---")