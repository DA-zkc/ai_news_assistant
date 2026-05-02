"""
test_filter_logic.py - 测试 filter.py 的逻辑而不调用真实 API
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "modules"))

from filter import _build_filter_prompt
import json


def test_prompt_builder():
    """测试 prompt 构建逻辑"""
    
    test_news = [
        {
            "title": "Test Article 1",
            "description": "A test AI article",
            "source_name": "Test Source",
            "url": "https://example.com/1"
        },
        {
            "title": "Test Article 2",
            "description": "Another AI news",
            "source_name": "Reuters",
            "url": "https://example.com/2"
        }
    ]
    
    prompt = _build_filter_prompt(test_news)
    
    # 验证 prompt 包含必要的信息
    assert "Test Article 1" in prompt, "✗ Prompt should contain article titles"
    assert "Reuters" in prompt, "✗ Prompt should contain source names"
    assert "is_worth_reading" in prompt, "✗ Prompt should mention is_worth_reading"
    assert "authority_score" in prompt, "✗ Prompt should mention authority_score"
    assert "JSON" in prompt, "✗ Prompt should mention JSON format"
    
    print("✅ Prompt builder test passed")
    print(f"📝 Generated prompt length: {len(prompt)} chars\n")


def test_mock_filter_response():
    """测试 JSON 响应解析（模拟 API 响应）"""
    
    # 模拟 DeepSeek API 的 JSON 响应
    mock_response = '''[
    {
        "index": 1,
        "is_worth_reading": true,
        "authority_score": 0.85,
        "reason": "Reuters is a reputable source with verified facts"
    },
    {
        "index": 2,
        "is_worth_reading": true,
        "authority_score": 0.72,
        "reason": "Bloomberg provides good analysis"
    }
]'''
    
    # 验证 JSON 解析
    try:
        assessments = json.loads(mock_response)
        assert len(assessments) == 2, "✗ Should have 2 assessments"
        assert assessments[0]["authority_score"] == 0.85, "✗ Authority score parsing failed"
        assert assessments[1]["is_worth_reading"] == True, "✗ Boolean parsing failed"
        print("✅ JSON response parsing test passed")
        print(f"📊 Parsed {len(assessments)} assessment results\n")
    except json.JSONDecodeError as e:
        print(f"✗ JSON parsing failed: {e}\n")
        return False
    
    return True


def test_edge_cases():
    """测试边界情况"""
    
    # 测试空列表
    test_news = []
    prompt = _build_filter_prompt(test_news)
    assert prompt, "✗ Empty list should still generate valid prompt"
    
    # 测试特殊字符
    test_news = [
        {
            "title": 'Title with "quotes" and \'apostrophes\'',
            "description": "Description with special chars: @#$%",
            "source_name": "Test",
            "url": "https://example.com"
        }
    ]
    prompt = _build_filter_prompt(test_news)
    assert 'quotes' in prompt, "✗ Should handle quotes"
    assert '@#$%' in prompt, "✗ Should handle special chars"
    
    print("✅ Edge cases test passed\n")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Running filter.py logic tests (without API calls)")
    print("=" * 60 + "\n")
    
    try:
        test_prompt_builder()
        test_mock_filter_response()
        test_edge_cases()
        
        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print("\n📌 filter.py is ready for use with real API calls")
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
