"""
数据处理管线
串联清洗、校验、转换等处理步骤
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from .cleaner import DataCleaner
from .validator import DataValidator
from .quality import QualityScorer


class PipelineStage(Enum):
    """管线阶段枚举"""
    COLLECTED = "collected"
    CLEANED = "cleaned"
    VALIDATED = "validated"
    SCORED = "scored"
    OUTPUTTED = "outputted"
    FAILED = "failed"


@dataclass
class PipelineResult:
    """管线处理结果"""
    source: str
    stage: PipelineStage
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "source": self.source,
            "stage": self.stage.value,
            "data": self.data,
            "metadata": self.metadata,
            "error": self.error,
            "processing_time": self.processing_time
        }


class DataPipeline:
    """
    数据处理管线
    
    负责串联数据清洗、校验、转换等处理步骤
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化数据处理管线
        
        Args:
            config: 管线配置
        """
        self.config = config or {}
        self.logger = logging.getLogger("pipeline")
        
        # 初始化处理组件
        self.cleaner = DataCleaner(self.config.get('cleaner', {}))
        self.validator = DataValidator(self.config.get('validator', {}))
        self.quality_scorer = QualityScorer(self.config.get('quality', {}))
        
        # 管线阶段处理器
        self.stage_processors: Dict[PipelineStage, Callable] = {
            PipelineStage.COLLECTED: self._process_collected,
            PipelineStage.CLEANED: self._process_cleaned,
            PipelineStage.VALIDATED: self._process_validated,
            PipelineStage.SCORED: self._process_scored,
        }
    
    def process(self, data: Dict[str, Any], source: str) -> PipelineResult:
        """
        处理数据
        
        Args:
            data: 原始数据
            source: 数据源名称
            
        Returns:
            PipelineResult: 处理结果
        """
        import time
        start_time = time.time()
        
        self.logger.info(f"开始处理数据: {source}")
        
        try:
            # 阶段1: 数据清洗
            self.logger.info("阶段1: 数据清洗")
            cleaned_data = self.cleaner.clean(data)
            
            # 阶段2: 数据校验
            self.logger.info("阶段2: 数据校验")
            validation_result = self.validator.validate(cleaned_data, source)
            
            if not validation_result.is_valid:
                self.logger.error(f"数据校验失败: {validation_result.errors}")
                return PipelineResult(
                    source=source,
                    stage=PipelineStage.FAILED,
                    error=f"数据校验失败: {validation_result.errors}",
                    processing_time=time.time() - start_time
                )
            
            # 阶段3: 质量评分
            self.logger.info("阶段3: 质量评分")
            quality_score = self.quality_scorer.score(cleaned_data, source)
            
            # 检查质量阈值
            quality_threshold = self.config.get('quality_threshold', 0.8)
            if quality_score < quality_threshold:
                self.logger.warning(f"数据质量评分 {quality_score} 低于阈值 {quality_threshold}")
                return PipelineResult(
                    source=source,
                    stage=PipelineStage.FAILED,
                    error=f"数据质量评分 {quality_score} 低于阈值 {quality_threshold}",
                    processing_time=time.time() - start_time
                )
            
            # 阶段4: 生成最终数据
            self.logger.info("阶段4: 生成最终数据")
            final_data = self._generate_final_data(cleaned_data, source, quality_score)
            
            processing_time = time.time() - start_time
            
            self.logger.info(f"数据处理完成，耗时: {processing_time:.2f}秒")
            
            return PipelineResult(
                source=source,
                stage=PipelineStage.OUTPUTTED,
                data=final_data,
                metadata=final_data.get('metadata', {}),
                processing_time=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"数据处理异常: {e}")
            return PipelineResult(
                source=source,
                stage=PipelineStage.FAILED,
                error=str(e),
                processing_time=time.time() - start_time
            )
    
    def _process_collected(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理采集阶段数据"""
        return data
    
    def _process_cleaned(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理清洗阶段数据"""
        return self.cleaner.clean(data)
    
    def _process_validated(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理校验阶段数据"""
        validation_result = self.validator.validate(data)
        if not validation_result.is_valid:
            raise ValueError(f"数据校验失败: {validation_result.errors}")
        return data
    
    def _process_scored(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理评分阶段数据"""
        quality_score = self.quality_scorer.score(data)
        data['metadata'] = data.get('metadata', {})
        data['metadata']['quality_score'] = quality_score
        return data
    
    def _generate_final_data(self, data: Dict[str, Any], source: str, quality_score: float) -> Dict[str, Any]:
        """
        生成最终数据格式
        
        Args:
            data: 处理后的数据
            source: 数据源名称
            quality_score: 质量评分
            
        Returns:
            最终格式的数据
        """
        # 获取数据内容
        data_content = data.get('data', data)
        
        # 计算字段数量和记录数量
        fields_count = len(data_content.keys())
        
        # 计算记录数量（假设数据在数组字段中）
        records_count = 0
        for key, value in data_content.items():
            if isinstance(value, list):
                records_count = max(records_count, len(value))
        
        # 生成元数据
        metadata = {
            "source": source,
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "version": datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
            "quality_score": quality_score,
            "fields_count": fields_count,
            "records_count": records_count
        }
        
        # 构建最终数据结构
        final_data = {
            "status": "success",
            "data": data_content,
            "metadata": metadata
        }
        
        return final_data
    
    def batch_process(self, data_list: List[Dict[str, Any]], sources: List[str]) -> List[PipelineResult]:
        """
        批量处理数据
        
        Args:
            data_list: 数据列表
            sources: 数据源名称列表
            
        Returns:
            处理结果列表
        """
        results = []
        
        for data, source in zip(data_list, sources):
            result = self.process(data, source)
            results.append(result)
        
        return results
    
    def get_processing_stats(self, results: List[PipelineResult]) -> Dict[str, Any]:
        """
        获取处理统计信息
        
        Args:
            results: 处理结果列表
            
        Returns:
            统计信息
        """
        total = len(results)
        success = sum(1 for r in results if r.stage == PipelineStage.OUTPUTTED)
        failed = sum(1 for r in results if r.stage == PipelineStage.FAILED)
        
        avg_processing_time = 0
        if results:
            processing_times = [r.processing_time for r in results if r.processing_time]
            if processing_times:
                avg_processing_time = sum(processing_times) / len(processing_times)
        
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": success / total if total > 0 else 0,
            "average_processing_time": avg_processing_time
        }