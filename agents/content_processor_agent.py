# 内容处理代理，处理和分块长文本内�?
"""
内容处理代理，处理和分块长文本内容，便于后续生成摘要。
"""
import re
from typing import List
import tiktoken
from config.config import CHUNK_SIZE


class ContentProcessorAgent:
    """
    内容处理代理，负责清理和分块处理网页内容
    """
    
    def __init__(self):
        """初始化内容处理代理"""
        # 使用cl100k_base编码器，这是GPT模型使用的编码器
        # 如果DeepSeek使用不同的编码器，这里需要调整
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except:
            # 降级方案，使用基础编码器
            self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
    
    def _clean_content(self, content: str) -> str:
        """
        清理网页内容，移除多余的空白和不需要的元素
        
        Args:
            content: 原始网页内容
        
        Returns:
            清理后的内容
        """
        # 1. 替换连续多个空行为单个空行
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        # 2. 去除非ASCII字符但保留中文等常见字符
        content = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9.,;:!?()[\]{}，。；：！？（）【】「」『』\s\-\'"]+', '', content)
        
        # 3. 规范化空白字符
        content = re.sub(r'\s+', ' ', content)
        
        return content.strip()
    
    def _split_into_chunks(self, content: str) -> List[str]:
        """
        将内容分割成更小的块
        
        Args:
            content: 网页内容
        
        Returns:
            内容块列表
        """
        # 将内容转换为token
        tokens = self.tokenizer.encode(content)
        
        # 如果内容较短，不需要分块
        if len(tokens) <= CHUNK_SIZE:
            return [content]
        
        # 按照自然段落分割内容
        paragraphs = [p for p in content.split("\n\n") if p.strip()]
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para_tokens = self.tokenizer.encode(para)
            para_length = len(para_tokens)
            
            # 如果单个段落超过块大小，需要进一步分割
            if para_length > CHUNK_SIZE:
                # 处理超长段落，按句子分割
                sentences = re.split(r'(?<=[.!?。！？])\s+', para)
                for sentence in sentences:
                    sent_tokens = self.tokenizer.encode(sentence)
                    sent_length = len(sent_tokens)
                    
                    if sent_length > CHUNK_SIZE:
                        # 如果单个句子还是太长，直接截断
                        for i in range(0, len(sent_tokens), CHUNK_SIZE):
                            sub_tokens = sent_tokens[i:i + CHUNK_SIZE]
                            sub_text = self.tokenizer.decode(sub_tokens)
                            chunks.append(sub_text)
                    elif current_length + sent_length > CHUNK_SIZE:
                        # 当前块加上这个句子会超过大小限制
                        chunks.append("\n\n".join(current_chunk))
                        current_chunk = [sentence]
                        current_length = sent_length
                    else:
                        # 添加句子到当前块
                        current_chunk.append(sentence)
                        current_length += sent_length
            elif current_length + para_length > CHUNK_SIZE:
                # 当前块加上这个段落会超过大小限制
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [para]
                current_length = para_length
            else:
                # 添加段落到当前块
                current_chunk.append(para)
                current_length += para_length
        
        # 添加最后一个块
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
        
        return chunks
    
    async def process_content(self, content: str) -> List[str]:
        """
        处理并分块网页内容
        
        Args:
            content: 原始网页内容
        
        Returns:
            处理后的内容块列表
        """
        # 清理内容
        cleaned_content = self._clean_content(content)
        
        # 分块
        chunks = self._split_into_chunks(cleaned_content)
        
        print(f"内容已处理并分成 {len(chunks)} 个块")
        
        return chunks