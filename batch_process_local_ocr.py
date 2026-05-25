#!/usr/bin/env python3
"""
批量处理油价图片OCR识别（本地OCR版本）
使用本地OCR技能（Tesseract.js）重新识别所有图片
"""

import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/local_ocr_batch.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# OCR脚本路径
OCR_SCRIPT = r"C:\Users\19901\.codebuddy\skills\ocr-local\scripts\ocr.js"


class LocalOCRProcessor:
    """本地OCR处理器"""
    
    def __init__(self):
        self.image_dir = project_root / "api" / "v1" / "oil-price" / "images"
        self.data_dir = project_root / "api" / "v1" / "oil-price" / "data"
        self.data_dir.mkdir(exist_ok=True)
        
    def recognize_image(self, image_path: str) -> Optional[str]:
        """
        使用本地OCR技能识别图片
        
        Args:
            image_path: 图片路径
            
        Returns:
            识别到的文字，失败返回None
        """
        try:
            logger.info(f"开始识别图片: {image_path}")
            
            # 调用本地OCR脚本
            cmd = ["node", OCR_SCRIPT, image_path, "--lang", "chi_sim+eng"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=120  # 2分钟超时
            )
            
            if result.returncode == 0:
                # 提取输出中的识别结果（忽略进度信息）
                output = result.stdout
                # 过滤掉进度信息和错误信息
                lines = output.split('\n')
                text_lines = []
                capture = False
                
                for line in lines:
                    if line.startswith('📝'):
                        continue
                    if line.startswith('🌐'):
                        continue
                    if line.startswith('Error'):
                        continue
                    if line.startswith('Please'):
                        continue
                    if line.startswith('Failed'):
                        continue
                    if line.startswith('⏳'):
                        continue
                    if line.strip():
                        text_lines.append(line.strip())
                
                ocr_text = '\n'.join(text_lines)
                
                if ocr_text and len(ocr_text) > 50:  # 确保有足够的识别内容
                    logger.info(f"识别成功，文本长度: {len(ocr_text)} 字符")
                    return ocr_text
                else:
                    logger.warning(f"识别内容过短: {len(ocr_text)} 字符")
                    return None
            else:
                logger.error(f"OCR脚本执行失败: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"识别超时: {image_path}")
            return None
        except Exception as e:
            logger.error(f"识别过程中发生错误: {e}")
            return None
    
    def parse_oil_price_data(self, ocr_text: str) -> Dict[str, Any]:
        """
        解析OCR识别到的油价数据
        （复用现有的解析逻辑）
        """
        try:
            # 导入现有的解析器
            from processors.oil_price_parser import OilPriceParser
            parser = OilPriceParser()
            return parser.parse(ocr_text)
        except ImportError:
            # 如果导入失败，使用简化的解析逻辑
            return self._simple_parse(ocr_text)
    
    def _simple_parse(self, ocr_text: str) -> Dict[str, Any]:
        """简化的解析逻辑"""
        result = {
            "title": "",
            "subtitle": "",
            "date": "",
            "regions": [],
            "notes": []
        }
        
        lines = ocr_text.split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        
        # 提取标题
        for line in lines:
            if "附表" in line or "附 表" in line:
                result["title"] = line
                break
        
        # 提取副标题
        for line in lines:
            if "各省" in line and "中心城市" in line:
                result["subtitle"] = line
                break
        
        # 提取日期（从内容中）
        import re
        date_pattern = r"(\d{4})年(\d{1,2})月(\d{1,2})日"
        for line in lines:
            date_match = re.search(date_pattern, line)
            if date_match:
                year, month, day = date_match.groups()
                result["date"] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                break
        
        # 简单的地区数据提取
        regions = []
        current_region = None
        
        for line in lines:
            # 跳过表头和注释
            if "汽油" in line or "柴油" in line or "注：" in line:
                continue
            
            # 尝试匹配地区名称
            if any(name in line for name in ["市", "省", "自治区", "壮族", "回族", "维吾尔"]):
                # 提取地区名称
                region_match = re.match(r'^([^\d]+)', line)
                if region_match:
                    region_name = region_match.group(1).strip()
                    # 提取价格
                    price_matches = re.findall(r'(\d{4,5})', line)
                    if price_matches:
                        gasoline_price = int(price_matches[0]) if price_matches else None
                        diesel_price = int(price_matches[1]) if len(price_matches) > 1 else None
                        
                        regions.append({
                            "name": region_name,
                            "gasoline_price": gasoline_price,
                            "diesel_price": diesel_price,
                            "section": ""
                        })
        
        result["regions"] = regions
        return result
    
    def get_pending_images(self):
        """获取需要处理的图片列表"""
        all_images = sorted(self.image_dir.glob("oil_price_*"))
        pending = []
        
        for img in all_images:
            date_str = img.stem.replace("oil_price_", "")
            data_file = self.data_dir / f"oil_price_{date_str}.json"
            
            # 检查是否已有有效数据（强制重新处理所有图片）
            # 如果要重新处理所有图片，注释掉下面的检查
            # if data_file.exists():
            #     try:
            #         with open(data_file, 'r', encoding='utf-8') as f:
            #             data = json.load(f)
            #         if data.get("success") and data.get("regions"):
            #             continue  # 已有有效数据，跳过
            #     except:
            #         pass
            
            pending.append((img, date_str))
        
        return pending
    
    def process_single_image(self, image_path: Path, date_str: str) -> Optional[Dict[str, Any]]:
        """处理单张图片"""
        try:
            # 识别图片
            ocr_text = self.recognize_image(str(image_path))
            
            if not ocr_text:
                return {
                    "success": False,
                    "error": "图片识别失败",
                    "image_path": str(image_path),
                    "date": date_str
                }
            
            # 解析数据
            parsed_data = self.parse_oil_price_data(ocr_text)
            
            # 添加元数据
            parsed_data["success"] = True
            parsed_data["image_path"] = str(image_path)
            parsed_data["ocr_text_length"] = len(ocr_text)
            parsed_data["ocr_text_preview"] = ocr_text[:500] + "..." if len(ocr_text) > 500 else ocr_text
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"处理图片时发生错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "image_path": str(image_path),
                "date": date_str
            }
    
    def run(self):
        """执行批量处理"""
        logger.info("=" * 60)
        logger.info("开始批量本地OCR处理")
        logger.info("=" * 60)
        
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
            result = self.process_single_image(image_path, date_str)
            
            if result and result.get("success"):
                # 保存结果
                data_file = self.data_dir / f"oil_price_{date_str}.json"
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                successful += 1
                logger.info(f"成功: {date_str} - {len(result.get('regions', []))} 个地区")
            else:
                failed += 1
                error = result.get("error", "未知错误") if result else "处理返回None"
                logger.warning(f"失败: {date_str} - {error}")
            
            # 添加延迟，避免过载
            if i < len(pending):
                delay = 2  # 本地处理可以稍快
                time.sleep(delay)
        
        # 打印统计
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("\n" + "=" * 60)
        logger.info("处理完成")
        logger.info("=" * 60)
        logger.info(f"总图片: {len(pending)}")
        logger.info(f"成功: {successful}")
        logger.info(f"失败: {failed}")
        logger.info(f"成功率: {successful/len(pending)*100:.1f}%")
        logger.info(f"耗时: {elapsed:.0f} 秒")
        logger.info(f"平均每张: {elapsed/len(pending):.1f} 秒")


def main():
    """主函数"""
    processor = LocalOCRProcessor()
    processor.run()


if __name__ == "__main__":
    main()