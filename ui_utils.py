"""
通用UI工具模块，包含常用的UI助手函数
"""
import os
from PyQt5.QtWidgets import QMessageBox, QFileDialog


def show_error(parent, title, message):
    """
    显示错误对话框
    
    Args:
        parent (QWidget): 父窗口
        title (str): 标题
        message (str): 错误消息
    """
    QMessageBox.critical(parent, title, message)


def show_info(parent, title, message):
    """
    显示信息对话框
    
    Args:
        parent (QWidget): 父窗口
        title (str): 标题
        message (str): 信息消息
    """
    QMessageBox.information(parent, title, message)


def show_warning(parent, title, message):
    """
    显示警告对话框
    
    Args:
        parent (QWidget): 父窗口
        title (str): 标题
        message (str): 警告消息
    """
    QMessageBox.warning(parent, title, message)


def confirm(parent, title, message):
    """
    显示确认对话框
    
    Args:
        parent (QWidget): 父窗口
        title (str): 标题
        message (str): 确认消息
    
    Returns:
        bool: 用户是否确认
    """
    reply = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )
    return reply == QMessageBox.Yes


def select_file(parent, title, filter="All Files (*.*)", directory=""):
    """
    选择文件对话框
    
    Args:
        parent (QWidget): 父窗口
        title (str): 对话框标题
        filter (str): 文件过滤器
        directory (str): 初始目录
    
    Returns:
        str: 选中的文件路径，如果未选择则为空字符串
    """
    file_path, _ = QFileDialog.getOpenFileName(
        parent,
        title,
        directory,
        filter
    )
    return file_path


def select_directory(parent, title, directory=""):
    """
    选择目录对话框
    
    Args:
        parent (QWidget): 父窗口
        title (str): 对话框标题
        directory (str): 初始目录
    
    Returns:
        str: 选中的目录路径，如果未选择则为空字符串
    """
    dir_path = QFileDialog.getExistingDirectory(
        parent,
        title,
        directory,
        QFileDialog.ShowDirsOnly
    )
    return dir_path


def save_file(parent, title, filter="All Files (*.*)", directory=""):
    """
    保存文件对话框
    
    Args:
        parent (QWidget): 父窗口
        title (str): 对话框标题
        filter (str): 文件过滤器
        directory (str): 初始目录
    
    Returns:
        str: 选中的文件路径，如果未选择则为空字符串
    """
    file_path, _ = QFileDialog.getSaveFileName(
        parent,
        title,
        directory,
        filter
    )
    return file_path


def set_material_style(widget):
    """
    为小部件设置Material Design风格
    
    Args:
        widget (QWidget): 目标小部件
    """
    widget.setStyleSheet("""
        QWidget {
            font-family: "Microsoft YaHei", "Segoe UI", Arial;
            font-size: 10pt;
        }
        
        QDialog, QMainWindow, QWidget {
            background-color: #ffffff;
        }
        
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
        
        QLineEdit, QTextEdit, QComboBox {
            border-radius: 8px;
            padding: 8px;
            background-color: #f5f5f7;
            border: 1px solid #d1d1d6;
        }
        
        QLineEdit:focus, QTextEdit:focus {
            border: 1px solid #007aff;
        }
        
        QLabel {
            color: #000000;
        }
        
        QTabWidget::pane {
            border: 1px solid #d1d1d6;
            border-radius: 8px;
            padding: 5px;
            background-color: #ffffff;
        }
        
        QTabBar::tab {
            background-color: #f5f5f7;
            border: 1px solid #d1d1d6;
            border-bottom: none;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            padding: 8px 15px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: #ffffff;
            border-bottom: 2px solid #007aff;
        }
        
        QTabBar::tab:hover {
            background-color: #e5e5ea;
        }
        
        QTableView, QTreeView, QListView {
            border: 1px solid #d1d1d6;
            border-radius: 8px;
            background-color: #ffffff;
        }
        
        QHeaderView::section {
            background-color: #f5f5f7;
            padding: 5px;
            border: 1px solid #d1d1d6;
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
        }
        
        QScrollBar:vertical {
            border: none;
            background: #f5f5f7;
            width: 10px;
            border-radius: 5px;
        }
        
        QScrollBar::handle:vertical {
            background: #c7c7cc;
            border-radius: 5px;
        }
        
        QScrollBar:horizontal {
            border: none;
            background: #f5f5f7;
            height: 10px;
            border-radius: 5px;
        }
        
        QScrollBar::handle:horizontal {
            background: #c7c7cc;
            border-radius: 5px;
        }
        
        QMenuBar {
            background-color: #f5f5f7;
            border-bottom: 1px solid #d1d1d6;
        }
        
        QMenuBar::item {
            spacing: 5px;
            padding: 5px 10px;
            background: transparent;
        }
        
        QMenuBar::item:selected {
            background-color: #007aff;
            color: white;
        }
        
        QMenu {
            background-color: #ffffff;
            border: 1px solid #d1d1d6;
            border-radius: 8px;
        }
        
        QMenu::item {
            padding: 5px 25px 5px 30px;
        }
        
        QMenu::item:selected {
            background-color: #007aff;
            color: white;
        }
    """) 