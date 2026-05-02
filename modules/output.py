"""
output.py - 生成 Markdown 格式的新闻输出

功能：
- 按可信度分数排序事件
- 调用 DeepSeek-V4-flash 生成优美的 Markdown 格式
- 返回完整的 Markdown 字符串
"""

import os
from typing import List, Dict
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from loguru import logger

# 加载 .env 文件
load_dotenv()


class OutputError(Exception):
    """输出模块异常"""
    pass


def _build_markdown_generation_prompt(
    merged_events: List[Dict],
    date: str
) -> str:
    """
    构建 Markdown 生成提示词
    
    参数：
    - merged_events: 合并后的事件列表
    - date: 日期字符串 YYYY-MM-DD
    
    返回：
    - 提示词字符串
    """
    
    # 格式化事件信息
    events_text = ""
    for i, event in enumerate(merged_events, 1):
        event_desc = event["unified_event"]
        reliability = event["reliability_score"]
        sources = ", ".join(event["sources"])
        source_count = event["source_count"]
        
        events_text += f"""
Event {i}:
- Description: {event_desc}
- Reliability Score: {reliability:.2f}/1.00
- Source Count: {source_count}
- Sources: {sources}
- Average Authority: {event['avg_authority_score']:.2f}
- Average Acceptance: {event['avg_acceptance_rate']:.2f}
"""
    
    prompt = f"""You are a professional news editor. Based on the following AI news events from {date}, generate a beautiful and informative Markdown document.

**News Events Data:**
{events_text}

Please generate a Markdown document with the following structure:

1. **Header**: Title "AI 要闻摘要" with date {date}
2. **Summary**: Brief overview of today's AI news (2-3 sentences)
3. **News Events**: For each event, create a section with:
   - Event number and title (auto-generate a catchy title from the event description)
   - Event description
   - Reliability indicator (star rating based on score: ⭐⭐⭐⭐⭐ for 0.9+, etc.)
   - Source information
4. **Footer**: "---" and "Report generated on {date}"

Style requirements:
- Use clear, professional language
- Make event titles concise and informative
- Use emoji and formatting for better readability
- Organize by reliability (highest first)
- English text is acceptable for technical terms

Return ONLY the Markdown content, no additional text or code blocks.
"""
    
    return prompt


def generate_markdown(
    merged_events: List[Dict],
    date: str = None,
    temperature: float = 0.2
) -> str:
    """
    使用 DeepSeek-V4-flash 生成 Markdown
    
    参数：
    - merged_events: 合并后的事件列表（来自 merger.py）
    - date: 日期字符串 YYYY-MM-DD，默认今天
    - temperature: 采样温度，默认 0.2（低温度=更一致）
    
    返回：
    - str: Markdown 格式的文本
    
    异常：
    - OutputError: 生成失败时抛出
    """
    
    if not merged_events:
        logger.warning("⚠️  No events to generate markdown")
        return ""
    
    # 设置默认日期
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    api_base = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    
    if not api_key:
        raise OutputError("❌ DEEPSEEK_API_KEY not found in .env file")
    
    logger.info(f"📝 Generating Markdown for {len(merged_events)} events (date: {date})")
    
    # 初始化 DeepSeek 客户端
    client = OpenAI(
        api_key=api_key,
        base_url=api_base
    )
    
    # 构建提示词
    prompt = _build_markdown_generation_prompt(merged_events, date)
    
    try:
        # 调用 DeepSeek-V4-flash API
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=temperature,
            max_tokens=4000
        )
        
        markdown_content = response.choices[0].message.content
        logger.info(f"✅ Generated Markdown ({len(markdown_content)} chars)")
        
    except Exception as e:
        raise OutputError(f"❌ Failed to generate Markdown: {str(e)}")
    
    return markdown_content


def format_event_table(merged_events: List[Dict]) -> str:
    """
    生成事件统计表格（作为 Markdown 补充）
    
    参数：
    - merged_events: 合并后的事件列表
    
    返回：
    - str: 表格 Markdown
    """
    
    if not merged_events:
        return ""
    
    table = "| 排名 | 事件 | 可信度 | 来源数 | 平均权威分 |\n"
    table += "|------|------|--------|--------|----------|\n"
    
    for i, event in enumerate(merged_events, 1):
        event_preview = event["unified_event"][:40] + "..." if len(event["unified_event"]) > 40 else event["unified_event"]
        
        # 根据可信度生成星级
        score = event["reliability_score"]
        stars = int(score * 5)
        star_rating = "⭐" * stars + "☆" * (5 - stars)
        
        table += f"| {i} | {event_preview} | {score:.2f} {star_rating} | {event['source_count']} | {event['avg_authority_score']:.2f} |\n"
    
    return table


if __name__ == "__main__":
    # 测试代码
    try:
        # 模拟合并后的事件数据
        test_merged_events = [
            {
                "unified_event": "OpenAI releases GPT-4 with enhanced reasoning capabilities",
                "reliability_score": 0.88,
                "source_count": 2,
                "sources": ["TechCrunch", "Reuters"],
                "avg_authority_score": 0.82,
                "avg_acceptance_rate": 0.86
            },
            {
                "unified_event": "New AI safety research reveals potential risks in language models",
                "reliability_score": 0.82,
                "source_count": 1,
                "sources": ["MIT News"],
                "avg_authority_score": 0.9,
                "avg_acceptance_rate": 0.75
            },
            {
                "unified_event": "Google announces new AI model for code generation",
                "reliability_score": 0.75,
                "source_count": 1,
                "sources": ["InfoQ"],
                "avg_authority_score": 0.75,
                "avg_acceptance_rate": 0.75
            }
        ]
        
        print("📝 Testing output.py with test events...\n")
        
        # 生成 Markdown
        markdown = generate_markdown(
            test_merged_events,
            date="2026-04-29"
        )
        
        print("✅ Markdown generation complete!\n")
        print("=" * 70)
        print(markdown)
        print("=" * 70)
        
        # 生成统计表格
        print("\n📊 Event Statistics Table:\n")
        table = format_event_table(test_merged_events)
        print(table)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Test failed")
