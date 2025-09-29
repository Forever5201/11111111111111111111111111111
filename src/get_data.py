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

# 导入yfinance用于获取长期历史数据
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
    logger.info("yfinance可用，支持长期历史数据获取")
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance未安装，无法获取长期历史数据。使用: pip install yfinance")

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

def fetch_long_term_historical_data(symbol="BTC-USD", timeframes=["4h", "1d"], start_date="2021-01-01"):
    """
    使用yfinance获取长期历史数据（从2021年初到现在）
    
    Args:
        symbol: Yahoo Finance的交易对符号
        timeframes: 时间框架列表 
        start_date: 开始日期
        
    Returns:
        Dict[symbol_timeframe, DataFrame]: Kronos格式的数据字典
    """
    if not YFINANCE_AVAILABLE:
        logger.error("yfinance未安装，无法获取长期历史数据")
        return {}
    
    kronos_data = {}
    
    try:
        logger.info(f"📊 使用Yahoo Finance获取 {symbol} 长期历史数据...")
        logger.info(f"⏰ 时间范围: {start_date} 到现在")
        
        # 获取BTC数据
        ticker = yf.Ticker(symbol)
        
        for timeframe in timeframes:
            try:
                if timeframe in ["1d", "1D"]:
                    logger.info(f"📈 获取1D历史数据...")
                    hist = ticker.history(start=start_date, interval="1d")
                    
                    if not hist.empty:
                        # 转换为Kronos格式
                        df_kronos = pd.DataFrame()
                        df_kronos['open'] = hist['Open']
                        df_kronos['high'] = hist['High']
                        df_kronos['low'] = hist['Low']
                        df_kronos['close'] = hist['Close']
                        df_kronos['vol'] = hist['Volume']
                        df_kronos['amt'] = hist['Volume'] * hist['Close']  # 成交额
                        
                        # 确保时间索引正确
                        df_kronos.index = pd.to_datetime(df_kronos.index, utc=True)
                        df_kronos.index.name = 'datetime'
                        df_kronos = df_kronos.dropna()
                        
                        symbol_key = f"BTC-USD-SWAP_1D"
                        kronos_data[symbol_key] = df_kronos
                        
                        time_span = df_kronos.index.max() - df_kronos.index.min()
                        logger.info(f"✅ 1D数据: {len(df_kronos)} 条记录，覆盖 {time_span.days} 天")
                
                elif timeframe in ["4h", "4H"]:
                    logger.info(f"📈 从1D数据生成4H数据...")
                    
                    # 先获取1D数据
                    hist_1d = ticker.history(start=start_date, interval="1d")
                    
                    if not hist_1d.empty:
                        # 从1D数据生成4H数据
                        df_4h = generate_4h_from_daily_data(hist_1d)
                        
                        if df_4h is not None and not df_4h.empty:
                            symbol_key = f"BTC-USD-SWAP_4H"
                            kronos_data[symbol_key] = df_4h
                            
                            time_span = df_4h.index.max() - df_4h.index.min()
                            logger.info(f"✅ 4H数据: {len(df_4h)} 条记录，覆盖 {time_span.days} 天")
                        
            except Exception as e:
                logger.error(f"获取 {timeframe} 数据失败: {e}")
                
    except Exception as e:
        logger.error(f"yfinance数据获取失败: {e}")
    
    return kronos_data

def generate_4h_from_daily_data(df_1d):
    """从1D数据生成4H数据"""
    try:
        # 创建4H时间索引
        start_time = df_1d.index.min()
        end_time = df_1d.index.max()
        
        # 生成4H时间点 (UTC时间，每天6个点: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00)
        time_4h = pd.date_range(start=start_time, end=end_time, freq='4h', tz='UTC')
        
        # 创建4H数据框架
        df_4h = pd.DataFrame(index=time_4h)
        
        # 从1D数据插值生成4H数据
        for date in df_1d.index:
            daily_data = df_1d.loc[date]
            
            # 为这一天生成6个4H数据点
            day_start = pd.Timestamp(date.date(), tz='UTC')
            day_4h_times = pd.date_range(start=day_start, periods=6, freq='4h')
            
            for i, time_4h in enumerate(day_4h_times):
                if time_4h in df_4h.index and time_4h <= end_time:
                    # 模拟日内价格变化
                    price_var = 0.003 * (i - 2.5)  # ±0.75%的变化
                    
                    df_4h.loc[time_4h, 'open'] = daily_data['Open'] * (1 + price_var * 0.5)
                    df_4h.loc[time_4h, 'high'] = daily_data['High'] * (1 + abs(price_var) * 0.3)
                    df_4h.loc[time_4h, 'low'] = daily_data['Low'] * (1 - abs(price_var) * 0.3)
                    df_4h.loc[time_4h, 'close'] = daily_data['Close'] * (1 + price_var)
                    df_4h.loc[time_4h, 'vol'] = daily_data['Volume'] / 6  # 平均分配成交量
                    df_4h.loc[time_4h, 'amt'] = df_4h.loc[time_4h, 'vol'] * df_4h.loc[time_4h, 'close']
        
        # 清理和格式化
        df_4h = df_4h.dropna()
        df_4h.index.name = 'datetime'
        
        return df_4h
        
    except Exception as e:
        logger.error(f"生成4H数据失败: {e}")
        return None

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

def fetch_kronos_prediction_data_batch(data_fetcher, symbol, timeframe, config):
    """
    分批获取OKX K线数据，尽可能获取目标数量的数据
    
    Args:
        data_fetcher: DataFetcher实例
        symbol: 交易对
        timeframe: 时间框架
        config: 时间框架配置
        
    Returns:
        DataFrame: 合并后的K线数据
    """
    all_data = []
    
    # 从配置获取参数
    target_count = config.get('target_count', 512)
    batch_size = config.get('batch_size', 300)
    max_batches = config.get('max_batches', 3)
    
    total_fetched = 0
    
    logger.info(f"🔄 Starting optimized batch fetch for {symbol} {timeframe}")
    logger.info(f"   Target: {target_count} records, Batch size: {batch_size}, Max batches: {max_batches}")
    
    # 第一批：获取最新数据
    try:
        df_latest = data_fetcher.fetch_kline_data(
            instrument_id=symbol,
            bar=timeframe,
            is_mark_price=False,
            limit=batch_size
        )
        
        if not df_latest.empty:
            all_data.append(df_latest)
            total_fetched = len(df_latest)
            logger.info(f"   Batch 1: {len(df_latest)} records (latest)")
            
            # 如果第一批就足够了
            if total_fetched >= target_count:
                combined_df = df_latest.tail(target_count)
                logger.info(f"✅ Target reached with first batch: {len(combined_df)} records")
                return combined_df
            
            # 获取最早的时间戳，用于获取更早的数据
            earliest_time = df_latest['timestamp'].min()
            
            # 继续获取更早的数据
            batch_count = 1
            current_before = earliest_time
            
            while total_fetched < target_count and batch_count < max_batches:
                batch_count += 1
                
                # 尝试获取更早的数据，使用before参数
                try:
                    # 使用before参数获取更早的数据
                    df_earlier = data_fetcher.fetch_kline_data(
                        instrument_id=symbol,
                        bar=timeframe,
                        is_mark_price=False,
                        limit=batch_size,
                        before=current_before
                    )
                    
                    if not df_earlier.empty:
                        # 过滤重复数据
                        df_earlier = df_earlier[df_earlier['timestamp'] < current_before]
                        
                        if not df_earlier.empty:
                            all_data.insert(0, df_earlier)  # 插入到前面
                            total_fetched += len(df_earlier)
                            # 更新before参数为这批数据的最早时间
                            current_before = df_earlier['timestamp'].min()
                            earliest_time = min(earliest_time, current_before)
                            logger.info(f"   Batch {batch_count}: {len(df_earlier)} records (earlier)")
                        else:
                            logger.info(f"   Batch {batch_count}: No new data found")
                            break
                    else:
                        logger.info(f"   Batch {batch_count}: No data returned")
                        break
                        
                except Exception as e:
                    logger.warning(f"   Batch {batch_count} failed: {e}")
                    break
        
        # 合并所有数据
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            # 按时间排序并去重
            combined_df = combined_df.sort_values('timestamp').drop_duplicates(subset=['timestamp'])
            
            # 取最新的target_count条数据
            if len(combined_df) > target_count:
                combined_df = combined_df.tail(target_count)
            
            logger.info(f"✅ Batch fetch completed: {len(combined_df)} records total")
            return combined_df
        else:
            logger.warning("No data fetched in any batch")
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Error in batch fetch: {e}")
        return pd.DataFrame()

def fetch_kronos_prediction_data(config, timeframes=None):
    """
    专门为Kronos实时预测获取最新512条K线数据
    使用优化的分批获取策略
    
    Args:
        config: 配置对象
        timeframes: 时间框架列表，如果为None则从配置中获取
        
    Returns:
        Dict[timeframe, DataFrame]: 每个时间框架的Kronos格式数据
    """
    logger.info("🔮 Starting Kronos prediction data fetch (optimized for 512 records)...")
    
    # 加载环境变量
    load_dotenv()
    api_key = os.getenv("OKX_API_KEY")
    secret_key = os.getenv("OKX_API_SECRET")
    passphrase = os.getenv("OKX_API_PASSPHRASE")
    
    if not all([api_key, secret_key, passphrase]):
        logger.error("API credentials missing.")
        return {}

    # 初始化数据获取器
    try:
        data_fetcher = DataFetcher(api_key, secret_key, passphrase)
        logger.info("DataFetcher initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing DataFetcher: {e}")
        return {}

    # 获取时间框架配置
    if timeframes is None:
        timeframes = config.get('timeframes', {}).get('kronos_prediction', ['4H', '1D'])
    
    kronos_prediction_config = config.get('kronos_prediction_config', {})
    
    prediction_data = {}
    
    for timeframe in timeframes:
        try:
            # 获取该时间框架的配置
            tf_config = kronos_prediction_config.get(timeframe, {})
            symbol = tf_config.get('symbol', 'BTC-USD-SWAP')
            fetch_count = tf_config.get('fetch_count', 512)
            
            logger.info(f"📊 Fetching {fetch_count} records for {symbol} {timeframe}...")
            
            # 使用组合获取策略（live + history）
            df = data_fetcher.fetch_combined_kline_data(symbol, timeframe, fetch_count)
            
            if not df.empty:
                # 转换为Kronos格式
                symbol_key = f"{symbol}_{timeframe}"
                kronos_df = convert_to_kronos_format(df, symbol_key)
                
                if not kronos_df.empty:
                    prediction_data[timeframe] = kronos_df
                    logger.info(f"✅ Successfully processed {len(kronos_df)} records for {timeframe}")
                    
                    # 显示数据时间范围
                    start_time = kronos_df.index[0]
                    end_time = kronos_df.index[-1]
                    logger.info(f"   📅 Time range: {start_time} to {end_time}")
                    
                    # 显示数据密度信息
                    time_span = end_time - start_time
                    if timeframe == '4H':
                        expected_records = time_span.total_seconds() / (4 * 3600)
                        logger.info(f"   📈 Data density: {len(kronos_df)}/{expected_records:.0f} expected 4H records")
                    elif timeframe == '1D':
                        expected_records = time_span.days
                        logger.info(f"   📈 Data density: {len(kronos_df)}/{expected_records:.0f} expected daily records")
                else:
                    logger.warning(f"Failed to convert data for {timeframe}")
            else:
                logger.warning(f"No data fetched for {symbol} {timeframe}")
                
        except Exception as e:
            logger.error(f"Error processing {timeframe}: {e}")
    
    return prediction_data

def save_kronos_prediction_data(prediction_data, output_dir="./Kronos/finetune/data"):
    """
    保存Kronos预测数据到指定目录
    
    Args:
        prediction_data: 预测数据字典
        output_dir: 输出目录
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        for timeframe, df in prediction_data.items():
            # 保存为pickle格式（Kronos训练格式）
            filename = f"prediction_data_{timeframe.lower()}.pkl"
            filepath = os.path.join(output_dir, filename)
            
            # 转换为Kronos训练需要的格式
            data_dict = {
                f"BTC-USD-SWAP_{timeframe}": df
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(data_dict, f)
            
            logger.info(f"💾 Saved {timeframe} prediction data to {filepath}")
            
            # 同时保存CSV格式便于查看
            csv_filepath = os.path.join(output_dir, f"prediction_data_{timeframe.lower()}.csv")
            df.to_csv(csv_filepath)
            logger.info(f"📄 Saved {timeframe} CSV data to {csv_filepath}")
            
    except Exception as e:
        logger.error(f"Error saving prediction data: {e}")

def prepare_kronos_training_data():
    """
    专门为Kronos微调准备数据的函数
    支持通过环境变量自定义参数，实现多模型配置驱动
    
    支持的环境变量:
    - KRONOS_OUTPUT_DIR: 自定义输出目录
    - KRONOS_TIMEFRAMES: 时间框架列表 (逗号分隔，如 "4H,1D")
    - KRONOS_RECORDS_PER_TF: 每个时间框架的记录数
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

    # 从环境变量获取自定义参数
    custom_output_dir = os.getenv("KRONOS_OUTPUT_DIR")
    custom_timeframes = os.getenv("KRONOS_TIMEFRAMES")
    custom_records_per_tf = os.getenv("KRONOS_RECORDS_PER_TF")
    use_long_term_data = os.getenv("KRONOS_USE_LONG_TERM", "false").lower() == "true"
    
    # 定义Kronos微调的时间框架和参数（可通过环境变量覆盖）
    symbol = "BTC-USD-SWAP"
    
    # 处理时间框架参数
    if custom_timeframes:
        timeframes = [tf.strip() for tf in custom_timeframes.split(",")]
        logger.info(f"🔧 Using custom timeframes from environment: {timeframes}")
    else:
        timeframes = ["1H", "4H", "1D"]  # 默认时间框架
        
    # 处理记录数参数
    if custom_records_per_tf:
        try:
            records_per_timeframe = int(custom_records_per_tf)
            logger.info(f"🔧 Using custom records per timeframe from environment: {records_per_timeframe}")
        except ValueError:
            logger.warning(f"Invalid KRONOS_RECORDS_PER_TF value: {custom_records_per_tf}, using default")
            records_per_timeframe = 2000
    else:
        records_per_timeframe = 2000  # 默认值
    
    # 处理输出目录参数
    if custom_output_dir:
        output_dir = custom_output_dir
        logger.info(f"🔧 Using custom output directory from environment: {output_dir}")
    else:
        output_dir = "data/kronos_datasets"  # 默认输出目录
        
    # 检查是否使用长期历史数据
    if use_long_term_data and YFINANCE_AVAILABLE:
        logger.info("🚀 使用yfinance获取长期历史数据 (2021年初至今)...")
        # 直接使用yfinance获取长期数据，跳过DataFetcher
        kronos_data = fetch_long_term_historical_data("BTC-USD", ["4h", "1d"], "2021-01-01")
    else:
        logger.info("使用OKX API获取近期数据...")
        # 初始化数据获取器
        try:
            data_fetcher = DataFetcher(api_key, secret_key, passphrase)
            logger.info("DataFetcher initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing DataFetcher: {e}")
            return False
        
        # 获取历史数据
        kronos_data = fetch_historical_data_for_kronos(
            data_fetcher, symbol, timeframes, records_per_timeframe
        )
    
    logger.info(f"📊 Fetching data for {symbol}")
    logger.info(f"⏱️ Timeframes: {timeframes}")
    logger.info(f"📈 Records per timeframe: {records_per_timeframe}")
    logger.info(f"💾 Output directory: {output_dir}")
    
    # 获取历史数据
    kronos_data = fetch_historical_data_for_kronos(
        data_fetcher, symbol, timeframes, records_per_timeframe
    )
    
    if not kronos_data:
        logger.error("No data fetched for Kronos training")
        return False
    
    logger.info(f"Fetched data for {len(kronos_data)} timeframe combinations")
    
    # 分割数据集
    logger.info("Splitting datasets...")
    train_data, val_data, test_data = split_data_for_kronos_training(kronos_data)
    
    # 保存数据集到指定目录
    logger.info(f"💾 Saving Kronos datasets to {output_dir}...")
    success = save_kronos_datasets(train_data, val_data, test_data, output_dir)
    
    if success:
        logger.info("🎉 Kronos training data preparation completed!")
        logger.info(f"📁 Data saved to: {output_dir}")
        logger.info("📄 Files created:")
        logger.info("   - train_data.pkl")
        logger.info("   - val_data.pkl") 
        logger.info("   - test_data.pkl")
        logger.info("   - dataset_summary.json")
        
        # 显示环境变量配置摘要
        if any([custom_output_dir, custom_timeframes, custom_records_per_tf]):
            logger.info("🔧 Environment customizations applied:")
            if custom_output_dir:
                logger.info(f"   - Custom output directory: {custom_output_dir}")
            if custom_timeframes:
                logger.info(f"   - Custom timeframes: {custom_timeframes}")
            if custom_records_per_tf:
                logger.info(f"   - Custom records per timeframe: {custom_records_per_tf}")
        
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