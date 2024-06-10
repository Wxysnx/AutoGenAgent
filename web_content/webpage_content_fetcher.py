# 网页内容获取工具 
"""
网页内容获取模块，负责抓取和处理网页内容。
"""
import requests
import time
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import re
from bs4 import BeautifulSoup
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WebpageContentFetcher:
    """
    网页内容获取工具，用于抓取和清理网页内容
    """
    
    def __init__(self, 
                 timeout: int = 30, 
                 max_retries: int = 3, 
                 retry_wait: int = 2,
                 user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"):
        """
        初始化网页内容获取器
        
        Args:
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
            retry_wait: 重试等待时间(秒)
            user_agent: 请求使用的User-Agent
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_wait = retry_wait
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def fetch(self, url: str) -> str:
        """
        获取网页内容
        
        Args:
            url: 网页URL
        
        Returns:
            处理后的网页内容文本
        
        Raises:
            ValueError: URL无效
            ConnectionError: 连接错误
            TimeoutError: 请求超时
            Exception: 其他错误
        """
        # 验证URL
        if not self._is_valid_url(url):
            raise ValueError(f"无效的URL: {url}")
        
        # 尝试获取内容
        html_content = None
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"正在获取网页 {url}，尝试 {attempt + 1}/{self.max_retries}")
                response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
                response.raise_for_status()
                html_content = response.text
                break
            except requests.exceptions.Timeout as e:
                logger.warning(f"请求超时: {str(e)}")
                last_error = TimeoutError(f"请求超时: {str(e)}")
                time.sleep(self.retry_wait)
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"连接错误: {str(e)}")
                last_error = ConnectionError(f"连接错误: {str(e)}")
                time.sleep(self.retry_wait)
            except requests.exceptions.HTTPError as e:
                logger.warning(f"HTTP错误: {str(e)}")
                last_error = Exception(f"HTTP错误: {str(e)}")
                time.sleep(self.retry_wait)
            except Exception as e:
                logger.warning(f"获取网页内容时出现未知错误: {str(e)}")
                last_error = Exception(f"获取网页内容时出现未知错误: {str(e)}")
                time.sleep(self.retry_wait)
        
        if html_content is None:
            if last_error:
                raise last_error
            else:
                raise Exception(f"无法获取网页内容: {url}")
        
        # 处理内容
        return self._process_content(html_content, url)
    
    def _is_valid_url(self, url: str) -> bool:
        """
        验证URL是否有效
        
        Args:
            url: 网页URL
        
        Returns:
            URL是否有效
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except:
            return False
    
    def _process_content(self, html_content: str, url: str) -> str:
        """
        处理HTML内容，提取主要文本
        
        Args:
            html_content: 原始HTML内容
            url: 网页URL，用于特定网站的定制处理
        
        Returns:
            处理后的文本内容
        """
        # 使用BeautifulSoup解析HTML
        try:
            soup = BeautifulSoup(html_content, 'lxml')  # 使用lxml解析器
        except:
            # 降级到html.parser
            soup = BeautifulSoup(html_content, 'html.parser')
        
        # 删除不需要的元素
        self._remove_unwanted_elements(soup)
        
        # 获取标题
        title = self._get_title(soup)
        
        # 获取主要内容
        main_content = self._extract_main_content(soup, url)
        
        # 组合内容
        if title:
            processed_content = f"# {title}\n\n{main_content}"
        else:
            processed_content = main_content
        
        return processed_content
    
    def _remove_unwanted_elements(self, soup: BeautifulSoup):
        """
        从BeautifulSoup对象中删除不需要的元素
        
        Args:
            soup: BeautifulSoup对象
        """
        # 删除脚本和样式
        for element in soup(['script', 'style', 'iframe', 'noscript', 'head', 'meta', 'link']):
            element.decompose()
        
        # 删除可能是导航、页眉、页脚、广告等的元素
        selectors = [
            'header', 'footer', 'nav',
            '.header', '.footer', '.nav', '.navigation', '.menu',
            '.sidebar', '.advertisement', '.ads', '.ad',
            '#header', '#footer', '#nav', '#sidebar', '#menu',
            '[class*="cookie"]', '[class*="banner"]', '[class*="popup"]',
            '[id*="cookie"]', '[id*="banner"]', '[id*="popup"]'
        ]
        
        for selector in selectors:
            try:
                for element in soup.select(selector):
                    element.decompose()
            except:
                pass
    
    def _get_title(self, soup: BeautifulSoup) -> str:
        """
        从BeautifulSoup对象中提取标题
        
        Args:
            soup: BeautifulSoup对象
        
        Returns:
            网页标题
        """
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        
        # 尝试其他标题元素
        h1 = soup.find('h1')
        if h1 and h1.text:
            return h1.text.strip()
        
        return ""
    
    def _extract_main_content(self, soup: BeautifulSoup, url: str) -> str:
        """
        从BeautifulSoup对象中提取主要内容
        
        Args:
            soup: BeautifulSoup对象
            url: 网页URL，用于特定网站的定制处理
        
        Returns:
            主要内容文本
        """
        # 针对特定网站的定制处理
        domain = urlparse(url).netloc.lower()
        
        # 针对常见内容区域的选择器
        content_selectors = [
            'article', 'main', '.content', '.post', '.article', '.post-content',
            '#content', '#main', '#article', '.entry-content', '.post-body',
            '[role="main"]', '.main-content'
        ]
        
        # 尝试找到主要内容容器
        main_element = None
        for selector in content_selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    # 选择文本量最多的元素
                    main_element = max(elements, key=lambda e: len(e.text.strip()))
                    break
            except:
                continue
        
        if main_element:
            content = main_element.get_text(separator='\n', strip=True)
        else:
            # 如果没有找到主要内容容器，则使用整个body
            content = soup.get_text(separator='\n', strip=True)
        
        # 去除连续多行空白
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        # 去除超长的行（可能是未处理的代码或其他非正常内容）
        lines = []
        for line in content.splitlines():
            if len(line) < 1000:  # 设置一个合理的行长度上限
                lines.append(line)
        
        return '\n'.join(lines)