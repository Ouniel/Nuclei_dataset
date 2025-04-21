"""
POC生成器模块
负责将Deepseek生成的JSON数据与nuclei模板合并，生成最终的POC文件
"""
import os
import json
import re
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal, QSettings

# nuclei HTTP POC模板
NUCLEI_HTTP_TEMPLATE = '''id: {id}
info:
  name: {name}
  author: nuclei-poc-generator
  severity: {severity}
  description: |
    {description}
  reference:
    {references}
  tags: {tags}
  metadata:
    generated-by: nuclei-poc-generator
    created-at: {created_at}

{requests}
'''

# HTTP请求模板
HTTP_REQUEST_TEMPLATE = '''requests:
  - method: {method}
    path:
      - "{{BaseURL}}{path}"
    matchers:
      - type: word
        part: body
        words:
          {keywords}
        condition: or
      - type: status
        status:
          - {status_code}
'''

# 正则表达式匹配器模板
REGEX_MATCHER_TEMPLATE = '''      - type: regex
        part: body
        regex:
          {regex}
        condition: or
'''

# FOFA查询模板
FOFA_QUERY_TEMPLATE = '''    fofa-query: '{fofa_query}'
'''

class PocGenerator(QObject):
    """POC生成器类，将JSON数据与nuclei模板合并"""
    
    generation_started = pyqtSignal()
    generation_finished = pyqtSignal(str)
    generation_error = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 加载配置
        self.settings = QSettings("NucleiPOCManager", "PocGenerator")
        self.poc_dir = self.settings.value("poc_dir", "pocs")
        
        # 确保POC目录存在
        if not os.path.exists(self.poc_dir):
            try:
                os.makedirs(self.poc_dir)
            except OSError as e:
                self.generation_error.emit(f"创建POC目录失败: {str(e)}")
    
    def set_poc_dir(self, directory):
        """
        设置POC保存目录
        
        Args:
            directory (str): POC保存目录
        """
        self.poc_dir = directory
        self.settings.setValue("poc_dir", directory)
        
        # 确保目录存在
        if not os.path.exists(self.poc_dir):
            try:
                os.makedirs(self.poc_dir)
            except OSError as e:
                self.generation_error.emit(f"创建POC目录失败: {str(e)}")
    
    def generate_poc(self, poc_data):
        """
        生成POC文件
        
        Args:
            poc_data (dict): POC数据（从Deepseek生成）
        
        Returns:
            str: 生成的POC文件路径
        """
        self.generation_started.emit()
        
        try:
            # 验证输入数据
            if not isinstance(poc_data, dict):
                raise ValueError("POC数据必须是字典类型")
            
            # 必要字段检查
            required_fields = ["id", "name", "paths", "matchers"]
            missing_fields = [field for field in required_fields if field not in poc_data]
            if missing_fields:
                raise ValueError(f"POC数据缺少必要字段: {', '.join(missing_fields)}")
            
            # 提取并处理数据
            poc_id = poc_data.get("id", "").strip()
            if not poc_id:
                poc_id = f"generic-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            poc_name = poc_data.get("name", "").strip()
            if not poc_name:
                poc_name = f"未命名POC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 处理描述信息
            description = poc_data.get("description", "").strip()
            description = self._format_multiline(description)
            
            # 处理参考链接
            references = poc_data.get("references", [])
            if isinstance(references, str):
                references = [ref.strip() for ref in references.split(",")]
            formatted_references = self._format_references(references)
            
            # 处理标签
            tags = poc_data.get("tags", [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(",")]
            formatted_tags = self._format_tags(tags)
            
            # 处理严重程度
            severity = poc_data.get("severity", "medium").strip().lower()
            if severity not in ["critical", "high", "medium", "low", "info"]:
                severity = "medium"
            
            # 处理HTTP请求部分
            method = poc_data.get("method", "GET").strip().upper()
            
            paths = poc_data.get("paths", [])
            if isinstance(paths, str):
                paths = [paths]
            
            if not paths:
                paths = ["/"]
            
            path = paths[0]  # 取第一个路径
            
            # 处理匹配器
            matchers = poc_data.get("matchers", {})
            status_code = matchers.get("status", 200)
            
            keywords = matchers.get("keywords", [])
            if isinstance(keywords, str):
                keywords = [keywords]
            formatted_keywords = self._format_list_items(keywords)
            
            # 构建HTTP请求部分
            http_request = HTTP_REQUEST_TEMPLATE.format(
                method=method,
                path=path,
                keywords=formatted_keywords,
                status_code=status_code
            )
            
            # 添加正则表达式匹配器
            regex_patterns = matchers.get("regex", [])
            if regex_patterns:
                if isinstance(regex_patterns, str):
                    regex_patterns = [regex_patterns]
                formatted_regex = self._format_list_items(regex_patterns)
                regex_matcher = REGEX_MATCHER_TEMPLATE.format(regex=formatted_regex)
                http_request += regex_matcher
            
            # 添加FOFA查询
            fofa_query = poc_data.get("fofa_query", "")
            if fofa_query:
                fofa_part = FOFA_QUERY_TEMPLATE.format(fofa_query=fofa_query)
                # 在requests前插入fofa-query
                parts = http_request.split("requests:", 1)
                http_request = parts[0] + fofa_part + "requests:" + parts[1]
            
            # 生成完整POC
            created_at = datetime.now().strftime("%Y-%m-%d")
            poc_content = NUCLEI_HTTP_TEMPLATE.format(
                id=poc_id,
                name=poc_name,
                severity=severity,
                description=description,
                references=formatted_references,
                tags=formatted_tags,
                requests=http_request,
                created_at=created_at
            )
            
            # 保存POC文件
            file_name = f"{poc_id}.yaml"
            file_path = os.path.join(self.poc_dir, file_name)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(poc_content)
            
            self.generation_finished.emit(file_path)
            return file_path
            
        except Exception as e:
            error_msg = f"生成POC文件失败: {str(e)}"
            self.generation_error.emit(error_msg)
            return None
    
    def _format_multiline(self, text):
        """
        格式化多行文本，确保YAML格式正确
        
        Args:
            text (str): 原始文本
        
        Returns:
            str: 格式化后的文本
        """
        if not text:
            return "无描述"
        
        # 替换换行符为YAML兼容格式
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        
        # 添加缩进
        lines = text.split("\n")
        formatted_lines = ["    " + line for line in lines]
        
        return "\n".join(formatted_lines)
    
    def _format_references(self, references):
        """
        格式化参考链接列表
        
        Args:
            references (list): 参考链接列表
        
        Returns:
            str: 格式化后的参考链接
        """
        if not references:
            return "- https://github.com/nuclei-poc-generator"
        
        formatted = []
        for ref in references:
            ref = ref.strip()
            if ref:
                formatted.append(f"- {ref}")
        
        if not formatted:
            return "- https://github.com/nuclei-poc-generator"
        
        return "\n    ".join(formatted)
    
    def _format_tags(self, tags):
        """
        格式化标签列表
        
        Args:
            tags (list): 标签列表
        
        Returns:
            str: 格式化后的标签
        """
        if not tags:
            return "[nuclei-poc-generator]"
        
        # 清理标签
        cleaned_tags = []
        for tag in tags:
            tag = tag.strip()
            # 去除特殊字符
            tag = re.sub(r'[^\w-]', '', tag)
            if tag:
                cleaned_tags.append(tag)
        
        if not cleaned_tags:
            return "[nuclei-poc-generator]"
        
        return "[" + ", ".join(cleaned_tags) + "]"
    
    def _format_list_items(self, items):
        """
        格式化列表项为YAML格式
        
        Args:
            items (list): 列表项
        
        Returns:
            str: 格式化后的列表项
        """
        if not items:
            return '- "example"'
        
        formatted = []
        for item in items:
            item = str(item).strip()
            if item:
                # 转义引号
                item = item.replace('"', '\\"')
                formatted.append(f'- "{item}"')
        
        if not formatted:
            return '- "example"'
        
        return "\n          ".join(formatted) 