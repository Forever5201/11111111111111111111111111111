#!/usr/bin/env python3
"""
依赖冲突修复脚本
Dependency Conflict Resolution Script

This script automatically fixes the known dependency conflicts
identified in the dependency analysis.

Usage:
    python fix_dependencies.py [--dry-run] [--verbose]
"""

import subprocess
import sys
import argparse
from typing import List, Tuple, Dict
import json
import os

class DependencyFixer:
    """依赖修复工具"""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.conflicts_fixed = 0
        
        # 已知的冲突和解决方案
        self.conflict_resolutions = {
            "construct-typing": "0.5.5",  # 解决anchorpy和borsh-construct冲突
            "urllib3": "1.26.12",         # 解决okx API冲突  
            "pandas": "2.2.2",            # 统一pandas版本
            "numpy": "2.2.6",             # 统一numpy版本
            "huggingface_hub": "0.29.3",  # 统一HF hub版本
        }
        
        # 需要特别处理的包
        self.special_packages = {
            "torch": "2.6.0+cu126",       # PyTorch with CUDA
            "torchvision": "0.17.0+cu126", # 匹配的torchvision
            "torchaudio": "2.4.0+cu126",   # 匹配的torchaudio
        }
    
    def log(self, message: str, level: str = "INFO"):
        """日志输出"""
        if self.verbose or level in ["ERROR", "WARNING"]:
            print(f"[{level}] {message}")
    
    def run_command(self, command: List[str]) -> Tuple[int, str, str]:
        """执行命令"""
        if self.dry_run:
            self.log(f"DRY RUN: {' '.join(command)}", "INFO")
            return 0, "", ""
        
        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=False
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            self.log(f"命令执行失败: {e}", "ERROR")
            return 1, "", str(e)
    
    def check_current_versions(self) -> Dict[str, str]:
        """检查当前安装的包版本"""
        self.log("检查当前安装的包版本...")
        
        code, stdout, stderr = self.run_command(["pip", "list", "--format=json"])
        if code != 0:
            self.log(f"获取包列表失败: {stderr}", "ERROR")
            return {}
        
        try:
            packages = json.loads(stdout)
            return {pkg["name"]: pkg["version"] for pkg in packages}
        except json.JSONDecodeError as e:
            self.log(f"解析包列表失败: {e}", "ERROR")
            return {}
    
    def fix_basic_conflicts(self):
        """修复基本的版本冲突"""
        self.log("开始修复基本版本冲突...")
        
        current_versions = self.check_current_versions()
        
        for package, target_version in self.conflict_resolutions.items():
            current_version = current_versions.get(package)
            
            if current_version == target_version:
                self.log(f"{package} 版本已正确: {target_version}", "INFO")
                continue
            
            self.log(f"修复 {package}: {current_version} -> {target_version}", "INFO")
            
            # 卸载当前版本
            code, stdout, stderr = self.run_command(["pip", "uninstall", package, "-y"])
            if code != 0 and not self.dry_run:
                self.log(f"卸载 {package} 失败: {stderr}", "WARNING")
            
            # 安装指定版本
            code, stdout, stderr = self.run_command(["pip", "install", f"{package}=={target_version}"])
            if code != 0 and not self.dry_run:
                self.log(f"安装 {package}=={target_version} 失败: {stderr}", "ERROR")
            else:
                self.conflicts_fixed += 1
    
    def fix_pytorch_stack(self):
        """修复PyTorch相关的依赖"""
        self.log("检查PyTorch栈的兼容性...")
        
        pytorch_packages = ["torch", "torchvision", "torchaudio"]
        install_command = ["pip", "install"]
        
        for package in pytorch_packages:
            if package in self.special_packages:
                install_command.append(f"{package}=={self.special_packages[package]}")
        
        # 添加PyTorch索引
        install_command.extend([
            "--index-url", "https://download.pytorch.org/whl/cu126"
        ])
        
        self.log(f"重新安装PyTorch栈: {' '.join(install_command[2:])}", "INFO")
        code, stdout, stderr = self.run_command(install_command)
        
        if code != 0 and not self.dry_run:
            self.log(f"PyTorch安装失败: {stderr}", "ERROR")
        else:
            self.log("PyTorch栈安装成功", "INFO")
    
    def verify_fixes(self):
        """验证修复结果"""
        self.log("验证依赖修复结果...")
        
        if self.dry_run:
            self.log("跳过验证（干运行模式）", "INFO")
            return
        
        # 重新检查冲突
        code, stdout, stderr = self.run_command(["pipdeptree", "--warn", "silence"])
        
        if "Warning!!!" in stderr:
            self.log("仍存在依赖冲突，需要手动检查", "WARNING")
            self.log(stderr, "WARNING")
        else:
            self.log("依赖冲突修复完成！", "INFO")
    
    def generate_fixed_requirements(self):
        """生成修复后的requirements文件"""
        self.log("生成修复后的requirements文件...")
        
        code, stdout, stderr = self.run_command(["pip", "freeze"])
        if code != 0:
            self.log(f"生成requirements失败: {stderr}", "ERROR")
            return
        
        output_file = "requirements_fixed.txt"
        if not self.dry_run:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# 修复后的依赖文件\n")
                f.write("# Generated by fix_dependencies.py\n\n")
                f.write(stdout)
            
            self.log(f"修复后的requirements已保存到: {output_file}", "INFO")
        else:
            self.log(f"DRY RUN: 将生成 {output_file}", "INFO")
    
    def run(self):
        """执行完整的修复流程"""
        self.log("开始依赖修复流程...")
        self.log(f"模式: {'干运行' if self.dry_run else '实际执行'}", "INFO")
        
        try:
            # 1. 修复基本冲突
            self.fix_basic_conflicts()
            
            # 2. 修复PyTorch栈
            self.fix_pytorch_stack()
            
            # 3. 验证修复结果
            self.verify_fixes()
            
            # 4. 生成新的requirements文件
            self.generate_fixed_requirements()
            
            self.log(f"修复完成! 共修复 {self.conflicts_fixed} 个冲突", "INFO")
            
        except KeyboardInterrupt:
            self.log("用户中断了修复流程", "WARNING")
        except Exception as e:
            self.log(f"修复过程中发生错误: {e}", "ERROR")
            sys.exit(1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="自动修复项目依赖冲突",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
    python fix_dependencies.py                    # 执行修复
    python fix_dependencies.py --dry-run          # 仅显示要执行的操作
    python fix_dependencies.py --dry-run --verbose # 详细的干运行模式
        """
    )
    
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='仅显示将要执行的操作，不实际修改'
    )
    
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='显示详细的输出信息'
    )
    
    args = parser.parse_args()
    
    # 检查pip是否可用
    if subprocess.run(["pip", "--version"], capture_output=True).returncode != 0:
        print("错误: 未找到pip命令，请确保Python和pip已正确安装")
        sys.exit(1)
    
    # 创建修复器并运行
    fixer = DependencyFixer(dry_run=args.dry_run, verbose=args.verbose)
    fixer.run()

if __name__ == "__main__":
    main()

