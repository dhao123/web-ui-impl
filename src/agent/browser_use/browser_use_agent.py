from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Dict, Optional

# from lmnr.sdk.decorators import observe
from browser_use.agent.gif import create_history_gif
from browser_use.agent.service import Agent, AgentHookFunc
from browser_use.agent.views import (
    ActionResult,
    AgentHistory,
    AgentHistoryList,
    AgentStepInfo,
    ToolCallingMethod,
)
from browser_use.browser.views import BrowserStateHistory
from browser_use.utils import time_execution_async
from dotenv import load_dotenv
from browser_use.agent.message_manager.utils import is_model_without_tool_support

load_dotenv()
logger = logging.getLogger(__name__)

SKIP_LLM_API_KEY_VERIFICATION = (
        os.environ.get("SKIP_LLM_API_KEY_VERIFICATION", "false").lower()[0] in "ty1"
)


@dataclass
class RetryStrategy:
    """智能重试策略配置"""
    enabled: bool = True  # 是否启用重试
    max_retries_per_error: int = 2  # 单个错误的最大重试次数
    retry_delay: float = 1.0  # 重试延迟（秒）
    backoff_factor: float = 1.5  # 指数退避因子
    max_backoff: float = 10.0  # 最大退避时间
    retryable_errors: Optional[Dict[str, int]] = None  # 可重试的错误类型及重试次数
    
    def __post_init__(self):
        if self.retryable_errors is None:
            # 默认的可重试错误类型
            self.retryable_errors = {
                'timeout': 3,
                'connection': 3,
                'network': 3,
                'loading': 2,
                'temporary': 2,
            }
    
    def get_retry_count(self, error_type: str) -> int:
        """获取特定错误的重试次数"""
        # 尝试匹配错误类型
        error_lower = error_type.lower()
        for key, count in self.retryable_errors.items():
            if key in error_lower:
                return count
        # 默认重试次数
        return self.max_retries_per_error
    
    def calculate_backoff(self, retry_count: int) -> float:
        """计算指数退避延迟"""
        delay = self.retry_delay * (self.backoff_factor ** retry_count)
        return min(delay, self.max_backoff)


class BrowserUseAgent(Agent):
    def __init__(self, *args, **kwargs):
        # 兼容 webui 传递 extraction_llm 参数
        self.extraction_llm = kwargs.pop('extraction_llm', None)
        super().__init__(*args, **kwargs)
        # 初始化重试策略
        self.retry_strategy = RetryStrategy()
        self.error_retry_count: Dict[str, int] = {}  # 追踪每个错误的重试次数
    
    def _set_tool_calling_method(self) -> ToolCallingMethod | None:
        tool_calling_method = self.settings.tool_calling_method
        if tool_calling_method == 'auto':
            if is_model_without_tool_support(self.model_name):
                return 'raw'
            elif self.chat_model_library == 'ChatGoogleGenerativeAI':
                return None
            elif self.chat_model_library == 'ChatOpenAI':
                return 'function_calling'
            elif self.chat_model_library == 'AzureChatOpenAI':
                return 'function_calling'
            elif self.chat_model_library == 'ZKHChatOpenAI':
                # ✅ 添加对 ZKHChatOpenAI 的支持
                # ZKH (震坤行) 模型完整支持 function_calling
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f'🔧 ZKH 提供商已自动设置 Tool Calling Method 为 \'function_calling\' 以支持工具调用')
                return 'function_calling'
            else:
                return None
        else:
            return tool_calling_method

    def _generate_failure_summary(self, step_failure_history: list, max_steps: int) -> str:
        """生成失败摘要，帮助诊断问题"""
        if not step_failure_history:
            return "没有记录失败信息"
        
        summary = f"\n失败统计 (总步数: {max_steps})\n"
        summary += f"总失败数: {len(step_failure_history)}\n"
        
        # 统计错误类型
        error_counts = {}
        for failure in step_failure_history:
            error = failure['error']
            error_counts[error] = error_counts.get(error, 0) + 1
        
        summary += f"\n错误类型分布:\n"
        for error, count in sorted(error_counts.items(), key=lambda x: -x[1]):
            summary += f"  - [{count}次] {error}\n"
        
        # 最后几次失败的详细信息
        summary += f"\n最后 {min(3, len(step_failure_history))} 次失败:\n"
        for failure in step_failure_history[-3:]:
            summary += f"  步骤 {failure['step'] + 1}: {failure['error']}\n"
        
        return summary

    def _should_retry(self, error_msg: str, step: int) -> bool:
        """判断是否应该重试"""
        if not self.retry_strategy.enabled:
            return False
        
        # 获取该错误的重试次数限制
        max_retries = self.retry_strategy.get_retry_count(error_msg)
        
        # 获取当前重试次数
        current_retries = self.error_retry_count.get(error_msg, 0)
        
        if current_retries < max_retries:
            self.error_retry_count[error_msg] = current_retries + 1
            backoff_time = self.retry_strategy.calculate_backoff(current_retries)
            logger.info(f"🔄 将在 {backoff_time:.1f} 秒后重试 (重试 {current_retries + 1}/{max_retries})")
            return True
        
        return False
    
    async def _wait_with_backoff(self, retry_count: int):
        """等待指定的退避时间"""
        delay = self.retry_strategy.calculate_backoff(retry_count - 1)
        await asyncio.sleep(delay)
    
    def _validate_action_output(self, step_num: int) -> bool:
        """
        验证LLM生成的action是否有效。
        检测到空或无效的action时进行警告和诊断。
        返回: True 表示action有效，False 表示action无效或为空。
        """
        if not self.state.history or not self.state.history.history:
            return False
        
        last_history = self.state.history.history[-1]
        model_output = last_history.model_output
        
        if not model_output:
            logger.warning(f"⚠️ 步骤 {step_num + 1}: LLM未返回model_output")
            return False
        
        # 检查action是否为空或全为None
        if not model_output.action:
            logger.warning(
                f"⚠️ 步骤 {step_num + 1}: LLM返回的action列表为空\n"
                f"   current_state: {model_output.current_state}\n"
                f"   这可能表示LLM处于不一致状态或Tool Calling失败"
            )
            return False
        
        # 检查action对象是否全为空（所有字段都是None）
        for idx, action in enumerate(model_output.action):
            try:
                # 获取完整的字段信息（包括None值）
                action_full = action.model_dump(exclude_none=False)
                action_cleaned = action.model_dump(exclude_none=True)
                
                # 如果exclude_none后为空，说明所有字段都是None
                if not action_cleaned:
                    logger.warning(
                        f"⚠️ 步骤 {step_num + 1}: action[{idx}]所有字段都为None\n"
                        f"   Action类型: {type(action).__name__}\n"
                        f"   完整字段: {action_full}"
                    )
                    return False
            except Exception as e:
                logger.warning(f"⚠️ 步骤 {step_num + 1}: 无法验证action[{idx}]: {e}")
                return False
        
        return True
    
    def _diagnose_llm_failure(self, step_num: int, error: Exception) -> str:
        """
        诊断LLM API调用失败的原因
        返回诊断信息字符串
        """
        import traceback
        error_msg = str(error)
        error_type = type(error).__name__
        
        diagnosis = f"\n🔍 步骤 {step_num + 1} LLM调用诊断:\n"
        diagnosis += f"   错误类型: {error_type}\n"
        diagnosis += f"   错误信息: {error_msg}\n"
        
        # 根据错误类型给出诊断建议
        if "400" in error_msg:
            diagnosis += f"   ❌ HTTP 400 Bad Request - 请求参数格式错误\n"
            diagnosis += f"   🔧 可能原因:\n"
            diagnosis += f"      1. tools参数格式不兼容\n"
            diagnosis += f"      2. 消息内容过长或包含不支持的字符\n"
            diagnosis += f"      3. API认证信息不正确\n"
            diagnosis += f"      4. ZKH API版本不匹配\n"
            diagnosis += f"   💡 建议: 检查ZKH_API_KEY、ZKH_ENDPOINT配置，或尝试减少系统提示词长度\n"
        elif "401" in error_msg or "unauthorized" in error_msg.lower():
            diagnosis += f"   ❌ 认证失败 - API密钥或授权信息无效\n"
            diagnosis += f"   💡 建议: 检查ZKH_API_KEY环境变量是否正确设置\n"
        elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
            diagnosis += f"   ⏱️ 连接超时或网络错误\n"
            diagnosis += f"   💡 建议: 检查网络连接，稍后重试\n"
        elif "tool" in error_msg.lower():
            diagnosis += f"   ❌ Tool Calling 相关错误\n"
            diagnosis += f"   💡 建议: 检查Tool Calling Method设置，尝试改为'json_mode'或'raw'\n"
        
        # 记录完整traceback用于调试
        diagnosis += f"\n   完整Traceback:\n"
        for line in traceback.format_exc().split('\n'):
            if line:
                diagnosis += f"   {line}\n"
        
        return diagnosis
    
    async def _handle_empty_action_error(self, step_num: int) -> bool:
        """
        处理LLM返回的空action错误。
        尝试添加一个错误消息到历史记录中，并返回是否应该继续。
        返回: True 表示已处理，应该继续下一步; False 表示应该停止
        """
        logger.error(
            f'❌ 步骤 {step_num + 1}: LLM生成的action无效或为空\n'
            f'   可能原因：\n'
            f'   1. LLM工具调用失败\n'
            f'   2. 模型输出格式与期望不符\n'
            f'   3. Tool Calling Method配置不正确\n'
            f'   4. LLM处于不一致状态（思维崩溃）\n'
            f'   建议：检查Agent Settings中的Tool Calling Method设置，尝试改为"json_mode"或"function_calling"'
        )
        
        # 添加错误记录到历史中
        if self.state.history and self.state.history.history and len(self.state.history.history) > 0:
            last_history = self.state.history.history[-1]
            if last_history.model_output and not last_history.result:
                # 如果还没有result，添加一个错误result
                last_history.result = [
                    ActionResult(
                        error=f"LLM生成的action为空或无效。可能是Tool Calling失败或模型输出格式错误。",
                        include_in_memory=True
                    )
                ]
                logger.info(f"已添加错误记录到步骤 {step_num + 1}")
        
        # 返回True以继续下一步，而不是完全失败
        # 这允许agent在下一步尝试恢复
        return True



    @time_execution_async("--run (agent)")
    async def run(
            self, max_steps: int = 100, on_step_start: AgentHookFunc | None = None,
            on_step_end: AgentHookFunc | None = None
    ) -> AgentHistoryList:
        """Execute the task with maximum number of steps"""

        loop = asyncio.get_event_loop()

        # Set up the Ctrl+C signal handler with callbacks specific to this agent
        from browser_use.utils import SignalHandler

        signal_handler = SignalHandler(
            loop=loop,
            pause_callback=self.pause,
            resume_callback=self.resume,
            custom_exit_callback=None,  # No special cleanup needed on forced exit
            exit_on_second_int=True,
        )
        signal_handler.register()

        # 监控失败模式以检测循环
        step_failure_history = []
        max_consecutive_same_failures = 3  # 如果相同失败出现3次，则停止
        
        try:
            self._log_agent_run()

            # Execute initial actions if provided
            if self.initial_actions:
                result = await self.multi_act(self.initial_actions, check_for_new_elements=False)
                self.state.last_result = result

            for step in range(max_steps):
                # Check if waiting for user input after Ctrl+C
                if self.state.paused:
                    signal_handler.wait_for_resume()
                    signal_handler.reset()

                # Check if we should stop due to too many failures
                if self.state.consecutive_failures >= self.settings.max_failures:
                    logger.error(f'❌ 由于 {self.settings.max_failures} 次连续失败而停止')
                    break

                # Check control flags before each step
                if self.state.stopped:
                    logger.info('✋ Agent 已停止')
                    break

                while self.state.paused:
                    await asyncio.sleep(0.2)  # Small delay to prevent CPU spinning
                    if self.state.stopped:  # Allow stopping while paused
                        break

                if on_step_start is not None:
                    await on_step_start(self)

                step_info = AgentStepInfo(step_number=step, max_steps=max_steps)
                logger.info(f'📍 步骤 {step + 1}/{max_steps} 开始执行')
                
                await self.step(step_info)
                
                # 检查action输出的有效性
                action_valid = self._validate_action_output(step)
                if not action_valid:
                    # 处理空action错误，决定是否继续
                    should_continue = await self._handle_empty_action_error(step)
                    if not should_continue:
                        logger.error(f'中止执行：无法恢复步骤 {step + 1} 的action错误')
                        break

                # 监控步骤执行结果
                if self.state.history and self.state.history.history:
                    last_history = self.state.history.history[-1]
                    if last_history.result and last_history.result[0].error:
                        error_msg = str(last_history.result[0].error)[:100]  # 截断错误信息
                        step_failure_history.append({
                            'step': step,
                            'error': error_msg,
                            'model_output': str(last_history.model_output)[:150] if last_history.model_output else 'None'
                        })
                        logger.warning(f'⚠️ 步骤 {step + 1} 失败: {error_msg}')
                        
                        # 检查是否陷入重复失败循环
                        if len(step_failure_history) >= max_consecutive_same_failures:
                            recent_failures = step_failure_history[-max_consecutive_same_failures:]
                            if all(f['error'] == recent_failures[0]['error'] for f in recent_failures):
                                logger.error(f'🔄 检测到重复失败循环（{max_consecutive_same_failures}次相同错误），自动停止')
                                logger.error(f'   错误类型: {recent_failures[0]["error"]}')
                                break
                    else:
                        logger.info(f'✅ 步骤 {step + 1} 成功完成')

                if on_step_end is not None:
                    await on_step_end(self)

                if self.state.history.is_done():
                    if self.settings.validate_output and step < max_steps - 1:
                        if not await self._validate_output():
                            continue

                    await self.log_completion()
                    logger.info(f'🎉 任务已在步骤 {step + 1} 完成')
                    break
            else:
                error_message = f'超出最大步数限制（{max_steps}步）而未完成任务'
                logger.error(f'❌ {error_message}')
                
                # 生成失败摘要
                failure_summary = self._generate_failure_summary(step_failure_history, max_steps)
                logger.error(f'失败摘要:\n{failure_summary}')

                self.state.history.history.append(
                    AgentHistory(
                        model_output=None,
                        result=[ActionResult(error=error_message, include_in_memory=True)],
                        state=BrowserStateHistory(
                            url='',
                            title='',
                            tabs=[],
                            interacted_element=[],
                            screenshot=None,
                        ),
                        metadata=None,
                    )
                )

            return self.state.history

        except KeyboardInterrupt:
            # Already handled by our signal handler, but catch any direct KeyboardInterrupt as well
            logger.info('Got KeyboardInterrupt during execution, returning current history')
            return self.state.history

        finally:
            # Unregister signal handlers before cleanup
            signal_handler.unregister()

            if self.settings.save_playwright_script_path:
                logger.info(
                    f'Agent run finished. Attempting to save Playwright script to: {self.settings.save_playwright_script_path}'
                )
                try:
                    # Extract sensitive data keys if sensitive_data is provided
                    keys = list(self.sensitive_data.keys()) if self.sensitive_data else None
                    # Pass browser and context config to the saving method
                    self.state.history.save_as_playwright_script(
                        self.settings.save_playwright_script_path,
                        sensitive_data_keys=keys,
                        browser_config=self.browser.config,
                        context_config=self.browser_context.config,
                    )
                except Exception as script_gen_err:
                    # Log any error during script generation/saving
                    logger.error(f'Failed to save Playwright script: {script_gen_err}', exc_info=True)

            await self.close()

            if self.settings.generate_gif:
                output_path: str = 'agent_history.gif'
                if isinstance(self.settings.generate_gif, str):
                    output_path = self.settings.generate_gif

                create_history_gif(task=self.task, history=self.state.history, output_path=output_path)
