#!/usr/bin/env python3
"""
批量处理油价图片OCR识别（改进版）
功能：
1. 只处理没有数据的图片
2. 重试机制
3. 更好的错误处理
4. 图片预处理
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ocr_batch.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from processors.ocr_processor import OilPriceOCRProcessor


class ImprovedBatchProcessor:
    """改进的批量OCR处理器"""
    
    def __init__(self, max_retries=3, retry_delay=5):
        self.processor = OilPriceOCRProcessor()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.image_dir = project_root / "api" / "v1" / "oil-price" / "images"
        self.data_dir = project_root / "api" / "v1" / "oil-price" / "data"
        self.data_dir.mkdir(exist_ok=True)
    
    def get_pending_images(self):
        """获取需要处理的图片列表"""
        all_images = sorted(self.image_dir.glob("oil_price_*"))
        pending = []
        
        for img in all_images:
            date_str = img.stem.replace("oil_price_", "")
            data_file = self.data_dir / f"oil_price_{date_str}.json"
            
            # 检查是否已有有效数据
            if data_file.exists():
                try:
                    with open(data_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if data.get("success") and data.get("regions"):
                        continue  # 已有有效数据，跳过
                except:
                    pass  # 文件损坏，需要重新处理
            
            pending.append((img, date_str))
        
        return pending
    
    def process_image_with_retry(self, image_path: str, date_str: str) -> Optional[dict]:
        """带重试机制的图片处理"""
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"处理 {date_str} (尝试 {attempt}/{self.max_retries})")
                
                result = self.processor.process_image(image_path)
                
                if result.get("success"):
                    logger.info(f"成功: {date_str} - {len(result.get('regions', []))} 个地区")
                    return result
                else:
                    error = result.get("error", "未知错误")
                    logger.warning(f"失败: {date_str} - {error}")
                    
                    if attempt < self.max_retries:
                        logger.info(f"等待 {self.retry_delay} 秒后重试...")
                        time.sleep(self.retry_delay)
                    
            except Exception as e:
                logger.error(f"错误: {date_str} - {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
        
        return None
    
    def run(self):
        """执行批量处理"""
        logger.info("=" * 50)
        logger.info("开始批量OCR处理")
        logger.info("=" * 50)
        
        pending = self.get_pending_images()
        logger.info(f"待处理图片: {len(pending)}")
        
        if not pending:
            logger.info("没有待处理的图片")
            return
        
        # 统计
        successful = 0
        failed = 0
        start_time = datetime.now()
        
        for i, (image_path, date_str) in enumerate(pending, 1):
            logger.info(f"\n[{i}/{len(pending)}] 处理 {date_str}")
            
            # 处理图片
            result = self.process_image_with_retry(str(image_path), date_str)
            
            if result:
                # 保存结果
                data_file = self.data_dir / f"oil_price_{date_str}.json"
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                successful += 1
            else:
                failed += 1
            
            # 添加延迟，避免API限制
            if i < len(pending):
                delay = 3 if successful > 0 else 5  # 成功后延迟短一些
                time.sleep(delay)
        
        # 打印统计
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("\n" + "=" * 50)
        logger.info("处理完成")
        logger.info("=" * 50)
        logger.info(f"总图片: {len(pending)}")
        logger.info(f"成功: {successful}")
        logger.info(f"失败: {failed}")
        logger.info(f"成功率: {successful/len(pending)*100:.1f}%")
        logger.info(f"耗时: {elapsed:.0f} 秒")


def main():
    """主函数"""
    processor = ImprovedBatchProcessor(
        max_retries=3,
        retry_delay=5
    )
    processor.run()


if __name__ == "__main__":
    main()
