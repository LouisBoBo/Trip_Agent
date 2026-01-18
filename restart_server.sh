#!/bin/bash
# 重启Flask服务器脚本

echo "正在停止所有相关进程..."

# 停止所有Python Flask进程
pkill -9 -f "python.*app.py" 2>/dev/null
pkill -9 -f "flask" 2>/dev/null
lsof -ti:5001,5002 | xargs kill -9 2>/dev/null

echo "等待3秒..."
sleep 3

echo "检查端口是否释放..."
if lsof -ti:5001,5002 > /dev/null 2>&1; then
    echo "警告: 仍有进程占用端口，请手动检查"
    lsof -i:5001,5002
else
    echo "端口已释放"
fi

echo ""
echo "启动服务器..."
cd "$(dirname "$0")"
python3 app.py
