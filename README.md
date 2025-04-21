# Nuclei POC管理系统

一个用于管理Nuclei POC文件和自动化生成POC的PyQt5应用程序。

## 功能特点

### POC管理界面
- 本地POC文件的批量导入、导出和分类
- 关键词搜索、模糊搜索、标签筛选等功能
- 直接在界面内预览POC内容
- 支持一键执行POC验证

### 基于Deepseek的自动化POC编写
- 支持通过CVE编号自动收集漏洞信息
- 从阿里云漏洞库、Bing搜索、NVD等多个来源收集数据
- 利用Deepseek生成结构化POC数据
- 自动将JSON数据与Nuclei模板合并生成可执行POC

## 安装与使用

### 系统要求
- Python 3.7+
- 操作系统: Windows, Linux, macOS

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行应用
```bash
python main.py
```

## 配置

### API密钥设置
使用自动化POC编写功能需要设置以下API密钥:
- Deepseek API密钥


您可以在应用程序的"自动化POC编写"标签页中找到"API设置"按钮进行配置。

## 目录结构
```
project_root/
├── poc_management/        # POC管理模块
│   ├── __init__.py
│   ├── database.py        # JSON数据库处理
│   └── views.py           # POC管理界面视图
├── deepseek_automation/   # Deepseek自动化模块
│   ├── __init__.py
│   ├── api.py             # Deepseek API接口
│   ├── collector.py       # 数据采集功能
│   ├── generator.py       # POC生成器
│   ├── views.py           # 自动化界面视图
├── ui/                    # UI资源和设计文件
├── pocs/                  # 生成的POC保存目录
├── main.py                # 程序入口
└── requirements.txt       # 项目依赖
```

## 许可证
MIT License 

## 运行截图

### POC管理界面
![POC管理界面](./docs/images/poc_management.png)

### 数据采集界面
![数据采集界面](./docs/images/data_collection.png)

### POC生成界面
![POC生成界面](./docs/images/poc_generation.png) 