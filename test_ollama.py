#!/usr/bin/env python3

# Simple test using your exact working code format
from ollama import chat
from ollama import ChatResponse

try:
    response: ChatResponse = chat(model='llama3.2-vision:latest', messages=[
        {
            'role': 'user',
            'content': 'Say hello in exactly 2 words',
        },
    ])
    print("✅ Ollama working:")
    print(response['message']['content'])
    # or access fields directly from the response object
    print("Direct access:", response.message.content)
except Exception as e:
    print(f"❌ Ollama test failed: {e}")
    print("Make sure:")
    print("1. Ollama is running (ollama serve)")
    print("2. Model is available (ollama pull llama3.2-vision:latest)")