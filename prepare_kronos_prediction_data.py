#!/usr/bin/env python3
"""
Kronos实时预测数据准备脚本
获取最新512条K线数据，用于Kronos模型预测

用法:
  python prepare_kronos_prediction_data.py --timeframes 4H 1D
  python prepare_kronos_prediction_data.py --timeframes 4H --output-dir ./custom_data
  python prepare_kronos_prediction_data.py --all  # 获取所有配置的时间框架
"""

import os
import sys
import argparse
from datetime import datetime

# 添加src目录到路径
sys.path.append("./src")

from get_data import fetch_kronos_prediction_data, save_kronos_prediction_data
from config_loader import ConfigLoader
from logger import setup_logger

logger = setup_logger()

def create_argument_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='Kronos实时预测数据准备工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  %(prog)s --timeframes 4H 1D
  %(prog)s --timeframes 4H --output-dir ./prediction_data
  %(prog)s --all
  %(prog)s --timeframes 4H --run-prediction
'''
    )
    
    parser.add_argument(
        '--timeframes',
        nargs='+',
        help='指定时间框架 (如: 4H 1D)',
        default=None
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='获取配置文件中所有Kronos预测时间框架的数据'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default="./Kronos/finetune/data",
        help='输出目录 (默认: ./Kronos/finetune/data)'
    )
    
    parser.add_argument(
        '--run-prediction',
        action='store_true',
        help='获取数据后立即运行4H模型预测'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default="./config/config.yaml",
        help='配置文件路径 (默认: ./config/config.yaml)'
    )
    
    return parser

def run_4h_prediction():
    """运行4H模型预测"""
    try:
        logger.info("🚀 Starting 4H model prediction...")
        
        # 检查预测脚本是否存在
        prediction_script = "./predict_4h_model.py"
        if not os.path.exists(prediction_script):
            logger.error(f"Prediction script not found: {prediction_script}")
            return False
        
        # 运行预测脚本
        import subprocess
        result = subprocess.run([sys.executable, prediction_script], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ 4H model prediction completed successfully")
            logger.info("Prediction output:")
            print(result.stdout)
            return True
        else:
            logger.error("❌ 4H model prediction failed")
            logger.error("Error output:")
            print(result.stderr)
            return False
            
    except Exception as e:
        logger.error(f"Error running 4H prediction: {e}")
        return False

def main():
    """主函数"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    logger.info("🎯 Kronos实时预测数据准备工具")
    logger.info("=" * 60)
    
    # 加载配置
    try:
        config_loader = ConfigLoader(args.config)
        config = config_loader.load_config()
        logger.info(f"✅ Configuration loaded from {args.config}")
    except Exception as e:
        logger.error(f"❌ Error loading configuration: {e}")
        return False
    
    # 确定要处理的时间框架
    if args.all:
        timeframes = config.get('timeframes', {}).get('kronos_prediction', ['4H', '1D'])
        logger.info(f"🔧 Using all configured timeframes: {timeframes}")
    elif args.timeframes:
        timeframes = args.timeframes
        logger.info(f"🔧 Using specified timeframes: {timeframes}")
    else:
        timeframes = ['4H']  # 默认使用4H
        logger.info(f"🔧 Using default timeframe: {timeframes}")
    
    # 验证时间框架配置
    kronos_prediction_config = config.get('kronos_prediction_config', {})
    valid_timeframes = []
    for tf in timeframes:
        if tf in kronos_prediction_config:
            valid_timeframes.append(tf)
        else:
            logger.warning(f"⚠️  Timeframe {tf} not configured in kronos_prediction_config")
    
    if not valid_timeframes:
        logger.error("❌ No valid timeframes found in configuration")
        return False
    
    timeframes = valid_timeframes
    logger.info(f"📊 Processing timeframes: {timeframes}")
    
    # 获取预测数据
    logger.info("\n🔄 Fetching latest 512 K-line data...")
    prediction_data = fetch_kronos_prediction_data(config, timeframes)
    
    if not prediction_data:
        logger.error("❌ Failed to fetch prediction data")
        return False
    
    # 显示获取结果
    logger.info("\n📈 Data fetch summary:")
    for tf, df in prediction_data.items():
        logger.info(f"   {tf}: {len(df)} records")
        logger.info(f"      Time range: {df.index[0]} to {df.index[-1]}")
    
    # 保存数据
    logger.info(f"\n💾 Saving data to {args.output_dir}...")
    save_kronos_prediction_data(prediction_data, args.output_dir)
    
    # 运行预测（如果指定）
    if args.run_prediction and '4H' in prediction_data:
        logger.info("\n🔮 Running 4H model prediction...")
        prediction_success = run_4h_prediction()
        if not prediction_success:
            logger.warning("⚠️  Prediction failed, but data preparation was successful")
    
    logger.info("\n✅ Kronos prediction data preparation completed!")
    logger.info("\n💡 Next steps:")
    logger.info("   1. 数据已保存到指定目录")
    logger.info("   2. 可以运行 python predict_4h_model.py 进行预测")
    logger.info("   3. 或使用 --run-prediction 参数自动运行预测")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)