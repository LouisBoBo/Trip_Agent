from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import uuid

app = Flask(__name__)
CORS(app)

# 存储每个会话的配置
sessions = {}


@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """处理聊天请求 - 简化版本"""
    try:
        data = request.json
        message = data.get('message', '')
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if not message:
            return jsonify({'error': '消息不能为空'}), 400
        
        # 简单的回复（用于测试）
        response = f"收到您的消息：{message}\n\n这是一个测试回复。完整的多智能体功能需要导入graph_chat模块。"
        
        return jsonify({
            'response': response,
            'session_id': session_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/session/new', methods=['POST'])
def new_session():
    """创建新会话"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = {'created_at': str(uuid.uuid4())}
    return jsonify({'session_id': session_id})


if __name__ == '__main__':
    import os
    # 禁用自动加载.env文件，避免权限错误
    os.environ['FLASK_SKIP_DOTENV'] = '1'
    
    # 尝试使用5001端口，避免与AirPlay冲突
    port = 5001
    
    print("=" * 50)
    print("启动简化版服务器（用于测试界面）")
    print(f"访问地址: http://localhost:{port}")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=port, use_reloader=False)
