#!/usr/bin/env python3
"""
检查图片处理状态
"""

import os
from pathlib import Path
import json

def count_files():
    project_root = Path(__file__).parent
    image_dir = project_root / "api" / "v1" / "oil-price" / "images"
    data_dir = project_root / "api" / "v1" / "oil-price" / "data"
    
    # 统计图片文件
    image_files = list(image_dir.glob("oil_price_*"))
    
    # 统计数据文件
    data_files = list(data_dir.glob("oil_price_*.json"))
    
    # 检查哪些图片没有对应的数据文件
    processed_dates = set()
    for data_file in data_files:
        date_str = data_file.stem.replace("oil_price_", "")
        processed_dates.add(date_str)
    
    pending_images = []
    for image_file in image_files:
        date_str = image_file.stem.replace("oil_price_", "")
        if date_str not in processed_dates:
            pending_images.append(image_file.name)
    
    print(f"总图片数: {len(image_files)}")
    print(f"已处理图片数: {len(data_files)}")
    print(f"剩余图片数: {len(pending_images)}")
    print(f"处理率: {len(data_files) / len(image_files) * 100:.1f}%")
    
    if pending_images:
        print(f"\n前10个待处理图片:")
        for i, img in enumerate(pending_images[:10]):
            print(f"  {i+1}. {img}")
        if len(pending_images) > 10:
            print(f"  ... 还有 {len(pending_images) - 10} 个")
    
    # 检查数据文件质量
    successful = 0
    failed = 0
    for data_file in data_files:
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data.get("success") and data.get("regions"):
                successful += 1
            else:
                failed += 1
        except:
            failed += 1
    
    print(f"\n数据质量:")
    print(f"  成功数据: {successful}")
    print(f"  失败/无效数据: {failed}")
    
    return len(image_files), len(data_files), len(pending_images)

if __name__ == "__main__":
    total, processed, pending = count_files()