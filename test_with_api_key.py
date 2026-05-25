#!/usr/bin/env python3
"""
临时使用API密钥测试图片识别
注意：此脚本不会保存API密钥到文件
"""

import os
import sys
import json
import time
import getpass
from pathlib import Path

# 尝试导入openai库
try:
    from openai import OpenAI
except ImportError:
    print("请先安装openai库: pip install openai")
    sys.exit(1)


def test_with_api_key():
    """使用API密钥测试图片识别"""
    print("=== 临时使用API密钥测试 ===")
    print("⚠️  安全提示：API密钥不会被保存到文件中")
    print()
    
    # 获取API密钥
    api_key = getpass.getpass("请输入小米MiMo API密钥: ").strip()
    if not api_key:
        print("❌ 未输入API密钥")
        return
    
    print(f"✅ 已收到API密钥: {api_key[:8]}...{api_key[-4:]}")
    print()
    
    # 测试图片列表
    test_images = [
        "oil_price_2021-09-06.jpg",
        "oil_price_2022-01-17.jpg",
        "oil_price_2023-01-03.jpg"
    ]
    
    # 读取Base64编码数据
    base64_file = Path(__file__).parent / "temp" / "all_images_base64.json"
    
    try:
        with open(base64_file, 'r', encoding='utf-8') as f:
            all_images = json.load(f)
        
        # 创建文件名到Base64数据的映射
        image_map = {img['filename']: img for img in all_images}
        
    except Exception as e:
        print(f"读取Base64数据失败: {e}")
        return
    
    # 初始化客户端
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.xiaomimimo.com/v1"
        )
        print("✅ API客户端初始化成功")
    except Exception as e:
        print(f"❌ API客户端初始化失败: {e}")
        return
    
    # 测试识别
    print(f"\n开始测试 {len(test_images)} 张图片...")
    
    results = []
    successful = 0
    
    for i, filename in enumerate(test_images):
        print(f"\n[{i+1}/{len(test_images)}] 测试 {filename}")
        
        if filename not in image_map:
            print(f"  错误: 未找到 {filename} 的Base64编码")
            continue
        
        image_info = image_map[filename]
        
        try:
            # 构建提示词
            prompt = """请识别这张国内成品油价格表图片，提取以下信息：
1. 日期（从标题或内容中提取，格式：YYYY-MM-DD）
2. 标题
3. 地区数据（包括地区名称、汽油价格、柴油价格、所属区域）

请按以下JSON格式输出：
{
  "date": "YYYY-MM-DD",
  "title": "表格标题",
  "regions": [
    {
      "name": "地区名称",
      "gasoline_price": 数字（元/吨）,
      "diesel_price": 数字（元/吨）或null,
      "section": "一省一价 或 暂不实行一省一价"
    }
  ],
  "notes": ["注释内容"]
}

注意：
1. 价格单位是元/吨
2. 如果某个价格在图片中没有显示，设为null
3. 地区名称保持原样，不要修改
4. 日期从图片标题或内容中提取
5. 请只输出JSON，不要其他解释文字"""
            
            # 调用API
            print("  正在调用API...")
            completion = client.chat.completions.create(
                model="mimo-v2.5",
                messages=[
                    {
                        "role": "system",
                        "content": "You are MiMo, an AI assistant developed by Xiaomi. Today is date: 2026-05-25. Your knowledge cutoff date is December 2024."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_info['base64_with_prefix']
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                max_completion_tokens=4096
            )
            
            content = completion.choices[0].message.content
            
            # 尝试解析JSON
            try:
                parsed_data = json.loads(content)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    try:
                        parsed_data = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        parsed_data = None
                else:
                    parsed_data = None
            
            if parsed_data:
                print(f"  ✅ 识别成功: {len(parsed_data.get('regions', []))} 个地区")
                print(f"  日期: {parsed_data.get('date', '未提取')}")
                print(f"  标题: {parsed_data.get('title', '未提取')[:50]}...")
                
                results.append({
                    "filename": filename,
                    "success": True,
                    "data": parsed_data
                })
                successful += 1
            else:
                print(f"  ⚠️  JSON解析失败")
                print(f"  原始响应: {content[:100]}...")
                
                results.append({
                    "filename": filename,
                    "success": False,
                    "error": "JSON解析失败",
                    "raw_response": content[:200]
                })
            
            # 添加延迟
            if i < len(test_images) - 1:
                time.sleep(2)
                
        except Exception as e:
            print(f"  ❌ 识别失败: {e}")
            results.append({
                "filename": filename,
                "success": False,
                "error": str(e)
            })
    
    # 打印统计
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
    print(f"总测试: {len(test_images)}")
    print(f"成功: {successful}")
    print(f"失败: {len(test_images) - successful}")
    print(f"成功率: {successful/len(test_images)*100:.1f}%")
    
    # 保存结果（不保存API密钥）
    output_file = Path(__file__).parent / "temp" / "api_key_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到: {output_file}")
    
    # 提供下一步建议
    if successful > 0:
        print("\n=== 下一步建议 ===")
        print("1. 检查识别结果是否准确")
        print("2. 如果准确，可以运行批量处理脚本:")
        print("   python batch_process_mimo_vision.py")
        print("3. 批量处理前请设置环境变量:")
        print("   $env:MIMO_API_KEY='your-api-key-here'")
    else:
        print("\n=== 建议 ===")
        print("1. 检查API密钥是否正确")
        print("2. 检查网络连接")
        print("3. 查看API文档: https://api.xiaomimimo.com/docs")


if __name__ == "__main__":
    test_with_api_key()