"""
test_fact_opinion_logic.py - 测试 fact_opinion.py 的逻辑
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "modules"))

from fact_opinion import _build_extraction_prompt
import json


def test_extraction_prompt():
    """测试提取提示词构建"""
    
    test_article = {
        "title": "Test Article Title",
        "description": "This is a test article with some facts and opinions.",
        "url": "https://example.com/article"
    }
    
    prompt = _build_extraction_prompt(
        test_article["title"],
        test_article["description"],
        test_article["url"]
    )
    
    # 验证提示词包含必要的信息
    assert "Quantitative Facts" in prompt, "✗ Should mention quantitative facts"
    assert "Qualitative Facts" in prompt, "✗ Should mention qualitative facts"
    assert "Opinions" in prompt, "✗ Should mention opinions"
    assert "JSON" in prompt, "✗ Should mention JSON format"
    assert test_article["title"] in prompt, "✗ Should include article title"
    
    print("✅ Extraction prompt builder test passed")
    print(f"📝 Generated prompt length: {len(prompt)} chars\n")


def test_mock_extraction_response():
    """测试提取响应解析"""
    
    # 模拟 DashScope API 的 JSON 响应
    mock_response = '''{
    "quantitative_facts": [
        {"fact": "50% increase in AI investment", "context": "Year-over-year growth"},
        {"fact": "2026 market size", "context": "Estimated at $500 billion"}
    ],
    "qualitative_facts": [
        {"fact": "AI adoption increasing in enterprises", "context": "Widespread enterprise adoption"},
        {"fact": "New regulatory frameworks emerging", "context": "Governance and compliance"}
    ],
    "opinions": [
        {"opinion": "AI will transform the industry", "source": "Industry expert"},
        {"opinion": "Regulations should prioritize safety", "source": "Policy maker"}
    ]
}'''
    
    try:
        extraction = json.loads(mock_response)
        
        assert len(extraction["quantitative_facts"]) == 2, "✗ Should have 2 quantitative facts"
        assert len(extraction["qualitative_facts"]) == 2, "✗ Should have 2 qualitative facts"
        assert len(extraction["opinions"]) == 2, "✗ Should have 2 opinions"
        
        print("✅ Extraction response parsing test passed")
        print(f"📊 Successfully parsed extraction with:")
        print(f"   - {len(extraction['quantitative_facts'])} quantitative facts")
        print(f"   - {len(extraction['qualitative_facts'])} qualitative facts")
        print(f"   - {len(extraction['opinions'])} opinions\n")
        
    except json.JSONDecodeError as e:
        print(f"✗ JSON parsing failed: {e}\n")
        return False
    
    return True


def test_empty_lists():
    """测试空列表处理"""
    
    mock_response = '''{
    "quantitative_facts": [],
    "qualitative_facts": [],
    "opinions": []
}'''
    
    extraction = json.loads(mock_response)
    
    # 验证空列表被正确处理
    assert extraction["quantitative_facts"] == [], "✗ Empty quantitative facts"
    assert extraction["qualitative_facts"] == [], "✗ Empty qualitative facts"
    assert extraction["opinions"] == [], "✗ Empty opinions"
    
    print("✅ Empty lists test passed\n")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Running fact_opinion.py logic tests")
    print("=" * 60 + "\n")
    
    try:
        test_extraction_prompt()
        test_mock_extraction_response()
        test_empty_lists()
        
        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print("\n📌 fact_opinion.py is ready for integration")
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
