#!/usr/bin/env python3
"""
快速启动Kronos微调数据准备
一键完成数据获取、转换、验证和复制
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """执行命令并处理结果"""
    print(f"⏳ {description}...")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} 完成")
            return True
        else:
            print(f"❌ {description} 失败:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ 执行错误: {e}")
        return False

def check_prerequisites():
    """检查先决条件"""
    print("🔍 检查先决条件...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8+")
        return False
    
    # 检查必要文件
    required_files = [
        "src/get_data.py",
        "config/config.yaml",
        ".env"
    ]
    
    for file in required_files:
        if not Path(file).exists():
            print(f"❌ 缺少文件: {file}")
            return False
    
    # 检查环境变量
    required_env = ["OKX_API_KEY", "OKX_API_SECRET", "OKX_API_PASSPHRASE"]
    missing_env = []
    
    for env_var in required_env:
        if not os.getenv(env_var):
            missing_env.append(env_var)
    
    if missing_env:
        print(f"❌ 缺少环境变量: {missing_env}")
        print("请在.env文件中设置OKX API凭证")
        return False
    
    print("✅ 所有先决条件满足")
    return True

def generate_data():
    """生成Kronos微调数据"""
    print("\n📊 生成Kronos微调数据...")
    return run_command(
        f"{sys.executable} src/get_data.py --kronos",
        "数据获取和转换"
    )

def test_data():
    """测试生成的数据"""
    print("\n🧪 测试数据格式...")
    return run_command(
        f"{sys.executable} test_kronos_integration.py",
        "数据格式验证"
    )

def copy_to_kronos():
    """复制数据到Kronos目录"""
    print("\n📁 复制数据到Kronos目录...")
    
    source_dir = Path("data/kronos_datasets")
    target_dir = Path("Kronos/finetune/data")
    
    if not source_dir.exists():
        print("❌ 源数据目录不存在")
        return False
    
    if not target_dir.exists():
        print(f"📁 创建目录: {target_dir}")
        target_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 复制pickle文件
        for pkl_file in source_dir.glob("*.pkl"):
            target_file = target_dir / pkl_file.name
            shutil.copy2(pkl_file, target_file)
            print(f"✅ 复制: {pkl_file.name}")
        
        print("✅ 数据复制完成")
        return True
    
    except Exception as e:
        print(f"❌ 复制失败: {e}")
        return False

def show_next_steps():
    """显示后续步骤"""
    print("\n🎉 数据准备完成！")
    print("=" * 50)
    print("📋 下一步操作:")
    print("1. 进入Kronos目录:")
    print("   cd Kronos")
    print()
    print("2. 配置微调参数 (可选):")
    print("   vim finetune/config.py")
    print()
    print("3. 开始微调tokenizer:")
    print("   torchrun --standalone --nproc_per_node=1 finetune/train_tokenizer.py")
    print()
    print("4. 开始微调predictor:")
    print("   torchrun --standalone --nproc_per_node=1 finetune/train_predictor.py")
    print()
    print("5. 运行回测:")
    print("   python finetune/qlib_test.py --device cuda:0")
    print()
    print("🔗 完整文档: KRONOS_DATA_GUIDE.md")

def main():
    print("🚀 Kronos微调数据一键准备工具")
    print("=" * 50)
    
    steps = [
        ("检查先决条件", check_prerequisites),
        ("生成数据", generate_data),
        ("测试数据", test_data),
        ("复制到Kronos", copy_to_kronos)
    ]
    
    for step_name, step_func in steps:
        print(f"\n📌 步骤: {step_name}")
        print("-" * 30)
        
        if not step_func():
            print(f"\n❌ 步骤 '{step_name}' 失败，停止执行")
            return False
    
    show_next_steps()
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
