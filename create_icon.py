#!/usr/bin/env python3
# 此脚本用于创建Windows图标文件
# 需要安装Pillow库: pip install Pillow

from PIL import Image, ImageDraw, ImageFont
import os

try:
    # 创建一个512x512的图像，带透明背景
    img = Image.new('RGBA', (512, 512), color=(0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    
    # 绘制圆形背景
    d.ellipse((50, 50, 462, 462), fill=(0, 120, 212))
    
    # 尝试加载字体，如果找不到，使用默认字体
    try:
        font = ImageFont.truetype("Arial.ttf", 200)
    except IOError:
        font = ImageFont.load_default()
    
    # 添加文本
    d.text((180, 150), "C", fill=(255, 255, 255), font=font)
    
    # 保存为PNG
    png_path = "app_icon.png"
    img.save(png_path)
    print(f"PNG图标已保存为: {png_path}")
    
    # 生成多种尺寸的图标
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icons = []
    
    for size in sizes:
        icon = img.resize(size, Image.LANCZOS)
        icons.append(icon)
    
    # 保存为ICO
    ico_path = "app_icon.ico"
    icons[0].save(ico_path, sizes=[(icon.width, icon.height) for icon in icons], 
                 format="ICO")
    print(f"ICO图标已保存为: {ico_path}")
    
    print("图标创建成功！您可以将app_icon.ico用于Windows打包。")
    
except Exception as e:
    print(f"创建图标时出错: {e}")
    print("请确保已安装Pillow库: pip install Pillow") 