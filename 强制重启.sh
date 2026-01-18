#!/bin/bash
echo "正在强制停止所有相关进程..."

# 强制停止进程
kill -9 11183 20420 2>/dev/null
pkill -9 -f "python.*app.py" 2>/dev/null
pkill -9 -f "flask" 2>/dev/null

# 停止占用端口的进程
lsof -ti:5001 | xargs kill -9 2>/dev/null
lsof -ti:5002 | xargs kill -9 2>/dev/null

echo "等待3秒..."
sleep 3

echo "启动新服务器..."
cd "$(dirname "$0")"
python3 app.py
