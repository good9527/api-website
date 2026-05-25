#!/usr/bin/env python3
"""
生成所有数据源的模拟数据
用于本地开发测试
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
API_DIR = PROJECT_ROOT / 'api'


def ensure_directories():
    """确保目录结构存在"""
    directories = [
        API_DIR / 'v1' / 'oil-price',
        API_DIR / 'v1' / 'traffic-restrict',
        API_DIR / 'v1' / 'policy',
        API_DIR / 'v1' / 'admin-division',
        API_DIR / 'v1' / 'price-table',
        API_DIR / 'metadata',
    ]
    for d in directories:
        d.mkdir(parents=True, exist_ok=True)


def generate_oil_price_data():
    """生成油价模拟数据"""
    now = datetime.now(timezone.utc)
    data = {
        "status": "success",
        "data": {
            "update_time": now.isoformat(),
            "prices": [
                {
                    "province": "北京",
                    "92号汽油": 7.85,
                    "95号汽油": 8.35,
                    "98号汽油": 9.33,
                    "0号柴油": 7.55
                },
                {
                    "province": "上海",
                    "92号汽油": 7.82,
                    "95号汽油": 8.32,
                    "98号汽油": 9.30,
                    "0号柴油": 7.52
                },
                {
                    "province": "广东",
                    "92号汽油": 7.88,
                    "95号汽油": 8.53,
                    "98号汽油": 9.53,
                    "0号柴油": 7.50
                }
            ]
        },
        "metadata": {
            "source": "oil-price",
            "collected_at": now.isoformat(),
            "version": now.strftime("%Y%m%d-%H%M%S"),
            "quality_score": 0.96,
            "fields_count": 2,
            "records_count": 3
        }
    }
    return data


def generate_traffic_restrict_data():
    """生成限行信息模拟数据"""
    now = datetime.now(timezone.utc)
    data = {
        "status": "success",
        "data": {
            "update_time": now.isoformat(),
            "restrictions": [
                {
                    "city": "北京",
                    "rule": "工作日早晚高峰时段限行，按车牌尾号轮换",
                    "time_range": "工作日7:00-9:00，17:00-20:00",
                    "area": "五环路以内（不含五环）",
                    "exceptions": ["新能源汽车", "出租车", "公交车"],
                    "effective_date": "2026-01-01",
                    "end_date": "2026-12-31"
                },
                {
                    "city": "上海",
                    "rule": "外牌高架限行，内环地面限行",
                    "time_range": "工作日7:00-20:00",
                    "area": "高架道路、内环地面道路",
                    "exceptions": ["新能源汽车", "沪牌车辆"],
                    "effective_date": "2026-01-01",
                    "end_date": "2026-12-31"
                },
                {
                    "city": "广州",
                    "rule": "开四停四政策",
                    "time_range": "全天",
                    "area": "管控区域内",
                    "exceptions": ["广州牌照车辆", "新能源汽车"],
                    "effective_date": "2026-01-01",
                    "end_date": "2026-12-31"
                },
                {
                    "city": "深圳",
                    "rule": "外地车限行",
                    "time_range": "工作日7:00-9:00，17:30-19:30",
                    "area": "全市范围",
                    "exceptions": ["深圳牌照车辆", "新能源汽车"],
                    "effective_date": "2026-01-01",
                    "end_date": "2026-12-31"
                }
            ]
        },
        "metadata": {
            "source": "traffic-restrict",
            "collected_at": now.isoformat(),
            "version": now.strftime("%Y%m%d-%H%M%S"),
            "quality_score": 0.95,
            "fields_count": 2,
            "records_count": 4
        }
    }
    return data


def generate_policy_data():
    """生成政策信息模拟数据"""
    now = datetime.now(timezone.utc)
    data = {
        "status": "success",
        "data": {
            "update_time": now.isoformat(),
            "policies": [
                {
                    "title": "关于进一步优化营商环境的若干措施",
                    "category": "经济",
                    "issuer": "国务院",
                    "publish_date": "2026-05-20",
                    "effective_date": "2026-06-01",
                    "summary": "深化放管服改革，持续优化营商环境",
                    "url": "https://www.gov.cn/example"
                },
                {
                    "title": "新能源汽车产业发展规划",
                    "category": "产业",
                    "issuer": "工信部",
                    "publish_date": "2026-05-15",
                    "effective_date": "2026-07-01",
                    "summary": "加快推进新能源汽车技术创新和产业化",
                    "url": "https://www.miit.gov.cn/example"
                }
            ]
        },
        "metadata": {
            "source": "policy",
            "collected_at": now.isoformat(),
            "version": now.strftime("%Y%m%d-%H%M%S"),
            "quality_score": 0.92,
            "fields_count": 2,
            "records_count": 2
        }
    }
    return data


def generate_admin_division_data():
    """生成行政区划模拟数据"""
    now = datetime.now(timezone.utc)
    data = {
        "status": "success",
        "data": {
            "update_time": now.isoformat(),
            "divisions": [
                {
                    "code": "110000",
                    "name": "北京市",
                    "level": "province",
                    "parent_code": "000000",
                    "children": [
                        {"code": "110100", "name": "市辖区", "level": "city"},
                        {"code": "110101", "name": "东城区", "level": "district"},
                        {"code": "110102", "name": "西城区", "level": "district"}
                    ]
                },
                {
                    "code": "310000",
                    "name": "上海市",
                    "level": "province",
                    "parent_code": "000000",
                    "children": [
                        {"code": "310100", "name": "市辖区", "level": "city"},
                        {"code": "310101", "name": "黄浦区", "level": "district"}
                    ]
                }
            ]
        },
        "metadata": {
            "source": "admin-division",
            "collected_at": now.isoformat(),
            "version": now.strftime("%Y%m%d-%H%M%S"),
            "quality_score": 0.98,
            "fields_count": 2,
            "records_count": 2
        }
    }
    return data


def generate_price_table_data():
    """生成价格表模拟数据"""
    now = datetime.now(timezone.utc)
    data = {
        "status": "success",
        "data": {
            "update_time": now.isoformat(),
            "prices": [
                {
                    "category": "食品",
                    "items": [
                        {"name": "大米", "unit": "元/公斤", "price": 5.50, "change": 0.02},
                        {"name": "面粉", "unit": "元/公斤", "price": 4.20, "change": -0.01},
                        {"name": "猪肉", "unit": "元/公斤", "price": 28.50, "change": 0.05}
                    ]
                },
                {
                    "category": "能源",
                    "items": [
                        {"name": "92号汽油", "unit": "元/升", "price": 7.85, "change": 0.03},
                        {"name": "0号柴油", "unit": "元/升", "price": 7.55, "change": 0.02},
                        {"name": "天然气", "unit": "元/立方米", "price": 3.20, "change": 0.01}
                    ]
                }
            ]
        },
        "metadata": {
            "source": "price-table",
            "collected_at": now.isoformat(),
            "version": now.strftime("%Y%m%d-%H%M%S"),
            "quality_score": 0.94,
            "fields_count": 2,
            "records_count": 2
        }
    }
    return data


def write_data(source_name, data):
    """写入数据文件"""
    source_dir = API_DIR / 'v1' / source_name
    
    # 写入latest.json
    latest_file = source_dir / 'latest.json'
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  - {latest_file}")
    
    # 写入带时间戳的历史文件
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    history_file = source_dir / f"{timestamp}.json"
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  - {history_file}")
    
    # 写入元数据
    metadata_file = API_DIR / 'metadata' / f'{source_name}.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(data.get('metadata', {}), f, ensure_ascii=False, indent=2)
    print(f"  - {metadata_file}")


def generate_health_report():
    """生成健康状态报告"""
    now = datetime.now(timezone.utc)
    health_data = {
        "status": "success",
        "timestamp": now.isoformat(),
        "sources": {
            "oil-price": {"status": "success", "last_updated": now.isoformat()},
            "traffic-restrict": {"status": "success", "last_updated": now.isoformat()},
            "policy": {"status": "success", "last_updated": now.isoformat()},
            "admin-division": {"status": "success", "last_updated": now.isoformat()},
            "price-table": {"status": "success", "last_updated": now.isoformat()}
        }
    }
    
    health_file = API_DIR / 'health.json'
    with open(health_file, 'w', encoding='utf-8') as f:
        json.dump(health_data, f, ensure_ascii=False, indent=2)
    print(f"  - {health_file}")


def main():
    """主函数"""
    print("=" * 50)
    print("生成模拟数据")
    print("=" * 50)
    
    # 确保目录存在
    ensure_directories()
    
    # 生成各数据源数据
    generators = [
        ("oil-price", generate_oil_price_data),
        ("traffic-restrict", generate_traffic_restrict_data),
        ("policy", generate_policy_data),
        ("admin-division", generate_admin_division_data),
        ("price-table", generate_price_table_data),
    ]
    
    for source_name, generator in generators:
        print(f"\n生成 {source_name} 数据:")
        data = generator()
        write_data(source_name, data)
    
    # 生成健康报告
    print(f"\n生成健康状态报告:")
    generate_health_report()
    
    print("\n" + "=" * 50)
    print("所有模拟数据生成完成！")
    print("=" * 50)
    print("\n下一步:")
    print("1. 启动Flask服务器: python app.py")
    print("2. 启动前端: cd web && npm run dev")


if __name__ == "__main__":
    main()