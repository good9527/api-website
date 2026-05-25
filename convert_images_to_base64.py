#!/usr/bin/env python3
"""
将所有油价图片转换为Base64编码字符串
输出格式：JSON文件，包含文件名和对应的Base64编码
"""

import os
import sys
import json
import base64
from pathlib import Path
from datetime import datetime
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def image_to_base64(image_path: str) -> dict:
    """
    将单个图片转换为Base64编码
    
    Args:
        image_path: 图片路径
        
    Returns:
        包含文件名、MIME类型和Base64编码的字典
    """
    try:
        # 读取图片文件
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        # 检查文件大小（限制50MB）
        file_size_mb = len(image_data) / (1024 * 1024)
        if file_size_mb > 50:
            logger.warning(f"图片过大 ({file_size_mb:.1f}MB): {image_path}")
            return None
        
        # 转换为Base64
        base64_encoded = base64.b64encode(image_data).decode("utf-8")
        
        # 根据文件扩展名确定MIME类型
        ext = Path(image_path).suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        mime_type = mime_types.get(ext, "image/jpeg")
        
        # 添加前缀
        base64_with_prefix = f"data:{mime_type};base64,{base64_encoded}"
        
        return {
            "filename": Path(image_path).name,
            "filepath": str(image_path),
            "mime_type": mime_type,
            "file_size_bytes": len(image_data),
            "file_size_mb": round(file_size_mb, 2),
            "base64_length": len(base64_encoded),
            "base64_with_prefix": base64_with_prefix,
            "base64_only": base64_encoded
        }
        
    except Exception as e:
        logger.error(f"转换图片失败 {image_path}: {e}")
        return None

def convert_all_images():
    """转换所有图片"""
    project_root = Path(__file__).parent
    image_dir = project_root / "api" / "v1" / "oil-price" / "images"
    output_dir = project_root / "temp"
    
    # 确保输出目录存在
    output_dir.mkdir(exist_ok=True)
    
    # 获取所有图片文件
    image_files = sorted(image_dir.glob("oil_price_*"))
    logger.info(f"找到 {len(image_files)} 个图片文件")
    
    # 转换结果
    results = []
    successful = 0
    failed = 0
    total_size_mb = 0
    
    start_time = datetime.now()
    
    for i, image_file in enumerate(image_files, 1):
        logger.info(f"[{i}/{len(image_files)}] 转换 {image_file.name}")
        
        result = image_to_base64(str(image_file))
        
        if result:
            results.append(result)
            successful += 1
            total_size_mb += result["file_size_mb"]
            logger.info(f"  成功: {result['mime_type']} ({result['file_size_mb']}MB)")
        else:
            failed += 1
            logger.warning(f"  失败: {image_file.name}")
        
        # 每10张图片输出进度
        if i % 10 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"进度: {i}/{len(image_files)} ({i/len(image_files)*100:.1f}%) - 耗时: {elapsed:.1f}秒")
    
    # 保存结果
    output_file = output_dir / "all_images_base64.json"
    
    # 只保存必要的字段（不保存完整的base64字符串，避免文件过大）
    summary_results = []
    for result in results:
        summary_results.append({
            "filename": result["filename"],
            "filepath": result["filepath"],
            "mime_type": result["mime_type"],
            "file_size_mb": result["file_size_mb"],
            "base64_length": result["base64_length"],
            "base64_with_prefix": result["base64_with_prefix"]  # 保留完整的base64字符串
        })
    
    # 保存完整结果
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary_results, f, ensure_ascii=False, indent=2)
    
    # 同时保存一个简化版本（不含base64字符串）
    summary_file = output_dir / "images_base64_summary.json"
    summary_only = []
    for result in results:
        summary_only.append({
            "filename": result["filename"],
            "mime_type": result["mime_type"],
            "file_size_mb": result["file_size_mb"],
            "base64_length": result["base64_length"]
        })
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_only, f, ensure_ascii=False, indent=2)
    
    # 打印统计信息
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info("\n" + "=" * 50)
    logger.info("转换完成")
    logger.info("=" * 50)
    logger.info(f"总图片数: {len(image_files)}")
    logger.info(f"成功转换: {successful}")
    logger.info(f"失败: {failed}")
    logger.info(f"总大小: {total_size_mb:.1f}MB")
    logger.info(f"平均大小: {total_size_mb/successful:.2f}MB/张" if successful > 0 else "无")
    logger.info(f"耗时: {elapsed:.1f}秒")
    logger.info(f"完整结果保存到: {output_file}")
    logger.info(f"摘要保存到: {summary_file}")
    
    # 提供使用说明
    logger.info("\n=== 使用说明 ===")
    logger.info("1. 完整结果文件包含所有图片的Base64编码字符串")
    logger.info("2. 您可以读取JSON文件，获取每张图片的Base64编码")
    logger.info("3. Base64编码已经包含MIME类型前缀，可直接用于API调用")
    logger.info("4. 示例用法：")
    logger.info("   with open('temp/all_images_base64.json', 'r') as f:")
    logger.info("       images = json.load(f)")
    logger.info("   for image in images:")
    logger.info("       base64_string = image['base64_with_prefix']")
    logger.info("       # 调用API...")
    
    return results

if __name__ == "__main__":
    convert_all_images()