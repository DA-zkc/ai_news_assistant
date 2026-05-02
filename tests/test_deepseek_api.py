"""
test_deepseek_api.py - 测试 DeepSeek API 连接
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
from loguru import logger

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")
api_base = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

if not api_key:
    print("❌ DEEPSEEK_API_KEY not found")
    exit(1)

print(f"✓ API Key found: {api_key[:20]}...")
print(f"✓ API Base URL: {api_base}")
print("\n📡 Testing DeepSeek API connection...\n")

client = OpenAI(
    api_key=api_key,
    base_url=api_base
)

# 简单的测试请求
try:
    print("⏳ Sending test request...")
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "user",
                "content": "Return a JSON object with one key 'status' and value 'ok'"
            }
        ],
        temperature=0.2,
        max_tokens=100
    )
    
    response_text = response.choices[0].message.content
    print(f"✅ API Response received!\n")
    print(f"Response: {response_text}\n")
    
    print("=" * 60)
    print("✅ DeepSeek API is working correctly!")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ API Error: {e}")
    import traceback
    traceback.print_exc()
