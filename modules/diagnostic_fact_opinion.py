"""
diagnostic_fact_opinion.py - 诊断 fact_opinion API 调用
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "modules"))

import os
from dotenv import load_dotenv
import httpx
from loguru import logger

load_dotenv()

api_key = os.getenv("DASHSCOPE_API_KEY")

print("=" * 60)
print("🔧 Diagnostic: Testing fact_opinion API call directly")
print("=" * 60 + "\n")

# 构建真实的提取提示词
from fact_opinion import _build_extraction_prompt

title = "AI Ethics in Legal System"
description = "A federal judge reprimanded an attorney for using AI-generated research without disclosure."
url = "https://example.com"

prompt = _build_extraction_prompt(title, description, url)

print(f"📝 Prompt length: {len(prompt)} chars")
print(f"🔑 API Key: {api_key[:20]}...\n")

try:
    print("⏳ Calling DashScope API...")
    
    client = httpx.Client(timeout=60.0)
    
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
                    "content": prompt
                }
            ]
        },
        "parameters": {
            "temperature": 0.3,
            "max_tokens": 2000,
        }
    }
    
    response = client.post(
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
        headers=headers,
        json=payload,
        timeout=60.0
    )
    
    print(f"✓ Response Status: {response.status_code}")
    
    response_data = response.json()
    
    if "output" not in response_data:
        print(f"❌ Invalid response format: {response_data}")
        exit(1)
    
    output = response_data.get("output", {})
    choices = output.get("choices", [])
    
    if not choices:
        print("❌ No choices in response")
        exit(1)
    
    response_text = choices[0].get("message", {}).get("content", "")
    
    print(f"✓ Response length: {len(response_text)} chars\n")
    print(f"Response preview:\n{response_text[:500]}...\n")
    
    # 尝试解析 JSON
    import json
    
    # 清理响应
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    
    extraction = json.loads(cleaned)
    
    print("✅ JSON parsing successful!")
    print(f"📊 Results:")
    print(f"   - {len(extraction.get('quantitative_facts', []))} quantitative facts")
    print(f"   - {len(extraction.get('qualitative_facts', []))} qualitative facts")
    print(f"   - {len(extraction.get('opinions', []))} opinions")
    
    client.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
