# Flask 安装指南

## 问题
运行 `python3 app.py` 时出现错误：
```
ModuleNotFoundError: No module named 'flask'
```

## 解决方案

### 方法1：使用安装脚本（推荐）

在终端中运行：
```bash
cd /Users/hebo/PycharmProjects/pythonProject_new_trip
./install_flask.sh
```

### 方法2：手动安装

1. **激活虚拟环境**：
```bash
source /Users/hebo/PycharmProjects/pythonProject_new_trip/.trip_env/bin/activate
```

2. **确认虚拟环境已激活**（应该看到 `(.trip_env)` 前缀）

3. **安装 Flask 和 flask-cors**：
```bash
pip install Flask flask-cors
```

4. **验证安装**：
```bash
python3 -c "import flask; print('Flask 版本:', flask.__version__)"
```

### 方法3：安装所有依赖

如果需要安装所有依赖（包括多智能体系统需要的包）：
```bash
source /Users/hebo/PycharmProjects/pythonProject_new_trip/.trip_env/bin/activate
pip install -r requirements.txt
```

## 安装完成后

运行服务器：
```bash
python3 app.py
```

服务器将在 `http://localhost:5001` 启动。

## 常见问题

### 如果遇到权限错误

尝试使用 `--user` 标志：
```bash
pip install --user Flask flask-cors
```

### 如果 pip 命令不可用

确保虚拟环境已正确激活，或使用：
```bash
python3 -m pip install Flask flask-cors
```
