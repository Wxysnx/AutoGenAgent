"""
摘要生成代理，使用DeepSeek API生成文本摘要。
"""
from typing import Dict, Any, Optional
from autogen import AssistantAgent, UserProxyAgent


class SummarizerAgent:
    """
    摘要生成代理，负责对文本内容生成摘要
    """
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        初始化摘要生成代理
        
        Args:
            llm_config: LLM配置
        """
        self.agent = AssistantAgent(
            name="summarizer",
            system_message="""你是一个专业的文本摘要专家。你的任务是生成准确、全面、连贯的内容摘要。
            请遵循以下原则:
            1. 保持客观性，不添加个人观点
            2. 确保摘要涵盖文本的主要观点和关键信息
            3. 提取重要的事实、数据和论点
            4. 使用清晰、简洁的语言
            5. 保持原文的语气和风格
            6. 摘要应当是连贯的文本，而不是要点列表
            7. 总结长度应根据原始内容的复杂度和长度进行适当调整，通常为原文的10%-20%
            
            直接输出摘要内容，不要包含诸如"以下是摘要"等元描述。
            """,
            llm_config=llm_config
        )
    
    async def generate_summary(self, content: str) -> str:
        """
        为给定内容生成摘要
        
        Args:
            content: 需要摘要的文本内容
        
        Returns:
            生成的摘要文本
        """
        from autogen.agentchat import UserProxyAgent
        
        # 创建一个临时的用户代理来与摘要代理交互
        user_proxy = UserProxyAgent(
            name="user",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0
        )
        
        # 构建提示
        prompt = f"""请为以下内容生成一个全面、准确的摘要：

```内容开始
{content}
```内容结束

请直接输出摘要内容，不要包含诸如"以下是摘要"等元描述。"""
        
        # 发送请求并获取回复
        await user_proxy.initiate_chat(self.agent, message=prompt)
        
        # 获取摘要文本(最后一条消息)
        messages = user_proxy.chat_messages[self.agent.name]
        if messages:
            summary = messages[-1]["content"]
            return summary
        
        return "无法生成摘要。"