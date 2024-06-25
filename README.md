![AutoGen](https://img.shields.io/badge/Framework-AutoGen-orange)
![Python版本](https://img.shields.io/badge/Python-3.8%2B-brightgreen)
![DeepSeek](https://img.shields.io/badge/API-DeepSeek-blueviolet)
# 项目说明文档，包含安装与使用指南 
# AutoGen网页内容摘要系统

这是一个使用AutoGen代理框架和DeepSeek API的网页内容摘要系统。该系统可以抓取任意网页内容，并自动生成摘要，特别适用于内容很长的网页。

## 特性


- 自动抓取网页内容
- 处理超长网页内容，自动分块处理
- 使用DeepSeek API生成高质量摘要
- 本地存储原始网页内容和摘要结果
- 命令行界面，方便使用和测试

## 安装

### 前提条件

- Python 3.8或更高版本
- DeepSeek API密钥

### 安装步骤

1. 克隆此仓库
git clone https://https://github.com/Wxysnx/AutoGenAgent.git cd AutoGenAgent


2. 安装依赖
pip install -r requirements.txt


3. 配置环境变量
- 编辑`.env`文件，填入您的DeepSeek API密钥
cp .env.example .env

用编辑器打开.env并填写API密钥

## 使用方法

### 命令行使用

1. 摘要单个网页
python run.py summarize --url https://example.com


2. 查看历史摘要
python run.py history


3. 阅读之前生成的摘要
python run.py read --url https://example.com

或者通过ID
python run.py read --id 12345


4. 显示帮助
python run.py --help


## 工作原理

本系统使用AutoGen代理框架组织多个智能代理协作完成任务：

1. **网页获取代理**: 负责抓取网页内容
2. **内容处理代理**: 清理和分块处理网页内容
3. **摘要生成代理**: 对内容生成摘要
4. **摘要整合代理**: 整合多个分块的摘要成为连贯的完整摘要