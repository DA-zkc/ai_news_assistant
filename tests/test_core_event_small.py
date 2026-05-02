"""
test_core_event_small.py - 用小批量新闻测试 core_event.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "modules"))

from core_event import extract

# 模拟从 fact_opinion 获取的新闻数据（1 条）
test_news = [
    {
        "title": "DeepSeek Releases V4-Pro Model with Extended Thinking Capabilities",
        "description": "DeepSeek announced a new AI model with advanced reasoning capabilities using extended thinking mode.",
        "url": "https://example.com",
        "source_name": "Tech News",
        "published_at": "2026-04-29T12:00:00Z",
        "is_worth_reading": True,
        "authority_score": 0.8,
        "quantitative_facts": [
            {"fact": "New model released", "context": "Product release"}
        ],
        "qualitative_facts": [
            {"fact": "Model includes extended thinking mode", "context": "New feature"},
            {"fact": "Advanced reasoning capabilities added", "context": "Technical capability"}
        ],
        "opinions": [
            {"opinion": "This represents significant advancement in AI reasoning", "source": "Industry analyst"},
            {"opinion": "Extended thinking enables better problem solving", "source": "AI researcher"}
        ]
    }
]

print(f"🎯 Testing core_event.py with {len(test_news)} news article...\n")
print("⏳ Note: First-time API call may take 30-60+ seconds due to model reasoning\n")

try:
    # 使用扩展思考模式（这会较慢）
    extracted = extract(test_news, use_extended_thinking=True)
    
    print(f"\n✅ Core event extraction complete!\n")
    
    if extracted:
        item = extracted[0]
        
        print("=" * 70)
        print(f"\n📝 Article: {item['title']}")
        print(f"来源: {item['source_name']}")
        print(f"权威分: {item['authority_score']:.2f}\n")
        
        # 显示核心事件
        print(f"📌 核心事件:")
        print(f"   {item.get('core_event', 'N/A')}\n")
        
        # 显示接受率
        acceptance_rate = item.get('acceptance_rate', 0.0)
        print(f"🎯 接受率: {acceptance_rate:.2f}")
        if acceptance_rate >= 0.8:
            certainty = "非常高"
        elif acceptance_rate >= 0.6:
            certainty = "高"
        elif acceptance_rate >= 0.4:
            certainty = "中等"
        else:
            certainty = "低"
        print(f"   确定性: {certainty}\n")
        
        # 显示推理
        print(f"💭 推理:")
        print(f"   {item.get('event_reasoning', 'N/A')}\n")
        
        print("=" * 70)
    else:
        print("⚠️  No articles processed")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
