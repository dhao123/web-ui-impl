"""
执行历史持久化模块
保存和恢复Agent执行的历史记录
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ExecutionHistoryManager:
    """执行历史管理器"""
    
    def __init__(self, history_dir: str = "./tmp/execution_history"):
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    def save_execution(self, task_id: str, execution_data: Dict) -> str:
        """保存执行记录"""
        execution_data['timestamp'] = datetime.now().isoformat()
        execution_data['task_id'] = task_id
        
        # 创建文件路径
        file_path = self.history_dir / f"{task_id}.json"
        
        # 保存为JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(execution_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 执行历史已保存: {file_path}")
        return str(file_path)
    
    def load_execution(self, task_id: str) -> Optional[Dict]:
        """加载执行记录"""
        file_path = self.history_dir / f"{task_id}.json"
        
        if not file_path.exists():
            logger.warning(f"❌ 找不到执行历史: {task_id}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"📂 执行历史已加载: {file_path}")
            return data
        except Exception as e:
            logger.error(f"❌ 加载执行历史失败: {e}")
            return None
    
    def list_executions(self) -> List[Dict]:
        """列出所有执行记录"""
        executions = []
        for file_path in self.history_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                executions.append({
                    'task_id': data.get('task_id'),
                    'timestamp': data.get('timestamp'),
                    'success': data.get('success'),
                    'file_path': str(file_path)
                })
            except Exception as e:
                logger.warning(f"⚠️ 无法读取 {file_path}: {e}")
        
        # 按时间戳排序（最新的在前）
        executions.sort(key=lambda x: x['timestamp'], reverse=True)
        return executions
    
    def get_execution_summary(self) -> Dict:
        """获取执行摘要"""
        executions = self.list_executions()
        
        if not executions:
            return {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'success_rate': 0.0,
            }
        
        successful = sum(1 for e in executions if e['success'])
        total = len(executions)
        
        return {
            'total_executions': total,
            'successful_executions': successful,
            'failed_executions': total - successful,
            'success_rate': (successful / total * 100) if total > 0 else 0.0,
            'latest_execution': executions[0] if executions else None,
        }
    
    def delete_execution(self, task_id: str) -> bool:
        """删除执行记录"""
        file_path = self.history_dir / f"{task_id}.json"
        
        if file_path.exists():
            file_path.unlink()
            logger.info(f"🗑️ 执行历史已删除: {task_id}")
            return True
        
        return False
    
    def export_executions(self, export_path: str) -> bool:
        """导出所有执行记录"""
        try:
            executions = self.list_executions()
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(executions, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📤 执行历史已导出: {export_file}")
            return True
        except Exception as e:
            logger.error(f"❌ 导出执行历史失败: {e}")
            return False


# 全局执行历史管理实例
_history_manager = ExecutionHistoryManager()


def get_history_manager() -> ExecutionHistoryManager:
    """获取全局执行历史管理器"""
    return _history_manager
