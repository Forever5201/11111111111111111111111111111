#!/usr/bin/env python3
"""
参数化的Kronos微调数据准备脚本
支持多模型配置驱动的数据准备

用法:
  python prepare_kronos_data_simple.py --config model_a_4h
  python prepare_kronos_data_simple.py --config model_b_1d
  python prepare_kronos_data_simple.py --config default
"""

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# 添加Kronos配置管理器路径
sys.path.append("Kronos/finetune")

def import_config_manager():
    """动态导入配置管理器"""
    try:
        from config_manager import ConfigManager
        return ConfigManager
    except ImportError:
        print("❌ 错误: 无法导入ConfigManager")
        print("请确保已经按照多模型平台设置完成配置")
        return None

def create_argument_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='Kronos多模型数据准备工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  %(prog)s --config model_a_4h
  %(prog)s --config model_b_1d --force
  %(prog)s --list-configs
  %(prog)s --config default --timeframes 4H 1D
'''
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='选择模型配置 (model_a_4h, model_b_1d, default)'
    )
    
    parser.add_argument(
        '--list-configs',
        action='store_true',
        help='列出所有可用的配置'
    )
    
    parser.add_argument(
        '--timeframes',
        nargs='+',
        default=None,
        help='指定时间框架（覆盖配置文件设置）'
    )
    
    parser.add_argument(
        '--records-per-timeframe',
        type=int,
        default=None,
        help='每个时间框架的记录数（覆盖配置文件设置）'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='自定义输出目录'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='强制覆盖已存在的数据文件'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅显示将要执行的操作，不实际执行'
    )
    
    return parser

def check_environment() -> Tuple[bool, List[str]]:
    """检查环境和依赖"""
    errors = []
    
    # 检查必要文件
    required_files = [
        "src/get_data.py",
        "Kronos/finetune/config_manager.py"
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            errors.append(f"找不到必要文件: {file_path}")
    
    # 检查环境变量
    env_vars = ["OKX_API_KEY", "OKX_API_SECRET", "OKX_API_PASSPHRASE"]
    missing_env = []
    
    for var in env_vars:
        if not os.getenv(var):
            missing_env.append(var)
    
    if missing_env:
        errors.append(f"缺少环境变量: {', '.join(missing_env)}")
    
    return len(errors) == 0, errors

def extract_data_requirements(config) -> Dict:
    """从配置中提取数据需求"""
    requirements = {
        "model_name": getattr(config, 'model_name', 'Unknown'),
        "timeframe": getattr(config, 'timeframe', None),
        "target_symbols": getattr(config, 'target_symbols', []),
        "timeframes": [],
        "records_per_timeframe": 2000,  # 默认值
        "output_dir": getattr(config, 'dataset_path', 'data/kronos_datasets'),
    }
    
    # 从target_symbols中提取时间框架
    if hasattr(config, 'target_symbols') and config.target_symbols:
        for symbol in config.target_symbols:
            if '_' in symbol:
                timeframe = symbol.split('_')[-1]
                if timeframe not in requirements["timeframes"]:
                    requirements["timeframes"].append(timeframe)
    
    # 如果没有从target_symbols中提取到，使用单一时间框架
    if not requirements["timeframes"] and requirements["timeframe"]:
        requirements["timeframes"] = [requirements["timeframe"]]
    
    # 如果仍然没有，使用默认值
    if not requirements["timeframes"]:
        requirements["timeframes"] = ["1H", "4H", "1D"]
    
    return requirements

def prepare_model_specific_data(config, timeframes=None, records_per_timeframe=None, 
                              output_dir=None, dry_run=False) -> bool:
    """为特定模型准备数据"""
    
    # 提取数据需求
    requirements = extract_data_requirements(config)
    
    # 应用命令行覆盖
    if timeframes:
        requirements["timeframes"] = timeframes
    if records_per_timeframe:
        requirements["records_per_timeframe"] = records_per_timeframe
    if output_dir:
        requirements["output_dir"] = output_dir
    
    print(f"📊 为模型准备数据: {requirements['model_name']}")
    print(f"⏱️ 时间框架: {', '.join(requirements['timeframes'])}")
    print(f"📈 每个时间框架记录数: {requirements['records_per_timeframe']}")
    print(f"💾 输出目录: {requirements['output_dir']}")
    print()
    
    if dry_run:
        print("🔍 干运行模式 - 不会实际执行数据获取")
        return True
    
    # 创建模型专用的输出目录
    model_output_dir = Path(requirements["output_dir"]) / requirements["model_name"].lower()
    model_output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🚀 开始数据获取和转换...")
    print(f"📁 模型专用目录: {model_output_dir}")
    
    try:
        # 构建get_data.py命令
        cmd = [
            sys.executable, "src/get_data.py", "--kronos"
        ]
        
        # 设置环境变量指定输出目录
        env = os.environ.copy()
        env["KRONOS_OUTPUT_DIR"] = str(model_output_dir)
        env["KRONOS_TIMEFRAMES"] = ",".join(requirements["timeframes"])
        env["KRONOS_RECORDS_PER_TF"] = str(requirements["records_per_timeframe"])
        
        print(f"🔧 执行命令: {' '.join(cmd)}")
        print(f"📋 环境变量:")
        print(f"   KRONOS_OUTPUT_DIR={env['KRONOS_OUTPUT_DIR']}")
        print(f"   KRONOS_TIMEFRAMES={env['KRONOS_TIMEFRAMES']}")
        print(f"   KRONOS_RECORDS_PER_TF={env['KRONOS_RECORDS_PER_TF']}")
        
        # 执行数据获取
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            print("✅ 数据获取成功!")
            
            # 显示生成的文件
            show_generated_files(model_output_dir)
            
            # 复制到Kronos目录
            copy_data_to_kronos(model_output_dir, config)
            
            # 创建数据摘要
            create_data_summary(model_output_dir, requirements)
            
            print("\n🎉 模型数据准备完成!")
            show_next_steps(config)
            
            return True
        else:
            print("❌ 数据获取失败:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 执行错误: {e}")
        return False

def show_generated_files(data_dir: Path):
    """显示生成的文件信息"""
    print("\n📄 生成的文件:")
    if data_dir.exists():
        total_size = 0
        file_count = 0
        
        for file in data_dir.iterdir():
            if file.is_file():
                file_size = file.stat().st_size / (1024 * 1024)  # MB
                print(f"   📁 {file.name} ({file_size:.2f} MB)")
                total_size += file_size
                file_count += 1
        
        if file_count > 0:
            print(f"   📊 总计: {file_count} 个文件, {total_size:.2f} MB")
        else:
            print("   ⚠️ 未找到生成的文件")
    else:
        print("   ❌ 输出目录不存在")

def copy_data_to_kronos(source_dir: Path, config):
    """复制数据到Kronos项目目录"""
    kronos_data_dir = Path("Kronos/finetune/data")
    
    if not kronos_data_dir.exists():
        kronos_data_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 创建Kronos数据目录: {kronos_data_dir}")
    
    print(f"\n📋 复制数据到Kronos项目...")
    
    copied_files = []
    for file in source_dir.glob("*.pkl"):
        dest_file = kronos_data_dir / file.name
        
        try:
            import shutil
            shutil.copy2(file, dest_file)
            copied_files.append(file.name)
            print(f"   ✅ {file.name} -> {dest_file}")
        except Exception as e:
            print(f"   ❌ 复制失败 {file.name}: {e}")
    
    if copied_files:
        print(f"   📊 成功复制 {len(copied_files)} 个文件")
    else:
        print("   ⚠️ 没有文件被复制")

def create_data_summary(output_dir: Path, requirements: Dict):
    """创建数据摘要文件"""
    summary = {
        "model_name": requirements["model_name"],
        "timeframes": requirements["timeframes"],
        "records_per_timeframe": requirements["records_per_timeframe"],
        "output_directory": str(output_dir),
        "created_at": datetime.now().isoformat(),
        "files": []
    }
    
    # 收集文件信息
    for file in output_dir.glob("*.pkl"):
        file_info = {
            "filename": file.name,
            "size_mb": round(file.stat().st_size / (1024 * 1024), 2),
            "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
        }
        summary["files"].append(file_info)
    
    # 保存摘要
    summary_file = output_dir / "data_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n📋 数据摘要已保存: {summary_file}")

def show_next_steps(config):
    """显示后续步骤"""
    model_name = getattr(config, 'model_name', 'Unknown')
    config_name = model_name.lower().replace('_', '_').replace(' ', '_')
    
    print(f"\n📌 接下来的步骤 ({model_name}):")
    print("1. 验证数据:")
    print("   python test_kronos_integration.py")
    
    print("2. 开始训练:")
    if hasattr(config, 'model_name'):
        if 'model_a' in config.model_name.lower():
            config_arg = 'model_a_4h'
        elif 'model_b' in config.model_name.lower():
            config_arg = 'model_b_1d'
        else:
            config_arg = 'default'
            
        print(f"   cd Kronos/finetune")
        print(f"   torchrun --standalone --nproc_per_node=1 train_tokenizer_multi.py --config {config_arg}")
        print(f"   torchrun --standalone --nproc_per_node=1 train_predictor_multi.py --config {config_arg}")
    else:
        print("   cd Kronos/finetune")
        print("   python quick_start_multi_model.py")
    
    print("3. 批量训练:")
    print("   python multi_model_trainer.py --models model_a_4h model_b_1d")

def main():
    """主函数"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    print("🎯 Kronos多模型数据准备工具")
    print("=" * 60)
    
    # 导入配置管理器
    ConfigManager = import_config_manager()
    if not ConfigManager:
        return False
    
    config_manager = ConfigManager()
    
    # 列出配置选项
    if args.list_configs:
        config_manager.list_available_configs()
        return True
    
    # 检查是否指定了配置
    if not args.config:
        print("❌ 错误: 必须指定配置文件")
        print("使用 --list-configs 查看可用配置")
        print("使用 --config <配置名> 指定配置")
        return False
    
    # 环境检查
    print("🔍 检查环境...")
    env_ok, env_errors = check_environment()
    if not env_ok:
        print("❌ 环境检查失败:")
        for error in env_errors:
            print(f"   - {error}")
        print("\n请解决以上问题后重试")
        return False
    print("✅ 环境检查通过")
    
    # 加载配置
    try:
        print(f"\n📋 加载配置: {args.config}")
        config = config_manager.load_config(args.config)
        
        if hasattr(config, 'get_model_info'):
            model_info = config.get_model_info()
            print(f"   模型: {model_info.get('name', 'Unknown')}")
            print(f"   描述: {model_info.get('description', 'No description')}")
            print(f"   时间框架: {model_info.get('timeframe', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False
    
    # 询问用户确认（除非是dry-run）
    if not args.dry_run and not args.force:
        print(f"\n⚠️ 即将为 {getattr(config, 'model_name', args.config)} 准备数据")
        response = input("是否继续? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ 操作已取消")
            return False
    
    # 准备数据
    success = prepare_model_specific_data(
        config=config,
        timeframes=args.timeframes,
        records_per_timeframe=args.records_per_timeframe,
        output_dir=args.output_dir,
        dry_run=args.dry_run
    )
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
