# utils/api_clients.py
import os
import requests
import json
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# ========== DeepSeek 客户端（兼容 OpenAI SDK 风格）==========
from openai import OpenAI

deepseek_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
)

def call_deepseek_flash(messages, temperature=0.2, max_tokens=2000):
    """调用 DeepSeek-V4-flash（非思考模式）"""
    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-v4-flash",   # 请确认实际模型名
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}  # 要求JSON输出
        )
        content = response.choices[0].message.content
        logger.debug(f"DeepSeek flash 返回: {content[:200]}...")
        return content
    except Exception as e:
        logger.error(f"DeepSeek flash 调用失败: {e}")
        return None

def call_deepseek_pro(messages, temperature=0.1, max_tokens=3000):
    """调用 DeepSeek-V4-pro（思考模式）"""
    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-v4-pro",      # 请确认实际模型名
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_effort="high",
            extra_body={ "thinking": { "type": "enabled" } }
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"DeepSeek pro 调用失败: {e}")
        return None

# ========== 通义千问客户端（DashScope）==========
import dashscope
from dashscope import Generation

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

def call_qwen(messages, temperature=0.1, max_tokens=2000):
    """调用 Qwen3-235B-A22B"""
    try:
        response = Generation.call(
            model="qwen3-235b-a22b",      # 请确认实际模型名
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            result_format="message"
        )
        if response.status_code == 200:
            content = response.output.choices[0].message.content
            logger.debug(f"Qwen 返回: {content[:200]}...")
            return content
        else:
            logger.error(f"Qwen 调用失败: {response.code} - {response.message}")
            return None
    except Exception as e:
        logger.error(f"Qwen 调用异常: {e}")
        return None

# ========== NewsAPI 新闻获取 ==========
def fetch_news_from_api(query="artificial intelligence", page_size=20):
    api_key = os.getenv("GNEWS_API_KEY")   # 在 .env 中添加
    url = "https://gnews.io/api/v4/search"
    params = {
        "q": query,
        "lang": "en",
        "max": page_size,
        "apikey": api_key,
        "sortby": "publishedAt"
    }
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()
    articles = data.get("articles", [])
    # 转换为与 NewsAPI 相似的格式
    formatted = []
    for art in articles:
        formatted.append({
            "title": art["title"],
            "description": art["description"],
            "url": art["url"],
            "source": {"name": art["source"]["name"]},
            "publishedAt": art["publishedAt"]
        })
    return formatted