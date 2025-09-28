# get_data.py

import os
import json
import pickle
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv
from logger import setup_logger
from config_loader import ConfigLoader
# from account_fetcher import AccountFetcher  # 暂时注释，测试时不需要账户信息
from data_fetcher import DataFetcher
from technical_indicator import TechnicalIndicator

logger = setup_logger()

def select_indicator_params(config, timeframe):
    """
    根据timeframe选择对应的指标参数
    :param config: 配置信息
    :param timeframe: 时间周期
    :return: 对应的指标参数
    """
    for category, intervals in config.get('timeframes', {}).items():
        if timeframe in intervals:
            return config['indicators'].get(category, config['indicators']['midterm'])
    return config['indicators']['midterm']

def fetch_and_process_kline(data_fetcher, symbol, timeframe, config, is_mark_price=False):
    """
    获取和处理K线数据，包括获取历史K线和当前未完结K线
    """
    try:
        # 获取该时间周期的配置
        kline_config = config.get('kline_config', {}).get(timeframe, {})
        fetch_count = kline_config.get('fetch_count', 100)  # 默认获取100条
        output_count = kline_config.get('output_count', 50) # 默认输出50条
        
        logger.info(f"Fetching K-line data for {timeframe}...")
        
        # 获取历史K线数据
        kline_df = data_fetcher.fetch_kline_data(
            instrument_id=symbol,
            bar=timeframe,
            is_mark_price=is_mark_price,
            limit=fetch_count
        )
        
        if kline_df.empty:
            logger.warning(f"No K-line data for {timeframe}.")
            return pd.DataFrame()

        # 获取当前未完结K线
        current_kline_df = data_fetcher.get_current_kline(symbol, timeframe)
        
        # 如果有未完结K线，添加到数据集
        if not current_kline_df.empty:
            kline_df = pd.concat([kline_df, current_kline_df])

        # 确保按时间排序并重置索引
        kline_df = kline_df.sort_values('timestamp', ascending=False)
        kline_df = kline_df.head(fetch_count).sort_values('timestamp')
        kline_df = kline_df.reset_index(drop=True)

        # 选择指标参数并计算技术指标
        indicator_params = select_indicator_params(config, timeframe)
        
        if 'volume' not in kline_df.columns:
            kline_df['volume'] = 0

        logger.info(f"Calculating indicators for {timeframe}...")
        indicator_calculator = TechnicalIndicator(params=indicator_params)
        kline_df = indicator_calculator.calculate_all(kline_df, category=timeframe)

        # 只保留最近的指定数量的K线
        if len(kline_df) > output_count:
            kline_df = kline_df.tail(output_count)

        # 设置K线状态
        kline_df["is_closed"] = True
        if not current_kline_df.empty:
            kline_df.iloc[-1, kline_df.columns.get_loc("is_closed")] = False

        return kline_df

    except Exception as e:
        logger.error(f"Error processing K-line data for {timeframe}: {e}")
        return pd.DataFrame()

def convert_to_kronos_format(df, symbol_name):
    """
    将OKX K线数据转换为Kronos微调需要的格式
    
    Args:
        df: OKX K线数据DataFrame
        symbol_name: 交易对标识符
        
    Returns:
        转换后的Kronos格式DataFrame
    """
    if df.empty:
        logger.warning(f"Empty dataframe for {symbol_name}")
        return pd.DataFrame()
    
    try:
        # 创建Kronos格式的DataFrame
        kronos_df = pd.DataFrame()
        
        # 字段映射：OKX -> Kronos
        field_mapping = {
            'open': 'open',
            'high': 'high', 
            'low': 'low',
            'close': 'close',
            'volume': 'vol',              # OKX volume -> Kronos vol
            'currency_volume': 'amt'      # OKX currency_volume -> Kronos amt
        }
        
        # 映射字段
        for okx_field, kronos_field in field_mapping.items():
            if okx_field in df.columns:
                kronos_df[kronos_field] = pd.to_numeric(df[okx_field], errors='coerce')
            else:
                logger.warning(f"Field {okx_field} not found in data for {symbol_name}")
                kronos_df[kronos_field] = 0.0
        
        # 处理时间索引 - 转换为datetime并设为索引
        if 'time_iso' in df.columns:
            kronos_df.index = pd.to_datetime(df['time_iso'])
        elif 'timestamp' in df.columns:
            # 假设timestamp是秒或毫秒时间戳
            if df['timestamp'].iloc[0] > 1e10:  # 毫秒时间戳
                kronos_df.index = pd.to_datetime(df['timestamp'], unit='ms')
            else:  # 秒时间戳
                kronos_df.index = pd.to_datetime(df['timestamp'], unit='s')
        else:
            logger.error(f"No timestamp field found for {symbol_name}")
            return pd.DataFrame()
        
        # 确保索引名称为datetime（Kronos要求）
        kronos_df.index.name = 'datetime'
        
        # 填充NaN值
        kronos_df = kronos_df.fillna(0.0)
        
        # 确保数据类型正确
        for col in ['open', 'high', 'low', 'close', 'vol', 'amt']:
            kronos_df[col] = kronos_df[col].astype(float)
        
        # 按时间排序
        kronos_df = kronos_df.sort_index()
        
        logger.info(f"Converted {len(kronos_df)} records for {symbol_name}")
        return kronos_df
        
    except Exception as e:
        logger.error(f"Error converting {symbol_name} to Kronos format: {e}")
        return pd.DataFrame()

def fetch_historical_data_for_kronos(data_fetcher, symbol, timeframes, records_per_timeframe=1000):
    """
    获取历史数据用于Kronos微调
    
    Args:
        data_fetcher: DataFetcher实例
        symbol: 交易对
        timeframes: 时间框架列表
        records_per_timeframe: 每个时间框架获取的记录数
        
    Returns:
        Dict[symbol_timeframe, DataFrame]: Kronos格式的数据字典
    """
    kronos_data = {}
    
    for timeframe in timeframes:
        try:
            logger.info(f"Fetching {records_per_timeframe} records for {symbol} {timeframe}")
            
            # 获取历史数据
            df = data_fetcher.fetch_kline_data(
                instrument_id=symbol,
                bar=timeframe,
                is_mark_price=False,
                limit=records_per_timeframe
            )
            
            if not df.empty:
                # 转换为Kronos格式
                symbol_key = f"{symbol}_{timeframe}"
                kronos_df = convert_to_kronos_format(df, symbol_key)
                
                if not kronos_df.empty:
                    kronos_data[symbol_key] = kronos_df
                    logger.info(f"Successfully processed {len(kronos_df)} records for {symbol_key}")
                else:
                    logger.warning(f"Failed to convert data for {symbol_key}")
            else:
                logger.warning(f"No data fetched for {symbol} {timeframe}")
                
        except Exception as e:
            logger.error(f"Error processing {symbol} {timeframe}: {e}")
    
    return kronos_data

def split_data_for_kronos_training(data_dict, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
    """
    按时间顺序分割数据为训练/验证/测试集
    
    Args:
        data_dict: 原始数据字典
        train_ratio: 训练集比例
        val_ratio: 验证集比例
        test_ratio: 测试集比例
        
    Returns:
        (train_data, val_data, test_data) 三个数据字典
    """
    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-6:
        logger.error("Data split ratios must sum to 1.0")
        return {}, {}, {}
    
    train_data = {}
    val_data = {}
    test_data = {}
    
    for symbol, df in data_dict.items():
        if df.empty:
            continue
            
        n_total = len(df)
        n_train = int(n_total * train_ratio)
        n_val = int(n_total * val_ratio)
        
        # 按时间顺序分割（早期->训练，中期->验证，最新->测试）
        train_data[symbol] = df.iloc[:n_train].copy()
        val_data[symbol] = df.iloc[n_train:n_train+n_val].copy()
        test_data[symbol] = df.iloc[n_train+n_val:].copy()
        
        logger.info(f"Split {symbol}: train={len(train_data[symbol])}, "
                   f"val={len(val_data[symbol])}, test={len(test_data[symbol])}")
    
    return train_data, val_data, test_data

def save_kronos_datasets(train_data, val_data, test_data, output_dir="data/kronos_datasets"):
    """
    保存Kronos格式的数据集为pickle文件
    
    Args:
        train_data: 训练数据字典
        val_data: 验证数据字典
        test_data: 测试数据字典
        output_dir: 输出目录
        
    Returns:
        是否保存成功
    """
    try:
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存三个数据集
        datasets = {
            'train_data.pkl': train_data,
            'val_data.pkl': val_data,
            'test_data.pkl': test_data
        }
        
        for filename, data in datasets.items():
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
            logger.info(f"Saved {filename} with {len(data)} symbols")
        
        # 保存数据摘要
        summary = {
            'train_symbols': len(train_data),
            'val_symbols': len(val_data), 
            'test_symbols': len(test_data),
            'total_train_records': sum(len(df) for df in train_data.values()),
            'total_val_records': sum(len(df) for df in val_data.values()),
            'total_test_records': sum(len(df) for df in test_data.values()),
            'created_at': datetime.now().isoformat(),
            'symbols': list(train_data.keys())
        }
        
        summary_path = os.path.join(output_dir, 'dataset_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully saved Kronos datasets to {output_dir}")
        logger.info(f"Summary: {summary}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving Kronos datasets: {e}")
        return False

def prepare_kronos_training_data():
    """
    专门为Kronos微调准备数据的函数
    """
    logger.info("🎯 Starting Kronos training data preparation...")
    
    # 加载配置
    try:
        config_loader = ConfigLoader("../config/config.yaml")
        config = config_loader.load_config()
        logger.info("Configuration loaded.")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return False

    # 加载环境变量
    load_dotenv()
    api_key = os.getenv("OKX_API_KEY")
    secret_key = os.getenv("OKX_API_SECRET")
    passphrase = os.getenv("OKX_API_PASSPHRASE")
    if not all([api_key, secret_key, passphrase]):
        logger.error("API credentials missing.")
        return False

    # 初始化数据获取器
    try:
        data_fetcher = DataFetcher(api_key, secret_key, passphrase)
        logger.info("DataFetcher initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing DataFetcher: {e}")
        return False

    # 定义Kronos微调的时间框架和参数
    symbol = "BTC-USD-SWAP"
    timeframes = ["1H", "4H", "1D"]  # 适合Kronos的时间框架
    records_per_timeframe = 2000  # 每个时间框架获取2000条记录
    
    logger.info(f"📊 Fetching data for {symbol}")
    logger.info(f"⏱️ Timeframes: {timeframes}")
    logger.info(f"📈 Records per timeframe: {records_per_timeframe}")
    
    # 获取历史数据
    kronos_data = fetch_historical_data_for_kronos(
        data_fetcher, symbol, timeframes, records_per_timeframe
    )
    
    if not kronos_data:
        logger.error("❌ No data fetched for Kronos training")
        return False
    
    logger.info(f"✅ Fetched data for {len(kronos_data)} timeframe combinations")
    
    # 分割数据集
    logger.info("📊 Splitting datasets...")
    train_data, val_data, test_data = split_data_for_kronos_training(kronos_data)
    
    # 保存数据集
    logger.info("💾 Saving Kronos datasets...")
    success = save_kronos_datasets(train_data, val_data, test_data)
    
    if success:
        logger.info("🎉 Kronos training data preparation completed!")
        logger.info("📁 Data saved to: data/kronos_datasets/")
        logger.info("📄 Files created:")
        logger.info("   - train_data.pkl")
        logger.info("   - val_data.pkl") 
        logger.info("   - test_data.pkl")
        logger.info("   - dataset_summary.json")
        logger.info("🚀 Ready for Kronos fine-tuning!")
        return True
    else:
        logger.error("❌ Failed to save Kronos datasets")
        return False

def main():
    logger.info("Starting the data fetching process...")
    
    # 加载配置
    try:
        config_loader = ConfigLoader("../config/config.yaml")
        config = config_loader.load_config()
        logger.info("Configuration loaded.")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return

    # 加载环境变量
    load_dotenv()
    api_key = os.getenv("OKX_API_KEY")
    secret_key = os.getenv("OKX_API_SECRET")
    passphrase = os.getenv("OKX_API_PASSPHRASE")
    if not all([api_key, secret_key, passphrase]):
        logger.error("API credentials missing.")
        return

    # 初始化API客户端
    try:
        account_fetcher = AccountFetcher(api_key, secret_key, passphrase)
        data_fetcher = DataFetcher(api_key, secret_key, passphrase)
    except Exception as e:
        logger.error(f"Error initializing modules: {e}")
        return

    # 获取账户详细信息
    logger.info("Fetching account data...")
    account_info = {"balance": 0, "positions": []}
    try:
        acct_bal = account_fetcher.get_balance()
        account_info = {
            "balance": acct_bal.get("balance", 0),
            "available_balance": acct_bal.get("available_balance", 0),
            "margin_ratio": acct_bal.get("margin_ratio", 0),
            "margin_frozen": acct_bal.get("margin_frozen", 0),
            "total_equity": acct_bal.get("total_equity", 0),
            "unrealized_pnl": acct_bal.get("unrealized_pnl", 0),
            "positions": account_fetcher.get_detailed_positions()
        }
    except Exception as e:
        logger.error(f"Error fetching account data: {e}")

    # 获取所有需要处理的时间周期
    all_timeframes = []
    for category, tfs in config.get('timeframes', {}).items():
        all_timeframes.extend(tfs)

    symbol = "BTC-USD-SWAP"  # 可从config或env中加载

    # 处理K线数据
    timeframes_data = {}
    logger.info("Fetching actual price timeframes data...")
    for tf in all_timeframes:
        df = fetch_and_process_kline(data_fetcher, symbol, tf, config, is_mark_price=False)
        if not df.empty:
            timeframes_data[tf] = {
                "type": "actual_price",
                "indicators_params": select_indicator_params(config, tf),
                "data": df.to_dict(orient="records")
            }

    # 获取当前市场数据
    current_market_data = {}
    try:
        # 获取市场基础数据
        market_data = data_fetcher.fetch_ticker(symbol)
        # 获取资金费率数据
        funding_data = data_fetcher.fetch_funding_rate(symbol)
        
        current_market_data = {
            "last_price": market_data.get("last_price", 0),
            "best_bid": market_data.get("best_bid", 0),
            "best_ask": market_data.get("best_ask", 0),
            "24h_high": market_data.get("24h_high", 0),
            "24h_low": market_data.get("24h_low", 0),
            "24h_volume": market_data.get("24h_volume", 0),
            "24h_turnover": market_data.get("24h_turnover", 0),
            "open_interest": market_data.get("open_interest", 0),
            "funding_rate": funding_data.get("funding_rate", 0),
            "next_funding_time": funding_data.get("next_funding_time", ""),
            "estimated_rate": funding_data.get("estimated_rate", 0),
            "timestamp": market_data.get("timestamp", 0),
            "time_iso": market_data.get("time_iso", "")
        }
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")

    # 整合输出数据
    output_data = {
        "account_info": account_info,
        "current_market_data": current_market_data,
        "timeframes": timeframes_data,
        "metadata": {
            "fetch_time": pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "symbol": symbol,
            "data_version": "1.0"
        }
    }

    # 保存结果到文件
    try:
        with open("data.json", "w") as f:
            json.dump(output_data, f, indent=4)
        logger.info("Results saved to data.json")
    except Exception as e:
        logger.error(f"Error saving results: {e}")

if __name__ == "__main__":
    import sys
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--kronos":
        # 生成Kronos微调数据
        success = prepare_kronos_training_data()
        sys.exit(0 if success else 1)
    else:
        # 默认生成常规JSON数据
        main()