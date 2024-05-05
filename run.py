#!/usr/bin/env python

"""
AutoGen网页内容摘要系统 - 命令行入口程序
"""

import sys
import click
from pathlib import Path
import asyncio


# 添加项目根目录到Python路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))


from config.config import DEEPSEEK_API_KEY
from agents.agent_factory import create_agents
from storage.summary_storage import SummaryStorage


@click.group()
def cli():
    """AutoGen网页内容摘要系统 - 自动生成网页内容的摘要"""
    # 检查API密钥配置
    if not DEEPSEEK_API_KEY:
        click.echo("错误: DeepSeek API密钥未配置。请检查您的.env文件。")
        sys.exit(1)


@cli.command()
@click.option('--url', required=True, help='要摘要的网页URL')
def summarize(url):
    """生成指定网页的内容摘要"""
    click.echo(f"正在处理网页: {url}")
   
    try:
        # 创建代理组
        agents = create_agents()
       
        # 启动摘要过程
        result_obj = asyncio.run(agents.start_summarization(url))
        
        # 处理可能的ChatResult对象或其他类型
        if hasattr(result_obj, 'content'):
            # 如果是ChatResult对象有content属性
            result = result_obj.content
        elif hasattr(result_obj, 'message') and hasattr(result_obj.message, 'content'):
            # 如果是有message.content结构的对象
            result = result_obj.message.content
        elif isinstance(result_obj, dict) and 'content' in result_obj:
            # 如果是字典类型
            result = result_obj['content']
        else:
            # 如果是字符串或其他类型，直接使用
            result = result_obj
       
        # 输出摘要结果
        click.echo("\n" + "="*50)
        click.echo("摘要生成成功!")
        click.echo("="*50 + "\n")
        click.echo(result)
       
    except Exception as e:
        click.echo(f"错误: 摘要生成失败 - {str(e)}")
        if "--debug" in sys.argv:
            import traceback
            click.echo(traceback.format_exc())


@cli.command()
def history():
    """显示历史摘要记录"""
    storage = SummaryStorage()
    summaries = storage.list_summaries()
   
    if not summaries:
        click.echo("没有找到历史摘要记录。")
        return
   
    click.echo("\n历史摘要记录:")
    click.echo("="*80)
   
    for i, summary in enumerate(summaries, 1):
        click.echo(f"{i}. URL: {summary['url']}")
        click.echo(f"   ID: {summary['id']}")
        click.echo(f"   时间: {summary['timestamp']}")
        click.echo(f"   预览: {summary['preview'][:100]}...")
        click.echo("-"*80)


@cli.command()
@click.option('--url', help='要阅读的网页URL')
@click.option('--id', help='要阅读的摘要ID')
def read(url, id):
    """阅读之前生成的摘要"""
    if not url and not id:
        click.echo("错误: 请提供URL或ID来指定要阅读的摘要。")
        return
   
    storage = SummaryStorage()
   
    try:
        if url:
            summary = storage.get_summary_by_url(url)
        else:
            summary = storage.get_summary_by_id(id)
       
        if not summary:
            click.echo("未找到指定的摘要。")
            return
       
        click.echo("\n" + "="*50)
        click.echo(f"URL: {summary['url']}")
        click.echo(f"生成时间: {summary['timestamp']}")
        click.echo("="*50 + "\n")
        click.echo(summary['content'])
       
    except Exception as e:
        click.echo(f"错误: 无法读取摘要 - {str(e)}")


if __name__ == '__main__':
    cli()