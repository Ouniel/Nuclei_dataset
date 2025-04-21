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


## 运行截图

### POC管理界面
![POC管理界面](./docs/images/poc_management.png)

### 数据采集界面
![数据采集界面](./docs/images/data_collection.png)

### POC生成界面
![POC生成界面](./docs/images/poc_generation.png) 


## 许可证

本项目采用 **Apache License 2.0**，以下是关键条款摘要：


### 要求
- ❗ 必须保留原始版权声明和许可证文件  
- ❗ 修改后的文件需在显著位置说明变更内容  

### 禁止
- 🚫 使用项目商标直接宣传衍生作品  
- 🚫 追究原作者责任（免责条款）  

完整许可证文本见 [LICENSE](LICENSE) 文件。

---

## 免责声明

1. **合法用途**  
   本工具仅限用于**合法安全测试**和**授权渗透测试**。使用者需确保遵守当地法律法规，禁止用于未授权系统测试或恶意攻击。因滥用导致的后果由使用者自行承担。

2. **POC 准确性**  
   自动化生成的 POC 可能存在误报或漏报，**使用前请人工验证**。作者不保证 POC 的完整性和可靠性。

3. **第三方依赖**  
   本工具集成了 Deepseek 等第三方服务，其数据准确性、API 稳定性不受本项目控制。

4. **无担保条款**  
   作者不对工具的适用性、安全性提供任何明示或暗示担保，使用者需自行承担风险。

---

## 安全使用建议

1. **测试环境限制**  
   所有 POC 验证应在隔离的测试环境中进行，避免影响生产系统。

2. **权限控制**  
   运行本工具时使用最小必要权限账户，避免直接使用 root/Administrator。

3. **审计生成内容**  
   自动化生成的 POC 需经过安全团队人工审核后再部署。

4. **敏感信息保护**  
   禁止将工具配置为扫描互联网公共 IP 或敏感内网系统。

---
