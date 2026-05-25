#!/usr/bin/env python3
"""
测试本地OCR处理单张图片
"""

import json
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from batch_process_local_ocr import LocalOCRProcessor

def test_single_image():
    """测试处理单张图片"""
    processor = LocalOCRProcessor()
    
    # 测试图片
    image_path = project_root / "api" / "v1" / "oil-price" / "images" / "oil_price_2026-05-21.png"
    date_str = "2026-05-21"
    
    print(f"测试处理图片: {image_path}")
    print("=" * 50)
    
    result = processor.process_single_image(image_path, date_str)
    
    if result:
        print(f"处理成功: {result.get('success', False)}")
        
        if result.get('success'):
            print(f"标题: {result.get('title', '无')}")
            print(f"副标题: {result.get('subtitle', '无')}")
            print(f"日期: {result.get('date', '无')}")
            print(f"地区数量: {len(result.get('regions', []))}")
            print(f"OCR文本长度: {result.get('ocr_text_length', 0)}")
            
            # 显示前3个地区
            regions = result.get('regions', [])
            if regions:
                print("\n前3个地区:")
                for i, region in enumerate(regions[:3]):
                    print(f"  {i+1}. {region['name']}: 汽油 {region.get('gasoline_price', '无')}元/吨, 柴油 {region.get('diesel_price', '无')}元/吨")
            
            # 保存结果
            output_file = project_root / "api" / "v1" / "oil-price" / "data" / f"test_{date_str}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n结果已保存到: {output_file}")
        else:
            print(f"错误: {result.get('error', '未知错误')}")
    else:
        print("处理返回None")

if __name__ == "__main__":
    test_single_image()