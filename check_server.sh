#!/bin/bash
# 服务器诊断脚本

echo "=========================================="
echo "服务器诊断"
echo "=========================================="

# 检查端口占用
echo "1. 检查端口5001占用情况..."
if lsof -ti:5001 > /dev/null 2>&1; then
    echo "   ⚠ 端口5001被占用，进程ID:"
    lsof -ti:5001 | while read pid; do
        echo "      PID: $pid"
        ps -p $pid -o command= 2>/dev/null || echo "      无法获取进程信息"
    done
    echo ""
    echo "   停止占用端口的进程？(y/n)"
    read -r answer
    if [ "$answer" = "y" ]; then
        lsof -ti:5001 | xargs kill -9 2>/dev/null
        echo "   ✓ 已停止占用端口的进程"
    fi
else
    echo "   ✓ 端口5001空闲"
fi

echo ""
echo "2. 检查Flask安装..."
source .trip_env/bin/activate
if python3 -c "import flask" 2>/dev/null; then
    echo "   ✓ Flask 已安装"
else
    echo "   ✗ Flask 未安装"
    echo "   运行: pip install Flask flask-cors"
fi

echo ""
echo "3. 检查模板文件..."
if [ -f "templates/index.html" ]; then
    echo "   ✓ 模板文件存在"
else
    echo "   ✗ 模板文件不存在"
fi

echo ""
echo "=========================================="
echo "诊断完成"
echo "=========================================="
