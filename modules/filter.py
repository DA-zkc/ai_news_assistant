"""
filter.py - 使用 DeepSeek-V4-flash 进行初步新闻筛选

功能：
- 评估新闻的价值：is_worth_reading (True/False)
- 评分新闻的权威性：authority_score (0.0 - 1.0)
- 返回筛选后的新闻列表
"""

import os
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv
from openai import OpenAI
from loguru import logger

# 加载 .env 文件
load_dotenv()


class FilterError(Exception):
    """筛选模块异常"""
    pass


def _build_filter_prompt(news_items: List[Dict]) -> str:
    """
    构建 DeepSeek 的筛选提示词
    
    参数：
    - news_items: 新闻列表
    
    返回：
    - 提示词字符串
    """
    
    # 格式化新闻列表用于提示词
    news_text = ""
    for i, news in enumerate(news_items, 1):
        news_text += f"""
【新闻 {i}】
标题: {news['title']}
描述: {news['description']}
来源: {news['source_name']}
链接: {news['url']}
"""
    
    prompt = f"""You are an AI news quality assessor. Your task is to evaluate a list of AI-related news articles and determine their worth and credibility.

For each news article, you must provide:
1. **is_worth_reading**: Boolean (true/false) - Whether this news is worth reading based on:
   - Relevance to AI field
   - Actual news value (not just hype or opinion)
   - Uniqueness and informativeness
   - Impact potential

2. **authority_score**: Number between 0.0 and 1.0 - Credibility score based on:
   - Source reputation (major outlets like Reuters, Bloomberg, etc. should be higher)
   - Technical accuracy and depth
   - Balance and objectivity
   - Verifiable facts

Below are the news articles to evaluate:

{news_text}

Return your assessment as a valid JSON array with this exact structure:
[
  {{
    "index": 1,
    "is_worth_reading": true,
    "authority_score": 0.85,
    "reason": "Brief reason for the rating"
  }},
  ...
]

Important rules:
- Return ONLY valid JSON, no markdown formatting
- Each article must have an index matching its position in the list
- authority_score must be a decimal number between 0.0 and 1.0
- Be objective and consistent in your assessment
- Major reputable news sources (Reuters, Bloomberg, AP, etc.) typically get 0.7+
- Sensationalized or unverified claims get lower scores
"""
    
    return prompt


def filter_news(
    news_items: List[Dict],
    temperature: float = 0.2,
    min_authority_score: float = 0.0
) -> List[Dict]:
    """
    使用 DeepSeek-V4-flash 筛选新闻
    
    参数：
    - news_items: 原始新闻列表 (来自 fetcher.py)
    - temperature: 采样温度，默认 0.2 (低温度=更确定)
    - min_authority_score: 最低权威分数阈值，低于此值的新闻将被过滤
    
    返回：
    - List[Dict]: 筛选后的新闻列表，每条包含：
        - title, description, url, source_name, published_at (原字段)
        - is_worth_reading, authority_score (新增字段)
    
    异常：
    - FilterError: API 调用或处理失败时抛出
    """
    
    if not news_items:
        logger.warning("⚠️  No news items to filter")
        return []
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    api_base = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    
    if not api_key:
        raise FilterError("❌ DEEPSEEK_API_KEY not found in .env file")
    
    # 初始化 OpenAI 客户端 (DeepSeek 兼容 OpenAI SDK)
    client = OpenAI(
        api_key=api_key,
        base_url=api_base
    )
    
    logger.info(f"🔍 Filtering {len(news_items)} news items with DeepSeek-V4-flash")
    
    # 构建提示词
    prompt = _build_filter_prompt(news_items)
    
    try:
        # 调用 DeepSeek API
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=temperature,
            max_tokens=2000,
            response_format={
                "type": "json_object"
            } if hasattr(client.chat.completions.create, '__wrapped__') else None
        )
        
        response_text = response.choices[0].message.content
        logger.debug(f"📝 DeepSeek response received: {len(response_text)} chars")
        
    except Exception as e:
        raise FilterError(f"❌ Failed to call DeepSeek API: {str(e)}")
    
    # 解析 JSON 响应
    try:
        # 尝试清理响应文本 (移除 markdown 代码块标记)
        if response_text.startswith("```"):
            # 移除 ```json 或 ``` 标记
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        response_text = response_text.strip()
        assessments = json.loads(response_text)
        
        if not isinstance(assessments, list):
            raise ValueError("Response is not a JSON array")
        
        logger.info(f"✅ Parsed {len(assessments)} assessments from DeepSeek")
        
    except json.JSONDecodeError as e:
        raise FilterError(f"❌ Failed to parse DeepSeek JSON response: {str(e)}\nResponse: {response_text}")
    
    # 整合原始新闻数据与评估结果
    filtered_news = []
    
    for i, news in enumerate(news_items):
        # 找到对应的评估
        assessment = None
        for assess in assessments:
            if assess.get("index") == i + 1:
                assessment = assess
                break
        
        if not assessment:
            logger.warning(f"⚠️  No assessment found for news item {i + 1}, skipping")
            continue
        
        # 检查是否值得阅读
        is_worth_reading = assessment.get("is_worth_reading", False)
        authority_score = assessment.get("authority_score", 0.0)
        
        if not isinstance(authority_score, (int, float)):
            try:
                authority_score = float(authority_score)
            except (ValueError, TypeError):
                authority_score = 0.0
        
        # 确保 authority_score 在 0-1 范围内
        authority_score = max(0.0, min(1.0, authority_score))
        
        # 应用最低权威分数阈值
        if authority_score < min_authority_score:
            logger.debug(f"⚛️  Filtering out: {news['title'][:50]}... (score: {authority_score})")
            continue
        
        # 组合原始数据与评估结果
        filtered_item = {
            **news,
            "is_worth_reading": is_worth_reading,
            "authority_score": authority_score,
            "assessment_reason": assessment.get("reason", "")
        }
        
        if is_worth_reading:
            filtered_news.append(filtered_item)
            logger.debug(f"✓ Kept: {news['title'][:50]}... (score: {authority_score:.2f})")
        else:
            logger.debug(f"✗ Filtered out: {news['title'][:50]}... (not worth reading)")
    
    logger.info(f"📊 Filtering complete: {len(filtered_news)} / {len(news_items)} articles kept")
    
    return filtered_news


if __name__ == "__main__":
    # 添加模块路径用于导入
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from fetcher import fetch_news
    
    try:
        # 获取原始新闻
        raw_news = fetch_news()
        
        if not raw_news:
            print("❌ No raw news to filter")
            exit(1)
        
        print(f"\n📰 Got {len(raw_news)} raw articles, filtering...\n")
        
        # 筛选新闻
        filtered = filter_news(raw_news)
        
        print(f"\n✅ Filtered to {len(filtered)} articles\n")
        
        # 打印筛选结果示例
        for i, item in enumerate(filtered[:3], 1):
            print(f"--- 文章 {i} ---")
            print(f"标题: {item['title']}")
            print(f"来源: {item['source_name']}")
            print(f"权威分: {item['authority_score']:.2f}")
            print(f"值得阅读: {item['is_worth_reading']}")
            print(f"原因: {item['assessment_reason']}")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Test failed")
