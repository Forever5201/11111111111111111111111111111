#!/usr/bin/env python3
"""
模型A (4H) 完整微调流程脚本
自动化执行Tokenizer和Predictor的完整训练流程
"""

import os
import sys
import time
import subprocess
from datetime import datetime

class ModelATrainingPipeline:
    def __init__(self):
        self.config_name = "model_a_4h"
        self.finetune_dir = "./Kronos/finetune"
        self.tokenizer_dir = "./Kronos/finetune/outputs/models/model_a_4h/tokenizer_model_a_4h"
        self.predictor_dir = "./Kronos/finetune/outputs/models/model_a_4h/predictor_model_a_4h"
        
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {message}")
        
    def check_tokenizer_status(self):
        """检查Tokenizer训练状态"""
        checkpoints_dir = os.path.join(self.tokenizer_dir, "checkpoints")
        best_model_path = os.path.join(checkpoints_dir, "best_model")
        
        if os.path.exists(best_model_path):
            self.log("✅ Tokenizer训练已完成")
            return "completed"
        elif os.path.exists(checkpoints_dir):
            checkpoints = [f for f in os.listdir(checkpoints_dir) if f.startswith('epoch_')]
            if checkpoints:
                latest = max(checkpoints, key=lambda x: int(x.split('_')[1]))
                epoch_num = int(latest.split('_')[1])
                self.log(f"🔄 Tokenizer训练进行中 - Epoch {epoch_num}/30")
                return "running"
        
        self.log("⏳ Tokenizer训练尚未开始")
        return "not_started"
    
    def check_predictor_status(self):
        """检查Predictor训练状态"""
        checkpoints_dir = os.path.join(self.predictor_dir, "checkpoints")
        best_model_path = os.path.join(checkpoints_dir, "best_model")
        
        if os.path.exists(best_model_path):
            self.log("✅ Predictor训练已完成")
            return "completed"
        elif os.path.exists(checkpoints_dir):
            checkpoints = [f for f in os.listdir(checkpoints_dir) if f.startswith('epoch_')]
            if checkpoints:
                latest = max(checkpoints, key=lambda x: int(x.split('_')[1]))
                epoch_num = int(latest.split('_')[1])
                self.log(f"🔄 Predictor训练进行中 - Epoch {epoch_num}")
                return "running"
        
        self.log("⏳ Predictor训练尚未开始")
        return "not_started"
    
    def wait_for_tokenizer_completion(self):
        """等待Tokenizer训练完成"""
        self.log("⏳ 等待Tokenizer训练完成...")
        
        while True:
            status = self.check_tokenizer_status()
            if status == "completed":
                self.log("🎉 Tokenizer训练完成！")
                break
            elif status == "running":
                time.sleep(30)  # 每30秒检查一次
            else:
                self.log("❌ Tokenizer训练似乎没有运行")
                return False
        
        return True
    
    def start_predictor_training(self):
        """开始Predictor训练"""
        self.log("🚀 开始Predictor训练...")
        
        try:
            # 切换到finetune目录
            os.chdir(self.finetune_dir)
            
            # 运行Predictor训练
            cmd = f"python train_predictor.py --config {self.config_name}"
            self.log(f"执行命令: {cmd}")
            
            # 使用subprocess运行命令
            process = subprocess.Popen(
                cmd.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # 实时输出日志
            for line in process.stdout:
                print(line.rstrip())
            
            process.wait()
            
            if process.returncode == 0:
                self.log("✅ Predictor训练完成！")
                return True
            else:
                self.log(f"❌ Predictor训练失败，返回码: {process.returncode}")
                return False
                
        except Exception as e:
            self.log(f"❌ Predictor训练出错: {e}")
            return False
    
    def run_complete_training(self):
        """运行完整的训练流程"""
        self.log("🚀 开始模型A (4H) 完整微调流程")
        self.log("=" * 60)
        
        # 1. 检查Tokenizer状态
        tokenizer_status = self.check_tokenizer_status()
        
        if tokenizer_status == "not_started":
            self.log("❌ Tokenizer训练尚未开始，请先运行Tokenizer训练")
            self.log("命令: cd Kronos/finetune && python train_tokenizer_single.py --config model_a_4h")
            return False
        elif tokenizer_status == "running":
            # 等待Tokenizer完成
            if not self.wait_for_tokenizer_completion():
                return False
        
        # 2. 检查Predictor状态
        predictor_status = self.check_predictor_status()
        
        if predictor_status == "completed":
            self.log("✅ Predictor训练已完成")
        elif predictor_status == "running":
            self.log("🔄 Predictor训练正在进行中")
        else:
            # 开始Predictor训练
            if not self.start_predictor_training():
                return False
        
        self.log("🎉 模型A (4H) 完整微调流程完成！")
        return True
    
    def show_training_summary(self):
        """显示训练摘要"""
        self.log("📊 训练摘要")
        self.log("=" * 40)
        
        # Tokenizer状态
        tokenizer_status = self.check_tokenizer_status()
        self.log(f"Tokenizer状态: {tokenizer_status}")
        
        # Predictor状态
        predictor_status = self.check_predictor_status()
        self.log(f"Predictor状态: {predictor_status}")
        
        # 模型文件
        tokenizer_best = os.path.join(self.tokenizer_dir, "checkpoints", "best_model")
        predictor_best = os.path.join(self.predictor_dir, "checkpoints", "best_model")
        
        if os.path.exists(tokenizer_best):
            self.log(f"✅ Tokenizer模型: {tokenizer_best}")
        
        if os.path.exists(predictor_best):
            self.log(f"✅ Predictor模型: {predictor_best}")

def main():
    """主函数"""
    pipeline = ModelATrainingPipeline()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--status":
            pipeline.show_training_summary()
        elif sys.argv[1] == "--wait":
            pipeline.wait_for_tokenizer_completion()
        elif sys.argv[1] == "--predictor":
            pipeline.start_predictor_training()
        else:
            print("使用方法:")
            print("  python complete_model_a_training.py           # 运行完整流程")
            print("  python complete_model_a_training.py --status  # 查看状态")
            print("  python complete_model_a_training.py --wait    # 等待Tokenizer完成")
            print("  python complete_model_a_training.py --predictor # 只运行Predictor训练")
    else:
        pipeline.run_complete_training()

if __name__ == "__main__":
    main()