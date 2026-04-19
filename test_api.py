# test_api.py
"""Test if OpenAI API is working."""
import os
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("❌ OPENAI_API_KEY not found in environment")
    print("Please create a .env file with: OPENAI_API_KEY=your_key_here")
    exit(1)

print(f"✓ API key found: {api_key[:10]}...")

# Set API key for older version
openai.api_key = api_key

try:
    # Test simple completion
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'API is working!'"}],
        max_tokens=20
    )
    
    print(f"✓ API test successful: {response['choices'][0]['message']['content']}")
    
    # Test embeddings
    response = openai.Embedding.create(
        model="text-embedding-ada-002",  # Older model that works with 0.28.1
        input=["Test embedding"]
    )
    
    print(f"✓ Embeddings test successful: Vector length {len(response['data'][0]['embedding'])}")
    
    print("\n✅ OpenAI API is working correctly!")
    
except Exception as e:
    print(f"❌ API test failed: {e}")
    print("\nNote: Even with 0 credits, the API should still respond with an error message.")
    print("The error would be about insufficient credits, not about the connection.")
    exit(1)