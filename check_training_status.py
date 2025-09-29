#!/usr/bin/env python3
"""
检查Kronos训练状态
"""

import os
import sys
import time
import psutil
from pathlib import Path
from datetime import datetime

def check_training_processes():
    """检查训练进程"""
    print("🔍 检查训练进程...")
    
    training_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'train_tokenizer.py' in cmdline or 'train_predictor.py' in cmdline:
                training_processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cmdline': cmdline,
                    'create_time': datetime.fromtimestamp(proc.create_time())
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if training_processes:
        print(f"✅ 发现 {len(training_processes)} 个训练进程:")
        for proc in training_processes:
            print(f"   PID {proc['pid']}: {proc['name']}")
            print(f"   启动时间: {proc['create_time']}")
            print(f"   命令: {proc['cmdline'][:80]}...")
    else:
        print("❌ 未发现训练进程")
    
    return training_processes

def check_output_directories():
    """检查输出目录"""
    print("\n📁 检查输出目录...")
    
    # 检查模型A的输出目录
    model_a_path = Path("outputs/models/model_a_4h")
    if model_a_path.exists():
        print(f"✅ 模型A输出目录存在: {model_a_path}")
        
        # 检查tokenizer目录
        tokenizer_path = model_a_path / "tokenizer_model_a_4h"
        if tokenizer_path.exists():
            print(f"   📂 Tokenizer目录: {tokenizer_path}")
            
            # 检查checkpoints
            checkpoints_path = tokenizer_path / "checkpoints"
            if checkpoints_path.exists():
                checkpoints = list(checkpoints_path.iterdir())
                print(f"   💾 检查点: {len(checkpoints)} 个")
                for cp in checkpoints:
                    print(f"      - {cp.name}")
        else:
            print("   ⏳ Tokenizer目录尚未创建")
    else:
        print(f"⏳ 模型A输出目录尚未创建: {model_a_path}")

def check_data_preparation():
    """检查数据准备情况"""
    print("\n📊 检查数据准备...")
    
    data_dir = Path("data")
    if data_dir.exists():
        print(f"✅ 数据目录存在: {data_dir}")
        
        # 检查训练数据
        for file in ['train_data.pkl', 'val_data.pkl', 'test_data.pkl']:
            file_path = data_dir / file
            if file_path.exists():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                print(f"   📄 {file}: {size_mb:.2f} MB")
            else:
                print(f"   ❌ {file}: 不存在")
    else:
        print(f"❌ 数据目录不存在: {data_dir}")

def show_training_commands():
    """显示训练相关命令"""
    print("\n📋 训练相关命令:")
    print("查看GPU使用情况:")
    print("   nvidia-smi")
    print("\n检查训练日志:")
    print("   # 如果配置了Comet ML，可以在网页查看")
    print("   # 或查看控制台输出")
    print("\n停止训练 (如果需要):")
    print("   # 找到训练进程PID并终止")
    print("   # 或使用 Ctrl+C")

def main():
    """主函数"""
    print("🎯 Kronos训练状态检查")
    print("=" * 50)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查训练进程
    processes = check_training_processes()
    
    # 检查输出目录
    check_output_directories()
    
    # 检查数据准备
    check_data_preparation()
    
    # 显示相关命令
    show_training_commands()
    
    if processes:
        print(f"\n🎉 模型A (4H) Tokenizer训练正在进行中！")
        print(f"📊 训练配置: 4H时间框架，10,381条历史记录")
        print(f"⏱️ 预计训练时间: 根据配置为30个epochs")
    else:
        print(f"\n⚠️ 未检测到活跃的训练进程")
        print(f"💡 如需开始训练，请运行:")
        print(f"   torchrun --standalone --nproc_per_node=1 train_tokenizer.py --config model_a_4h")

if __name__ == "__main__":
    main()








