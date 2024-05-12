# 文本处理工具，如分块、清理等 
"""
文本处理工具模块，提供各种文本处理和分析功能。
"""
import re
import unicodedata
import urllib.parse
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
from urllib.parse import urlparse
import tiktoken


def clean_html(html_text: str) -> str:
    """
    清理HTML文本，移除HTML标签
    
    Args:
        html_text: 包含HTML标签的文本
    
    Returns:
        清理后的纯文本
    """
    # 移除脚本标签和内容
    html_text = re.sub(r'<script[^>]*>[\s\S]*?</script>', ' ', html_text)
    
    # 移除样式标签和内容
    html_text = re.sub(r'<style[^>]*>[\s\S]*?</style>', ' ', html_text)
    
    # 移除其他HTML标签
    html_text = re.sub(r'<[^>]*>', ' ', html_text)
    
    # 处理HTML实体
    html_text = re.sub(r'&nbsp;', ' ', html_text)
    html_text = re.sub(r'&lt;', '<', html_text)
    html_text = re.sub(r'&gt;', '>', html_text)
    html_text = re.sub(r'&amp;', '&', html_text)
    html_text = re.sub(r'&quot;', '"', html_text)
    html_text = re.sub(r'&#39;', "'", html_text)
    html_text = re.sub(r'&[a-zA-Z0-9]+;', ' ', html_text)  # 其他HTML实体
    
    return normalize_whitespace(html_text)


def normalize_whitespace(text: str) -> str:
    """
    规范化文本中的空白字符
    
    Args:
        text: 原始文本
    
    Returns:
        规范化后的文本
    """
    # 替换连续的空白为单个空格
    text = re.sub(r'\s+', ' ', text)
    
    # 替换连续多个空行为双空行
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # 去除前后空白
    return text.strip()


def extract_main_content(text: str) -> str:
    """
    从文本中提取主要内容，尝试去除页眉、页脚、导航栏等
    
    Args:
        text: 完整网页文本
    
    Returns:
        提取的主要内容
    """
    # 分割文本为段落
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    
    # 过滤太短的段落(可能是菜单、导航等)
    main_paragraphs = [p for p in paragraphs if len(p) > 40 or re.search(r'[.!?。！？]', p)]
    
    # 如果过滤后的段落太少，则退回到原始段落
    if len(main_paragraphs) < len(paragraphs) * 0.3:
        main_paragraphs = paragraphs
    
    return '\n\n'.join(main_paragraphs)


def estimate_tokens(text: str) -> int:
    """
    估计文本的token数量
    
    Args:
        text: 要估计的文本
    
    Returns:
        估计的token数
    """
    try:
        # 尝试使用tiktoken
        tokenizer = tiktoken.get_encoding("cl100k_base")
        return len(tokenizer.encode(text))
    except:
        # 降级方案：使用简单估计
        # 按照OpenAI的估算，英文每4个字符约1个token，中文每1个字约2个token
        english_chars = sum(1 for c in text if ord(c) < 128)
        chinese_chars = sum(1 for c in text if ord(c) >= 0x4E00 and ord(c) <= 0x9FFF)
        other_chars = len(text) - english_chars - chinese_chars
        
        tokens_estimate = (english_chars / 4) + (chinese_chars * 2) + (other_chars / 3)
        return int(tokens_estimate)


def split_text_by_tokens(
    text: str, 
    max_tokens_per_chunk: int = 2000, 
    overlap_tokens: int = 100
) -> List[str]:
    """
    按token数量分割文本
    
    Args:
        text: 要分割的文本
        max_tokens_per_chunk: 每个块的最大token数
        overlap_tokens: 相邻块之间的重叠token数
    
    Returns:
        分割后的文本块列表
    """
    try:
        tokenizer = tiktoken.get_encoding("cl100k_base")
        tokens = tokenizer.encode(text)
        
        # 分割tokens
        chunks_tokens = []
        for i in range(0, len(tokens), max_tokens_per_chunk - overlap_tokens):
            chunk_end = min(i + max_tokens_per_chunk, len(tokens))
            chunks_tokens.append(tokens[i:chunk_end])
        
        # 将tokens转回文本
        chunks = [tokenizer.decode(chunk) for chunk in chunks_tokens]
        return chunks
    except:
        # 降级方案：按段落分割
        return split_text_by_paragraphs(text, max_tokens_per_chunk, overlap_tokens)


def split_text_by_paragraphs(
    text: str, 
    max_tokens_per_chunk: int = 2000, 
    overlap_tokens: int = 100
) -> List[str]:
    """
    按段落分割文本，并控制每个块的大致token数
    
    Args:
        text: 要分割的文本
        max_tokens_per_chunk: 每个块的大致最大token数
        overlap_tokens: 忽略，仅为兼容API
    
    Returns:
        分割后的文本块列表
    """
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    
    chunks = []
    current_chunk = []
    current_chunk_tokens = 0
    
    for para in paragraphs:
        para_tokens = estimate_tokens(para)
        
        # 如果一个段落太大，需要进一步分割
        if para_tokens > max_tokens_per_chunk:
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_chunk_tokens = 0
            
            # 分割大段落为更小的单位
            sentences = split_text_by_sentences(para)
            temp_chunk = []
            temp_tokens = 0
            
            for sentence in sentences:
                sentence_tokens = estimate_tokens(sentence)
                if temp_tokens + sentence_tokens > max_tokens_per_chunk:
                    if temp_chunk:
                        chunks.append(' '.join(temp_chunk))
                        temp_chunk = []
                        temp_tokens = 0
                
                temp_chunk.append(sentence)
                temp_tokens += sentence_tokens
            
            if temp_chunk:
                chunks.append(' '.join(temp_chunk))
        
        # 正常段落处理
        elif current_chunk_tokens + para_tokens > max_tokens_per_chunk:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [para]
            current_chunk_tokens = para_tokens
        else:
            current_chunk.append(para)
            current_chunk_tokens += para_tokens
    
    # 添加最后一个块
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks


def split_text_by_sentences(text: str) -> List[str]:
    """
    将文本按句子分割
    
    Args:
        text: 要分割的文本
    
    Returns:
        句子列表
    """
    # 处理英文和中文标点
    text = re.sub(r'([.!?。！？；;])\s*', r'\1\n', text)
    sentences = [s.strip() for s in text.split('\n') if s.strip()]
    return sentences


def validate_url(url: str) -> bool:
    """
    验证URL是否有效
    
    Args:
        url: 要验证的URL
    
    Returns:
        URL是否有效
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def get_domain_from_url(url: str) -> str:
    """
    从URL中获取域名
    
    Args:
        url: 完整的URL
    
    Returns:
        域名
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        # 移除www前缀
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return url