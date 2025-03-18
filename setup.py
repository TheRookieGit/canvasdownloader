from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="canvas-downloader",
    version="0.1.0",
    author="Canvas Downloader Team",
    author_email="your.email@example.com",
    description="一个用于批量下载Canvas课程文件的工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/canvas-downloader",
    packages=find_packages(),
    py_modules=["canvas_downloader"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "canvassyncer>=0.1.0",
    ],
    entry_points={
        "console_scripts": [
            "canvas-downloader=canvas_downloader:main",
        ],
    },
) 