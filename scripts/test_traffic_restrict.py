#!/usr/bin/env python3
"""
限行信息数据源测试脚本
帮助用户验证限行数据源配置
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from collectors.traffic_restrict import TrafficRestrictCollector
from config import config_manager


def test_mock_data():
    """测试模拟数据"""
    print("=" * 50)
    print("测试1: 模拟数据采集")
    print("=" * 50)
    
    # 创建采集器实例
    collector = TrafficRestrictCollector({
        "name": "限行信息",
        "url": "https://api.example.com/traffic-restrict",
        "timeout": 30,
        "retries": 3
    })
    
    # 执行采集
    result = collector.run()
    
    print(f"采集状态: {result.status.value}")
    print(f"采集耗时: {result.duration:.2f}秒")
    
    if result.data:
        print(f"数据记录数: {len(result.data.get('data', {}).get('restrictions', []))}")
        
        # 保存到文件
        output_file = Path("api/v1/traffic-restrict/latest.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result.data, f, ensure_ascii=False, indent=2)
        
        print(f"数据已保存到: {output_file}")
        
        # 显示数据预览
        print("\n数据预览:")
        print(json.dumps(result.data, ensure_ascii=False, indent=2)[:500] + "...")
    
    print("\n" + "=" * 50)
    return result.status.value == "success"


def test_api_endpoint():
    """测试API端点"""
    print("\n测试2: API端点测试")
    print("=" * 50)
    
    # 检查数据文件是否存在
    data_file = Path("api/v1/traffic-restrict/latest.json")
    
    if not data_file.exists():
        print("数据文件不存在，请先运行测试1")
        return False
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("API端点测试:")
    print(f"  - 数据状态: {data.get('status')}")
    print(f"  - 更新时间: {data.get('data', {}).get('update_time')}")
    print(f"  - 记录数量: {len(data.get('data', {}).get('restrictions', []))}")
    print(f"  - 质量评分: {data.get('metadata', {}).get('quality_score')}")
    
    print("\n测试API访问:")
    print("  启动Flask服务器后，可以访问以下端点:")
    print("  - http://localhost:5000/api/health.json")
    print("  - http://localhost:5000/api/v1/traffic-restrict/latest.json")
    
    print("\n" + "=" * 50)
    return True


def test_frontend():
    """测试前端集成"""
    print("\n测试3: 前端集成测试")
    print("=" * 50)
    
    print("前端集成步骤:")
    print("1. 启动前端开发服务器:")
    print("   cd web && npm run dev")
    print("\n2. 访问前端界面:")
    print("   http://localhost:3000")
    print("\n3. 检查以下页面:")
    print("   - Dashboard: 查看限行数据统计")
    print("   - Monitor: 查看限行数据源状态")
    print("   - ApiDocs: 查看限行API文档")
    print("   - History: 查看限行历史数据")
    
    print("\n" + "=" * 50)
    return True


def main():
    """主函数"""
    print("限行信息数据源测试")
    print("=" * 50)
    
    # 测试模拟数据
    if not test_mock_data():
        print("模拟数据测试失败")
        return
    
    # 测试API端点
    if not test_api_endpoint():
        print("API端点测试失败")
        return
    
    # 测试前端集成
    if not test_frontend():
        print("前端集成测试失败")
        return
    
    print("\n所有测试完成！")
    print("\n下一步操作:")
    print("1. 配置真实数据源 (编辑 config/sources.yaml)")
    print("2. 启动Flask服务器 (python scripts/run_collection.py)")
    print("3. 启动前端开发服务器 (cd web && npm run dev)")
    print("4. 访问 http://localhost:3000 查看结果")


if __name__ == "__main__":
    main()