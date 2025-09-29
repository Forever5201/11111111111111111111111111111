# 📊 Kronos多模型数据准备指南

## 🎯 概述

这是一份完整的Kronos多模型数据准备指南，介绍如何使用参数化的数据准备脚本为不同的模型配置准备专门的训练数据。

## 🆕 新功能：配置驱动的数据准备

### ✨ 主要特性
- **配置驱动**: 根据模型配置自动调整数据准备参数
- **多模型支持**: 为不同模型生成专用数据集
- **环境变量控制**: 支持通过环境变量自定义参数
- **智能目录管理**: 自动创建模型专用的数据目录
- **参数覆盖**: 命令行参数可覆盖配置文件设置

## 🚀 快速开始

### 1. 基础使用

#### 查看可用配置
```bash
python prepare_kronos_data_simple.py --list-configs
```

#### 为Model A准备数据
```bash
python prepare_kronos_data_simple.py --config model_a_4h
```

#### 为Model B准备数据
```bash
python prepare_kronos_data_simple.py --config model_b_1d
```

#### 预览操作（干运行）
```bash
python prepare_kronos_data_simple.py --config model_a_4h --dry-run
```

### 2. 高级用法

#### 自定义时间框架
```bash
python prepare_kronos_data_simple.py --config model_a_4h --timeframes 4H 1D
```

#### 自定义记录数量
```bash
python prepare_kronos_data_simple.py --config model_b_1d --records-per-timeframe 3000
```

#### 自定义输出目录
```bash
python prepare_kronos_data_simple.py --config model_a_4h --output-dir custom_data/model_a
```

#### 强制覆盖现有文件
```bash
python prepare_kronos_data_simple.py --config model_a_4h --force
```

## 🎛️ 配置系统

### 模型特定配置

脚本会根据选择的模型配置自动提取数据需求：

#### Model A (4H模型)
- **时间框架**: 自动从 `target_symbols` 提取（通常是 4H）
- **数据量**: 适中，针对中频交易优化
- **输出目录**: `data/kronos_datasets/model_a_4h/`

#### Model B (1D宏观模型)
- **时间框架**: 自动从 `target_symbols` 提取（通常是 1D）
- **数据量**: 更多历史数据，适合宏观分析
- **输出目录**: `data/kronos_datasets/model_b_1d/`

### 配置提取逻辑

脚本自动从配置文件中提取以下信息：
```python
requirements = {
    "model_name": config.model_name,
    "timeframe": config.timeframe,
    "target_symbols": config.target_symbols,
    "timeframes": [],  # 从target_symbols自动提取
    "records_per_timeframe": 2000,  # 默认值
    "output_dir": config.dataset_path,
}
```

## 🔧 环境变量支持

### 支持的环境变量

| 环境变量 | 描述 | 示例 |
|----------|------|------|
| `KRONOS_OUTPUT_DIR` | 自定义输出目录 | `/path/to/custom/output` |
| `KRONOS_TIMEFRAMES` | 时间框架列表（逗号分隔） | `"4H,1D"` |
| `KRONOS_RECORDS_PER_TF` | 每个时间框架的记录数 | `3000` |

### 使用示例

```bash
# 设置环境变量
export KRONOS_OUTPUT_DIR="/data/custom_location"
export KRONOS_TIMEFRAMES="4H,1D"
export KRONOS_RECORDS_PER_TF="2500"

# 运行数据准备
python prepare_kronos_data_simple.py --config model_a_4h
```

### 优先级

参数的优先级从高到低：
1. **命令行参数** (最高优先级)
2. **环境变量**
3. **配置文件设置**
4. **默认值** (最低优先级)

## 📁 输出结构

### 标准输出结构
```
data/kronos_datasets/
├── model_a_4h/              # Model A专用数据
│   ├── train_data.pkl
│   ├── val_data.pkl
│   ├── test_data.pkl
│   └── data_summary.json
├── model_b_1d/              # Model B专用数据
│   ├── train_data.pkl
│   ├── val_data.pkl
│   ├── test_data.pkl
│   └── data_summary.json
└── [其他模型]/
```

### 自动复制到Kronos项目
数据准备完成后，脚本会自动将数据复制到Kronos项目目录：
```
Kronos/finetune/data/
├── train_data.pkl           # 最新准备的数据
├── val_data.pkl
└── test_data.pkl
```

## 📊 数据摘要文件

每次数据准备都会生成 `data_summary.json` 文件：

```json
{
  "model_name": "Model_A_4H",
  "timeframes": ["4H"],
  "records_per_timeframe": 2000,
  "output_directory": "data/kronos_datasets/model_a_4h",
  "created_at": "2024-01-01T12:00:00",
  "files": [
    {
      "filename": "train_data.pkl",
      "size_mb": 15.67,
      "modified": "2024-01-01T12:00:00"
    }
  ]
}
```

## 🧪 测试和验证

### 运行测试套件
```bash
python test_multi_data_preparation.py
```

### 测试项目
- ✅ 脚本语法检查
- ✅ 帮助信息显示
- ✅ 配置列表功能
- ✅ 干运行模式
- ✅ 自定义参数
- ✅ 错误处理
- ✅ 环境变量支持

### 手动验证
```bash
# 1. 检查语法
python -m py_compile prepare_kronos_data_simple.py

# 2. 测试帮助
python prepare_kronos_data_simple.py --help

# 3. 测试配置列表
python prepare_kronos_data_simple.py --list-configs

# 4. 测试干运行
python prepare_kronos_data_simple.py --config model_a_4h --dry-run
```

## 🔍 故障排除

### 常见问题

#### ❌ 配置管理器导入失败
```
Error: 无法导入ConfigManager
```
**解决方案**: 确保多模型平台已正确设置
```bash
# 检查配置文件是否存在
ls Kronos/finetune/config_manager.py
ls Kronos/finetune/config_model_A_4H.py
ls Kronos/finetune/config_model_B_1D.py
```

#### ❌ 环境变量缺失
```
Error: API credentials missing
```
**解决方案**: 设置OKX API凭证
```bash
export OKX_API_KEY="your_api_key"
export OKX_API_SECRET="your_secret_key"
export OKX_API_PASSPHRASE="your_passphrase"
```

#### ❌ 配置加载失败
```
Error: Configuration validation failed
```
**解决方案**: 检查配置文件语法和路径设置

#### ❌ 数据获取失败
```
Error: No data fetched for Kronos training
```
**解决方案**: 
- 检查网络连接
- 验证API权限
- 检查市场数据可用性

### 调试模式

启用详细日志：
```bash
# 设置日志级别
export LOG_LEVEL=DEBUG

# 运行数据准备
python prepare_kronos_data_simple.py --config model_a_4h --dry-run
```

## 📈 工作流程建议

### 推荐的数据准备流程

1. **环境检查**
   ```bash
   python test_multi_data_preparation.py
   ```

2. **配置检查**
   ```bash
   python prepare_kronos_data_simple.py --list-configs
   ```

3. **干运行测试**
   ```bash
   python prepare_kronos_data_simple.py --config model_a_4h --dry-run
   python prepare_kronos_data_simple.py --config model_b_1d --dry-run
   ```

4. **实际数据准备**
   ```bash
   # 为4H模型准备数据
   python prepare_kronos_data_simple.py --config model_a_4h
   
   # 为1D模型准备数据
   python prepare_kronos_data_simple.py --config model_b_1d
   ```

5. **验证数据**
   ```bash
   # 检查数据文件
   ls -la data/kronos_datasets/*/
   
   # 查看数据摘要
   cat data/kronos_datasets/*/data_summary.json
   ```

6. **开始训练**
   ```bash
   cd Kronos/finetune
   python quick_start_multi_model.py
   ```

### 批量准备数据

对于多个模型的数据准备，可以使用脚本：

```bash
#!/bin/bash
# prepare_all_models.sh

models=("model_a_4h" "model_b_1d")

for model in "${models[@]}"; do
    echo "Preparing data for $model..."
    python prepare_kronos_data_simple.py --config "$model" --force
    
    if [ $? -eq 0 ]; then
        echo "✅ $model data preparation completed"
    else
        echo "❌ $model data preparation failed"
        exit 1
    fi
done

echo "🎉 All model data preparation completed!"
```

## 🔄 与训练流程集成

### 完整工作流程

```bash
# 1. 准备Model A数据
python prepare_kronos_data_simple.py --config model_a_4h

# 2. 准备Model B数据
python prepare_kronos_data_simple.py --config model_b_1d

# 3. 开始多模型训练
cd Kronos/finetune
python multi_model_trainer.py --models model_a_4h model_b_1d
```

### 自动化脚本

创建 `full_pipeline.py`：
```python
#!/usr/bin/env python3
import subprocess
import sys

def run_data_prep(config):
    return subprocess.run([
        sys.executable, "prepare_kronos_data_simple.py",
        "--config", config, "--force"
    ]).returncode == 0

def run_training(models):
    return subprocess.run([
        sys.executable, "Kronos/finetune/multi_model_trainer.py",
        "--models"] + models
    ).returncode == 0

models = ["model_a_4h", "model_b_1d"]

# 准备数据
for model in models:
    if not run_data_prep(model):
        print(f"❌ Data preparation failed for {model}")
        sys.exit(1)

# 开始训练
if run_training(models):
    print("🎉 Pipeline completed successfully!")
else:
    print("❌ Training failed")
    sys.exit(1)
```

## 📚 相关文档

- **多模型平台指南**: `KRONOS_MULTI_MODEL_GUIDE.md`
- **技术文档**: `Kronos/finetune/README_MULTI_MODEL.md`
- **原始数据指南**: `KRONOS_DATA_GUIDE.md`
- **快速开始**: `README_KRONOS.md`

## 🙏 总结

参数化的数据准备脚本为Kronos多模型平台提供了灵活、高效的数据准备解决方案。通过配置驱动的方式，您可以：

- 🎯 **为不同模型准备专门优化的数据**
- 🔧 **通过环境变量和命令行参数灵活控制**
- 📊 **自动管理数据目录和文件组织**
- 🧪 **通过测试套件确保功能正常**
- 🚀 **与训练流程无缝集成**

现在您可以开始为多个Kronos模型准备专门的训练数据了！





