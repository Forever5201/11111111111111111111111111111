#!/usr/bin/env python3
"""
OKX API调试脚本
用于理解OKX API的真实行为和限制
"""

import os
import sys
sys.path.append("./src")

from data_fetcher import DataFetcher
from logger import setup_logger
from dotenv import load_dotenv
import pandas as pd

logger = setup_logger()

def debug_okx_api():
    """调试OKX API的行为"""
    
    # 加载环境变量
    load_dotenv()
    api_key = os.getenv("OKX_API_KEY")
    secret_key = os.getenv("OKX_API_SECRET")
    passphrase = os.getenv("OKX_API_PASSPHRASE")
    
    if not all([api_key, secret_key, passphrase]):
        logger.error("API credentials missing")
        return
    
    # 初始化数据获取器
    data_fetcher = DataFetcher(api_key, secret_key, passphrase)
    symbol = "BTC-USD-SWAP"
    timeframe = "4H"
    
    logger.info("🔍 OKX API调试分析")
    logger.info("=" * 50)
    
    # 测试1: 标准candles端点
    logger.info("\n📊 测试1: 标准candles端点")
    df1 = data_fetcher.fetch_actual_price_kline(symbol, timeframe, limit=300)
    if not df1.empty:
        logger.info(f"   Records: {len(df1)}")
        logger.info(f"   Time range: {df1['timestamp'].min()} to {df1['timestamp'].max()}")
        earliest_live = df1['timestamp'].min()
        latest_live = df1['timestamp'].max()
    
    # 测试2: history-candles端点
    logger.info("\n📊 测试2: history-candles端点 (无参数)")
    df2 = data_fetcher.fetch_history_kline(symbol, timeframe, limit=300)
    if not df2.empty:
        logger.info(f"   Records: {len(df2)}")
        logger.info(f"   Time range: {df2['timestamp'].min()} to {df2['timestamp'].max()}")
    
    # 测试3: history-candles with before参数
    if not df1.empty:
        logger.info(f"\n📊 测试3: history-candles with before={earliest_live}")
        df3 = data_fetcher.fetch_history_kline(symbol, timeframe, limit=300, before=earliest_live)
        if not df3.empty:
            logger.info(f"   Records: {len(df3)}")
            logger.info(f"   Time range: {df3['timestamp'].min()} to {df3['timestamp'].max()}")
            
            # 检查是否有比live数据更早的数据
            earlier_data = df3[df3['timestamp'] < earliest_live]
            logger.info(f"   Earlier than live: {len(earlier_data)} records")
        
        # 测试4: history-candles with after参数
        logger.info(f"\n📊 测试4: history-candles with after={earliest_live}")
        df4 = data_fetcher.fetch_history_kline(symbol, timeframe, limit=300, after=earliest_live)
        if not df4.empty:
            logger.info(f"   Records: {len(df4)}")
            logger.info(f"   Time range: {df4['timestamp'].min()} to {df4['timestamp'].max()}")
    
    # 测试5: 尝试更大的limit值
    logger.info("\n📊 测试5: 尝试更大的limit值")
    for limit_val in [400, 500, 600, 1000]:
        logger.info(f"\n   Testing limit={limit_val}")
        df_test = data_fetcher.fetch_actual_price_kline(symbol, timeframe, limit=limit_val)
        if not df_test.empty:
            logger.info(f"      Got: {len(df_test)} records")
            logger.info(f"      Time range: {df_test['timestamp'].min()} to {df_test['timestamp'].max()}")
        else:
            logger.info(f"      Got: 0 records")
    
    # 测试6: 检查数据重叠
    if not df1.empty and not df2.empty:
        logger.info("\n📊 测试6: 数据重叠分析")
        overlap = set(df1['timestamp']).intersection(set(df2['timestamp']))
        logger.info(f"   Live vs History overlap: {len(overlap)} records")
        
        # 合并测试
        combined = pd.concat([df2, df1], ignore_index=True)
        combined = combined.sort_values('timestamp').drop_duplicates(subset=['timestamp'])
        logger.info(f"   Combined unique records: {len(combined)}")
        logger.info(f"   Combined time range: {combined['timestamp'].min()} to {combined['timestamp'].max()}")

if __name__ == "__main__":
    debug_okx_api()