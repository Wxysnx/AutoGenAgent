# 摘要存储管理，处理摘要的保存与检�?
"""
摘要存储管理模块，处理摘要的保存与检索。
"""
import os
import json
import time
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, TypedDict

from config.config import SUMMARY_CONTENT_DIR


class SummaryMetadata(TypedDict):
    """摘要元数据类型定义"""
    id: str
    url: str
    timestamp: str
    timestamp_unix: float
    preview: str


class SummaryStorage:
    """
    摘要存储管理类，负责处理摘要的保存和检索
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        初始化摘要存储管理器
        
        Args:
            storage_dir: 摘要存储目录路径，如果为None则使用配置中的默认路径
        """
        self.storage_dir = Path(storage_dir or SUMMARY_CONTENT_DIR)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 摘要索引文件
        self.index_file = self.storage_dir / "summary_index.json"
        
        # 初始化索引文件(如果不存在)
        self._init_index_file()
    
    def _init_index_file(self):
        """初始化索引文件"""
        if not self.index_file.exists():
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)
    
    def _load_index(self) -> Dict[str, SummaryMetadata]:
        """
        加载摘要索引
        
        Returns:
            摘要索引字典，键为URL，值为摘要元数据
        """
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_index(self, index: Dict[str, SummaryMetadata]):
        """
        保存摘要索引
        
        Args:
            index: 摘要索引字典
        """
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    def _get_summary_path(self, summary_id: str) -> Path:
        """
        获取摘要文件路径
        
        Args:
            summary_id: 摘要ID
        
        Returns:
            摘要文件路径
        """
        return self.storage_dir / f"{summary_id}.txt"
    
    def _url_to_id(self, url: str) -> str:
        """
        将URL转换为唯一ID
        
        Args:
            url: 网页URL
        
        Returns:
            摘要ID
        """
        # 使用URL的MD5哈希前8位作为ID前缀
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        # 添加时间戳和随机元素
        unique_id = f"{url_hash}-{int(time.time())}-{uuid.uuid4().hex[:4]}"
        return unique_id
    
    def save_summary(self, url: str, content: str) -> str:
        """
        保存摘要
        
        Args:
            url: 网页URL
            content: 摘要内容
        
        Returns:
            摘要ID
        """
        # 加载索引
        index = self._load_index()
        
        # 检查是否已存在相同URL的摘要
        existing_id = None
        if url in index:
            existing_id = index[url]['id']
        
        # 生成新的摘要ID
        summary_id = existing_id or self._url_to_id(url)
        
        # 生成摘要文件路径
        summary_path = self._get_summary_path(summary_id)
        
        # 保存摘要内容
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 更新索引
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timestamp_unix = time.time()
        preview = content[:200].replace("\n", " ")
        
        index[url] = {
            'id': summary_id,
            'url': url,
            'timestamp': timestamp,
            'timestamp_unix': timestamp_unix,
            'preview': preview
        }
        
        self._save_index(index)
        
        return summary_id
    
    def get_summary_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        根据URL获取摘要
        
        Args:
            url: 网页URL
        
        Returns:
            摘要信息字典，包含'id'、'url'、'timestamp'、'content'等字段，
            如果未找到则返回None
        """
        # 加载索引
        index = self._load_index()
        
        # 检查URL是否存在
        if url not in index:
            return None
        
        # 获取摘要元数据
        metadata = index[url]
        summary_id = metadata['id']
        
        # 读取摘要内容
        summary_path = self._get_summary_path(summary_id)
        
        if not summary_path.exists():
            return None
            
        with open(summary_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 返回完整信息
        return {
            'id': summary_id,
            'url': url,
            'timestamp': metadata['timestamp'],
            'timestamp_unix': metadata['timestamp_unix'],
            'preview': metadata['preview'],
            'content': content
        }
    
    def get_summary_by_id(self, summary_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取摘要
        
        Args:
            summary_id: 摘要ID
        
        Returns:
            摘要信息字典，包含'id'、'url'、'timestamp'、'content'等字段，
            如果未找到则返回None
        """
        # 加载索引
        index = self._load_index()
        
        # 查找对应ID的URL
        target_url = None
        for url, metadata in index.items():
            if metadata['id'] == summary_id:
                target_url = url
                break
        
        if not target_url:
            return None
        
        # 调用URL获取方法
        return self.get_summary_by_url(target_url)
    
    def list_summaries(self, limit: int = 100, sort_by: str = 'timestamp_unix', reverse: bool = True) -> List[SummaryMetadata]:
        """
        列出已保存的摘要
        
        Args:
            limit: 返回结果的最大数量
            sort_by: 排序字段，支持'timestamp_unix'、'url'
            reverse: 是否逆序排序
        
        Returns:
            摘要元数据列表
        """
        # 加载索引
        index = self._load_index()
        
        # 提取元数据列表
        summaries = list(index.values())
        
        # 排序
        if sort_by in ['timestamp_unix', 'url']:
            summaries.sort(key=lambda x: x[sort_by], reverse=reverse)
        
        # 限制数量
        return summaries[:limit]
    
    def delete_summary(self, url_or_id: str) -> bool:
        """
        删除摘要
        
        Args:
            url_or_id: 摘要URL或ID
        
        Returns:
            是否删除成功
        """
        # 加载索引
        index = self._load_index()
        
        # 确定是URL还是ID
        is_id = True
        for stored_url, metadata in index.items():
            if stored_url == url_or_id:
                # 这是一个URL
                is_id = False
                break
        
        if is_id:
            # 找对应ID的URL
            target_url = None
            for url, metadata in index.items():
                if metadata['id'] == url_or_id:
                    target_url = url
                    break
            
            if not target_url:
                return False
            
            url = target_url
        else:
            url = url_or_id
        
        # 检查URL是否存在
        if url not in index:
            return False
        
        # 获取摘要元数据
        metadata = index[url]
        summary_id = metadata['id']
        
        # 删除摘要文件
        summary_path = self._get_summary_path(summary_id)
        if summary_path.exists():
            summary_path.unlink()
        
        # 更新索引
        del index[url]
        self._save_index(index)
        
        return True