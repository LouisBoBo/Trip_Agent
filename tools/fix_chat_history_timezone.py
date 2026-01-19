"""
修复聊天历史记录的时区问题
将UTC时间转换为本地时间（+8小时）
"""
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# 获取项目根目录
basic_dir = Path(__file__).resolve().parent.parent
local_file = f"{basic_dir}/travel_new.sqlite"


def fix_timezone():
    """修复时区问题：将UTC时间转换为本地时间（+8小时）"""
    try:
        conn = sqlite3.connect(local_file)
        cursor = conn.cursor()
        
        # 获取所有记录
        cursor.execute('SELECT id, created_at FROM chat_history')
        rows = cursor.fetchall()
        
        print(f'找到 {len(rows)} 条记录')
        
        updated_count = 0
        for row in rows:
            record_id = row[0]
            old_time = row[1]
            
            try:
                # 解析UTC时间
                utc_time = datetime.strptime(old_time, '%Y-%m-%d %H:%M:%S')
                # 转换为本地时间（+8小时）
                local_time = utc_time + timedelta(hours=8)
                new_time = local_time.strftime('%Y-%m-%d %H:%M:%S')
                
                # 更新记录
                cursor.execute('''
                    UPDATE chat_history 
                    SET created_at = ? 
                    WHERE id = ?
                ''', (new_time, record_id))
                
                updated_count += 1
                if updated_count % 10 == 0:
                    print(f'已更新 {updated_count} 条记录...')
            except Exception as e:
                print(f'更新记录 {record_id} 失败: {e}, 时间: {old_time}')
        
        conn.commit()
        conn.close()
        
        print(f'✓ 完成！共更新 {updated_count} 条记录')
        return updated_count
    except Exception as e:
        print(f'修复失败: {e}')
        return 0


if __name__ == '__main__':
    print('开始修复聊天历史记录的时区问题...')
    print('将UTC时间转换为本地时间（+8小时）')
    print('')
    fix_timezone()
