# 多智能体对话界面使用说明

## 功能特性

- 🎨 参照DeepSeek风格的现代化对话界面
- 💬 实时对话交互
- 🤖 对接多智能体系统（航班、酒店、租车、旅行推荐、网络搜索）
- 🔄 会话管理，支持多用户对话
- 📱 响应式设计，支持移动端

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动服务

```bash
python app.py
```

服务将在 `http://localhost:5000` 启动。

## 使用说明

1. 打开浏览器访问 `http://localhost:5000`
2. 在输入框中输入您的问题
3. 点击发送按钮或按 Enter 键发送消息
4. AI助手会根据您的问题自动选择合适的智能体进行回答

## 界面功能

- **输入框**：输入您的问题
- **深度思考**：启用深度思考模式（功能扩展中）
- **联网搜索**：启用联网搜索模式（功能扩展中）
- **附件**：上传附件（功能扩展中）
- **发送**：发送消息

## API接口

### POST /api/chat
发送聊天消息

请求体：
```json
{
  "message": "用户消息",
  "session_id": "会话ID（可选）"
}
```

响应：
```json
{
  "response": "AI回复",
  "session_id": "会话ID"
}
```

### POST /api/session/new
创建新会话

响应：
```json
{
  "session_id": "新会话ID"
}
```

## 技术栈

- 后端：Flask + LangGraph
- 前端：HTML + CSS + JavaScript
- 多智能体：LangGraph Supervisor Pattern

## 注意事项

- 确保数据库文件 `travel_new.sqlite` 存在
- 确保环境变量配置正确（如API密钥等）
- 首次运行可能需要初始化数据库
