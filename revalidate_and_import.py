#!/usr/bin/env python3
"""
重新验证并导入油价数据到数据库
"""

import json
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from processors.ocr_processor import OilPriceOCRProcessor
from database.oil_price_db import OilPriceDatabase


def revalidate_and_import():
    """重新验证所有JSON文件并导入数据库"""
    print("=== 重新验证并导入油价数据 ===")
    
    processor = OilPriceOCRProcessor()
    db = OilPriceDatabase()
    
    data_dir = project_root / "api" / "v1" / "oil-price" / "data"
    json_files = sorted(data_dir.glob("oil_price_*.json"))
    
    print(f"找到 {len(json_files)} 个JSON文件")
    
    imported = 0
    failed = 0
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data.get("success"):
                print(f"  跳过 {json_file.name}: OCR识别失败")
                failed += 1
                continue
            
            # 确保日期字段存在
            if not data.get("date"):
                filename = json_file.stem
                date_str = filename.replace("oil_price_", "")
                data["date"] = date_str
            
            # 重新验证数据
            validation = processor.validate_data(data)
            data["validation"] = validation
            
            # 更新JSON文件中的验证结果
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 插入数据库
            db.insert_announcement(data)
            imported += 1
            
            is_valid = validation.get("is_valid", False)
            regions_count = len(data.get("regions", []))
            print(f"  {json_file.name}: {regions_count}个地区, 有效={is_valid}")
            
        except Exception as e:
            print(f"  失败 {json_file.name}: {e}")
            failed += 1
    
    print(f"\n导入完成: 成功 {imported}, 失败 {failed}")
    
    # 显示统计
    stats = db.get_statistics()
    print(f"\n=== 数据库统计 ===")
    print(f"公告数量: {stats['announcements_count']}")
    print(f"成功公告: {stats['successful_announcements']}")
    print(f"地区数据: {stats['regions_count']}")
    print(f"有效数据: {stats['valid_data_count']}")
    print(f"最新日期: {stats['latest_date']}")
    print(f"最旧日期: {stats['oldest_date']}")


if __name__ == "__main__":
    revalidate_and_import()
