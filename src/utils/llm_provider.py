from openai import OpenAI
import pdb
from langchain_openai import ChatOpenAI
from langchain_core.globals import get_llm_cache
from langchain_core.language_models.base import (
    BaseLanguageModel,
    LangSmithParams,
    LanguageModelInput,
)
import os
from langchain_core.load import dumpd, dumps
from langchain_core.messages import (
    AIMessage,
    SystemMessage,
    AnyMessage,
    BaseMessage,
    BaseMessageChunk,
    HumanMessage,
    convert_to_messages,
    message_chunk_to_message,
)
from langchain_core.outputs import (
    ChatGeneration,
    ChatGenerationChunk,
    ChatResult,
    LLMResult,
    RunInfo,
)
from langchain_ollama import ChatOllama
from langchain_core.output_parsers.base import OutputParserLike
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.tools import BaseTool

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Literal,
    Optional,
    Union,
    cast, List,
)
from contextlib import contextmanager
from langchain_anthropic import ChatAnthropic
from langchain_mistralai import ChatMistralAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_ibm import ChatWatsonx
from langchain_aws import ChatBedrock
from pydantic import SecretStr

from src.utils import config


class DeepSeekR1ChatOpenAI(ChatOpenAI):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.client = OpenAI(
            base_url=kwargs.get("base_url"),
            api_key=kwargs.get("api_key")
        )

    async def ainvoke(
            self,
            input: LanguageModelInput,
            config: Optional[RunnableConfig] = None,
            *,
            stop: Optional[list[str]] = None,
            **kwargs: Any,
    ) -> AIMessage:
        message_history = []
        for input_ in input:
            if isinstance(input_, SystemMessage):
                message_history.append({"role": "system", "content": input_.content})
            elif isinstance(input_, AIMessage):
                message_history.append({"role": "assistant", "content": input_.content})
            else:
                message_history.append({"role": "user", "content": input_.content})

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=message_history
        )

        reasoning_content = response.choices[0].message.reasoning_content
        content = response.choices[0].message.content
        return AIMessage(content=content, reasoning_content=reasoning_content)

    def invoke(
            self,
            input: LanguageModelInput,
            config: Optional[RunnableConfig] = None,
            *,
            stop: Optional[list[str]] = None,
            **kwargs: Any,
    ) -> AIMessage:
        message_history = []
        for input_ in input:
            if isinstance(input_, SystemMessage):
                message_history.append({"role": "system", "content": input_.content})
            elif isinstance(input_, AIMessage):
                message_history.append({"role": "assistant", "content": input_.content})
            else:
                message_history.append({"role": "user", "content": input_.content})

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=message_history
        )

        reasoning_content = response.choices[0].message.reasoning_content
        content = response.choices[0].message.content
        return AIMessage(content=content, reasoning_content=reasoning_content)


class ZKHChatOpenAI(ChatOpenAI):
    """
    震坤行(ZKH) AI API 的自定义ChatOpenAI包装类
    处理ZKH特定的API请求格式和认证
    完整支持 Tool Calling (Function Calling) 
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # 使用自定义的OpenAI客户端处理ZKH API
        api_key = kwargs.get("api_key")
        base_url = kwargs.get("base_url")

        # 存储ZKH专用值，但不要持久修改进程环境。
        # 在每次实际发送请求时会临时设置并恢复环境变量。
        self._zkh_base_url = base_url
        self._zkh_api_key = api_key

        # 创建 OpenAI 客户端（传入 base_url/api_key 以尽量保证使用指定端点）
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[ZKHChatOpenAI] 已初始化，BaseURL: {base_url}")

    @contextmanager
    def _temporary_env(self, overrides: dict):
        """Temporarily set environment variables from `overrides` and restore after use."""
        import os
        saved = {}
        for k, v in overrides.items():
            saved[k] = os.environ.get(k)
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        try:
            yield
        finally:
            for k, prev in saved.items():
                if prev is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = prev

    def _build_api_kwargs(self, message_history: list, **kwargs: Any) -> dict:
        """
        构建API请求参数，处理tools和消息格式
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # ✅ 基础参数
        api_kwargs = {
            "model": self.model_name,
            "messages": message_history,
            "temperature": self.temperature,
        }
        
        # ✅ 处理 tools 参数（关键修复！）
        if "tools" in kwargs and kwargs["tools"]:
            tools = kwargs["tools"]
            
            # ✅ 转换 LangChain 工具为 OpenAI 格式
            converted_tools = self._convert_tools_to_openai_format(tools)
            
            if converted_tools:
                # 诊断tools参数
                import json
                try:
                    tools_json_str = json.dumps(converted_tools, ensure_ascii=False)
                    tools_size = len(tools_json_str.encode('utf-8'))
                    logger.info(f"[ZKHChatOpenAI] Tools参数大小: {tools_size} bytes, 数量: {len(converted_tools)}")
                except Exception as e:
                    logger.warning(f"[ZKHChatOpenAI] 无法序列化tools用于诊断: {e}")
                
                api_kwargs["tools"] = converted_tools
                logger.info(f"[ZKHChatOpenAI] 传递 {len(converted_tools)} 个有效的tools参数")
            else:
                logger.warning("[ZKHChatOpenAI] Tools列表中没有有效的工具定义，跳过tools参数")
        
        # ✅ 检查消息历史的合理性
        total_chars = sum(len(str(msg.get("content", ""))) for msg in message_history)
        logger.info(f"[ZKHChatOpenAI] 消息历史总字符数: {total_chars}")
        
        return api_kwargs
    
    def _convert_tools_to_openai_format(self, tools: list) -> list:
        """
        将 LangChain 工具转换为 OpenAI 兼容的格式
        处理多种工具对象类型
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if not tools:
            return []
        
        converted_tools = []
        
        for tool in tools:
            try:
                # 情况1: 已经是OpenAI格式的字典
                if isinstance(tool, dict):
                    if 'function' in tool or 'name' in tool:
                        converted_tools.append(tool)
                        continue
                
                # 情况2: LangChain 工具对象 (StructuredTool, BaseTool等)
                # 检查是否有 to_dict 或 lc_kwargs 方法
                if hasattr(tool, 'lc_kwargs'):
                    # LangChain 工具的标准转换方法
                    func_dict = self._langchain_tool_to_dict(tool)
                    if func_dict:
                        openai_tool = {
                            "type": "function",
                            "function": func_dict
                        }
                        converted_tools.append(openai_tool)
                        continue
                
                # 情况3: 尝试提取工具的标准属性
                if hasattr(tool, 'name') and hasattr(tool, 'description'):
                    func_dict = {
                        "name": tool.name,
                        "description": tool.description,
                    }
                    
                    # 添加参数信息（如果有）
                    if hasattr(tool, 'args'):
                        func_dict["parameters"] = tool.args
                    elif hasattr(tool, 'args_schema'):
                        func_dict["parameters"] = self._extract_schema(tool.args_schema)
                    
                    openai_tool = {
                        "type": "function",
                        "function": func_dict
                    }
                    converted_tools.append(openai_tool)
                    continue
                
                logger.warning(f"[ZKHChatOpenAI] 无法转换工具: {type(tool).__name__}")
                
            except Exception as e:
                logger.warning(f"[ZKHChatOpenAI] 转换工具失败 ({type(tool).__name__}): {e}")
        
        return converted_tools
    
    def _langchain_tool_to_dict(self, tool) -> dict:
        """
        将 LangChain 工具转换为字典格式
        """
        try:
            func_dict = {
                "name": tool.name if hasattr(tool, 'name') else str(tool)[:20],
                "description": tool.description if hasattr(tool, 'description') else "",
            }
            
            # 提取参数schema
            if hasattr(tool, 'args_schema') and tool.args_schema:
                func_dict["parameters"] = self._extract_schema(tool.args_schema)
            
            return func_dict
        except Exception as e:
            return None
    
    def _extract_schema(self, schema) -> dict:
        """
        从 Pydantic schema 或其他格式提取参数定义
        """
        try:
            # 如果是 Pydantic schema
            if hasattr(schema, 'model_json_schema'):
                return schema.model_json_schema()
            elif hasattr(schema, 'schema'):
                return schema.schema()
            elif isinstance(schema, dict):
                return schema
            else:
                return {"type": "object", "properties": {}}
        except Exception as e:
            return {"type": "object", "properties": {}}

    async def ainvoke(
            self,
            input: LanguageModelInput,
            config: Optional[RunnableConfig] = None,
            *,
            stop: Optional[list[str]] = None,
            **kwargs: Any,
    ) -> AIMessage:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        
        # 构建消息历史
        message_history = []
        for input_ in input:
            if isinstance(input_, SystemMessage):
                message_history.append({"role": "system", "content": input_.content})
            elif isinstance(input_, AIMessage):
                msg = {"role": "assistant", "content": input_.content}
                # ✅ 处理 tool_calls
                if hasattr(input_, "tool_calls") and input_.tool_calls:
                    msg["tool_calls"] = input_.tool_calls
                message_history.append(msg)
            else:
                message_history.append({"role": "user", "content": input_.content})

        # ✅ 构建 API 调用参数
        api_kwargs = self._build_api_kwargs(message_history, **kwargs)
        
        # 日志输出请求参数（不显示完整的消息体，因为可能太长）
        logger.info(f"[ZKHChatOpenAI] 准备发送API请求:")
        logger.info(f"  - 模型: {api_kwargs.get('model')}")
        logger.info(f"  - 消息数: {len(api_kwargs.get('messages', []))}")
        logger.info(f"  - Tools: {len(api_kwargs.get('tools', []))} 个")
        logger.info(f"  - 温度: {api_kwargs.get('temperature')}")
        
        try:
            # 在调用时临时设置环境变量，避免影响同一进程中其他provider
            env_overrides = {}
            if getattr(self, '_zkh_base_url', None):
                env_overrides['OPENAI_API_BASE'] = self._zkh_base_url
            if getattr(self, '_zkh_api_key', None):
                env_overrides['OPENAI_API_KEY'] = self._zkh_api_key

            if env_overrides:
                with self._temporary_env(env_overrides):
                    response = self.client.chat.completions.create(**api_kwargs)
            else:
                response = self.client.chat.completions.create(**api_kwargs)

            logger.info("[ZKHChatOpenAI] API请求成功")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[ZKHChatOpenAI] LLM请求异常: {error_msg}")
            logger.error(f"[ZKHChatOpenAI] 请求参数总结:")
            logger.error(f"  - 模型: {api_kwargs.get('model')}")
            logger.error(f"  - 消息数: {len(api_kwargs.get('messages', []))}")
            logger.error(f"  - Tools数: {len(api_kwargs.get('tools', []))}")
            logger.debug(f"[ZKHChatOpenAI] Traceback:\n{traceback.format_exc()}")
            raise

        content = response.choices[0].message.content
        # ✅ 提取 tool_calls
        tool_calls = getattr(response.choices[0].message, "tool_calls", None)

        ai_message = AIMessage(content=content)
        if tool_calls:
            ai_message.tool_calls = tool_calls
        
        logger.info(f"[ZKHChatOpenAI] 返回内容长度: {len(content) if content else 0}")
        return ai_message

    def invoke(
            self,
            input: LanguageModelInput,
            config: Optional[RunnableConfig] = None,
            *,
            stop: Optional[list[str]] = None,
            **kwargs: Any,
    ) -> AIMessage:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        
        # 构建消息历史
        message_history = []
        for input_ in input:
            if isinstance(input_, SystemMessage):
                message_history.append({"role": "system", "content": input_.content})
            elif isinstance(input_, AIMessage):
                msg = {"role": "assistant", "content": input_.content}
                # ✅ 处理 tool_calls
                if hasattr(input_, "tool_calls") and input_.tool_calls:
                    msg["tool_calls"] = input_.tool_calls
                message_history.append(msg)
            else:
                message_history.append({"role": "user", "content": input_.content})

        # ✅ 构建 API 调用参数
        api_kwargs = self._build_api_kwargs(message_history, **kwargs)
        
        logger.info(f"[ZKHChatOpenAI] 准备发送API请求 (同步):")
        logger.info(f"  - 模型: {api_kwargs.get('model')}")
        logger.info(f"  - 消息数: {len(api_kwargs.get('messages', []))}")
        logger.info(f"  - Tools: {len(api_kwargs.get('tools', []))} 个")
        
        try:
            env_overrides = {}
            if getattr(self, '_zkh_base_url', None):
                env_overrides['OPENAI_API_BASE'] = self._zkh_base_url
            if getattr(self, '_zkh_api_key', None):
                env_overrides['OPENAI_API_KEY'] = self._zkh_api_key

            if env_overrides:
                with self._temporary_env(env_overrides):
                    response = self.client.chat.completions.create(**api_kwargs)
            else:
                response = self.client.chat.completions.create(**api_kwargs)

            logger.info("[ZKHChatOpenAI] API请求成功 (同步)")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[ZKHChatOpenAI] LLM请求异常 (同步): {error_msg}")
            logger.debug(f"[ZKHChatOpenAI] Traceback:\n{traceback.format_exc()}")
            raise

        content = response.choices[0].message.content
        # ✅ 提取 tool_calls
        tool_calls = getattr(response.choices[0].message, "tool_calls", None)
        
        ai_message = AIMessage(content=content)
        if tool_calls:
            ai_message.tool_calls = tool_calls
        
        return ai_message


class DeepSeekR1ChatOllama(ChatOllama):

    async def ainvoke(
            self,
            input: LanguageModelInput,
            config: Optional[RunnableConfig] = None,
            *,
            stop: Optional[list[str]] = None,
            **kwargs: Any,
    ) -> AIMessage:
        org_ai_message = await super().ainvoke(input=input)
        org_content = org_ai_message.content
        reasoning_content = org_content.split("</think>")[0].replace("<think>", "")
        content = org_content.split("</think>")[1]
        if "**JSON Response:**" in content:
            content = content.split("**JSON Response:**")[-1]
        return AIMessage(content=content, reasoning_content=reasoning_content)

    def invoke(
            self,
            input: LanguageModelInput,
            config: Optional[RunnableConfig] = None,
            *,
            stop: Optional[list[str]] = None,
            **kwargs: Any,
    ) -> AIMessage:
        org_ai_message = super().invoke(input=input)
        org_content = org_ai_message.content
        reasoning_content = org_content.split("</think>")[0].replace("<think>", "")
        content = org_content.split("</think>")[1]
        if "**JSON Response:**" in content:
            content = content.split("**JSON Response:**")[-1]
        return AIMessage(content=content, reasoning_content=reasoning_content)


def get_llm_model(provider: str, **kwargs):
    """
    Get LLM model
    :param provider: LLM provider
    :param kwargs:
    :return:
    """
    if provider not in ["ollama", "bedrock"]:
        env_var = f"{provider.upper()}_API_KEY"
        api_key = kwargs.get("api_key", "") or os.getenv(env_var, "")
        if not api_key:
            provider_display = config.PROVIDER_DISPLAY_NAMES.get(provider, provider.upper())
            error_msg = f"💥 {provider_display} API key not found! 🔑 Please set the `{env_var}` environment variable or provide it in the UI."
            raise ValueError(error_msg)
        kwargs["api_key"] = api_key

    if provider == "anthropic":
        if not kwargs.get("base_url", ""):
            base_url = "https://api.anthropic.com"
        else:
            base_url = kwargs.get("base_url")

        return ChatAnthropic(
            model=kwargs.get("model_name", "claude-3-5-sonnet-20241022"),
            temperature=kwargs.get("temperature", 0.0),
            base_url=base_url,
            api_key=api_key,
        )
    elif provider == 'mistral':
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("MISTRAL_ENDPOINT", "https://api.mistral.ai/v1")
        else:
            base_url = kwargs.get("base_url")
        if not kwargs.get("api_key", ""):
            api_key = os.getenv("MISTRAL_API_KEY", "")
        else:
            api_key = kwargs.get("api_key")

        return ChatMistralAI(
            model=kwargs.get("model_name", "mistral-large-latest"),
            temperature=kwargs.get("temperature", 0.0),
            base_url=base_url,
            api_key=api_key,
        )
    elif provider == "openai":
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("OPENAI_ENDPOINT", "https://api.openai.com/v1")
        else:
            base_url = kwargs.get("base_url")

        return ChatOpenAI(
            model=kwargs.get("model_name", "gpt-4o"),
            temperature=kwargs.get("temperature", 0.0),
            base_url=base_url,
            api_key=api_key,
        )
    elif provider == "grok":
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("GROK_ENDPOINT", "https://api.x.ai/v1")
        else:
            base_url = kwargs.get("base_url")

        return ChatOpenAI(
            model=kwargs.get("model_name", "grok-3"),
            temperature=kwargs.get("temperature", 0.0),
            base_url=base_url,
            api_key=api_key,
        )
    elif provider == "deepseek":
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("DEEPSEEK_ENDPOINT", "")
        else:
            base_url = kwargs.get("base_url")

        if kwargs.get("model_name", "deepseek-chat") == "deepseek-reasoner":
            return DeepSeekR1ChatOpenAI(
                model=kwargs.get("model_name", "deepseek-reasoner"),
                temperature=kwargs.get("temperature", 0.0),
                base_url=base_url,
                api_key=api_key,
            )
        else:
            return ChatOpenAI(
                model=kwargs.get("model_name", "deepseek-chat"),
                temperature=kwargs.get("temperature", 0.0),
                base_url=base_url,
                api_key=api_key,
            )
    elif provider == "google":
        return ChatGoogleGenerativeAI(
            model=kwargs.get("model_name", "gemini-2.0-flash-exp"),
            temperature=kwargs.get("temperature", 0.0),
            api_key=api_key,
        )
    elif provider == "ollama":
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
        else:
            base_url = kwargs.get("base_url")

        if "deepseek-r1" in kwargs.get("model_name", "qwen2.5:7b"):
            return DeepSeekR1ChatOllama(
                model=kwargs.get("model_name", "deepseek-r1:14b"),
                temperature=kwargs.get("temperature", 0.0),
                num_ctx=kwargs.get("num_ctx", 32000),
                base_url=base_url,
            )
        else:
            return ChatOllama(
                model=kwargs.get("model_name", "qwen2.5:7b"),
                temperature=kwargs.get("temperature", 0.0),
                num_ctx=kwargs.get("num_ctx", 32000),
                num_predict=kwargs.get("num_predict", 1024),
                base_url=base_url,
            )
    elif provider == "azure_openai":
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        else:
            base_url = kwargs.get("base_url")
        api_version = kwargs.get("api_version", "") or os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
        return AzureChatOpenAI(
            model=kwargs.get("model_name", "gpt-4o"),
            temperature=kwargs.get("temperature", 0.0),
            api_version=api_version,
            azure_endpoint=base_url,
            api_key=api_key,
        )
    elif provider == "alibaba":
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("ALIBABA_ENDPOINT", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        else:
            base_url = kwargs.get("base_url")

        return ChatOpenAI(
            model=kwargs.get("model_name", "qwen-plus"),
            temperature=kwargs.get("temperature", 0.0),
            base_url=base_url,
            api_key=api_key,
        )
    elif provider == "ibm":
        parameters = {
            "temperature": kwargs.get("temperature", 0.0),
            "max_tokens": kwargs.get("num_ctx", 32000)
        }
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("IBM_ENDPOINT", "https://us-south.ml.cloud.ibm.com")
        else:
            base_url = kwargs.get("base_url")

        return ChatWatsonx(
            model_id=kwargs.get("model_name", "ibm/granite-vision-3.1-2b-preview"),
            url=base_url,
            project_id=os.getenv("IBM_PROJECT_ID"),
            apikey=os.getenv("IBM_API_KEY"),
            params=parameters
        )
    elif provider == "moonshot":
        return ChatOpenAI(
            model=kwargs.get("model_name", "moonshot-v1-32k-vision-preview"),
            temperature=kwargs.get("temperature", 0.0),
            base_url=os.getenv("MOONSHOT_ENDPOINT"),
            api_key=os.getenv("MOONSHOT_API_KEY"),
        )
    elif provider == "unbound":
        return ChatOpenAI(
            model=kwargs.get("model_name", "gpt-4o-mini"),
            temperature=kwargs.get("temperature", 0.0),
            base_url=os.getenv("UNBOUND_ENDPOINT", "https://api.getunbound.ai"),
            api_key=api_key,
        )
    elif provider == "siliconflow":
        if not kwargs.get("api_key", ""):
            api_key = os.getenv("SiliconFLOW_API_KEY", "")
        else:
            api_key = kwargs.get("api_key")
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("SiliconFLOW_ENDPOINT", "")
        else:
            base_url = kwargs.get("base_url")
        return ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model_name=kwargs.get("model_name", "Qwen/QwQ-32B"),
            temperature=kwargs.get("temperature", 0.0),
        )
    elif provider == "modelscope":
        if not kwargs.get("api_key", ""):
            api_key = os.getenv("MODELSCOPE_API_KEY", "")
        else:
            api_key = kwargs.get("api_key")
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("MODELSCOPE_ENDPOINT", "")
        else:
            base_url = kwargs.get("base_url")
        return ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model_name=kwargs.get("model_name", "Qwen/QwQ-32B"),
            temperature=kwargs.get("temperature", 0.0),
            extra_body = {"enable_thinking": False}
        )
    elif provider == "zkh":
        if not kwargs.get("api_key", ""):
            api_key = os.getenv("ZKH_API_KEY", "")
        else:
            api_key = kwargs.get("api_key")
        if not api_key:
            raise ValueError(
                "💥 震坤行API Key未找到！🔑 请设置 `ZKH_API_KEY` 环境变量或在UI中提供。"
            )
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("ZKH_ENDPOINT", "https://ai-dev-gateway.zkh360.com/llm/v1")
        else:
            base_url = kwargs.get("base_url")
        # 不再强制补 /v1，直接用配置
        return ZKHChatOpenAI(
            model=kwargs.get("model_name", "ep_20251217_i18v"),
            temperature=kwargs.get("temperature", 0.0),
            base_url=base_url,
            api_key=api_key,
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")
