"""
配置模块
提供配置文件的读取和管理功能
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import os


class ConfigManager:
    """
    配置管理器
    
    负责读取和管理YAML配置文件
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = Path(config_dir)
        self.settings = {}
        self.sources = {}
        
    def load_settings(self) -> Dict[str, Any]:
        """
        加载全局设置
        
        Returns:
            设置字典
        """
        settings_file = self.config_dir / "settings.yaml"
        
        if not settings_file.exists():
            raise FileNotFoundError(f"设置文件不存在: {settings_file}")
        
        with open(settings_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        self.settings = data.get('settings', {})
        return self.settings
    
    def load_sources(self) -> Dict[str, Any]:
        """
        加载数据源配置
        
        Returns:
            数据源配置字典
        """
        sources_file = self.config_dir / "sources.yaml"
        
        if not sources_file.exists():
            raise FileNotFoundError(f"数据源配置文件不存在: {sources_file}")
        
        with open(sources_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        self.sources = data.get('sources', {})
        return self.sources
    
    def get_source_config(self, source_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定数据源的配置
        
        Args:
            source_name: 数据源名称
            
        Returns:
            数据源配置，如果不存在则返回None
        """
        if not self.sources:
            self.load_sources()
        
        return self.sources.get(source_name)
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        获取指定设置项
        
        Args:
            key: 设置键名
            default: 默认值
            
        Returns:
            设置值
        """
        if not self.settings:
            self.load_settings()
        
        return self.settings.get(key, default)
    
    def get_enabled_sources(self) -> Dict[str, Any]:
        """
        获取所有启用的数据源
        
        Returns:
            启用的数据源配置字典
        """
        if not self.sources:
            self.load_sources()
        
        return {
            name: config 
            for name, config in self.sources.items() 
            if config.get('enabled', True)
        }
    
    def reload(self):
        """重新加载所有配置"""
        self.load_settings()
        self.load_sources()


# 全局配置实例
config_manager = ConfigManager()