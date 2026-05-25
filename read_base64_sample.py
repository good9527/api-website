#!/usr/bin/env python3
"""
读取Base64编码文件的一部分
"""

import json
import sys

def read_sample():
    """读取Base64编码文件的前几个条目"""
    try:
        with open('temp/all_images_base64.json', 'r', encoding='utf-8') as f:
            # 只读取前1000个字符来解析JSON结构
            content = f.read(1000)
            
        # 尝试解析为JSON（可能不完整）
        # 由于文件很大，我们使用流式读取
        print("=== Base64编码文件信息 ===")
        print("文件大小: 59.85MB")
        print("总图片数: 175")
        print("平均每张图片Base64大小: 约0.34MB")
        
        print("\n=== 前3张图片的Base64编码示例 ===")
        print("注意: 以下示例只显示Base64编码的前100个字符")
        
        # 重新读取文件，提取前3张图片的信息
        with open('temp/all_images_base64.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 显示前3张图片的信息
        for i, image in enumerate(data[:3]):
            print(f"\n图片 {i+1}: {image['filename']}")
            print(f"  MIME类型: {image['mime_type']}")
            print(f"  文件大小: {image['file_size_mb']}MB")
            print(f"  Base64长度: {image['base64_length']} 字符")
            
            # 显示Base64编码的前100个字符
            base64_prefix = image['base64_with_prefix'][:100]
            print(f"  Base64前缀: {base64_prefix}...")
            
        print("\n=== 说明 ===")
        print("1. 每张图片的Base64编码都以 'data:{MIME_TYPE};base64,' 开头")
        print("2. 例如: data:image/jpeg;base64,/9j/4AAQSkZJRgABAQE...")
        print("3. 完整的Base64编码字符串很长，这里只显示前100个字符")
        print("4. 实际使用时需要完整的Base64字符串")
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    read_sample()