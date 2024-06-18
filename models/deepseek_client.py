# DeepSeek API客户端，处理API调用 
"""
DeepSeek API客户端，处理与DeepSeek API的交互。
"""
from typing import Dict, Any, Optional, List, Union
import json
import os
import time
from autogen.oai.client import OpenAIWrapper


class DeepSeekModelClient:
    """
    DeepSeek API客户端，封装对DeepSeek API的调用
    """
    
    def __init__(
        self, 
        api_key: str,
        api_base: str = "https://api.deepseek.com/v1",
        model: str = "deepseek-chat",
        timeout: int = 60,
        max_retries: int = 3,
        retry_wait: int = 3
    ):
        """
        初始化DeepSeek API客户端
        
        Args:
            api_key: DeepSeek API密钥
            api_base: DeepSeek API基本URL
            model: 使用的模型名称
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
            retry_wait: 重试等待时间(秒)
        """
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_wait = retry_wait
        
        # 创建OpenAI兼容的客户端包装器
        self.client = OpenAIWrapper(
            config_list=[{
                "model": self.model,
                "api_key": self.api_key,
                "base_url": self.api_base,
                "api_type": "openai",  # 使用OpenAI兼容格式
                "timeout": self.timeout,
            }]
        )
        
    def generate(
        self, 
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成文本响应
        
        Args:
            messages: 对话消息列表
            temperature: 采样温度，控制输出的随机性
            max_tokens: 生成的最大token数
            stream: 是否使用流式输出
            **kwargs: 其他传递给API的参数
        
        Returns:
            API响应
        """
        # 准备参数
        params = {
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }
        
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
            
        # 添加其他参数
        params.update(kwargs)
        
        # 尝试请求，带重试机制
        for attempt in range(self.max_retries):
            try:
                if stream:
                    return self._generate_stream(params)
                else:
                    return self._generate_sync(params)
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"API调用失败，{self.retry_wait}秒后重试: {str(e)}")
                    time.sleep(self.retry_wait)
                else:
                    raise Exception(f"DeepSeek API调用失败: {str(e)}")
    
    def _generate_sync(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        同步生成文本响应
        
        Args:
            params: API参数
        
        Returns:
            API响应
        """
        response = self.client.create(
            messages=params["messages"],
            model=self.model,
            temperature=params.get("temperature", 0.7),
            max_tokens=params.get("max_tokens"),
            **{k: v for k, v in params.items() if k not in ["messages", "temperature", "max_tokens"]}
        )
        
        return response
    
    def _generate_stream(self, params: Dict[str, Any]) -> str:
        """
        流式生成文本响应
        
        Args:
            params: API参数
        
        Returns:
            生成的完整文本
        """
        full_response = ""
        for chunk in self.client.create(
            messages=params["messages"],
            model=self.model,
            temperature=params.get("temperature", 0.7),
            max_tokens=params.get("max_tokens"),
            stream=True,
            **{k: v for k, v in params.items() if k not in ["messages", "temperature", "max_tokens", "stream"]}
        ):
            if chunk and "choices" in chunk and chunk["choices"]:
                content = chunk["choices"][0].get("delta", {}).get("content", "")
                if content:
                    full_response += content
                    print(content, end="", flush=True)
        
        print()  # 添加换行符
        return full_response


def create_deepseek_config(
    model: str = "deepseek-chat", 
    api_key: Optional[str] = None,
    api_base: str = "https://api.deepseek.com/v1"
) -> Dict[str, Any]:
    """
    创建DeepSeek API的LLM配置
    此配置可用于AutoGen代理的llm_config参数
    
    Args:
        model: DeepSeek模型名称
        api_key: DeepSeek API密钥，如果为None则从环境变量获取
        api_base: DeepSeek API基本URL
    
    Returns:
        LLM配置字典
    """
    if api_key is None:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError(
                "DeepSeek API密钥未配置。请提供api_key参数或设置DEEPSEEK_API_KEY环境变量。"
            )
    
    # 创建配置
    return {
        "config_list": [{
            "model": model,
            "api_key": api_key,
            "base_url": api_base,
            "api_type": "openai"
        }]
    }