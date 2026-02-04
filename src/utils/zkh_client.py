"""
震坤行(ZKH) AI API 客户端

支持功能：
- 文本对话
- 图像输入（URL和Base64）
- 工具调用（Function Calling）
- 文件上传和处理（Qwen-Long）
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional
import requests
from pathlib import Path

logger = logging.getLogger(__name__)


class ZKHAPIClient:
    """震坤行 API 客户端"""
    
    def __init__(self, api_key: str, base_url: str = "https://ai-dev-gateway.zkh360.com/llm"):
        """
        初始化ZKH客户端
        
        Args:
            api_key: ZKH API密钥
            base_url: API基础URL，默认为https://ai-dev-gateway.zkh360.com/llm
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    def list_models(self) -> Dict[str, Any]:
        """
        获取可用的模型列表
        
        Returns:
            Dict: 模型列表响应
        """
        try:
            response = self.session.get(f"{self.base_url}/v1/models")
            response.raise_for_status()
            data = response.json()
            # 如果 API 返回服务异常，返回备选模型列表
            if isinstance(data, dict) and data.get('code') == 500:
                logger.warning(f"获取模型列表失败: {data.get('message', '服务异常')}")
                return {
                    'data': [
                        {'id': 'ep_20251217_i18v', 'name': 'DeepSeek-V3'},
                        {'id': 'ep_20250908_1pgk', 'name': 'DeepSeek-V3.1'},
                        {'id': 'ep_20251217_hr5x', 'name': 'DeepSeek-R1'},
                    ]
                }
            return data
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            # 返回备选的模型列表
            return {
                'data': [
                    {'id': 'ep_20251217_i18v', 'name': 'DeepSeek-V3'},
                    {'id': 'ep_20250908_1pgk', 'name': 'DeepSeek-V3.1'},
                    {'id': 'ep_20251217_hr5x', 'name': 'DeepSeek-R1'},
                ]
            }
    
    def chat_completions(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 0.6,
        max_tokens: Optional[int] = None,
        top_p: float = 0.9,
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用对话模型
        
        Args:
            model: 模型ID (推理接入点ID)
            messages: 消息列表，格式如下：
                [
                    {"role": "system", "content": "..."},
                    {"role": "user", "content": "..."},
                    {"role": "assistant", "content": "..."}
                ]
            temperature: 温度参数 (0.0-2.0)
            max_tokens: 最大生成tokens
            top_p: Top-P采样参数
            tools: 工具列表 (用于函数调用)
            stream: 是否流式输出
            **kwargs: 其他参数
        
        Returns:
            Dict: API响应
        
        Example:
            >>> client = ZKHAPIClient(api_key="your_api_key")
            >>> response = client.chat_completions(
            ...     model="ep-20250429102651-hd5dd",
            ...     messages=[{"role": "user", "content": "你好"}],
            ...     temperature=0.6
            ... )
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "stream": stream,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if tools:
            payload["tools"] = tools
        
        payload.update(kwargs)
        
        try:
            response = self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"调用聊天API失败: {e}")
            raise
    
    def chat_completions_stream(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 0.6,
        **kwargs
    ):
        """
        流式调用对话模型
        
        Args:
            model: 模型ID
            messages: 消息列表
            temperature: 温度参数
            **kwargs: 其他参数
        
        Yields:
            str: 流式返回的内容片段
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        payload.update(kwargs)
        
        try:
            response = self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                stream=True
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    if isinstance(line, bytes):
                        line = line.decode('utf-8')
                    
                    if line.startswith('data: '):
                        data = line[6:]  # 移除 'data: ' 前缀
                        if data == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data)
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    yield delta['content']
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"流式调用API失败: {e}")
            raise
    
    def upload_file(self, file_path: str, purpose: str = "file-extract") -> Dict[str, Any]:
        """
        上传文件（用于文档处理）
        
        Args:
            file_path: 本地文件路径
            purpose: 文件用途，默认为 "file-extract"
        
        Returns:
            Dict: 上传结果，包含文件ID
        
        Example:
            >>> file_result = client.upload_file("document.pdf")
            >>> file_id = file_result['id']
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        try:
            with open(file_path, 'rb') as f:
                files = {
                    'file': (os.path.basename(file_path), f),
                    'purpose': (None, purpose)
                }
                # 上传文件时不使用JSON头
                response = requests.post(
                    f"{self.base_url}/v1/files",
                    files=files,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"上传文件失败: {e}")
            raise
    
    def list_files(self, limit: int = 20, purpose: str = "file-extract") -> List[Dict[str, Any]]:
        """
        查询已上传的文件列表
        
        Args:
            limit: 返回数量限制，默认20
            purpose: 文件用途，默认为 "file-extract"
        
        Returns:
            List[Dict]: 文件列表
        """
        try:
            response = self.session.get(
                f"{self.base_url}/v1/files",
                params={"limit": limit, "purpose": purpose}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"查询文件列表失败: {e}")
            raise
    
    def delete_file(self, file_id: str) -> Dict[str, Any]:
        """
        删除已上传的文件
        
        Args:
            file_id: 文件ID
        
        Returns:
            Dict: 删除结果
        """
        try:
            response = self.session.delete(f"{self.base_url}/v1/files/{file_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            raise
    
    def embeddings(
        self,
        model: str,
        input_text: str
    ) -> Dict[str, Any]:
        """
        获取文本嵌入向量
        
        Args:
            model: 嵌入模型ID
            input_text: 输入文本
        
        Returns:
            Dict: 嵌入结果
        """
        payload = {
            "model": model,
            "input": input_text
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/v1/embeddings",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取嵌入向量失败: {e}")
            raise


def create_image_message_content(
    text: str,
    image_urls: Optional[List[str]] = None,
    image_base64: Optional[str] = None,
    detail: str = "auto"
) -> List[Dict[str, Any]]:
    """
    创建包含文本和图像的消息内容
    
    Args:
        text: 文本内容
        image_urls: 图像URL列表
        image_base64: Base64编码的图像数据
        detail: 图像细节级别 ("low", "high", "auto")
    
    Returns:
        List[Dict]: 消息内容列表
    
    Example:
        >>> content = create_image_message_content(
        ...     text="这是什么？",
        ...     image_urls=["https://example.com/image.jpg"]
        ... )
    """
    content = []
    
    # 添加图像
    if image_urls:
        for url in image_urls:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": url,
                    "detail": detail
                }
            })
    
    if image_base64:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{image_base64}",
                "detail": detail
            }
        })
    
    # 添加文本
    content.append({
        "type": "text",
        "text": text
    })
    
    return content


def create_file_message_content(
    text: str,
    file_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    创建包含文本和文件ID的消息内容（用于文档处理）
    
    Args:
        text: 问询文本
        file_ids: 文件ID列表
    
    Returns:
        List[Dict]: 消息内容列表
    
    Example:
        >>> content = create_file_message_content(
        ...     text="这份文档讲了什么？",
        ...     file_ids=["file-fe-xxx1", "file-fe-xxx2"]
        ... )
    """
    # 构建system消息中的文件引用
    file_references = ",".join([f"fileid://{fid}" for fid in file_ids])
    
    return [
        {
            "role": "system",
            "content": file_references
        },
        {
            "role": "user",
            "content": text
        }
    ]


# 使用示例和测试代码
if __name__ == "__main__":
    # 初始化客户端
    api_key = os.getenv("ZKH_API_KEY")
    if not api_key:
        print("错误：请设置 ZKH_API_KEY 环境变量")
        exit(1)
    
    client = ZKHAPIClient(api_key=api_key)
    
    # 示例1: 简单文本对话
    print("=== 示例1: 简单文本对话 ===")
    response = client.chat_completions(
        model="ep-20250429102651-hd5dd",
        messages=[
            {"role": "system", "content": "你是一个有帮助的AI助手。"},
            {"role": "user", "content": "你好，介绍一下自己"}
        ],
        temperature=0.6
    )
    print(f"回复: {response['choices'][0]['message']['content']}")
    
    # 示例2: 流式输出
    print("\n=== 示例2: 流式输出 ===")
    print("回复: ", end="", flush=True)
    for chunk in client.chat_completions_stream(
        model="ep-20250429102651-hd5dd",
        messages=[
            {"role": "user", "content": "请写一个简短的故事"}
        ]
    ):
        print(chunk, end="", flush=True)
    print()
    
    # 示例3: 工具调用
    print("\n=== 示例3: 工具调用 ===")
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "获取指定城市的天气",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名称"
                        }
                    },
                    "required": ["city"]
                }
            }
        }
    ]
    
    response = client.chat_completions(
        model="ep-20250429102651-hd5dd",
        messages=[
            {"role": "user", "content": "杭州天气怎么样？"}
        ],
        tools=tools
    )
    print(f"响应: {json.dumps(response, ensure_ascii=False, indent=2)}")
