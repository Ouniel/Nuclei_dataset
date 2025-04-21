"""
使用DrissionPage进行网页爬取的模块
负责从阿里云漏洞库和Bing搜索爬取CVE相关信息
"""
import re
import time
import logging
from urllib.parse import quote
from PyQt5.QtCore import QObject, pyqtSignal

# 导入DrissionPage的组件
try:
    from DrissionPage import ChromiumPage, ChromiumOptions
    from DrissionPage.errors import ElementNotFoundError
except ImportError:
    logging.error("未找到DrissionPage模块，请确保已安装：pip install DrissionPage>=4.0.0")
    raise


class CveCrawler(QObject):
    """使用DrissionPage爬取CVE相关信息的类"""
    
    # 定义信号
    crawling_started = pyqtSignal()
    crawling_progress = pyqtSignal(int, int)  # 当前进度，总进度
    url_collected = pyqtSignal(str, str)  # URL, 来源
    crawling_completed = pyqtSignal(str, list)  # 内容，URL列表
    crawling_error = pyqtSignal(str)  # 错误信息
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.browser = None
        self.collected_urls = []
        self.collected_content = ""
        self.logger = logging.getLogger(__name__)
        self._should_stop = False  # 用于控制爬取中断
        
    def initialize_browser(self):
        """初始化浏览器"""
        try:
            # 配置浏览器选项
            options = ChromiumOptions()
            # 使用无头模式参数，而不是set_headless方法
            options.headless = True  # 无头模式，不显示浏览器窗口
            options.set_argument("--disable-gpu")
            options.set_argument("--no-sandbox")
            options.set_argument("--disable-dev-shm-usage")
            options.set_argument("--disable-extensions")
            
            # 创建浏览器实例
            self.browser = ChromiumPage(options)
            return True
        except Exception as e:
            self.crawling_error.emit(f"初始化浏览器失败: {str(e)}")
            return False
            
    def close_browser(self):
        """安全关闭浏览器"""
        if self.browser:
            try:
                self.browser.quit()
                self.logger.info("浏览器已成功关闭")
            except Exception as e:
                self.logger.error(f"关闭浏览器时出错: {str(e)}")
            finally:
                self.browser = None
            
    def stop_crawling(self):
        """停止当前爬取过程"""
        self._should_stop = True
        self.logger.info("收到停止爬取的请求")
        # 关闭浏览器会导致当前操作中断
        self.close_browser()
        
    def crawl_cve_info(self, cve_id):
        """
        爬取与CVE相关的信息
        
        Args:
            cve_id (str): CVE编号
        """
        # 重置停止标志
        self._should_stop = False
        
        try:
            self.crawling_started.emit()
            self.collected_urls = []
            self.collected_content = ""
            
            # 初始化浏览器
            if not self.browser:
                if not self.initialize_browser():
                    return
                    
            # 要爬取的来源总数
            total_sources = 2  # 目前有阿里云和Bing两个来源
            current_progress = 0
            
            # 发送进度信号
            self.crawling_progress.emit(current_progress, total_sources)
            
            # 从阿里云爬取信息
            if self._should_stop:
                self.crawling_error.emit("爬取已被用户取消")
                return
                
            current_progress += 1
            self.crawling_progress.emit(current_progress, total_sources)
            aliyun_urls, aliyun_content = self.crawl_aliyun(cve_id)
            all_urls = aliyun_urls
            all_content = aliyun_content
            
            # 从Bing爬取信息
            if self._should_stop:
                self.crawling_error.emit("爬取已被用户取消")
                return
                
            current_progress += 1
            self.crawling_progress.emit(current_progress, total_sources)
            bing_urls, bing_content = self.crawl_bing(cve_id)
            all_urls.extend(bing_urls)
            all_content += "== Bing搜索结果 ==\n" + bing_content
            
            self.collected_urls = all_urls
            self.collected_content = all_content
            
            # 完成信号
            self.crawling_progress.emit(total_sources, total_sources)
            self.crawling_completed.emit(all_content, all_urls)
            
        except Exception as e:
            self.crawling_error.emit(f"爬取过程中发生错误: {str(e)}")
        finally:
            if not self._should_stop:  # 只有在不是用户主动停止的情况下才关闭浏览器
                self.close_browser()
            
    def crawl_aliyun(self, cve_id):
        """
        从阿里云漏洞库爬取CVE信息
        
        Args:
            cve_id (str): CVE编号
            
        Returns:
            tuple: (爬取到的URL列表, 爬取到的内容文本)
        """
        urls = []
        content = "== 阿里云漏洞库搜索结果 ==\n"
        
        try:
            # 检查是否应该停止
            if self._should_stop:
                return [], ""
                
            # 访问阿里云漏洞库，搜索CVE
            search_url = f"https://avd.aliyun.com/search?q={quote(cve_id)}"
            # 保存搜索URL
            urls.append(search_url)
            self.url_collected.emit(search_url, "阿里云漏洞库-搜索")
            
            # 访问搜索页面
            self.browser.get(search_url)
            time.sleep(3)  # 等待页面加载
            
            # 检查是否应该停止
            if self._should_stop:
                return urls, content
            
            # 记录原始搜索页面内容
            content += f"搜索URL: {search_url}\n\n"
            
            # 尝试多种可能的XPath选择器来查找结果
            result_found = False
            
            # 选择器列表，从最可能到最不可能
            selectors = [
                "xpath://div[contains(@class, 'vuln-list-item')]", 
                "xpath://div[contains(@class, 'table-responsive')]//tr",
                "xpath://table//tr[contains(., '" + cve_id + "')]",
                "xpath://a[contains(text(), '" + cve_id + "')]",
                "xpath://div[contains(text(), '" + cve_id + "')]"
            ]
            
            # 尝试不同的选择器
            for selector in selectors:
                try:
                    result_elements = self.browser.eles(selector, timeout=2)
                    if result_elements and len(result_elements) > 0:
                        content += f"找到 {len(result_elements)} 个匹配结果\n"
                        
                        # 对于每个找到的元素
                        for element in result_elements:
                            # 检查是否应该停止
                            if self._should_stop:
                                return urls, content
                                
                            element_text = element.text
                            content += f"搜索结果: {element_text}\n"
                            
                            # 尝试找到链接
                            try:
                                # 尝试在元素或其子元素中查找链接
                                link_eles = element.eles("tag:a", timeout=2)
                                
                                if link_eles:
                                    for link_ele in link_eles:
                                        vuln_url = link_ele.link
                                        if vuln_url and cve_id.lower() in link_ele.text.lower():
                                            full_url = f"https://avd.aliyun.com{vuln_url}" if vuln_url.startswith("/") else vuln_url
                                            if full_url not in urls:
                                                urls.append(full_url)
                                                self.url_collected.emit(full_url, "阿里云漏洞库")
                                                content += f"找到链接: {full_url}\n"
                                                
                                                # 访问详情页
                                                self.browser.get(full_url)
                                                time.sleep(3)  # 等待页面加载
                                                
                                                # 检查是否应该停止
                                                if self._should_stop:
                                                    return urls, content
                                                
                                                # 提取漏洞详情
                                                try:
                                                    # 获取标题
                                                    title_elem = self.browser.ele("xpath://h1", timeout=2)
                                                    if title_elem:
                                                        content += f"标题: {title_elem.text}\n\n"
                                                        
                                                    # 获取详情 - 尝试多种可能的选择器
                                                    detail_selectors = [
                                                        "xpath://div[contains(@class, 'content-item')]",
                                                        "xpath://div[contains(@class, 'detail-content')]",
                                                        "xpath://div[contains(@class, 'description')]"
                                                    ]
                                                    
                                                    for detail_selector in detail_selectors:
                                                        detail_elems = self.browser.eles(detail_selector, timeout=1)
                                                        if detail_elems:
                                                            for elem in detail_elems:
                                                                # 检查是否应该停止
                                                                if self._should_stop:
                                                                    return urls, content
                                                                content += f"{elem.text}\n\n"
                                                            break  # 如果找到了就不再尝试其他选择器
                                                        
                                                    # 获取参考链接
                                                    ref_selectors = [
                                                        "xpath://div[contains(@class, 'reference-list')]//a",
                                                        "xpath://div[contains(@class, 'references')]//a",
                                                        "xpath://a[contains(@href, 'http')]"
                                                    ]
                                                    
                                                    for ref_selector in ref_selectors:
                                                        ref_elems = self.browser.eles(ref_selector, timeout=1)
                                                        if ref_elems:
                                                            content += "参考链接:\n"
                                                            for ref in ref_elems:
                                                                # 检查是否应该停止
                                                                if self._should_stop:
                                                                    return urls, content
                                                                ref_url = ref.link
                                                                if ref_url:
                                                                    content += f"- {ref_url}\n"
                                                                    if ref_url not in urls:
                                                                        urls.append(ref_url)
                                                                        self.url_collected.emit(ref_url, "阿里云参考链接")
                                                            break  # 如果找到了就不再尝试其他选择器
                                                except Exception as e:
                                                    content += f"解析详情页时出错: {str(e)}\n"
                                                
                                                # 标记为已找到结果
                                                result_found = True
                                                break  # 找到一个就够了
                            except Exception as e:
                                content += f"尝试获取链接时出错: {str(e)}\n"
                        
                        if result_found:
                            break  # 如果已经找到结果，就不再尝试其他选择器
                except ElementNotFoundError:
                    continue
                except Exception as e:
                    content += f"使用选择器 {selector} 搜索时出错: {str(e)}\n"
            
            # 如果没有找到结果，记录这一情况
            if not result_found:
                content += f"在阿里云漏洞库中未找到关于 {cve_id} 的直接链接\n"
                # 保存页面源码以便调试
                page_source = self.browser.html
                content += f"页面源码长度: {len(page_source)} 字符\n"
                
        except Exception as e:
            content += f"爬取阿里云漏洞库时出错: {str(e)}\n"
            
        return urls, content
        
    def crawl_bing(self, cve_id):
        """
        从Bing搜索引擎爬取CVE信息
        
        Args:
            cve_id (str): CVE编号
            
        Returns:
            tuple: (爬取到的URL列表, 爬取到的内容文本)
        """
        urls = []
        content = ""
        
        try:
            # 检查是否应该停止
            if self._should_stop:
                return [], ""
                
            # 构造搜索关键词，加上POC和exploit关键词以获取更相关的结果
            search_query = f"{cve_id} POC exploit"
            search_url = f"https://www.bing.com/search?q={quote(search_query)}"
            
            self.browser.get(search_url)
            time.sleep(2)  # 等待页面加载
            
            # 检查是否应该停止
            if self._should_stop:
                return [], ""
            
            # 尝试提取搜索结果
            try:
                result_elements = self.browser.eles("xpath://li[@class='b_algo']")
                
                if not result_elements:
                    # 尝试另一种可能的选择器
                    result_elements = self.browser.eles("xpath://div[@class='b_title']")
                
                if result_elements:
                    content += f"找到 {len(result_elements)} 个搜索结果:\n\n"
                    
                    # 只取前5个结果
                    for i, element in enumerate(result_elements[:5]):
                        # 检查是否应该停止
                        if self._should_stop:
                            return urls, content
                            
                        try:
                            title_ele = element.ele("tag:h2", timeout=1)
                            if not title_ele:
                                title_ele = element.ele("tag:a", timeout=1)
                                
                            if title_ele:
                                title = title_ele.text
                                link = title_ele.ele("tag:a", timeout=1)
                                if link:
                                    url = link.link
                                    if url:
                                        # 优先收集GitHub相关的链接
                                        if "github.com" in url.lower():
                                            urls.insert(0, url)  # 放在列表前面
                                        else:
                                            urls.append(url)
                                        self.url_collected.emit(url, "Bing搜索")
                                        content += f"{i+1}. {title}\n   链接: {url}\n\n"
                        except Exception as e:
                            continue
                else:
                    content += "在Bing中未找到相关搜索结果\n"
            except ElementNotFoundError:
                content += "在Bing中未找到相关搜索结果\n"
                
        except Exception as e:
            content += f"爬取Bing搜索引擎时出错: {str(e)}\n"
            
        return urls, content

    def extract_poc_from_url(self, url):
        """
        尝试从URL页面提取POC相关内容
        
        Args:
            url (str): 要爬取的URL
            
        Returns:
            str: 提取的POC相关内容
        """
        poc_content = ""
        try:
            # 检查是否应该停止
            if self._should_stop:
                return ""
                
            if not self.browser:
                self.initialize_browser()
                
            self.browser.get(url)
            time.sleep(3)  # 等待页面加载
            
            # 检查是否应该停止
            if self._should_stop:
                return ""
            
            # 尝试找到页面中的代码块
            code_elements = self.browser.eles("xpath://pre") or self.browser.eles("xpath://code")
            
            if code_elements:
                for code_elem in code_elements:
                    # 检查是否应该停止
                    if self._should_stop:
                        return poc_content
                        
                    code_text = code_elem.text
                    
                    # 检查是否是POC或漏洞利用相关的代码
                    if (re.search(r'poc|exploit|vuln|payload|attack', code_text, re.I) or 
                        "http" in code_text.lower()):
                        poc_content += f"{code_text}\n\n"
            
            # 如果没有找到代码块，尝试获取页面文本
            if not poc_content and not self._should_stop:
                # 尝试获取页面主要内容
                main_content = self.browser.ele("xpath://main") or self.browser.ele("xpath://article") or self.browser.ele("xpath://body")
                
                if main_content:
                    text = main_content.text
                    
                    # 提取包含POC关键词附近的内容
                    poc_matches = re.finditer(r'(?i)(?:poc|exploit|payload|vulnerability|attack|漏洞利用|攻击向量).{0,100}', text)
                    for match in poc_matches:
                        # 检查是否应该停止
                        if self._should_stop:
                            return poc_content
                        poc_content += f"{match.group(0)}...\n\n"
        
        except Exception as e:
            poc_content += f"从URL提取POC内容时出错: {str(e)}\n"
            
        return poc_content 