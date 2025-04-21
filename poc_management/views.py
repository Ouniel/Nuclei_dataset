"""
Nuclei POC管理界面视图模块
包含POC列表、搜索和分类功能
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                           QListWidgetItem, QLineEdit, QPushButton, QComboBox,
                           QLabel, QMessageBox, QFileDialog, QMenu, QSplitter,
                           QTextEdit, QTreeWidget, QTreeWidgetItem, QCheckBox,
                           QGroupBox, QTabWidget, QStackedWidget, QFrame,
                           QStyledItemDelegate, QStyle, QDialog, QFormLayout,
                           QDialogButtonBox, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QRect, QRectF, QProcess
from PyQt5.QtGui import QIcon, QColor, QFont, QCursor, QPen, QPainter, QFontMetrics, QPainterPath

import os
import json
import re
import sys
import subprocess
from datetime import datetime

from .database import PocDatabase


class PocItemDelegate(QStyledItemDelegate):
    """POC列表项自定义代理，用于显示两行文本"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.margin = 8
    
    def sizeHint(self, option, index):
        """返回项目的建议大小"""
        # 获取默认大小
        size = super().sizeHint(option, index)
        # 调整高度以容纳两行文本和边距
        size.setHeight(60)
        return size
    
    def paint(self, painter, option, index):
        """绘制列表项"""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)  # 启用抗锯齿
        
        # 创建圆角矩形
        rect = option.rect
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 8, 8)  # 将QRect转换为QRectF
        
        # 绘制背景
        if option.state & QStyle.State_Selected:
            painter.fillPath(path, QColor("#007aff"))
        elif option.state & QStyle.State_MouseOver:
            painter.fillPath(path, QColor("#e0e0e2"))
        else:
            painter.fillPath(path, QColor("#f5f5f7"))
        
        # 获取数据
        poc_data = index.data(Qt.UserRole)
        if not poc_data:
            super().paint(painter, option, index)
            painter.restore()
            return
        
        # 获取POC信息
        poc_name = poc_data.get("name", "未命名")
        poc_id = poc_data.get("id", "无ID")
        poc_path = os.path.basename(poc_data.get("path", "无路径"))
        severity = poc_data.get("severity", "").lower()
        
        # 严重程度颜色
        severity_colors = {
            "critical": "#ff3b30",  # 红色
            "high": "#ff9500",      # 橙色
            "medium": "#ffcc00",    # 黄色
            "low": "#34c759"        # 绿色
        }
        severity_color = severity_colors.get(severity, "#8e8e93")
        
        # 设置内容绘制矩形
        content_rect = rect.adjusted(self.margin, self.margin, -self.margin, -self.margin)
        
        # 设置字体
        font = painter.font()
        title_font = QFont(font)
        title_font.setBold(True)
        title_font.setPointSize(11)
        
        detail_font = QFont(font)
        detail_font.setPointSize(9)
        
        # 绘制标题
        painter.setFont(title_font)
        if option.state & QStyle.State_Selected:
            painter.setPen(QPen(Qt.white))
        else:
            painter.setPen(QPen(Qt.black))
        
        title_rect = QRect(
            content_rect.left(), 
            content_rect.top(), 
            content_rect.width() - 100, 
            25
        )
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter, poc_name)
        
        # 绘制严重性
        if severity:
            severity_text = severity.upper()
            
            # 创建严重性背景
            severity_rect = QRect(
                content_rect.right() - 80, 
                content_rect.top(), 
                80, 
                20
            )
            
            # 绘制严重性圆角背景
            severity_path = QPainterPath()
            severity_path.addRoundedRect(QRectF(severity_rect), 4, 4)  # 将QRect转换为QRectF
            painter.fillPath(severity_path, QColor(severity_color))
            
            # 绘制严重性文本 (白色)
            painter.setPen(QPen(Qt.white))
            painter.drawText(severity_rect, Qt.AlignCenter, severity_text)
        
        # 绘制ID和路径
        painter.setFont(detail_font)
        if option.state & QStyle.State_Selected:
            painter.setPen(QPen(Qt.white))
        else:
            painter.setPen(QPen(QColor("#8e8e93")))
            
        details_text = f"ID: {poc_id} | 路径: {poc_path}"
        details_rect = QRect(
            content_rect.left(), 
            content_rect.top() + 30, 
            content_rect.width(), 
            20
        )
        painter.drawText(details_rect, Qt.AlignLeft | Qt.AlignVCenter, details_text)
        
        painter.restore()


class PocListView(QWidget):
    """POC列表视图组件"""
    poc_selected = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = PocDatabase()
        self._init_ui()
        self._populate_list()
        
    def _init_ui(self):
        """初始化UI"""
        # 主布局
        layout = QVBoxLayout(self)
        
        # 搜索框
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索POC...")
        self.search_input.textChanged.connect(self._on_search)
        self.search_button = QPushButton("搜索")
        self.search_button.clicked.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)
        
        # 筛选条件
        filter_layout = QHBoxLayout()
        
        # 严重性筛选
        self.severity_filter = QComboBox()
        self.severity_filter.addItem("所有严重级别", None)
        self.severity_filter.addItem("危急 (Critical)", "critical")
        self.severity_filter.addItem("高危 (High)", "high")
        self.severity_filter.addItem("中危 (Medium)", "medium")
        self.severity_filter.addItem("低危 (Low)", "low")
        self.severity_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("严重级别:"))
        filter_layout.addWidget(self.severity_filter)
        
        # 标签筛选
        self.tag_filter = QComboBox()
        self.tag_filter.addItem("所有标签", None)
        # 将从数据库中获取所有标签并添加到下拉框
        self._populate_tag_filter()
        self.tag_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("标签:"))
        filter_layout.addWidget(self.tag_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # POC列表
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(False)  # 关闭交替行颜色
        self.list_widget.setSpacing(5)  # 设置项目间间距
        
        # 使用自定义代理来绘制列表项
        self.item_delegate = PocItemDelegate(self.list_widget)
        self.list_widget.setItemDelegate(self.item_delegate)
        
        # 设置统一项目高度
        self.list_widget.setUniformItemSizes(True)
        
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.list_widget)
        
        # 按钮行
        button_layout = QHBoxLayout()
        self.import_button = QPushButton("导入POC")
        self.import_button.clicked.connect(self._on_import)
        self.export_button = QPushButton("导出POC")
        self.export_button.clicked.connect(self._on_export)
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 设置样式
        self._set_style()
    
    def _set_style(self):
        """设置控件样式"""
        # 列表项样式
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: white;
                border-radius: 10px;
                padding: 8px;
                border: 1px solid #eeeeee;
            }
            QListWidget::item {
                border: none;
                background-color: transparent;
            }
        """)
        
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
        self.import_button.setStyleSheet(button_style)
        self.export_button.setStyleSheet(button_style)
        self.search_button.setStyleSheet(button_style)
        
        # 搜索框样式
        self.search_input.setStyleSheet("""
            QLineEdit {
                border-radius: 8px;
                padding: 8px;
                background-color: #f5f5f7;
                border: 1px solid #d1d1d6;
            }
            QLineEdit:focus {
                border: 1px solid #007aff;
            }
        """)
        
        # 下拉框样式
        combobox_style = """
            QComboBox {
                border-radius: 6px;
                padding: 6px;
                background-color: #f5f5f7;
                border: 1px solid #d1d1d6;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: #d1d1d6;
                border-left-style: solid;
                border-radius: 3px;
            }
        """
        self.severity_filter.setStyleSheet(combobox_style)
        self.tag_filter.setStyleSheet(combobox_style)
    
    def _populate_tag_filter(self):
        """填充标签筛选下拉框"""
        all_tags = set()
        pocs = self.db.get_all_pocs()
        
        for poc in pocs:
            if "tags" in poc and isinstance(poc["tags"], list):
                all_tags.update(poc["tags"])
        
        # 按字母顺序排序
        for tag in sorted(all_tags):
            self.tag_filter.addItem(tag, tag)
    
    def _populate_list(self):
        """填充POC列表"""
        self.list_widget.clear()
        
        try:
            pocs = self.db.get_all_pocs()
            
            if not pocs:
                empty_item = QListWidgetItem("没有POC记录")
                empty_item.setFlags(Qt.NoItemFlags)
                self.list_widget.addItem(empty_item)
                return
            
            for poc in pocs:
                self._add_poc_to_list(poc)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载POC列表失败: {str(e)}")
    
    def _add_poc_to_list(self, poc):
        """将POC添加到列表"""
        item = QListWidgetItem()
        
        # 设置POC数据
        item.setData(Qt.UserRole, poc)
        
        # 获取POC信息
        poc_name = poc.get("name", "未命名")
        poc_id = poc.get("id", "无ID")
        poc_path = os.path.basename(poc.get("path", "无路径"))
        severity = poc.get("severity", "").lower()
        
        # 根据严重性设置颜色
        severity_colors = {
            "critical": "#ff3b30",  # 红色
            "high": "#ff9500",      # 橙色
            "medium": "#ffcc00",    # 黄色
            "low": "#34c759"        # 绿色
        }
        severity_color = severity_colors.get(severity, "#8e8e93")
        
        # 设置项目文本（不使用HTML格式）
        item.setText(f"{poc_name} ({severity.upper()})")
        
        # 设置第二行文本作为详细信息
        item.setToolTip(f"ID: {poc_id}\n路径: {poc_path}")
        
        # 使用自定义数据显示第二行
        item.setData(Qt.UserRole + 1, f"ID: {poc_id} | 路径: {poc_path}")
        
        # 添加到列表
        self.list_widget.addItem(item)
    
    def refresh(self):
        """刷新POC列表"""
        self._populate_list()
        self._populate_tag_filter()
    
    def _on_search(self):
        """搜索处理"""
        keyword = self.search_input.text().strip()
        self._apply_filters(keyword)
    
    def _on_filter_changed(self):
        """筛选条件变化处理"""
        keyword = self.search_input.text().strip()
        self._apply_filters(keyword)
    
    def _apply_filters(self, keyword=None):
        """应用筛选条件"""
        # 获取选择的严重程度
        severity_index = self.severity_filter.currentIndex()
        severity = self.severity_filter.itemData(severity_index)
        
        # 获取选择的标签
        tag_index = self.tag_filter.currentIndex()
        tag = self.tag_filter.itemData(tag_index)
        tags = [tag] if tag else None
        
        # 搜索POC
        try:
            pocs = self.db.search_pocs(keyword, tags, severity)
            
            # 清空并重新填充列表
            self.list_widget.clear()
            
            if not pocs:
                empty_item = QListWidgetItem("没有匹配的POC记录")
                empty_item.setFlags(Qt.NoItemFlags)
                self.list_widget.addItem(empty_item)
                return
            
            for poc in pocs:
                self._add_poc_to_list(poc)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"搜索POC失败: {str(e)}")
    
    def _on_item_clicked(self, item):
        """处理列表项点击事件"""
        if item.flags() & Qt.ItemIsSelectable:
            poc_data = item.data(Qt.UserRole)
            if poc_data:
                self.poc_selected.emit(poc_data)
    
    def _show_context_menu(self, position):
        """显示右键菜单"""
        item = self.list_widget.itemAt(position)
        if not item or not (item.flags() & Qt.ItemIsSelectable):
            return
        
        poc_data = item.data(Qt.UserRole)
        if not poc_data:
            return
        
        # 创建右键菜单
        context_menu = QMenu(self)
        
        # 添加菜单项
        edit_action = context_menu.addAction("编辑")
        delete_action = context_menu.addAction("删除")
        export_action = context_menu.addAction("导出")
        execute_action = context_menu.addAction("执行POC")
        
        # 显示菜单并获取用户选择的动作
        action = context_menu.exec_(QCursor.pos())
        
        # 处理菜单选择
        if action == edit_action:
            # TODO: 实现编辑POC功能
            pass
        elif action == delete_action:
            self._delete_poc(poc_data)
        elif action == export_action:
            self._export_poc(poc_data)
        elif action == execute_action:
            self._execute_poc(poc_data)
    
    def _delete_poc(self, poc_data):
        """删除POC记录"""
        if not poc_data or "id" not in poc_data:
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除 '{poc_data.get('name', '未命名')}' 吗？\n(注意：只会删除数据库记录，不会删除实际文件)",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 删除数据库记录
                success = self.db.delete_poc(poc_data["id"])
                if success:
                    QMessageBox.information(self, "成功", "POC记录已删除")
                    self.refresh()
                else:
                    QMessageBox.warning(self, "警告", "删除POC记录失败，可能记录不存在")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除POC记录时发生错误: {str(e)}")
    
    def _on_import(self):
        """导入POC文件"""
        # 选择文件
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择POC文件", "", 
            "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        
        if not file_paths:
            return
        
        # 处理每个文件
        imported_count = 0
        for file_path in file_paths:
            try:
                # 从文件名提取名称
                file_name = os.path.basename(file_path)
                name = os.path.splitext(file_name)[0]
                
                # 创建POC记录
                poc_data = {
                    "name": name,
                    "path": file_path,
                    "severity": "medium",  # 默认为中危
                    "tags": []
                }
                
                # TODO: 解析YAML文件获取更多信息
                
                # 添加到数据库
                self.db.add_poc(poc_data)
                imported_count += 1
                
            except Exception as e:
                QMessageBox.warning(
                    self, "导入警告", 
                    f"导入文件 {file_path} 失败: {str(e)}"
                )
        
        if imported_count > 0:
            QMessageBox.information(
                self, "导入成功", 
                f"成功导入 {imported_count} 个POC文件"
            )
            self.refresh()
    
    def _on_export(self):
        """导出所有POC"""
        # 选择导出目录
        export_dir = QFileDialog.getExistingDirectory(
            self, "选择导出目录", ""
        )
        
        if not export_dir:
            return
        
        # 获取所有POC
        pocs = self.db.get_all_pocs()
        if not pocs:
            QMessageBox.information(self, "导出", "没有POC可以导出")
            return
        
        # 导出每个POC
        export_count = 0
        for poc in pocs:
            if "path" not in poc or not os.path.exists(poc["path"]):
                continue
            
            try:
                # 生成导出文件路径
                file_name = os.path.basename(poc["path"])
                export_path = os.path.join(export_dir, file_name)
                
                # 复制文件
                with open(poc["path"], "r", encoding="utf-8") as src_file:
                    content = src_file.read()
                
                with open(export_path, "w", encoding="utf-8") as dst_file:
                    dst_file.write(content)
                
                export_count += 1
                
            except Exception as e:
                QMessageBox.warning(
                    self, "导出警告", 
                    f"导出POC {poc.get('name', '未命名')} 失败: {str(e)}"
                )
        
        if export_count > 0:
            QMessageBox.information(
                self, "导出成功", 
                f"成功导出 {export_count} 个POC文件到 {export_dir}"
            )
    
    def _export_poc(self, poc_data):
        """导出单个POC"""
        if not poc_data or "path" not in poc_data or not os.path.exists(poc_data["path"]):
            QMessageBox.warning(self, "导出警告", "POC文件路径无效或文件不存在")
            return
        
        # 选择导出目录
        export_dir = QFileDialog.getExistingDirectory(
            self, "选择导出目录", ""
        )
        
        if not export_dir:
            return
        
        try:
            # 生成导出文件路径
            file_name = os.path.basename(poc_data["path"])
            export_path = os.path.join(export_dir, file_name)
            
            # 复制文件
            with open(poc_data["path"], "r", encoding="utf-8") as src_file:
                content = src_file.read()
            
            with open(export_path, "w", encoding="utf-8") as dst_file:
                dst_file.write(content)
            
            QMessageBox.information(
                self, "导出成功", 
                f"POC文件已导出到 {export_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "导出错误", 
                f"导出POC失败: {str(e)}"
            )
    
    def _execute_poc(self, poc_data):
        """执行POC"""
        if not poc_data or "path" not in poc_data:
            QMessageBox.warning(self, "执行POC", "POC路径无效")
            return
        
        path = poc_data.get("path", "")
        if not os.path.exists(path):
            QMessageBox.warning(self, "执行POC", "POC文件不存在")
            return
            
        # 创建并显示执行对话框
        dialog = PocExecutionDialog(poc_data, self)
        dialog.exec_()


class PocExecutionDialog(QDialog):
    """POC执行对话框，用于配置执行参数和显示执行结果"""
    
    def __init__(self, poc_data, parent=None):
        super().__init__(parent)
        self.poc_data = poc_data
        self.process = None
        self.setWindowTitle("执行POC")
        self.resize(800, 600)
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # POC信息
        info_group = QGroupBox("POC信息")
        info_layout = QFormLayout(info_group)
        
        # POC名称
        name = self.poc_data.get("name", "未命名")
        info_layout.addRow("名称:", QLabel(name))
        
        # POC ID
        poc_id = self.poc_data.get("id", "无ID")
        info_layout.addRow("ID:", QLabel(poc_id))
        
        # POC路径
        path = self.poc_data.get("path", "")
        path_label = QLabel(path)
        path_label.setWordWrap(True)
        info_layout.addRow("文件路径:", path_label)
        
        # 严重程度
        severity = self.poc_data.get("severity", "").upper()
        severity_colors = {
            "CRITICAL": "#ff3b30",  # 红色
            "HIGH": "#ff9500",      # 橙色
            "MEDIUM": "#ffcc00",    # 黄色
            "LOW": "#34c759"        # 绿色
        }
        severity_color = severity_colors.get(severity, "#8e8e93")
        severity_label = QLabel(severity)
        severity_label.setStyleSheet(f"color: {severity_color}; font-weight: bold;")
        info_layout.addRow("严重程度:", severity_label)
        
        layout.addWidget(info_group)
        
        # 执行参数
        param_group = QGroupBox("执行参数")
        param_layout = QVBoxLayout(param_group)
        
        form_layout = QFormLayout()
        
        # 目标URL
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("输入目标URL，如 https://example.com")
        form_layout.addRow("目标URL:", self.target_input)
        
        # 高级选项
        options_layout = QHBoxLayout()
        
        self.verbose_checkbox = QCheckBox("详细输出")
        self.debug_checkbox = QCheckBox("调试模式")
        self.no_color_checkbox = QCheckBox("无颜色输出")
        
        options_layout.addWidget(self.verbose_checkbox)
        options_layout.addWidget(self.debug_checkbox)
        options_layout.addWidget(self.no_color_checkbox)
        
        form_layout.addRow("选项:", options_layout)
        
        # 超时设置
        self.timeout_combo = QComboBox()
        self.timeout_combo.addItem("5秒", "5")
        self.timeout_combo.addItem("10秒", "10")
        self.timeout_combo.addItem("30秒", "30")
        self.timeout_combo.addItem("60秒", "60")
        self.timeout_combo.setCurrentIndex(1)  # 默认10秒
        form_layout.addRow("超时时间:", self.timeout_combo)
        
        param_layout.addLayout(form_layout)
        
        # 命令预览
        self.command_preview = QLineEdit()
        self.command_preview.setReadOnly(True)
        self.command_preview.setStyleSheet("background-color: #f5f5f7;")
        param_layout.addWidget(QLabel("命令预览:"))
        param_layout.addWidget(self.command_preview)
        
        layout.addWidget(param_group)
        
        # 输出区域
        output_group = QGroupBox("执行输出")
        output_layout = QVBoxLayout(output_group)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                background-color: #1e1e1e;
                color: #f5f5f5;
                padding: 5px;
            }
        """)
        output_layout.addWidget(self.output_text)
        
        layout.addWidget(output_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.execute_button = QPushButton("执行POC")
        self.execute_button.clicked.connect(self._execute_poc)
        self.execute_button.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border-radius: 8px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2eb350;
            }
            QPushButton:pressed {
                background-color: #269f45;
            }
        """)
        
        self.stop_button = QPushButton("停止执行")
        self.stop_button.clicked.connect(self._stop_execution)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #ff3b30;
                color: white;
                border-radius: 8px;
                padding: 8px 15px;
                font-weight: bold;
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
        
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.reject)
        close_button.setStyleSheet("""
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
        """)
        
        button_layout.addWidget(self.execute_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        # 连接信号槽以更新命令预览
        self.target_input.textChanged.connect(self._update_command_preview)
        self.verbose_checkbox.stateChanged.connect(self._update_command_preview)
        self.debug_checkbox.stateChanged.connect(self._update_command_preview)
        self.no_color_checkbox.stateChanged.connect(self._update_command_preview)
        self.timeout_combo.currentIndexChanged.connect(self._update_command_preview)
        
        # 初始更新命令预览
        self._update_command_preview()
        
    def _update_command_preview(self):
        """更新命令预览"""
        # 找到Nuclei可执行文件路径
        nuclei_path = os.path.abspath(os.path.join("Tools", "nuclei.exe"))
        
        # 构建命令行参数
        target_url = self.target_input.text().strip()
        poc_path = self.poc_data.get("path", "")
        
        # 基本命令格式
        command = [nuclei_path, "-t", poc_path]
        
        # 添加目标URL
        if target_url:
            command.extend(["-u", target_url])
        
        # 添加超时设置
        timeout = self.timeout_combo.currentData()
        if timeout:
            command.extend(["-timeout", timeout])
        
        # 添加其他选项
        if self.verbose_checkbox.isChecked():
            command.append("-v")
        
        if self.debug_checkbox.isChecked():
            command.append("-debug")
        
        if self.no_color_checkbox.isChecked():
            command.append("-no-color")
        
        # 更新命令预览
        command_str = " ".join(command)
        self.command_preview.setText(command_str)
        
    def _execute_poc(self):
        """执行POC"""
        # 检查目标URL
        target_url = self.target_input.text().strip()
        if not target_url:
            QMessageBox.warning(self, "参数错误", "请输入目标URL")
            return
        
        # 检查POC文件路径
        poc_path = self.poc_data.get("path", "")
        if not os.path.exists(poc_path):
            QMessageBox.warning(self, "文件错误", "POC文件不存在")
            return
        
        # 找到Nuclei可执行文件路径
        nuclei_path = os.path.abspath(os.path.join("Tools", "nuclei.exe"))
        if not os.path.exists(nuclei_path):
            QMessageBox.critical(self, "错误", "未找到nuclei工具，请确保Tools目录下存在nuclei.exe")
            return
        
        # 构建命令行参数
        command = [nuclei_path, "-t", poc_path, "-u", target_url]
        
        # 添加超时设置
        timeout = self.timeout_combo.currentData()
        if timeout:
            command.extend(["-timeout", timeout])
        
        # 添加其他选项
        if self.verbose_checkbox.isChecked():
            command.append("-v")
        
        if self.debug_checkbox.isChecked():
            command.append("-debug")
        
        if self.no_color_checkbox.isChecked():
            command.append("-no-color")
        
        # 清空输出区域
        self.output_text.clear()
        
        # 创建进程
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process.readyReadStandardError.connect(self._handle_stderr)
        self.process.finished.connect(self._process_finished)
        
        # 更新按钮状态
        self.execute_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # 开始执行
        self.output_text.append(f"<span style='color:#34c759'>正在执行命令: {' '.join(command)}</span>")
        self.output_text.append("<span style='color:#34c759'>======= 开始执行 =======</span>")
        self.process.start(command[0], command[1:])
        
    def _handle_stdout(self):
        """处理标准输出"""
        if self.process:
            data = self.process.readAllStandardOutput().data().decode('utf-8', errors='replace')
            self._append_output(data)
            
    def _handle_stderr(self):
        """处理标准错误输出"""
        if self.process:
            data = self.process.readAllStandardError().data().decode('utf-8', errors='replace')
            self._append_output(f"<span style='color:#ff3b30'>{data}</span>")
            
    def _process_finished(self, exit_code, exit_status):
        """进程完成处理"""
        # 更新按钮状态
        self.execute_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        # 显示执行结果
        if exit_code == 0:
            self.output_text.append("<span style='color:#34c759'>======= 执行完成 =======</span>")
        else:
            self.output_text.append(f"<span style='color:#ff3b30'>======= 执行失败 (退出代码: {exit_code}) =======</span>")
        
        # 清理进程
        self.process = None
        
    def _stop_execution(self):
        """停止执行"""
        if self.process and self.process.state() == QProcess.Running:
            self.process.kill()
            self.output_text.append("<span style='color:#ff9500'>======= 执行已停止 =======</span>")
            self.execute_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            
    def _append_output(self, text):
        """添加输出文本"""
        # 添加文本
        self.output_text.append(text)
        
        # 滚动到底部
        cursor = self.output_text.textCursor()
        cursor.movePosition(cursor.End)
        self.output_text.setTextCursor(cursor)
        
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 如果进程还在运行，则杀死进程
        if self.process and self.process.state() == QProcess.Running:
            result = QMessageBox.question(
                self, "确认", "POC正在执行中，确定要停止并关闭窗口吗？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if result == QMessageBox.Yes:
                self.process.kill()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


class PocContentView(QWidget):
    """POC内容预览组件"""
    execute_poc = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.current_poc = None
    
    def _init_ui(self):
        """初始化UI"""
        # 主布局
        layout = QVBoxLayout(self)
        
        # 头部信息
        self.header_frame = QFrame()
        self.header_frame.setFrameShape(QFrame.StyledPanel)
        self.header_frame.setFrameShadow(QFrame.Raised)
        self.header_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f7;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        
        header_layout = QVBoxLayout(self.header_frame)
        
        # POC名称
        self.name_label = QLabel()
        self.name_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        header_layout.addWidget(self.name_label)
        
        # POC ID 和路径
        info_layout = QHBoxLayout()
        self.id_label = QLabel()
        self.path_label = QLabel()
        info_layout.addWidget(self.id_label)
        info_layout.addStretch()
        info_layout.addWidget(self.path_label)
        header_layout.addLayout(info_layout)
        
        # 严重程度和标签
        meta_layout = QHBoxLayout()
        self.severity_label = QLabel()
        self.severity_label.setStyleSheet("font-weight: bold;")
        self.tags_label = QLabel()
        meta_layout.addWidget(QLabel("严重程度:"))
        meta_layout.addWidget(self.severity_label)
        meta_layout.addStretch()
        meta_layout.addWidget(QLabel("标签:"))
        meta_layout.addWidget(self.tags_label)
        header_layout.addLayout(meta_layout)
        
        layout.addWidget(self.header_frame)
        
        # 内容预览
        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        self.content_text.setStyleSheet("""
            QTextEdit {
                border-radius: 10px;
                padding: 10px;
                background-color: #f5f5f7;
                font-family: "Courier New", monospace;
            }
        """)
        layout.addWidget(self.content_text)
        
        # 按钮栏
        button_layout = QHBoxLayout()
        
        self.execute_button = QPushButton("执行POC")
        self.execute_button.clicked.connect(self._on_execute)
        self.execute_button.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border-radius: 8px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2eb350;
            }
            QPushButton:pressed {
                background-color: #269f45;
            }
        """)
        
        self.edit_button = QPushButton("编辑POC")
        self.edit_button.clicked.connect(self._on_edit)
        self.edit_button.setStyleSheet("""
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
        
        button_layout.addWidget(self.execute_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 初始状态
        self.set_empty_state()
    
    def set_empty_state(self):
        """设置空状态"""
        self.name_label.setText("请选择POC")
        self.id_label.setText("")
        self.path_label.setText("")
        self.severity_label.setText("")
        self.tags_label.setText("")
        self.content_text.setText("")
        
        self.execute_button.setEnabled(False)
        self.edit_button.setEnabled(False)
        
        self.current_poc = None
    
    def show_poc(self, poc_data):
        """显示POC内容"""
        if not poc_data:
            self.set_empty_state()
            return
        
        # 保存当前POC数据
        self.current_poc = poc_data
        
        # 更新UI显示
        self.name_label.setText(poc_data.get("name", "未命名"))
        self.id_label.setText(f"ID: {poc_data.get('id', '无ID')}")
        
        path = poc_data.get("path", "")
        self.path_label.setText(f"路径: {path}")
        
        # 设置严重程度和颜色
        severity = poc_data.get("severity", "").lower()
        severity_colors = {
            "critical": "#ff3b30",  # 红色
            "high": "#ff9500",      # 橙色
            "medium": "#ffcc00",    # 黄色
            "low": "#34c759"        # 绿色
        }
        severity_color = severity_colors.get(severity, "#8e8e93")
        self.severity_label.setStyleSheet(f"font-weight: bold; color: {severity_color}")
        self.severity_label.setText(severity.upper())
        
        # 设置标签
        tags = poc_data.get("tags", [])
        if tags:
            self.tags_label.setText(", ".join(tags))
        else:
            self.tags_label.setText("无标签")
        
        # 尝试加载文件内容
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.content_text.setText(content)
                self.execute_button.setEnabled(True)
                self.edit_button.setEnabled(True)
            else:
                self.content_text.setText("文件路径无效或文件不存在")
                self.execute_button.setEnabled(False)
                self.edit_button.setEnabled(False)
        except Exception as e:
            self.content_text.setText(f"加载文件内容失败: {str(e)}")
            self.execute_button.setEnabled(False)
            self.edit_button.setEnabled(False)
    
    def _on_execute(self):
        """执行POC"""
        if self.current_poc:
            if not os.path.exists(self.current_poc.get("path", "")):
                QMessageBox.warning(self, "执行POC", "POC文件不存在")
                return
            
            # 创建并显示执行对话框
            dialog = PocExecutionDialog(self.current_poc, self)
            dialog.exec_()
    
    def _on_edit(self):
        """编辑POC"""
        if not self.current_poc:
            return
        
        # TODO: 实现编辑POC功能
        QMessageBox.information(self, "编辑POC", "编辑功能尚未实现")


class PocManagementView(QWidget):
    """POC管理主视图"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        # 主布局
        layout = QHBoxLayout(self)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        # 左侧POC列表
        self.poc_list_view = PocListView()
        splitter.addWidget(self.poc_list_view)
        
        # 右侧POC内容预览
        self.poc_content_view = PocContentView()
        splitter.addWidget(self.poc_content_view)
        
        # 设置初始分割比例
        splitter.setSizes([300, 500])
        
        layout.addWidget(splitter)
        
        # 连接信号
        self.poc_list_view.poc_selected.connect(self.poc_content_view.show_poc)
        self.poc_content_view.execute_poc.connect(self._on_execute_poc)
    
    def _on_execute_poc(self, poc_data):
        """处理执行POC请求"""
        if not poc_data or "path" not in poc_data:
            QMessageBox.warning(self, "执行POC", "POC路径无效")
            return
        
        path = poc_data.get("path", "")
        if not os.path.exists(path):
            QMessageBox.warning(self, "执行POC", "POC文件不存在")
            return
        
        # 创建并显示执行对话框
        dialog = PocExecutionDialog(poc_data, self)
        dialog.exec_() 