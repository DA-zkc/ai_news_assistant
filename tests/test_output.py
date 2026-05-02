#!/usr/bin/env python3
"""
测试 output 模块
"""

from modules.output import generate_markdown

def test_output():
    # 创建测试数据（模拟 merger.py 的输出格式）
    test_events = [
        {
            'unified_event': 'OpenAI releases new GPT model',
            'reliability_score': 0.85,
            'sources': ['TechCrunch', 'Wired'],
            'source_count': 2,
            'avg_authority_score': 0.75,
            'avg_acceptance_rate': 0.82
        },
        {
            'unified_event': 'Tesla announces new electric vehicle',
            'reliability_score': 0.72,
            'sources': ['Reuters'],
            'source_count': 1,
            'avg_authority_score': 0.65,
            'avg_acceptance_rate': 0.78
        }
    ]

    try:
        result = generate_markdown(test_events)
        print('✅ Output test successful')
        print('Generated Markdown:')
        print(result)
    except Exception as e:
        print(f'❌ Output test failed: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_output()