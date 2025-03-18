#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Canvas下载助手Windows版启动脚本
此脚本用于在Windows系统上运行Canvas下载助手
"""

import os
import sys
import subprocess
from pathlib import Path

# 直接导入原始界面模块
try:
    from canvas_downloader_gui import CanvasDownloaderGUI, QApplication, find_canvassyncer_path
except ImportError as e:
    print(f"无法导入必要的模块: {str(e)}")
    print("请确保所有文件完整，并已安装必要的依赖包（PyQt5, canvassyncer）")
    sys.exit(1)

# 重写canvassyncer路径查找函数以使用python代替python3
def windows_find_canvassyncer_path():
    """查找canvassyncer可执行文件路径 - Windows版本"""
    # 在Windows上使用python而不是python3
    return "python -m canvassyncer"

# 重写下载线程中的命令构建
def windows_run_canvassyncer(canvassyncer_path, temp_course_config):
    """构建Windows下的canvassyncer命令"""
    if canvassyncer_path == "python3 -m canvassyncer" or canvassyncer_path == "python -m canvassyncer":
        # 对于Windows，使用python而不是python3
        return [sys.executable, "-m", "canvassyncer", "-p", temp_course_config]
    else:
        return [canvassyncer_path, "-p", temp_course_config]

# 修补原始模块以适应Windows
import canvas_downloader_gui

# 替换原始的find_canvassyncer_path函数
canvas_downloader_gui.find_canvassyncer_path = windows_find_canvassyncer_path

# 修改DownloadThread类的run方法中构建命令的部分
original_run = canvas_downloader_gui.DownloadThread.run

def patched_run(self):
    """修补后的run方法"""
    self.progress_signal.emit(f"开始下载: {os.path.basename(self.config_file)}")
    
    # 验证配置文件
    try:
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = canvas_downloader_gui.json.load(f)
            
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
        canvassyncer_path = windows_find_canvassyncer_path()
        
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
                canvas_downloader_gui.json.dump(single_course_config, f, indent=2, ensure_ascii=False)
            
            # 构建命令 - Windows适配
            command = windows_run_canvassyncer(canvassyncer_path, temp_course_config)
                
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
            
            # 以下部分保持原样
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
        # 提示用户安装canvassyncer
        self.progress_signal.emit("错误: 找不到canvassyncer命令")
        self.progress_signal.emit("请手动运行: pip install canvassyncer")
        self.finished_signal.emit(False, "找不到canvassyncer命令")
    except Exception as e:
        self.progress_signal.emit(f"错误: {str(e)}")
        self.finished_signal.emit(False, str(e))

# 应用补丁
canvas_downloader_gui.DownloadThread.run = patched_run

def main():
    """Windows版本主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用Fusion风格，外观更现代
    
    # 设置应用程序图标和名称
    app.setApplicationName("Canvas下载助手(Windows版)")
    
    # 创建并显示主窗口
    window = CanvasDownloaderGUI()
    window.setWindowTitle("Canvas下载助手 - Windows版")
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 