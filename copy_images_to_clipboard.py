#!/usr/bin/env python3
"""
将图片复制到剪贴板的工具
支持批量选择图片，逐个复制到剪贴板供ChatGPT使用
"""

import os
import sys
import time
import json
import ctypes
from pathlib import Path
from typing import List

# Windows剪贴板操作
CF_BITMAP = 2
CF_DIB = 8

def copy_image_to_clipboard(image_path: str):
    """将图片复制到Windows剪贴板"""
    try:
        from PIL import Image
        import win32clipboard
        import io
        
        # 打开图片
        img = Image.open(image_path)
        
        # 转换为BMP格式（剪贴板需要）
        output = io.BytesIO()
        img.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]  # 去掉BMP文件头
        output.close()
        
        # 复制到剪贴板
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(CF_DIB, data)
        win32clipboard.CloseClipboard()
        
        return True
    except ImportError:
        print("需要安装依赖: pip install Pillow pywin32")
        return False
    except Exception as e:
        print(f"复制失败: {e}")
        return False


def get_pending_images() -> List[dict]:
    """获取待处理的图片列表"""
    image_dir = Path("api/v1/oil-price/images")
    data_dir = Path("api/v1/oil-price/data")
    
    # 获取所有图片
    all_images = sorted(image_dir.glob("oil_price_*"))
    
    # 获取已处理的数据
    processed = set()
    if data_dir.exists():
        for f in data_dir.glob("oil_price_*.json"):
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                if data.get("success") and data.get("regions"):
                    date_str = f.stem.replace("oil_price_", "")
                    processed.add(date_str)
            except:
                pass
    
    # 筛选未处理的图片
    pending = []
    for img in all_images:
        stem = img.stem
        date_str = stem.replace("oil_price_", "")
        if date_str not in processed:
            pending.append({
                "path": str(img),
                "date": date_str,
                "filename": img.name
            })
    
    return pending


def main():
    """主函数"""
    print("=" * 60)
    print("ChatGPT 图片复制助手")
    print("=" * 60)
    
    # 检查依赖
    try:
        import win32clipboard
        from PIL import Image
    except ImportError:
        print("\n需要安装依赖包:")
        print("pip install Pillow pywin32")
        print("\n安装后重新运行此脚本")
        return
    
    # 获取待处理图片
    pending = get_pending_images()
    print(f"\n待处理图片: {len(pending)} 张")
    
    if not pending:
        print("没有待处理的图片！")
        return
    
    # 显示图片列表
    print("\n可用图片:")
    for i, img in enumerate(pending[:30], 1):
        print(f"  {i:3d}. {img['date']}")
    
    if len(pending) > 30:
        print(f"  ... 还有 {len(pending) - 30} 张")
    
    # 用户选择
    print("\n" + "-" * 60)
    print("操作说明:")
    print("  - 输入图片编号（如: 1,3,5 或 1-10）")
    print("  - 输入 'all' 处理所有图片")
    print("  - 输入 'q' 退出")
    print("-" * 60)
    
    while True:
        choice = input("\n请选择: ").strip()
        
        if choice.lower() == 'q':
            break
        
        # 解析选择
        selected_indices = []
        
        if choice.lower() == 'all':
            selected_indices = list(range(len(pending)))
        else:
            # 解析编号
            parts = choice.replace('，', ',').split(',')
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # 范围选择
                    try:
                        start, end = part.split('-')
                        start_idx = int(start) - 1
                        end_idx = int(end)
                        selected_indices.extend(range(start_idx, min(end_idx, len(pending))))
                    except:
                        print(f"无效范围: {part}")
                else:
                    try:
                        idx = int(part) - 1
                        if 0 <= idx < len(pending):
                            selected_indices.append(idx)
                        else:
                            print(f"无效编号: {part}")
                    except:
                        print(f"无效输入: {part}")
        
        if not selected_indices:
            print("未选择任何图片")
            continue
        
        # 限制每次最多10张
        if len(selected_indices) > 10:
            print(f"最多选择10张图片，已截取前10张")
            selected_indices = selected_indices[:10]
        
        # 复制图片
        selected_images = [pending[i] for i in selected_indices]
        
        print(f"\n将复制 {len(selected_images)} 张图片:")
        for img in selected_images:
            print(f"  - {img['date']}")
        
        print("\n开始复制...")
        print("（复制后请立即到ChatGPT中粘贴）")
        
        for i, img in enumerate(selected_images, 1):
            print(f"\n[{i}/{len(selected_images)}] 复制 {img['date']}...")
            
            if copy_image_to_clipboard(img['path']):
                print(f"  ✓ 已复制到剪贴板")
                
                if i < len(selected_images):
                    print(f"  请在ChatGPT中粘贴（Ctrl+V），然后按Enter继续...")
                    input()
            else:
                print(f"  ✗ 复制失败")
        
        print("\n" + "=" * 60)
        print("所有图片复制完成！")
        print("请在ChatGPT中发送消息，然后使用网页工具解析结果")
        print("=" * 60)
        
        # 询问是否继续
        cont = input("\n继续选择图片？(y/n): ").strip()
        if cont.lower() != 'y':
            break


if __name__ == "__main__":
    main()
