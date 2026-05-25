"""
数据采集器基类
提供统一的接口、日志、重试机制和错误处理
"""

import abc
import time
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class CollectorStatus(Enum):
    """采集器状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class CollectorResult:
    """采集结果数据类"""
    source: str
    status: CollectorStatus
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    collected_at: Optional[str] = None
    duration: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['status'] = self.status.value
        return result
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class BaseCollector(abc.ABC):
    """
    数据采集器抽象基类
    
    所有数据源采集器都必须继承此类并实现抽象方法
    提供统一的接口、日志记录、重试机制和错误处理
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化采集器
        
        Args:
            config: 数据源配置字典，包含以下字段：
                - name: 数据源名称
                - url: 数据源URL
                - timeout: 请求超时时间（秒）
                - retries: 重试次数
                - headers: 请求头
                - params: 请求参数
        """
        self.config = config
        self.name = config.get('name', self.__class__.__name__)
        self.url = config.get('url', '')
        self.timeout = config.get('timeout', 30)
        self.retries = config.get('retries', 3)
        self.headers = config.get('headers', {})
        self.params = config.get('params', {})
        
        # 设置日志
        self.logger = logging.getLogger(f"collector.{self.name}")
        
        # 创建带重试机制的会话
        self.session = self._create_session()
        
        # 状态信息
        self.status = CollectorStatus.IDLE
        self.last_run = None
        self.last_error = None
        self.run_count = 0
        self.success_count = 0
    
    def _create_session(self) -> requests.Session:
        """创建带重试机制的HTTP会话"""
        session = requests.Session()
        
        # 设置重试策略
        retry_strategy = Retry(
            total=self.retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        # 创建适配器
        adapter = HTTPAdapter(max_retries=retry_strategy)
        
        # 挂载适配器
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 设置默认请求头
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            **self.headers
        })
        
        return session
    
    @abc.abstractmethod
    def collect(self) -> CollectorResult:
        """
        执行数据采集（抽象方法）
        
        Returns:
            CollectorResult: 采集结果
        """
        pass
    
    @abc.abstractmethod
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        验证采集到的数据（抽象方法）
        
        Args:
            data: 采集到的数据
            
        Returns:
            bool: 数据是否有效
        """
        pass
    
    @abc.abstractmethod
    def transform(self, raw_data: Any) -> Dict[str, Any]:
        """
        转换原始数据为标准格式（抽象方法）
        
        Args:
            raw_data: 原始数据
            
        Returns:
            Dict[str, Any]: 标准格式的数据
        """
        pass
    
    def fetch_data(self, url: Optional[str] = None, **kwargs) -> requests.Response:
        """
        从URL获取数据
        
        Args:
            url: 数据URL，如果为None则使用配置中的URL
            **kwargs: 传递给requests.get的额外参数
            
        Returns:
            requests.Response: HTTP响应对象
            
        Raises:
            requests.RequestException: 请求失败
        """
        target_url = url or self.url
        if not target_url:
            raise ValueError("未指定数据URL")
        
        self.logger.info(f"开始请求数据: {target_url}")
        
        try:
            response = self.session.get(
                target_url,
                timeout=self.timeout,
                params=self.params,
                **kwargs
            )
            response.raise_for_status()
            
            self.logger.info(f"请求成功，状态码: {response.status_code}")
            return response
            
        except requests.Timeout:
            self.logger.error(f"请求超时: {target_url}")
            raise
        except requests.HTTPError as e:
            self.logger.error(f"HTTP错误: {e}")
            raise
        except requests.RequestException as e:
            self.logger.error(f"请求异常: {e}")
            raise
    
    def fetch_json(self, url: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        获取JSON数据
        
        Args:
            url: 数据URL
            **kwargs: 传递给requests.get的额外参数
            
        Returns:
            Dict[str, Any]: 解析后的JSON数据
        """
        response = self.fetch_data(url, **kwargs)
        return response.json()
    
    def fetch_html(self, url: Optional[str] = None, **kwargs) -> str:
        """
        获取HTML内容
        
        Args:
            url: 数据URL
            **kwargs: 传递给requests.get的额外参数
            
        Returns:
            str: HTML内容
        """
        response = self.fetch_data(url, **kwargs)
        return response.text
    
    def run(self) -> CollectorResult:
        """
        执行完整的采集流程
        
        Returns:
            CollectorResult: 采集结果
        """
        start_time = time.time()
        self.status = CollectorStatus.RUNNING
        self.run_count += 1
        
        self.logger.info(f"开始采集: {self.name}")
        
        try:
            # 执行采集
            result = self.collect()
            
            # 验证数据
            if result.data and not self.validate(result.data):
                result.status = CollectorStatus.FAILED
                result.error = "数据验证失败"
                self.logger.error("数据验证失败")
            else:
                result.status = CollectorStatus.SUCCESS
                self.success_count += 1
                self.logger.info("数据采集成功")
            
        except requests.Timeout:
            result = CollectorResult(
                source=self.name,
                status=CollectorStatus.TIMEOUT,
                error="请求超时"
            )
            self.logger.error("采集超时")
            
        except Exception as e:
            result = CollectorResult(
                source=self.name,
                status=CollectorStatus.ERROR,
                error=str(e)
            )
            self.logger.error(f"采集异常: {e}")
        
        # 计算耗时
        duration = time.time() - start_time
        result.duration = duration
        result.collected_at = datetime.now(timezone.utc).isoformat()
        
        # 更新状态
        self.status = result.status
        self.last_run = result.collected_at
        self.last_error = result.error if result.error else None
        
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取采集器状态信息
        
        Returns:
            Dict[str, Any]: 状态信息
        """
        return {
            "name": self.name,
            "status": self.status.value,
            "last_run": self.last_run,
            "last_error": self.last_error,
            "run_count": self.run_count,
            "success_count": self.success_count,
            "success_rate": self.success_count / self.run_count if self.run_count > 0 else 0
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"