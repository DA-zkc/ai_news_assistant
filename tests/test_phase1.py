# test_phase1.py
from utils.api_clients import (
    call_deepseek_flash,
    call_deepseek_pro,
    call_qwen,
    fetch_news_from_api
)
from loguru import logger

def test_gnews_api():
    print("\n===== 测试 GNewsAPI =====")
    articles = fetch_news_from_api(page_size=5)
    if articles:
        for i, art in enumerate(articles[:3], 1):
            print(f"{i}. {art['title']} - {art['source']['name']}")
    else:
        print("❌ 未获取到新闻，请检查 API Key 或网络")

def test_deepseek_flash():
    print("\n===== 测试 DeepSeek-V4-flash =====")
    messages = [
        {"role": "system", "content": "你是一个AI助手，只输出JSON。"},
        {"role": "user", "content": "请输出 {'test': 'Hello from DeepSeek flash'}"}
    ]
    result = call_deepseek_flash(messages)
    print("响应内容:", result)

def test_deepseek_pro():
    print("\n===== 测试 DeepSeek-V4-pro =====")
    messages = [
        {"role": "system", "content": "你是一个分析专家。"},
        {"role": "user", "content": "请用JSON输出 {'test': 'DeepSeek pro working'}"}
    ]
    result = call_deepseek_pro(messages)
    print("响应内容:", result)

def test_qwen():
    print("\n===== 测试 Qwen3-235B-A22B =====")
    messages = [
        {"role": "system", "content": "你是一个助理，只输出JSON。"},
        {"role": "user", "content": "请输出 {'test': 'Qwen is ready'}"}
    ]
    result = call_qwen(messages)
    print("响应内容:", result)

if __name__ == "__main__":
    logger.add("test.log", rotation="1 MB")
    test_gnews_api()
    test_deepseek_flash()
    test_deepseek_pro()
    test_qwen()
    print("\n✅ 阶段一测试完成。若以上均有输出（非空、无报错），则通过验收标准。")