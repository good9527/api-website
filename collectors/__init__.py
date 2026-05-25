"""
数据采集器模块
提供模块化的数据采集器架构，支持多种数据源
"""

from .base import BaseCollector
from .registry import CollectorRegistry

__all__ = ["BaseCollector", "CollectorRegistry"]