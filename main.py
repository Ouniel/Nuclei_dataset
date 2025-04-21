#!/usr/bin/env python3
"""
Nuclei POC管理系统
主应用程序入口
"""
import sys
import os
import traceback
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, 
                             QVBoxLayout, QWidget, QMessageBox, QSplashScreen,
                             QMenuBar, QMenu, QAction, QStatusBar)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap

# 导入模块
from poc_management.views import PocManagementView
from deepseek_automation.views import DeepseekAutomationView
import ui_utils

# 全局变量，用于保存主窗口引用，防止被垃圾回收
_main_window = None

class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        
        try:
            print("开始初始化主窗口...")
            # 设置窗口标题和大小
            self.setWindowTitle("Nuclei POC管理系统")
            self.setMinimumSize(1200, 800)
            
            # 直接使用代码构建UI
            print("使用代码构建UI...")
            self._init_ui_manually()
            
            # 设置事件处理
            print("连接信号和槽...")
            self._connect_signals()
            print("主窗口初始化完成!")
        except Exception as e:
            print(f"主窗口初始化错误: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.critical(None, "初始化错误", f"主窗口初始化时发生错误: {str(e)}")
    
    def _init_ui_manually(self):
        """手动初始化UI"""
        try:
            # 创建中心部件
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # 主布局
            layout = QVBoxLayout(central_widget)
            layout.setContentsMargins(10, 10, 10, 10)
            
            # 创建菜单栏
            self._create_menu_bar()
            
            # 创建标签页
            self.tabWidget = QTabWidget()
            
            # POC管理标签页
            self.pocManagementTab = QWidget()
            self.tabWidget.addTab(self.pocManagementTab, "POC管理")
            
            # 自动化POC编写标签页
            self.automationTab = QWidget()
            self.tabWidget.addTab(self.automationTab, "自动化POC编写")
            
            layout.addWidget(self.tabWidget)
            
            # 创建状态栏
            self.statusBar = QStatusBar()
            self.setStatusBar(self.statusBar)
            self.statusBar.showMessage("准备就绪")
            
            # 设置样式
            ui_utils.set_material_style(self)
            
            # 初始化标签页内容
            self._init_tab_content()
        except Exception as e:
            print(f"手动初始化UI错误: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def _create_menu_bar(self):
        """创建菜单栏"""
        try:
            # 创建菜单栏
            menubar = self.menuBar()
            
            # 文件菜单
            fileMenu = menubar.addMenu("文件")
            
            # 导入POC
            self.actionImport = QAction("导入POC", self)
            self.actionImport.setShortcut("Ctrl+I")
            fileMenu.addAction(self.actionImport)
            
            # 导出POC
            self.actionExport = QAction("导出POC", self)
            self.actionExport.setShortcut("Ctrl+E")
            fileMenu.addAction(self.actionExport)
            
            fileMenu.addSeparator()
            
            # 退出
            self.actionExit = QAction("退出", self)
            self.actionExit.setShortcut("Ctrl+Q")
            fileMenu.addAction(self.actionExit)
            
            # 设置菜单
            settingsMenu = menubar.addMenu("设置")
            
            # API设置
            self.actionAPISettings = QAction("API设置", self)
            settingsMenu.addAction(self.actionAPISettings)
            
            # 帮助菜单
            helpMenu = menubar.addMenu("帮助")
            
            # 关于
            self.actionAbout = QAction("关于", self)
            helpMenu.addAction(self.actionAbout)
        except Exception as e:
            print(f"创建菜单栏错误: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def _init_tab_content(self):
        """初始化标签页内容"""
        try:
            # 为POC管理标签页创建布局（如果不存在）
            if not self.pocManagementTab.layout():
                poc_layout = QVBoxLayout(self.pocManagementTab)
                poc_layout.setContentsMargins(5, 5, 5, 5)
            
            # 为自动化POC编写标签页创建布局（如果不存在）
            if not self.automationTab.layout():
                automation_layout = QVBoxLayout(self.automationTab)
                automation_layout.setContentsMargins(5, 5, 5, 5)
            
            # POC管理标签页
            print("创建POC管理视图...")
            self.poc_management_view = PocManagementView()
            self.pocManagementTab.layout().addWidget(self.poc_management_view)
            
            # Deepseek自动化标签页
            print("创建Deepseek自动化视图...")
            self.deepseek_automation_view = DeepseekAutomationView()
            self.automationTab.layout().addWidget(self.deepseek_automation_view)
            print("标签页内容初始化完成!")
        except Exception as e:
            print(f"初始化标签页内容错误: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def _connect_signals(self):
        """连接信号和槽"""
        try:
            # 连接菜单操作信号
            self.actionExit.triggered.connect(self.close)
            self.actionImport.triggered.connect(self._on_import)
            self.actionExport.triggered.connect(self._on_export)
            self.actionAPISettings.triggered.connect(self._on_api_settings)
            self.actionAbout.triggered.connect(self._on_about)
        except Exception as e:
            print(f"连接信号和槽错误: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def _on_import(self):
        """导入POC菜单动作处理函数"""
        try:
            # 委托给POC管理视图
            if hasattr(self, 'poc_management_view'):
                # 调用POC管理视图的导入方法
                # 假设POC管理视图有一个_on_import方法
                if hasattr(self.poc_management_view, '_on_import'):
                    self.poc_management_view._on_import()
        except Exception as e:
            print(f"导入POC错误: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.critical(self, "导入错误", f"导入POC时发生错误: {str(e)}")
    
    def _on_export(self):
        """导出POC菜单动作处理函数"""
        try:
            # 委托给POC管理视图
            if hasattr(self, 'poc_management_view'):
                # 调用POC管理视图的导出方法
                # 假设POC管理视图有一个_on_export方法
                if hasattr(self.poc_management_view, '_on_export'):
                    self.poc_management_view._on_export()
        except Exception as e:
            print(f"导出POC错误: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.critical(self, "导出错误", f"导出POC时发生错误: {str(e)}")
    
    def _on_api_settings(self):
        """API设置菜单动作处理函数"""
        try:
            # 委托给Deepseek自动化视图
            if hasattr(self, 'deepseek_automation_view'):
                # 调用Deepseek自动化视图的API设置方法
                # 假设DeepseekAutomationView的poc_generation_widget有一个_show_api_settings方法
                if hasattr(self.deepseek_automation_view, 'poc_generation_widget') and \
                hasattr(self.deepseek_automation_view.poc_generation_widget, '_show_api_settings'):
                    self.deepseek_automation_view.poc_generation_widget._show_api_settings()
        except Exception as e:
            print(f"API设置错误: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.critical(self, "API设置错误", f"打开API设置时发生错误: {str(e)}")
    
    def _on_about(self):
        """关于菜单动作处理函数"""
        try:
            about_text = """
            <h2>Nuclei POC管理系统</h2>
            <p>版本: 1.0.0</p>
            <p>一个用于管理Nuclei POC的工具，支持自动化生成POC。</p>
            <p>基于PyQt5构建。</p>
            """
            QMessageBox.about(self, "关于", about_text)
        except Exception as e:
            print(f"关于对话框错误: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.critical(self, "错误", f"显示关于对话框时发生错误: {str(e)}")


def main():
    """程序入口函数"""
    try:
        # 创建应用
        app = QApplication(sys.argv)
        app.setStyle("Fusion")  # 使用Fusion风格
        
        # 创建启动画面
        splash_pixmap = QPixmap(400, 300)
        splash_pixmap.fill(Qt.white)
        splash = QSplashScreen(splash_pixmap)
        splash.show()
        
        # 启动消息
        splash.showMessage("正在初始化应用...", 
                        Qt.AlignCenter | Qt.AlignBottom, 
                        Qt.black)
        
        # 确保目录存在
        os.makedirs("pocs", exist_ok=True)
        
        # 延迟启动
        QTimer.singleShot(1000, lambda: _show_main_window(app, splash))
        
        # 运行应用
        print("开始应用程序事件循环...")
        return app.exec_()
    except Exception as e:
        print(f"主程序错误: {str(e)}")
        print(traceback.format_exc())
        QMessageBox.critical(None, "程序错误", f"程序执行过程中发生错误: {str(e)}")
        return 1


def _show_main_window(app, splash):
    """显示主窗口"""
    try:
        print("正在创建主窗口...")
        # 创建并显示主窗口
        main_window = MainWindow()
        # 保存主窗口引用到全局变量，防止被垃圾回收
        global _main_window
        _main_window = main_window
        
        print("显示主窗口...")
        main_window.show()
        
        # 关闭启动画面
        splash.finish(main_window)
        print("主窗口显示完成，启动画面已关闭")
        
    except Exception as e:
        print(f"显示主窗口错误: {str(e)}")
        print(traceback.format_exc())
        QMessageBox.critical(None, "启动错误", f"启动应用程序时发生错误: {str(e)}")
        app.quit()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"程序退出错误: {str(e)}")
        print(traceback.format_exc()) 