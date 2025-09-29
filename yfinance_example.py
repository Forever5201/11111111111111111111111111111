
# 使用yfinance获取BTC历史数据示例
import yfinance as yf
import pandas as pd

# 获取BTC-USD数据
ticker = yf.Ticker("BTC-USD")
hist = ticker.history(start="2021-01-01", end="2025-09-28", interval="1d")

# 转换为Kronos格式
df_kronos = pd.DataFrame()
df_kronos['open'] = hist['Open']
df_kronos['high'] = hist['High'] 
df_kronos['low'] = hist['Low']
df_kronos['close'] = hist['Close']
df_kronos['vol'] = hist['Volume']
df_kronos['amt'] = hist['Volume'] * hist['Close']  # 估算成交额

# 保存
df_kronos.to_pickle("btc_historical_1d.pkl")
print(f"保存了 {len(df_kronos)} 条1D记录")
