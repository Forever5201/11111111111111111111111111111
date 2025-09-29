#!/usr/bin/env python3
"""
OKX最大数据获取脚本
专门优化OKX API调用，获取尽可能多的K线数据

用法:
  python fetch_max_okx_data.py --timeframes 4H 1D
  python fetch_max_okx_data.py --symbol BTC-USD-SWAP --timeframe 4H --target 512
"""

import os
import sys
import argparse
import pandas as pd
from datetime import datetime, timedelta
import time

# 添加src目录到路径
sys.path.append("./src")

from data_fetcher import DataFetcher
from get_data import convert_to_kronos_format, save_kronos_prediction_data
from config_loader import ConfigLoader
from logger import setup_logger
from dotenv import load_dotenv

logger = setup_logger()

def fetch_maximum_okx_data(data_fetcher, symbol, timeframe, target_records=512):
    """
    使用多种策略获取OKX的最大数据量
    
    Args:
        data_fetcher: DataFetcher实例
        symbol: 交易对
        timeframe: 时间框架
        target_records: 目标记录数
        
    Returns:
        DataFrame: 获取的最大数据
    """
    logger.info(f"🎯 Attempting to fetch maximum data for {symbol} {timeframe}")
    logger.info(f"   Target: {target_records} records")
    
    all_data = []
    total_records = 0
    
    # 策略1: 直接请求最大数量
    try:
        logger.info("📊 Strategy 1: Direct maximum request")
        df1 = data_fetcher.fetch_kline_data(
            instrument_id=symbol,
            bar=timeframe,
            is_mark_price=False,
            limit=target_records  # 直接请求目标数量
        )
        
        if not df1.empty:
            all_data.append(df1)
            total_records += len(df1)
            logger.info(f"   ✅ Strategy 1: {len(df1)} records")
            
            # 如果已经达到目标，直接返回
            if len(df1) >= target_records:
                logger.info(f"🎉 Target achieved with strategy 1: {len(df1)} records")
                return df1.tail(target_records)
        else:
            logger.warning("   ❌ Strategy 1: No data returned")
            
    except Exception as e:
        logger.error(f"   ❌ Strategy 1 failed: {e}")
    
    # 策略2: 分批获取（如果策略1不够）
    if total_records < target_records:
        logger.info("📊 Strategy 2: Multiple batch requests")
        
        try:
            # 获取第一批（最新数据）
            df_latest = data_fetcher.fetch_kline_data(
                instrument_id=symbol,
                bar=timeframe,
                is_mark_price=False,
                limit=300
            )
            
            if not df_latest.empty:
                batch_data = [df_latest]
                logger.info(f"   Batch 1: {len(df_latest)} records (latest)")
                
                # 尝试获取更多历史数据
                earliest_time = df_latest['timestamp'].min()
                
                for batch_num in range(2, 4):  # 最多3批
                    try:
                        df_batch = data_fetcher.fetch_kline_data(
                            instrument_id=symbol,
                            bar=timeframe,
                            is_mark_price=False,
                            limit=300,
                            before=earliest_time
                        )
                        
                        if not df_batch.empty:
                            # 过滤重复数据
                            df_batch = df_batch[df_batch['timestamp'] < earliest_time]
                            
                            if not df_batch.empty:
                                batch_data.insert(0, df_batch)
                                earliest_time = df_batch['timestamp'].min()
                                logger.info(f"   Batch {batch_num}: {len(df_batch)} records (historical)")
                            else:
                                logger.info(f"   Batch {batch_num}: No new data")
                                break
                        else:
                            logger.info(f"   Batch {batch_num}: Empty response")
                            break
                            
                    except Exception as e:
                        logger.warning(f"   Batch {batch_num} failed: {e}")
                        break
                
                # 合并批次数据
                if batch_data:
                    combined_df = pd.concat(batch_data, ignore_index=True)
                    combined_df = combined_df.sort_values('timestamp').drop_duplicates(subset=['timestamp'])
                    
                    # 如果合并后的数据比策略1更多，使用合并数据
                    if len(combined_df) > total_records:
                        all_data = [combined_df]
                        total_records = len(combined_df)
                        logger.info(f"   ✅ Strategy 2: {len(combined_df)} records total")
                        
        except Exception as e:
            logger.error(f"   ❌ Strategy 2 failed: {e}")
    
    # 策略3: 使用不同的limit值尝试
    if total_records < target_records:
        logger.info("📊 Strategy 3: Different limit values")
        
        for limit_val in [500, 400, 350]:
            try:
                df_limit = data_fetcher.fetch_kline_data(
                    instrument_id=symbol,
                    bar=timeframe,
                    is_mark_price=False,
                    limit=limit_val
                )
                
                if not df_limit.empty and len(df_limit) > total_records:
                    all_data = [df_limit]
                    total_records = len(df_limit)
                    logger.info(f"   ✅ Strategy 3 (limit={limit_val}): {len(df_limit)} records")
                    break
                    
            except Exception as e:
                logger.warning(f"   Strategy 3 (limit={limit_val}) failed: {e}")
                continue
    
    # 返回最佳结果
    if all_data:
        final_df = all_data[0]
        if len(final_df) > target_records:
            final_df = final_df.tail(target_records)
        
        logger.info(f"🎯 Final result: {len(final_df)} records")
        logger.info(f"   Time range: {final_df['timestamp'].min()} to {final_df['timestamp'].max()}")
        
        return final_df
    else:
        logger.error("❌ All strategies failed")
        return pd.DataFrame()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='OKX最大数据获取工具')
    parser.add_argument('--symbol', default='BTC-USD-SWAP', help='交易对')
    parser.add_argument('--timeframe', default='4H', help='时间框架')
    parser.add_argument('--target', type=int, default=512, help='目标记录数')
    parser.add_argument('--output-dir', default='./Kronos/finetune/data', help='输出目录')
    
    args = parser.parse_args()
    
    logger.info("🚀 OKX最大数据获取工具")
    logger.info("=" * 50)
    
    # 加载环境变量
    load_dotenv()
    api_key = os.getenv("OKX_API_KEY")
    secret_key = os.getenv("OKX_API_SECRET")
    passphrase = os.getenv("OKX_API_PASSPHRASE")
    
    if not all([api_key, secret_key, passphrase]):
        logger.error("❌ API credentials missing")
        return False
    
    # 初始化数据获取器
    try:
        data_fetcher = DataFetcher(api_key, secret_key, passphrase)
        logger.info("✅ DataFetcher initialized")
    except Exception as e:
        logger.error(f"❌ DataFetcher initialization failed: {e}")
        return False
    
    # 获取数据
    df = fetch_maximum_okx_data(data_fetcher, args.symbol, args.timeframe, args.target)
    
    if df.empty:
        logger.error("❌ No data obtained")
        return False
    
    # 转换为Kronos格式
    symbol_key = f"{args.symbol}_{args.timeframe}"
    kronos_df = convert_to_kronos_format(df, symbol_key)
    
    if kronos_df.empty:
        logger.error("❌ Kronos format conversion failed")
        return False
    
    # 保存数据
    prediction_data = {args.timeframe: kronos_df}
    save_kronos_prediction_data(prediction_data, args.output_dir)
    
    # 显示结果
    logger.info("\n📊 Final Results:")
    logger.info(f"   Records obtained: {len(kronos_df)}")
    logger.info(f"   Target was: {args.target}")
    logger.info(f"   Success rate: {len(kronos_df)/args.target*100:.1f}%")
    logger.info(f"   Time range: {kronos_df.index[0]} to {kronos_df.index[-1]}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)