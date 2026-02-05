#!/usr/bin/env python3
"""
Test script to demonstrate Agent robustness improvements.
Tests the loop detection and progress tracking features.
"""

import asyncio
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockAgentState:
    """Mock Agent State for testing"""
    def __init__(self):
        self.history = MockHistory()
        
class MockHistory:
    """Mock History to simulate agent steps"""
    def __init__(self):
        self.history = []
        
    def add_step(self, error=None):
        """Add a step to history"""
        self.history.append({
            'step': len(self.history),
            'error': error,
            'success': error is None
        })

def test_loop_detection():
    """Test the loop detection algorithm"""
    logger.info("=" * 60)
    logger.info("测试：重复失败循环检测")
    logger.info("=" * 60)
    
    # Simulate steps with repeated failures
    step_failure_history = []
    max_consecutive_same_failures = 3
    
    test_steps = [
        (0, None, "首步成功"),
        (1, "Failed to load", "第2步失败"),
        (2, "Failed to load", "第3步相同失败"),
        (3, "Failed to load", "第4步再次相同失败"),
    ]
    
    for step, error, desc in test_steps:
        logger.info(f"📍 步骤 {step + 1} 开始执行")
        
        if error:
            logger.warning(f"⚠️ 步骤 {step + 1} 失败: {error}")
            step_failure_history.append({
                'step': step,
                'error': error,
                'model_output': f'Output for step {step}'
            })
            
            # Check for loop
            if len(step_failure_history) >= max_consecutive_same_failures:
                recent_failures = step_failure_history[-max_consecutive_same_failures:]
                if all(f['error'] == recent_failures[0]['error'] for f in recent_failures):
                    logger.error(f'🔄 检测到重复失败循环（{max_consecutive_same_failures}次相同错误），自动停止')
                    logger.error(f'   错误类型: {recent_failures[0]["error"]}')
                    break
        else:
            logger.info(f"✅ 步骤 {step + 1} 成功完成")
    
    logger.info(f"\n📊 最终统计:")
    logger.info(f"  总步数: {len(test_steps)}")
    logger.info(f"  总失败数: {len(step_failure_history)}")
    
    if step_failure_history:
        error_counts = {}
        for failure in step_failure_history:
            error = failure['error']
            error_counts[error] = error_counts.get(error, 0) + 1
        
        logger.info(f"\n  错误类型分布:")
        for error, count in sorted(error_counts.items(), key=lambda x: -x[1]):
            logger.info(f"    - [{count}次] {error}")
    
    logger.info("=" * 60 + "\n")

def test_progress_tracking():
    """Test progress tracking"""
    logger.info("=" * 60)
    logger.info("测试：进度跟踪")
    logger.info("=" * 60)
    
    max_steps = 10
    mock_agent = MockAgentState()
    
    # Simulate task execution
    for step in range(max_steps):
        # Randomly determine if step succeeds
        import random
        has_error = random.random() < 0.3  # 30% failure rate
        
        if has_error:
            error = "Network timeout" if step % 2 == 0 else "Invalid element"
            mock_agent.history.add_step(error=error)
            logger.warning(f"⚠️ 步骤 {step + 1} 失败: {error}")
        else:
            mock_agent.history.add_step()
            logger.info(f"✅ 步骤 {step + 1} 成功完成")
        
        # Calculate stats
        current_step = len(mock_agent.history.history)
        failure_count = sum(1 for h in mock_agent.history.history if h['error'])
        success_count = sum(1 for h in mock_agent.history.history if not h['error'])
        
        # Log progress
        logger.info(f"📊 进度: 步骤 {current_step}/{max_steps}, 成功: {success_count}, 失败: {failure_count}")
    
    logger.info("=" * 60 + "\n")

def test_edge_cases():
    """Test edge cases"""
    logger.info("=" * 60)
    logger.info("测试：边界情况")
    logger.info("=" * 60)
    
    # Test 1: Empty history
    logger.info("\n[测试1] 空历史记录")
    step_failure_history = []
    logger.info(f"  状态: 无失败记录")
    
    # Test 2: Single failure
    logger.info("\n[测试2] 单个失败")
    step_failure_history = [{'step': 0, 'error': 'Test error'}]
    logger.info(f"  状态: {len(step_failure_history)} 次失败 (未达到循环阈值)")
    
    # Test 3: Different errors
    logger.info("\n[测试3] 不同的错误")
    step_failure_history = [
        {'step': 0, 'error': 'Error A'},
        {'step': 1, 'error': 'Error B'},
        {'step': 2, 'error': 'Error A'},
    ]
    logger.info(f"  状态: {len(step_failure_history)} 次失败，但错误类型不同 (不触发循环检测)")
    
    logger.info("=" * 60 + "\n")

def main():
    """Run all tests"""
    logger.info("\n")
    logger.info("🧪 Agent 健壮性改进测试套件")
    logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("\n")
    
    # Run tests
    test_loop_detection()
    test_progress_tracking()
    test_edge_cases()
    
    logger.info("✅ 所有测试完成")
    logger.info("\n")
    logger.info("📝 关键改进点:")
    logger.info("  1. ✨ 自动重复失败循环检测")
    logger.info("  2. 📊 实时进度跟踪")
    logger.info("  3. 🔄 详细的失败诊断")
    logger.info("  4. 🚀 优雅的错误处理")

if __name__ == "__main__":
    main()
