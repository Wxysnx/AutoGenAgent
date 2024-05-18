# 配置管理模块，负责加载环境变量和配置 
"""
配置管理模块，负责加载环境变量和系统配置。
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 确定项目根目录
ROOT_DIR = Path(__file__).parent.parent

# 加载.env文件中的环境变量
load_dotenv(ROOT_DIR / '.env')

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_API_BASE = os.getenv('DEEPSEEK_API_BASE', 'https://api.deepseek.com')

# 确保API密钥已配置
if not DEEPSEEK_API_KEY:
    raise ValueError(
        "DeepSeek API密钥未配置。请复制.env.example为.env，"
        "并设置您的DEEPSEEK_API_KEY。"
    )

# 存储配置
WEBPAGE_CONTENT_DIR = os.getenv('WEBPAGE_CONTENT_DIR', str(ROOT_DIR / 'data' / 'webpage_content'))
SUMMARY_CONTENT_DIR = os.getenv('SUMMARY_CONTENT_DIR', str(ROOT_DIR / 'data' / 'summaries'))

# 确保存储目录存在
Path(WEBPAGE_CONTENT_DIR).mkdir(parents=True, exist_ok=True)
Path(SUMMARY_CONTENT_DIR).mkdir(parents=True, exist_ok=True)

# 系统配置
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')

# 模型配置
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "deepseek-chat")  # 默认使用的DeepSeek模型
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "8192"))  # 单次API调用的最大token数
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "6000"))  # 内容分块大小，单位为token

# 功能配置
SUMMARY_PREFIX = "## 网页内容摘要：\n\n"