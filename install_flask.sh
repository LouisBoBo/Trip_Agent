#!/bin/bash
# Flask 安装脚本

echo "=========================================="
echo "安装 Flask 和 flask-cors"
echo "=========================================="

# 激活虚拟环境
source /Users/hebo/PycharmProjects/pythonProject_new_trip/.trip_env/bin/activate

# 检查虚拟环境是否激活
if [ -z "$VIRTUAL_ENV" ]; then
    echo "错误: 虚拟环境未激活"
    exit 1
fi

echo "虚拟环境: $VIRTUAL_ENV"
echo "Python: $(which python3)"
echo ""

# 安装 Flask 和 flask-cors
echo "正在安装 Flask 和 flask-cors..."
pip install Flask flask-cors

# 验证安装
echo ""
echo "验证安装..."
python3 -c "import flask; print('✓ Flask 版本:', flask.__version__)"
python3 -c "import flask_cors; print('✓ flask-cors 已安装')"

echo ""
echo "=========================================="
echo "安装完成！"
echo "=========================================="
