#!/usr/bin/env python3
"""
使用小米MiMo API批量处理油价图片识别
"""

import os
import sys
import json
import time
import base64
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/mimo_vision_batch.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 尝试导入openai库
try:
    from openai import OpenAI
except ImportError:
    logger.error("请先安装openai库: pip install openai")
    sys.exit(1)


class MiMoVisionProcessor:
    """使用小米MiMo API识别油价图片"""
    
    def __init__(self, api_key: str = None):
        """初始化处理器"""
        self.api_key = api_key or os.environ.get("MIMO_API_KEY") or "tp-c7af33knz2kyu6dxw9y1wyci7iu3ldmac7691cncauts12z8"
        if not self.api_key:
            raise ValueError("需要提供小米MiMo API密钥 (MIMO_API_KEY)")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://token-plan-cn.xiaomimimo.com/v1"
        )
        self.model = "mimo-v2.5"
        
        # 提示词
        self.prompt = """请识别这张国内成品油价格表图片，提取以下信息：
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
    
    def recognize_image(self, image_base64: str) -> Optional[str]:
        """
        使用MiMo API识别图片
        
        Args:
            image_base64: Base64编码的图片（带前缀）
            
        Returns:
            识别结果文本
        """
        try:
            logger.info("正在调用小米MiMo API...")
            
            completion = self.client.chat.completions.create(
                model=self.model,
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
                                "text": self.prompt
                            }
                        ]
                    }
                ],
                max_completion_tokens=8192
            )
            
            content = completion.choices[0].message.content
            logger.info(f"API调用成功，返回内容长度: {len(content)} 字符")
            return content
            
        except Exception as e:
            logger.error(f"API调用失败: {e}")
            return None
    
    def parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        """解析JSON响应"""
        # 清理文本，移除Markdown代码块标记
        cleaned_text = text.strip()
        if cleaned_text.startswith('```json'):
            cleaned_text = cleaned_text[7:]  # 移除开头的```json
        if cleaned_text.endswith('```'):
            cleaned_text = cleaned_text[:-3]  # 移除结尾的```
        cleaned_text = cleaned_text.strip()
        
        try:
            # 尝试直接解析
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            # 尝试提取JSON部分
            import re
            json_match = re.search(r'\{[\s\S]*\}', cleaned_text)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            logger.warning("无法解析JSON响应")
            return None


class BatchProcessor:
    """批量处理器"""
    
    def __init__(self, api_key: str = None):
        """初始化批量处理器"""
        self.processor = MiMoVisionProcessor(api_key)
        self.project_root = Path(__file__).parent
        self.image_dir = self.project_root / "api" / "v1" / "oil-price" / "images"
        self.data_dir = self.project_root / "api" / "v1" / "oil-price" / "data"
        self.base64_file = self.project_root / "temp" / "all_images_base64.json"
        
        # 确保目录存在
        self.data_dir.mkdir(exist_ok=True)
        
    def load_base64_data(self) -> List[Dict[str, Any]]:
        """加载Base64编码数据"""
        try:
            logger.info(f"正在加载Base64编码数据: {self.base64_file}")
            with open(self.base64_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"成功加载 {len(data)} 张图片的Base64编码")
            return data
        except Exception as e:
            logger.error(f"加载Base64数据失败: {e}")
            return []
    
    def get_pending_images(self, base64_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """获取待处理的图片列表（重新处理所有图片）"""
        pending = []
        
        for image_info in base64_data:
            # 总是添加图片，重新处理所有图片
            pending.append(image_info)
        
        return pending
    
    def process_batch(self, batch: List[Dict[str, Any]], batch_size: int = 10) -> Dict[str, Any]:
        """处理一批图片"""
        results = {
            'successful': 0,
            'failed': 0,
            'processed': []
        }
        
        for i, image_info in enumerate(batch):
            filename = image_info['filename']
            date_str = filename.replace('oil_price_', '').split('.')[0]
            
            logger.info(f"[{i+1}/{len(batch)}] 处理 {filename}")
            
            try:
                # 识别图片
                response_text = self.processor.recognize_image(image_info['base64_with_prefix'])
                
                if not response_text:
                    results['failed'] += 1
                    results['processed'].append({
                        'filename': filename,
                        'success': False,
                        'error': 'API识别失败'
                    })
                    continue
                
                # 解析JSON
                parsed_data = self.processor.parse_json_response(response_text)
                
                if not parsed_data:
                    results['failed'] += 1
                    results['processed'].append({
                        'filename': filename,
                        'success': False,
                        'error': 'JSON解析失败',
                        'raw_response': response_text[:200] + '...'
                    })
                    continue
                
                # 添加元数据
                parsed_data['success'] = True
                parsed_data['image_path'] = str(self.image_dir / filename)
                parsed_data['model'] = self.processor.model
                parsed_data['processed_at'] = datetime.now().isoformat()
                parsed_data['date'] = date_str  # 使用从文件名提取的日期
                
                # 保存结果
                data_file = self.data_dir / f"oil_price_{date_str}.json"
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(parsed_data, f, ensure_ascii=False, indent=2)
                
                results['successful'] += 1
                results['processed'].append({
                    'filename': filename,
                    'success': True,
                    'regions_count': len(parsed_data.get('regions', []))
                })
                
                logger.info(f"  成功: {len(parsed_data.get('regions', []))} 个地区")
                
                # 添加延迟，避免API限制
                if i < len(batch) - 1:
                    time.sleep(2)
                
            except Exception as e:
                logger.error(f"  处理失败: {e}")
                results['failed'] += 1
                results['processed'].append({
                    'filename': filename,
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def run(self, batch_size: int = 10):
        """执行批量处理"""
        logger.info("=" * 60)
        logger.info("开始使用小米MiMo API批量处理油价图片")
        logger.info("=" * 60)
        
        # 加载Base64数据
        base64_data = self.load_base64_data()
        if not base64_data:
            logger.error("无法加载Base64数据")
            return
        
        # 获取待处理图片
        pending_images = self.get_pending_images(base64_data)
        logger.info(f"待处理图片: {len(pending_images)}")
        
        if not pending_images:
            logger.info("没有待处理的图片")
            return
        
        # 分批处理
        total_successful = 0
        total_failed = 0
        start_time = datetime.now()
        
        for batch_start in range(0, len(pending_images), batch_size):
            batch = pending_images[batch_start:batch_start + batch_size]
            batch_num = (batch_start // batch_size) + 1
            total_batches = (len(pending_images) + batch_size - 1) // batch_size
            
            logger.info(f"\n处理第 {batch_num}/{total_batches} 批 ({len(batch)} 张图片)")
            
            # 处理这批图片
            batch_results = self.process_batch(batch)
            
            total_successful += batch_results['successful']
            total_failed += batch_results['failed']
            
            # 打印批次统计
            logger.info(f"批次完成: 成功 {batch_results['successful']}, 失败 {batch_results['failed']}")
            
            # 批次间延迟
            if batch_start + batch_size < len(pending_images):
                logger.info("等待 5 秒后处理下一批...")
                time.sleep(5)
        
        # 打印最终统计
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("\n" + "=" * 60)
        logger.info("批量处理完成")
        logger.info("=" * 60)
        logger.info(f"总图片数: {len(pending_images)}")
        logger.info(f"成功: {total_successful}")
        logger.info(f"失败: {total_failed}")
        logger.info(f"成功率: {total_successful/len(pending_images)*100:.1f}%")
        logger.info(f"耗时: {elapsed:.0f} 秒")
        logger.info(f"平均每张: {elapsed/len(pending_images):.1f} 秒")
        
        # 生成处理报告
        self.generate_report(pending_images, total_successful, total_failed, elapsed)
    
    def generate_report(self, pending_images, successful, failed, elapsed):
        """生成处理报告"""
        report = {
            "processed_at": datetime.now().isoformat(),
            "model": self.processor.model,
            "total_images": len(pending_images),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / len(pending_images) * 100 if pending_images else 0,
            "elapsed_seconds": elapsed,
            "average_time_per_image": elapsed / len(pending_images) if pending_images else 0
        }
        
        report_file = self.project_root / "temp" / "mimo_vision_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"处理报告已保存到: {report_file}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="使用小米MiMo API批量处理油价图片")
    parser.add_argument("--api-key", help="小米MiMo API密钥")
    parser.add_argument("--batch-size", type=int, default=10, help="每批处理的图片数量 (默认: 10)")
    
    args = parser.parse_args()
    
    # 创建批量处理器
    try:
        processor = BatchProcessor(api_key=args.api_key)
        processor.run(batch_size=args.batch_size)
    except ValueError as e:
        logger.error(str(e))
        logger.info("请设置MIMO_API_KEY环境变量或使用--api-key参数提供API密钥")
        sys.exit(1)


if __name__ == "__main__":
    main()