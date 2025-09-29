#!/usr/bin/env python3
"""
Kronos Tokenizer训练状态监控脚本
用于监控模型A (4H) Tokenizer的训练进度
"""

import os
import time
import json
from datetime import datetime

def monitor_training_progress():
    """监控训练进度"""
    
    # 训练输出目录
    model_dir = "./Kronos/finetune/outputs/models/model_a_4h/tokenizer_model_a_4h"
    checkpoints_dir = os.path.join(model_dir, "checkpoints")
    
    print("🔍 Kronos Tokenizer (Model A - 4H) 训练监控")
    print("=" * 60)
    
    while True:
        try:
            # 检查是否有checkpoint文件
            if os.path.exists(checkpoints_dir):
                checkpoints = [f for f in os.listdir(checkpoints_dir) if f.startswith('epoch_')]
                if checkpoints:
                    latest_checkpoint = max(checkpoints, key=lambda x: int(x.split('_')[1]))
                    print(f"📊 最新checkpoint: {latest_checkpoint}")
                    
                    # 检查best_model
                    best_model_path = os.path.join(checkpoints_dir, "best_model")
                    if os.path.exists(best_model_path):
                        print(f"✅ 最佳模型已保存: {best_model_path}")
                        
                        # 尝试读取训练日志
                        log_file = os.path.join(model_dir, "training_log.txt")
                        if os.path.exists(log_file):
                            with open(log_file, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                                if lines:
                                    print(f"📝 最新日志: {lines[-1].strip()}")
                else:
                    print("⏳ 等待训练开始...")
            else:
                print("⏳ 训练尚未开始，等待输出目录创建...")
            
            # 检查GPU使用情况
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                    gpu_used = torch.cuda.memory_allocated(0) / 1024**3
                    print(f"🖥️  GPU内存使用: {gpu_used:.1f}GB / {gpu_memory:.1f}GB")
            except:
                pass
            
            print(f"🕒 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 60)
            
            # 等待30秒后再次检查
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n👋 监控已停止")
            break
        except Exception as e:
            print(f"❌ 监控错误: {e}")
            time.sleep(10)

def check_training_status():
    """快速检查训练状态"""
    model_dir = "./Kronos/finetune/outputs/models/model_a_4h/tokenizer_model_a_4h"
    checkpoints_dir = os.path.join(model_dir, "checkpoints")
    
    print("🔍 快速状态检查")
    print("=" * 40)
    
    if os.path.exists(model_dir):
        print(f"✅ 训练目录存在: {model_dir}")
        
        if os.path.exists(checkpoints_dir):
            checkpoints = [f for f in os.listdir(checkpoints_dir) if f.startswith('epoch_')]
            print(f"📊 Checkpoint数量: {len(checkpoints)}")
            
            if checkpoints:
                latest = max(checkpoints, key=lambda x: int(x.split('_')[1]))
                epoch_num = latest.split('_')[1]
                print(f"📈 最新epoch: {epoch_num}")
            
            best_model_path = os.path.join(checkpoints_dir, "best_model")
            if os.path.exists(best_model_path):
                print("✅ 最佳模型已保存")
            else:
                print("⏳ 最佳模型尚未保存")
        else:
            print("⏳ Checkpoints目录不存在")
    else:
        print("❌ 训练目录不存在")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        check_training_status()
    else:
        print("使用方法:")
        print("  python monitor_tokenizer_training.py          # 持续监控")
        print("  python monitor_tokenizer_training.py --quick  # 快速检查")
        print()
        
        choice = input("选择模式 (1=持续监控, 2=快速检查): ").strip()
        if choice == "1":
            monitor_training_progress()
        elif choice == "2":
            check_training_status()
        else:
            print("无效选择")