"""
fetcher.py - 从 GNewsAPI 获取原始新闻数据

功能：
- 调用 GNewsAPI 获取 AI 相关新闻
- 提取关键字段：title, description, url, source.name, publishedAt
- 返回格式化的新闻列表
"""

import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv
from loguru import logger

# 加载 .env 文件
load_dotenv()


class NewsAPIError(Exception):
    """GNewsAPI 调用异常"""
    pass


def get_api_key(key_name: str) -> str:
    """
    获取API KEY，支持 Streamlit secrets 和环境变量
    
    参数：
    - key_name: 环境变量名
    
    返回：
    - API KEY 字符串
    
    异常：
    - NewsAPIError: 未找到 KEY 时抛出
    """
    try:
        # 尝试从 Streamlit secrets 获取
        import streamlit as st
        if hasattr(st, 'secrets') and key_name in st.secrets:
            return st.secrets[key_name]
    except ImportError:
        # 不在 Streamlit 环境中
        pass
    
    # 从环境变量获取
    api_key = os.getenv(key_name)
    if not api_key:
        raise NewsAPIError(f"❌ {key_name} not found in environment variables or Streamlit secrets")
    
    return api_key


def fetch_news(
    query: str = "artificial intelligence",
    lang: Optional[str] = "en",
    country: Optional[str] = None,
    max_articles: int = 100,
    sort_by: str = "publishedAt",
    date: Optional[str] = None
) -> List[Dict]:
    """
    从 GNewsAPI 获取新闻
    
    参数：
    - query: 搜索关键词 (默认: "artificial intelligence")
    - lang: 语言代码 (默认: "en" - 英文)
    - country: 国家代码 (默认: "us" - 美国)
    - max_articles: 最多获取的新闻条数 (默认: 50)
    - sort_by: 排序方式，可选 "publishedAt" 或 "relevance" (默认: "publishedAt")
    - date: 指定日期 YYYY-MM-DD，若为 None 则查询今天的新闻
    
    返回：
    - List[Dict]: 新闻列表，每条包含 title, description, url, source_name, published_at
    
    异常：
    - NewsAPIError: API 调用失败时抛出
    """
    
    api_key = get_api_key("GNEWS_API_KEY")
    
    # GNewsAPI 端点 (https://gnews.io)
    base_url = "https://gnews.io/api/v4/search"
    
    # 构建参数
    # 如果指定了日期，则查询该日期的新闻；否则查询今天的新闻
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise NewsAPIError(f"❌ Invalid date format: {date}. Use YYYY-MM-DD")
    else:
        target_date = datetime.now()
    
    # GNewsAPI 支持按日期范围筛选
    start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=1)
    
    params = {
        "q": query,
        "max": max_articles,
        "sortby": sort_by,
        "token": api_key,
    }
    if lang:
        params["lang"] = lang
    if country:
        params["country"] = country

    def _fetch_articles(fetch_params):
        logger.info(
            f"📡 Fetching news from GNewsAPI: q='{fetch_params.get('q')}', lang={fetch_params.get('lang', 'any')}, country={fetch_params.get('country', 'global')}, max={fetch_params.get('max')}"
        )
        try:
            response = requests.get(base_url, params=fetch_params, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise NewsAPIError(f"❌ Failed to fetch news from GNewsAPI: {str(e)}")

        try:
            data = response.json()
        except ValueError:
            raise NewsAPIError(f"❌ Invalid JSON response from GNewsAPI: {response.text}")

        if "articles" not in data:
            logger.warning(f"⚠️  No articles found. API response: {data}")
            return []

        articles = data.get("articles", [])
        logger.info(f"✅ Retrieved {len(articles)} articles from GNewsAPI")
        return articles

    articles = _fetch_articles(params)
    
    # 处理和格式化新闻数据
    news_list = []
    for article in articles:
        try:
            news_item = {
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "url": article.get("url", ""),
                "source_name": article.get("source", {}).get("name", "Unknown Source"),
                "published_at": article.get("publishedAt", ""),
            }
            
            # 只保留有标题和描述的新闻
            if news_item["title"] and news_item["description"]:
                news_list.append(news_item)
        except (KeyError, AttributeError) as e:
            logger.warning(f"⚠️  Skipping malformed article: {e}")
            continue
    
    logger.info(f"📰 Processed {len(news_list)} valid articles after filtering")
    return news_list


def fetch_news_for_date(date: str) -> List[Dict]:
    """
    为指定日期获取 AI 新闻（便捷函数）
    
    参数：
    - date: 日期字符串 YYYY-MM-DD
    
    返回：
    - List[Dict]: 新闻列表
    """
    return fetch_news(date=date)


if __name__ == "__main__":
    # 测试代码
    try:
        # 获取今天的新闻
        news = fetch_news()
        
        print(f"\n✅ 获取了 {len(news)} 条新闻\n")
        
        # 打印前3条新闻作为示例
        for i, item in enumerate(news[:3], 1):
            print(f"--- 新闻 {i} ---")
            print(f"标题: {item['title']}")
            print(f"来源: {item['source_name']}")
            print(f"时间: {item['published_at']}")
            print(f"描述: {item['description'][:100]}...")
            print(f"链接: {item['url']}\n")
        
    except NewsAPIError as e:
        print(f"错误: {e}")
    except Exception as e:
        print(f"未知错误: {e}")
        logger.exception("Unexpected error in fetcher")
