"""
Deepseek API接口模块
负责与Deepseek API交互，发送请求和处理响应
"""
import json
import requests
from PyQt5.QtCore import QObject, pyqtSignal, QSettings
import re

class DeepseekAPI(QObject):
    """Deepseek API接口类"""
    
    # 状态信号
    request_started = pyqtSignal()
    request_finished = pyqtSignal()
    request_error = pyqtSignal(str)
    response_received = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("NucleiPOCManager", "ApiSettings")
        self.api_key = self.settings.value("deepseek_api_key", "")
        # 最新的DeepSeek API URL
        self.api_url = "https://api.deepseek.cn/v1/chat/completions"
    
    def set_api_key(self, api_key):
        """设置API密钥"""
        self.api_key = api_key
        self.settings.setValue("deepseek_api_key", api_key)
    
    def get_api_key(self):
        """获取API密钥"""
        return self.api_key
    
    def generate_poc(self, prompt, content):
        """
        根据提示和内容生成POC
        
        Args:
            prompt (str): 提示内容
            content (str): 漏洞相关内容
        """
        if not self.api_key:
            self.request_error.emit("未设置API密钥")
            return
        
        self.request_started.emit()
        
        # 构造请求数据
        full_prompt = f"{prompt}\n\n{content}"
        
        # 按照最新的DeepSeek API格式构造请求
        data = {
            "model": "Pro/deepseek-ai/DeepSeek-V3",  # 使用DeepSeek-V3模型
            "messages": [
                {"role": "system", "content": "你是一个安全专家，擅长编写Nuclei漏洞验证POC。请根据提供的信息生成有效的Nuclei POC，并严格按照YAML格式模板输出，注意缩进和语法，确保生成的POC可以被Nuclei直接加载并执行。"},
                {"role": "user", "content": full_prompt}
            ],
            "temperature": 0.3,  # 较低的温度，使输出更确定性
            "max_tokens": 4000
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            # 发送请求
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=120  # 设置120秒超时，因为生成POC可能需要更长时间
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应数据
            result = response.json()
            
            # 从响应中提取生成的内容
            generated_content = self._extract_content(result)
            
            # 尝试提取YAML内容
            try:
                poc_yaml = self._extract_yaml(generated_content)
                self.response_received.emit({"yaml_content": poc_yaml})
            except Exception as e:
                self.request_error.emit(f"无法提取Nuclei POC YAML内容: {str(e)}\n原始响应:\n{generated_content}")
            
        except requests.RequestException as e:
            self.request_error.emit(f"API请求错误: {str(e)}")
        except Exception as e:
            self.request_error.emit(f"发生未知错误: {str(e)}")
        finally:
            self.request_finished.emit()
    
    def _extract_content(self, response_data):
        """
        从API响应中提取生成的内容
        
        Args:
            response_data (dict): API响应数据
        
        Returns:
            str: 提取出的内容
        """
        # 按照最新的DeepSeek API响应格式提取内容
        try:
            # 获取助手消息的内容
            if "choices" in response_data and len(response_data["choices"]) > 0:
                if "message" in response_data["choices"][0]:
                    return response_data["choices"][0]["message"].get("content", "")
            raise Exception("响应格式不符合预期，无法提取内容")
        except (IndexError, KeyError, AttributeError) as e:
            raise Exception(f"无法从API响应中提取内容: {str(e)}")
    
    def _extract_yaml(self, content):
        """
        从文本内容中提取YAML部分
        
        Args:
            content (str): 包含YAML的文本内容
        
        Returns:
            str: 提取出的YAML内容
        """
        # 尝试查找YAML内容（通常在```yaml和```之间）
        yaml_pattern = r"```yaml\s*([\s\S]*?)\s*```"
        yaml_match = re.search(yaml_pattern, content)
        
        if yaml_match:
            return yaml_match.group(1).strip()
        
        # 如果找不到明确的YAML标记，尝试提取可能的YAML内容
        # 寻找以"id:"开头的行，这通常是Nuclei POC的起始
        lines = content.split('\n')
        start_index = -1
        
        for i, line in enumerate(lines):
            if line.strip().startswith("id:"):
                start_index = i
                break
        
        if start_index >= 0:
            # 提取从"id:"开始的所有内容
            return '\n'.join(lines[start_index:])
        
        # 如果上述方法都失败，返回原始内容
        return content 