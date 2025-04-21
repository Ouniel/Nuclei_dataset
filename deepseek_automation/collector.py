"""
数据采集模块
使用DrissionPage爬虫从阿里云漏洞库和Bing搜索获取CVE相关信息
"""
import re
import time
import json
import logging
import threading
from PyQt5.QtCore import QObject, pyqtSignal, QSettings

from .crawler import CveCrawler


class CveCollector(QObject):
    """CVE信息收集类"""
    
    # 定义信号
    collection_started = pyqtSignal()
    collection_progress = pyqtSignal(int, int)  # 当前进度, 总进度
    url_collected = pyqtSignal(str, str)  # URL, 来源
    collection_completed = pyqtSignal(str, list)  # 内容, URL列表
    collection_error = pyqtSignal(str)  # 错误信息
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.crawler = None
        self._collection_thread = None
        self._cancel_flag = False
        
    def collect(self, cve_id):
        """
        收集CVE相关的数据
        
        Args:
            cve_id (str): CVE编号，如CVE-2021-44228
            
        Returns:
            bool: 是否成功开始收集
        """
        # 验证CVE ID格式
        if not self._validate_cve_id(cve_id):
            self.collection_error.emit(f"无效的CVE ID格式: {cve_id}")
            return False
            
        # 重置取消标志
        self._cancel_flag = False
        
        # 创建线程进行数据收集
        self._collection_thread = threading.Thread(
            target=self._collect_data_thread,
            args=(cve_id,),
            daemon=True
        )
        self._collection_thread.start()
        return True
    
    def cancel_collection(self):
        """取消正在进行的数据收集"""
        self._cancel_flag = True
        if self.crawler:
            # 关闭浏览器
            try:
                self.crawler.close_browser()
            except Exception as e:
                self.logger.error(f"关闭浏览器时出错: {str(e)}")
        
    def _collect_data_thread(self, cve_id):
        """
        在线程中收集数据
        
        Args:
            cve_id (str): CVE编号
        """
        try:
            # 发出开始信号
            self.collection_started.emit()
            
            # 创建爬虫实例
            self.crawler = CveCrawler()
            
            # 连接信号
            self.crawler.crawling_started.connect(lambda: self.logger.info(f"开始为 {cve_id} 爬取数据"))
            self.crawler.crawling_progress.connect(self.collection_progress.emit)
            self.crawler.url_collected.connect(self.url_collected.emit)
            self.crawler.crawling_error.connect(self.collection_error.emit)
            
            # 收集结果
            collected_content = ""
            collected_urls = []
            
            def on_crawling_completed(content, urls):
                nonlocal collected_content, collected_urls
                collected_content = content
                collected_urls = urls
            
            # 连接完成信号到本地函数
            self.crawler.crawling_completed.connect(on_crawling_completed)
            
            # 开始爬取数据
            self.crawler.crawl_cve_info(cve_id)
            
            # 检查是否被取消
            if self._cancel_flag:
                return
                
            # 发出完成信号
            self.collection_completed.emit(collected_content, collected_urls)
            
        except Exception as e:
            if not self._cancel_flag:
                error_msg = f"数据收集过程中发生错误: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                self.collection_error.emit(error_msg)
        finally:
            # 确保关闭浏览器
            if self.crawler and not self._cancel_flag:
                try:
                    self.crawler.close_browser()
                except Exception as e:
                    self.logger.error(f"关闭浏览器时出错: {str(e)}")
    
    def _validate_cve_id(self, cve_id):
        """
        验证CVE ID格式
        
        Args:
            cve_id (str): CVE编号
            
        Returns:
            bool: 是否是有效的CVE ID
        """
        pattern = r"^CVE-\d{4}-\d{4,}$"
        return re.match(pattern, cve_id) is not None
    
    def _on_crawling_started(self):
        """爬虫开始信号处理"""
        self.collection_started.emit()
    
    def _on_crawling_progress(self, current, total):
        """爬虫进度信号处理"""
        self.collection_progress.emit(current, total)
    
    def _on_url_collected(self, url, source):
        """爬虫URL收集信号处理"""
        self.url_collected.emit(url, source)
    
    def _on_crawling_completed(self, content, urls):
        """爬虫完成信号处理"""
        # 增加处理，提取更多POC相关内容
        enhanced_content = content
        
        # 尝试从收集到的每个URL中提取POC内容
        if urls and len(urls) > 0:
            poc_contents = []
            enhanced_content += "\n\n== POC相关内容提取 ==\n"
            
            try:
                # 只处理前3个URL，避免处理时间过长
                for url in urls[:3]:
                    poc_text = self.crawler.extract_poc_from_url(url)
                    if poc_text and len(poc_text.strip()) > 0:
                        poc_contents.append(f"从 {url} 提取的POC内容:\n{poc_text}")
                
                if poc_contents:
                    enhanced_content += "\n\n".join(poc_contents)
                else:
                    enhanced_content += "未从收集的URL中提取到明确的POC内容"
            except Exception as e:
                enhanced_content += f"\n提取POC内容时出错: {str(e)}"
        
        self.collection_completed.emit(enhanced_content, urls)
    
    def _on_crawling_error(self, error_msg):
        """爬虫错误信号处理"""
        self.collection_error.emit(error_msg) 