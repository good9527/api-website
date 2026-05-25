"""
国内油价数据采集器
从国家发改委官网采集国内成品油价格信息及图片
"""

import re
import os
import json
import time
import requests
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path
from bs4 import BeautifulSoup

from .base import BaseCollector, CollectorResult, CollectorStatus
from .registry import CollectorRegistry


@CollectorRegistry.register("oil-price")
class OilPriceCollector(BaseCollector):
    """
    国内油价数据采集器
    
    从国家发改委官网采集国内成品油价格调整公告，提取图片附件
    """
    
    # 默认配置
    DEFAULT_CONFIG = {
        "name": "国内油价",
        "url": "https://www.ndrc.gov.cn/xwdt/xwfb/",
        "timeout": 30,
        "retries": 3,
        "headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化油价采集器
        
        Args:
            config: 配置字典，如果为None则使用默认配置
        """
        # 合并默认配置
        final_config = {**self.DEFAULT_CONFIG, **(config or {})}
        super().__init__(final_config)
        
        # 图片存储目录
        self.image_dir = Path("api/v1/oil-price/images")
        self.image_dir.mkdir(parents=True, exist_ok=True)
    
    def collect(self) -> CollectorResult:
        """
        执行油价数据采集（采集最新一条）
        
        Returns:
            CollectorResult: 采集结果
        """
        self.logger.info("开始采集国内油价数据（最新一条）")
        
        try:
            # 1. 获取最新公告链接
            latest_link = self._get_latest_announcement_link()
            if not latest_link:
                raise Exception("未找到油价公告链接")
            
            # 2. 处理单个公告
            data = self._process_announcement(latest_link)
            
            return CollectorResult(
                source=self.name,
                status=CollectorStatus.SUCCESS,
                data=data,
                metadata=self._create_metadata(data)
            )
            
        except Exception as e:
            self.logger.error(f"采集油价数据失败: {e}")
            return CollectorResult(
                source=self.name,
                status=CollectorStatus.ERROR,
                error=str(e)
            )
    
    def collect_all(self) -> CollectorResult:
        """
        执行油价数据采集（采集所有公告）
        
        Returns:
            CollectorResult: 采集结果
        """
        self.logger.info("开始采集所有油价公告数据")
        
        try:
            # 1. 获取所有公告链接
            all_links = self._get_all_announcement_links()
            if not all_links:
                raise Exception("未找到油价公告链接")
            
            # 2. 处理所有公告
            all_data = []
            for i, link in enumerate(all_links):
                self.logger.info(f"处理第{i+1}/{len(all_links)}个公告: {link['title']}")
                try:
                    data = self._process_announcement(link)
                    all_data.append(data)
                    # 添加延迟，避免频繁请求
                    if i < len(all_links) - 1:
                        time.sleep(2)
                except Exception as e:
                    self.logger.error(f"处理公告失败: {link['title']}, 错误: {e}")
                    continue
            
            # 3. 构建返回数据
            result_data = {
                "update_time": datetime.now(timezone.utc).isoformat(),
                "total_count": len(all_links),
                "processed_count": len(all_data),
                "announcements": all_data
            }
            
            return CollectorResult(
                source=self.name,
                status=CollectorStatus.SUCCESS,
                data=result_data,
                metadata=self._create_metadata(result_data)
            )
            
        except Exception as e:
            self.logger.error(f"采集所有油价数据失败: {e}")
            return CollectorResult(
                source=self.name,
                status=CollectorStatus.ERROR,
                error=str(e)
            )
    
    def _process_announcement(self, link_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理单个公告
        
        Args:
            link_info: 公告链接信息，包含title、url、date
            
        Returns:
            处理后的公告数据
        """
        self.logger.info(f"处理公告: {link_info['title']}")
        
        try:
            # 1. 获取公告页面内容
            announcement_html = self._fetch_announcement_page(link_info['url'])
            
            # 2. 提取图片附件
            try:
                image_url = self._extract_image_from_html(announcement_html, link_info['url'])
                # 3. 下载图片
                image_path = self._download_image(image_url, link_info['date'])
                image_data = {
                    "url": image_url,
                    "local_path": str(image_path),
                    "api_endpoint": f"/api/v1/oil-price/images/{image_path.name}"
                }
            except Exception as e:
                self.logger.warning(f"公告 {link_info['title']} 没有图片附件: {e}")
                image_data = None
            
            # 4. 构建返回数据
            data = {
                "announcement": {
                    "title": link_info['title'],
                    "url": link_info['url'],
                    "date": link_info['date']
                },
                "image": image_data,
                "has_image": image_data is not None
            }
            
            return data
            
        except Exception as e:
            self.logger.error(f"处理公告失败: {link_info['title']}, 错误: {e}")
            raise
    
    def _get_latest_announcement_link(self) -> Optional[Dict[str, Any]]:
        """
        从发改委列表页面获取最新的油价公告链接
        
        Returns:
            最新公告链接信息，包含title、url、date
        """
        self.logger.info(f"获取列表页面: {self.url}")
        
        try:
            response = self.session.get(self.url, timeout=self.timeout)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找所有包含"成品油价格"的链接
            links = []
            for a in soup.find_all('a'):
                href = a.get('href', '')
                title = a.get_text()
                if '成品油价格' in title and href.startswith('./'):
                    # 转换为绝对路径
                    full_url = f"https://www.ndrc.gov.cn/xwdt/xwfb/{href[2:]}"
                    
                    # 从标题中提取日期
                    date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', title)
                    if date_match:
                        year, month, day = date_match.groups()
                        date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    else:
                        # 从URL中提取日期
                        url_date_match = re.search(r't(\d{4})(\d{2})(\d{2})_', href)
                        if url_date_match:
                            year, month, day = url_date_match.groups()
                            date_str = f"{year}-{month}-{day}"
                        else:
                            continue
                    
                    links.append({
                        'title': title,
                        'url': full_url,
                        'date': date_str
                    })
            
            if not links:
                self.logger.warning("未找到油价公告链接")
                return None
            
            # 按日期排序，获取最新的
            links.sort(key=lambda x: x['date'], reverse=True)
            latest = links[0]
            
            self.logger.info(f"找到最新公告: {latest['title']} ({latest['date']})")
            return latest
            
        except Exception as e:
            self.logger.error(f"获取列表页面失败: {e}")
            raise
    
    def _get_all_announcement_links(self) -> List[Dict[str, Any]]:
        """
        从发改委列表页面获取所有油价公告链接（遍历所有分页）
        
        Returns:
            所有公告链接列表，每个元素包含title、url、date
        """
        self.logger.info("开始获取所有油价公告链接")
        
        all_links = []
        base_url = "https://www.ndrc.gov.cn/xwdt/xwfb/"
        
        # 遍历所有分页（共40页）
        for page in range(1, 41):
            try:
                # 构建分页URL
                if page == 1:
                    page_url = base_url
                else:
                    page_url = f"{base_url}index_{page - 1}.html"
                
                self.logger.info(f"获取第{page}页: {page_url}")
                
                response = self.session.get(page_url, timeout=self.timeout)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找当前页面中包含"成品油价格"或搁浅相关关键词的链接
                keywords = ["成品油价格", "搁浅", "取消", "推迟", "暂停", "不调整", "不作调整"]
                for a in soup.find_all('a'):
                    href = a.get('href', '')
                    title = a.get_text()
                    if any(keyword in title for keyword in keywords) and href.startswith('./'):
                        # 转换为绝对路径
                        full_url = f"https://www.ndrc.gov.cn/xwdt/xwfb/{href[2:]}"
                        
                        # 从标题中提取日期
                        date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', title)
                        if date_match:
                            year, month, day = date_match.groups()
                            date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        else:
                            # 从URL中提取日期
                            url_date_match = re.search(r't(\d{4})(\d{2})(\d{2})_', href)
                            if url_date_match:
                                year, month, day = url_date_match.groups()
                                date_str = f"{year}-{month}-{day}"
                            else:
                                continue
                        
                        # 避免重复
                        link_info = {
                            'title': title,
                            'url': full_url,
                            'date': date_str
                        }
                        if link_info not in all_links:
                            all_links.append(link_info)
                
                # 添加延迟，避免频繁请求
                if page < 40:
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"获取第{page}页失败: {e}")
                continue
        
        # 按日期排序
        all_links.sort(key=lambda x: x['date'], reverse=True)
        
        self.logger.info(f"共找到{len(all_links)}个油价公告链接")
        return all_links
    
    def _fetch_announcement_page(self, url: str) -> str:
        """
        获取公告页面HTML内容
        
        Args:
            url: 公告页面URL
            
        Returns:
            HTML内容
        """
        self.logger.info(f"获取公告页面: {url}")
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            self.logger.error(f"获取公告页面失败: {e}")
            raise
    
    def _extract_image_from_html(self, html: str, base_url: str) -> str:
        """
        从公告页面HTML中提取图片附件URL
        
        Args:
            html: HTML内容
            base_url: 基础URL，用于处理相对路径
            
        Returns:
            图片URL
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # 查找附件区域
        attachment_div = soup.find('div', class_='attachment_l')
        if attachment_div:
            # 在附件区域查找图片
            img = attachment_div.find('img')
            if img:
                src = img.get('src', '')
                if src:
                    # 处理相对路径
                    if src.startswith('./'):
                        # 从base_url提取目录部分
                        base_dir = base_url.rsplit('/', 1)[0]
                        return f"{base_dir}/{src[2:]}"
                    elif src.startswith('/'):
                        return f"https://www.ndrc.gov.cn{src}"
                    elif src.startswith('http'):
                        return src
        
        # 如果附件区域没有找到，查找所有图片
        for img in soup.find_all('img'):
            src = img.get('src', '')
            # 跳过网站图标等小图片
            if 'favicon' in src or 'logo' in src or 'icon' in src:
                continue
            # 查找可能的价格表图片
            if 'W0' in src or 'price' in src.lower() or 'oil' in src.lower():
                if src.startswith('./'):
                    base_dir = base_url.rsplit('/', 1)[0]
                    return f"{base_dir}/{src[2:]}"
                elif src.startswith('/'):
                    return f"https://www.ndrc.gov.cn{src}"
                elif src.startswith('http'):
                    return src
        
        # 如果还是没有找到，返回页面中的第一个非图标图片
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src and 'favicon' not in src and 'logo' not in src and 'icon' not in src:
                if src.startswith('./'):
                    base_dir = base_url.rsplit('/', 1)[0]
                    return f"{base_dir}/{src[2:]}"
                elif src.startswith('/'):
                    return f"https://www.ndrc.gov.cn{src}"
                elif src.startswith('http'):
                    return src
        
        raise Exception("未找到图片附件")
    
    def _download_image(self, url: str, date_str: str) -> Path:
        """
        下载图片到本地
        
        Args:
            url: 图片URL
            date_str: 日期字符串，用于文件名
            
        Returns:
            本地文件路径
        """
        self.logger.info(f"下载图片: {url}")
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # 生成文件名
            file_extension = '.png' if '.png' in url.lower() else '.jpg'
            filename = f"oil_price_{date_str}{file_extension}"
            file_path = self.image_dir / filename
            
            # 保存图片
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"图片已保存: {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"下载图片失败: {e}")
            raise
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        验证油价数据
        
        Args:
            data: 油价数据
            
        Returns:
            bool: 数据是否有效
        """
        try:
            # 检查是否是所有公告的数据结构
            if "announcements" in data:
                return self._validate_all_announcements(data)
            else:
                return self._validate_single_announcement(data)
            
        except Exception as e:
            self.logger.error(f"验证油价数据时发生异常: {e}")
            return False
    
    def _validate_single_announcement(self, data: Dict[str, Any]) -> bool:
        """
        验证单个公告数据
        
        Args:
            data: 单个公告数据
            
        Returns:
            bool: 数据是否有效
        """
        # 检查必要字段
        required_fields = ["announcement", "has_image"]
        for field in required_fields:
            if field not in data:
                self.logger.error(f"缺少{field}字段")
                return False
        
        # 检查announcement字段
        announcement = data["announcement"]
        if not isinstance(announcement, dict):
            self.logger.error("announcement字段不是对象")
            return False
        
        announcement_fields = ["title", "url", "date"]
        for field in announcement_fields:
            if field not in announcement:
                self.logger.error(f"announcement缺少{field}字段")
                return False
        
        # 检查has_image字段
        has_image = data["has_image"]
        if not isinstance(has_image, bool):
            self.logger.error("has_image字段不是布尔值")
            return False
        
        # 如果有图片，检查图片字段
        if has_image:
            image = data.get("image")
            if not image or not isinstance(image, dict):
                self.logger.error("有图片但image字段无效")
                return False
            
            image_fields = ["url", "local_path", "api_endpoint"]
            for field in image_fields:
                if field not in image:
                    self.logger.error(f"image缺少{field}字段")
                    return False
            
            # 检查图片文件是否存在
            image_path = Path(image["local_path"])
            if not image_path.exists():
                self.logger.error(f"图片文件不存在: {image_path}")
                return False
        
        self.logger.info("单个公告数据验证通过")
        return True
    
    def _validate_all_announcements(self, data: Dict[str, Any]) -> bool:
        """
        验证所有公告数据
        
        Args:
            data: 所有公告数据
            
        Returns:
            bool: 数据是否有效
        """
        # 检查必要字段
        required_fields = ["update_time", "total_count", "processed_count", "announcements"]
        for field in required_fields:
            if field not in data:
                self.logger.error(f"缺少{field}字段")
                return False
        
        # 检查announcements字段
        announcements = data["announcements"]
        if not isinstance(announcements, list):
            self.logger.error("announcements字段不是数组")
            return False
        
        # 验证每个公告
        for i, announcement in enumerate(announcements):
            if not self._validate_single_announcement(announcement):
                self.logger.error(f"第{i+1}个公告验证失败")
                return False
        
        self.logger.info(f"所有公告数据验证通过，共{len(announcements)}个公告")
        return True
    
    def transform(self, raw_data: Any) -> Dict[str, Any]:
        """
        转换原始油价数据为标准格式
        
        Args:
            raw_data: 原始数据
            
        Returns:
            Dict[str, Any]: 标准格式的油价数据
        """
        # 如果已经是字典，直接返回
        if isinstance(raw_data, dict):
            return raw_data
        
        raise ValueError(f"不支持的数据类型: {type(raw_data)}")
    
    def _create_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建元数据
        
        Args:
            data: 数据
            
        Returns:
            元数据
        """
        # 检查是否是所有公告的数据结构
        if "announcements" in data:
            return {
                "source": self.name,
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "version": datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
                "quality_score": self._calculate_quality_score(data),
                "fields_count": len(data.keys()),
                "total_announcements": data.get("total_count", 0),
                "processed_announcements": data.get("processed_count", 0)
            }
        else:
            return {
                "source": self.name,
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "version": datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
                "quality_score": self._calculate_quality_score(data),
                "fields_count": len(data.keys()),
                "has_image": data.get("has_image", False)
            }
    
    def _calculate_quality_score(self, data: Dict[str, Any]) -> float:
        """
        计算数据质量评分
        
        Args:
            data: 数据
            
        Returns:
            质量评分（0-1）
        """
        # 检查是否是所有公告的数据结构
        if "announcements" in data:
            return self._calculate_quality_score_all(data)
        else:
            return self._calculate_quality_score_single(data)
    
    def _calculate_quality_score_single(self, data: Dict[str, Any]) -> float:
        """
        计算单个公告的数据质量评分
        
        Args:
            data: 单个公告数据
            
        Returns:
            质量评分（0-1）
        """
        score = 1.0
        
        # 检查必要字段
        required_fields = ["announcement", "has_image"]
        for field in required_fields:
            if field not in data:
                score -= 0.2
        
        # 检查公告信息完整性
        announcement = data.get("announcement", {})
        if not announcement.get("title"):
            score -= 0.1
        if not announcement.get("url"):
            score -= 0.1
        if not announcement.get("date"):
            score -= 0.1
        
        # 检查是否有图片
        has_image = data.get("has_image", False)
        if has_image:
            # 如果有图片，检查图片信息完整性
            image = data.get("image", {})
            if not image:
                score -= 0.3  # 声明有图片但没有图片数据
            else:
                if not image.get("url"):
                    score -= 0.1
                if not image.get("local_path"):
                    score -= 0.1
                
                # 检查图片文件是否存在
                image_path = image.get("local_path")
                if image_path and not Path(image_path).exists():
                    score -= 0.2
        else:
            # 如果没有图片，适当扣分（因为图片是重要数据）
            score -= 0.3
        
        return max(0.0, min(1.0, score))
    
    def _calculate_quality_score_all(self, data: Dict[str, Any]) -> float:
        """
        计算所有公告的数据质量评分
        
        Args:
            data: 所有公告数据
            
        Returns:
            质量评分（0-1）
        """
        score = 1.0
        
        # 检查必要字段
        required_fields = ["update_time", "total_count", "processed_count", "announcements"]
        for field in required_fields:
            if field not in data:
                score -= 0.2
        
        # 检查公告列表
        announcements = data.get("announcements", [])
        if not announcements:
            score -= 0.3
        else:
            # 计算每个公告的平均质量分
            total_score = 0
            for announcement in announcements:
                total_score += self._calculate_quality_score_single(announcement)
            average_score = total_score / len(announcements)
            score = (score + average_score) / 2
        
        return max(0.0, min(1.0, score))