#!/usr/bin/env python3
"""
测试小米MiMo API识别油价图片
处理3-5张图片，验证识别效果
"""

import os
import sys
import json
import time
import base64
import logging
from pathlib import Path
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 尝试导入openai库
try:
    from openai import OpenAI
except ImportError:
    logger.error("请先安装openai库: pip install openai")
    sys.exit(1)


def test_single_image(api_key: str, image_base64: str, filename: str) -> dict:
    """测试单张图片识别"""
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.xiaomimimo.com/v1"
        )
        
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
        
        logger.info(f"正在识别图片: {filename}")
        
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
                                "url": image_base64
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
            # 尝试直接解析
            parsed_data = json.loads(content)
        except json.JSONDecodeError:
            # 尝试提取JSON部分
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
            logger.info(f"识别成功: {len(parsed_data.get('regions', []))} 个地区")
            return {
                "success": True,
                "filename": filename,
                "data": parsed_data,
                "raw_response": content
            }
        else:
            logger.warning(f"JSON解析失败")
            return {
                "success": False,
                "filename": filename,
                "error": "JSON解析失败",
                "raw_response": content[:200] + "..."
            }
            
    except Exception as e:
        logger.error(f"识别失败: {e}")
        return {
            "success": False,
            "filename": filename,
            "error": str(e)
        }


def main():
    """主函数"""
    print("=== 测试小米MiMo API识别油价图片 ===")
    
    # 检查API密钥
    api_key = os.environ.get("MIMO_API_KEY")
    if not api_key:
        print("错误: 未设置MIMO_API_KEY环境变量")
        print("请先设置: $env:MIMO_API_KEY='your-api-key'")
        return
    
    # 测试图片列表（选择不同年份的图片）
    test_images = [
        "oil_price_2021-09-06.jpg",  # 2021年
        "oil_price_2022-01-17.jpg",  # 2022年
        "oil_price_2023-01-03.jpg",  # 2023年
        "oil_price_2024-01-03.png",  # 2024年
        "oil_price_2025-01-02.png"   # 2025年
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
    
    # 测试结果
    results = []
    successful = 0
    failed = 0
    
    print(f"\n开始测试 {len(test_images)} 张图片...")
    
    for i, filename in enumerate(test_images):
        print(f"\n[{i+1}/{len(test_images)}] 测试 {filename}")
        
        if filename not in image_map:
            print(f"  错误: 未找到 {filename} 的Base64编码")
            failed += 1
            results.append({
                "filename": filename,
                "success": False,
                "error": "未找到Base64编码"
            })
            continue
        
        image_info = image_map[filename]
        result = test_single_image(api_key, image_info['base64_with_prefix'], filename)
        
        results.append(result)
        
        if result['success']:
            successful += 1
            data = result['data']
            print(f"  成功: {len(data.get('regions', []))} 个地区")
            print(f"  日期: {data.get('date', '未提取')}")
            print(f"  标题: {data.get('title', '未提取')[:50]}...")
        else:
            failed += 1
            print(f"  失败: {result.get('error', '未知错误')}")
        
        # 添加延迟
        if i < len(test_images) - 1:
            time.sleep(2)
    
    # 打印统计
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
    print(f"总测试: {len(test_images)}")
    print(f"成功: {successful}")
    print(f"失败: {failed}")
    print(f"成功率: {successful/len(test_images)*100:.1f}%")
    
    # 保存结果
    output_file = Path(__file__).parent / "temp" / "mimo_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到: {output_file}")
    
    # 显示详细结果
    if successful > 0:
        print("\n=== 成功识别的图片详情 ===")
        for result in results:
            if result['success']:
                data = result['data']
                print(f"\n{result['filename']}:")
                print(f"  日期: {data.get('date', '未提取')}")
                print(f"  地区数量: {len(data.get('regions', []))}")
                
                # 显示前2个地区
                regions = data.get('regions', [])
                if regions:
                    print("  前2个地区:")
                    for region in regions[:2]:
                        print(f"    {region.get('name', '未知')}: "
                              f"汽油 {region.get('gasoline_price', '无')}元/吨, "
                              f"柴油 {region.get('diesel_price', '无')}元/吨")


if __name__ == "__main__":
    main()