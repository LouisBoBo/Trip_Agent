from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import uuid
import os

# 禁用自动加载.env文件，避免权限错误
os.environ['FLASK_SKIP_DOTENV'] = '1'

# 尝试导入多智能体系统
print("正在初始化多智能体系统...")
MULTI_AGENT_AVAILABLE = False
graph = None
execute_graph = None

try:
    print("  导入 graph.graph_chat 模块...")
    from graph.graph_chat import graph, execute_graph
    MULTI_AGENT_AVAILABLE = True
    print("✓ 多智能体系统已成功加载")
except PermissionError as e:
    print(f"⚠ 权限错误: 无法导入多智能体系统 ({e})")
    print("提示: 这可能是由于macOS安全限制。在实际运行环境中应该可以正常工作。")
    print("将使用简化版本")
except Exception as e:
    print(f"⚠ 警告: 无法导入多智能体系统: {type(e).__name__}: {e}")
    print("将使用简化版本")

app = Flask(__name__)
CORS(app)

# 存储每个会话的配置
sessions = {}


def get_session_config(session_id: str):
    """获取或创建会话配置"""
    if session_id not in sessions:
        sessions[session_id] = {
            "configurable": {
                "passenger_id": "3442 587242",
                "thread_id": session_id,
            }
        }
    return sessions[session_id]


@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """处理聊天请求"""
    try:
        data = request.json
        message = data.get('message', '')
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if not message:
            return jsonify({'error': '消息不能为空'}), 400
        
        # 如果多智能体系统可用，使用它
        if MULTI_AGENT_AVAILABLE and execute_graph:
            try:
                # 获取会话配置
                session_config = get_session_config(session_id)
                
                # 执行图并获取回复
                response = execute_graph(message, session_config, verbose=False)
                
                # 如果没有回复，返回默认消息
                if not response:
                    response = "抱歉，没有收到回复，请稍后重试。"
                
                return jsonify({
                    'response': response,
                    'session_id': session_id
                })
            except Exception as e:
                # 如果多智能体系统出错，返回错误信息
                return jsonify({
                    'response': f'多智能体系统处理出错: {str(e)}\n\n请检查系统配置或联系管理员。',
                    'session_id': session_id
                })
        else:
            # 使用简化版本
            response = f"收到您的消息：{message}\n\n多智能体系统未正确加载，请检查配置。"
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
    get_session_config(session_id)
    return jsonify({'session_id': session_id})


if __name__ == '__main__':
    import sys
    
    # 尝试使用5001端口，如果被占用则使用5002
    import socket
    port = 5001
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    if result == 0:
        print(f"⚠ 端口 {port} 被占用，尝试使用 5002")
        port = 5002
    
    print("\n" + "=" * 50)
    print("Flask 服务器启动中...")
    print("=" * 50)
    if MULTI_AGENT_AVAILABLE:
        print("✓ 多智能体系统已加载")
    else:
        print("⚠ 多智能体系统未加载，使用简化模式")
    print(f"访问地址: http://localhost:{port}")
    print("按 Ctrl+C 停止服务器")
    print("=" * 50 + "\n")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=port, use_reloader=False)
    except KeyboardInterrupt:
        print("\n服务器已停止")
        sys.exit(0)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n错误: 端口 {port} 已被占用")
            print("请先停止占用端口的进程，或修改端口号")
        else:
            print(f"\n错误: {e}")
        sys.exit(1)
