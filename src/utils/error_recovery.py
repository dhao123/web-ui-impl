"""
错误恢复策略模块
实现各种错误恢复策略
"""

import logging
from typing import Optional, Dict, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = 1        # 低：可以继续
    MEDIUM = 2     # 中：需要重试
    HIGH = 3       # 高：需要恢复
    CRITICAL = 4   # 严重：无法恢复


class ErrorRecoveryStrategy:
    """错误恢复策略"""
    
    # 常见错误及其严重程度
    ERROR_SEVERITY = {
        'timeout': ErrorSeverity.MEDIUM,
        'connection': ErrorSeverity.MEDIUM,
        'network': ErrorSeverity.MEDIUM,
        'loading': ErrorSeverity.MEDIUM,
        'element not found': ErrorSeverity.HIGH,
        'permission denied': ErrorSeverity.HIGH,
        'invalid url': ErrorSeverity.HIGH,
        'crash': ErrorSeverity.CRITICAL,
        'out of memory': ErrorSeverity.CRITICAL,
    }
    
    def __init__(self):
        self.recovery_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认的恢复处理器"""
        self.register_handler('timeout', self._recover_timeout)
        self.register_handler('connection', self._recover_connection)
        self.register_handler('element_not_found', self._recover_element_not_found)
    
    def register_handler(self, error_type: str, handler: Callable):
        """注册错误处理器"""
        self.recovery_handlers[error_type] = handler
        logger.info(f"🔧 注册错误处理器: {error_type}")
    
    def get_error_severity(self, error_msg: str) -> ErrorSeverity:
        """判断错误严重程度"""
        error_lower = error_msg.lower()
        
        for error_type, severity in self.ERROR_SEVERITY.items():
            if error_type in error_lower:
                return severity
        
        return ErrorSeverity.MEDIUM  # 默认为中等
    
    async def execute_recovery(self, error_msg: str, context: Optional[Dict] = None) -> bool:
        """执行错误恢复"""
        severity = self.get_error_severity(error_msg)
        logger.info(f"🔄 执行错误恢复: {error_msg} (严重程度: {severity.name})")
        
        # 根据错误类型查找处理器
        for error_type, handler in self.recovery_handlers.items():
            if error_type in error_msg.lower():
                try:
                    result = await handler(error_msg, context)
                    if result:
                        logger.info(f"✅ 错误恢复成功: {error_type}")
                    else:
                        logger.warning(f"⚠️ 错误恢复失败: {error_type}")
                    return result
                except Exception as e:
                    logger.error(f"❌ 错误恢复异常: {e}")
                    return False
        
        logger.warning(f"⚠️ 找不到处理器，无法恢复: {error_msg}")
        return False
    
    # 具体的恢复策略
    
    async def _recover_timeout(self, error_msg: str, context: Optional[Dict] = None) -> bool:
        """恢复超时错误"""
        logger.info("💡 尝试恢复超时错误: 重新加载页面")
        # 在实际应用中，这里会调用浏览器的重新加载功能
        return True
    
    async def _recover_connection(self, error_msg: str, context: Optional[Dict] = None) -> bool:
        """恢复连接错误"""
        logger.info("💡 尝试恢复连接错误: 重新建立连接")
        return True
    
    async def _recover_element_not_found(self, error_msg: str, context: Optional[Dict] = None) -> bool:
        """恢复元素未找到错误"""
        logger.info("💡 尝试恢复元素未找到: 刷新页面重新定位")
        return True
    
    def should_give_up(self, error_msg: str, retry_count: int, max_retries: int) -> bool:
        """判断是否应该放弃重试"""
        severity = self.get_error_severity(error_msg)
        
        # 严重错误不应该继续重试
        if severity == ErrorSeverity.CRITICAL:
            logger.error(f"❌ 严重错误，放弃重试: {error_msg}")
            return True
        
        # 高严重程度错误，超过一定次数后放弃
        if severity == ErrorSeverity.HIGH and retry_count >= max_retries:
            logger.error(f"❌ 高严重程度错误，已达到重试上限: {error_msg}")
            return True
        
        return False


class AdaptiveErrorRecovery:
    """自适应错误恢复"""
    
    def __init__(self):
        self.strategy = ErrorRecoveryStrategy()
        self.error_patterns: Dict[str, int] = {}  # 错误模式计数
    
    def learn_error_pattern(self, error_msg: str):
        """学习错误模式"""
        error_type = error_msg.split(':')[0].strip().lower()
        self.error_patterns[error_type] = self.error_patterns.get(error_type, 0) + 1
    
    def get_most_common_errors(self, top_n: int = 5) -> list:
        """获取最常见的错误"""
        sorted_errors = sorted(
            self.error_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_errors[:top_n]
    
    def suggest_improvements(self) -> str:
        """建议改进方案"""
        common_errors = self.get_most_common_errors()
        
        if not common_errors:
            return "未发现任何错误模式"
        
        suggestions = "🎯 基于错误模式的改进建议:\n"
        for error_type, count in common_errors:
            suggestions += f"  - {error_type} ({count}次):\n"
            
            if 'timeout' in error_type:
                suggestions += "    → 增加超时时间\n"
                suggestions += "    → 改进页面加载检测\n"
            elif 'connection' in error_type:
                suggestions += "    → 检查网络连接\n"
                suggestions += "    → 添加重试机制\n"
            elif 'element' in error_type:
                suggestions += "    → 改进元素定位策略\n"
                suggestions += "    → 添加等待机制\n"
        
        return suggestions


# 全局错误恢复实例
_recovery_strategy = ErrorRecoveryStrategy()
_adaptive_recovery = AdaptiveErrorRecovery()


def get_recovery_strategy() -> ErrorRecoveryStrategy:
    """获取全局错误恢复策略"""
    return _recovery_strategy


def get_adaptive_recovery() -> AdaptiveErrorRecovery:
    """获取全局自适应错误恢复"""
    return _adaptive_recovery
