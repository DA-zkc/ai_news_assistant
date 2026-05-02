#!/usr/bin/env python3
"""
集成测试 - 验证完整的 AI 新闻助手流程
"""

import os
from datetime import datetime
from modules import fetcher, filter, fact_opinion, core_event, merger, output

def test_full_pipeline():
    """测试完整的处理流程"""
    print("🚀 Starting full pipeline integration test...")

    try:
        # 1. 获取新闻
        print("\n📡 [1/6] Fetching news...")
        raw_news = fetcher.fetch_news()
        print(f"✅ Retrieved {len(raw_news)} articles")

        if not raw_news:
            print("❌ No news retrieved, stopping test")
            return

        # 2. 质量筛选
        print("\n🔍 [2/6] Filtering news...")
        filtered_news = filter.filter_news(raw_news)
        print(f"✅ Filtered to {len(filtered_news)} quality articles")

        if not filtered_news:
            print("❌ No news passed filtering, stopping test")
            return

        # 3. 事实/意见提取
        print("\n🧠 [3/6] Extracting facts and opinions...")
        analyzed_news = fact_opinion.process(filtered_news)
        print(f"✅ Analyzed {len(analyzed_news)} articles")

        # 4. 核心事件提取
        print("\n🎯 [4/6] Extracting core events...")
        events = core_event.extract(analyzed_news)
        print(f"✅ Extracted {len(events)} core events")

        if not events:
            print("❌ No events extracted, stopping test")
            return

        # 5. 事件合并
        print("\n🔀 [5/6] Merging similar events...")
        merged_events = merger.merge_and_score(events, eps=0.3, use_qwen_description=False)
        print(f"✅ Merged into {len(merged_events)} events")

        # 6. 生成输出
        print("\n📝 [6/6] Generating Markdown output...")
        today = datetime.now().strftime("%Y-%m-%d")
        markdown = output.generate_markdown(merged_events, date=today)

        # 保存结果
        with open("integration_test_output.md", "w", encoding="utf-8") as f:
            f.write(markdown)

        print("\n✅ Integration test completed successfully!")
        print(f"📄 Output saved to: integration_test_output.md")
        print(f"📊 Final result: {len(merged_events)} merged events")

        # 显示前几个事件
        print("\n📋 Top events:")
        for i, event in enumerate(merged_events[:3], 1):
            print(f"{i}. {event['unified_event']} (score: {event['reliability_score']:.2f})")

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_pipeline()