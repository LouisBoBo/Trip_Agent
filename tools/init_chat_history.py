"""
初始化聊天历史记录表
"""
import sqlite3
from pathlib import Path

# 获取项目根目录
basic_dir = Path(__file__).resolve().parent.parent
local_file = f"{basic_dir}/travel_new.sqlite"


def init_chat_history_table():
    """创建聊天历史记录表"""
    conn = sqlite3.connect(local_file)
    cursor = conn.cursor()
    
    # 创建聊天历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            message_type TEXT NOT NULL,
            message_content TEXT NOT NULL,
            is_voice INTEGER DEFAULT 0,
            voice_duration INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建索引
    try:
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON chat_history(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON chat_history(created_at)')
    except sqlite3.OperationalError:
        pass  # 索引可能已存在
    
    conn.commit()
    conn.close()
    print("✓ 聊天历史表已创建")


if __name__ == '__main__':
    init_chat_history_table()
