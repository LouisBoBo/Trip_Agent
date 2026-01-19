"""
智能修复UTC时间记录
只修复那些明显是UTC时间的记录（时间在12-15点之间，而其他记录在20点之后）
"""
import sqlite3
from datetime import datetime, timedelta
from . import local_file


def fix_utc_records():
    """智能修复UTC时间记录：只修复明显是UTC的记录"""
    try:
        conn = sqlite3.connect(local_file)
        cursor = conn.cursor()
        
        # 获取所有记录，按日期分组
        cursor.execute('''
            SELECT id, created_at, session_id
            FROM chat_history
            ORDER BY created_at
        ''')
        rows = cursor.fetchall()
        
        print(f'找到 {len(rows)} 条记录')
        
        # 按日期分组，找出每个日期的时间范围
        date_groups = {}
        for row in rows:
            record_id, created_at, session_id = row
            date_part = created_at.split(' ')[0]  # YYYY-MM-DD
            time_part = created_at.split(' ')[1] if ' ' in created_at else ''
            
            if date_part not in date_groups:
                date_groups[date_part] = []
            date_groups[date_part].append((record_id, created_at, session_id, time_part))
        
        updated_count = 0
        for date_str, records in date_groups.items():
            # 找出这个日期的最大小时数
            max_hour = 0
            for _, _, _, time_part in records:
                try:
                    hour = int(time_part.split(':')[0])
                    max_hour = max(max_hour, hour)
                except:
                    pass
            
            # 如果最大小时数在20-23之间，说明有本地时间的记录
            # 那么时间在12-15之间的记录可能是UTC时间
            if max_hour >= 20:
                for record_id, created_at, session_id, time_part in records:
                    try:
                        hour = int(time_part.split(':')[0])
                        # 如果时间在12-15之间，且同一天有其他记录在20点之后，则可能是UTC
                        if 12 <= hour <= 15:
                            # 解析UTC时间
                            utc_time = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                            # 转换为本地时间（+8小时）
                            local_time = utc_time + timedelta(hours=8)
                            new_time = local_time.strftime('%Y-%m-%d %H:%M:%S')
                            
                            print(f'修复记录 {record_id}: {created_at} -> {new_time}')
                            
                            # 更新记录
                            cursor.execute('''
                                UPDATE chat_history 
                                SET created_at = ? 
                                WHERE id = ?
                            ''', (new_time, record_id))
                            
                            updated_count += 1
                    except Exception as e:
                        print(f'处理记录 {record_id} 失败: {e}')
        
        conn.commit()
        conn.close()
        
        print(f'✓ 完成！共更新 {updated_count} 条记录')
        return updated_count
    except Exception as e:
        print(f'修复失败: {e}')
        import traceback
        traceback.print_exc()
        return 0


if __name__ == '__main__':
    print('开始智能修复UTC时间记录...')
    print('只修复明显是UTC的记录（12-15点，且同一天有其他记录在20点之后）')
    print('')
    fix_utc_records()
