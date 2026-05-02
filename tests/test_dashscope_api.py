"""
test_dashscope_api.py - 测试 DashScope API 连接
"""

import os
from dotenv import load_dotenv
import httpx
from loguru import logger

load_dotenv()

api_key = os.getenv("DASHSCOPE_API_KEY")

if not api_key:
    print("❌ DASHSCOPE_API_KEY not found")
    exit(1)

print(f"✓ API Key found: {api_key[:20]}...")
print("\n📡 Testing DashScope (Qwen3-235B-A22B) API connection...\n")

try:
    print("⏳ Sending test request...")
    
    client = httpx.Client(timeout=30.0)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "qwen3-235b-a22b",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": "Return a JSON object with one key 'status' and value 'ok'"
                }
            ]
        },
        "parameters": {
            "temperature": 0.3,
            "max_tokens": 100,
        }
    }
    
    response = client.post(
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
        headers=headers,
        json=payload
    )
    
    print(f"Response Status: {response.status_code}\n")
    
    response_data = response.json()
    
    # DashScope 的响应格式不同，直接检查 output
    if "output" not in response_data:
        print(f"❌ DashScope API error: Invalid response format")
        print(f"Response: {response_data}")
        exit(1)
        exit(1)
    
    # 提取响应
    output = response_data.get("output", {})
    choices = output.get("choices", [])
    
    if choices:
        response_text = choices[0].get("message", {}).get("content", "")
        print(f"✅ API Response received:\n{response_text}\n")
    
    client.close()
    
    print("=" * 60)
    print("✅ DashScope API is working correctly!")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ API Error: {e}")
    import traceback
    traceback.print_exc()
