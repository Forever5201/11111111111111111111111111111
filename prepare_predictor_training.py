#!/usr/bin/env python3
"""
模型A (4H) Predictor训练准备脚本
在Tokenizer训练完成后，准备Predictor的训练
"""

import os
import sys
import time
from datetime import datetime

def check_tokenizer_completion():
    """检查Tokenizer训练是否完成"""
    tokenizer_dir = "./Kronos/finetune/outputs/models/model_a_4h/tokenizer_model_a_4h"
    checkpoints_dir = os.path.join(tokenizer_dir, "checkpoints")
    best_model_path = os.path.join(checkpoints_dir, "best_model")
    
    print("🔍 检查Tokenizer训练状态...")
    
    if os.path.exists(best_model_path):
        print("✅ Tokenizer训练已完成，最佳模型已保存")
        return True
    else:
        print("⏳ Tokenizer训练尚未完成")
        return False

def prepare_predictor_training():
    """准备Predictor训练"""
    print("\n🚀 准备Predictor训练...")
    
    # 检查配置文件
    config_file = "./Kronos/finetune/config_model_A_4H.py"
    if os.path.exists(config_file):
        print("✅ 配置文件存在")
    else:
        print("❌ 配置文件不存在")
        return False
    
    # 检查数据集
    dataset_path = "./data/kronos_datasets/model_a_4h_full"
    if os.path.exists(dataset_path):
        print("✅ 数据集存在")
        
        # 检查数据文件
        required_files = ["train_data.pkl", "val_data.pkl", "test_data.pkl"]
        for file in required_files:
            file_path = os.path.join(dataset_path, file)
            if os.path.exists(file_path):
                print(f"  ✅ {file}")
            else:
                print(f"  ❌ {file} 缺失")
                return False
    else:
        print("❌ 数据集不存在")
        return False
    
    # 检查训练脚本
    predictor_script = "./Kronos/finetune/train_predictor.py"
    if os.path.exists(predictor_script):
        print("✅ Predictor训练脚本存在")
    else:
        print("❌ Predictor训练脚本不存在")
        return False
    
    print("\n✅ Predictor训练准备完成！")
    return True

def show_next_steps():
    """显示下一步操作"""
    print("\n📋 下一步操作指南：")
    print("=" * 50)
    print("1. 等待Tokenizer训练完成（约30个epochs）")
    print("2. 运行Predictor训练：")
    print("   cd Kronos/finetune")
    print("   python train_predictor.py --config model_a_4h")
    print("3. 监控训练进度")
    print("4. 验证模型性能")
    print("\n💡 提示：")
    print("- Tokenizer训练通常需要20-30分钟")
    print("- Predictor训练可能需要1-2小时")
    print("- 可以使用monitor_tokenizer_training.py监控进度")

def estimate_completion_time():
    """估算完成时间"""
    tokenizer_dir = "./Kronos/finetune/outputs/models/model_a_4h/tokenizer_model_a_4h"
    checkpoints_dir = os.path.join(tokenizer_dir, "checkpoints")
    
    if os.path.exists(checkpoints_dir):
        checkpoints = [f for f in os.listdir(checkpoints_dir) if f.startswith('epoch_')]
        if checkpoints:
            latest_checkpoint = max(checkpoints, key=lambda x: int(x.split('_')[1]))
            current_epoch = int(latest_checkpoint.split('_')[1])
            total_epochs = 30
            
            # 假设每个epoch 15秒
            remaining_epochs = total_epochs - current_epoch
            estimated_minutes = (remaining_epochs * 15) / 60
            
            print(f"\n⏱️  训练进度估算：")
            print(f"   当前epoch: {current_epoch}/{total_epochs}")
            print(f"   剩余时间: 约{estimated_minutes:.1f}分钟")
            
            return estimated_minutes
    
    return None

def main():
    """主函数"""
    print("🔧 模型A (4H) Predictor训练准备")
    print("=" * 50)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查Tokenizer状态
    tokenizer_ready = check_tokenizer_completion()
    
    if tokenizer_ready:
        # Tokenizer完成，准备Predictor训练
        predictor_ready = prepare_predictor_training()
        if predictor_ready:
            print("\n🎉 可以开始Predictor训练了！")
            show_next_steps()
        else:
            print("\n❌ Predictor训练准备失败")
    else:
        # Tokenizer还在训练中
        estimate_completion_time()
        print("\n⏳ 请等待Tokenizer训练完成...")
        show_next_steps()

if __name__ == "__main__":
    main()