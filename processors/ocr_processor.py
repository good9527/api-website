#!/usr/bin/env python3
"""
OCR处理器模块
负责识别油价图片并提取结构化数据
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# 添加技能目录到Python路径
sys.path.insert(0, r"C:\Users\19901\.codebuddy\skills\ocr-space")

from ocr_space import ocr_image

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OilPriceOCRProcessor:
    """
    油价图片OCR处理器
    """
    
    def __init__(self):
        """初始化OCR处理器"""
        pass
    
    def recognize_image(self, image_path: str) -> Optional[str]:
        """
        识别图片中的文字
        
        Args:
            image_path: 图片路径
            
        Returns:
            识别到的文字，失败返回None
        """
        try:
            logger.info(f"开始识别图片: {image_path}")
            
            # 调用OCR Space API
            result = ocr_image(image_path, language="chs")
            
            if result:
                logger.info(f"识别成功，文本长度: {len(result)} 字符")
                return result
            else:
                logger.error("识别失败")
                return None
                
        except Exception as e:
            logger.error(f"识别过程中发生错误: {e}")
            return None
    
    def parse_oil_price_data(self, ocr_text: str) -> Dict[str, Any]:
        """
        解析OCR识别到的油价数据
        
        Args:
            ocr_text: OCR识别到的文字
            
        Returns:
            结构化的油价数据
        """
        try:
            # 初始化结果
            result = {
                "title": "",
                "subtitle": "",
                "date": "",
                "regions": [],
                "notes": []
            }
            
            # 按行分割文本
            lines = ocr_text.split('\n')
            lines = [line.strip() for line in lines if line.strip()]
            
            # 提取标题
            if lines and "附表" in lines[0]:
                result["title"] = lines[0]
            
            # 提取副标题
            for line in lines:
                if "各省" in line and "中心城市" in line and "最高零售价格" in line:
                    result["subtitle"] = line
                    break
            
            # 提取日期（从文件名或内容中）
            date_pattern = r"(\d{4})年(\d{1,2})月(\d{1,2})日"
            for line in lines:
                date_match = re.search(date_pattern, line)
                if date_match:
                    year, month, day = date_match.groups()
                    result["date"] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    break
            
            # 解析地区数据
            regions = self._parse_regions(lines)
            result["regions"] = regions
            
            # 提取注释
            notes = self._parse_notes(lines)
            result["notes"] = notes
            
            return result
            
        except Exception as e:
            logger.error(f"解析数据时发生错误: {e}")
            return {"error": str(e)}
    
    def _parse_regions(self, lines: List[str]) -> List[Dict[str, Any]]:
        """
        解析地区数据
        
        Args:
            lines: 文本行列表
            
        Returns:
            地区数据列表
        """
        regions = []
        
        # 查找数据区域
        in_data_section = False
        current_section = ""
        region_names = []
        gasoline_prices = []
        diesel_prices = []
        
        # 预定义的地区名称列表
        known_regions = [
            "北京市", "天津市", "河北省", "山西省", "辽宁省", "吉林省", "黑龙江省",
            "上海市", "江苏省", "浙江省", "安徽省", "福建省", "江西省", "山东省",
            "湖北省", "湖南省", "河南省", "海南省", "重庆市", "广东省", "广西壮族自治区",
            "宁夏回族自治区", "甘肃省", "新疆维吾尔自治区", "内蒙古自治区",
            "呼和浩特市", "成都市", "贵阳市", "昆明市", "西安市", "西宁市",
            "拉萨市", "乌鲁木齐市"
        ]
        
        for i, line in enumerate(lines):
            # 检测数据区域开始
            if "一、实行一省一价的地区" in line:
                in_data_section = True
                current_section = "一省一价"
                continue
            elif "二、暂不实行一省一价的地区" in line:
                current_section = "暂不实行一省一价"
                continue
            elif "注：" in line:
                # 注释部分，停止解析
                break
            
            if in_data_section:
                # 检查是否是已知地区名称
                is_region = False
                for region in known_regions:
                    if region in line:
                        region_names.append(line)
                        is_region = True
                        break
                
                # 如果不是地区名称，检查是否是价格
                if not is_region:
                    # 尝试匹配价格（4-5位数字）
                    price_match = re.match(r'^(\d{4,5})$', line)
                    if price_match:
                        price = int(price_match.group(1))
                        # 合理的价格范围（汽油价格通常在6000-12000元/吨）
                        if 6000 <= price <= 12000:
                            if len(gasoline_prices) < len(region_names):
                                gasoline_prices.append(price)
                            elif len(diesel_prices) < len(region_names):
                                diesel_prices.append(price)
        
        # 组装地区数据
        for i in range(len(region_names)):
            region_data = {
                "name": region_names[i],
                "gasoline_price": gasoline_prices[i] if i < len(gasoline_prices) else None,
                "diesel_price": diesel_prices[i] if i < len(diesel_prices) else None,
                "section": current_section if i < len(region_names) else ""
            }
            regions.append(region_data)
        
        return regions
    
    def _parse_notes(self, lines: List[str]) -> List[str]:
        """
        解析注释信息
        
        Args:
            lines: 文本行列表
            
        Returns:
            注释列表
        """
        notes = []
        in_notes_section = False
        
        for line in lines:
            if "注：" in line:
                in_notes_section = True
                # 提取"注："后面的内容
                note_content = line.split("注：")[1].strip()
                if note_content:
                    notes.append(note_content)
                continue
            
            if in_notes_section:
                # 注释可能跨多行
                if line and not re.match(r'^\d+\.', line):
                    notes.append(line)
                else:
                    # 遇到新的编号或非注释内容，停止
                    break
        
        return notes
    
    def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        处理单张图片，返回结构化数据
        
        Args:
            image_path: 图片路径
            
        Returns:
            结构化的油价数据
        """
        # 从文件名提取日期
        date_from_filename = self._extract_date_from_filename(image_path)
        
        # 识别图片
        ocr_text = self.recognize_image(image_path)
        
        if not ocr_text:
            return {
                "success": False,
                "error": "图片识别失败",
                "image_path": image_path,
                "date": date_from_filename
            }
        
        # 解析数据
        parsed_data = self.parse_oil_price_data(ocr_text)
        
        # 如果OCR没有提取到日期，使用文件名中的日期
        if not parsed_data.get("date") and date_from_filename:
            parsed_data["date"] = date_from_filename
        
        # 验证数据
        validation_result = self.validate_data(parsed_data)
        parsed_data["validation"] = validation_result
        
        # 添加元数据
        parsed_data["success"] = True
        parsed_data["image_path"] = image_path
        parsed_data["ocr_text_length"] = len(ocr_text)
        
        return parsed_data
    
    def _extract_date_from_filename(self, image_path: str) -> str:
        """
        从文件名中提取日期
        
        Args:
            image_path: 图片路径
            
        Returns:
            日期字符串，格式为YYYY-MM-DD
        """
        try:
            # 从文件名中提取日期
            filename = Path(image_path).stem
            # 文件名格式: oil_price_YYYY-MM-DD
            if filename.startswith("oil_price_"):
                date_str = filename.replace("oil_price_", "")
                # 验证日期格式
                if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                    return date_str
            return ""
        except Exception:
            return ""
    
    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证解析后的数据质量
        
        Args:
            data: 解析后的数据
            
        Returns:
            验证结果
        """
        validation = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "statistics": {}
        }
        
        # 检查必要字段
        required_fields = ["title", "subtitle", "regions"]
        for field in required_fields:
            if field not in data or not data[field]:
                validation["warnings"].append(f"缺少必要字段: {field}")
        
        # 检查地区数据
        regions = data.get("regions", [])
        validation["statistics"]["total_regions"] = len(regions)
        
        if not regions:
            validation["errors"].append("未找到地区数据")
            validation["is_valid"] = False
        else:
            # 检查每个地区的数据完整性
            complete_regions = 0
            for region in regions:
                if region.get("gasoline_price") and region.get("diesel_price"):
                    complete_regions += 1
                else:
                    validation["warnings"].append(f"地区 {region.get('name', '未知')} 数据不完整")
            
            validation["statistics"]["complete_regions"] = complete_regions
            validation["statistics"]["completeness_rate"] = complete_regions / len(regions) if regions else 0
            
            # 如果完整性率太低，标记为无效（只需有汽油价格即可）
            # 只要有任何一个地区有汽油价格就算有效
            has_any_gasoline = any(r.get("gasoline_price") for r in regions)
            if not has_any_gasoline:
                validation["errors"].append("没有任何地区的汽油价格数据")
                validation["is_valid"] = False
            elif validation["statistics"]["completeness_rate"] < 0.3:
                validation["warnings"].append(f"数据完整性率偏低: {validation['statistics']['completeness_rate']:.1%}")
        
        # 检查价格合理性
        for region in regions:
            gasoline_price = region.get("gasoline_price")
            diesel_price = region.get("diesel_price")
            
            if gasoline_price and not (6000 <= gasoline_price <= 12000):
                validation["warnings"].append(f"地区 {region.get('name', '未知')} 汽油价格异常: {gasoline_price}")
            
            if diesel_price and not (5000 <= diesel_price <= 11000):
                validation["warnings"].append(f"地区 {region.get('name', '未知')} 柴油价格异常: {diesel_price}")
        
        return validation


def main():
    """测试函数"""
    # 测试图片路径
    image_path = r"h:\2026年项目\2.建立一个api网站\api\v1\oil-price\images\oil_price_2026-05-21.png"
    
    processor = OilPriceOCRProcessor()
    result = processor.process_image(image_path)
    
    print("=== 处理结果 ===")
    print(f"成功: {result.get('success', False)}")
    
    if result.get('success'):
        print(f"标题: {result.get('title', '无')}")
        print(f"副标题: {result.get('subtitle', '无')}")
        print(f"日期: {result.get('date', '无')}")
        print(f"地区数量: {len(result.get('regions', []))}")
        print(f"注释数量: {len(result.get('notes', []))}")
        
        # 显示前3个地区
        regions = result.get('regions', [])
        if regions:
            print("\n前3个地区:")
            for i, region in enumerate(regions[:3]):
                print(f"  {i+1}. {region['name']}: 汽油 {region['gasoline_price']}元/吨, 柴油 {region['diesel_price']}元/吨")
    else:
        print(f"错误: {result.get('error', '未知错误')}")


if __name__ == "__main__":
    main()