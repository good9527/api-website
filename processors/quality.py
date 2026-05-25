"""
数据质量评分模块
负责评估数据质量并生成质量评分
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


class QualityScorer:
    """
    数据质量评分器
    
    评估数据质量并生成0-1之间的质量评分
    评分维度：
    - 完整性：必要字段是否齐全
    - 准确性：数据格式和范围是否正确
    - 一致性：数据格式是否统一
    - 时效性：数据是否及时更新
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化质量评分器
        
        Args:
            config: 评分配置
        """
        self.config = config or {}
        self.logger = logging.getLogger("quality")
        
        # 评分权重
        self.weights = self.config.get('weights', {
            'completeness': 0.3,
            'accuracy': 0.3,
            'consistency': 0.2,
            'timeliness': 0.2
        })
        
        # 必要字段定义
        self.required_fields = self.config.get('required_fields', {
            'default': ['status', 'data', 'metadata'],
            'oil-price': ['data.update_time', 'data.prices'],
            'traffic-restrict': ['data.update_time', 'data.restrictions'],
            'policy': ['data.update_time', 'data.policies'],
            'admin-division': ['data.update_time', 'data.divisions'],
            'price-table': ['data.update_time', 'data.prices']
        })
        
        # 字段类型定义
        self.field_types = self.config.get('field_types', {
            'data.update_time': 'datetime',
            'data.prices': 'array',
            'metadata.quality_score': 'number',
            'metadata.collected_at': 'datetime'
        })
    
    def score(self, data: Dict[str, Any], source: str = 'default') -> float:
        """
        计算数据质量评分
        
        Args:
            data: 数据
            source: 数据源名称
            
        Returns:
            质量评分（0-1）
        """
        self.logger.info(f"开始计算数据质量评分: {source}")
        
        # 计算各维度评分
        completeness_score = self._calculate_completeness(data, source)
        accuracy_score = self._calculate_accuracy(data, source)
        consistency_score = self._calculate_consistency(data, source)
        timeliness_score = self._calculate_timeliness(data, source)
        
        # 计算加权总分
        total_score = (
            completeness_score * self.weights['completeness'] +
            accuracy_score * self.weights['accuracy'] +
            consistency_score * self.weights['consistency'] +
            timeliness_score * self.weights['timeliness']
        )
        
        # 确保评分在0-1范围内
        total_score = max(0.0, min(1.0, total_score))
        
        self.logger.info(f"质量评分完成: {total_score:.3f}")
        self.logger.debug(f"各维度评分: 完整性={completeness_score:.3f}, 准确性={accuracy_score:.3f}, "
                         f"一致性={consistency_score:.3f}, 时效性={timeliness_score:.3f}")
        
        return total_score
    
    def _calculate_completeness(self, data: Dict[str, Any], source: str) -> float:
        """
        计算完整性评分
        
        Args:
            data: 数据
            source: 数据源名称
            
        Returns:
            完整性评分（0-1）
        """
        score = 1.0
        
        # 获取必要字段
        required_fields = self.required_fields.get(source, self.required_fields['default'])
        
        # 检查必要字段
        missing_fields = []
        for field_path in required_fields:
            if not self._has_field(data, field_path):
                missing_fields.append(field_path)
        
        # 根据缺失字段数量扣分
        if missing_fields:
            penalty = len(missing_fields) * 0.1
            score = max(0.0, score - penalty)
            self.logger.debug(f"缺失字段: {missing_fields}")
        
        # 检查数据内容
        data_content = data.get('data', {})
        if isinstance(data_content, dict):
            # 检查数组字段是否为空
            for key, value in data_content.items():
                if isinstance(value, list) and len(value) == 0:
                    score = max(0.0, score - 0.05)
                    self.logger.debug(f"空数组字段: {key}")
        
        return score
    
    def _calculate_accuracy(self, data: Dict[str, Any], source: str) -> float:
        """
        计算准确性评分
        
        Args:
            data: 数据
            source: 数据源名称
            
        Returns:
            准确性评分（0-1）
        """
        score = 1.0
        
        # 检查字段类型
        for field_path, expected_type in self.field_types.items():
            value = self._get_field(data, field_path)
            
            if value is not None:
                if not self._check_type(value, expected_type):
                    score = max(0.0, score - 0.05)
                    self.logger.debug(f"字段类型错误: {field_path} (期望: {expected_type}, 实际: {type(value).__name__})")
        
        # 检查数值范围
        if 'data' in data and isinstance(data['data'], dict):
            data_content = data['data']
            
            # 检查价格数据
            if 'prices' in data_content and isinstance(data_content['prices'], list):
                for i, price_item in enumerate(data_content['prices']):
                    if isinstance(price_item, dict):
                        # 检查价格范围
                        price = price_item.get('price')
                        if isinstance(price, (int, float)):
                            if price < 0 or price > 100:
                                score = max(0.0, score - 0.02)
                                self.logger.debug(f"价格超出范围: prices[{i}].price = {price}")
        
        # 检查日期格式
        if 'metadata' in data and isinstance(data['metadata'], dict):
            metadata = data['metadata']
            
            # 检查collected_at格式
            collected_at = metadata.get('collected_at')
            if collected_at and not self._is_valid_datetime(collected_at):
                score = max(0.0, score - 0.02)
                self.logger.debug(f"日期格式错误: metadata.collected_at = {collected_at}")
        
        return score
    
    def _calculate_consistency(self, data: Dict[str, Any], source: str) -> float:
        """
        计算一致性评分
        
        Args:
            data: 数据
            source: 数据源名称
            
        Returns:
            一致性评分（0-1）
        """
        score = 1.0
        
        # 检查数据结构一致性
        if 'data' in data and isinstance(data['data'], dict):
            data_content = data['data']
            
            # 检查数组字段中对象结构是否一致
            for key, value in data_content.items():
                if isinstance(value, list) and len(value) > 1:
                    # 检查数组中对象的字段是否一致
                    first_item = value[0]
                    if isinstance(first_item, dict):
                        first_keys = set(first_item.keys())
                        
                        for i, item in enumerate(value[1:], 1):
                            if isinstance(item, dict):
                                item_keys = set(item.keys())
                                
                                # 检查字段差异
                                missing_keys = first_keys - item_keys
                                extra_keys = item_keys - first_keys
                                
                                if missing_keys or extra_keys:
                                    score = max(0.0, score - 0.01)
                                    self.logger.debug(f"数组字段结构不一致: {key}[{i}]")
        
        # 检查字段命名一致性
        if 'data' in data and isinstance(data['data'], dict):
            data_content = data['data']
            
            # 检查字段命名风格是否一致
            naming_styles = set()
            for key in data_content.keys():
                if '_' in key:
                    naming_styles.add('snake_case')
                elif key[0].isupper():
                    naming_styles.add('PascalCase')
                elif key[0].islower():
                    naming_styles.add('camelCase')
            
            if len(naming_styles) > 1:
                score = max(0.0, score - 0.02)
                self.logger.debug(f"字段命名风格不一致: {naming_styles}")
        
        return score
    
    def _calculate_timeliness(self, data: Dict[str, Any], source: str) -> float:
        """
        计算时效性评分
        
        Args:
            data: 数据
            source: 数据源名称
            
        Returns:
            时效性评分（0-1）
        """
        score = 1.0
        
        # 检查数据更新时间
        data_content = data.get('data', {})
        if isinstance(data_content, dict):
            update_time = data_content.get('update_time')
            
            if update_time:
                try:
                    # 解析更新时间
                    if isinstance(update_time, str):
                        # 尝试多种格式
                        formats = [
                            "%Y-%m-%dT%H:%M:%SZ",
                            "%Y-%m-%dT%H:%M:%S.%fZ",
                            "%Y-%m-%d %H:%M:%S",
                            "%Y-%m-%d"
                        ]
                        
                        update_dt = None
                        for fmt in formats:
                            try:
                                update_dt = datetime.strptime(update_time, fmt)
                                break
                            except ValueError:
                                continue
                        
                        if update_dt:
                            # 计算时间差
                            now = datetime.now(timezone.utc)
                            time_diff = now - update_dt
                            
                            # 根据时间差调整评分
                            hours_diff = time_diff.total_seconds() / 3600
                            
                            if hours_diff > 24:  # 超过24小时
                                score = max(0.0, score - 0.1)
                            elif hours_diff > 168:  # 超过一周
                                score = max(0.0, score - 0.3)
                            elif hours_diff > 720:  # 超过一个月
                                score = max(0.0, score - 0.5)
                
                except Exception as e:
                    self.logger.debug(f"解析更新时间失败: {e}")
                    score = max(0.0, score - 0.05)
        
        # 检查采集时间
        metadata = data.get('metadata', {})
        if isinstance(metadata, dict):
            collected_at = metadata.get('collected_at')
            
            if collected_at:
                try:
                    # 解析采集时间
                    if isinstance(collected_at, str):
                        # 尝试ISO格式
                        collected_dt = datetime.fromisoformat(collected_at.replace('Z', '+00:00'))
                        
                        # 计算时间差
                        now = datetime.now(timezone.utc)
                        time_diff = now - collected_dt
                        
                        # 如果采集时间在未来，扣分
                        if time_diff.total_seconds() < 0:
                            score = max(0.0, score - 0.1)
                            self.logger.debug("采集时间在未来")
                
                except Exception as e:
                    self.logger.debug(f"解析采集时间失败: {e}")
                    score = max(0.0, score - 0.02)
        
        return score
    
    def _has_field(self, data: Dict[str, Any], field_path: str) -> bool:
        """
        检查字段是否存在
        
        Args:
            data: 数据
            field_path: 字段路径（如 'data.update_time'）
            
        Returns:
            字段是否存在
        """
        try:
            value = self._get_field(data, field_path)
            return value is not None
        except:
            return False
    
    def _get_field(self, data: Dict[str, Any], field_path: str) -> Any:
        """
        获取字段值
        
        Args:
            data: 数据
            field_path: 字段路径
            
        Returns:
            字段值
        """
        try:
            parts = field_path.split('.')
            current = data
            
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
            
            return current
        except:
            return None
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """
        检查值的类型
        
        Args:
            value: 值
            expected_type: 期望类型
            
        Returns:
            类型是否匹配
        """
        if expected_type == 'string':
            return isinstance(value, str)
        elif expected_type == 'number':
            return isinstance(value, (int, float))
        elif expected_type == 'integer':
            return isinstance(value, int)
        elif expected_type == 'boolean':
            return isinstance(value, bool)
        elif expected_type == 'array':
            return isinstance(value, list)
        elif expected_type == 'object':
            return isinstance(value, dict)
        elif expected_type == 'datetime':
            # 检查是否是有效的日期时间字符串
            return isinstance(value, str) and self._is_valid_datetime(value)
        
        return True
    
    def _is_valid_datetime(self, value: str) -> bool:
        """
        检查是否是有效的日期时间字符串
        
        Args:
            value: 字符串
            
        Returns:
            是否是有效的日期时间
        """
        try:
            datetime.fromisoformat(value.replace('Z', '+00:00'))
            return True
        except:
            # 尝试其他格式
            formats = [
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d"
            ]
            
            for fmt in formats:
                try:
                    datetime.strptime(value, fmt)
                    return True
                except:
                    continue
            
            return False
    
    def get_score_breakdown(self, data: Dict[str, Any], source: str = 'default') -> Dict[str, Any]:
        """
        获取评分详情
        
        Args:
            data: 数据
            source: 数据源名称
            
        Returns:
            评分详情
        """
        completeness_score = self._calculate_completeness(data, source)
        accuracy_score = self._calculate_accuracy(data, source)
        consistency_score = self._calculate_consistency(data, source)
        timeliness_score = self._calculate_timeliness(data, source)
        
        total_score = (
            completeness_score * self.weights['completeness'] +
            accuracy_score * self.weights['accuracy'] +
            consistency_score * self.weights['consistency'] +
            timeliness_score * self.weights['timeliness']
        )
        
        return {
            "total_score": total_score,
            "breakdown": {
                "completeness": {
                    "score": completeness_score,
                    "weight": self.weights['completeness'],
                    "weighted_score": completeness_score * self.weights['completeness']
                },
                "accuracy": {
                    "score": accuracy_score,
                    "weight": self.weights['accuracy'],
                    "weighted_score": accuracy_score * self.weights['accuracy']
                },
                "consistency": {
                    "score": consistency_score,
                    "weight": self.weights['consistency'],
                    "weighted_score": consistency_score * self.weights['consistency']
                },
                "timeliness": {
                    "score": timeliness_score,
                    "weight": self.weights['timeliness'],
                    "weighted_score": timeliness_score * self.weights['timeliness']
                }
            }
        }