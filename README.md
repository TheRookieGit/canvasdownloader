# Canvas下载助手 (Canvas Downloader)

一个简单的工具，用于批量同步和下载Canvas学习管理系统中的课程文件。

## 功能特点

- 支持多课程配置
- 自动同步Canvas课程文件
- 可配置下载路径和过滤器
- 支持超时和错误处理

## 安装方法

### 方法1：使用pip安装

```bash
pip install canvas-downloader
```

### 方法2：从源代码安装

1. 克隆此仓库
```bash
git clone https://github.com/yourusername/canvas-downloader.git
cd canvas-downloader
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 安装包
```bash
pip install -e .
```

## 使用方法

1. 创建配置文件 (JSON格式)：

```json
{
  "token": "你的Canvas API令牌",
  "base_url": "https://your-institution.instructure.com",
  "course_id": "课程ID",
  "download_path": "下载路径",
  "includes": ["可选，文件类型过滤器"],
  "excludes": ["可选，排除文件类型"]
}
```

2. 运行程序：

```bash
# 单个配置文件
canvas-downloader -p 配置文件路径.json

# 或使用配置目录
canvas-downloader -d 配置文件目录
```

## 配置文件说明

每个课程需要一个独立的JSON配置文件，包含以下字段：

- `token`: Canvas API访问令牌
- `base_url`: Canvas实例的基础URL
- `course_id`: 要下载的课程ID
- `download_path`: 文件保存位置
- `includes`: 可选，指定要包含的文件类型
- `excludes`: 可选，指定要排除的文件类型

## 获取Canvas API令牌

1. 登录您的Canvas账户
2. 进入"账户" > "设置"
3. 滚动到底部找到"批准的集成"部分
4. 点击"新建访问令牌"
5. 提供一个描述并生成令牌

## 许可证

MIT 