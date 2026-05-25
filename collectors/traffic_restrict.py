"""
限行信息数据采集器
采集各城市机动车限行规定
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base import BaseCollector, CollectorResult, CollectorStatus
from .registry import CollectorRegistry


@CollectorRegistry.register("traffic-restrict")
class TrafficRestrictCollector(BaseCollector):
    """
    限行信息数据采集器
    
    采集各城市机动车限行规定，包括限行时间、区域、规则等
    """
    
    # 默认配置
    DEFAULT_CONFIG = {
        "name": "限行信息",
        "url": "https://api.example.com/traffic-restrict",
        "timeout": 45,
        "retries": 2,
        "headers": {},
        "params": {
            "cities": "北京,上海,广州,深圳"
        }
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化限行采集器
        
        Args:
            config: 配置字典
        """
        final_config = {**self.DEFAULT_CONFIG, **(config or {})}
        super().__init__(final_config)
    
    def collect(self) -> CollectorResult:
        """
        执行限行数据采集
        
        Returns:
            CollectorResult: 采集结果
        """
        self.logger.info("开始采集限行信息")
        
        try:
            # 获取原始数据
            raw_data = self._fetch_raw_data()
            
            # 转换数据格式
            transformed_data = self.transform(raw_data)
            
            return CollectorResult(
                source=self.name,
                status=CollectorStatus.SUCCESS,
                data=transformed_data,
                metadata=self._create_metadata(transformed_data)
            )
            
        except Exception as e:
            self.logger.error(f"采集限行信息失败: {e}")
            return CollectorResult(
                source=self.name,
                status=CollectorStatus.ERROR,
                error=str(e)
            )
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        验证限行数据
        
        Args:
            data: 限行数据
            
        Returns:
            bool: 数据是否有效
        """
        try:
            # 检查必要字段
            if "data" not in data:
                self.logger.error("缺少data字段")
                return False
            
            data_content = data["data"]
            
            # 检查update_time
            if "update_time" not in data_content:
                self.logger.error("缺少update_time字段")
                return False
            
            # 检查restrictions数组
            if "restrictions" not in data_content:
                self.logger.error("缺少restrictions字段")
                return False
            
            restrictions = data_content["restrictions"]
            
            if not isinstance(restrictions, list):
                self.logger.error("restrictions字段不是数组")
                return False
            
            # 验证每个限行项
            for i, restriction in enumerate(restrictions):
                if not isinstance(restriction, dict):
                    self.logger.error(f"restrictions[{i}]不是对象")
                    return False
                
                # 检查必要字段
                required_fields = ["city", "rule", "time_range"]
                for field in required_fields:
                    if field not in restriction:
                        self.logger.error(f"restrictions[{i}]缺少{field}字段")
                        return False
            
            self.logger.info("限行数据验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"验证限行数据时发生异常: {e}")
            return False
    
    def transform(self, raw_data: Any) -> Dict[str, Any]:
        """
        转换原始限行数据为标准格式
        
        Args:
            raw_data: 原始数据
            
        Returns:
            Dict[str, Any]: 标准格式的限行数据
        """
        if isinstance(raw_data, dict):
            return self._transform_dict(raw_data)
        
        if isinstance(raw_data, str):
            try:
                data = json.loads(raw_data)
                return self._transform_dict(data)
            except json.JSONDecodeError:
                raise ValueError("无法解析JSON数据")
        
        raise ValueError(f"不支持的数据类型: {type(raw_data)}")
    
    def _fetch_raw_data(self) -> Any:
        """
        获取原始限行数据
        
        Returns:
            原始数据
        """
        # 示例：返回模拟数据
        return {
            "update_time": datetime.now(timezone.utc).isoformat(),
            "restrictions": [
                {
                    "city": "北京",
                    "rule": "工作日早晚高峰时段限行，按车牌尾号轮换",
                    "time_range": "工作日7:00-9:00，17:00-20:00",
                    "area": "五环路以内（不含五环）",
                    "exceptions": ["新能源汽车", "出租车", "公交车"],
                    "effective_date": "2026-01-01",
                    "end_date": "2026-12-31"
                },
                {
                    "city": "上海",
                    "rule": "外牌高架限行，内环地面限行",
                    "time_range": "工作日7:00-20:00",
                    "area": "高架道路、内环地面道路",
                    "exceptions": ["新能源汽车", "沪牌车辆"],
                    "effective_date": "2026-01-01",
                    "end_date": "2026-12-31"
                },
                {
                    "city": "广州",
                    "rule": "开四停四政策",
                    "time_range": "全天",
                    "area": "管控区域内",
                    "exceptions": ["广州牌照车辆", "新能源汽车"],
                    "effective_date": "2026-01-01",
                    "end_date": "2026-12-31"
                },
                {
                    "city": "深圳",
                    "rule": "外地车限行",
                    "time_range": "工作日7:00-9:00，17:30-19:30",
                    "area": "全市范围",
                    "exceptions": ["深圳牌照车辆", "新能源汽车"],
                    "effective_date": "2026-01-01",
                    "end_date": "2026-12-31"
                }
            ]
        }
    
    def _transform_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换字典格式的限行数据
        
        Args:
            data: 原始字典数据
            
        Returns:
            标准格式数据
        """
        restrictions = data.get("restrictions", [])
        
        # 标准化限行数据
        standardized_restrictions = []
        for restriction in restrictions:
            standardized_restriction = {
                "city": restriction.get("city", "未知"),
                "rule": restriction.get("rule", ""),
                "time_range": restriction.get("time_range", ""),
                "area": restriction.get("area", ""),
                "exceptions": restriction.get("exceptions", []),
                "effective_date": restriction.get("effective_date", ""),
                "end_date": restriction.get("end_date", "")
            }
            standardized_restrictions.append(standardized_restriction)
        
        return {
            "update_time": data.get("update_time", datetime.now(timezone.utc).isoformat()),
            "restrictions": standardized_restrictions
        }
    
    def _create_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建元数据
        
        Args:
            data: 数据
            
        Returns:
            元数据
        """
        restrictions = data.get("restrictions", [])
        
        return {
            "source": self.name,
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "version": datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
            "quality_score": self._calculate_quality_score(data),
            "fields_count": len(data.keys()),
            "records_count": len(restrictions)
        }
    
    def _calculate_quality_score(self, data: Dict[str, Any]) -> float:
        """
        计算数据质量评分
        
        Args:
            data: 数据
            
        Returns:
            质量评分（0-1）
        """
        score = 1.0
        
        # 检查必要字段
        required_fields = ["update_time", "restrictions"]
        for field in required_fields:
            if field not in data:
                score -= 0.2
        
        # 检查限行数据完整性
        restrictions = data.get("restrictions", [])
        if not restrictions:
            score -= 0.3
        else:
            # 检查每个限行项的完整性
            for restriction in restrictions:
                if "city" not in restriction:
                    score -= 0.05
                if "rule" not in restriction:
                    score -= 0.05
                if "time_range" not in restriction:
                    score -= 0.02
        
        return max(0.0, min(1.0, score))