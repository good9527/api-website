#!/usr/bin/env python3
"""
批量处理所有油价图片的OCR识别
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from processors.ocr_processor import OilPriceOCRProcessor

def batch_process_ocr():
    """批量处理所有图片的OCR识别"""
    print("=== 批量处理油价图片OCR识别 ===")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 初始化OCR处理器
    processor = OilPriceOCRProcessor()
    
    # 图片目录
    image_dir = project_root / "api" / "v1" / "oil-price" / "images"
    data_dir = project_root / "api" / "v1" / "oil-price" / "data"
    
    # 确保数据目录存在
    data_dir.mkdir(exist_ok=True)
    
    # 获取所有图片文件
    image_files = sorted(image_dir.glob("oil_price_*"))
    
    print(f"找到 {len(image_files)} 个图片文件")
    print(f"数据将保存到: {data_dir}")
    
    # 统计信息
    total_processed = 0
    successful = 0
    failed = 0
    skipped = 0
    
    # 处理每个图片
    for i, image_file in enumerate(image_files, 1):
        # 提取日期
        filename = image_file.name
        date_str = filename.replace("oil_price_", "").replace(".png", "").replace(".jpg", "")
        
        # 检查是否已经处理过
        data_file = data_dir / f"oil_price_{date_str}.json"
        if data_file.exists():
            skipped += 1
            print(f"[{i}/{len(image_files)}] 跳过 {date_str} (已存在)")
            continue
        
        print(f"[{i}/{len(image_files)}] 处理 {date_str}...")
        
        try:
            # 处理图片
            result = processor.process_image(str(image_file))
            
            # 保存结果
            if result.get("success"):
                with open(data_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                successful += 1
                regions_count = len(result.get("regions", []))
                print(f"  成功: {regions_count} 个地区")
            else:
                failed += 1
                error_msg = result.get("error", "未知错误")
                print(f"  失败: {error_msg}")
            
            total_processed += 1
            
            # 添加延迟，避免API限制
            if i < len(image_files):
                time.sleep(2)  # 每次请求间隔2秒
                
        except Exception as e:
            failed += 1
            print(f"  错误: {e}")
            total_processed += 1
    
    # 打印统计信息
    print("\n=== 处理完成 ===")
    print(f"总图片数: {len(image_files)}")
    print(f"已处理: {total_processed}")
    print(f"成功: {successful}")
    print(f"失败: {failed}")
    print(f"跳过: {skipped}")
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 生成处理报告
    generate_processing_report(image_files, data_dir)

def generate_processing_report(image_files, data_dir):
    """生成处理报告"""
    print("\n=== 处理报告 ===")
    
    # 统计数据文件
    data_files = list(data_dir.glob("oil_price_*.json"))
    
    print(f"图片文件数: {len(image_files)}")
    print(f"数据文件数: {len(data_files)}")
    
    # 计算处理率
    processing_rate = len(data_files) / len(image_files) * 100 if image_files else 0
    print(f"处理率: {processing_rate:.1f}%")
    
    # 分析数据质量
    successful_data = []
    failed_data = []
    
    for data_file in data_files:
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if data.get("success"):
                successful_data.append(data)
            else:
                failed_data.append(data_file.name)
        except Exception as e:
            failed_data.append(data_file.name)
    
    print(f"成功数据: {len(successful_data)}")
    print(f"失败数据: {len(failed_data)}")
    
    # 统计地区数据
    if successful_data:
        total_regions = sum(len(d.get("regions", [])) for d in successful_data)
        avg_regions = total_regions / len(successful_data)
        print(f"总地区数: {total_regions}")
        print(f"平均每页地区数: {avg_regions:.1f}")
    
    # 保存报告
    report = {
        "generated_at": datetime.now().isoformat(),
        "image_files_count": len(image_files),
        "data_files_count": len(data_files),
        "processing_rate": processing_rate,
        "successful_data_count": len(successful_data),
        "failed_data_count": len(failed_data),
        "failed_files": failed_data,
        "total_regions": total_regions if successful_data else 0,
        "average_regions_per_page": avg_regions if successful_data else 0
    }
    
    report_file = data_dir / "processing_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n处理报告已保存到: {report_file}")

if __name__ == "__main__":
    batch_process_ocr()