"""
test_fact_opinion_small.py - 用小批量新闻测试 fact_opinion.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "modules"))

from fact_opinion import process

# 模拟从 filter 获取的新闻数据（1 条）
test_news = [
    {
        "title": "AI Ethics in Legal System: New Standards for AI-Generated Evidence",
        "description": "A federal judge in North Carolina has formally reprimanded an attorney who as a U.S. prosecutor used AI-generated legal research without proper disclosure. This case marks the first major ruling on AI transparency in courtrooms. The judge stated that AI systems must be explicitly disclosed when used in legal proceedings. Industry experts predict this will set a precedent for other jurisdictions.",
        "url": "https://www.reuters.com/legal/ai-evidence/",
        "source_name": "Reuters",
        "published_at": "2026-04-28T21:08:52Z",
        "is_worth_reading": True,
        "authority_score": 0.85,
        "assessment_reason": "High quality legal news from reputable source"
    }
]

print(f"📚 Testing fact_opinion.py with {len(test_news)} news article...\n")

try:
    analyzed = process(test_news)
    
    print(f"\n✅ Processing complete!\n")
    
    if analyzed:
        item = analyzed[0]
        
        print("=" * 70)
        print(f"\n📝 Article: {item['title']}")
        print(f"来源: {item['source_name']}")
        print(f"权威分: {item['authority_score']:.2f}\n")
        
        # 显示定量事实
        quantitative = item.get('quantitative_facts', [])
        print(f"📊 定量事实 ({len(quantitative)}):")
        if quantitative:
            for fact in quantitative:
                print(f"   • {fact.get('fact', '')} | 背景: {fact.get('context', '')}")
        else:
            print("   (无定量事实)")
        
        # 显示定性事实
        qualitative = item.get('qualitative_facts', [])
        print(f"\n📖 定性事实 ({len(qualitative)}):")
        if qualitative:
            for fact in qualitative:
                print(f"   • {fact.get('fact', '')} | 背景: {fact.get('context', '')}")
        else:
            print("   (无定性事实)")
        
        # 显示观点
        opinions = item.get('opinions', [])
        print(f"\n💭 观点 ({len(opinions)}):")
        if opinions:
            for opinion in opinions:
                print(f"   • {opinion.get('opinion', '')} | 来源: {opinion.get('source', 'N/A')}")
        else:
            print("   (无观点)")
        
        print("\n" + "=" * 70)
    else:
        print("⚠️  No articles processed")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
