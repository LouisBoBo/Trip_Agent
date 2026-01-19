from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import uuid
import os
import sqlite3
from datetime import datetime
from tools import local_file

# 禁用自动加载.env文件，避免权限错误
os.environ['FLASK_SKIP_DOTENV'] = '1'

# 初始化聊天历史表
try:
    from tools.init_chat_history import init_chat_history_table
    init_chat_history_table()
    print("✓ 聊天历史表已初始化")
except Exception as e:
    print(f"⚠ 初始化聊天历史表失败: {e}")

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

# 添加before_request钩子，优先处理文件上传，避免415错误
@app.before_request
def before_request():
    """在请求处理前检查文件上传，避免415错误"""
    if request.method == 'POST':
        # 如果是multipart/form-data且有文件，跳过后续JSON解析
        content_type = request.content_type or ''
        if 'multipart/form-data' in content_type and request.files:
            # 设置标志，告诉chat函数不要尝试解析JSON
            request._skip_json_check = True

# 存储每个会话的配置
sessions = {}


def save_chat_message(session_id: str, message_type: str, content: str, is_voice: bool = False, voice_duration: int = None):
    """保存聊天消息到数据库"""
    try:
        # 使用本地时间而不是UTC时间
        from datetime import datetime
        local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect(local_file)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO chat_history (session_id, message_type, message_content, is_voice, voice_duration, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, message_type, content, 1 if is_voice else 0, voice_duration, local_time))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[ERROR] 保存聊天消息失败: {e}")


def get_chat_history(session_id: str, limit: int = 100):
    """获取聊天历史记录"""
    try:
        conn = sqlite3.connect(local_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT message_type, message_content, is_voice, voice_duration, created_at
            FROM chat_history
            WHERE session_id = ?
            ORDER BY created_at ASC
            LIMIT ?
        ''', (session_id, limit))
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'type': row[0],
                'content': row[1],
                'is_voice': bool(row[2]),
                'voice_duration': row[3],
                'created_at': row[4]
            })
        return history
    except Exception as e:
        print(f"[ERROR] 获取聊天历史失败: {e}")
        return []


def get_all_sessions(limit: int = 50):
    """获取所有会话列表"""
    try:
        conn = sqlite3.connect(local_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT session_id, 
                   MIN(created_at) as first_message_time,
                   MAX(created_at) as last_message_time,
                   COUNT(*) as message_count
            FROM chat_history
            GROUP BY session_id
            ORDER BY last_message_time DESC
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        
        # 获取每个会话的第一条用户消息作为预览
        sessions = []
        for row in rows:
            session_id = row[0]
            first_time = row[1]
            last_time = row[2]
            message_count = row[3]
            
            # 获取第一条用户消息作为预览
            cursor.execute('''
                SELECT message_content
                FROM chat_history
                WHERE session_id = ? AND message_type = 'user'
                ORDER BY created_at ASC
                LIMIT 1
            ''', (session_id,))
            preview_row = cursor.fetchone()
            preview = preview_row[0] if preview_row else '新对话'
            
            sessions.append({
                'session_id': session_id,
                'preview': preview[:50] + ('...' if len(preview) > 50 else ''),
                'first_time': first_time,
                'last_time': last_time,
                'message_count': message_count
            })
        
        conn.close()
        return sessions
    except Exception as e:
        print(f"[ERROR] 获取会话列表失败: {e}")
        return []


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
    # ===== 第一步：检查是否是语音识别请求（上传音频文件）=====
    # 使用try-except包裹，避免任何JSON解析错误
    try:
        # 优先检查文件上传（更可靠的方式）
        # 无论Content-Type是什么，只要有files就尝试处理
        if request.files:
            print(f"[DEBUG] 检测到文件上传，Content-Type: {request.content_type}")
            print(f"[DEBUG] 文件字段: {list(request.files.keys())}")
            if 'audio' in request.files:
                print("[DEBUG] 找到audio字段，调用语音识别")
                return handle_speech_recognition()
            else:
                # 如果有文件但不是audio字段，返回错误
                print(f"[DEBUG] 文件字段列表: {list(request.files.keys())}")
                return jsonify({'error': f'请求包含文件但未找到audio字段，实际字段: {list(request.files.keys())}'}), 400
        
        # 检查Content-Type，如果是multipart/form-data但没有files，可能是错误
        content_type = request.content_type or ''
        if 'multipart/form-data' in content_type:
            print(f"[DEBUG] Content-Type是multipart/form-data但未找到files")
            return jsonify({'error': '请求类型是multipart/form-data但未找到文件数据'}), 400
        
        # ===== 第二步：处理文本消息（JSON格式）=====
        # 只有Content-Type是application/json时才解析JSON
        if 'application/json' not in content_type:
            return jsonify({'error': '请求必须是JSON格式或包含音频文件'}), 400
        
        # 安全地获取JSON数据
        data = request.get_json(silent=True, force=False)
        if not data:
            data = {}
        
        if not isinstance(data, dict):
            return jsonify({'error': '请求必须是JSON格式或包含音频文件'}), 400
    except Exception as e:
        # 捕获所有异常，包括415错误
        error_msg = str(e)
        if '415' in error_msg or 'Unsupported Media Type' in error_msg:
            # 如果是415错误，可能是文件上传，再次尝试
            try:
                if request.files and 'audio' in request.files:
                    return handle_speech_recognition()
            except:
                pass
        return jsonify({'error': error_msg}), 500
    
    # ===== 第三步：处理文本消息内容 =====
    try:
        message = data.get('message', '')
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        print(f"[DEBUG chat] 收到消息: {message[:50]}...")
        print(f"[DEBUG chat] 会话ID: {session_id}")
        
        if not message:
            return jsonify({'error': '消息不能为空'}), 400
        
        # 保存用户消息到历史记录
        save_chat_message(session_id, 'user', message, is_voice=False)
        
        # 如果多智能体系统可用，使用它
        if MULTI_AGENT_AVAILABLE and execute_graph:
            try:
                # 获取会话配置
                session_config = get_session_config(session_id)
                print(f"[DEBUG chat] 会话配置: {session_config}")
                
                # 执行图并获取回复
                response = execute_graph(message, session_config, verbose=False)
                print(f"[DEBUG chat] 执行图完成，回复长度: {len(response) if response else 0}")
                
                # 如果没有回复，返回默认消息
                if not response:
                    response = "抱歉，没有收到回复，请稍后重试。"
                
                # 保存AI回复到历史记录
                save_chat_message(session_id, 'ai', response, is_voice=False)
                
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
            # 保存AI回复到历史记录
            save_chat_message(session_id, 'ai', response, is_voice=False)
            return jsonify({
                'response': response,
                'session_id': session_id
            })
    except Exception as e:
        # 避免在异常处理中触发JSON解析
        error_msg = str(e)
        # 如果是415错误，说明可能是文件上传但检测失败
        if '415' in error_msg or 'Unsupported Media Type' in error_msg:
            # 再次尝试检查文件上传
            if request.files and 'audio' in request.files:
                return handle_speech_recognition()
        return jsonify({'error': error_msg}), 500


@app.route('/api/session/new', methods=['POST'])
def new_session():
    """创建新会话"""
    session_id = str(uuid.uuid4())
    get_session_config(session_id)
    return jsonify({'session_id': session_id})


@app.route('/api/chat/history', methods=['GET'])
def get_history():
    """获取聊天历史记录"""
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'error': '缺少session_id参数'}), 400

    limit = int(request.args.get('limit', 100))
    history = get_chat_history(session_id, limit)
    return jsonify({'history': history})


@app.route('/api/session/delete', methods=['POST'])
def delete_session():
    """删除会话及其所有消息"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({'error': '缺少session_id参数'}), 400
        
        conn = sqlite3.connect(local_file)
        cursor = conn.cursor()
        
        # 删除该会话的所有消息
        cursor.execute('DELETE FROM chat_history WHERE session_id = ?', (session_id,))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        # 同时从内存中的sessions字典删除
        if session_id in sessions:
            del sessions[session_id]
        
        print(f"[INFO] 删除会话 {session_id}，共删除 {deleted_count} 条消息")
        return jsonify({'success': True, 'deleted_count': deleted_count})
    except Exception as e:
        print(f"[ERROR] 删除会话失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/list', methods=['GET'])
def list_sessions():
    """获取所有会话列表"""
    limit = int(request.args.get('limit', 50))
    sessions = get_all_sessions(limit)
    return jsonify({'sessions': sessions})


def handle_speech_recognition():
    """处理语音识别请求"""
    try:
        print("[DEBUG handle_speech_recognition] 开始处理语音识别")
        print(f"[DEBUG handle_speech_recognition] request.files: {request.files}")
        print(f"[DEBUG handle_speech_recognition] request.files.keys(): {list(request.files.keys()) if request.files else 'None'}")
        
        if not request.files:
            print("[DEBUG handle_speech_recognition] request.files为空")
            return jsonify({'success': False, 'error': '请求中未找到文件数据'}), 400
        
        if 'audio' not in request.files:
            print(f"[DEBUG handle_speech_recognition] 未找到audio字段，可用字段: {list(request.files.keys())}")
            return jsonify({'success': False, 'error': f'请上传音频文件（audio字段），实际字段: {list(request.files.keys())}'}), 400
        
        audio_file = request.files['audio']
        print(f"[DEBUG handle_speech_recognition] 音频文件名: {audio_file.filename}")
        print(f"[DEBUG handle_speech_recognition] 音频文件Content-Type: {audio_file.content_type}")
        
        audio_data = audio_file.read()
        print(f"[DEBUG handle_speech_recognition] 音频数据大小: {len(audio_data)} 字节")
        
        if len(audio_data) == 0:
            print("[DEBUG handle_speech_recognition] 音频文件为空")
            return jsonify({'success': False, 'error': '音频文件为空'}), 400
        
        # 检查文件大小（≤ 25MB）
        max_size = 25 * 1024 * 1024  # 25MB
        if len(audio_data) > max_size:
            return jsonify({
                'success': False, 
                'error': f'音频文件过大 ({len(audio_data)} 字节 > {max_size} 字节)，智谱AI限制为25MB'
            }), 400
        
        # 检测音频文件格式（通过文件头）
        # webm文件头: 1A 45 DF A3
        # wav文件头: 52 49 46 46 (RIFF)
        # mp3文件头通常以FF FB或ID3开始
        file_header = audio_data[:4] if len(audio_data) >= 4 else b''
        detected_format = 'webm'
        
        if file_header[:3] == b'\x1a\x45\xdf':
            detected_format = 'webm'
        elif file_header == b'RIFF':
            detected_format = 'wav'
        elif file_header[:2] == b'\xff\xfb' or file_header[:3] == b'ID3':
            detected_format = 'mp3'
        
        # 从文件名获取扩展名
        ext = audio_file.filename.rsplit('.', 1)[1].lower() if '.' in audio_file.filename else detected_format
        
        print(f"[DEBUG handle_speech_recognition] 文件名扩展名: {ext}")
        print(f"[DEBUG handle_speech_recognition] 检测到的格式: {detected_format}")
        print(f"[DEBUG handle_speech_recognition] 文件头: {file_header.hex()}")
        
        # 重要：智谱AI只支持 wav 和 mp3，不支持 webm
        # 如果格式是webm，返回明确错误提示
        if ext == 'webm' or detected_format == 'webm':
            return jsonify({
                'success': False,
                'error': '音频格式不支持。智谱AI只支持 wav 和 mp3 格式，当前上传的是 webm 格式。请在前端使用 wav 或 mp3 格式录音。'
            }), 400
        
        # 只使用检测到的格式（wav或mp3）
        final_format = detected_format if detected_format in ['wav', 'mp3'] else ext
        
        from tools.speech_tools import speech_to_text
        result = speech_to_text(audio_data, final_format)
        print(f"[DEBUG handle_speech_recognition] 识别结果: {result}")
        
        if result['success']:
            return jsonify({'success': True, 'text': result['text']})
        else:
            return jsonify({'success': False, 'error': result['error']}), 500
    except Exception as e:
        print(f"[DEBUG handle_speech_recognition] 异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'语音识别处理失败: {str(e)}'}), 500


@app.route('/api/speech/recognize', methods=['POST', 'GET'])
def speech_recognize():
    """语音识别接口 - 直接转发到handle_speech_recognition"""
    if request.method == 'GET':
        return jsonify({'message': '语音识别API正常', 'status': 'ok'})
    
    # 增加调试日志
    print(f"[DEBUG /api/speech/recognize] Content-Type: {request.content_type}")
    print(f"[DEBUG /api/speech/recognize] request.files: {request.files}")
    print(f"[DEBUG /api/speech/recognize] request.files.keys(): {list(request.files.keys()) if request.files else 'None'}")
    
    # 如果request.files为空，尝试检查是否是Content-Type问题
    if not request.files:
        print("[DEBUG /api/speech/recognize] request.files为空，可能Content-Type不正确")
        # 返回详细错误，让前端fallback到/api/chat
        return jsonify({
            'success': False, 
            'error': '请求中未找到文件数据，请检查Content-Type是否正确',
            'content_type': request.content_type,
            'fallback': True
        }), 400
    
    return handle_speech_recognition()


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
    
    # 打印已注册的路由
    print("\n已注册的路由:")
    for rule in app.url_map.iter_rules():
        if 'speech' in rule.rule or 'api' in rule.rule:
            print(f"  {rule.rule} -> {rule.endpoint} (methods: {list(rule.methods)})")
    
    print(f"\n访问地址: http://localhost:{port}")
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
