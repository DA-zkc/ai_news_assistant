#!/usr/bin/env python3
"""
测试 merger 模块
"""

from modules.merger import merge_and_score

def test_merger():
    # 创建测试数据
    test_events = [
        {
            'core_event': 'OpenAI releases new GPT model',
            'authority_score': 0.8,
            'acceptance_rate': 0.9
        },
        {
            'core_event': 'OpenAI launches GPT-4 update',
            'authority_score': 0.7,
            'acceptance_rate': 0.8
        },
        {
            'core_event': 'Tesla announces new electric vehicle',
            'authority_score': 0.6,
            'acceptance_rate': 0.7
        }
    ]

    try:
        result = merge_and_score(test_events, eps=0.5)
        print('✅ Merger test successful')
        print(f'Result: {len(result)} merged events')
        for event in result:
            print(f'- {event["unified_event"]} (score: {event["reliability_score"]:.2f})')
    except Exception as e:
        print(f'❌ Merger test failed: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_merger()