#!/usr/bin/env python3
"""
调试脚本：检查tokenizer输出格式
"""

import sys
import torch
sys.path.append("./Kronos/")
sys.path.append("./Kronos/finetune/")

from config_model_A_4H import Config
from dataset import QlibDataset
from model.kronos import KronosTokenizer
from torch.utils.data import DataLoader

def debug_tokenizer():
    """调试tokenizer输出"""
    print("🔍 调试Tokenizer输出格式")
    print("=" * 50)
    
    # 直接创建配置
    config = Config()
    # 修改数据集路径
    config.dataset_path = "./data/kronos_datasets/model_a_4h_full"
    
    # 设置设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"设备: {device}")
    
    # 加载tokenizer
    tokenizer_path = "./Kronos/finetune/outputs/models/model_a_4h/tokenizer_model_a_4h/checkpoints/best_model"
    print(f"加载tokenizer: {tokenizer_path}")
    tokenizer = KronosTokenizer.from_pretrained(tokenizer_path)
    tokenizer.to(device)
    tokenizer.eval()
    
    print(f"Tokenizer参数:")
    print(f"  s1_bits: {tokenizer.s1_bits}")
    print(f"  s2_bits: {tokenizer.s2_bits}")
    print(f"  codebook_dim: {tokenizer.codebook_dim}")
    
    # 创建测试数据
    dataset = QlibDataset('train', config=config)
    dataloader = DataLoader(dataset, batch_size=2, shuffle=False)
    
    # 获取一个batch
    batch = next(iter(dataloader))
    x_tensor, x_stamp_tensor = batch
    x_tensor = x_tensor.to(device)
    
    print(f"\n输入数据形状:")
    print(f"  x_tensor: {x_tensor.shape}")
    print(f"  x_stamp_tensor: {x_stamp_tensor.shape}")
    
    # 运行tokenizer
    with torch.no_grad():
        outputs, bsq_loss, quantized, z_indices = tokenizer(x_tensor)
        
        print(f"\nTokenizer输出:")
        print(f"  outputs类型: {type(outputs)}")
        if isinstance(outputs, tuple):
            print(f"  outputs长度: {len(outputs)}")
            for i, out in enumerate(outputs):
                print(f"    outputs[{i}]: {out.shape}")
        else:
            print(f"  outputs形状: {outputs.shape}")
        
        print(f"  bsq_loss: {bsq_loss}")
        print(f"  quantized形状: {quantized.shape}")
        print(f"  z_indices形状: {z_indices.shape}")
        
        print(f"\nz_indices详细信息:")
        print(f"  数据类型: {z_indices.dtype}")
        print(f"  数值范围: [{z_indices.min().item():.4f}, {z_indices.max().item():.4f}]")
        print(f"  前几个值: {z_indices[0, 0, :10]}")
        
        # 尝试分离s1和s2
        s1_bits = tokenizer.s1_bits
        s2_bits = tokenizer.s2_bits
        
        print(f"\n分离s1和s2:")
        print(f"  s1_bits: {s1_bits}, s2_bits: {s2_bits}")
        
        if z_indices.dim() == 3:
            s1_indices = z_indices[:, :, :s1_bits]
            s2_indices = z_indices[:, :, s1_bits:]
            
            print(f"  s1_indices形状: {s1_indices.shape}")
            print(f"  s2_indices形状: {s2_indices.shape}")
            
            # 检查是否是二进制数据
            unique_values = torch.unique(z_indices)
            print(f"  z_indices唯一值: {unique_values}")
            
            if len(unique_values) == 2 and 0 in unique_values and 1 in unique_values:
                print("  ✅ z_indices是二进制数据")
                # 将二进制转换为整数
                s1_ids = torch.sum(s1_indices * (2 ** torch.arange(s1_bits, device=device)), dim=-1)
                s2_ids = torch.sum(s2_indices * (2 ** torch.arange(s2_bits, device=device)), dim=-1)
                
                print(f"  s1_ids形状: {s1_ids.shape}, 范围: [{s1_ids.min()}, {s1_ids.max()}]")
                print(f"  s2_ids形状: {s2_ids.shape}, 范围: [{s2_ids.min()}, {s2_ids.max()}]")
            else:
                print("  ❌ z_indices不是二进制数据")
                print("  尝试使用argmax...")
                s1_ids = torch.argmax(s1_indices, dim=-1)
                s2_ids = torch.argmax(s2_indices, dim=-1)
                print(f"  s1_ids形状: {s1_ids.shape}")
                print(f"  s2_ids形状: {s2_ids.shape}")
        else:
            print(f"  ❌ z_indices维度不是3: {z_indices.dim()}")

if __name__ == "__main__":
    debug_tokenizer()