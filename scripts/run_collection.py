#!/usr/bin/env python3
"""
数据采集主入口脚本
执行数据采集、处理和输出
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from collectors.registry import CollectorRegistry
from processors.pipeline import DataPipeline
from config import config_manager


def setup_logging(log_level: str = "INFO"):
    """设置日志"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/collection.log', encoding='utf-8')
        ]
    )


def ensure_directories():
    """确保必要目录存在"""
    directories = [
        'logs',
        'staging',
        'api/v1',
        'api/metadata'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    """加载配置"""
    try:
        settings = config_manager.load_settings()
        sources = config_manager.load_sources()
        
        return {
            'settings': settings,
            'sources': sources
        }
    except Exception as e:
        logging.error(f"加载配置失败: {e}")
        sys.exit(1)


def discover_collectors():
    """发现并注册采集器"""
    try:
        # 自动发现采集器
        CollectorRegistry.discover("collectors")
        
        # 列出发现的采集器
        collectors = CollectorRegistry.list_collectors()
        logging.info(f"发现 {len(collectors)} 个采集器: {collectors}")
        
        return collectors
    except Exception as e:
        logging.error(f"发现采集器失败: {e}")
        return []


def run_collection(sources_config: Dict[str, Any], dry_run: bool = False) -> List[Dict[str, Any]]:
    """
    执行数据采集
    
    Args:
        sources_config: 数据源配置
        dry_run: 是否为模拟运行
        
    Returns:
        采集结果列表
    """
    results = []
    
    # 获取启用的数据源
    enabled_sources = {
        name: config for name, config in sources_config.items()
        if config.get('enabled', True)
    }
    
    logging.info(f"开始采集 {len(enabled_sources)} 个数据源")
    
    for source_name, source_config in enabled_sources.items():
        logging.info(f"采集数据源: {source_name}")
        
        try:
            # 创建采集器实例
            collector = CollectorRegistry.create(source_name, source_config)
            
            if not collector:
                logging.warning(f"未找到采集器: {source_name}")
                continue
            
            if dry_run:
                logging.info(f"[模拟运行] 跳过采集: {source_name}")
                results.append({
                    'source': source_name,
                    'status': 'dry_run',
                    'message': '模拟运行，未实际采集'
                })
                continue
            
            # 执行采集
            result = collector.run()
            
            results.append({
                'source': source_name,
                'status': result.status.value,
                'data': result.data,
                'metadata': result.metadata,
                'error': result.error,
                'duration': result.duration
            })
            
            logging.info(f"采集完成: {source_name} - {result.status.value}")
            
        except Exception as e:
            logging.error(f"采集 {source_name} 失败: {e}")
            results.append({
                'source': source_name,
                'status': 'error',
                'error': str(e)
            })
    
    return results


def process_data(collected_data: List[Dict[str, Any]], settings: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    处理采集到的数据
    
    Args:
        collected_data: 采集结果
        settings: 全局设置
        
    Returns:
        处理结果
    """
    # 创建数据处理管线
    pipeline_config = {
        'quality_threshold': settings.get('quality_threshold', 0.8),
        'cleaner': {},
        'validator': {
            'schema_dir': 'config/schemas'
        },
        'quality': {
            'weights': {
                'completeness': 0.3,
                'accuracy': 0.3,
                'consistency': 0.2,
                'timeliness': 0.2
            }
        }
    }
    
    pipeline = DataPipeline(pipeline_config)
    
    processed_results = []
    
    for item in collected_data:
        if item['status'] != 'success':
            processed_results.append(item)
            continue
        
        try:
            # 处理数据
            result = pipeline.process(item['data'], item['source'])
            
            processed_results.append({
                'source': item['source'],
                'status': result.stage.value,
                'data': result.data,
                'metadata': result.metadata,
                'error': result.error,
                'processing_time': result.processing_time
            })
            
        except Exception as e:
            logging.error(f"处理 {item['source']} 失败: {e}")
            processed_results.append({
                'source': item['source'],
                'status': 'error',
                'error': str(e)
            })
    
    return processed_results


def output_data(processed_results: List[Dict[str, Any]], settings: Dict[str, Any]):
    """
    输出处理后的数据
    
    Args:
        processed_results: 处理结果
        settings: 全局设置
    """
    live_dir = Path(settings.get('live_dir', 'api/v1'))
    metadata_dir = Path(settings.get('metadata_dir', 'api/metadata'))
    
    # 确保目录存在
    live_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成时间戳
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    
    for result in processed_results:
        source_name = result['source']
        
        if result['status'] != 'outputted':
            logging.warning(f"跳过未成功处理的数据: {source_name}")
            continue
        
        try:
            # 创建数据目录
            source_dir = live_dir / source_name
            source_dir.mkdir(parents=True, exist_ok=True)
            
            # 写入最新数据
            latest_file = source_dir / "latest.json"
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(result['data'], f, ensure_ascii=False, indent=2)
            
            # 写入带时间戳的历史数据
            history_file = source_dir / f"{timestamp}.json"
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(result['data'], f, ensure_ascii=False, indent=2)
            
            # 写入元数据
            metadata_file = metadata_dir / f"{source_name}.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(result['metadata'], f, ensure_ascii=False, indent=2)
            
            logging.info(f"数据已输出: {source_name}")
            
        except Exception as e:
            logging.error(f"输出 {source_name} 失败: {e}")


def generate_health_report(processed_results: List[Dict[str, Any]]):
    """
    生成健康状态报告
    
    Args:
        processed_results: 处理结果
    """
    health_data = {
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sources": {}
    }
    
    for result in processed_results:
        source_name = result['source']
        health_data["sources"][source_name] = {
            "status": result['status'],
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "error": result.get('error')
        }
    
    # 写入健康状态文件
    health_file = Path("api/health.json")
    health_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(health_file, 'w', encoding='utf-8') as f:
        json.dump(health_data, f, ensure_ascii=False, indent=2)
    
    logging.info("健康状态报告已生成")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="数据采集主入口")
    parser.add_argument("--dry-run", action="store_true", help="模拟运行，不实际采集")
    parser.add_argument("--log-level", default="INFO", help="日志级别")
    parser.add_argument("--sources", nargs="+", help="指定要采集的数据源")
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    
    # 确保目录存在
    ensure_directories()
    
    logging.info("开始数据采集任务")
    
    try:
        # 加载配置
        config = load_config()
        
        # 发现采集器
        discover_collectors()
        
        # 执行采集
        collected_data = run_collection(
            config['sources'],
            dry_run=args.dry_run
        )
        
        # 处理数据
        processed_data = process_data(collected_data, config['settings'])
        
        # 输出数据
        if not args.dry_run:
            output_data(processed_data, config['settings'])
            generate_health_report(processed_data)
        
        # 统计结果
        success_count = sum(1 for r in processed_data if r['status'] == 'outputted')
        total_count = len(processed_data)
        
        logging.info(f"数据采集任务完成: {success_count}/{total_count} 成功")
        
        # 如果有失败的采集，返回非零退出码
        if success_count < total_count:
            sys.exit(1)
        
    except Exception as e:
        logging.error(f"数据采集任务失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()