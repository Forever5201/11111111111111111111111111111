#!/usr/bin/env python3
"""
测试OKX数据到Kronos格式转换的集成脚本
"""

import os
import pickle
import pandas as pd
from pathlib import Path

def test_kronos_data_format():
    """测试生成的Kronos数据格式是否正确"""
    
    print("🔍 测试Kronos数据格式...")
    print("=" * 50)
    
    data_dir = Path("data/kronos_datasets")
    
    if not data_dir.exists():
        print("❌ 数据目录不存在: data/kronos_datasets/")
        print("请先运行: python src/get_data.py --kronos")
        return False
    
    # 检查必需文件
    required_files = ['train_data.pkl', 'val_data.pkl', 'test_data.pkl']
    missing_files = []
    
    for file in required_files:
        if not (data_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 缺少文件: {missing_files}")
        return False
    
    print("✅ 所有必需文件存在")
    
    # 测试数据格式
    try:
        all_passed = True
        
        for file in required_files:
            print(f"\n📁 检查 {file}...")
            
            with open(data_dir / file, 'rb') as f:
                data = pickle.load(f)
            
            if not isinstance(data, dict):
                print(f"❌ {file}: 数据不是字典格式")
                all_passed = False
                continue
            
            print(f"✅ {file}: 字典格式正确，包含 {len(data)} 个symbols")
            
            # 检查每个symbol的数据
            for symbol, df in data.items():
                print(f"   📊 {symbol}:")
                
                # 检查是否是DataFrame
                if not isinstance(df, pd.DataFrame):
                    print(f"      ❌ 不是DataFrame格式")
                    all_passed = False
                    continue
                
                # 检查必需列
                required_cols = ['open', 'high', 'low', 'close', 'vol', 'amt']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    print(f"      ❌ 缺少列: {missing_cols}")
                    all_passed = False
                else:
                    print(f"      ✅ 所有必需列存在: {required_cols}")
                
                # 检查索引
                if not isinstance(df.index, pd.DatetimeIndex):
                    print(f"      ❌ 索引不是DatetimeIndex: {type(df.index)}")
                    all_passed = False
                else:
                    print(f"      ✅ DatetimeIndex正确")
                    print(f"      📅 时间范围: {df.index.min()} 到 {df.index.max()}")
                
                # 检查数据量
                print(f"      📈 记录数: {len(df)}")
                
                # 检查数据类型
                numeric_cols = ['open', 'high', 'low', 'close', 'vol', 'amt']
                for col in numeric_cols:
                    if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
                        print(f"      ⚠️ 列 {col} 不是数值类型: {df[col].dtype}")
                
                # 检查缺失值
                null_counts = df.isnull().sum()
                if null_counts.any():
                    print(f"      ⚠️ 存在缺失值: {dict(null_counts[null_counts > 0])}")
                else:
                    print(f"      ✅ 无缺失值")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        return False

def show_data_summary():
    """显示数据摘要"""
    
    summary_file = Path("data/kronos_datasets/dataset_summary.json")
    
    if summary_file.exists():
        import json
        print("\n📊 数据集摘要:")
        print("-" * 30)
        
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary = json.load(f)
        
        for key, value in summary.items():
            if key == 'symbols':
                print(f"{key}: {len(value)} 个交易对时间框架")
                for symbol in value:
                    print(f"  - {symbol}")
            else:
                print(f"{key}: {value}")

def check_kronos_compatibility():
    """检查与Kronos的兼容性"""
    
    print("\n🔗 检查Kronos兼容性...")
    print("-" * 30)
    
    # 检查Kronos目录
    kronos_dir = Path("Kronos")
    if not kronos_dir.exists():
        print("⚠️ Kronos目录不存在")
        return False
    
    # 检查Kronos数据目录
    kronos_data_dir = kronos_dir / "finetune" / "data"
    if not kronos_data_dir.exists():
        print(f"📁 创建Kronos数据目录: {kronos_data_dir}")
        kronos_data_dir.mkdir(parents=True, exist_ok=True)
    
    # 检查是否可以复制文件
    source_dir = Path("data/kronos_datasets")
    if source_dir.exists():
        print("✅ 可以复制数据到Kronos目录")
        print(f"执行命令: cp {source_dir}/*.pkl {kronos_data_dir}/")
    else:
        print("❌ 源数据目录不存在")
        return False
    
    return True

def main():
    print("🧪 OKX到Kronos数据转换测试")
    print("=" * 50)
    
    # 测试数据格式
    format_ok = test_kronos_data_format()
    
    # 显示摘要
    show_data_summary()
    
    # 检查兼容性
    compat_ok = check_kronos_compatibility()
    
    print("\n" + "=" * 50)
    if format_ok and compat_ok:
        print("🎉 所有测试通过！")
        print("📋 下一步操作:")
        print("1. 复制数据到Kronos: cp data/kronos_datasets/*.pkl Kronos/finetune/data/")
        print("2. 配置Kronos: 编辑 Kronos/finetune/config.py")
        print("3. 开始微调: cd Kronos && python finetune/train_tokenizer.py")
        return True
    else:
        print("❌ 部分测试失败，请检查上述错误信息")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
