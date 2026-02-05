"""
性能监控和分析模块
跟踪Agent执行的性能指标
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class StepMetrics:
    """单步执行的性能指标"""
    step_number: int
    start_time: float
    end_time: Optional[float] = None
    status: str = "running"  # running, success, failed
    error_type: Optional[str] = None
    duration: float = 0.0
    action_count: int = 0
    
    def finish(self, status: str, error_type: Optional[str] = None):
        """完成步骤测量"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.status = status
        self.error_type = error_type


@dataclass
class TaskMetrics:
    """任务的性能指标"""
    task_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_steps: int = 0
    successful_steps: int = 0
    failed_steps: int = 0
    total_duration: float = 0.0
    step_metrics: List[StepMetrics] = field(default_factory=list)
    success: bool = False
    error_summary: Optional[str] = None
    
    def add_step(self, step: StepMetrics):
        """添加步骤指标"""
        self.step_metrics.append(step)
        self.total_steps += 1
        if step.status == "success":
            self.successful_steps += 1
        elif step.status == "failed":
            self.failed_steps += 1
    
    def finish(self, success: bool, error_summary: Optional[str] = None):
        """完成任务测量"""
        self.end_time = datetime.now()
        self.total_duration = (self.end_time - self.start_time).total_seconds()
        self.success = success
        self.error_summary = error_summary
    
    def get_average_step_time(self) -> float:
        """获取平均步骤时间"""
        if not self.step_metrics:
            return 0.0
        return sum(s.duration for s in self.step_metrics) / len(self.step_metrics)
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_steps == 0:
            return 0.0
        return (self.successful_steps / self.total_steps) * 100


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.current_task: Optional[TaskMetrics] = None
        self.completed_tasks: List[TaskMetrics] = []
    
    def start_task(self, task_id: str) -> TaskMetrics:
        """开始任务监控"""
        self.current_task = TaskMetrics(task_id=task_id, start_time=datetime.now())
        logger.info(f"📊 开始任务性能监控: {task_id}")
        return self.current_task
    
    def start_step(self, step_number: int) -> StepMetrics:
        """开始步骤监控"""
        if self.current_task is None:
            raise RuntimeError("没有正在进行的任务")
        
        step_metrics = StepMetrics(step_number=step_number, start_time=time.time())
        return step_metrics
    
    def finish_step(self, step_metrics: StepMetrics, status: str, error_type: Optional[str] = None):
        """完成步骤监控"""
        if self.current_task is None:
            raise RuntimeError("没有正在进行的任务")
        
        step_metrics.finish(status, error_type)
        self.current_task.add_step(step_metrics)
        
        if status == "success":
            logger.info(f"  ✅ 步骤 {step_metrics.step_number} 完成 ({step_metrics.duration:.2f}s)")
        else:
            logger.warning(f"  ⚠️ 步骤 {step_metrics.step_number} 失败 ({step_metrics.duration:.2f}s) - {error_type}")
    
    def finish_task(self, success: bool, error_summary: Optional[str] = None):
        """完成任务监控"""
        if self.current_task is None:
            raise RuntimeError("没有正在进行的任务")
        
        self.current_task.finish(success, error_summary)
        self.completed_tasks.append(self.current_task)
        
        # 生成性能报告
        self._log_task_report(self.current_task)
        
        self.current_task = None
    
    def _log_task_report(self, task: TaskMetrics):
        """生成并输出任务性能报告"""
        logger.info("\n" + "=" * 60)
        logger.info(f"📊 任务性能报告: {task.task_id}")
        logger.info("=" * 60)
        logger.info(f"任务状态: {'✅ 成功' if task.success else '❌ 失败'}")
        logger.info(f"总耗时: {task.total_duration:.2f}s")
        logger.info(f"步骤统计: {task.successful_steps}✅ / {task.failed_steps}❌ (总计: {task.total_steps})")
        logger.info(f"成功率: {task.get_success_rate():.1f}%")
        logger.info(f"平均步骤时间: {task.get_average_step_time():.2f}s")
        
        # 最慢的步骤
        if task.step_metrics:
            slowest_step = max(task.step_metrics, key=lambda s: s.duration)
            logger.info(f"最慢步骤: 步骤 {slowest_step.step_number} ({slowest_step.duration:.2f}s)")
        
        if task.error_summary:
            logger.info(f"错误摘要: {task.error_summary}")
        
        logger.info("=" * 60 + "\n")
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if not self.completed_tasks:
            return {}
        
        total_tasks = len(self.completed_tasks)
        successful_tasks = sum(1 for t in self.completed_tasks if t.success)
        total_steps = sum(t.total_steps for t in self.completed_tasks)
        total_duration = sum(t.total_duration for t in self.completed_tasks)
        
        return {
            'total_tasks': total_tasks,
            'successful_tasks': successful_tasks,
            'success_rate': (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'total_steps': total_steps,
            'total_duration': total_duration,
            'average_task_duration': total_duration / total_tasks if total_tasks > 0 else 0,
        }


# 全局性能监控实例
_global_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控实例"""
    return _global_monitor
