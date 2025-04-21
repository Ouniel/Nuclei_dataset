"""
UI加载器模块，用于加载UI文件并处理公共UI操作
"""
import os
from PyQt5 import uic
from PyQt5.QtWidgets import QMessageBox


def get_ui_path(filename):
    """
    获取UI文件的绝对路径
    
    Args:
        filename (str): UI文件名
    
    Returns:
        str: UI文件的绝对路径
    """
    # 获取当前文件的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 获取工作目录
    base_dir = os.path.normpath(os.path.join(current_dir, '..', '..'))
    
    # UI文件目录
    ui_dir = os.path.join(base_dir, 'ui')
    
    # 处理文件名
    if 'dialogs' in filename.lower():
        # 对话框UI文件
        file_path = os.path.join(ui_dir, filename)
    elif 'main' in filename.lower():
        # 主窗口UI文件
        file_path = os.path.join(ui_dir, filename)
    else:
        # 假设是对话框UI
        file_path = os.path.join(ui_dir, 'dialogs', filename)
    
    return file_path


def load_ui(ui_file, widget):
    """
    加载UI文件到小部件
    
    Args:
        ui_file (str): UI文件名
        widget (QWidget): 目标小部件
    
    Returns:
        bool: 是否成功加载
    """
    try:
        ui_path = get_ui_path(ui_file)
        uic.loadUi(ui_path, widget)
        return True
    except Exception as e:
        QMessageBox.critical(
            None, 
            "UI加载错误", 
            f"无法加载UI文件 {ui_file}: {str(e)}"
        )
        return False


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
    """) 