"""
摘要整合代理，整合多个摘要块成为一个连贯的完整摘要。
"""
from typing import List, Dict, Any
from autogen import AssistantAgent, UserProxyAgent


class IntegratorAgent:
    """
    摘要整合代理，负责将多个分块摘要整合成一个连贯的完整摘要
    """
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        初始化摘要整合代理
        
        Args:
            llm_config: LLM配置
        """
        self.agent = AssistantAgent(
            name="integrator",
            system_message="""你是一个专业的文本整合专家。你的任务是将多个相关的文本摘要整合成一个连贯、全面的完整摘要。
            请遵循以下原则:
            1. 确保最终摘要内容连贯流畅，避免重复
            2. 识别并整合各个摘要块中的共同主题和观点
            3. 保留每个摘要块中的独特信息和见解
            4. 调整和重组内容以确保逻辑顺序和清晰度
            5. 使用适当的过渡词和连接句使整体摘要更加连贯
            6. 合并相似或重复的信息，但保持内容的完整性
            7. 最终摘要应当是一个统一的整体，而不是分散的片段
            
            直接输出整合后的摘要内容，不要包含诸如"以下是整合后的摘要"等元描述。
            """,
            llm_config=llm_config
        )
    
    async def integrate_summaries(self, summaries: List[str], url: str) -> str:
        """
        整合多个摘要块成为一个连贯的完整摘要
        
        Args:
            summaries: 摘要块列表
            url: 原始网页URL，用于提供上下文
        
        Returns:
            整合后的完整摘要
        """
        from autogen.agentchat import UserProxyAgent
        
        # 创建一个临时的用户代理来与整合代理交互
        user_proxy = UserProxyAgent(
            name="user",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0
        )
        
        # 构建提示
        prompt = f"""下面是来自同一网页({url})的多个部分摘要。请将它们整合成一个连贯、全面的完整摘要：

"""
        for i, summary in enumerate(summaries, 1):
            prompt += f"\n摘要块 {i}:\n{summary}\n"
        
        prompt += """
请整合上述摘要块，创建一个连贯、全面且不重复的完整摘要。直接输出整合后的摘要内容，不要包含诸如"以下是整合后的摘要"等元描述。
"""
        
        # 发送请求并获取回复
        await user_proxy.initiate_chat(self.agent, message=prompt)
        
        # 获取整合后的摘要(最后一条消息)
        messages = user_proxy.chat_messages[self.agent.name]
        if messages:
            integrated_summary = messages[-1]["content"]
            return integrated_summary
        
        return "无法整合摘要。"