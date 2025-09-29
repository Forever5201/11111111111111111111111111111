#!/usr/bin/env python3
"""
详细的K线数据连续性检查
"""

import pandas as pd
from datetime import datetime, timedelta
import sys
sys.path.append("./src")
from logger import setup_logger

logger = setup_logger()

def check_4h_continuity():
    """检查4H数据连续性"""
    logger.info("检查4H数据连续性")
    logger.info("=" * 40)
    
    # 读取CSV数据
    df = pd.read_csv("./Kronos/finetune/data/prediction_data_4h.csv")
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime')
    
    logger.info(f"总记录数: {len(df)}")
    logger.info(f"时间范围: {df['datetime'].iloc[0]} 到 {df['datetime'].iloc[-1]}")
    
    # 检查时间间隔
    time_diffs = df['datetime'].diff().dropna()
    expected_interval = timedelta(hours=4)
    
    # 统计间隔
    normal_count = 0
    gap_count = 0
    overlap_count = 0
    
    gaps = []
    overlaps = []
    
    for i, diff in enumerate(time_diffs):
        if diff == expected_interval:
            normal_count += 1
        elif diff > expected_interval:
            gap_count += 1
            missing_periods = int(diff.total_seconds() / (4 * 3600)) - 1
            gaps.append({
                'index': i + 1,
                'time': df['datetime'].iloc[i + 1],
                'gap': diff,
                'missing_periods': missing_periods
            })
        elif diff < expected_interval:
            overlap_count += 1
            overlaps.append({
                'index': i + 1,
                'time': df['datetime'].iloc[i + 1],
                'overlap': diff
            })
    
    logger.info(f"\n间隔统计:")
    logger.info(f"  正常间隔 (4小时): {normal_count}")
    logger.info(f"  时间间隔: {gap_count}")
    logger.info(f"  时间重叠: {overlap_count}")
    
    # 连续性评分
    total_intervals = len(time_diffs)
    continuity_score = (normal_count / total_intervals) * 100
    logger.info(f"\n连续性评分: {continuity_score:.1f}%")
    
    # 显示间隔详情
    if gaps:
        logger.info(f"\n时间间隔详情:")
        for gap in gaps[:5]:  # 显示前5个
            logger.info(f"  位置 {gap['index']}: {gap['time']}")
            logger.info(f"    间隔: {gap['gap']}")
            logger.info(f"    缺失周期: {gap['missing_periods']}")
    
    # 显示重叠详情
    if overlaps:
        logger.info(f"\n时间重叠详情:")
        for overlap in overlaps[:5]:  # 显示前5个
            logger.info(f"  位置 {overlap['index']}: {overlap['time']}")
            logger.info(f"    重叠: {overlap['overlap']}")
    
    return continuity_score, gaps, overlaps

def check_1d_continuity():
    """检查1D数据连续性"""
    logger.info("\n检查1D数据连续性")
    logger.info("=" * 40)
    
    # 读取CSV数据
    df = pd.read_csv("./Kronos/finetune/data/prediction_data_1d.csv")
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime')
    
    logger.info(f"总记录数: {len(df)}")
    logger.info(f"时间范围: {df['datetime'].iloc[0]} 到 {df['datetime'].iloc[-1]}")
    
    # 检查时间间隔
    time_diffs = df['datetime'].diff().dropna()
    expected_interval = timedelta(days=1)
    
    # 统计间隔
    normal_count = 0
    gap_count = 0
    overlap_count = 0
    
    gaps = []
    overlaps = []
    
    for i, diff in enumerate(time_diffs):
        diff_days = diff.total_seconds() / (24 * 3600)
        
        if 0.9 <= diff_days <= 1.1:  # 允许小误差
            normal_count += 1
        elif diff_days > 1.1:
            gap_count += 1
            missing_periods = int(diff_days) - 1
            gaps.append({
                'index': i + 1,
                'time': df['datetime'].iloc[i + 1],
                'gap_days': diff_days,
                'missing_periods': missing_periods
            })
        elif diff_days < 0.9:
            overlap_count += 1
            overlaps.append({
                'index': i + 1,
                'time': df['datetime'].iloc[i + 1],
                'overlap_days': diff_days
            })
    
    logger.info(f"\n间隔统计:")
    logger.info(f"  正常间隔 (1天): {normal_count}")
    logger.info(f"  时间间隔: {gap_count}")
    logger.info(f"  时间重叠: {overlap_count}")
    
    # 连续性评分
    total_intervals = len(time_diffs)
    continuity_score = (normal_count / total_intervals) * 100
    logger.info(f"\n连续性评分: {continuity_score:.1f}%")
    
    # 显示间隔详情
    if gaps:
        logger.info(f"\n时间间隔详情:")
        for gap in gaps[:5]:  # 显示前5个
            logger.info(f"  位置 {gap['index']}: {gap['time']}")
            logger.info(f"    间隔: {gap['gap_days']:.1f} 天")
            logger.info(f"    缺失周期: {gap['missing_periods']}")
    
    return continuity_score, gaps, overlaps

def main():
    """主函数"""
    logger.info("K线数据连续性详细分析")
    logger.info("=" * 50)
    
    # 检查4H数据
    score_4h, gaps_4h, overlaps_4h = check_4h_continuity()
    
    # 检查1D数据
    score_1d, gaps_1d, overlaps_1d = check_1d_continuity()
    
    # 总结
    logger.info(f"\n总结报告")
    logger.info("=" * 30)
    logger.info(f"4H数据:")
    logger.info(f"  连续性: {score_4h:.1f}%")
    logger.info(f"  间隔数: {len(gaps_4h)}")
    logger.info(f"  重叠数: {len(overlaps_4h)}")
    
    logger.info(f"\n1D数据:")
    logger.info(f"  连续性: {score_1d:.1f}%")
    logger.info(f"  间隔数: {len(gaps_1d)}")
    logger.info(f"  重叠数: {len(overlaps_1d)}")
    
    # 整体评价
    avg_score = (score_4h + score_1d) / 2
    logger.info(f"\n整体评价:")
    logger.info(f"  平均连续性: {avg_score:.1f}%")
    
    if avg_score >= 95:
        logger.info(f"  结论: 数据质量优秀，高度连续")
    elif avg_score >= 85:
        logger.info(f"  结论: 数据质量良好，基本连续")
    else:
        logger.info(f"  结论: 数据质量需要改进")

if __name__ == "__main__":
    main()