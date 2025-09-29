#!/usr/bin/env python3
"""
K线数据连续性分析脚本
检查512条K线数据是否连续、有无中断或重叠
"""

import os
import sys
import pandas as pd
import pickle
from datetime import datetime, timedelta

# 添加src目录到路径
sys.path.append("./src")
from logger import setup_logger

logger = setup_logger()

def analyze_kline_continuity(data_file, timeframe):
    """
    分析K线数据的连续性
    
    Args:
        data_file: 数据文件路径
        timeframe: 时间框架 (4H, 1D)
    """
    logger.info(f"🔍 分析 {timeframe} K线数据连续性")
    logger.info("=" * 60)
    
    try:
        # 读取pickle数据
        with open(data_file, 'rb') as f:
            data_dict = pickle.load(f)
        
        # 获取数据
        symbol_key = f"BTC-USD-SWAP_{timeframe}"
        if symbol_key not in data_dict:
            logger.error(f"❌ 未找到 {symbol_key} 数据")
            return False
        
        df = data_dict[symbol_key]
        logger.info(f"📊 数据基本信息:")
        logger.info(f"   总记录数: {len(df)}")
        logger.info(f"   时间范围: {df.index[0]} 到 {df.index[-1]}")
        
        # 转换为时间戳进行分析
        timestamps = pd.to_datetime(df.index)
        timestamps_sorted = timestamps.sort_values()
        
        # 计算时间间隔
        time_diffs = timestamps_sorted.diff().dropna()
        
        # 根据时间框架确定预期间隔
        if timeframe == '4H':
            expected_interval = timedelta(hours=4)
            interval_name = "4小时"
        elif timeframe == '1D':
            expected_interval = timedelta(days=1)
            interval_name = "1天"
        else:
            logger.error(f"❌ 不支持的时间框架: {timeframe}")
            return False
        
        logger.info(f"\n📈 时间间隔分析 (预期间隔: {interval_name}):")
        
        # 统计不同间隔的数量
        interval_counts = {}
        gaps = []
        overlaps = []
        
        for i, diff in enumerate(time_diffs):
            diff_hours = diff.total_seconds() / 3600
            
            if timeframe == '4H':
                if diff_hours == 4:
                    interval_counts['正常'] = interval_counts.get('正常', 0) + 1
                elif diff_hours > 4:
                    interval_counts['间隔过大'] = interval_counts.get('间隔过大', 0) + 1
                    gaps.append({
                        'position': i,
                        'time': timestamps_sorted.iloc[i],
                        'gap_hours': diff_hours,
                        'missing_periods': int(diff_hours / 4) - 1
                    })
                elif diff_hours < 4:
                    interval_counts['间隔过小'] = interval_counts.get('间隔过小', 0) + 1
                    if diff_hours <= 0:
                        overlaps.append({
                            'position': i,
                            'time': timestamps_sorted.iloc[i],
                            'overlap_hours': abs(diff_hours)
                        })
            elif timeframe == '1D':
                diff_days = diff.total_seconds() / (24 * 3600)
                if 0.9 <= diff_days <= 1.1:  # 允许小误差
                    interval_counts['正常'] = interval_counts.get('正常', 0) + 1
                elif diff_days > 1.1:
                    interval_counts['间隔过大'] = interval_counts.get('间隔过大', 0) + 1
                    gaps.append({
                        'position': i,
                        'time': timestamps_sorted.iloc[i],
                        'gap_days': diff_days,
                        'missing_periods': int(diff_days) - 1
                    })
                elif diff_days < 0.9:
                    interval_counts['间隔过小'] = interval_counts.get('间隔过小', 0) + 1
                    if diff_days <= 0:
                        overlaps.append({
                            'position': i,
                            'time': timestamps_sorted.iloc[i],
                            'overlap_days': abs(diff_days)
                        })
        
        # 显示统计结果
        logger.info(f"   间隔统计:")
        for interval_type, count in interval_counts.items():
            percentage = (count / len(time_diffs)) * 100
            logger.info(f"     {interval_type}: {count} ({percentage:.1f}%)")
        
        # 检查数据连续性
        logger.info(f"\n🔍 连续性检查:")
        
        # 检查重复时间戳
        duplicate_times = df.index.duplicated()
        if duplicate_times.any():
            dup_count = duplicate_times.sum()
            logger.warning(f"   ⚠️ 发现 {dup_count} 个重复时间戳")
            dup_times = df.index[duplicate_times]
            for dup_time in dup_times[:5]:  # 显示前5个
                logger.warning(f"      重复: {dup_time}")
        else:
            logger.info(f"   ✅ 无重复时间戳")
        
        # 检查时间顺序
        is_sorted = timestamps.is_monotonic_increasing
        logger.info(f"   时间顺序: {'✅ 递增' if is_sorted else '❌ 非递增'}")
        
        # 检查间隔
        if gaps:
            logger.warning(f"   ⚠️ 发现 {len(gaps)} 个时间间隔")
            logger.warning(f"   最大间隔详情:")
            for gap in sorted(gaps, key=lambda x: x.get('gap_hours', x.get('gap_days', 0)), reverse=True)[:3]:
                if timeframe == '4H':
                    logger.warning(f"      位置 {gap['position']}: {gap['time']} (间隔 {gap['gap_hours']:.1f}小时, 缺失 {gap['missing_periods']} 个周期)")
                else:
                    logger.warning(f"      位置 {gap['position']}: {gap['time']} (间隔 {gap['gap_days']:.1f}天, 缺失 {gap['missing_periods']} 个周期)")
        else:
            logger.info(f"   ✅ 无时间间隔")
        
        # 检查重叠
        if overlaps:
            logger.warning(f"   ⚠️ 发现 {len(overlaps)} 个时间重叠")
            for overlap in overlaps[:3]:  # 显示前3个
                if timeframe == '4H':
                    logger.warning(f"      位置 {overlap['position']}: {overlap['time']} (重叠 {overlap['overlap_hours']:.1f}小时)")
                else:
                    logger.warning(f"      位置 {overlap['position']}: {overlap['time']} (重叠 {overlap['overlap_days']:.1f}天)")
        else:
            logger.info(f"   ✅ 无时间重叠")
        
        # 计算连续性评分
        total_intervals = len(time_diffs)
        normal_intervals = interval_counts.get('正常', 0)
        continuity_score = (normal_intervals / total_intervals) * 100 if total_intervals > 0 else 0
        
        logger.info(f"\n📊 连续性评分:")
        logger.info(f"   连续性得分: {continuity_score:.1f}%")
        
        if continuity_score >= 95:
            logger.info(f"   评级: ✅ 优秀 (数据高度连续)")
        elif continuity_score >= 85:
            logger.info(f"   评级: ✅ 良好 (数据基本连续)")
        elif continuity_score >= 70:
            logger.info(f"   评级: ⚠️ 一般 (有少量间隔)")
        else:
            logger.info(f"   评级: ❌ 较差 (间隔较多)")
        
        # 显示时间分布
        logger.info(f"\n📅 时间分布分析:")
        logger.info(f"   开始时间: {timestamps_sorted.iloc[0]}")
        logger.info(f"   结束时间: {timestamps_sorted.iloc[-1]}")
        logger.info(f"   总时间跨度: {timestamps_sorted.iloc[-1] - timestamps_sorted.iloc[0]}")
        
        if timeframe == '4H':
            expected_total_hours = (len(df) - 1) * 4
            actual_total_hours = (timestamps_sorted.iloc[-1] - timestamps_sorted.iloc[0]).total_seconds() / 3600
            logger.info(f"   预期总时长: {expected_total_hours} 小时")
            logger.info(f"   实际总时长: {actual_total_hours:.1f} 小时")
            logger.info(f"   时长匹配度: {(expected_total_hours/actual_total_hours)*100:.1f}%")
        elif timeframe == '1D':
            expected_total_days = len(df) - 1
            actual_total_days = (timestamps_sorted.iloc[-1] - timestamps_sorted.iloc[0]).days
            logger.info(f"   预期总天数: {expected_total_days} 天")
            logger.info(f"   实际总天数: {actual_total_days} 天")
            logger.info(f"   时长匹配度: {(expected_total_days/actual_total_days)*100:.1f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 分析失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("🔍 K线数据连续性分析工具")
    logger.info("=" * 60)
    
    # 分析4H数据
    data_4h_file = "./Kronos/finetune/data/prediction_data_4h.pkl"
    if os.path.exists(data_4h_file):
        logger.info("\n📊 分析4H数据:")
        analyze_kline_continuity(data_4h_file, "4H")
    else:
        logger.warning("⚠️ 4H数据文件不存在")
    
    # 分析1D数据
    data_1d_file = "./Kronos/finetune/data/prediction_data_1d.pkl"
    if os.path.exists(data_1d_file):
        logger.info("\n📊 分析1D数据:")
        analyze_kline_continuity(data_1d_file, "1D")
    else:
        logger.warning("⚠️ 1D数据文件不存在")
    
    logger.info("\n✅ 连续性分析完成!")

if __name__ == "__main__":
    main()