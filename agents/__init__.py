# 包初始化文件 
"""
AutoGen多代理系统包初始化文件。
导出主要的代理类和工厂函数。
"""
from .agent_factory import create_agents, SummarizationAgentTeam
from .web_fetcher_agent import WebFetcherAgent
from .content_processor_agent import ContentProcessorAgent
from .summarizer_agent import SummarizerAgent
from .integrator_agent import IntegratorAgent

__all__ = [
    'create_agents',
    'SummarizationAgentTeam',
    'WebFetcherAgent',
    'ContentProcessorAgent',
    'SummarizerAgent',
    'IntegratorAgent'
]