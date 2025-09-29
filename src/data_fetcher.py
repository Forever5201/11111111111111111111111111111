import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from logger import setup_logger
import time
import hmac
import base64
import hashlib
import pandas as pd

logger = setup_logger()

class DataFetcher:
    def __init__(self, api_key, secret_key, passphrase, base_url="https://www.okx.com"):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.base_url = base_url
        self.session = requests.Session()
        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)

    def _get_headers(self, method, path, body):
        timestamp = str(time.time())
        pre_hash_string = f"{timestamp}{method}{path}{body}"
        signature = hmac.new(
            self.secret_key.encode("utf-8"), pre_hash_string.encode("utf-8"), hashlib.sha256
        ).digest()
        signature_base64 = base64.b64encode(signature).decode()

        headers = {
            "Content-Type": "application/json",
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": signature_base64,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase
        }
        return headers

    def fetch_funding_rate(self, instrument_id):
        """获取资金费率信息，添加空值处理"""
        endpoint = "/api/v5/public/funding-rate"
        params = {"instId": instrument_id}
        headers = self._get_headers("GET", endpoint, "")
        
        try:
            logger.info(f"Fetching funding rate for {instrument_id}...")
            response = self.session.get(f"{self.base_url}{endpoint}", headers=headers, params=params)
            response.raise_for_status()
            data = response.json().get("data", [])
            
            if data and len(data) > 0:
                funding_data = data[0]
                return {
                    "funding_rate": float(funding_data.get("fundingRate") or 0),
                    "next_funding_time": funding_data.get("nextFundingTime", ""),
                    "estimated_rate": float(funding_data.get("nextFundingRate") or 0)
                }
            return {
                "funding_rate": 0,
                "next_funding_time": "",
                "estimated_rate": 0
            }
        except Exception as e:
            logger.error(f"Error fetching funding rate: {e}")
            return {
                "funding_rate": 0,
                "next_funding_time": "",
                "estimated_rate": 0
            }

    def _process_kline_data(self, df):
        """处理K线数据的公共方法"""
        try:
            numeric_columns = ["open", "high", "low", "close", "volume", 
                             "currency_volume", "turnover"]
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
            
            if "trades" in df.columns:
                df["trades"] = df["trades"].astype(int, errors="ignore")

            df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), 
                                           unit="ms", utc=True)
            df["time_iso"] = df["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            df["timestamp"] = df["timestamp"].astype(int) // 10**6

            df["ohlc"] = df.apply(lambda row: {
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"]
            }, axis=1)

            return df.where(pd.notna(df), None)
        except Exception as e:
            logger.error(f"Error processing kline data: {e}")
            return df

    def get_current_kline(self, instrument_id, bar):
        """获取当前未完结的K线数据"""
        endpoint = "/api/v5/market/candles"
        params = {"instId": instrument_id, "bar": bar, "limit": 1}
        headers = self._get_headers("GET", endpoint, "")
        
        try:
            logger.info(f"Fetching current k-line for {instrument_id} at {bar}...")
            response = self.session.get(f"{self.base_url}{endpoint}", 
                                     headers=headers, 
                                     params=params)
            response.raise_for_status()
            data = response.json().get("data", [])
            
            if data:
                columns = ["timestamp", "open", "high", "low", "close", "volume", 
                          "currency_volume", "turnover", "trades"]
                df = pd.DataFrame([data[0]], columns=columns)
                df = self._process_kline_data(df)
                funding_data = self.fetch_funding_rate(instrument_id)
                df["funding_rate"] = funding_data.get("funding_rate", 0)
                df["is_closed"] = False
                logger.info("Successfully fetched current k-line.")
                return df
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching current kline: {e}")
            return pd.DataFrame()

    def fetch_market_tickers(self, instrument_id):
        """获取市场数据"""
        endpoint = "/api/v5/market/ticker"
        params = {"instId": instrument_id}
        headers = self._get_headers("GET", endpoint, "")
        try:
            logger.info(f"Fetching market tickers for {instrument_id}...")
            response = self.session.get(f"{self.base_url}{endpoint}", 
                                     headers=headers, 
                                     params=params)
            response.raise_for_status()
            data = response.json().get("data", [])
            
            if data and len(data) > 0:
                ticker = data[0]
                funding_data = self.fetch_funding_rate(instrument_id)
                return {
                    "last_price": float(ticker.get("last") or 0),
                    "best_bid": float(ticker.get("bidPx") or 0),
                    "best_ask": float(ticker.get("askPx") or 0),
                    "24h_high": float(ticker.get("high24h") or 0),
                    "24h_low": float(ticker.get("low24h") or 0),
                    "24h_volume": float(ticker.get("vol24h") or 0),
                    "24h_turnover": float(ticker.get("volCcy24h") or 0),
                    "open_interest": float(ticker.get("openInt") or 0),
                    "funding_rate": funding_data.get("funding_rate", 0),
                    "next_funding_time": funding_data.get("next_funding_time", ""),
                    "estimated_rate": funding_data.get("estimated_rate", 0),
                    "timestamp": int(time.time() * 1000),
                    "time_iso": pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                }
            return {}
        except Exception as e:
            logger.error(f"Error fetching market tickers: {e}")
            return {}

    # 保持兼容性的方法
    def fetch_ticker(self, instrument_id):
        """保持与旧代码的兼容性"""
        return self.fetch_market_tickers(instrument_id)

    def fetch_kline_data(self, instrument_id, bar, is_mark_price=True, limit=100, before=None, after=None):
        if is_mark_price:
            return self.fetch_mark_price_kline(instrument_id, bar, limit, before, after)
        else:
            return self.fetch_actual_price_kline(instrument_id, bar, limit, before, after)

    def fetch_mark_price_kline(self, instrument_id, bar, limit=100, before=None, after=None):
        columns = ["timestamp", "open", "high", "low", "close", "volume", 
                  "currency_volume", "turnover", "trades"]
        return self._fetch_kline_data("/api/v5/market/mark-price-candles", 
                                    instrument_id, bar, limit, columns, before, after)

    def fetch_actual_price_kline(self, instrument_id, bar, limit=100, before=None, after=None):
        columns = ["timestamp", "open", "high", "low", "close", "volume", 
                  "currency_volume", "turnover", "trades"]
        df = self._fetch_kline_data("/api/v5/market/candles", instrument_id, bar, limit, columns, before, after)
        
        # 添加资金费率信息
        if not df.empty:
            funding_data = self.fetch_funding_rate(instrument_id)
            df["funding_rate"] = funding_data.get("funding_rate", 0)
        
        return df

    def fetch_history_kline(self, instrument_id, bar, limit=100, before=None, after=None):
        """
        获取历史K线数据 - 使用history-candles端点
        支持更大的数据量获取
        """
        columns = ["timestamp", "open", "high", "low", "close", "volume", 
                  "currency_volume", "turnover", "trades"]
        df = self._fetch_kline_data("/api/v5/market/history-candles", instrument_id, bar, limit, columns, before, after)
        
        # 添加资金费率信息
        if not df.empty:
            funding_data = self.fetch_funding_rate(instrument_id)
            df["funding_rate"] = funding_data.get("funding_rate", 0)
        
        return df

    def fetch_combined_kline_data(self, instrument_id, bar, target_limit=512):
        """
        组合获取K线数据：历史数据 + 最新数据
        突破单一端点的限制，获取更多数据
        
        Args:
            instrument_id: 交易对ID
            bar: 时间框架
            target_limit: 目标数据条数
            
        Returns:
            DataFrame: 合并后的K线数据
        """
        all_data = []
        total_records = 0
        
        logger.info(f"🔄 Combined fetch strategy for {instrument_id} {bar}, target: {target_limit}")
        
        try:
            # 策略1: 获取最新数据 (live candles - 最多300条)
            logger.info("📊 Step 1: Fetching latest data (live candles)")
            df_live = self.fetch_actual_price_kline(instrument_id, bar, limit=300)
            
            if not df_live.empty:
                all_data.append(df_live)
                total_records += len(df_live)
                logger.info(f"   ✅ Live data: {len(df_live)} records")
                
                # 如果需要更多数据，获取历史数据
                if total_records < target_limit:
                    needed_records = target_limit - total_records
                    earliest_time = df_live['timestamp'].min()
                    
                    logger.info(f"📊 Step 2: Fetching historical data (need {needed_records} more)")
                    logger.info(f"   Live data earliest time: {earliest_time}")
                    
                    # 分批获取历史数据 - 使用after参数策略
                    batch_count = 0
                    current_after = earliest_time  # 从live数据的最早时间开始
                    
                    while total_records < target_limit and batch_count < 5:
                        batch_count += 1
                        batch_limit = min(300, needed_records)
                        
                        # 关键修复：使用after参数获取更早的历史数据
                        df_history = self.fetch_history_kline(
                            instrument_id, bar, 
                            limit=batch_limit,
                            after=current_after  # 获取current_after之前的数据
                        )
                        
                        if not df_history.empty:
                            # 调试信息：显示时间戳范围
                            hist_min = df_history['timestamp'].min()
                            hist_max = df_history['timestamp'].max()
                            logger.info(f"   📅 History batch {batch_count} raw: {len(df_history)} records")
                            logger.info(f"      Time range: {hist_min} to {hist_max}")
                            logger.info(f"      Current after: {current_after}")
                            
                            # 检查是否与已有数据重复
                            existing_timestamps = set()
                            for existing_df in all_data:
                                existing_timestamps.update(existing_df['timestamp'].tolist())
                            
                            # 过滤已存在的时间戳
                            df_history_final = df_history[
                                ~df_history['timestamp'].isin(existing_timestamps)
                            ]
                            
                            logger.info(f"   📊 After deduplication: {len(df_history_final)} records")
                            
                            if not df_history_final.empty:
                                all_data.insert(0, df_history_final)  # 插入到前面
                                total_records += len(df_history_final)
                                needed_records = target_limit - total_records
                                logger.info(f"   ✅ History batch {batch_count}: {len(df_history_final)} records added")
                                logger.info(f"      Total so far: {total_records}/{target_limit}")
                                
                                # 更新current_after为这批数据的最早时间，继续向前获取
                                current_after = df_history_final['timestamp'].min()
                                logger.info(f"      Next after: {current_after}")
                            else:
                                logger.info(f"   ⚠️ History batch {batch_count}: All data already exists")
                                break
                        else:
                            logger.info(f"   ⚠️ History batch {batch_count}: Empty response")
                            break
            
            # 合并所有数据
            if all_data:
                combined_df = pd.concat(all_data, ignore_index=True)
                combined_df = combined_df.sort_values('timestamp').drop_duplicates(subset=['timestamp'])
                
                # 取最新的target_limit条数据
                if len(combined_df) > target_limit:
                    combined_df = combined_df.tail(target_limit)
                
                logger.info(f"🎯 Combined result: {len(combined_df)} records (target: {target_limit})")
                return combined_df
            else:
                logger.warning("❌ No data obtained from any strategy")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"❌ Combined fetch failed: {e}")
            return pd.DataFrame()

    def _fetch_kline_data(self, endpoint, instrument_id, bar, limit, columns, before=None, after=None):
        params = {"instId": instrument_id, "bar": bar, "limit": limit}
        
        # 添加时间范围参数
        if before is not None:
            params["before"] = str(int(before))
        if after is not None:
            params["after"] = str(int(after))
            
        headers = self._get_headers("GET", endpoint, "")
        try:
            param_info = f"({limit} points)"
            if before:
                param_info += f" before {before}"
            if after:
                param_info += f" after {after}"
                
            logger.info(f"Fetching K-line data from {endpoint} {param_info} for {instrument_id} at {bar}...")
            response = self.session.get(self.base_url + endpoint, headers=headers, params=params)
            response.raise_for_status()
            raw_data = response.json().get("data", [])

            if not raw_data:
                logger.warning("No K-line data returned.")
                return pd.DataFrame()

            if len(raw_data[0]) != len(columns):
                logger.warning(f"Column mismatch. Adjusting...")
                columns = columns[:len(raw_data[0])]

            df = pd.DataFrame(raw_data, columns=columns)
            df = self._process_kline_data(df)
            df["is_closed"] = True
            
            logger.info(f"Fetched {len(df)} K-line data.")
            return df

        except Exception as e:
            logger.error(f"Error fetching K-line data: {e}", exc_info=True)
            return pd.DataFrame()