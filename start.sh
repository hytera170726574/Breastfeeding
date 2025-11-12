#!/bin/bash

# 启动Flask应用

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 检查依赖
if [ ! -f "requirements.txt" ]; then
    echo "未找到 requirements.txt 文件"
    exit 1
fi

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 设置环境变量
export FLASK_APP=run.py
export FLASK_ENV=development

# 启动应用
echo "启动Flask应用..."
flask run --host=0.0.0.0 --port=9001