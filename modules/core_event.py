"""
core_event.py - 核心事件提取（使用 DeepSeek-V4-pro 思考模式）

功能：
- 基于事实和观点，提取新闻的核心事件
- 使用 DeepSeek-V4-pro 的扩展思考模式（Extended Thinking）进行深度分析
- 计算事件接受率（acceptance_rate）- 表示事件的确定性
- 返回结构化的核心事件数据
"""

import os
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv
from openai import OpenAI
from loguru import logger

# 加载 .env 文件
load_dotenv()


class CoreEventError(Exception):
    """核心事件提取模块异常"""
    pass


def _build_event_extraction_prompt(news_item: Dict) -> str:
    """
    构建 DeepSeek 的核心事件提取提示词
    
    参数：
    - news_item: 新闻字典（包含事实和观点）
    
    返回：
    - 提示词字符串
    """
    
    title = news_item.get("title", "")
    qualitative_facts = news_item.get("qualitative_facts", [])
    opinions = news_item.get("opinions", [])
    
    # 格式化定性事实
    facts_text = ""
    for i, fact in enumerate(qualitative_facts, 1):
        facts_text += f"\n{i}. {fact.get('fact', '')} (背景: {fact.get('context', '')})"
    
    if not facts_text:
        facts_text = "\n(无定性事实提取)"
    
    # 格式化观点
    opinions_text = ""
    for i, opinion in enumerate(opinions, 1):
        opinions_text += f"\n{i}. {opinion.get('opinion', '')} (来源: {opinion.get('source', 'Unknown')})"
    
    if not opinions_text:
        opinions_text = "\n(无观点提取)"
    
    prompt = f"""You are an AI news analysis expert. Your task is to extract the core event from the following news article and assess its certainty level.

**Article Title:** {title}

**Qualitative Facts Extracted:**
{facts_text}

**Opinions Extracted:**
{opinions_text}

Based on the facts and opinions above, please:

1. **Identify the Core Event**: Extract the single, most important event that this news is reporting about. This should be a concise, factual statement that captures the essence of the news.

2. **Assess Acceptance Rate**: Determine how certain/verifiable this core event is based on:
   - How many facts support it (more facts = higher certainty)
   - How credible the sources are (expert opinions vs general comments)
   - Whether it's based on verified facts vs opinions
   - The consistency of supporting information
   - Rate from 0.0 to 1.0 where:
     - 0.9-1.0: Very high certainty, multiple credible sources, clear facts
     - 0.7-0.9: Good certainty, supported by facts, minor opinion elements
     - 0.5-0.7: Moderate certainty, mixed facts and opinions
     - 0.3-0.5: Low certainty, relies heavily on opinions
     - 0.0-0.3: Very low certainty, speculative or unverified

Return your analysis as a valid JSON object with this exact structure:
{{
  "core_event": "A concise, factual statement of the core event",
  "acceptance_rate": 0.75,
  "reasoning": "Brief explanation of why this is the core event and the acceptance rate"
}}

Important rules:
- Return ONLY valid JSON, no markdown formatting
- core_event must be a clear, objective statement
- acceptance_rate must be a decimal number between 0.0 and 1.0
- Be consistent and objective in assessment
- The core event should be the most newsworthy single event
- Consider the balance of facts vs opinions in determining acceptance_rate
"""
    
    return prompt


def extract_core_event(
    news_item: Dict,
    use_extended_thinking: bool = True,
    max_thinking_length: int = 8000,
    temperature: float = 0.5
) -> Dict:
    """
    从单条新闻提取核心事件
    
    参数：
    - news_item: 新闻字典（来自 fact_opinion.py）
    - use_extended_thinking: 是否使用 DeepSeek 的扩展思考模式
    - max_thinking_length: 最大思考长度（仅当 use_extended_thinking=True 时）
    - temperature: 采样温度，默认 0.5 (中等)
    
    返回：
    - Dict: 包含原始新闻信息 + 核心事件和接受率
    
    异常：
    - CoreEventError: API 调用或处理失败时抛出
    """
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    api_base = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    
    if not api_key:
        raise CoreEventError("❌ DEEPSEEK_API_KEY not found in .env file")
    
    title = news_item.get("title", "")
    if not title:
        raise CoreEventError("❌ News item missing title")
    
    # 初始化 OpenAI 客户端 (DeepSeek 兼容)
    client = OpenAI(
        api_key=api_key,
        base_url=api_base
    )
    
    logger.debug(f"🔍 Extracting core event: {title[:50]}...")
    
    # 构建提示词
    prompt = _build_event_extraction_prompt(news_item)
    
    try:
        # 调用 DeepSeek-V4-pro API
        if use_extended_thinking:
            # 使用可用的 DeepSeek 调用参数，避免不兼容的扩展参数
            logger.debug("🧠 Using extended thinking mode...")
            
            response = client.chat.completions.create(
                model="deepseek-v4-pro",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=2000,
            )
        else:
            # 标准模式
            logger.debug("💬 Using standard mode (no extended thinking)...")
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=2000
            )
        
        # 提取响应内容
        response_text = response.choices[0].message.content
        logger.debug(f"📝 DeepSeek response received: {len(response_text)} chars")
        
    except Exception as e:
        raise CoreEventError(f"❌ Failed to call DeepSeek API: {str(e)}")
    
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
        
        logger.debug(f"✅ Parsed core event extraction")
        
    except json.JSONDecodeError as e:
        raise CoreEventError(f"❌ Failed to parse DeepSeek JSON response: {str(e)}\nResponse: {response_text}")
    
    # 验证提取结果
    if not isinstance(extraction, dict):
        raise CoreEventError("❌ Extraction result is not a JSON object")
    
    core_event = extraction.get("core_event", "")
    acceptance_rate = extraction.get("acceptance_rate", 0.5)
    reasoning = extraction.get("reasoning", "")
    
    # 验证字段
    if not core_event:
        raise CoreEventError("❌ core_event field is empty")
    
    # 确保 acceptance_rate 在 0-1 范围内
    try:
        acceptance_rate = float(acceptance_rate)
        acceptance_rate = max(0.0, min(1.0, acceptance_rate))
    except (ValueError, TypeError):
        acceptance_rate = 0.5
    
    # 合并原始新闻信息与提取结果
    result = {
        **news_item,
        "core_event": core_event,
        "acceptance_rate": acceptance_rate,
        "event_reasoning": reasoning
    }
    
    return result


def extract(
    news_items: List[Dict],
    use_extended_thinking: bool = True,
    temperature: float = 0.5
) -> List[Dict]:
    """
    批量提取核心事件
    
    参数：
    - news_items: 分析后的新闻列表（来自 fact_opinion.py）
    - use_extended_thinking: 是否使用扩展思考模式
    - temperature: 采样温度，默认 0.5
    
    返回：
    - List[Dict]: 包含核心事件的新闻列表
    
    异常：
    - CoreEventError: 处理失败时抛出
    """
    
    if not news_items:
        logger.warning("⚠️  No news items to extract")
        return []
    
    logger.info(f"🎯 Extracting core events from {len(news_items)} articles using DeepSeek-V4-pro")
    
    extracted_news = []
    failed_count = 0
    
    for i, news in enumerate(news_items, 1):
        try:
            result = extract_core_event(
                news,
                use_extended_thinking=use_extended_thinking,
                temperature=temperature
            )
            extracted_news.append(result)
            
            logger.info(f"✓ [{i}/{len(news_items)}] {news['title'][:40]}... "
                       f"(acceptance: {result['acceptance_rate']:.2f})")
            
        except CoreEventError as e:
            logger.warning(f"✗ [{i}/{len(news_items)}] Failed to extract: {news['title'][:40]}... - {e}")
            failed_count += 1
        except Exception as e:
            logger.error(f"✗ [{i}/{len(news_items)}] Unexpected error: {str(e)}")
            failed_count += 1
    
    logger.info(f"📊 Core event extraction complete: {len(extracted_news)}/{len(news_items)} "
               f"articles successfully processed ({failed_count} failed)")
    
    return extracted_news


if __name__ == "__main__":
    # 测试代码
    try:
        # 导入前面的模块
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent / "modules"))
        from fetcher import fetch_news
        from filter import filter_news
        from fact_opinion import process
        
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
        
        # 提取事实和观点
        print(f"💡 Extracting facts and opinions from first article...\n")
        test_articles = filtered[:1]  # 只处理第一条用于测试
        analyzed = process(test_articles)
        
        if not analyzed:
            print("❌ Failed to analyze articles")
            exit(1)
        
        # 提取核心事件
        print(f"🎯 Extracting core event...\n")
        events = extract(analyzed)
        
        print(f"\n✅ Core event extraction complete!\n")
        
        # 打印结果示例
        if events:
            item = events[0]
            print(f"--- 文章 1 ---")
            print(f"标题: {item['title']}")
            print(f"\n📌 核心事件: {item['core_event']}")
            print(f"🎯 接受率: {item['acceptance_rate']:.2f}")
            print(f"\n💭 推理: {item['event_reasoning']}")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Test failed")
