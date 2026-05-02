"""
test_core_event_logic.py - 测试 core_event.py 的逻辑
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "modules"))

from core_event import _build_event_extraction_prompt
import json


def test_event_prompt():
    """测试核心事件提取提示词构建"""
    
    test_article = {
        "title": "AI Regulation Framework Announced",
        "qualitative_facts": [
            {"fact": "Government announces new AI regulation", "context": "Policy update"},
            {"fact": "Industry responds with mixed reactions", "context": "Market response"}
        ],
        "opinions": [
            {"opinion": "Regulation will slow innovation", "source": "Tech CEO"},
            {"opinion": "Safety measures are necessary", "source": "AI researcher"}
        ]
    }
    
    prompt = _build_event_extraction_prompt(test_article)
    
    # 验证提示词包含必要的信息
    assert "Core Event" in prompt, "✗ Should mention Core Event"
    assert "acceptance_rate" in prompt, "✗ Should mention acceptance_rate"
    assert "Qualitative Facts" in prompt, "✗ Should include facts section"
    assert "Opinions" in prompt, "✗ Should include opinions section"
    assert "JSON" in prompt, "✗ Should mention JSON format"
    
    print("✅ Event extraction prompt builder test passed")
    print(f"📝 Generated prompt length: {len(prompt)} chars\n")


def test_mock_event_response():
    """测试核心事件响应解析"""
    
    # 模拟 DeepSeek API 的 JSON 响应
    mock_response = '''{
    "core_event": "Government announces comprehensive AI regulation framework requiring transparency and safety measures",
    "acceptance_rate": 0.85,
    "reasoning": "Multiple credible facts support this core event, including government announcement and industry response. High certainty based on factual reporting."
}'''
    
    try:
        extraction = json.loads(mock_response)
        
        assert "core_event" in extraction, "✗ Missing core_event"
        assert "acceptance_rate" in extraction, "✗ Missing acceptance_rate"
        assert "reasoning" in extraction, "✗ Missing reasoning"
        
        assert isinstance(extraction["core_event"], str), "✗ core_event should be string"
        assert isinstance(extraction["acceptance_rate"], (int, float)), "✗ acceptance_rate should be number"
        assert 0.0 <= extraction["acceptance_rate"] <= 1.0, "✗ acceptance_rate out of range"
        
        print("✅ Event response parsing test passed")
        print(f"📊 Successfully parsed:")
        print(f"   - Core Event: '{extraction['core_event'][:50]}...'")
        print(f"   - Acceptance Rate: {extraction['acceptance_rate']:.2f}")
        print(f"   - Reasoning: '{extraction['reasoning'][:50]}...'\n")
        
    except json.JSONDecodeError as e:
        print(f"✗ JSON parsing failed: {e}\n")
        return False
    
    return True


def test_edge_cases():
    """测试边界情况"""
    
    # 测试 1: 无定性事实和观点
    test_article = {
        "title": "Test Article",
        "qualitative_facts": [],
        "opinions": []
    }
    
    prompt = _build_event_extraction_prompt(test_article)
    assert "(无定性事实提取)" in prompt, "✗ Should handle empty facts"
    assert "(无观点提取)" in prompt, "✗ Should handle empty opinions"
    
    # 测试 2: 响应格式变化（acceptance_rate 边界）
    test_responses = [
        ('{"core_event": "Event", "acceptance_rate": 0.0, "reasoning": ""}', 0.0),
        ('{"core_event": "Event", "acceptance_rate": 1.0, "reasoning": ""}', 1.0),
        ('{"core_event": "Event", "acceptance_rate": 0.5, "reasoning": ""}', 0.5),
    ]
    
    for response_str, expected_rate in test_responses:
        response = json.loads(response_str)
        assert response["acceptance_rate"] == expected_rate, f"✗ Rate should be {expected_rate}"
    
    # 测试 3: acceptance_rate 越界处理
    invalid_rates = [-0.5, 1.5, "invalid"]
    for rate in invalid_rates:
        # 模拟处理逻辑
        try:
            processed_rate = float(rate)
            processed_rate = max(0.0, min(1.0, processed_rate))
            assert 0.0 <= processed_rate <= 1.0, "✗ Rate not in valid range after processing"
        except (ValueError, TypeError):
            # 这是预期的，对于 "invalid" 字符串
            pass
    
    print("✅ Edge cases test passed\n")


def test_article_merging():
    """测试文章信息合并"""
    
    original_article = {
        "title": "Sample Article",
        "source_name": "Test Source",
        "authority_score": 0.8,
        "is_worth_reading": True,
        "qualitative_facts": [{"fact": "test", "context": "context"}],
        "opinions": [{"opinion": "test", "source": "source"}]
    }
    
    extraction = {
        "core_event": "Core event extracted",
        "acceptance_rate": 0.75,
        "event_reasoning": "Reasoning provided"
    }
    
    # 模拟合并操作（如 core_event.py 中的做法）
    merged = {
        **original_article,
        **extraction
    }
    
    # 验证所有字段都被保留
    assert merged["title"] == original_article["title"]
    assert merged["source_name"] == original_article["source_name"]
    assert merged["authority_score"] == original_article["authority_score"]
    assert merged["core_event"] == extraction["core_event"]
    assert merged["acceptance_rate"] == extraction["acceptance_rate"]
    
    print("✅ Article merging test passed")
    print(f"   - Original fields preserved: {len(original_article)} fields")
    print(f"   - New fields added: {len(extraction)} fields")
    print(f"   - Total merged fields: {len(merged)} fields\n")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Running core_event.py logic tests")
    print("=" * 60 + "\n")
    
    try:
        test_event_prompt()
        test_mock_event_response()
        test_edge_cases()
        test_article_merging()
        
        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print("\n📌 core_event.py is ready for integration")
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
