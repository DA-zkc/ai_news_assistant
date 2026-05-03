"""
merger.py - 合并相同/相似核心事件

功能：
- 使用 TF-IDF 向量计算事件相似度
- DBSCAN 聚类相似事件
- 为每个簇调用 Qwen 生成最终事件描述
- 计算聚类后事件的可信度分数（reliability_score）
"""

import os
import time
from typing import List, Dict, Tuple
from collections import defaultdict
import numpy as np
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
import httpx
from loguru import logger
import json

# 加载 .env 文件
load_dotenv()


class MergerError(Exception):
    """合并模块异常"""
    pass


def _load_embedding_model() -> TfidfVectorizer:
    """
    创建 TF-IDF 向量器
    
    返回：
    - TfidfVectorizer: 配置的向量器
    """
    try:
        logger.debug("📥 Creating TF-IDF vectorizer...")
        vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        logger.debug("✅ Vectorizer created successfully")
        return vectorizer
    except Exception as e:
        raise MergerError(f"❌ Failed to create vectorizer: {str(e)}")


def _compute_event_vectors(
    events: List[Dict],
    vectorizer: TfidfVectorizer
) -> Tuple[np.ndarray, TfidfVectorizer]:
    """
    计算事件的 TF-IDF 向量表示
    
    参数：
    - events: 核心事件列表
    - vectorizer: TF-IDF 向量器
    
    返回：
    - Tuple[np.ndarray, TfidfVectorizer]: 向量矩阵和拟合的向量器
    """
    core_events = [event["core_event"] for event in events]
    logger.debug(f"🧮 Computing TF-IDF vectors for {len(core_events)} events...")
    
    # 拟合并转换
    vectors = vectorizer.fit_transform(core_events).toarray()
    logger.debug(f"✅ Computed vectors shape: {vectors.shape}")
    
    return vectors, vectorizer


def _cluster_events(
    vectors: np.ndarray,
    eps: float = 0.3,
    min_samples: int = 1
) -> np.ndarray:
    """
    使用 DBSCAN 聚类事件向量
    
    参数：
    - vectors: 事件向量矩阵
    - eps: DBSCAN eps 参数（相似度阈值）
    - min_samples: DBSCAN min_samples 参数
    
    返回：
    - np.ndarray: 聚类标签数组
    """
    logger.debug(f"🔀 Clustering with DBSCAN (eps={eps}, min_samples={min_samples})...")
    
    # 对于 TF-IDF，使用欧几里得距离
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="euclidean")
    labels = clustering.fit_predict(vectors)
    
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)
    
    logger.debug(f"✅ Clustering complete: {n_clusters} clusters, {n_noise} noise points")
    
    return labels


def _build_cluster_description_prompt(cluster_events: List[Dict]) -> str:
    """
    构建聚类事件描述生成提示词
    
    参数：
    - cluster_events: 同一聚类中的所有事件
    
    返回：
    - 提示词字符串
    """
    
    # 格式化聚类中的事件
    events_text = ""
    for i, event in enumerate(cluster_events, 1):
        events_text += f"\n事件 {i}: {event['core_event']}"
        events_text += f"\n  - 来源: {event['source_name']}"
        events_text += f"\n  - 接受率: {event['acceptance_rate']:.2f}"
        events_text += f"\n  - 权威分: {event['authority_score']:.2f}\n"
    
    prompt = f"""You are an AI news aggregation expert. Multiple news sources have reported on similar events.

Below are {len(cluster_events)} versions of the same or very similar event from different sources:
{events_text}

Your task is to:
1. Analyze all the reported versions
2. Extract the common core information
3. Generate a unified, comprehensive event description that captures the essence while being accurate to all versions
4. The description should be objective, factual, and suitable for a news summary

Generate a concise but comprehensive unified event description (in English, 1-2 sentences):
"""
    
    return prompt


def _dashscope_post(payload: dict, api_key: str, retries: int = 3, timeout: float = 60.0) -> httpx.Response:
    """
    调用 DashScope API 并在失败时重试。
    """
    last_error = None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for attempt in range(1, retries + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(
                    "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                return response
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.NetworkError) as e:
            last_error = e
            logger.warning(
                f"⚠️ DashScope request timeout/network error on attempt {attempt}/{retries}: {e}"
            )
            if attempt < retries:
                time.sleep(2 ** attempt)
            continue
        except httpx.HTTPStatusError as e:
            raise MergerError(f"❌ DashScope API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise MergerError(f"❌ Unexpected error calling DashScope: {str(e)}")

    raise MergerError(f"❌ Failed to call DashScope API after {retries} attempts: {last_error}")


async def _generate_cluster_description(
    cluster_events: List[Dict],
    api_key: str
) -> str:
    """
    使用 Qwen API 为聚类生成统一描述
    
    参数：
    - cluster_events: 聚类中的所有事件
    - api_key: DashScope API Key
    
    返回：
    - 统一事件描述
    """
    
    prompt = _build_cluster_description_prompt(cluster_events)
    
    try:
        client = httpx.AsyncClient(timeout=30.0)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "qwen3-235b-a22b",
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            "parameters": {
                "temperature": 0.3,
                "max_tokens": 500,
            }
        }
        
        response = await client.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            headers=headers,
            json=payload
        )
        
        response_data = response.json()
        
        if "output" not in response_data:
            raise MergerError("❌ Invalid DashScope response format")
        
        output = response_data.get("output", {})
        choices = output.get("choices", [])
        
        if not choices:
            raise MergerError("❌ No response from DashScope")
        
        description = choices[0].get("message", {}).get("content", "")
        
        await client.aclose()
        return description.strip()
        
    except Exception as e:
        raise MergerError(f"❌ Failed to generate cluster description: {str(e)}")


def _generate_cluster_description_sync(
    cluster_events: List[Dict],
    api_key: str
) -> str:
    """
    同步版本的聚类描述生成
    
    参数：
    - cluster_events: 聚类中的所有事件
    - api_key: DashScope API Key
    
    返回：
    - 统一事件描述
    """
    
    prompt = _build_cluster_description_prompt(cluster_events)
    
    try:
        payload = {
            "model": "qwen3-235b-a22b",
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            "parameters": {
                "temperature": 0.3,
                "max_tokens": 500,
            }
        }

        response = _dashscope_post(payload, api_key=api_key, retries=3, timeout=60.0)
        response_data = response.json()

        if "output" not in response_data:
            raise MergerError("❌ Invalid DashScope response format")

        output = response_data.get("output", {})
        choices = output.get("choices", [])

        if not choices:
            raise MergerError("❌ No response from DashScope")

        description = choices[0].get("message", {}).get("content", "")
        return description.strip()

    except MergerError:
        raise
    except Exception as e:
        raise MergerError(f"❌ Failed to generate cluster description: {str(e)}")


def _calculate_reliability_score(
    cluster_events: List[Dict],
    boost_threshold_sources: int = 3,
    boost_threshold_authority: float = 0.6,
    boost_amount: float = 0.05
) -> float:
    """
    计算聚类事件的可信度分数
    
    公式：reliability_score = sum(authority_score * acceptance_rate) / sum(authority_score)
    
    可选修正：来源数量 >= 3 且平均权威分 > 0.6 时小幅上调
    
    参数：
    - cluster_events: 聚类中的所有事件
    - boost_threshold_sources: 触发提升的最小来源数
    - boost_threshold_authority: 触发提升的最小平均权威分
    - boost_amount: 提升幅度
    
    返回：
    - float: 可信度分数 (0.0 - 1.0)
    """
    
    if not cluster_events:
        return 0.0
    
    # 计算基础分数
    numerator = sum(
        event.get("authority_score", 0.5) * event.get("acceptance_rate", 0.5)
        for event in cluster_events
    )
    denominator = sum(
        event.get("authority_score", 0.5)
        for event in cluster_events
    )
    
    if denominator == 0:
        base_score = 0.0
    else:
        base_score = numerator / denominator
    
    # 计算是否满足提升条件
    n_sources = len(cluster_events)
    avg_authority = denominator / n_sources if n_sources > 0 else 0.0
    
    score = base_score
    
    # 应用可选提升
    if n_sources >= boost_threshold_sources and avg_authority > boost_threshold_authority:
        score = min(1.0, score + boost_amount)
        logger.debug(f"   ↑ Boosted score (sources={n_sources}, avg_auth={avg_authority:.2f})")
    
    # 确保分数在有效范围内
    score = max(0.0, min(1.0, score))
    
    return score


def merge_and_score(
    events: List[Dict],
    eps: float = 0.3,
    use_qwen_description: bool = True
) -> List[Dict]:
    """
    合并相似事件并计算可信度
    
    参数：
    - events: 核心事件列表（来自 core_event.py）
    - eps: DBSCAN 聚类参数（eps 越小，聚类越严格）
    - use_qwen_description: 是否使用 Qwen 生成聚类描述
    
    返回：
    - List[Dict]: 合并后的事件列表，每条包含：
        - unified_event: 统一的事件描述
        - reliability_score: 可信度分数
        - sources: 该事件的来源列表
        - source_count: 来源数量
    
    异常：
    - MergerError: 处理失败时抛出
    """
    
    if not events:
        logger.warning("⚠️  No events to merge")
        return []
    
    logger.info(f"🔀 Merging {len(events)} events with DBSCAN (eps={eps})")
    
    # 加载嵌入模型
    vectorizer = _load_embedding_model()
    
    # 计算向量
    vectors, fitted_vectorizer = _compute_event_vectors(events, vectorizer)
    
    # 聚类
    labels = _cluster_events(vectors, eps=eps)
    
    # 按聚类分组
    clusters = defaultdict(list)
    for idx, label in enumerate(labels):
        clusters[label].append(events[idx])
    
    # 处理每个聚类
    merged_events = []
    api_key = os.getenv("DASHSCOPE_API_KEY")
    
    for cluster_id, cluster_events in clusters.items():
        cluster_label = "noise" if cluster_id == -1 else f"cluster_{cluster_id}"
        logger.debug(f"\n📦 Processing {cluster_label}: {len(cluster_events)} events")
        
        # 生成统一描述
        if use_qwen_description and len(cluster_events) > 1:
            try:
                logger.debug(f"   📝 Generating unified description...")
                unified_event = _generate_cluster_description_sync(cluster_events, api_key)
            except MergerError as e:
                logger.warning(f"   ⚠️  Failed to generate description: {e}, using first event")
                unified_event = cluster_events[0]["core_event"]
        else:
            # 单个事件或跳过生成，直接使用原始
            if len(cluster_events) == 1:
                unified_event = cluster_events[0]["core_event"]
            else:
                # 多个事件但不使用 Qwen，使用第一个事件
                unified_event = cluster_events[0]["core_event"]
        
        # 计算可信度
        reliability_score = _calculate_reliability_score(cluster_events)
        
        # 提取来源信息
        sources = [event.get("source_name", "Unknown") for event in cluster_events]
        
        # 创建合并后的事件
        merged_event = {
            "unified_event": unified_event,
            "core_event_cluster": [event.get("core_event") for event in cluster_events],
            "reliability_score": reliability_score,
            "source_count": len(sources),
            "sources": sources,
            "source_details": [
                {
                    "name": event.get("source_name"),
                    "authority_score": event.get("authority_score"),
                    "acceptance_rate": event.get("acceptance_rate")
                }
                for event in cluster_events
            ],
            "avg_authority_score": np.mean([e.get("authority_score", 0.5) for e in cluster_events]),
            "avg_acceptance_rate": np.mean([e.get("acceptance_rate", 0.5) for e in cluster_events])
        }
        
        merged_events.append(merged_event)
        
        logger.debug(f"   ✅ Merged: {len(sources)} sources, reliability={reliability_score:.2f}")
    
    # 按可信度分数排序（降序）
    merged_events.sort(key=lambda x: x["reliability_score"], reverse=True)
    
    logger.info(f"📊 Merging complete: {len(events)} → {len(merged_events)} events")
    
    return merged_events


if __name__ == "__main__":
    # 测试代码
    try:
        # 模拟核心事件数据
        test_events = [
            {
                "title": "Event 1",
                "core_event": "OpenAI releases new GPT-4 model with improved capabilities",
                "acceptance_rate": 0.85,
                "source_name": "TechCrunch",
                "authority_score": 0.8
            },
            {
                "title": "Event 2",
                "core_event": "OpenAI announces GPT-4 upgrade with better reasoning",
                "acceptance_rate": 0.88,
                "source_name": "Reuters",
                "authority_score": 0.85
            },
            {
                "title": "Event 3",
                "core_event": "New research shows AI safety concerns in language models",
                "acceptance_rate": 0.75,
                "source_name": "MIT News",
                "authority_score": 0.9
            }
        ]
        
        print(f"📰 Testing merger.py with {len(test_events)} test events...\n")
        
        merged = merge_and_score(test_events, eps=0.3)
        
        print(f"\n✅ Merging complete: {len(test_events)} → {len(merged)} events\n")
        
        for i, event in enumerate(merged, 1):
            print(f"--- 合并事件 {i} ---")
            print(f"事件: {event['unified_event']}")
            print(f"可信度: {event['reliability_score']:.2f}")
            print(f"来源: {event['source_count']} ({', '.join(event['sources'])})")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Test failed")
