"""
fact_opinion.py - 事实与观点分离（使用 Qwen3-235B-A22B）

功能：
- 从新闻内容中提取定量事实（quantitative facts）
- 从新闻内容中提取定性事实（qualitative facts）
- 从新闻内容中提取观点（opinions）
- 返回结构化的事实和观点数据
"""

import os
import json
import re
from typing import List, Dict, Optional
from dotenv import load_dotenv
import httpx
from loguru import logger

# 加载 .env 文件
load_dotenv()


class FactOpinionError(Exception):
    """事实观点分离模块异常"""
    pass


def _build_extraction_prompt(title: str, description: str, url: str) -> str:
    """
    构建 Qwen 的事实与观点提取提示词
    
    参数：
    - title: 新闻标题
    - description: 新闻描述
    - url: 新闻链接
    
    返回：
    - 提示词字符串
    """
    
    prompt = f"""Analyze the following news article and extract facts and opinions.

Article Title: {title}

Article Content: {description}

Article URL: {url}

Please provide a structured analysis with:

1. **Quantitative Facts**: Specific numbers, percentages, dates, statistics, measurements
   - List each fact as a separate item
   - Include the numerical value and context

2. **Qualitative Facts**: Non-numerical observations, descriptions, events, relationships
   - List objective facts that can be verified
   - Avoid subjective statements

3. **Opinions**: Subjective statements, predictions, interpretations, recommendations
   - Identify clearly stated or implied opinions
   - Note who expressed the opinion (if mentioned)

Return the analysis as a valid JSON object with this exact structure:
{{
  "quantitative_facts": [
    {{"fact": "specific number or statistic", "context": "brief context"}},
    ...
  ],
  "qualitative_facts": [
    {{"fact": "observable fact or event", "context": "brief context"}},
    ...
  ],
  "opinions": [
    {{"opinion": "subjective statement", "source": "who said it or 'author'" }},
    ...
  ]
}}

Important rules:
- Return ONLY valid JSON, no markdown formatting
- Be objective when classifying facts vs opinions
- Extract all significant facts and opinions
- If a category is empty, use an empty array []
- Ensure facts are verifiable and specific
- Separate distinct facts into different items
"""
    
    return prompt


def process_article(
    news_item: Dict,
    temperature: float = 0.3
) -> Dict:
    """
    处理单条新闻，提取事实和观点
    
    参数：
    - news_item: 新闻字典（来自 filter.py）
    - temperature: 采样温度，默认 0.3 (中等确定性)
    
    返回：
    - Dict: 包含原始新闻信息 + 提取的事实和观点
    
    异常：
    - FactOpinionError: API 调用或处理失败时抛出
    """
    
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise FactOpinionError("❌ DASHSCOPE_API_KEY not found in .env file")
    
    title = news_item.get("title", "")
    description = news_item.get("description", "")
    url = news_item.get("url", "")
    
    if not title or not description:
        raise FactOpinionError("❌ News item missing title or description")
    
    # 构建提示词
    prompt = _build_extraction_prompt(title, description, url)
    
    logger.debug(f"🔍 Processing: {title[:50]}...")
    
    try:
        # 调用 DashScope API（阿里云灵积）
        # 使用 httpx 库进行 HTTP 请求
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
                        "content": prompt
                    }
                ]
            },
            "parameters": {
                "temperature": temperature,
                "max_tokens": 2000,
            }
        }
        
        response = client.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise FactOpinionError(f"❌ DashScope API error: {response.status_code} - {response.text}")
        
        response_data = response.json()
        
        # 检查响应中是否有 output 字段
        if "output" not in response_data:
            raise FactOpinionError(f"❌ DashScope API returned invalid format: {response_data}")
        
        # 提取文本内容
        output = response_data.get("output", {})
        choices = output.get("choices", [])
        
        if not choices:
            raise FactOpinionError("❌ DashScope API returned empty choices")
        
        response_text = choices[0].get("message", {}).get("content", "")
        
        logger.debug(f"📝 DashScope response received: {len(response_text)} chars")
        
        client.close()
        
    except httpx.RequestError as e:
        raise FactOpinionError(f"❌ Failed to call DashScope API: {str(e)}")
    except Exception as e:
        raise FactOpinionError(f"❌ Unexpected error calling DashScope: {str(e)}")
    
    # 解析 JSON 响应
    try:
        # 清理响应文本
        response_text = response_text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        response_text = response_text.strip()
        extraction = json.loads(response_text)
        
        logger.debug(f"✅ Parsed extraction results")
        
    except json.JSONDecodeError as e:
        raise FactOpinionError(f"❌ Failed to parse DashScope JSON response: {str(e)}\nResponse: {response_text}")
    
    # 验证提取结果的结构
    if not isinstance(extraction, dict):
        raise FactOpinionError("❌ Extraction result is not a JSON object")
    
    # 合并原始新闻信息与提取结果
    result = {
        **news_item,
        "quantitative_facts": extraction.get("quantitative_facts", []),
        "qualitative_facts": extraction.get("qualitative_facts", []),
        "opinions": extraction.get("opinions", []),
    }
    
    return result


def process(
    news_items: List[Dict],
    temperature: float = 0.3
) -> List[Dict]:
    """
    批量处理新闻，提取事实和观点
    
    参数：
    - news_items: 筛选后的新闻列表（来自 filter.py）
    - temperature: 采样温度，默认 0.3
    
    返回：
    - List[Dict]: 包含提取结果的新闻列表
    
    异常：
    - FactOpinionError: 处理失败时抛出
    """
    
    if not news_items:
        logger.warning("⚠️  No news items to process")
        return []
    
    logger.info(f"📚 Processing {len(news_items)} articles for fact-opinion extraction")
    
    processed_news = []
    failed_count = 0
    
    for i, news in enumerate(news_items, 1):
        try:
            result = process_article(news, temperature=temperature)
            processed_news.append(result)
            
            fact_count = len(result.get("quantitative_facts", []))
            opinion_count = len(result.get("opinions", []))
            logger.info(f"✓ [{i}/{len(news_items)}] {news['title'][:40]}... "
                       f"({fact_count} facts, {opinion_count} opinions)")
            
        except FactOpinionError as e:
            logger.warning(f"✗ [{i}/{len(news_items)}] Failed to process: {news['title'][:40]}... - {e}")
            failed_count += 1
        except Exception as e:
            logger.error(f"✗ [{i}/{len(news_items)}] Unexpected error: {str(e)}")
            failed_count += 1
    
    logger.info(f"📊 Processing complete: {len(processed_news)}/{len(news_items)} "
               f"articles successfully processed ({failed_count} failed)")
    
    return processed_news


if __name__ == "__main__":
    # 测试代码
    try:
        # 导入前面的模块
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent / "modules"))
        from fetcher import fetch_news
        from filter import filter_news
        
        # 获取原始新闻
        print("📰 Fetching news...\n")
        raw_news = fetch_news()
        
        if not raw_news:
            print("❌ No news to process")
            exit(1)
        
        # 筛选新闻
        print("🔍 Filtering news...\n")
        filtered = filter_news(raw_news)
        
        if not filtered:
            print("❌ No news passed filtering")
            exit(1)
        
        # 提取事实和观点（只处理前 2 条作为测试）
        print(f"💡 Extracting facts and opinions from {min(2, len(filtered))} articles...\n")
        test_articles = filtered[:2]
        
        analyzed = process(test_articles)
        
        print(f"\n✅ Extraction complete!\n")
        
        # 打印结果示例
        for i, item in enumerate(analyzed[:1], 1):
            print(f"--- 文章 {i} ---")
            print(f"标题: {item['title']}")
            print(f"\n📊 定量事实 ({len(item.get('quantitative_facts', []))}):")
            for fact in item.get('quantitative_facts', [])[:2]:
                print(f"  • {fact.get('fact', '')} ({fact.get('context', '')})")
            
            print(f"\n📖 定性事实 ({len(item.get('qualitative_facts', []))}):")
            for fact in item.get('qualitative_facts', [])[:2]:
                print(f"  • {fact.get('fact', '')} ({fact.get('context', '')})")
            
            print(f"\n💭 观点 ({len(item.get('opinions', []))}):")
            for opinion in item.get('opinions', [])[:2]:
                print(f"  • {opinion.get('opinion', '')} (来源: {opinion.get('source', 'N/A')})")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Test failed")
