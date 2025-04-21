"""
Nuclei POC 数据库管理模块
使用JSON文件存储和管理POC元数据
"""
import json
import os
import uuid
from datetime import datetime
import jsonschema
from PyQt5.QtWidgets import QMessageBox

# POC元数据的JSON Schema定义
POC_DATABASE_SCHEMA = {
    "type": "object",
    "properties": {
        "pocs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "POC唯一标识符（如CVE编号或自动生成的UUID）"},
                    "name": {"type": "string", "description": "POC名称（如漏洞名称）"},
                    "path": {"type": "string", "description": "POC文件在本地的路径（相对路径或绝对路径）"},
                    "description": {"type": "string", "description": "漏洞描述"},
                    "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "漏洞类型标签"},
                    "references": {"type": "array", "items": {"type": "string"}, "description": "参考链接列表"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"}
                },
                "required": ["id", "name", "path", "severity"]
            }
        }
    }
}


class PocDatabase:
    """POC数据库管理类，处理JSON文件的读写操作和元数据验证"""
    
    def __init__(self, db_path="poc_database.json"):
        """
        初始化POC数据库
        
        Args:
            db_path (str): JSON数据库文件路径
        """
        self.db_path = db_path
        self._ensure_database_exists()
        
    def _ensure_database_exists(self):
        """确保数据库文件存在，如果不存在则创建一个空的数据库"""
        if not os.path.exists(self.db_path):
            self._create_empty_database()
    
    def _create_empty_database(self):
        """创建一个空的数据库文件"""
        empty_db = {"pocs": []}
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(empty_db, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise Exception(f"创建数据库文件失败: {str(e)}")
    
    def load_database(self):
        """
        加载数据库内容
        
        Returns:
            dict: 数据库内容
        """
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            self._create_empty_database()
            return {"pocs": []}
        except json.JSONDecodeError:
            raise Exception("数据库文件格式错误，无法解析JSON")
        except Exception as e:
            raise Exception(f"加载数据库失败: {str(e)}")
    
    def save_database(self, data):
        """
        保存数据库内容
        
        Args:
            data (dict): 要保存的数据库内容
        """
        try:
            # 验证数据格式是否符合Schema
            jsonschema.validate(data, POC_DATABASE_SCHEMA)
            
            # 保存数据到文件
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except jsonschema.exceptions.ValidationError as e:
            raise Exception(f"数据验证失败: {str(e)}")
        except Exception as e:
            raise Exception(f"保存数据库失败: {str(e)}")
    
    def get_all_pocs(self):
        """
        获取所有POC记录
        
        Returns:
            list: POC记录列表
        """
        data = self.load_database()
        return data.get("pocs", [])
    
    def add_poc(self, poc_data):
        """
        添加一个POC记录
        
        Args:
            poc_data (dict): POC元数据
        
        Returns:
            str: 新添加的POC的ID
        """
        # 加载当前数据库
        data = self.load_database()
        
        # 确保有必要的字段
        if "id" not in poc_data:
            poc_data["id"] = str(uuid.uuid4())
        
        current_time = datetime.now().isoformat()
        if "created_at" not in poc_data:
            poc_data["created_at"] = current_time
        
        poc_data["updated_at"] = current_time
        
        # 添加新POC记录
        data["pocs"].append(poc_data)
        
        # 保存数据库
        self.save_database(data)
        return poc_data["id"]
    
    def update_poc(self, poc_id, updated_data):
        """
        更新POC记录
        
        Args:
            poc_id (str): 要更新的POC的ID
            updated_data (dict): 更新的数据
        
        Returns:
            bool: 更新是否成功
        """
        data = self.load_database()
        for i, poc in enumerate(data["pocs"]):
            if poc["id"] == poc_id:
                # 更新数据
                updated_data["updated_at"] = datetime.now().isoformat()
                data["pocs"][i].update(updated_data)
                self.save_database(data)
                return True
        return False
    
    def delete_poc(self, poc_id):
        """
        删除POC记录
        
        Args:
            poc_id (str): 要删除的POC的ID
        
        Returns:
            bool: 删除是否成功
        """
        data = self.load_database()
        for i, poc in enumerate(data["pocs"]):
            if poc["id"] == poc_id:
                del data["pocs"][i]
                self.save_database(data)
                return True
        return False
    
    def search_pocs(self, keyword=None, tags=None, severity=None):
        """
        搜索POC记录
        
        Args:
            keyword (str, optional): 关键词
            tags (list, optional): 标签列表
            severity (str, optional): 严重程度
        
        Returns:
            list: 匹配的POC记录列表
        """
        pocs = self.get_all_pocs()
        results = []
        
        for poc in pocs:
            # 关键词搜索
            if keyword and not (
                keyword.lower() in poc.get("name", "").lower() or
                keyword.lower() in poc.get("description", "").lower() or
                keyword.lower() in poc.get("id", "").lower()
            ):
                continue
            
            # 标签筛选
            if tags and not any(tag in poc.get("tags", []) for tag in tags):
                continue
            
            # 严重程度筛选
            if severity and poc.get("severity") != severity:
                continue
            
            results.append(poc)
        
        return results 