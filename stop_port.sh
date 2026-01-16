#!/bin/bash
# 停止占用端口的进程

PORT=5001

echo "查找占用端口 $PORT 的进程..."
PIDS=$(lsof -ti:$PORT 2>/dev/null)

if [ -z "$PIDS" ]; then
    echo "端口 $PORT 没有被占用"
    exit 0
fi

echo "找到以下进程占用端口 $PORT:"
for PID in $PIDS; do
    echo "  PID: $PID"
    ps -p $PID -o command= 2>/dev/null || echo "    (无法获取进程信息)"
done

echo ""
echo "是否停止这些进程? (y/n)"
read -r answer

if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
    for PID in $PIDS; do
        kill -9 $PID 2>/dev/null
        echo "已停止进程 $PID"
    done
    echo "✓ 所有占用端口的进程已停止"
else
    echo "取消操作"
fi
