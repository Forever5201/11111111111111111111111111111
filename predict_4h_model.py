#!/usr/bin/env python3
"""
Kronos 4H模型预测脚本
使用训练好的4H时间框架模型进行价格预测
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 添加Kronos模型路径
sys.path.append("./Kronos/")
from model import Kronos, KronosTokenizer, KronosPredictor


class Kronos4HPredictor:
    def __init__(self):
        """初始化4H预测器"""
        self.tokenizer_path = "./Kronos/finetune/outputs/models/model_a_4h/tokenizer_model_a_4h/checkpoints/best_model"
        self.predictor_path = "./Kronos/finetune/outputs/models/model_a_4h/predictor_model_a_4h/checkpoints/best_model"
        
        # 预测参数（基于配置文件）
        self.lookback_window = 90  # 历史窗口：90个4H周期
        self.predict_window = 10   # 预测窗口：10个4H周期
        self.max_context = 512     # 最大上下文长度
        
        # 初始化模型
        self.tokenizer = None
        self.model = None
        self.predictor = None
        
    def load_models(self):
        """加载训练好的模型"""
        print("🔄 正在加载训练好的4H模型...")
        
        try:
            # 加载tokenizer
            print(f"📁 加载tokenizer: {self.tokenizer_path}")
            self.tokenizer = KronosTokenizer.from_pretrained(self.tokenizer_path)
            
            # 加载predictor模型
            print(f"📁 加载predictor: {self.predictor_path}")
            self.model = Kronos.from_pretrained(self.predictor_path)
            
            # 创建预测器
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
            print(f"🖥️  使用设备: {device}")
            self.predictor = KronosPredictor(
                self.model, 
                self.tokenizer, 
                device=device, 
                max_context=self.max_context
            )
            
            print("✅ 模型加载成功！")
            return True
            
        except Exception as e:
            print(f"❌ 模型加载失败: {str(e)}")
            return False
    
    def fetch_4h_data(self, symbol="BTC-USD", periods=200):
        """
        获取4H线数据
        
        Args:
            symbol: 交易对符号
            periods: 需要的4H周期数量（默认200，确保有足够的历史数据）
        
        Returns:
            DataFrame: 4H线数据
        """
        print(f"📊 正在获取 {symbol} 的4H线数据...")
        
        try:
            # 计算需要的时间范围（4H * periods）
            end_date = datetime.now()
            # 4小时 * periods + 一些缓冲时间
            start_date = end_date - timedelta(hours=4 * periods * 1.5)
            
            # 获取1小时数据，然后重采样为4小时
            ticker = yf.Ticker(symbol)
            data = ticker.history(
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                interval='1h'
            )
            
            if data.empty:
                raise ValueError(f"无法获取 {symbol} 的数据")
            
            # 重采样为4小时数据
            data_4h = data.resample('4H').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()
            
            # 重命名列以匹配Kronos格式
            data_4h = data_4h.rename(columns={
                'Open': 'open',
                'High': 'high', 
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # 添加amount列（简化计算）
            data_4h['amount'] = data_4h['close'] * data_4h['volume']
            
            # 添加时间戳
            data_4h['timestamps'] = data_4h.index
            
            print(f"✅ 成功获取 {len(data_4h)} 条4H线数据")
            print(f"📅 时间范围: {data_4h.index[0]} 到 {data_4h.index[-1]}")
            
            return data_4h
            
        except Exception as e:
            print(f"❌ 数据获取失败: {str(e)}")
            return None
    
    def prepare_prediction_data(self, df):
        """
        准备预测数据
        
        Args:
            df: 4H线数据DataFrame
            
        Returns:
            tuple: (输入数据, 输入时间戳, 预测时间戳)
        """
        if len(df) < self.lookback_window:
            raise ValueError(f"数据不足！需要至少 {self.lookback_window} 条4H线数据，当前只有 {len(df)} 条")
        
        # 使用最近的lookback_window条数据作为输入
        x_df = df.iloc[-self.lookback_window:][['open', 'high', 'low', 'close', 'volume', 'amount']].copy()
        x_timestamp = df.iloc[-self.lookback_window:]['timestamps'].copy()
        
        # 生成未来的时间戳（每4小时一个）
        last_timestamp = df.index[-1]
        future_timestamps = []
        for i in range(1, self.predict_window + 1):
            future_time = last_timestamp + timedelta(hours=4 * i)
            future_timestamps.append(future_time)
        
        y_timestamp = pd.Series(future_timestamps)
        
        print(f"📊 输入数据: {len(x_df)} 条4H线")
        print(f"🔮 预测周期: {self.predict_window} 个4H周期 ({self.predict_window * 4} 小时)")
        print(f"📅 预测时间范围: {future_timestamps[0]} 到 {future_timestamps[-1]}")
        
        return x_df, x_timestamp, y_timestamp
    
    def make_prediction(self, x_df, x_timestamp, y_timestamp):
        """
        执行预测
        
        Args:
            x_df: 输入数据
            x_timestamp: 输入时间戳
            y_timestamp: 预测时间戳
            
        Returns:
            DataFrame: 预测结果
        """
        print("🔮 正在进行4H线预测...")
        
        try:
            pred_df = self.predictor.predict(
                df=x_df,
                x_timestamp=x_timestamp,
                y_timestamp=y_timestamp,
                pred_len=self.predict_window,
                T=1.0,          # 温度参数
                top_p=0.9,      # Top-p采样
                sample_count=1, # 采样次数
                verbose=True
            )
            
            print("✅ 预测完成！")
            return pred_df
            
        except Exception as e:
            print(f"❌ 预测失败: {str(e)}")
            return None
    
    def plot_prediction(self, historical_df, pred_df, save_path=None):
        """
        绘制预测结果
        
        Args:
            historical_df: 历史数据
            pred_df: 预测数据
            save_path: 保存路径（可选）
        """
        # 设置预测数据的索引
        pred_df.index = pd.date_range(
            start=historical_df.index[-1] + timedelta(hours=4),
            periods=len(pred_df),
            freq='4H'
        )
        
        # 准备绘图数据
        hist_close = historical_df['close'].iloc[-50:]  # 显示最近50个4H周期
        pred_close = pred_df['close']
        
        hist_volume = historical_df['volume'].iloc[-50:]
        pred_volume = pred_df['volume']
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
        
        # 价格图
        ax1.plot(hist_close.index, hist_close.values, label='历史价格', color='blue', linewidth=2)
        ax1.plot(pred_close.index, pred_close.values, label='预测价格', color='red', linewidth=2, linestyle='--')
        ax1.axvline(x=historical_df.index[-1], color='gray', linestyle=':', alpha=0.7, label='预测起点')
        ax1.set_ylabel('价格 (USD)', fontsize=12)
        ax1.set_title('Kronos 4H模型 - 价格预测', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 成交量图
        ax2.plot(hist_volume.index, hist_volume.values, label='历史成交量', color='blue', linewidth=2)
        ax2.plot(pred_volume.index, pred_volume.values, label='预测成交量', color='red', linewidth=2, linestyle='--')
        ax2.axvline(x=historical_df.index[-1], color='gray', linestyle=':', alpha=0.7, label='预测起点')
        ax2.set_ylabel('成交量', fontsize=12)
        ax2.set_xlabel('时间', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 图表已保存到: {save_path}")
        
        plt.show()
    
    def run_prediction(self, symbol="BTC-USD", save_results=True):
        """
        运行完整的预测流程
        
        Args:
            symbol: 交易对符号
            save_results: 是否保存结果
        """
        print("🚀 开始Kronos 4H模型预测流程...")
        print("=" * 60)
        
        # 1. 加载模型
        if not self.load_models():
            return None
        
        # 2. 获取数据
        df = self.fetch_4h_data(symbol, periods=200)
        if df is None:
            return None
        
        # 3. 准备预测数据
        try:
            x_df, x_timestamp, y_timestamp = self.prepare_prediction_data(df)
        except ValueError as e:
            print(f"❌ {str(e)}")
            return None
        
        # 4. 执行预测
        pred_df = self.make_prediction(x_df, x_timestamp, y_timestamp)
        if pred_df is None:
            return None
        
        # 5. 显示结果
        print("\n📊 预测结果摘要:")
        print("=" * 40)
        print(pred_df.head())
        
        current_price = df['close'].iloc[-1]
        predicted_price = pred_df['close'].iloc[-1]
        price_change = ((predicted_price - current_price) / current_price) * 100
        
        print(f"\n💰 价格分析:")
        print(f"   当前价格: ${current_price:.2f}")
        print(f"   预测价格: ${predicted_price:.2f} (40小时后)")
        print(f"   预期变化: {price_change:+.2f}%")
        
        # 6. 绘制图表
        if save_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plot_path = f"./prediction_results_4h_{symbol}_{timestamp}.png"
            self.plot_prediction(df, pred_df, plot_path)
        else:
            self.plot_prediction(df, pred_df)
        
        # 7. 保存预测数据
        if save_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = f"./prediction_data_4h_{symbol}_{timestamp}.csv"
            pred_df.to_csv(csv_path)
            print(f"💾 预测数据已保存到: {csv_path}")
        
        print("\n✅ 预测流程完成！")
        return pred_df


def main():
    """主函数"""
    import torch
    
    print("🎯 Kronos 4H模型预测系统")
    print("=" * 60)
    
    # 创建预测器
    predictor = Kronos4HPredictor()
    
    # 运行预测（默认BTC-USD）
    results = predictor.run_prediction(symbol="BTC-USD", save_results=True)
    
    if results is not None:
        print("\n🎉 预测成功完成！")
        print("\n💡 使用建议:")
        print("   - 4H模型适合中短期交易决策")
        print("   - 建议结合技术分析和风险管理")
        print("   - 预测结果仅供参考，投资需谨慎")
    else:
        print("\n❌ 预测失败，请检查模型文件和数据连接")


if __name__ == "__main__":
    main()