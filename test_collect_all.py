#!/usr/bin/env python3
"""
测试采集所有油价公告的功能
"""

import sys
import yaml
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from collectors.oil_price import OilPriceCollector

def test_collect_all():
    """测试采集所有油价公告"""
    print("=== 测试采集所有油价公告 ===")
    
    # 加载配置
    config_file = project_root / 'config' / 'sources.yaml'
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        oil_config = config.get('sources', {}).get('oil-price', {})
        print(f"加载配置: {oil_config}")
    else:
        oil_config = {}
        print("使用默认配置")
    
    # 创建采集器
    collector = OilPriceCollector(oil_config)
    
    # 执行采集所有公告
    print("\n开始执行采集所有公告...")
    result = collector.collect_all()
    
    print(f"\n采集结果:")
    print(f"  状态: {result.status.value}")
    if result.duration:
        print(f"  耗时: {result.duration:.2f}秒")
    else:
        print(f"  耗时: 未知")
    print(f"  采集时间: {result.collected_at}")
    
    if result.status.value == 'success':
        print(f"\n采集成功!")
        data = result.data
        print(f"  总公告数: {data.get('total_count', 0)}")
        print(f"  已处理数: {data.get('processed_count', 0)}")
        
        # 显示前5个公告
        announcements = data.get('announcements', [])
        print(f"\n前5个公告:")
        for i, announcement in enumerate(announcements[:5]):
            print(f"  {i+1}. {announcement['announcement']['title']}")
            print(f"     日期: {announcement['announcement']['date']}")
            if announcement.get('has_image') and announcement.get('image'):
                print(f"     图片: {announcement['image'].get('api_endpoint', '无')}")
            else:
                print(f"     图片: 无图片附件")
        
        # 验证数据
        is_valid = collector.validate(data)
        print(f"\n  数据验证: {'通过' if is_valid else '失败'}")
        
        # 统计图片情况
        has_image_count = sum(1 for ann in announcements if ann.get('has_image'))
        print(f"  有图片公告数: {has_image_count}/{len(announcements)}")
        
        # 统计图片文件
        image_dir = Path("api/v1/oil-price/images")
        if image_dir.exists():
            image_files = list(image_dir.glob('oil_price_*'))
            print(f"  图片文件数: {len(image_files)}")
    else:
        print(f"\n采集失败: {result.error}")
    
    return result

if __name__ == "__main__":
    test_collect_all()