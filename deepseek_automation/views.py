"""
Deepseek自动化POC编写界面视图模块
包含CVE输入、数据采集和POC生成功能
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                            QPushButton, QLabel, QTextEdit, QProgressBar,
                            QMessageBox, QFileDialog, QGroupBox, QFormLayout,
                            QListWidget, QListWidgetItem, QSplitter, QTabWidget,
                            QDialog, QCheckBox, QRadioButton, QStackedWidget,
                            QFrame, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QSettings, QUrl
from PyQt5.QtGui import QIcon, QColor, QFont, QTextCursor, QPixmap, QDesktopServices

import os
import json
import re
import time

from .api import DeepseekAPI
from .collector import CveCollector
from .generator import PocGenerator
from poc_management.database import PocDatabase


class ApiKeySettingsDialog(QDialog):
    """API密钥设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API密钥设置")
        self.setMinimumWidth(400)
        
        # 加载设置
        self.settings = QSettings("NucleiPOCManager", "ApiSettings")
        
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 创建表单
        form_layout = QFormLayout()
        
        # Deepseek API密钥
        self.deepseek_api_key = QLineEdit()
        self.deepseek_api_key.setEchoMode(QLineEdit.Password)
        self.deepseek_api_key.setPlaceholderText("输入Deepseek API密钥")
        form_layout.addRow("Deepseek API密钥:", self.deepseek_api_key)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self._save_settings)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # 设置样式
        self._set_style()
    
    def _set_style(self):
        """设置控件样式"""
        # 按钮样式
        button_style = """
            QPushButton {
                background-color: #007aff;
                color: white;
                border-radius: 8px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0069d9;
            }
            QPushButton:pressed {
                background-color: #0062cc;
            }
        """
        self.save_button.setStyleSheet(button_style)
        
        cancel_button_style = """
            QPushButton {
                background-color: #8e8e93;
                color: white;
                border-radius: 8px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7a7a7e;
            }
            QPushButton:pressed {
                background-color: #68686c;
            }
        """
        self.cancel_button.setStyleSheet(cancel_button_style)
        
        # 输入框样式
        input_style = """
            QLineEdit {
                border-radius: 8px;
                padding: 8px;
                background-color: #f5f5f7;
                border: 1px solid #d1d1d6;
            }
            QLineEdit:focus {
                border: 1px solid #007aff;
            }
        """
        self.deepseek_api_key.setStyleSheet(input_style)
    
    def _load_settings(self):
        """加载设置"""
        self.deepseek_api_key.setText(self.settings.value("deepseek_api_key", ""))
    
    def _save_settings(self):
        """保存设置"""
        # 保存设置
        self.settings.setValue("deepseek_api_key", self.deepseek_api_key.text())
        
        QMessageBox.information(self, "保存成功", "API密钥设置已保存")
        self.accept()


class CveInputWidget(QWidget):
    """CVE输入组件"""
    
    cve_submitted = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("CVE漏洞编号输入")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 输入表单
        input_layout = QHBoxLayout()
        
        self.cve_input = QLineEdit()
        self.cve_input.setPlaceholderText("输入CVE编号，例如：CVE-2021-44228")
        
        self.submit_button = QPushButton("开始收集")
        self.submit_button.clicked.connect(self._on_submit)
        
        input_layout.addWidget(QLabel("CVE编号:"))
        input_layout.addWidget(self.cve_input)
        input_layout.addWidget(self.submit_button)
        
        layout.addLayout(input_layout)
        
        # 说明信息
        info_label = QLabel("输入有效的CVE编号，系统将自动从多个来源收集相关信息，并生成POC")
        info_label.setStyleSheet("color: #8e8e93; font-style: italic;")
        layout.addWidget(info_label)
        
        # 设置样式
        self._set_style()
    
    def _set_style(self):
        """设置控件样式"""
        # 输入框样式
        self.cve_input.setStyleSheet("""
            QLineEdit {
                border-radius: 8px;
                padding: 8px;
                background-color: #f5f5f7;
                border: 1px solid #d1d1d6;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #007aff;
            }
        """)
        
        # 按钮样式
        self.submit_button.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
                color: white;
                border-radius: 8px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0069d9;
            }
            QPushButton:pressed {
                background-color: #0062cc;
            }
        """)
    
    def _on_submit(self):
        """提交CVE编号"""
        cve_id = self.cve_input.text().strip()
        
        # 验证CVE格式
        if not self._validate_cve(cve_id):
            QMessageBox.warning(self, "格式错误", "请输入有效的CVE编号，例如：CVE-2021-44228")
            return
        
        self.cve_submitted.emit(cve_id)
    
    def _validate_cve(self, cve_id):
        """验证CVE ID格式"""
        pattern = r"^CVE-\d{4}-\d+$"
        return bool(re.match(pattern, cve_id))


class DataCollectionWidget(QWidget):
    """数据采集组件"""
    
    collection_completed = pyqtSignal(str, list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化收集器
        self.collector = CveCollector(self)
        
        # 连接信号
        self.collector.collection_started.connect(self._on_collection_started)
        self.collector.collection_progress.connect(self._on_collection_progress)
        self.collector.url_collected.connect(self._on_url_collected)
        self.collector.collection_completed.connect(self._on_collection_completed)
        self.collector.collection_error.connect(self._on_collection_error)
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_layout = QHBoxLayout()
        title_label = QLabel("数据采集")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_layout.addWidget(title_label)
        
        self.stop_button = QPushButton("停止采集")
        self.stop_button.clicked.connect(self._stop_collection)
        self.stop_button.setEnabled(False)
        title_layout.addStretch()
        title_layout.addWidget(self.stop_button)
        
        layout.addLayout(title_layout)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 数据源列表组
        urls_group = QGroupBox("收集到的数据源")
        urls_layout = QVBoxLayout(urls_group)
        
        self.url_list = QListWidget()
        self.url_list.itemDoubleClicked.connect(self._on_url_double_clicked)
        urls_layout.addWidget(self.url_list)
        
        splitter.addWidget(urls_group)
        
        # 采集内容组
        content_group = QGroupBox("采集内容")
        content_layout = QVBoxLayout(content_group)
        
        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        content_layout.addWidget(self.content_text)
        
        splitter.addWidget(content_group)
        
        layout.addWidget(splitter)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 状态信息
        self.status_label = QLabel("等待开始采集数据...")
        self.status_label.setStyleSheet("color: #8e8e93;")
        layout.addWidget(self.status_label)
        
        # 设置样式
        self._set_style()
    
    def _set_style(self):
        """设置控件样式"""
        # 列表样式
        self.url_list.setStyleSheet("""
            QListWidget {
                border-radius: 10px;
                padding: 5px;
                background-color: #f5f5f7;
            }
            QListWidget::item {
                border-radius: 5px;
                padding: 5px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: #007aff;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e0e0e2;
            }
        """)
        
        # 文本框样式
        self.content_text.setStyleSheet("""
            QTextEdit {
                border-radius: 10px;
                padding: 10px;
                background-color: #f5f5f7;
                font-family: "Courier New", monospace;
            }
        """)
        
        # 进度条样式
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #d1d1d6;
                border-radius: 8px;
                background-color: #f5f5f7;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #34c759;
                border-radius: 8px;
            }
        """)
        
        # 按钮样式
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #ff3b30;
                color: white;
                border-radius: 6px;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background-color: #d63a34;
            }
            QPushButton:pressed {
                background-color: #b02c27;
            }
            QPushButton:disabled {
                background-color: #ffcbc8;
            }
        """)
    
    def collect_data(self, cve_id):
        """
        开始数据采集
        
        Args:
            cve_id (str): CVE编号
        """
        # 清空之前的结果
        self.url_list.clear()
        self.content_text.clear()
        self.progress_bar.setValue(0)
        
        # 更新状态
        self.status_label.setText(f"正在收集 {cve_id} 的相关数据...")
        
        # 更新按钮状态
        self.stop_button.setEnabled(True)
        
        # 开始收集
        self.collector.collect(cve_id)
    
    def _stop_collection(self):
        """停止数据采集"""
        self.collector.cancel_collection()
        self.status_label.setText("数据采集已停止")
        self.stop_button.setEnabled(False)
    
    def _on_collection_started(self):
        """收集开始处理"""
        self.progress_bar.setValue(0)
        self.stop_button.setEnabled(True)
    
    def _on_collection_progress(self, current, total):
        """收集进度处理"""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
            self.status_label.setText(f"正在处理数据源 {current}/{total}...")
    
    def _on_url_collected(self, url, source):
        """URL收集处理"""
        item = QListWidgetItem(f"{source}: {url}")
        item.setData(Qt.UserRole, url)
        self.url_list.addItem(item)
    
    def _on_collection_completed(self, content, urls):
        """收集完成处理"""
        # 显示内容
        self.content_text.setText(content)
        
        # 更新状态
        self.status_label.setText(f"数据采集完成，共收集到 {len(urls)} 个数据源")
        self.progress_bar.setValue(100)
        self.stop_button.setEnabled(False)
        
        # 发送信号
        self.collection_completed.emit(content, urls)
    
    def _on_collection_error(self, error_msg):
        """收集错误处理"""
        QMessageBox.warning(self, "采集错误", error_msg)
        self.status_label.setText(f"采集过程中发生错误: {error_msg}")
        self.stop_button.setEnabled(False)
    
    def _on_url_double_clicked(self, item):
        """URL项目双击处理"""
        url = item.data(Qt.UserRole)
        # 使用默认浏览器打开URL
        QDesktopServices.openUrl(QUrl(url)) 


class PocGenerationWidget(QWidget):
    """POC生成组件"""
    
    generation_completed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化API和生成器
        self.deepseek_api = DeepseekAPI(self)
        self.poc_generator = PocGenerator(self)  # 保留初始化以避免错误
        
        # 连接信号
        self.deepseek_api.request_started.connect(self._on_api_request_started)
        self.deepseek_api.request_finished.connect(self._on_api_request_finished)
        self.deepseek_api.request_error.connect(self._on_api_request_error)
        self.deepseek_api.response_received.connect(self._on_api_response_received)
        
        # 不再使用PocGenerator生成POC，但保留初始化以兼容其他功能
        # self.poc_generator.generation_started.connect(self._on_generation_started)
        # self.poc_generator.generation_finished.connect(self._on_generation_finished)
        # self.poc_generator.generation_error.connect(self._on_generation_error)
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_layout = QHBoxLayout()
        title_label = QLabel("POC生成")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_layout.addWidget(title_label)
        
        self.api_settings_button = QPushButton("API设置")
        self.api_settings_button.clicked.connect(self._show_api_settings)
        title_layout.addStretch()
        title_layout.addWidget(self.api_settings_button)
        
        layout.addLayout(title_layout)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 生成选项
        options_group = QGroupBox("生成选项")
        options_layout = QFormLayout(options_group)
        
        # 提示文本编辑
        prompt_label = QLabel("Deepseek提示:")
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("在此修改Deepseek提示...")
        
        # 设置默认提示
        default_prompt = """请分析以下关于安全漏洞的信息，并生成一个用于漏洞验证的Nuclei POC（Proof of Concept）。

请按照以下Nuclei YAML模板格式输出完整的POC文件内容:

```yaml
id: {{漏洞ID或CVE编号}}

info:
  name: {{漏洞名称}} {{版本信息（如有）}} - {{漏洞类型}}
  author: nuclei-poc-generator
  severity: {{严重等级：critical/high/medium/low/info}}
  description: |
    {{详细的漏洞描述，包括影响版本、漏洞原理等}}
  reference:
    - {{参考链接1}}
    - {{参考链接2}}
  classification:
    cvss-metrics: {{CVSS指标，如CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:L/A:L}}
    cvss-score: {{CVSS评分，如6.3}}
    cve-id: {{CVE编号，如有}}
  metadata:
    fofa-query: {{FOFA搜索语句}}
    google-query: {{Google搜索语句}}
    shodan-query: {{Shodan搜索语句}}
  tags: {{标签列表，逗号分隔}}

http:
  - method: {{HTTP方法：GET/POST/PUT等}}
    path:
      - "{{BaseURL}}{{URI路径}}"
    
    # 可选：HTTP请求头
    headers:
      {{请求头名称}}: {{请求头值}}
    
    # 可选：POST请求体
    body: |
      {{请求体内容}}
    
    # 可选：提取器，用于从响应中提取信息
    extractors:
      - type: regex
        name: version
        part: body
        group: 1
        regex:
          - "{{正则表达式模式}}"
    
    # 匹配器条件：and表示所有匹配器都需要满足，or表示任一匹配器满足即可
    matchers-condition: and
    matchers:
      # 状态码匹配器
      - type: status
        status:
          - {{HTTP状态码，如200}}
      
      # 关键词匹配器
      - type: word
        words:
          - "{{特征关键词1}}"
          - "{{特征关键词2}}"
        part: body
        condition: and
      
      # 可选：正则表达式匹配器
      - type: regex
        regex:
          - "{{正则表达式}}"
        part: body
      
      # 可选：DSL条件匹配器
      - type: dsl
        dsl:
          - "{{DSL表达式，如检查版本号}}"
```

请确保：
1. 根据收集的CVE信息，填充所有必要字段，特别是漏洞路径、请求参数和响应特征
2. 严格遵循YAML格式，注意缩进和引号
3. 选择合适的匹配器（matchers）来验证漏洞是否存在
4. 提供准确的FOFA、Google或Shodan查询语句，帮助定位可能存在漏洞的目标
5. 不要在模板以外添加额外解释

完整输出应该是一个可以直接保存为.yaml文件并被Nuclei引擎执行的POC。
"""
        
        self.prompt_edit.setText(default_prompt)
        
        options_layout.addRow(prompt_label, self.prompt_edit)
        
        # POC保存目录
        dir_layout = QHBoxLayout()
        self.poc_dir_input = QLineEdit()
        self.poc_dir_input.setReadOnly(True)
        
        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self._browse_poc_dir)
        
        dir_layout.addWidget(self.poc_dir_input)
        dir_layout.addWidget(self.browse_button)
        
        options_layout.addRow("POC保存目录:", dir_layout)
        
        # 加载默认保存目录
        self.settings = QSettings("NucleiPOCManager", "PocGenerator")
        default_poc_dir = self.settings.value("poc_dir", "pocs")
        self.poc_dir_input.setText(default_poc_dir)
        self.poc_generator.set_poc_dir(default_poc_dir)
        
        splitter.addWidget(options_group)
        
        # 生成结果
        result_group = QGroupBox("生成结果")
        result_layout = QVBoxLayout(result_group)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        result_layout.addWidget(self.result_text)
        
        splitter.addWidget(result_group)
        
        # 设置分割比例
        splitter.setSizes([200, 400])
        
        layout.addWidget(splitter)
        
        # 按钮行
        button_layout = QHBoxLayout()
        
        self.generate_button = QPushButton("生成POC")
        self.generate_button.clicked.connect(self._on_generate_poc)
        self.generate_button.setEnabled(False)  # 初始禁用
        
        self.save_button = QPushButton("保存到数据库")
        self.save_button.clicked.connect(self._on_save_poc)
        self.save_button.setEnabled(False)  # 初始禁用
        
        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 状态信息
        self.status_label = QLabel("等待数据采集完成...")
        self.status_label.setStyleSheet("color: #8e8e93;")
        layout.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 设置样式
        self._set_style()
        
        # 内部数据
        self.collected_content = ""
        self.collected_urls = []
        self.generated_json = None
        self.generated_yaml = None
        self.generated_poc_path = None
    
    def _set_style(self):
        """设置控件样式"""
        # 文本框样式
        text_edit_style = """
            QTextEdit {
                border-radius: 10px;
                padding: 10px;
                background-color: #f5f5f7;
                font-family: "Courier New", monospace;
            }
        """
        self.prompt_edit.setStyleSheet(text_edit_style)
        self.result_text.setStyleSheet(text_edit_style)
        
        # 按钮样式
        button_style = """
            QPushButton {
                background-color: #007aff;
                color: white;
                border-radius: 8px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0069d9;
            }
            QPushButton:pressed {
                background-color: #0062cc;
            }
            QPushButton:disabled {
                background-color: #b5d4ff;
                color: #eeeeee;
            }
        """
        self.generate_button.setStyleSheet(button_style)
        self.save_button.setStyleSheet(button_style)
        
        self.api_settings_button.setStyleSheet("""
            QPushButton {
                background-color: #8e8e93;
                color: white;
                border-radius: 6px;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background-color: #7a7a7e;
            }
            QPushButton:pressed {
                background-color: #68686c;
            }
        """)
        
        self.browse_button.setStyleSheet("""
            QPushButton {
                background-color: #8e8e93;
                color: white;
                border-radius: 6px;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background-color: #7a7a7e;
            }
            QPushButton:pressed {
                background-color: #68686c;
            }
        """)
        
        # 输入框样式
        self.poc_dir_input.setStyleSheet("""
            QLineEdit {
                border-radius: 8px;
                padding: 8px;
                background-color: #f5f5f7;
                border: 1px solid #d1d1d6;
            }
        """)
        
        # 进度条样式
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #d1d1d6;
                border-radius: 8px;
                background-color: #f5f5f7;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #34c759;
                border-radius: 8px;
            }
        """)
    
    def set_collected_data(self, content, urls):
        """
        设置收集到的数据
        
        Args:
            content (str): 收集到的内容
            urls (list): 收集到的URL列表
        """
        self.collected_content = content
        self.collected_urls = urls
        
        # 更新默认提示，将URL列表添加进去
        current_prompt = self.prompt_edit.toPlainText()
        
        # 如果存在URL，添加到提示中
        if urls and len(urls) > 0:
            url_section = "\n\n参考URL链接：\n"
            for i, url in enumerate(urls):
                url_section += f"{i+1}. {url}\n"
            
            # 检查提示中是否已经有URL部分
            if "参考URL链接：" not in current_prompt:
                # 在JSON示例前添加URL部分
                if "输出格式：" in current_prompt:
                    # 在输出格式前插入
                    parts = current_prompt.split("输出格式：", 1)
                    updated_prompt = parts[0] + url_section + "\n输出格式：" + parts[1]
                else:
                    # 添加到最后
                    updated_prompt = current_prompt + url_section
                
                self.prompt_edit.setText(updated_prompt)
        
        self.generate_button.setEnabled(True)
        self.status_label.setText(f"数据采集完成，可以生成POC。共有 {len(urls)} 个数据源")
    
    def _browse_poc_dir(self):
        """浏览POC保存目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择POC保存目录", self.poc_dir_input.text()
        )
        
        if directory:
            self.poc_dir_input.setText(directory)
            self.poc_generator.set_poc_dir(directory)
    
    def _on_generate_poc(self):
        """生成POC"""
        # 检查是否设置了API密钥
        api_key = self.deepseek_api.get_api_key()
        if not api_key:
            self._show_api_settings()
            if not self.deepseek_api.get_api_key():
                QMessageBox.warning(self, "API密钥缺失", "请先设置Deepseek API密钥")
                return
        
        # 检查是否有收集的数据
        if not self.collected_content:
            QMessageBox.warning(self, "数据缺失", "请先完成数据采集")
            return
        
        # 获取提示
        prompt = self.prompt_edit.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "提示缺失", "请输入Deepseek提示")
            return
        
        # 确保提示中包含收集到的URL列表
        if self.collected_urls and len(self.collected_urls) > 0:
            if "参考URL链接：" not in prompt:
                url_section = "\n\n参考URL链接：\n"
                for i, url in enumerate(self.collected_urls):
                    url_section += f"{i+1}. {url}\n"
                
                # 在JSON示例前添加URL部分
                if "输出格式：" in prompt:
                    # 在输出格式前插入
                    parts = prompt.split("输出格式：", 1)
                    prompt = parts[0] + url_section + "\n输出格式：" + parts[1]
                else:
                    # 添加到最后
                    prompt = prompt + url_section
            
            # 更新编辑框
            self.prompt_edit.setText(prompt)
        
        # 构建完整内容(提示 + 收集的内容)
        complete_content = f"{prompt}\n\n收集的信息：\n\n{self.collected_content}"
        
        # 更新状态
        self.status_label.setText("正在使用Deepseek生成POC...")
        self.progress_bar.setValue(20)  # 起始进度设为20%
        
        # 禁用按钮
        self.generate_button.setEnabled(False)
        
        # 调用API
        self.deepseek_api.generate_poc(prompt, complete_content)
    
    def _on_api_request_started(self):
        """API请求开始处理"""
        self.status_label.setText("正在请求Deepseek API...")
        self.progress_bar.setValue(40)  # 将进度更新为40%
    
    def _on_api_request_finished(self):
        """API请求完成处理"""
        self.status_label.setText("Deepseek API请求完成")
        self.progress_bar.setValue(80)
    
    def _on_api_request_error(self, error_msg):
        """API请求错误处理"""
        self.status_label.setText(f"Deepseek API请求失败: {error_msg}")
        self.progress_bar.setValue(0)
        self.generate_button.setEnabled(True)
        QMessageBox.warning(self, "API错误", error_msg)
    
    def _on_api_response_received(self, data):
        """API响应处理"""
        # 检查数据中是否包含YAML内容
        if "yaml_content" in data:
            yaml_content = data["yaml_content"]
            self.generated_yaml = yaml_content
            
            # 显示YAML
            self.result_text.setText(f"```yaml\n{yaml_content}\n```")
            
            # 更新状态
            self.status_label.setText("Deepseek生成成功，正在生成POC文件...")
            self.progress_bar.setValue(90)  # 将进度设为90%，为最后的文件保存留出空间
            
            # 直接保存YAML文件
            try:
                # 从YAML中提取ID
                id_match = re.search(r"id:\s*([^\s\n]+)", yaml_content)
                poc_id = id_match.group(1) if id_match else f"nuclei-poc-{int(time.time())}"
                
                # 从YAML中提取name
                name_match = re.search(r"name:\s*(.+?)\n", yaml_content)
                poc_name = name_match.group(1).strip() if name_match else "未命名POC"
                
                # 从YAML中提取description
                desc_match = re.search(r"description:\s*\|\s*\n((\s{4}.+\n)+)", yaml_content)
                poc_description = desc_match.group(1).strip() if desc_match else ""
                
                # 从YAML中提取severity
                severity_match = re.search(r"severity:\s*([^\s\n]+)", yaml_content)
                poc_severity = severity_match.group(1) if severity_match else "medium"
                
                # 从YAML中提取tags
                tags_match = re.search(r"tags:\s*(.+?)\n", yaml_content)
                poc_tags_str = tags_match.group(1).strip() if tags_match else ""
                poc_tags = [tag.strip() for tag in poc_tags_str.strip("[]").split(",")]
                
                # 从YAML中提取reference
                references = []
                reference_pattern = r"reference:\s*\n(\s{4}-\s*.+\n)+"
                reference_match = re.search(reference_pattern, yaml_content)
                if reference_match:
                    ref_block = reference_match.group(0)
                    ref_lines = re.findall(r"\s{4}-\s*(.+)", ref_block)
                    references = [ref.strip() for ref in ref_lines]
                
                # 构建POC数据
                self.generated_json = {
                    "id": poc_id,
                    "name": poc_name,
                    "description": poc_description,
                    "severity": poc_severity,
                    "tags": poc_tags,
                    "references": references
                }
                
                # 生成文件名和路径
                file_name = f"{poc_id}.yaml"
                file_path = os.path.join(self.poc_dir_input.text(), file_name)
                
                # 保存文件
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(yaml_content)
                
                self.generated_poc_path = file_path
                
                # 执行生成完成后的操作
                self.status_label.setText(f"POC生成完成，文件已保存到: {file_path}")
                self.progress_bar.setValue(100)
                self.save_button.setEnabled(True)
                self.generate_button.setEnabled(True)
                self.generation_completed.emit(file_path)
                
                # 将YAML内容添加到结果显示
                self.result_text.append("\n\n# 已保存的POC文件路径:\n" + file_path)
                
            except Exception as e:
                self.status_label.setText(f"处理YAML内容失败: {str(e)}")
                self.progress_bar.setValue(0)
                self.generate_button.setEnabled(True)
                QMessageBox.warning(self, "生成错误", f"处理YAML内容失败: {str(e)}")
        else:
            self.status_label.setText("API响应格式错误，未包含YAML内容")
            self.progress_bar.setValue(0)
            self.generate_button.setEnabled(True)
    
    def _on_generation_started(self):
        """生成开始处理"""
        self.status_label.setText("正在生成POC文件...")
        self.progress_bar.setValue(80)
    
    def _on_generation_finished(self, file_path):
        """生成完成处理"""
        self.generated_poc_path = file_path
        
        # 读取生成的文件
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                poc_content = f.read()
                
            # 添加到结果显示
            self.result_text.append("\n\n# 生成的POC文件内容\n\n```yaml\n" + poc_content + "\n```")
            
            # 更新状态
            self.status_label.setText(f"POC生成完成，文件已保存到: {file_path}")
            self.progress_bar.setValue(100)
            
            # 启用保存按钮
            self.save_button.setEnabled(True)
            self.generate_button.setEnabled(True)
            
            # 发送信号
            self.generation_completed.emit(file_path)
            
        except Exception as e:
            self.status_label.setText(f"读取生成的POC文件失败: {str(e)}")
            self.progress_bar.setValue(0)
    
    def _on_generation_error(self, error_msg):
        """生成错误处理"""
        self.status_label.setText(f"生成POC文件失败: {error_msg}")
        self.progress_bar.setValue(0)
        self.generate_button.setEnabled(True)
        QMessageBox.warning(self, "生成错误", error_msg)
    
    def _on_save_poc(self):
        """保存POC到数据库"""
        if not self.generated_json or not self.generated_poc_path:
            QMessageBox.warning(self, "数据缺失", "没有可以保存的POC")
            return
        
        try:
            # 创建POC记录
            poc_data = {
                "id": self.generated_json.get("id", ""),
                "name": self.generated_json.get("name", ""),
                "path": self.generated_poc_path,
                "description": self.generated_json.get("description", ""),
                "severity": self.generated_json.get("severity", "medium"),
                "tags": self.generated_json.get("tags", []),
                "references": self.generated_json.get("references", [])
            }
            
            # 保存到数据库
            db = PocDatabase()
            poc_id = db.add_poc(poc_data)
            
            QMessageBox.information(
                self, "保存成功", 
                f"POC已保存到数据库，ID: {poc_id}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "保存失败", 
                f"保存POC到数据库失败: {str(e)}"
            )
    
    def _show_api_settings(self):
        """显示API设置对话框"""
        dialog = ApiKeySettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # 更新API密钥
            deepseek_api_key = dialog.settings.value("deepseek_api_key", "")
            self.deepseek_api.set_api_key(deepseek_api_key) 

class DeepseekAutomationView(QWidget):
    """Deepseek自动化POC编写主视图"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 创建主标签页
        tabs = QTabWidget()
        
        # CVE输入和数据采集页
        collection_tab = QWidget()
        collection_layout = QVBoxLayout(collection_tab)
        
        # CVE输入组件
        print("正在创建CVE输入组件...")
        self.cve_input_widget = CveInputWidget()
        collection_layout.addWidget(self.cve_input_widget)
        
        # 数据采集组件
        print("正在创建数据采集组件...")
        self.data_collection_widget = DataCollectionWidget()
        collection_layout.addWidget(self.data_collection_widget)
        
        tabs.addTab(collection_tab, "数据采集")
        
        # POC生成页
        generation_tab = QWidget()
        generation_layout = QVBoxLayout(generation_tab)
        
        # POC生成组件
        print("正在创建POC生成组件...")
        self.poc_generation_widget = PocGenerationWidget()
        generation_layout.addWidget(self.poc_generation_widget)
        
        tabs.addTab(generation_tab, "POC生成")
        
        layout.addWidget(tabs)
        
        # 连接信号
        print("正在连接组件信号...")
        self.cve_input_widget.cve_submitted.connect(self.data_collection_widget.collect_data)
        self.data_collection_widget.collection_completed.connect(self.poc_generation_widget.set_collected_data)
        self.poc_generation_widget.generation_completed.connect(self._on_generation_completed)
        
        # 标签页切换
        self.tabs = tabs
        
        # 输出调试信息
        print("Deepseek自动化界面初始化完成")
        print(f"- CVE输入组件: {'已连接' if hasattr(self, 'cve_input_widget') else '未连接'}")
        print(f"- 数据采集组件: {'已连接' if hasattr(self, 'data_collection_widget') else '未连接'}")
        print(f"- POC生成组件: {'已连接' if hasattr(self, 'poc_generation_widget') else '未连接'}")
    
    def _on_generation_completed(self, file_path):
        """POC生成完成处理"""
        # 可以在这里添加额外处理，如自动切换到管理界面等 