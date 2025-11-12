@echo off
title 哺乳期喂养记录系统

echo 创建虚拟环境...
python -m venv venv

echo 激活虚拟环境...
call venv\Scripts\activate

echo 安装依赖...
pip install -r requirements.txt

echo 设置环境变量...
set FLASK_APP=run.py
set FLASK_ENV=development

echo 启动Flask应用...
flask run --host=0.0.0.0 --port=9001

pause