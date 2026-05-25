#!/usr/bin/env python3
"""
修复所有OCR JSON文件中的空日期字段
从文件名中提取日期并写入JSON
"""

import json
from pathlib import Path

def fix_json_dates():
    data_dir = Path("api/v1/oil-price/data")
    json_files = sorted(data_dir.glob("oil_price_*.json"))
    
    print(f"找到 {len(json_files)} 个JSON文件")
    
    fixed = 0
    already_ok = 0
    
    for json_file in json_files:
        # 从文件名提取日期
        filename = json_file.stem  # oil_price_2017-11-02
        date_str = filename.replace("oil_price_", "")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if data.get("date") and data["date"] != "":
            already_ok += 1
            continue
        
        # 修复日期字段
        data["date"] = date_str
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        fixed += 1
        print(f"  修复: {json_file.name} -> date={date_str}")
    
    print(f"\n修复完成: {fixed} 个文件已修复, {already_ok} 个已是正确日期")

if __name__ == "__main__":
    fix_json_dates()
