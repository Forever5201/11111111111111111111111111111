# OKX数据转Kronos微调格式指南

## 🎯 概述

本指南说明如何将OKX的BTC K线数据转换为Kronos微调所需的格式。通过修改现有的`get_data.py`脚本，我们可以直接输出符合Kronos要求的数据格式。

## 📊 Kronos数据格式要求

Kronos微调需要以下格式的数据：

### 存储格式
- **文件类型**: pickle文件 (`.pkl`)
- **文件结构**: 
  ```
  data/kronos_datasets/
  ├── train_data.pkl
  ├── val_data.pkl
  ├── test_data.pkl
  └── dataset_summary.json
  ```

### 数据结构
```python
# 每个pickle文件包含一个字典
{
    "BTC-USD-SWAP_1H": DataFrame,  # 1小时K线数据
    "BTC-USD-SWAP_4H": DataFrame,  # 4小时K线数据
    "BTC-USD-SWAP_1D": DataFrame   # 1天K线数据
}
```

### DataFrame格式
```python
# DataFrame必须包含以下列
columns = ['open', 'high', 'low', 'close', 'vol', 'amt']
# 索引必须是datetime类型
index = DatetimeIndex(name='datetime')
```

### 字段映射
| OKX字段 | Kronos字段 | 说明 |
|---------|------------|------|
| `open` | `open` | 开盘价 |
| `high` | `high` | 最高价 |
| `low` | `low` | 最低价 |
| `close` | `close` | 收盘价 |
| `volume` | `vol` | 成交量 |
| `currency_volume` | `amt` | 成交额 |

## 🚀 使用方法

### 方法1: 使用修改后的get_data.py

```bash
# 生成Kronos微调数据
python src/get_data.py --kronos

# 生成常规JSON数据（默认）
python src/get_data.py
```

### 方法2: 使用简化脚本

```bash
# 使用交互式脚本
python prepare_kronos_data_simple.py
```

## ⚙️ 配置说明

### 环境变量设置
在`.env`文件中设置OKX API凭证：
```env
OKX_API_KEY=your_api_key
OKX_API_SECRET=your_secret_key
OKX_API_PASSPHRASE=your_passphrase
```

### 默认参数
- **交易对**: BTC-USD-SWAP
- **时间框架**: 1H, 4H, 1D
- **每个时间框架记录数**: 2000条
- **数据分割比例**: 70% 训练, 15% 验证, 15% 测试

### 自定义参数
修改`src/get_data.py`中的`prepare_kronos_training_data()`函数:

```python
# 定义Kronos微调的时间框架和参数
symbol = "BTC-USD-SWAP"
timeframes = ["1H", "4H", "1D"]  # 可修改时间框架
records_per_timeframe = 2000     # 可修改记录数
```

## 📁 输出文件说明

### 数据文件
- `train_data.pkl`: 训练数据集
- `val_data.pkl`: 验证数据集  
- `test_data.pkl`: 测试数据集

### 元数据文件
- `dataset_summary.json`: 数据集摘要信息
  ```json
  {
    "train_symbols": 3,
    "val_symbols": 3,
    "test_symbols": 3,
    "total_train_records": 4200,
    "total_val_records": 900,
    "total_test_records": 900,
    "created_at": "2025-01-27T10:30:00",
    "symbols": ["BTC-USD-SWAP_1H", "BTC-USD-SWAP_4H", "BTC-USD-SWAP_1D"]
  }
  ```

## 🔄 集成到Kronos项目

### 步骤1: 复制数据文件
```bash
# 复制到Kronos项目数据目录
cp data/kronos_datasets/*.pkl Kronos/finetune/data/
```

### 步骤2: 配置Kronos
编辑`Kronos/finetune/config.py`:
```python
# 更新数据路径
self.dataset_path = "./data"

# 更新特征列表（确保与我们的数据匹配）
self.feature_list = ['open', 'high', 'low', 'close', 'vol', 'amt']
```

### 步骤3: 开始微调
```bash
cd Kronos

# 第一步：微调tokenizer
torchrun --standalone --nproc_per_node=1 finetune/train_tokenizer.py

# 第二步：微调predictor
torchrun --standalone --nproc_per_node=1 finetune/train_predictor.py
```

## 🛠️ 故障排除

### 常见问题

**1. API凭证错误**
```
Error: API credentials missing
```
**解决**: 检查`.env`文件中的OKX API凭证

**2. 数据获取失败**
```
Error: No data fetched for Kronos training
```
**解决**: 
- 检查网络连接
- 验证API权限
- 检查交易对是否正确

**3. 数据格式错误**
```
Error: Field currency_volume not found
```
**解决**: OKX API返回的字段可能有变化，检查数据获取器的字段映射

### 调试模式
在`src/get_data.py`中添加详细日志：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 数据验证

### 验证脚本
```python
import pickle
import pandas as pd

# 加载数据
with open('data/kronos_datasets/train_data.pkl', 'rb') as f:
    train_data = pickle.load(f)

# 检查数据结构
for symbol, df in train_data.items():
    print(f"{symbol}: {len(df)} records")
    print(f"Columns: {list(df.columns)}")
    print(f"Index type: {type(df.index)}")
    print(f"Date range: {df.index.min()} to {df.index.max()}")
    print("-" * 40)
```

## 🎉 成功指标

生成的数据应该满足以下条件：
- ✅ 包含3个pickle文件
- ✅ 每个文件包含3个时间框架的数据
- ✅ DataFrame有正确的列名和datetime索引
- ✅ 数据量充足（每个时间框架至少1000+条记录）
- ✅ 数据连续性良好（无大量缺失值）

## 📞 支持

如果遇到问题，请检查：
1. 日志文件：`logs/app.log`
2. 数据摘要：`data/kronos_datasets/dataset_summary.json`
3. 环境配置：`.env`文件

---

**注意**: 此功能直接修改了`get_data.py`，确保在生产环境中谨慎使用。
