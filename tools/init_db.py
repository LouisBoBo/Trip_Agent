import os
import shutil
import sqlite3
import pandas as pd

from tools import backup_file, local_file


def update_dates():
    """
    更新数据库中的日期，使其与2026年2月14日对齐。
    同步更新所有表的日期字段：flights, bookings, hotels, car_rentals

    返回:
        str: 更新后的数据库文件路径。
    """
    # 使用备份文件覆盖现有文件，作为重置步骤
    shutil.copy(backup_file, local_file)  # 如果目标路径已经存在一个同名文件，shutil.copy 会覆盖该文件。

    conn = sqlite3.connect(local_file)

    # 获取所有表名
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn).name.tolist()
    tdf = {}

    # 读取每个表的数据
    for t in tables:
        tdf[t] = pd.read_sql(f"SELECT * from {t}", conn)

    # 找出示例时间（这里用flights表中的actual_departure的最大值）
    example_time = pd.to_datetime(tdf["flights"]["actual_departure"].replace("\\N", pd.NaT)).max()
    
    # 目标时间：2026年2月14日，使用与example_time相同的时区
    target_time = pd.to_datetime("2026-02-14 00:00:00").tz_localize(example_time.tz)
    time_diff = target_time - example_time

    print(f"基准时间: {example_time}")
    print(f"目标时间: {target_time}")
    print(f"时间差: {time_diff}")

    # 更新flights表的日期列
    datetime_columns = ["scheduled_departure", "scheduled_arrival", "actual_departure", "actual_arrival"]
    for column in datetime_columns:
        tdf["flights"][column] = (
                pd.to_datetime(tdf["flights"][column].replace("\\N", pd.NaT)) + time_diff
        )

    # 更新bookings表中的book_date
    if "bookings" in tdf:
        tdf["bookings"]["book_date"] = (
                pd.to_datetime(tdf["bookings"]["book_date"].replace("\\N", pd.NaT), utc=True) + time_diff
        )

    # 更新hotels表的checkin_date和checkout_date
    if "hotels" in tdf:
        for col in ["checkin_date", "checkout_date"]:
            if col in tdf["hotels"].columns:
                # 保存原始值
                original_values = tdf["hotels"][col].copy()
                # 转换为datetime，添加时间差，然后转换回日期格式字符串
                dates = pd.to_datetime(tdf["hotels"][col].replace("\\N", pd.NaT).replace("", pd.NaT), errors='coerce')
                mask = dates.notna()
                if mask.any():
                    valid_dates = dates[mask].copy()
                    # 添加时区（如果需要）
                    if hasattr(valid_dates.iloc[0], 'tz') and valid_dates.iloc[0].tz is None:
                        valid_dates = valid_dates.dt.tz_localize(example_time.tz)
                    # 添加时间差
                    valid_dates = valid_dates + time_diff
                    # 转换回日期格式字符串（YYYY-MM-DD）
                    if hasattr(valid_dates.iloc[0], 'tz') and valid_dates.iloc[0].tz is not None:
                        valid_dates = valid_dates.dt.tz_localize(None)
                    tdf["hotels"].loc[mask, col] = valid_dates.dt.strftime('%Y-%m-%d').values
                # 保持空值不变
                tdf["hotels"].loc[~mask, col] = original_values.loc[~mask]

    # 更新car_rentals表的start_date和end_date
    if "car_rentals" in tdf:
        for col in ["start_date", "end_date"]:
            if col in tdf["car_rentals"].columns:
                # 保存原始值
                original_values = tdf["car_rentals"][col].copy()
                # 转换为datetime，添加时间差，然后转换回日期格式字符串
                dates = pd.to_datetime(tdf["car_rentals"][col].replace("\\N", pd.NaT).replace("", pd.NaT), errors='coerce')
                mask = dates.notna()
                if mask.any():
                    valid_dates = dates[mask].copy()
                    # 添加时区（如果需要）
                    if hasattr(valid_dates.iloc[0], 'tz') and valid_dates.iloc[0].tz is None:
                        valid_dates = valid_dates.dt.tz_localize(example_time.tz)
                    # 添加时间差
                    valid_dates = valid_dates + time_diff
                    # 转换回日期格式字符串（YYYY-MM-DD）
                    if hasattr(valid_dates.iloc[0], 'tz') and valid_dates.iloc[0].tz is not None:
                        valid_dates = valid_dates.dt.tz_localize(None)
                    tdf["car_rentals"].loc[mask, col] = valid_dates.dt.strftime('%Y-%m-%d').values
                # 保持空值不变
                tdf["car_rentals"].loc[~mask, col] = original_values.loc[~mask]

    # 将更新后的数据写回数据库
    for table_name, df in tdf.items():
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        del df  # 清理内存
    del tdf  # 清理内存

    conn.commit()
    conn.close()

    print("✓ 所有日期已同步更新为2026年2月14日")
    return local_file


if __name__ == '__main__':

    # 执行日期更新操作
    db = update_dates()