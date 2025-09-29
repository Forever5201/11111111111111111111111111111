# 🚀 项目安装指南

## 📋 快速开始

本指南将帮助您快速设置并运行整个量化交易平台系统。

---

## 🔧 环境要求

### 系统要求
- **操作系统**: Windows 10/11, macOS 10.14+, Ubuntu 18.04+
- **Python版本**: 3.10 或 3.11 (推荐)
- **内存**: 最低 8GB，推荐 16GB+
- **GPU**: NVIDIA GPU (可选，用于加速训练)

### CUDA支持 (可选)
如需GPU加速：
- **CUDA**: 12.6 或更高版本
- **cuDNN**: 对应的版本

---

## 📦 安装步骤

### 方式一：推荐安装（自动修复冲突）

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd <your-project>

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. 升级pip
python -m pip install --upgrade pip

# 5. 安装整合的依赖
pip install -r requirements_consolidated.txt

# 6. 修复已知冲突
python fix_dependencies.py

# 7. 验证安装
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import pandas; print(f'Pandas: {pandas.__version__}')"
```

### 方式二：分步安装

```bash
# 1. 基础环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 2. 核心依赖
pip install -r requirements.txt

# 3. Kronos模型依赖
pip install -r Kronos/requirements.txt

# 4. Web UI依赖
pip install -r Kronos/webui/requirements.txt

# 5. 手动修复冲突
pip install construct-typing==0.5.5
pip install urllib3==1.26.12
```

### 方式三：Docker安装（推荐生产环境）

```bash
# 1. 构建镜像
docker build -t quant-trading-platform .

# 2. 运行容器
docker run -it --gpus all -p 8000:8000 quant-trading-platform
```

---

## ⚠️ 常见问题解决

### 问题1：依赖冲突
```bash
# 症状：pip install时出现版本冲突警告
# 解决：
python fix_dependencies.py --verbose
```

### 问题2：PyTorch CUDA问题
```bash
# 症状：torch.cuda.is_available()返回False
# 解决：重新安装PyTorch
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

### 问题3：OKX API问题
```bash
# 症状：okx库报urllib3错误
# 解决：固定urllib3版本
pip install urllib3==1.26.12
```

### 问题4：内存不足
```bash
# 症状：安装时内存不足
# 解决：
pip install --no-cache-dir -r requirements_consolidated.txt
```

---

## 🧪 验证安装

运行以下脚本验证各模块是否正常工作：

```python
# test_installation.py
import sys
import importlib

def test_module(module_name, display_name=None):
    """测试模块导入"""
    display_name = display_name or module_name
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, '__version__', 'N/A')
        print(f"✅ {display_name}: {version}")
        return True
    except ImportError as e:
        print(f"❌ {display_name}: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 验证安装...")
    print("-" * 40)
    
    modules = [
        ('torch', 'PyTorch'),
        ('pandas', 'Pandas'),
        ('numpy', 'NumPy'),
        ('flask', 'Flask'),
        ('requests', 'Requests'),
        ('matplotlib', 'Matplotlib'),
        ('plotly', 'Plotly'),
        ('ta', 'TA-Lib'),
        ('yfinance', 'Yahoo Finance'),
        ('websocket', 'WebSocket Client'),
    ]
    
    success_count = 0
    total_count = len(modules)
    
    for module_name, display_name in modules:
        if test_module(module_name, display_name):
            success_count += 1
    
    print("-" * 40)
    print(f"📊 测试结果: {success_count}/{total_count} 模块正常")
    
    if success_count == total_count:
        print("🎉 所有核心模块安装成功！")
    else:
        print("⚠️  部分模块安装失败，请检查错误信息")
    
    # GPU测试
    try:
        import torch
        if torch.cuda.is_available():
            print(f"🚀 CUDA可用: {torch.cuda.get_device_name()}")
        else:
            print("💻 使用CPU模式")
    except:
        print("❌ PyTorch CUDA检查失败")

if __name__ == "__main__":
    main()
```

运行测试：
```bash
python test_installation.py
```

---

## 🔧 开发环境设置

### IDE配置

**VS Code推荐插件**:
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.flake8",
    "ms-python.mypy-type-checker",
    "ms-toolsai.jupyter"
  ]
}
```

**PyCharm配置**:
- 设置Python解释器为虚拟环境中的python
- 启用代码格式化工具(Black)
- 配置类型检查(MyPy)

### 环境变量配置

创建 `.env` 文件：
```bash
# API配置
OKX_API_KEY=your_okx_api_key
OKX_SECRET_KEY=your_okx_secret_key
OKX_PASSPHRASE=your_okx_passphrase

# 模型配置
MODEL_PATH=./models
DATA_PATH=./data
CACHE_PATH=./cache

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log

# Web UI配置
FLASK_DEBUG=False
FLASK_PORT=5000
```

---

## 📚 项目结构说明

```
项目根目录/
├── src/                    # 核心源代码
├── Kronos/                 # AI模型相关
│   ├── model/             # 模型定义
│   ├── finetune/          # 模型微调
│   └── webui/             # Web界面
├── data/                  # 数据文件
├── config/                # 配置文件
├── logs/                  # 日志文件
├── requirements*.txt      # 依赖文件
├── DEPENDENCY_ANALYSIS.md # 依赖分析报告
└── fix_dependencies.py    # 依赖修复脚本
```

---

## 🚀 运行项目

### 启动Web界面
```bash
# 启动主应用
python src/main.py

# 启动Kronos WebUI
cd Kronos/webui
python app.py
```

### 运行数据获取
```bash
python src/data_fetcher.py
```

### 模型训练
```bash
cd Kronos/finetune
python train_tokenizer.py
python train_predictor.py
```

---

## 🔍 问题排查

### 日志位置
- 应用日志: `logs/app.log`
- 源代码日志: `src/logs/app.log`

### 调试模式
```bash
export DEBUG=1
python your_script.py
```

### 性能监控
```bash
pip install psutil
python -c "import psutil; print(f'内存使用: {psutil.virtual_memory().percent}%')"
```

---

## 📞 获取帮助

如果安装过程中遇到问题：

1. 查看 `DEPENDENCY_ANALYSIS.md` 中的详细依赖分析
2. 运行 `python fix_dependencies.py --dry-run --verbose` 检查修复操作
3. 查看项目日志文件
4. 提交Issue到项目仓库

---

## 📄 相关文档

- [依赖分析报告](DEPENDENCY_ANALYSIS.md)
- [Kronos使用指南](README_KRONOS.md)
- [数据准备指南](DATA_PREPARATION_GUIDE.md)
- [多模型训练指南](KRONOS_MULTI_MODEL_GUIDE.md)

---

*祝您使用愉快！如有问题，欢迎反馈。* 🎉

