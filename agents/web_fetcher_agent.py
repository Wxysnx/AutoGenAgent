# 网页获取代理，调用WebpageContentFetcher 
"""
网页获取代理，负责调用WebpageContentFetcher获取和存储网页内容。
"""
import os
import hashlib
from pathlib import Path
from typing import Optional

from web_content.webpage_content_fetcher import WebpageContentFetcher
from config.config import WEBPAGE_CONTENT_DIR


class WebFetcherAgent:
    """
    网页获取代理，负责抓取和存储网页内容
    """
    
    def __init__(self):
        """初始化网页获取代理"""
        self.content_dir = Path(WEBPAGE_CONTENT_DIR)
        self.content_dir.mkdir(parents=True, exist_ok=True)
        self.fetcher = WebpageContentFetcher()
        self.content_index_file = self.content_dir / "content_index.json"
        
        # 确保索引文件存在
        if not self.content_index_file.exists():
            self._init_content_index()
    
    def _init_content_index(self):
        """初始化内容索引文件"""
        import json
        with open(self.content_index_file, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    
    def _get_content_path(self, url: str) -> Path:
        """
        获取URL对应的内容文件路径
        
        Args:
            url: 网页URL
        
        Returns:
            对应的文件路径
        """
        # 使用URL的MD5哈希作为文件名
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.content_dir / f"{url_hash}.txt"
    
    def _update_content_index(self, url: str, file_path: Path):
        """
        更新内容索引
        
        Args:
            url: 网页URL
            file_path: 内容文件路径
        """
        import json
        try:
            with open(self.content_index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            index = {}
        
        index[url] = str(file_path.relative_to(self.content_dir))
        
        with open(self.content_index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    async def fetch_webpage(self, url: str) -> Optional[str]:
        """
        获取网页内容，如果已经存在本地缓存则直接返回缓存内容
        
        Args:
            url: 网页URL
        
        Returns:
            网页内容文本，如果获取失败则返回None
        """
        content_path = self._get_content_path(url)
        
        # 检查是否已经有缓存
        if content_path.exists():
            print(f"找到缓存的网页内容: {content_path}")
            with open(content_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        # 没有缓存，需要抓取
        print(f"正在获取网页内容: {url}")
        try:
            content = self.fetcher.fetch(url)
            
            # 保存内容到文件
            with open(content_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 更新索引
            self._update_content_index(url, content_path)
            
            return content
            
        except Exception as e:
            print(f"获取网页内容失败: {str(e)}")
            return None