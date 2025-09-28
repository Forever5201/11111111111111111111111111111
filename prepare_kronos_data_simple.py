#!/usr/bin/env python3
"""
简单的Kronos微调数据准备脚本
使用修改后的get_data.py直接生成Kronos格式数据
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🎯 Kronos微调数据准备工具")
    print("=" * 50)
    
    # 检查必要文件
    get_data_path = Path("src/get_data.py")
    if not get_data_path.exists():
        print("❌ 错误: 找不到 src/get_data.py 文件")
        return False
    
    # 检查.env文件
    env_path = Path(".env")
    if not env_path.exists():
        print("⚠️ 警告: 找不到 .env 文件")
        print("请确保已设置以下环境变量:")
        print("  - OKX_API_KEY")
        print("  - OKX_API_SECRET")
        print("  - OKX_API_PASSPHRASE")
        print()
    
    print("📊 准备生成Kronos微调数据...")
    print("⏱️ 时间框架: 1H, 4H, 1D")
    print("📈 每个时间框架: 2000条记录")
    print("💾 输出目录: data/kronos_datasets/")
    print()
    
    # 询问用户确认
    response = input("是否继续? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ 操作已取消")
        return False
    
    print("🚀 开始数据获取和转换...")
    
    try:
        # 执行get_data.py --kronos
        result = subprocess.run([
            sys.executable, "src/get_data.py", "--kronos"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 数据准备成功!")
            print("\n📄 生成的文件:")
            data_dir = Path("data/kronos_datasets")
            if data_dir.exists():
                for file in data_dir.iterdir():
                    if file.is_file():
                        file_size = file.stat().st_size / (1024 * 1024)  # MB
                        print(f"   📁 {file.name} ({file_size:.2f} MB)")
            
            print("\n🎉 Kronos微调数据准备完成!")
            print("📌 接下来的步骤:")
            print("1. 复制数据到Kronos项目:")
            print("   cp data/kronos_datasets/*.pkl Kronos/finetune/data/")
            print("2. 配置Kronos微调参数:")
            print("   编辑 Kronos/finetune/config.py")
            print("3. 开始微调:")
            print("   cd Kronos && python finetune/train_tokenizer.py")
            print("   cd Kronos && python finetune/train_predictor.py")
            
            return True
        else:
            print("❌ 数据准备失败:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 执行错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
