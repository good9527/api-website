"""
数据清洗模块
负责数据去重、格式化、缺失值处理等
"""

import re
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from copy import deepcopy


class DataCleaner:
    """
    数据清洗器
    
    提供数据清洗功能，包括：
    - 去除重复数据
    - 格式化字段
    - 处理缺失值
    - 标准化数据格式
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化数据清洗器
        
        Args:
            config: 清洗配置
        """
        self.config = config or {}
        self.logger = logging.getLogger("cleaner")
        
        # 清洗规则
        self.rules = self.config.get('rules', {})
    
    def clean(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清洗数据
        
        Args:
            data: 原始数据
            
        Returns:
            清洗后的数据
        """
        self.logger.info("开始数据清洗")
        
        # 深拷贝数据，避免修改原始数据
        cleaned_data = deepcopy(data)
        
        # 执行清洗步骤
        cleaned_data = self._remove_duplicates(cleaned_data)
        cleaned_data = self._normalize_fields(cleaned_data)
        cleaned_data = self._handle_missing_values(cleaned_data)
        cleaned_data = self._format_data(cleaned_data)
        cleaned_data = self._clean_strings(cleaned_data)
        
        self.logger.info("数据清洗完成")
        
        return cleaned_data
    
    def _remove_duplicates(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        去除重复数据
        
        Args:
            data: 数据
            
        Returns:
            去重后的数据
        """
        self.logger.debug("去除重复数据")
        
        # 查找数组字段并去重
        for key, value in data.items():
            if isinstance(value, list):
                # 根据数据类型选择去重策略
                if value and isinstance(value[0], dict):
                    # 字典列表去重
                    data[key] = self._deduplicate_dicts(value)
                else:
                    # 简单值去重
                    data[key] = list(dict.fromkeys(value))
        
        return data
    
    def _deduplicate_dicts(self, dict_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        字典列表去重
        
        Args:
            dict_list: 字典列表
            
        Returns:
            去重后的字典列表
        """
        seen = set()
        unique_list = []
        
        for item in dict_list:
            # 将字典转换为可哈希的元组
            item_tuple = tuple(sorted(item.items()))
            
            if item_tuple not in seen:
                seen.add(item_tuple)
                unique_list.append(item)
        
        return unique_list
    
    def _normalize_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化字段名称
        
        Args:
            data: 数据
            
        Returns:
            标准化后的数据
        """
        self.logger.debug("标准化字段名称")
        
        normalized_data = {}
        
        for key, value in data.items():
            # 标准化字段名：小写、下划线分隔
            normalized_key = self._normalize_key(key)
            normalized_data[normalized_key] = value
        
        return normalized_data
    
    def _normalize_key(self, key: str) -> str:
        """
        标准化字段名
        
        Args:
            key: 原始字段名
            
        Returns:
            标准化后的字段名
        """
        # 转换为小写
        key = key.lower()
        
        # 替换特殊字符为下划线
        key = re.sub(r'[^a-z0-9_]', '_', key)
        
        # 移除连续的下划线
        key = re.sub(r'_+', '_', key)
        
        # 移除首尾下划线
        key = key.strip('_')
        
        return key
    
    def _handle_missing_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理缺失值
        
        Args:
            data: 数据
            
        Returns:
            处理后的数据
        """
        self.logger.debug("处理缺失值")
        
        # 获取缺失值处理策略
        strategy = self.rules.get('missing_values', 'remove')
        
        for key, value in data.items():
            if value is None:
                if strategy == 'remove':
                    # 移除None值字段
                    continue
                elif strategy == 'default':
                    # 使用默认值
                    default_values = self.rules.get('default_values', {})
                    data[key] = default_values.get(key, '')
                elif strategy == 'keep':
                    # 保持None值
                    pass
            
            # 递归处理嵌套字典
            if isinstance(value, dict):
                data[key] = self._handle_missing_values(value)
            
            # 处理列表中的缺失值
            if isinstance(value, list):
                data[key] = self._handle_missing_values_in_list(value)
        
        return data
    
    def _handle_missing_values_in_list(self, data_list: List[Any]) -> List[Any]:
        """
        处理列表中的缺失值
        
        Args:
            data_list: 数据列表
            
        Returns:
            处理后的列表
        """
        strategy = self.rules.get('missing_values', 'remove')
        
        if strategy == 'remove':
            # 移除None值
            return [item for item in data_list if item is not None]
        elif strategy == 'keep':
            return data_list
        
        return data_list
    
    def _format_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化数据
        
        Args:
            data: 数据
            
        Returns:
            格式化后的数据
        """
        self.logger.debug("格式化数据")
        
        for key, value in data.items():
            # 格式化日期时间
            if isinstance(value, str) and self._is_datetime(value):
                data[key] = self._format_datetime(value)
            
            # 格式化数字
            if isinstance(value, (int, float)):
                data[key] = self._format_number(value)
            
            # 递归处理嵌套字典
            if isinstance(value, dict):
                data[key] = self._format_data(value)
            
            # 处理列表中的数据
            if isinstance(value, list):
                data[key] = [self._format_data(item) if isinstance(item, dict) else item for item in value]
        
        return data
    
    def _is_datetime(self, value: str) -> bool:
        """
        检查字符串是否是日期时间格式
        
        Args:
            value: 字符串
            
        Returns:
            是否是日期时间格式
        """
        datetime_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO格式
        ]
        
        for pattern in datetime_patterns:
            if re.match(pattern, value):
                return True
        
        return False
    
    def _format_datetime(self, value: str) -> str:
        """
        格式化日期时间
        
        Args:
            value: 日期时间字符串
            
        Returns:
            格式化后的ISO格式字符串
        """
        try:
            # 尝试解析各种格式
            formats = [
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%Y年%m月%d日"
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    continue
            
            # 如果无法解析，返回原始值
            return value
            
        except Exception:
            return value
    
    def _format_number(self, value: Union[int, float]) -> Union[int, float]:
        """
        格式化数字
        
        Args:
            value: 数字
            
        Returns:
            格式化后的数字
        """
        # 如果是浮点数，保留2位小数
        if isinstance(value, float):
            return round(value, 2)
        
        return value
    
    def _clean_strings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理字符串
        
        Args:
            data: 数据
            
        Returns:
            清理后的数据
        """
        self.logger.debug("清理字符串")
        
        for key, value in data.items():
            if isinstance(value, str):
                # 去除首尾空白
                value = value.strip()
                
                # 标准化空白字符
                value = re.sub(r'\s+', ' ', value)
                
                # 移除不可见字符
                value = ''.join(char for char in value if char.isprintable())
                
                data[key] = value
            
            # 递归处理嵌套字典
            if isinstance(value, dict):
                data[key] = self._clean_strings(value)
            
            # 处理列表中的字符串
            if isinstance(value, list):
                data[key] = [self._clean_strings(item) if isinstance(item, dict) else item for item in value]
        
        return data
    
    def add_rule(self, rule_name: str, rule_config: Any):
        """
        添加清洗规则
        
        Args:
            rule_name: 规则名称
            rule_config: 规则配置
        """
        self.rules[rule_name] = rule_config
        self.logger.info(f"添加清洗规则: {rule_name}")
    
    def get_rules(self) -> Dict[str, Any]:
        """
        获取所有清洗规则
        
        Returns:
            清洗规则字典
        """
        return self.rules.copy()