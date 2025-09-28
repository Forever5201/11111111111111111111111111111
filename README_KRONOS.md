# OKX数据获取系统 - Kronos微调支持

## 🆕 新功能：Kronos微调数据支持

现在你的OKX数据获取系统已经支持直接生成Kronos微调所需的数据格式！

## 🚀 快速开始

### 一键启动 (推荐)
```bash
python quick_start_kronos.py
```

### 手动操作
```bash
# 1. 生成Kronos格式数据
python src/get_data.py --kronos

# 2. 测试数据格式
python test_kronos_integration.py

# 3. 复制到Kronos项目
cp data/kronos_datasets/*.pkl Kronos/finetune/data/

# 4. 开始微调
cd Kronos
torchrun --standalone --nproc_per_node=1 finetune/train_tokenizer.py
torchrun --standalone --nproc_per_node=1 finetune/train_predictor.py
```

## 📊 功能特点

✅ **直接转换**: 修改现有`get_data.py`，直接输出Kronos格式  
✅ **字段映射**: 自动处理OKX → Kronos字段映射  
✅ **时间特征**: 自动生成Kronos需要的时间特征  
✅ **数据分割**: 按时间顺序分割训练/验证/测试集  
✅ **格式验证**: 内置数据格式验证功能  
✅ **兼容性**: 保持原有JSON输出功能不变  

## 📁 输出文件

```
data/kronos_datasets/
├── train_data.pkl      # 训练集 (70%)
├── val_data.pkl        # 验证集 (15%)
├── test_data.pkl       # 测试集 (15%)
└── dataset_summary.json # 数据摘要
```

## ⚙️ 配置说明

### 默认设置
- **交易对**: BTC-USD-SWAP
- **时间框架**: 1H, 4H, 1D
- **每个时间框架**: 2000条记录
- **数据分割**: 70% / 15% / 15%

### 字段映射
| OKX | → | Kronos | 说明 |
|-----|---|--------|------|
| `volume` | → | `vol` | 成交量 |
| `currency_volume` | → | `amt` | 成交额 |

## 🛠️ 工具脚本

| 脚本 | 功能 | 使用方法 |
|------|------|----------|
| `quick_start_kronos.py` | 一键完成所有步骤 | `python quick_start_kronos.py` |
| `prepare_kronos_data_simple.py` | 交互式数据准备 | `python prepare_kronos_data_simple.py` |
| `test_kronos_integration.py` | 测试数据格式 | `python test_kronos_integration.py` |

## 📖 详细文档

查看完整指南: [KRONOS_DATA_GUIDE.md](KRONOS_DATA_GUIDE.md)

## 🔄 兼容性

- ✅ **向后兼容**: 原有JSON输出功能保持不变
- ✅ **Kronos兼容**: 完全符合Kronos v1.0微调数据格式
- ✅ **Python 3.8+**: 支持主流Python版本

## 🆘 故障排除

### 常见问题

**Q: 运行时提示API凭证错误？**  
A: 检查`.env`文件中的OKX API设置

**Q: 生成的数据无法被Kronos识别？**  
A: 运行测试脚本验证格式: `python test_kronos_integration.py`

**Q: 数据量太少？**  
A: 修改`src/get_data.py`中的`records_per_timeframe`参数

### 获取帮助

1. 查看日志: `logs/app.log`
2. 检查数据摘要: `data/kronos_datasets/dataset_summary.json`
3. 运行测试: `python test_kronos_integration.py`

---

**注意**: 此功能扩展了现有系统，不影响原有功能的使用。
