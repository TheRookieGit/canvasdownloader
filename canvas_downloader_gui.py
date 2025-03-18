#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
import subprocess
import re
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QFileDialog, QCheckBox, 
                            QListWidget, QGroupBox, QFormLayout, QSpinBox, QMessageBox,
                            QTabWidget, QTextEdit, QScrollArea, QFrame, QListWidgetItem)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon, QFont

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("canvas-downloader-gui")

def find_canvassyncer_path():
    """查找canvassyncer可执行文件路径"""
    # 优先使用Python模块方式运行
    return "python3 -m canvassyncer"

    # 以下是备用方式，在PyInstaller打包环境中可能不适用
    # 可能的路径列表
    possible_paths = [
        # 标准PATH路径
        "canvassyncer",
        # 用户Python路径
        os.path.expanduser("~/Library/Python/3.9/bin/canvassyncer"),
        os.path.expanduser("~/Library/Python/3.8/bin/canvassyncer"),
        os.path.expanduser("~/Library/Python/3.7/bin/canvassyncer"),
        os.path.expanduser("~/.local/bin/canvassyncer"),
        # 虚拟环境路径
        os.path.join(sys.prefix, "bin", "canvassyncer"),
    ]
    
    # 检查每个可能的路径
    for path in possible_paths:
        try:
            # 使用which命令查找
            if path == "canvassyncer":
                result = subprocess.run(["which", "canvassyncer"], 
                                       capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            # 直接检查文件存在性
            elif os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        except Exception:
            pass
    
    # 如果找不到，尝试作为Python模块运行
    return "python3 -m canvassyncer"

class DownloadThread(QThread):
    """下载线程，防止UI卡顿"""
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, config_file, timeout):
        super().__init__()
        self.config_file = config_file
        self.timeout = timeout
        self.current_course = None
        self.total_files_downloaded = 0
        
    def run(self):
        self.progress_signal.emit(f"开始下载: {os.path.basename(self.config_file)}")
        
        # 验证配置文件
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 检查必要字段 - 兼容两种格式
            required_fields = []
            
            # 新格式
            if "base_url" in config and "course_id" in config:
                required_fields = ["token", "base_url", "course_id"]
            # 旧格式
            else:
                required_fields = ["token", "canvasURL", "courseIDs"]
                
            for field in required_fields:
                if field not in config:
                    self.progress_signal.emit(f"错误: 配置缺少必要字段 '{field}'")
                    self.finished_signal.emit(False, f"配置缺少必要字段: {field}")
                    return
            
            # 检查是否有课程ID
            if "courseIDs" in config and not config["courseIDs"]:
                self.progress_signal.emit("错误: 没有指定任何课程ID")
                self.finished_signal.emit(False, "没有指定任何课程ID")
                return
                
        except Exception as e:
            self.progress_signal.emit(f"错误: 无法解析配置文件: {e}")
            self.finished_signal.emit(False, f"无法解析配置文件: {e}")
            return
        
        # 执行下载
        try:
            # 查找canvassyncer可执行文件路径
            canvassyncer_path = find_canvassyncer_path()
            
            # 成功计数
            successful_courses = 0
            failed_courses = 0
            
            # 读取课程ID列表
            course_ids = config.get("courseIDs", [])
            total_courses = len(course_ids)
            
            self.progress_signal.emit(f"准备下载 {total_courses} 个课程的文件")
            
            for i, course_id in enumerate(course_ids):
                self.current_course = course_id
                self.progress_signal.emit(f"\n=== 课程 {i+1}/{total_courses}: ID {course_id} ===")
                
                # 创建单课程的临时配置
                import tempfile
                fd, temp_course_config = tempfile.mkstemp(suffix='.json')
                os.close(fd)
                
                # 复制原始配置并更新单课程ID
                single_course_config = config.copy()
                single_course_config["courseIDs"] = [course_id]
                
                with open(temp_course_config, 'w', encoding='utf-8') as f:
                    json.dump(single_course_config, f, indent=2, ensure_ascii=False)
                
                # 构建命令
                if canvassyncer_path == "python3 -m canvassyncer":
                    command = ["python3", "-m", "canvassyncer", "-p", temp_course_config]
                else:
                    command = [canvassyncer_path, "-p", temp_course_config]
                    
                self.progress_signal.emit(f"使用路径: {canvassyncer_path}")
                self.progress_signal.emit(f"执行命令: {' '.join(command)}")
                
                # 创建进程
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    universal_newlines=True
                )
                
                # 记录标准输出和错误
                stdout_lines = []
                stderr_lines = []
                
                # 读取输出
                for line in process.stdout:
                    cleaned_line = line.strip()
                    stdout_lines.append(cleaned_line)
                    self.progress_signal.emit(cleaned_line)
                
                # 尝试读取错误输出
                for line in process.stderr:
                    cleaned_line = line.strip()
                    stderr_lines.append(cleaned_line)
                    
                    # 检查是否为进度条或无害警告
                    if self.is_progress_bar(cleaned_line) or self.is_harmless_warning(cleaned_line):
                        # 仍然显示输出，但不将其视为错误
                        self.progress_signal.emit(f"信息: {cleaned_line}")
                    else:
                        self.progress_signal.emit(f"错误: {cleaned_line}")
                    
                # 等待进程完成，最多等待timeout秒
                try:
                    return_code = process.wait(timeout=self.timeout)
                    
                    # 检查是否有可能的错误
                    has_error = False
                    error_message = ""
                    
                    # 检查错误输出和常见错误信息
                    for line in stderr_lines:
                        if line and not self.is_harmless_warning(line) and not self.is_progress_bar(line):
                            has_error = True
                            error_message = line
                            break
                            
                    # 检查标准输出中的错误信息
                    for line in stdout_lines:
                        if "error:" in line.lower() or "exception:" in line.lower() or "traceback" in line.lower():
                            has_error = True
                            error_message = line
                            break
                    
                    # 特别处理KeyError情况
                    if any("KeyError" in line for line in stdout_lines):
                        self.progress_signal.emit(f"错误: 课程 {course_id} 配置或网络问题")
                        self.progress_signal.emit("请检查:")
                        self.progress_signal.emit("1. Canvas API令牌是否有效")
                        self.progress_signal.emit("2. Canvas网址是否正确")
                        self.progress_signal.emit("3. 课程ID是否存在")
                        self.progress_signal.emit("4. 网络连接是否正常")
                        failed_courses += 1
                        # 删除临时文件
                        try:
                            os.remove(temp_course_config)
                        except:
                            pass
                        continue
                    
                    # 检查下载完成的文件数量
                    files_found = 0
                    files_downloaded = 0
                    
                    for line in stdout_lines:
                        if "Get " in line and " files!" in line:
                            try:
                                files_found = int(line.split("Get ")[1].split(" files")[0])
                            except:
                                pass
                        
                        if "Start to download " in line and " file(s)!" in line:
                            try:
                                files_downloaded = int(line.split("Start to download ")[1].split(" file(s)")[0])
                            except:
                                pass
                    
                    # 如果找到文件并开始下载，且没有明确的错误，就认为是成功的
                    if files_found > 0 and not has_error:
                        self.progress_signal.emit(f"课程 {course_id} 下载成功！共下载了 {files_downloaded} 个文件。")
                        successful_courses += 1
                        self.total_files_downloaded += files_downloaded
                    elif return_code == 0 and not has_error:
                        self.progress_signal.emit(f"课程 {course_id} 下载成功!")
                        successful_courses += 1
                    else:
                        if has_error:
                            self.progress_signal.emit(f"课程 {course_id} 下载失败: {error_message}")
                        else:
                            self.progress_signal.emit(f"课程 {course_id} 下载失败，返回代码: {return_code}")
                        failed_courses += 1
                        
                except subprocess.TimeoutExpired:
                    process.kill()
                    self.progress_signal.emit(f"课程 {course_id} 下载超时 (>{self.timeout}秒)")
                    failed_courses += 1
                
                # 删除临时文件
                try:
                    os.remove(temp_course_config)
                except:
                    pass
            
            # 总结结果
            self.progress_signal.emit("\n=== 下载完成 ===")
            self.progress_signal.emit(f"总课程数: {total_courses}")
            self.progress_signal.emit(f"成功下载: {successful_courses} 个课程")
            if failed_courses > 0:
                self.progress_signal.emit(f"下载失败: {failed_courses} 个课程")
            self.progress_signal.emit(f"总共下载了 {self.total_files_downloaded} 个文件")
            
            if successful_courses == total_courses:
                self.finished_signal.emit(True, f"所有 {total_courses} 个课程下载成功")
            else:
                self.finished_signal.emit(False, f"部分课程下载失败 ({failed_courses}/{total_courses})")
                
        except FileNotFoundError:
            self.progress_signal.emit("错误: 找不到canvassyncer命令")
            self.progress_signal.emit("请确保已安装canvassyncer，可以使用 'pip install canvassyncer' 安装")
            self.finished_signal.emit(False, "找不到canvassyncer命令")
        except Exception as e:
            self.progress_signal.emit(f"错误: {str(e)}")
            self.finished_signal.emit(False, str(e))
            
    def is_progress_bar(self, line):
        """检查是否为进度条输出"""
        # 进度条通常包含百分比和进度条字符
        if "%" in line and ("|" in line or "[" in line):
            return True
        # tqdm进度条的典型模式
        if re.search(r'\d+%\|[\s\w█▏▎▍▌▋▊▉]*\|', line):
            return True
        # 检查是否包含下载速度和大小信息
        if re.search(r'\d+\.\d+[kMG]B/s', line):
            return True
        # 检查是否包含时间信息
        if re.search(r'\[\d+:\d+<\d+:\d+', line):
            return True
        return False
        
    def is_harmless_warning(self, line):
        """检查是否为无害警告"""
        harmless_patterns = [
            "RuntimeWarning: 'canvassyncer.__main__' found in sys.modules",
            "this may result in unpredictable behaviour",
            "warn(RuntimeWarning",
            "RuntimeWarning",
            "Warning:",
            "warning:"
        ]
        
        # 检查是否包含任何无害警告模式
        if any(pattern in line for pattern in harmless_patterns):
            return True
            
        # 检查是否为Python的导入警告
        if "found in sys.modules after import" in line:
            return True
            
        return False


class ConfigEditorWidget(QWidget):
    """配置编辑器小部件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout()
        
        # 基本信息表单
        form_group = QGroupBox("基本配置")
        form_layout = QFormLayout()
        
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.Password)  # 密码模式，不显示明文
        self.token_input.setPlaceholderText("填写您的Canvas API令牌")
        
        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("例如: https://canvas.ucdavis.edu")
        
        # 多个课程ID输入框
        self.course_id_inputs = []
        course_id_layout = QVBoxLayout()
        
        for i in range(5):
            course_input = QLineEdit()
            course_input.setPlaceholderText(f"课程ID {i+1} (数字，可选)")
            self.course_id_inputs.append(course_input)
            course_id_layout.addWidget(course_input)
        
        # 下载路径选择
        path_layout = QHBoxLayout()
        self.download_path_input = QLineEdit()
        self.download_path_input.setPlaceholderText("文件保存位置")
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self.browse_folder)
        path_layout.addWidget(self.download_path_input)
        path_layout.addWidget(self.browse_btn)
        
        # 添加表单字段
        form_layout.addRow("Canvas API令牌:", self.token_input)
        form_layout.addRow("Canvas网址:", self.base_url_input)
        form_layout.addRow("课程ID列表:", course_id_layout)
        form_layout.addRow("下载目录:", path_layout)
        form_group.setLayout(form_layout)
        
        # 文件类型过滤器
        filter_group = QGroupBox("文件类型过滤")
        filter_layout = QVBoxLayout()
        
        # 包含的文件类型
        includes_layout = QVBoxLayout()
        includes_label = QLabel("选择要下载的文件类型:")
        self.includes_list = QListWidget()
        self.includes_list.setSelectionMode(QListWidget.MultiSelection)
        
        # 常见文件类型
        common_types = ["pdf", "docx", "pptx", "xlsx", "txt", "zip", "mp4", "mp3", "jpg", "png"]
        for file_type in common_types:
            item = QListWidgetItem(file_type)
            self.includes_list.addItem(item)
        
        includes_layout.addWidget(includes_label)
        includes_layout.addWidget(self.includes_list)
        
        # 排除的文件类型
        excludes_layout = QVBoxLayout()
        excludes_label = QLabel("选择要排除的文件类型:")
        self.excludes_list = QListWidget()
        self.excludes_list.setSelectionMode(QListWidget.MultiSelection)
        
        # 添加相同的常见文件类型供排除
        for file_type in common_types:
            item = QListWidgetItem(file_type)
            self.excludes_list.addItem(item)
            
        excludes_layout.addWidget(excludes_label)
        excludes_layout.addWidget(self.excludes_list)
        
        # 水平布局放置两个列表
        types_layout = QHBoxLayout()
        types_layout.addLayout(includes_layout)
        types_layout.addLayout(excludes_layout)
        
        filter_layout.addLayout(types_layout)
        filter_group.setLayout(filter_layout)
        
        # 按钮
        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存配置")
        self.save_btn.clicked.connect(self.save_config)
        self.load_btn = QPushButton("加载配置")
        self.load_btn.clicked.connect(self.load_config)
        buttons_layout.addWidget(self.load_btn)
        buttons_layout.addWidget(self.save_btn)
        
        # 添加所有组件到主布局
        main_layout.addWidget(form_group)
        main_layout.addWidget(filter_group)
        main_layout.addLayout(buttons_layout)
        
        self.setLayout(main_layout)
        
    def browse_folder(self):
        """选择下载文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择下载文件夹")
        if folder:
            self.download_path_input.setText(folder)
            
    def save_config(self):
        """保存配置到文件"""
        if not self.validate_inputs():
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存配置文件", "", "JSON文件 (*.json)"
        )
        
        if not file_path:
            return
            
        # 如果没有.json后缀，添加它
        if not file_path.endswith('.json'):
            file_path += '.json'
            
        # 收集所有有效的课程ID
        course_ids = []
        for course_input in self.course_id_inputs:
            if course_input.text().strip():
                try:
                    course_ids.append(int(course_input.text()))
                except ValueError:
                    pass
            
        # 构建配置 - 使用与原有脚本兼容的格式
        config = {
            "canvasURL": self.base_url_input.text(),
            "token": self.token_input.text(),
            "courseIDs": course_ids,
            "downloadDir": self.download_path_input.text(),
            "filesizeThresh": 1000000000.0,  # 默认1GB文件大小限制
            "allowAudio": True,
            "allowVideo": True,
            "allowImage": True,
            "courseCodes": []
        }
        
        # 添加文件类型过滤配置
        includes = []
        for i in range(self.includes_list.count()):
            item = self.includes_list.item(i)
            if item.isSelected():
                includes.append(item.text())
                
        if includes:
            config["includes"] = includes
            
        excludes = []
        for i in range(self.excludes_list.count()):
            item = self.excludes_list.item(i)
            if item.isSelected():
                excludes.append(item.text())
                
        if excludes:
            config["excludes"] = excludes
            
        # 保存到文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "成功", f"配置已保存到: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置时出错: {str(e)}")
            
    def load_config(self):
        """从文件加载配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开配置文件", "", "JSON文件 (*.json)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 设置基本字段 - 兼容两种格式
            if "token" in config:
                self.token_input.setText(config["token"])
                
            if "canvasURL" in config:
                self.base_url_input.setText(config["canvasURL"])
            elif "base_url" in config:
                self.base_url_input.setText(config["base_url"])
                
            # 清空所有课程输入框
            for course_input in self.course_id_inputs:
                course_input.clear()
                
            # 设置课程ID
            if "courseIDs" in config and len(config["courseIDs"]) > 0:
                for i, course_id in enumerate(config["courseIDs"]):
                    if i < len(self.course_id_inputs):
                        self.course_id_inputs[i].setText(str(course_id))
            elif "course_id" in config:
                self.course_id_inputs[0].setText(str(config["course_id"]))
                
            if "downloadDir" in config:
                self.download_path_input.setText(config["downloadDir"])
            elif "download_path" in config:
                self.download_path_input.setText(config["download_path"])
                
            # 清除所有选择
            for i in range(self.includes_list.count()):
                self.includes_list.item(i).setSelected(False)
            for i in range(self.excludes_list.count()):
                self.excludes_list.item(i).setSelected(False)
                
            # 设置包含的文件类型
            if "includes" in config:
                for i in range(self.includes_list.count()):
                    item = self.includes_list.item(i)
                    if item.text() in config["includes"]:
                        item.setSelected(True)
                        
            # 设置排除的文件类型
            if "excludes" in config:
                for i in range(self.excludes_list.count()):
                    item = self.excludes_list.item(i)
                    if item.text() in config["excludes"]:
                        item.setSelected(True)
                        
            QMessageBox.information(self, "成功", f"已加载配置: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载配置时出错: {str(e)}")
            
    def validate_inputs(self):
        """验证输入字段"""
        if not self.token_input.text():
            QMessageBox.warning(self, "验证失败", "请输入Canvas API令牌")
            return False
            
        if not self.base_url_input.text():
            QMessageBox.warning(self, "验证失败", "请输入Canvas网址")
            return False
            
        # 检查是否至少有一个课程ID
        has_course_id = False
        for course_input in self.course_id_inputs:
            if course_input.text().strip():
                has_course_id = True
                break
                
        if not has_course_id:
            QMessageBox.warning(self, "验证失败", "请至少输入一个课程ID")
            return False
            
        if not self.download_path_input.text():
            QMessageBox.warning(self, "验证失败", "请选择下载路径")
            return False
            
        return True
        
    def get_config(self):
        """返回当前配置 - 使用与canvassyncer兼容的格式"""
        # 收集所有有效的课程ID
        course_ids = []
        for course_input in self.course_id_inputs:
            if course_input.text().strip():
                try:
                    course_ids.append(int(course_input.text()))
                except ValueError:
                    pass
                    
        config = {
            "canvasURL": self.base_url_input.text(),
            "token": self.token_input.text(),
            "courseIDs": course_ids,
            "downloadDir": self.download_path_input.text(),
            "filesizeThresh": 1000000000.0,
            "allowAudio": True,
            "allowVideo": True,
            "allowImage": True,
            "courseCodes": []
        }
        
        # 添加包含的文件类型
        includes = []
        for i in range(self.includes_list.count()):
            item = self.includes_list.item(i)
            if item.isSelected():
                includes.append(item.text())
                
        if includes:
            config["includes"] = includes
            
        # 添加排除的文件类型
        excludes = []
        for i in range(self.excludes_list.count()):
            item = self.excludes_list.item(i)
            if item.isSelected():
                excludes.append(item.text())
                
        if excludes:
            config["excludes"] = excludes
            
        return config


class CanvasDownloaderGUI(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.temp_config_file = None
        self.download_threads = []
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("Canvas下载助手")
        self.setMinimumSize(800, 600)
        
        # 中央小部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 配置编辑器标签页
        self.config_editor = ConfigEditorWidget()
        tab_widget.addTab(self.config_editor, "配置课程")
        
        # 下载管理标签页
        download_widget = QWidget()
        download_layout = QVBoxLayout(download_widget)
        
        # 下载设置
        settings_group = QGroupBox("下载设置")
        settings_layout = QHBoxLayout()
        
        timeout_layout = QHBoxLayout()
        timeout_label = QLabel("超时时间(秒):")
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(60, 3600)
        self.timeout_spin.setValue(300)
        self.timeout_spin.setSingleStep(60)
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addWidget(self.timeout_spin)
        
        settings_layout.addLayout(timeout_layout)
        settings_layout.addStretch()
        settings_group.setLayout(settings_layout)
        
        # 控制按钮
        controls_layout = QHBoxLayout()
        self.download_btn = QPushButton("开始下载")
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        controls_layout.addStretch()
        controls_layout.addWidget(self.download_btn)
        
        # 日志输出
        log_group = QGroupBox("下载日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        
        # 将所有组件添加到下载页面
        download_layout.addWidget(settings_group)
        download_layout.addLayout(controls_layout)
        download_layout.addWidget(log_group)
        
        tab_widget.addTab(download_widget, "下载管理")
        
        # 关于页面
        about_widget = QWidget()
        about_layout = QVBoxLayout(about_widget)
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setHtml("""
        <h2>Canvas下载助手</h2>
        <p>版本: 0.1.0</p>
        <p>一个简单的工具，用于批量同步和下载Canvas学习管理系统中的课程文件。</p>
        
        <h3>使用说明</h3>
        <ol>
            <li>在"配置课程"选项卡中填写Canvas API令牌和课程信息</li>
            <li>选择要下载的文件类型和排除的文件类型</li>
            <li>保存配置以便将来使用</li>
            <li>切换到"下载管理"选项卡开始下载</li>
        </ol>
        
        <h3>获取Canvas API令牌</h3>
        <ol>
            <li>登录您的Canvas账户</li>
            <li>进入"账户" > "设置"</li>
            <li>滚动到底部找到"批准的集成"部分</li>
            <li>点击"新建访问令牌"</li>
            <li>提供一个描述并生成令牌</li>
        </ol>
        
        <h3>开源许可</h3>
        <p>本软件采用MIT许可证</p>
        <p>项目地址: <a href="https://github.com/yourusername/canvas-downloader">https://github.com/yourusername/canvas-downloader</a></p>
        """)
        about_layout.addWidget(about_text)
        tab_widget.addTab(about_widget, "关于")
        
        main_layout.addWidget(tab_widget)
        
        # 设置主窗口
        self.setLayout(main_layout)
        
    def start_download(self):
        """开始下载过程"""
        if not self.config_editor.validate_inputs():
            return
            
        # 获取当前配置
        config = self.config_editor.get_config()
        
        # 创建临时配置文件
        try:
            import tempfile
            
            # 如果已存在临时文件，删除它
            if self.temp_config_file and os.path.exists(self.temp_config_file):
                try:
                    os.remove(self.temp_config_file)
                except:
                    pass
                    
            # 创建新的临时文件
            fd, self.temp_config_file = tempfile.mkstemp(suffix='.json')
            os.close(fd)
            
            with open(self.temp_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
            # 清空日志
            self.log_text.clear()
            self.log_text.append(f"使用配置文件: {self.temp_config_file}")
            self.log_text.append(f"Canvas网址: {config['canvasURL']}")
            
            # 显示所有课程ID
            if 'courseIDs' in config and config['courseIDs']:
                self.log_text.append(f"课程ID: {', '.join(map(str, config['courseIDs']))}")
                self.log_text.append(f"待下载课程数量: {len(config['courseIDs'])}")
            
            self.log_text.append(f"下载目录: {config['downloadDir']}")
            if 'includes' in config:
                self.log_text.append(f"包含文件类型: {', '.join(config['includes'])}")
            if 'excludes' in config:
                self.log_text.append(f"排除文件类型: {', '.join(config['excludes'])}")
            self.log_text.append("正在准备下载...")
            
            # 创建并启动下载线程
            thread = DownloadThread(self.temp_config_file, self.timeout_spin.value())
            thread.progress_signal.connect(self.update_log)
            thread.finished_signal.connect(self.download_finished)
            
            # 禁用下载按钮，避免重复点击
            self.download_btn.setEnabled(False)
            self.download_btn.setText("下载中...")
            
            # 保存并启动线程
            self.download_threads.append(thread)
            thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动下载失败: {str(e)}")
            self.download_btn.setEnabled(True)
            self.download_btn.setText("开始下载")
            
    def update_log(self, message):
        """更新日志输出"""
        self.log_text.append(message)
        # 滚动到底部
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        
    def download_finished(self, success, message):
        """下载完成的处理"""
        if success:
            QMessageBox.information(self, "完成", "Canvas文件下载完成!")
        else:
            QMessageBox.warning(self, "警告", f"下载未完全成功: {message}")
            
        # 清理临时文件
        if self.temp_config_file and os.path.exists(self.temp_config_file):
            try:
                os.remove(self.temp_config_file)
                self.temp_config_file = None
            except:
                pass
                
        # 重新启用下载按钮
        self.download_btn.setEnabled(True)
        self.download_btn.setText("开始下载")
        
    def closeEvent(self, event):
        """关闭时清理"""
        # 停止所有线程
        for thread in self.download_threads:
            if thread.isRunning():
                thread.terminate()
                thread.wait()
                
        # 删除临时文件
        if self.temp_config_file and os.path.exists(self.temp_config_file):
            try:
                os.remove(self.temp_config_file)
            except:
                pass
                
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用Fusion风格，外观更现代
    
    # 设置应用程序图标和名称
    app.setApplicationName("Canvas下载助手")
    
    # 创建并显示主窗口
    window = CanvasDownloaderGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 