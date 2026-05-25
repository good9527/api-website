"""
采集器注册中心
自动发现和调度数据采集器
"""

import importlib
import inspect
import pkgutil
from typing import Dict, List, Type, Optional, Any
from pathlib import Path

from .base import BaseCollector


class CollectorRegistry:
    """
    采集器注册中心
    
    负责：
    1. 自动发现采集器模块
    2. 注册采集器类
    3. 创建采集器实例
    4. 管理采集器生命周期
    """
    
    _instance = None
    _collectors: Dict[str, Type[BaseCollector]] = {}
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._collectors = {}
        return cls._instance
    
    @classmethod
    def register(cls, name: Optional[str] = None):
        """
        注册采集器的装饰器
        
        Args:
            name: 采集器名称，如果为None则使用类名
            
        Returns:
            装饰器函数
        """
        def decorator(collector_class: Type[BaseCollector]):
            if not issubclass(collector_class, BaseCollector):
                raise TypeError(f"{collector_class} 必须继承自 BaseCollector")
            
            collector_name = name or collector_class.__name__
            cls._collectors[collector_name] = collector_class
            
            return collector_class
        
        return decorator
    
    @classmethod
    def register_class(cls, collector_class: Type[BaseCollector], name: Optional[str] = None):
        """
        直接注册采集器类
        
        Args:
            collector_class: 采集器类
            name: 采集器名称
        """
        if not issubclass(collector_class, BaseCollector):
            raise TypeError(f"{collector_class} 必须继承自 BaseCollector")
        
        collector_name = name or collector_class.__name__
        cls._collectors[collector_name] = collector_class
    
    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseCollector]]:
        """
        获取采集器类
        
        Args:
            name: 采集器名称
            
        Returns:
            采集器类，如果不存在则返回None
        """
        return cls._collectors.get(name)
    
    @classmethod
    def create(cls, name: str, config: Dict[str, Any]) -> Optional[BaseCollector]:
        """
        创建采集器实例
        
        Args:
            name: 采集器名称
            config: 采集器配置
            
        Returns:
            采集器实例，如果不存在则返回None
        """
        collector_class = cls.get(name)
        if collector_class:
            return collector_class(config)
        return None
    
    @classmethod
    def list_collectors(cls) -> List[str]:
        """
        列出所有注册的采集器名称
        
        Returns:
            采集器名称列表
        """
        return list(cls._collectors.keys())
    
    @classmethod
    def get_all(cls) -> Dict[str, Type[BaseCollector]]:
        """
        获取所有注册的采集器
        
        Returns:
            采集器字典
        """
        return cls._collectors.copy()
    
    @classmethod
    def discover(cls, package_path: str = "collectors"):
        """
        自动发现并注册采集器
        
        Args:
            package_path: 包路径
        """
        try:
            # 导入包
            package = importlib.import_module(package_path)
            package_dir = Path(package.__file__).parent
            
            # 遍历包中的所有模块
            for _, module_name, is_pkg in pkgutil.iter_modules([str(package_dir)]):
                if module_name.startswith('_'):
                    continue
                
                try:
                    # 导入模块
                    module = importlib.import_module(f"{package_path}.{module_name}")
                    
                    # 查找所有BaseCollector子类
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, BaseCollector) and 
                            obj is not BaseCollector and
                            not inspect.isabstract(obj)):
                            
                            # 自动注册
                            cls.register_class(obj, name=obj.__name__)
                            
                except Exception as e:
                    print(f"导入模块 {module_name} 失败: {e}")
                    
        except Exception as e:
            print(f"发现采集器失败: {e}")
    
    @classmethod
    def clear(cls):
        """清空注册表"""
        cls._collectors.clear()
    
    @classmethod
    def create_all(cls, configs: Dict[str, Dict[str, Any]]) -> Dict[str, BaseCollector]:
        """
        根据配置创建所有采集器实例
        
        Args:
            configs: 配置字典，key为采集器名称，value为配置
            
        Returns:
            采集器实例字典
        """
        collectors = {}
        
        for name, config in configs.items():
            collector = cls.create(name, config)
            if collector:
                collectors[name] = collector
            else:
                print(f"警告: 未找到采集器 '{name}'")
        
        return collectors