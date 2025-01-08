from openai import OpenAI
from dotenv import load_dotenv
import os
import sys, getopt

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Ensure it is set in the .env file.")

# Set the OpenAI API key for ChatGPT
client = OpenAI(api_key=api_key)

try:
    response = client.chat.completions.create(model="gpt-3.5-turbo-0125",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"},
    ])
    print("API response:", response)
except Exception as e:
    print(f"Error: {e}")