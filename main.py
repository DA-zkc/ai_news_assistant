"""
main.py - AI 要闻助手主入口

命令行工具，使用 Click 库管理参数。
完整的端到端新闻处理流程：
fetcher -> filter -> fact_opinion -> core_event -> merger -> output
"""

import sys
from pathlib import Path

# 确保模块可以被导入
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime
import click
from loguru import logger
from modules.fetcher import fetch_news, NewsAPIError
from modules.filter import filter_news, FilterError
from modules.fact_opinion import process as process_fact_opinion, FactOpinionError
from modules.core_event import extract as extract_core_event, CoreEventError
from modules.merger import merge_and_score, MergerError
from modules.output import generate_markdown, OutputError

# 配置日志
logger.remove()
logger.add(
    "ai_news_assistant.log",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
)
logger.add(
    sys.stderr,
    level="INFO",
    format="<level>{message}</level>"
)


@click.command()
@click.option(
    "--date",
    default=None,
    help="指定日期 YYYY-MM-DD，默认今天"
)
@click.option(
    "--lang",
    default="en",
    help="查询语言代码，例如 en、zh，默认 en"
)
@click.option(
    "--country",
    default=None,
    help="国家代码，例如 us、cn，默认全球范围"
)
@click.option(
    "--max-articles",
    default=100,
    type=int,
    help="最大获取文章数量，默认 100"
)
@click.option(
    "--out",
    default="ai_news_today.md",
    help="输出 Markdown 文件路径，默认 ai_news_today.md"
)
@click.option(
    "--eps",
    default=0.3,
    type=float,
    help="事件聚类相似度阈值 eps，默认 0.3（值越大，聚类越宽松）"
)
@click.option(
    "--debug",
    is_flag=True,
    help="启用调试模式（输出更详细的日志）"
)
@click.option(
    "--no-qwen",
    is_flag=True,
    help="禁用 Qwen 生成聚类描述（更快但质量可能降低）"
)
def main(date, lang, country, max_articles, out, eps, debug, no_qwen):
    """
    AI 要闻助手 - 每日 AI 行业新闻摘要生成工具
    
    使用示例：
    
    \b
    python main.py                    # 生成今天的要闻，输出到 ai_news_today.md
    python main.py --date 2026-04-28  # 生成指定日期的要闻
    python main.py --out news.md      # 自定义输出文件
    python main.py --debug            # 启用调试模式
    python main.py --no-qwen          # 禁用 Qwen 描述生成（更快）
    """
    
    # 配置日志级别
    if debug:
        logger.remove()
        logger.add(
            "ai_news_assistant.log",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
        )
        logger.add(
            sys.stderr,
            level="DEBUG",
            format="<level>{message}</level>"
        )
        logger.info("🔧 Debug mode enabled")
    
    # 设置默认日期
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"📅 Using today's date: {date}")
    else:
        # 验证日期格式
        try:
            datetime.strptime(date, "%Y-%m-%d")
            logger.info(f"📅 Processing date: {date}")
        except ValueError:
            click.echo("❌ Invalid date format. Use YYYY-MM-DD", err=True)
            sys.exit(1)
    
    click.echo("\n" + "=" * 70)
    click.echo("🤖 AI 要闻助手 - 每日新闻摘要生成")
    click.echo("=" * 70)
    click.echo(f"📅 日期: {date}")
    click.echo(f"🌐 语言: {lang}")
    click.echo(f"🌍 国家: {country or 'global'}")
    click.echo(f"📄 最大文章数: {max_articles}")
    click.echo(f"📁 输出: {out}")
    click.echo(f"🔀 聚类 eps: {eps}")
    click.echo("=" * 70 + "\n")
    
    try:
        # ===== 阶段1：获取原始新闻 =====
        click.echo("📰 [1/6] 从 GNews API 获取新闻...")
        raw_news = fetch_news(
            query="artificial intelligence",
            lang=lang,
            country=country,
            max_articles=max_articles,
            sort_by="publishedAt",
            date=date,
        )
        
        if not raw_news:
            click.echo("❌ 未能获取任何新闻", err=True)
            logger.warning("No news retrieved from API")
            sys.exit(1)
        
        click.echo(f"✅ 获取了 {len(raw_news)} 条新闻\n")
        logger.info(f"Retrieved {len(raw_news)} raw news articles")
        
        # ===== 阶段2：初步筛选 =====
        click.echo("🔍 [2/6] 使用 DeepSeek 进行质量筛选...")
        filtered_news = filter_news(raw_news)
        
        if not filtered_news:
            click.echo("❌ 筛选后没有符合条件的新闻", err=True)
            logger.warning("No news passed filtering")
            sys.exit(1)
        
        click.echo(f"✅ 筛选到 {len(filtered_news)} 条高质量新闻\n")
        logger.info(f"Filtered to {len(filtered_news)} articles")
        
        # ===== 阶段3：事实与观点分离 =====
        click.echo("💡 [3/6] 使用 Qwen 提取事实和观点...")
        analyzed_news = process_fact_opinion(filtered_news)
        
        if not analyzed_news:
            click.echo("❌ 事实观点分析失败", err=True)
            logger.warning("Fact-opinion analysis failed")
            sys.exit(1)
        
        click.echo(f"✅ 分析了 {len(analyzed_news)} 条新闻\n")
        logger.info(f"Analyzed {len(analyzed_news)} articles for facts/opinions")
        
        # ===== 阶段4：核心事件提取 =====
        click.echo("🎯 [4/6] 使用 DeepSeek 提取核心事件...")
        core_events = extract_core_event(analyzed_news)
        
        if not core_events:
            click.echo("❌ 核心事件提取失败", err=True)
            logger.warning("Core event extraction failed")
            sys.exit(1)
        
        click.echo(f"✅ 提取了 {len(core_events)} 个核心事件\n")
        logger.info(f"Extracted {len(core_events)} core events")
        
        # ===== 阶段5：事件合并与可信度评分 =====
        click.echo(f"🔀 [5/6] 合并相似事件（eps={eps})...")
        merged_events = merge_and_score(core_events, eps=eps, use_qwen_description=not no_qwen)
        
        if not merged_events:
            click.echo("❌ 事件合并失败", err=True)
            logger.warning("Event merging failed")
            sys.exit(1)
        
        click.echo(f"✅ 合并为 {len(merged_events)} 个最终事件\n")
        logger.info(f"Merged to {len(merged_events)} final events")
        
        # ===== 阶段6：生成 Markdown 输出 =====
        click.echo("📝 [6/6] 生成 Markdown 输出...")
        markdown_content = generate_markdown(merged_events, date=date)
        
        if not markdown_content:
            click.echo("❌ Markdown 生成失败", err=True)
            logger.warning("Markdown generation failed")
            sys.exit(1)
        
        # 保存到文件
        try:
            output_path = Path(out)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown_content, encoding="utf-8")
            click.echo(f"✅ Markdown 已生成\n")
            logger.info(f"Markdown saved to {output_path}")
        except Exception as e:
            click.echo(f"❌ 保存文件失败: {e}", err=True)
            logger.error(f"Failed to save file: {e}")
            sys.exit(1)
        
        # ===== 完成 =====
        click.echo("=" * 70)
        click.echo("✅ 处理完成！")
        click.echo("=" * 70)
        click.echo(f"\n📊 统计信息:")
        click.echo(f"  • 原始新闻: {len(raw_news)} 条")
        click.echo(f"  • 高质量新闻: {len(filtered_news)} 条")
        click.echo(f"  • 分析完成: {len(analyzed_news)} 条")
        click.echo(f"  • 核心事件: {len(core_events)} 个")
        click.echo(f"  • 最终事件: {len(merged_events)} 个")
        click.echo(f"\n📁 输出文件: {out}")
        click.echo(f"📅 处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo()
        
        logger.info("Pipeline completed successfully")
        
    except (NewsAPIError, FilterError, FactOpinionError, CoreEventError, MergerError, OutputError) as e:
        click.echo(f"\n❌ 处理错误: {e}", err=True)
        logger.error(f"Pipeline error: {e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n❌ 未知错误: {e}", err=True)
        logger.exception("Unexpected error in pipeline")
        sys.exit(1)


if __name__ == "__main__":
    main()
