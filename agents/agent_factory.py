"""
创建和配置AutoGen代理的工厂类。

此模块负责实例化所有需要的代理并将它们连接成一个多代理系统。
"""

from typing import Dict, Any, Optional, List
import json
from autogen import Agent, AssistantAgent, UserProxyAgent


from config.config import DEFAULT_MODEL, DEEPSEEK_API_KEY, DEEPSEEK_API_BASE
from models.deepseek_client import create_deepseek_config
from .web_fetcher_agent import WebFetcherAgent
from .content_processor_agent import ContentProcessorAgent
from .summarizer_agent import SummarizerAgent
from .integrator_agent import IntegratorAgent
from storage.summary_storage import SummaryStorage


class SummarizationAgentTeam:
    """摘要生成代理团队，协调多个代理完成网页摘要生成任务"""
    
    def __init__(self):
        """初始化代理团队"""
        # 创建DeepSeek LLM配置
        self.llm_config = create_deepseek_config(
            model=DEFAULT_MODEL,
            api_key=DEEPSEEK_API_KEY,
            api_base=DEEPSEEK_API_BASE
        )
        
        # 存储管理器
        self.storage = SummaryStorage()
        
        # 初始化代理
        self.web_fetcher = WebFetcherAgent()
        self.content_processor = ContentProcessorAgent()
        self.summarizer = SummarizerAgent(llm_config=self.llm_config)
        self.integrator = IntegratorAgent(llm_config=self.llm_config)
        
        # 用户代理 - 充当整个系统的控制中心
        self.user_proxy = UserProxyAgent(
            name="user_proxy",
            is_termination_msg=self._is_termination_msg,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            code_execution_config={"work_dir": "workdir", "use_docker": False},
        )
    
    @staticmethod
    def _is_termination_msg(msg: Dict[str, Any]) -> bool:
        """判断是否终止对话的消息"""
        if isinstance(msg, dict) and "content" in msg:
            content = msg["content"]
            if "TASK_COMPLETED" in content or "TASK_FAILED" in content:
                return True
        return False
    
    async def start_summarization(self, url: str) -> str:
        """
        启动网页摘要生成流程
        
        Args:
            url: 要摘要的网页URL
        
        Returns:
            生成的摘要内容
        """
        # 检查是否已有缓存的摘要
        cached_summary = self.storage.get_summary_by_url(url)
        if cached_summary:
            print(f"找到缓存的摘要结果，直接返回。")
            return cached_summary['content']
        
        try:
            # 1. 获取网页内容
            webpage_content = await self.web_fetcher.fetch_webpage(url)
            if not webpage_content:
                raise ValueError(f"无法获取网页内容: {url}")
                
            # 2. 处理内容，分块
            content_chunks = await self.content_processor.process_content(webpage_content)
            
            # 3. 为每个块生成摘要
            chunk_summaries = []
            for i, chunk in enumerate(content_chunks):
                print(f"正在处理内容块 {i+1}/{len(content_chunks)}...")
                try:
                    summary_obj = await self.summarizer.generate_summary(chunk)
                    # 处理可能的各种返回类型
                    if isinstance(summary_obj, str):
                        summary = summary_obj
                    elif hasattr(summary_obj, 'content'):
                        summary = summary_obj.content
                    elif hasattr(summary_obj, 'message') and hasattr(summary_obj.message, 'content'):
                        summary = summary_obj.message.content
                    elif isinstance(summary_obj, dict) and 'content' in summary_obj:
                        summary = summary_obj['content']
                    else:
                        summary = str(summary_obj)
                    chunk_summaries.append(summary)
                except Exception as e:
                    print(f"处理块 {i+1} 时出错: {str(e)}")
                    chunk_summaries.append(f"[块 {i+1} 处理错误]")
            
            # 4. 整合摘要
            if len(chunk_summaries) == 1:
                final_summary = chunk_summaries[0]
            else:
                try:
                    integrated_obj = await self.integrator.integrate_summaries(chunk_summaries, url)
                    # 处理可能的各种返回类型
                    if isinstance(integrated_obj, str):
                        final_summary = integrated_obj
                    elif hasattr(integrated_obj, 'content'):
                        final_summary = integrated_obj.content
                    elif hasattr(integrated_obj, 'message') and hasattr(integrated_obj.message, 'content'):
                        final_summary = integrated_obj.message.content
                    elif isinstance(integrated_obj, dict) and 'content' in integrated_obj:
                        final_summary = integrated_obj['content']
                    else:
                        final_summary = str(integrated_obj)
                except Exception as e:
                    print(f"整合摘要时出错: {str(e)}")
                    final_summary = "\n\n".join(chunk_summaries)
            
            # 5. 保存摘要
            self.storage.save_summary(url, final_summary)
            
            return final_summary
            
        except Exception as e:
            print(f"摘要生成失败: {str(e)}")
            raise


def create_agents() -> SummarizationAgentTeam:
    """
    创建并配置所有代理
    
    Returns:
        配置好的SummarizationAgentTeam实例
    """
    return SummarizationAgentTeam()