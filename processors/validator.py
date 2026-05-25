"""
数据校验模块
负责数据Schema校验和完整性检查
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

import jsonschema
from jsonschema import ValidationError, Draft7Validator


@dataclass
class ValidationResult:
    """校验结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings
        }


class DataValidator:
    """
    数据校验器
    
    提供数据Schema校验和完整性检查功能
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化数据校验器
        
        Args:
            config: 校验配置
        """
        self.config = config or {}
        self.logger = logging.getLogger("validator")
        
        # Schema目录
        self.schema_dir = Path(self.config.get('schema_dir', 'config/schemas'))
        
        # 缓存已加载的Schema
        self.schemas: Dict[str, Dict[str, Any]] = {}
        
        # 校验规则
        self.rules = self.config.get('rules', {})
    
    def validate(self, data: Dict[str, Any], source: str) -> ValidationResult:
        """
        校验数据
        
        Args:
            data: 待校验数据
            source: 数据源名称
            
        Returns:
            ValidationResult: 校验结果
        """
        self.logger.info(f"开始校验数据: {source}")
        
        errors = []
        warnings = []
        
        try:
            # 加载Schema
            schema = self._load_schema(source)
            
            if schema:
                # 使用JSON Schema校验
                schema_errors = self._validate_with_schema(data, schema)
                errors.extend(schema_errors)
            else:
                self.logger.warning(f"未找到Schema: {source}，使用基本校验")
                # 使用基本校验
                basic_errors = self._basic_validation(data, source)
                errors.extend(basic_errors)
            
            # 执行自定义校验规则
            custom_errors, custom_warnings = self._apply_custom_rules(data, source)
            errors.extend(custom_errors)
            warnings.extend(custom_warnings)
            
            # 执行完整性检查
            integrity_errors = self._check_integrity(data, source)
            errors.extend(integrity_errors)
            
            is_valid = len(errors) == 0
            
            self.logger.info(f"数据校验完成: {'通过' if is_valid else '失败'}")
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            self.logger.error(f"数据校验异常: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"校验异常: {str(e)}"],
                warnings=[]
            )
    
    def _load_schema(self, source: str) -> Optional[Dict[str, Any]]:
        """
        加载JSON Schema
        
        Args:
            source: 数据源名称
            
        Returns:
            JSON Schema，如果不存在则返回None
        """
        # 检查缓存
        if source in self.schemas:
            return self.schemas[source]
        
        # 查找Schema文件
        schema_file = self.schema_dir / f"{source}.json"
        
        if not schema_file.exists():
            # 尝试其他可能的文件名
            possible_names = [
                f"{source.replace('-', '_')}.json",
                f"{source.replace('_', '-')}.json",
                f"{source}.schema.json"
            ]
            
            for name in possible_names:
                schema_file = self.schema_dir / name
                if schema_file.exists():
                    break
            else:
                return None
        
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            # 缓存Schema
            self.schemas[source] = schema
            
            self.logger.info(f"加载Schema: {schema_file}")
            return schema
            
        except Exception as e:
            self.logger.error(f"加载Schema失败: {e}")
            return None
    
    def _validate_with_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """
        使用JSON Schema校验数据
        
        Args:
            data: 数据
            schema: JSON Schema
            
        Returns:
            错误信息列表
        """
        errors = []
        
        try:
            # 创建校验器
            validator = Draft7Validator(schema)
            
            # 收集所有错误
            for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
                error_path = " -> ".join(str(p) for p in error.absolute_path)
                error_msg = f"{error_path}: {error.message}" if error_path else error.message
                errors.append(error_msg)
                
        except jsonschema.SchemaError as e:
            errors.append(f"Schema错误: {e.message}")
        except Exception as e:
            errors.append(f"Schema校验异常: {str(e)}")
        
        return errors
    
    def _basic_validation(self, data: Dict[str, Any], source: str) -> List[str]:
        """
        基本数据校验
        
        Args:
            data: 数据
            source: 数据源名称
            
        Returns:
            错误信息列表
        """
        errors = []
        
        # 检查是否为空
        if not data:
            errors.append("数据为空")
            return errors
        
        # 检查必要字段
        required_fields = self.rules.get(f'{source}_required', ['status', 'data', 'metadata'])
        
        for field in required_fields:
            if field not in data:
                errors.append(f"缺少必要字段: {field}")
        
        # 检查status字段
        if 'status' in data:
            if data['status'] not in ['success', 'error']:
                errors.append(f"无效的status值: {data['status']}")
        
        return errors
    
    def _apply_custom_rules(self, data: Dict[str, Any], source: str) -> tuple:
        """
        应用自定义校验规则
        
        Args:
            data: 数据
            source: 数据源名称
            
        Returns:
            (错误列表, 警告列表)
        """
        errors = []
        warnings = []
        
        # 获取自定义规则
        custom_rules = self.rules.get(f'{source}_custom', [])
        
        for rule in custom_rules:
            rule_type = rule.get('type')
            rule_config = rule.get('config', {})
            
            if rule_type == 'range':
                # 范围检查
                field = rule_config.get('field')
                min_val = rule_config.get('min')
                max_val = rule_config.get('max')
                
                if field in data:
                    value = data[field]
                    if isinstance(value, (int, float)):
                        if min_val is not None and value < min_val:
                            errors.append(f"{field} 值 {value} 小于最小值 {min_val}")
                        if max_val is not None and value > max_val:
                            errors.append(f"{field} 值 {value} 大于最大值 {max_val}")
            
            elif rule_type == 'pattern':
                # 正则表达式检查
                import re
                field = rule_config.get('field')
                pattern = rule_config.get('pattern')
                
                if field in data and isinstance(data[field], str):
                    if not re.match(pattern, data[field]):
                        errors.append(f"{field} 格式不匹配: {pattern}")
            
            elif rule_type == 'enum':
                # 枚举检查
                field = rule_config.get('field')
                allowed_values = rule_config.get('values', [])
                
                if field in data and data[field] not in allowed_values:
                    errors.append(f"{field} 值 {data[field]} 不在允许范围内")
            
            elif rule_type == 'not_empty':
                # 非空检查
                field = rule_config.get('field')
                
                if field in data:
                    value = data[field]
                    if isinstance(value, (list, dict)) and len(value) == 0:
                        warnings.append(f"{field} 为空")
                    elif isinstance(value, str) and not value.strip():
                        warnings.append(f"{field} 为空字符串")
        
        return errors, warnings
    
    def _check_integrity(self, data: Dict[str, Any], source: str) -> List[str]:
        """
        检查数据完整性
        
        Args:
            data: 数据
            source: 数据源名称
            
        Returns:
            错误信息列表
        """
        errors = []
        
        # 检查数据结构
        if 'data' in data:
            data_content = data['data']
            
            # 检查是否为空对象
            if isinstance(data_content, dict) and len(data_content) == 0:
                errors.append("data字段为空对象")
            
            # 检查数组字段
            if isinstance(data_content, dict):
                for key, value in data_content.items():
                    if isinstance(value, list) and len(value) == 0:
                        errors.append(f"data.{key} 为空数组")
        
        # 检查元数据
        if 'metadata' in data:
            metadata = data['metadata']
            
            # 检查必要元数据字段
            required_metadata = ['source', 'collected_at', 'version']
            for field in required_metadata:
                if field not in metadata:
                    errors.append(f"metadata缺少{field}字段")
            
            # 检查quality_score范围
            if 'quality_score' in metadata:
                score = metadata['quality_score']
                if not isinstance(score, (int, float)) or score < 0 or score > 1:
                    errors.append(f"metadata.quality_score值无效: {score}")
        
        return errors
    
    def add_schema(self, source: str, schema: Dict[str, Any]):
        """
        添加Schema
        
        Args:
            source: 数据源名称
            schema: JSON Schema
        """
        self.schemas[source] = schema
        self.logger.info(f"添加Schema: {source}")
    
    def get_schema(self, source: str) -> Optional[Dict[str, Any]]:
        """
        获取Schema
        
        Args:
            source: 数据源名称
            
        Returns:
            JSON Schema
        """
        return self.schemas.get(source)
    
    def list_schemas(self) -> List[str]:
        """
        列出所有Schema
        
        Returns:
            数据源名称列表
        """
        return list(self.schemas.keys())