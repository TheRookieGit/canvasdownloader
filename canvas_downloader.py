#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
import subprocess
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("canvas-downloader")

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="Canvas课程文件下载工具")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-p", "--config", help="指定单个配置文件路径")
    group.add_argument("-d", "--dir", help="指定配置文件目录路径")
    parser.add_argument("-t", "--timeout", type=int, default=300, help="设置每个课程下载的超时时间(秒)")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细输出")
    return parser.parse_args()

def get_config_files(args):
    """获取所有配置文件的路径"""
    config_files = []
    
    if args.config:
        # 单个配置文件模式
        if not os.path.isfile(args.config):
            logger.error(f"配置文件不存在: {args.config}")
            sys.exit(1)
        config_files.append(args.config)
    else:
        # 目录模式
        config_dir = args.dir
        if not os.path.isdir(config_dir):
            logger.error(f"配置目录不存在: {config_dir}")
            sys.exit(1)
            
        # 收集所有json文件
        for file in os.listdir(config_dir):
            if file.endswith('.json'):
                config_files.append(os.path.join(config_dir, file))
                
        if not config_files:
            logger.error(f"在目录 {config_dir} 中没有找到任何json配置文件")
            sys.exit(1)
    
    return config_files

def validate_config(config_file):
    """验证配置文件内容是否有效"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 检查必要的字段
        required_fields = ['token', 'base_url', 'course_id']
        for field in required_fields:
            if field not in config:
                logger.error(f"配置文件 {config_file} 缺少必要字段: {field}")
                return False
        
        return True
    except json.JSONDecodeError:
        logger.error(f"配置文件格式错误: {config_file}")
        return False
    except Exception as e:
        logger.error(f"验证配置文件时出错: {e}")
        return False

def download_course(config_file, timeout):
    """使用canvassyncer下载课程文件"""
    logger.info(f"正在处理配置文件: {config_file}")
    
    # 确保配置有效
    if not validate_config(config_file):
        return False
    
    # 查找canvassyncer可执行文件路径
    canvassyncer_path = "canvassyncer"  # 默认从PATH中查找
    
    # 构建命令
    command = [canvassyncer_path, "-p", config_file]
    logger.info(f"执行命令: {' '.join(command)}")
    
    try:
        # 执行命令
        result = subprocess.run(
            command, 
            text=True, 
            timeout=timeout,
            check=True,
            capture_output=True
        )
        logger.info(f"命令成功完成，返回码: {result.returncode}")
        if result.stdout:
            logger.debug(f"输出: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"命令执行失败，返回码 {e.returncode}: {e}")
        if e.stdout:
            logger.debug(f"标准输出: {e.stdout}")
        if e.stderr:
            logger.debug(f"错误输出: {e.stderr}")
    except subprocess.TimeoutExpired:
        logger.error(f"命令超时 (>{timeout}秒)")
    except FileNotFoundError:
        logger.error(f"找不到命令: {canvassyncer_path}")
        logger.info("请确保已安装canvassyncer，可以使用 'pip install canvassyncer' 安装")
    except Exception as e:
        logger.error(f"执行命令时发生错误: {e}")
    
    return False

def main():
    """主函数"""
    args = parse_args()
    
    # 设置日志级别
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info("Canvas文件下载器启动")
    
    # 获取所有配置文件
    config_files = get_config_files(args)
    logger.info(f"找到 {len(config_files)} 个配置文件")
    
    # 处理每个配置文件
    success_count = 0
    for config_file in config_files:
        if download_course(config_file, args.timeout):
            success_count += 1
    
    # 汇总结果
    logger.info(f"处理完成: {success_count}/{len(config_files)} 个课程成功同步")
    return 0 if success_count == len(config_files) else 1

if __name__ == "__main__":
    sys.exit(main()) 