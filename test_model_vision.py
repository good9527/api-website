#!/usr/bin/env python3
"""
测试模型视觉识别油价图片
将图片转换为Base64编码，调用OpenAI API进行识别
"""

import os
import sys
import json
import base64
from pathlib import Path
import requests
from typing import Optional, Dict, Any

# 设置日志
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelVisionProcessor:
    """使用OpenAI模型视觉识别图片"""
    
    def __init__(self, api_key: str = None):
        """初始化处理器"""
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("需要提供OpenAI API密钥")
        
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4o"  # 支持视觉的模型
        
    def image_to_base64(self, image_path: str) -> str:
        """
        将图片转换为Base64编码
        
        Args:
            image_path: 图片路径
            
        Returns:
            Base64编码字符串（带MIME类型前缀）
        """
        try:
            # 读取图片文件
            with open(image_path, "rb") as f:
                image_data = f.read()
            
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
            
            logger.info(f"图片转换成功: {image_path} -> {mime_type} ({len(base64_encoded)} 字符)")
            return base64_with_prefix
            
        except Exception as e:
            logger.error(f"图片转换失败: {e}")
            raise
    
    def recognize_image(self, image_base64: str, prompt: str = None) -> Optional[str]:
        """
        使用OpenAI API识别图片
        
        Args:
            image_base64: Base64编码的图片（带前缀）
            prompt: 提示词
            
        Returns:
            识别结果文本
        """
        if not prompt:
            prompt = """请识别这张国内成品油价格表图片，提取以下信息：
1. 日期（从标题或内容中提取）
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
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_base64,
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 4096
        }
        
        try:
            logger.info("正在调用OpenAI API...")
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            logger.info(f"API调用成功，返回内容长度: {len(content)} 字符")
            return content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"响应状态码: {e.response.status_code}")
                logger.error(f"响应内容: {e.response.text[:500]}")
            return None
        except Exception as e:
            logger.error(f"API调用异常: {e}")
            return None
    
    def parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        """
        解析JSON响应
        
        Args:
            text: API返回的文本
            
        Returns:
            解析后的JSON对象
        """
        try:
            # 尝试直接解析
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试提取JSON部分
            import re
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            logger.warning("无法解析JSON响应")
            return None
    
    def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        处理单张图片
        
        Args:
            image_path: 图片路径
            
        Returns:
            处理结果
        """
        try:
            # 1. 转换图片为Base64
            image_base64 = self.image_to_base64(image_path)
            
            # 2. 调用API识别
            response_text = self.recognize_image(image_base64)
            
            if not response_text:
                return {
                    "success": False,
                    "error": "API识别失败",
                    "image_path": image_path
                }
            
            # 3. 解析JSON
            parsed_data = self.parse_json_response(response_text)
            
            if not parsed_data:
                return {
                    "success": False,
                    "error": "JSON解析失败",
                    "image_path": image_path,
                    "raw_response": response_text
                }
            
            # 4. 添加元数据
            parsed_data["success"] = True
            parsed_data["image_path"] = image_path
            parsed_data["model"] = self.model
            parsed_data["raw_response_length"] = len(response_text)
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"处理图片失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "image_path": image_path
            }


def test_single_image():
    """测试单张图片识别"""
    print("=== 测试模型视觉识别油价图片 ===")
    
    # 检查API密钥
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("错误: 未设置OPENAI_API_KEY环境变量")
        print("请先设置: $env:OPENAI_API_KEY='your-api-key'")
        return
    
    # 测试图片路径
    project_root = Path(__file__).parent
    test_images = [
        project_root / "api" / "v1" / "oil-price" / "images" / "oil_price_2021-09-06.jpg",
        project_root / "api" / "v1" / "oil-price" / "images" / "oil_price_2022-01-17.jpg",
        project_root / "api" / "v1" / "oil-price" / "images" / "oil_price_2023-01-03.jpg"
    ]
    
    # 选择第一个存在的图片
    test_image = None
    for img in test_images:
        if img.exists():
            test_image = img
            break
    
    if not test_image:
        print("错误: 未找到测试图片")
        return
    
    print(f"测试图片: {test_image.name}")
    
    # 初始化处理器
    try:
        processor = ModelVisionProcessor(api_key)
    except ValueError as e:
        print(f"初始化失败: {e}")
        return
    
    # 处理图片
    print("正在处理图片...")
    result = processor.process_image(str(test_image))
    
    # 显示结果
    print("\n=== 处理结果 ===")
    print(f"成功: {result.get('success', False)}")
    
    if result.get('success'):
        print(f"日期: {result.get('date', '无')}")
        print(f"标题: {result.get('title', '无')}")
        print(f"地区数量: {len(result.get('regions', []))}")
        
        # 显示前3个地区
        regions = result.get('regions', [])
        if regions:
            print("\n前3个地区:")
            for i, region in enumerate(regions[:3]):
                print(f"  {i+1}. {region.get('name', '未知')}: "
                      f"汽油 {region.get('gasoline_price', '无')}元/吨, "
                      f"柴油 {region.get('diesel_price', '无')}元/吨")
    else:
        print(f"错误: {result.get('error', '未知错误')}")
        if 'raw_response' in result:
            print(f"原始响应: {result['raw_response'][:200]}...")
    
    # 保存结果
    output_file = project_root / "temp" / f"test_vision_{test_image.stem}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到: {output_file}")


if __name__ == "__main__":
    test_single_image()