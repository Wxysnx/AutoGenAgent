![AutoGen](https://img.shields.io/badge/Framework-AutoGen-orange)
![Python版本](https://img.shields.io/badge/Python-3.8%2B-brightgreen)
![DeepSeek](https://img.shields.io/badge/API-DeepSeek-blueviolet)
# 项目说明文档，包含安装与使用指南 
# AutoGen网页内容摘要系统

基于Microsoft AutoGen框架构建的企业级网页内容智能提取系统。利用多代理协作架构实现从网页抓取、内容处理到智能摘要生成的完整工作流，特别适用于信息过载场景下的高效内容理解。

## 核心特性

- AutoGen多代理架构: 基于Microsoft AutoGen框架实现智能代理间的协作
- 无限页面处理: 能够处理任何长度的网页内容，通过智能分块突破上下文限制
- 高质量摘要: 集成DeepSeek API生成结构化、连贯的摘要内容
- 持久化存储: 完整的本地存储系统，支持历史查询和结果比较
- 用户友好: 简洁的命令行界面，简化操作流程


## 系统架构
AutoGenAgent采用多代理协作架构，包含四个专业化代理：
网页获取代理: 高效抓取网页内容，处理各种网页格式
内容处理代理: 清理HTML标记，智能分块处理长文本
摘要生成代理: 为每个内容块生成精准摘要
摘要整合代理: 将多块摘要整合为连贯、结构化的完整摘要

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