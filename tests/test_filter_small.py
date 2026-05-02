"""
test_filter_with_small_batch.py - 用小批量新闻测试 filter.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "modules"))

from filter import filter_news

# 模拟从 fetcher 获取的新闻数据（3 条）
test_news = [
    {
        "title": "US prosecutor who lost job over AI-generated errors is rebuked by judge",
        "description": "A federal judge in North Carolina has formally reprimanded an attorney who as a U.S. prosecutor used AI-generated research in court filings without disclosing it.",
        "url": "https://www.reuters.com/legal/...",
        "source_name": "Reuters",
        "published_at": "2026-04-28T21:08:52Z"
    },
    {
        "title": "Elon Musk takes stand in trial vs. Sam Altman that could reshape AI's future",
        "description": "The high-stakes trial revolves around a bitter feud that could reshape the future development of artificial intelligence.",
        "url": "https://www.inquirer.com/news/...",
        "source_name": "The Philadelphia Inquirer",
        "published_at": "2026-04-28T20:11:38Z"
    },
    {
        "title": "India's Real Estate Will Meet the Reality of Agentic AI",
        "description": "The outsourcing industry, India's largest white-collar employer, is a juggernaut that has all but stopped hiring for certain categories of jobs.",
        "url": "https://www.bloomberg.com/opinion/...",
        "source_name": "Bloomberg",
        "published_at": "2026-04-28T20:00:18Z"
    }
]

print(f"📰 Testing filter.py with {len(test_news)} news articles...\n")

try:
    filtered = filter_news(test_news)
    
    print(f"\n✅ Filtering complete!\n")
    print(f"📊 Results: {len(filtered)} / {len(test_news)} articles passed the filter\n")
    
    if filtered:
        print("=" * 70)
        for i, item in enumerate(filtered, 1):
            print(f"\n✓ Article {i}: {item['title']}")
            print(f"  Source: {item['source_name']}")
            print(f"  Authority Score: {item['authority_score']:.2f}")
            print(f"  Worth Reading: {item['is_worth_reading']}")
            print(f"  Reason: {item['assessment_reason']}")
        print("\n" + "=" * 70)
    else:
        print("⚠️  No articles passed the filter")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
