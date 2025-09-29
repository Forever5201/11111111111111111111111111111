# 🚀 Kronos多模型微调平台 - 完整使用指南

## 📖 概述

恭喜！您现在拥有了一个完整的**配置驱动**Kronos多模型微调平台。这个平台支持并行部署和训练多个不同时间框架的Kronos模型，实现了从"单策略研究"到"多策略/多模型平台"的工程升级。

## 🎯 平台特性

### ✨ 核心优势
- **配置驱动开发**: 通过独立配置文件管理不同模型，无需重复代码
- **多时间框架支持**: 内置4H和1D模型配置，易于扩展到其他时间框架
- **并行训练能力**: 支持多GPU并行训练或单GPU顺序训练
- **自动化管理**: 依赖关系处理、目录创建、错误处理全自动化
- **监控集成**: 内置Comet ML监控和详细日志记录
- **向后兼容**: 保持与原始Kronos代码的完全兼容性

### 📦 已实现的模型配置

| 模型 | 时间框架 | 特点 | 用途 |
|------|----------|------|------|
| **Model A** | 4小时 (4H) | 中频交易模型 | 日内波段、技术分析 |
| **Model B** | 1天 (1D) | 宏观趋势模型 | 长期趋势、宏观分析 |

## 🏗️ 架构设计

```
📁 多模型平台架构
├── 🎛️ 配置层 (Configuration Layer)
│   ├── config_model_A_4H.py     # 4H模型配置
│   ├── config_model_B_1D.py     # 1D宏观模型配置
│   └── config_manager.py        # 统一配置管理
├── 🚂 训练层 (Training Layer)
│   ├── train_tokenizer_multi.py # 多配置tokenizer训练
│   ├── train_predictor_multi.py # 多配置predictor训练
│   └── multi_model_trainer.py   # 批量训练管理器
├── 🧪 测试层 (Testing Layer)
│   ├── test_multi_config.py     # 配置测试套件
│   └── quick_start_multi_model.py # 快速启动脚本
└── 📚 文档层 (Documentation Layer)
    ├── README_MULTI_MODEL.md    # 详细技术文档
    └── KRONOS_MULTI_MODEL_GUIDE.md # 本使用指南
```

## 🚀 快速开始

### 步骤1: 环境检查
```bash
cd Kronos/finetune
python quick_start_multi_model.py
```

### 步骤2: 配置测试
```bash
python test_multi_config.py
```

### 步骤3: 查看可用配置
```bash
python config_manager.py --list-configs
```

### 步骤4: 选择训练方式

#### 🎮 交互式训练（推荐新手）
```bash
python quick_start_multi_model.py
# 然后按照提示选择模型、阶段和模式
```

#### ⚡ 快速测试（推荐）
```bash
# 预览训练计划
python multi_model_trainer.py --models model_a_4h model_b_1d --dry-run
```

#### 🔄 顺序训练（推荐）
```bash
# 训练所有模型（tokenizer + predictor）
python multi_model_trainer.py --models model_a_4h model_b_1d --mode sequential
```

#### 🚀 并行训练（需要多GPU）
```bash
# 并行训练（需要至少2个GPU）
python multi_model_trainer.py --models model_a_4h model_b_1d --mode parallel --max-workers 2
```

## 📊 模型配置详解

### Model A (4H时间框架)
```python
# 文件: config_model_A_4H.py
特点:
- 时间框架: 4小时
- 目标: 中频交易、技术分析
- 窗口: 90步历史 → 10步预测
- 批量: 32, 累积步数: 2
- 学习率: tokenizer(1.5e-4), predictor(3e-5)
- 训练轮数: 30 epochs
```

### Model B (1D宏观模型)
```python
# 文件: config_model_B_1D.py
特点:
- 时间框架: 1天
- 目标: 宏观趋势、长期预测
- 窗口: 120步历史 → 15步预测  
- 批量: 16, 累积步数: 4
- 学习率: tokenizer(1e-4), predictor(2e-5)
- 训练轮数: 50 epochs
- 特色: 季节性、趋势、宏观指标分析
```

## 🎛️ 训练模式选择

### 🔄 顺序训练 (Sequential)
**推荐场景**: 单GPU环境、稳定性优先
```bash
python multi_model_trainer.py --models model_a_4h model_b_1d --mode sequential
```
**优点**: 资源利用稳定、错误隔离、易调试
**缺点**: 训练时间较长

### 🚀 并行训练 (Parallel)
**推荐场景**: 多GPU环境、效率优先
```bash
python multi_model_trainer.py --models model_a_4h model_b_1d --mode parallel --max-workers 2
```
**优点**: 训练时间短、资源利用率高
**缺点**: 需要多GPU、资源竞争

### 🎯 阶段训练 (Stage-wise)
**场景**: 分阶段训练、资源优化
```bash
# 只训练tokenizer
python multi_model_trainer.py --models model_a_4h model_b_1d --stage tokenizer

# 然后训练predictor
python multi_model_trainer.py --models model_a_4h model_b_1d --stage predictor
```

## 📈 监控和日志

### 🎯 Comet ML监控
每个模型都有独立的Comet ML实验:
- **Model A**: 标签为 `model_a_4h_finetune`
- **Model B**: 标签为 `model_b_1d_macro_finetune`

设置环境变量:
```bash
export COMET_API_KEY="your_api_key"
export COMET_WORKSPACE="your_workspace"
```

### 📋 日志系统
- **训练日志**: `logs/multi_model_training/`
- **模型输出**: `outputs/models/`
- **回测结果**: `outputs/backtest_results/`

### 📊 训练报告
```bash
# 训练完成后自动生成
cat logs/multi_model_training/training_report_*.txt
```

## 🔧 高级配置

### 添加新模型
1. **创建配置文件**: `config_model_C_XXX.py`
2. **注册配置**: 在 `config_manager.py` 中添加
3. **测试配置**: `python test_multi_config.py`
4. **开始训练**: 使用新配置名称

### 自定义环境变量
```bash
# 预训练模型路径
export KRONOS_TOKENIZER_PATH="/path/to/tokenizer"
export KRONOS_PREDICTOR_PATH="/path/to/predictor"

# 数据路径
export KRONOS_DATA_PATH="/path/to/data"

# 输出路径
export KRONOS_OUTPUT_PATH="/path/to/outputs"
```

### GPU配置优化
```bash
# 单GPU训练
torchrun --standalone --nproc_per_node=1 train_tokenizer_multi.py --config model_a_4h

# 多GPU训练
torchrun --standalone --nproc_per_node=4 train_tokenizer_multi.py --config model_a_4h

# 多节点训练
torchrun --nnodes=2 --nproc_per_node=2 --rdzv_id=100 --rdzv_backend=c10d train_tokenizer_multi.py --config model_a_4h
```

## 🧪 测试和验证

### 配置测试
```bash
python test_multi_config.py
```
测试内容:
- ✅ 配置文件加载
- ✅ 配置差异验证  
- ✅ 目录创建测试
- ✅ 脚本语法检查
- ✅ 依赖导入测试

### 训练测试
```bash
# 干运行测试
python multi_model_trainer.py --dry-run

# 单模型测试
torchrun --standalone --nproc_per_node=1 train_tokenizer_multi.py --config model_a_4h
```

## 🚨 故障排除

### 常见问题及解决方案

#### ❌ 配置加载失败
```
Error: Configuration validation failed
```
**解决**: 检查数据路径是否存在，运行数据准备脚本

#### ❌ CUDA内存不足
```
CUDA out of memory
```
**解决**: 
- 减少 `batch_size`
- 增加 `accumulation_steps`
- 使用梯度检查点

#### ❌ 依赖关系错误
```
Predictor requires tokenizer
```
**解决**: 先训练tokenizer或设置正确的预训练模型路径

#### ❌ 分布式训练失败
```
ProcessGroupNCCL initialization failed
```
**解决**: 
- 检查GPU可用性: `nvidia-smi`
- 检查NCCL配置: `python -c "import torch; print(torch.cuda.nccl.version())"`
- 设置环境变量: `export NCCL_DEBUG=INFO`

### 调试技巧
```bash
# 启用详细日志
export TORCH_DISTRIBUTED_DEBUG=DETAIL

# 检查配置
python -c "from config_manager import ConfigManager; cm = ConfigManager(); config = cm.load_config('model_a_4h'); print(config.get_model_info())"

# 测试导入
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"
```

## 📚 最佳实践

### 🎯 训练流程建议
1. **环境准备** → `quick_start_multi_model.py`
2. **配置测试** → `test_multi_config.py` 
3. **干运行测试** → `--dry-run`
4. **tokenizer训练** → 优先训练所有tokenizer
5. **predictor训练** → 然后训练predictor
6. **监控验证** → 检查Comet ML和日志

### ⚡ 性能优化
- **数据预处理**: 提前准备好所有数据文件
- **混合精度**: 在配置中启用AMP
- **批量调优**: 根据GPU内存调整batch_size
- **学习率调度**: 使用warmup和cosine调度

### 🔒 安全实践
- 使用环境变量存储API密钥
- 定期备份训练好的模型
- 版本控制配置文件变更
- 监控资源使用情况

## 🎊 总结

您现在拥有了一个**企业级**的Kronos多模型微调平台，具备以下能力:

### ✅ 已实现的功能
- **2个生产就绪的模型配置** (4H技术分析 + 1D宏观分析)
- **完全配置驱动的架构** (添加新模型只需配置文件)
- **多种训练模式** (顺序/并行/阶段化训练)
- **完整的监控体系** (Comet ML + 详细日志)
- **自动化测试套件** (配置验证 + 功能测试)
- **用户友好的接口** (交互式启动 + 命令行工具)

### 🚀 下一步行动
1. **立即开始**: `python quick_start_multi_model.py`
2. **准备数据**: 确保您的Kronos格式数据已准备好
3. **选择模型**: 从4H技术模型或1D宏观模型开始
4. **监控训练**: 使用Comet ML观察训练进度
5. **扩展平台**: 根据需要添加更多时间框架的模型

### 📞 技术支持
- **详细文档**: `Kronos/finetune/README_MULTI_MODEL.md`
- **配置测试**: `python test_multi_config.py`
- **交互启动**: `python quick_start_multi_model.py`

**🎉 恭喜！您的Kronos多模型微调平台已经准备就绪！**





