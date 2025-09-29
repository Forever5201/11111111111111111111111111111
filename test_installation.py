#!/usr/bin/env python3
"""
安装验证脚本
Installation Verification Script

This script tests if all required dependencies are properly installed
and configured for the quantitative trading platform.

Usage:
    python test_installation.py [--detailed] [--fix-missing]
"""

import sys
import importlib
import subprocess
import argparse
from typing import List, Tuple, Dict, Optional
import json
import os

class InstallationTester:
    """安装验证器"""
    
    def __init__(self, detailed: bool = False, fix_missing: bool = False):
        self.detailed = detailed
        self.fix_missing = fix_missing
        self.results = {
            'core_modules': [],
            'ml_modules': [],
            'web_modules': [],
            'finance_modules': [],
            'system_info': {},
            'conflicts': [],
            'missing_modules': []
        }
    
    def log(self, message: str, level: str = "INFO"):
        """日志输出"""
        colors = {
            "INFO": "\033[94m",      # Blue
            "SUCCESS": "\033[92m",   # Green
            "WARNING": "\033[93m",   # Yellow
            "ERROR": "\033[91m",     # Red
            "ENDC": "\033[0m"        # End color
        }
        
        color = colors.get(level, colors["INFO"])
        print(f"{color}[{level}]{colors['ENDC']} {message}")
    
    def test_module(self, module_name: str, display_name: str = None, 
                   required: bool = True) -> Tuple[bool, str, str]:
        """测试单个模块"""
        display_name = display_name or module_name
        
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, '__version__', 'N/A')
            
            if self.detailed:
                self.log(f"✅ {display_name}: {version}", "SUCCESS")
            
            return True, version, ""
        except ImportError as e:
            error_msg = str(e)
            
            if required:
                self.log(f"❌ {display_name}: {error_msg}", "ERROR")
                self.results['missing_modules'].append({
                    'module': module_name,
                    'display_name': display_name,
                    'error': error_msg
                })
            else:
                self.log(f"⚠️  {display_name}: {error_msg} (可选)", "WARNING")
            
            return False, "", error_msg
    
    def test_core_modules(self):
        """测试核心模块"""
        self.log("🔍 测试核心Python模块...", "INFO")
        
        core_modules = [
            ('pandas', 'Pandas数据处理'),
            ('numpy', 'NumPy数值计算'),
            ('requests', 'HTTP请求库'),
            ('yaml', 'PyYAML配置解析', False),  # 实际模块名是yaml
            ('logging', 'Python日志库'),
            ('json', 'JSON处理库'),
            ('datetime', '日期时间处理'),
            ('os', '操作系统接口'),
            ('sys', '系统参数和函数'),
        ]
        
        success_count = 0
        for module_info in core_modules:
            module_name = module_info[0]
            display_name = module_info[1]
            required = module_info[2] if len(module_info) > 2 else True
            
            success, version, error = self.test_module(module_name, display_name, required)
            if success:
                success_count += 1
                self.results['core_modules'].append({
                    'name': display_name,
                    'version': version,
                    'status': 'OK'
                })
        
        return success_count, len(core_modules)
    
    def test_ml_modules(self):
        """测试机器学习模块"""
        self.log("🤖 测试机器学习模块...", "INFO")
        
        ml_modules = [
            ('torch', 'PyTorch深度学习'),
            ('transformers', 'HuggingFace Transformers', False),
            ('huggingface_hub', 'HuggingFace Hub'),
            ('einops', 'Einops张量操作', False),
            ('matplotlib', 'Matplotlib可视化'),
            ('tqdm', '进度条库'),
            ('safetensors', '安全张量存储', False),
        ]
        
        success_count = 0
        for module_info in ml_modules:
            module_name = module_info[0]
            display_name = module_info[1]
            required = module_info[2] if len(module_info) > 2 else True
            
            success, version, error = self.test_module(module_name, display_name, required)
            if success:
                success_count += 1
                self.results['ml_modules'].append({
                    'name': display_name,
                    'version': version,
                    'status': 'OK'
                })
        
        return success_count, len(ml_modules)
    
    def test_web_modules(self):
        """测试Web开发模块"""
        self.log("🌐 测试Web开发模块...", "INFO")
        
        web_modules = [
            ('flask', 'Flask Web框架'),
            ('plotly', 'Plotly交互图表'),
            ('websocket', 'WebSocket客户端'),
        ]
        
        success_count = 0
        for module_info in web_modules:
            module_name = module_info[0]
            display_name = module_info[1]
            required = module_info[2] if len(module_info) > 2 else True
            
            success, version, error = self.test_module(module_name, display_name, required)
            if success:
                success_count += 1
                self.results['web_modules'].append({
                    'name': display_name,
                    'version': version,
                    'status': 'OK'
                })
        
        return success_count, len(web_modules)
    
    def test_finance_modules(self):
        """测试金融相关模块"""
        self.log("💰 测试金融数据模块...", "INFO")
        
        finance_modules = [
            ('yfinance', 'Yahoo Finance API'),
            ('ta', '技术分析指标库'),
            ('okx', 'OKX交易所API', False),
        ]
        
        success_count = 0
        for module_info in finance_modules:
            module_name = module_info[0]
            display_name = module_info[1]
            required = module_info[2] if len(module_info) > 2 else True
            
            success, version, error = self.test_module(module_name, display_name, required)
            if success:
                success_count += 1
                self.results['finance_modules'].append({
                    'name': display_name,
                    'version': version,
                    'status': 'OK'
                })
        
        return success_count, len(finance_modules)
    
    def check_system_info(self):
        """检查系统信息"""
        self.log("🖥️  检查系统信息...", "INFO")
        
        # Python版本
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self.log(f"Python版本: {python_version}", "INFO")
        
        # PyTorch CUDA支持
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                cuda_version = torch.version.cuda
                device_name = torch.cuda.get_device_name(0)
                self.log(f"CUDA可用: {device_name} (CUDA {cuda_version})", "SUCCESS")
            else:
                self.log("CUDA不可用，使用CPU模式", "WARNING")
            
            self.results['system_info'] = {
                'python_version': python_version,
                'torch_version': torch.__version__,
                'cuda_available': cuda_available,
                'cuda_version': torch.version.cuda if cuda_available else None,
                'device_name': torch.cuda.get_device_name(0) if cuda_available else None
            }
        except ImportError:
            self.log("PyTorch未安装，无法检查CUDA支持", "WARNING")
    
    def check_conflicts(self):
        """检查依赖冲突"""
        self.log("⚠️  检查依赖冲突...", "INFO")
        
        try:
            result = subprocess.run(
                ["pipdeptree", "--warn", "silence"], 
                capture_output=True, 
                text=True
            )
            
            if "Warning!!!" in result.stderr:
                self.log("发现依赖冲突:", "WARNING")
                conflicts = result.stderr.split("Warning!!!")[1:]
                for conflict in conflicts:
                    if conflict.strip():
                        self.log(f"  {conflict.strip()}", "WARNING")
                        self.results['conflicts'].append(conflict.strip())
            else:
                self.log("未发现依赖冲突", "SUCCESS")
                
        except FileNotFoundError:
            self.log("pipdeptree未安装，跳过冲突检查", "WARNING")
    
    def test_project_structure(self):
        """测试项目结构"""
        self.log("📁 检查项目结构...", "INFO")
        
        required_files = [
            'requirements.txt',
            'src/',
            'Kronos/',
            'config/',
        ]
        
        optional_files = [
            'Kronos/requirements.txt',
            'Kronos/webui/requirements.txt',
            'data/',
            'logs/',
        ]
        
        missing_required = []
        missing_optional = []
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_required.append(file_path)
                self.log(f"❌ 缺少必需文件/目录: {file_path}", "ERROR")
            else:
                self.log(f"✅ {file_path}", "SUCCESS" if self.detailed else "INFO")
        
        for file_path in optional_files:
            if not os.path.exists(file_path):
                missing_optional.append(file_path)
                if self.detailed:
                    self.log(f"⚠️  缺少可选文件/目录: {file_path}", "WARNING")
        
        return len(missing_required) == 0
    
    def fix_missing_packages(self):
        """修复缺失的包"""
        if not self.fix_missing or not self.results['missing_modules']:
            return
        
        self.log("🔧 尝试安装缺失的包...", "INFO")
        
        for missing in self.results['missing_modules']:
            module_name = missing['module']
            self.log(f"正在安装 {module_name}...", "INFO")
            
            try:
                result = subprocess.run(
                    ["pip", "install", module_name], 
                    capture_output=True, 
                    text=True,
                    check=True
                )
                self.log(f"✅ {module_name} 安装成功", "SUCCESS")
            except subprocess.CalledProcessError as e:
                self.log(f"❌ {module_name} 安装失败: {e}", "ERROR")
    
    def generate_report(self):
        """生成测试报告"""
        self.log("📊 生成测试报告...", "INFO")
        
        report = {
            'summary': {
                'core_modules': len([m for m in self.results['core_modules'] if m['status'] == 'OK']),
                'ml_modules': len([m for m in self.results['ml_modules'] if m['status'] == 'OK']),
                'web_modules': len([m for m in self.results['web_modules'] if m['status'] == 'OK']),
                'finance_modules': len([m for m in self.results['finance_modules'] if m['status'] == 'OK']),
                'missing_count': len(self.results['missing_modules']),
                'conflicts_count': len(self.results['conflicts'])
            },
            'details': self.results
        }
        
        with open('installation_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.log("测试报告已保存到: installation_test_report.json", "INFO")
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("🚀 开始安装验证测试...", "INFO")
        self.log("=" * 50, "INFO")
        
        # 运行各项测试
        core_success, core_total = self.test_core_modules()
        ml_success, ml_total = self.test_ml_modules()
        web_success, web_total = self.test_web_modules()
        finance_success, finance_total = self.test_finance_modules()
        
        # 系统信息
        self.check_system_info()
        
        # 检查冲突
        self.check_conflicts()
        
        # 项目结构
        structure_ok = self.test_project_structure()
        
        # 修复缺失包
        self.fix_missing_packages()
        
        # 生成报告
        self.generate_report()
        
        # 总结
        self.log("=" * 50, "INFO")
        self.log("📈 测试结果总结:", "INFO")
        self.log(f"  核心模块: {core_success}/{core_total}", "SUCCESS" if core_success == core_total else "WARNING")
        self.log(f"  ML模块: {ml_success}/{ml_total}", "SUCCESS" if ml_success == ml_total else "WARNING")
        self.log(f"  Web模块: {web_success}/{web_total}", "SUCCESS" if web_success == web_total else "WARNING")
        self.log(f"  金融模块: {finance_success}/{finance_total}", "SUCCESS" if finance_success == finance_total else "WARNING")
        self.log(f"  缺失模块: {len(self.results['missing_modules'])}", "ERROR" if self.results['missing_modules'] else "SUCCESS")
        self.log(f"  依赖冲突: {len(self.results['conflicts'])}", "WARNING" if self.results['conflicts'] else "SUCCESS")
        self.log(f"  项目结构: {'正常' if structure_ok else '异常'}", "SUCCESS" if structure_ok else "ERROR")
        
        # 最终判断
        total_success = core_success + ml_success + web_success + finance_success
        total_tests = core_total + ml_total + web_total + finance_total
        success_rate = (total_success / total_tests) * 100 if total_tests > 0 else 0
        
        if success_rate >= 90 and not self.results['conflicts'] and structure_ok:
            self.log("🎉 安装验证通过！项目已准备就绪。", "SUCCESS")
            return True
        elif success_rate >= 70:
            self.log("⚠️  安装基本完成，但存在一些问题需要解决。", "WARNING")
            return False
        else:
            self.log("❌ 安装存在严重问题，请检查依赖。", "ERROR")
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="验证量化交易平台的安装状态",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
    python test_installation.py                 # 基本测试
    python test_installation.py --detailed      # 详细输出
    python test_installation.py --fix-missing   # 自动修复缺失的包
        """
    )
    
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='显示详细的测试信息'
    )
    
    parser.add_argument(
        '--fix-missing',
        action='store_true',
        help='自动尝试安装缺失的包'
    )
    
    args = parser.parse_args()
    
    # 创建测试器并运行
    tester = InstallationTester(detailed=args.detailed, fix_missing=args.fix_missing)
    success = tester.run_all_tests()
    
    # 退出代码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

