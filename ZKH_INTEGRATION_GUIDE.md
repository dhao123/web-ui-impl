# 震坤行(ZKH) AI 大模型集成指南

## 概述

本文档介绍如何在 Browser Use WebUI 项目中集成和使用震坤行AI的大模型服务。

## 快速开始

### 1. 获取API密钥

1. 访问 [震坤行AI开发者平台](https://ai-dev.zkh360.com)
2. 注册或登录账户
3. 创建API密钥
4. 获取推理接入点ID（endpoint ID）

### 2. 配置环境变量

编辑 `.env` 文件，添加以下配置：

```env
# 震坤行AI配置
ZKH_API_KEY=your_api_key_here
ZKH_ENDPOINT=https://ai-dev-gateway.zkh360.com/llm
```

或者设置系统环境变量：

```bash
export ZKH_API_KEY="your_api_key_here"
export ZKH_ENDPOINT="https://ai-dev-gateway.zkh360.com/llm"
```

### 3. 使用 Web UI

1. 启动应用：`python webui.py`
2. 打开浏览器访问 `http://127.0.0.1:7788`
3. 在 **Agent Settings** 标签页中：
   - **LLM Provider**: 选择 "震坤行AI"
   - **LLM Model Name**: 输入推理接入点ID（例如：`ep-20250429102651-hd5dd`）
   - **Temperature**: 设置温度（0.0-2.0）
   - **Base URL**（可选）: 默认为官方API端点，可自定义
   - **API Key**（可选）: 如果未设置环境变量，可在此输入

4. 切换到 **Browser Settings** 配置浏览器
5. 在 **Run Agent** 标签页中输入任务并执行

## 集成实现细节

### 架构修改

项目进行了以下修改以支持震坤行：

#### 1. 配置文件 (`src/utils/config.py`)

```python
PROVIDER_DISPLAY_NAMES = {
    ...
    "zkh": "震坤行AI",  # 新增
}

model_names = {
    ...
    "zkh": [
        "ep-20250429102651-hd5dd",  # 推理接入点ID示例
    ],  # 新增
}
```

#### 2. LLM提供商 (`src/utils/llm_provider.py`)

```python
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
        base_url = os.getenv("ZKH_ENDPOINT", "https://ai-dev-gateway.zkh360.com/llm")
    else:
        base_url = kwargs.get("base_url")
    
    return ChatOpenAI(
        model=kwargs.get("model_name", "ep-20250429102651-hd5dd"),
        temperature=kwargs.get("temperature", 0.0),
        base_url=base_url,
        api_key=api_key,
    )
```

#### 3. 专用客户端 (`src/utils/zkh_client.py`)

新增了 `ZKHAPIClient` 类，提供以下功能：

- **聊天对话** (`chat_completions`)
- **流式输出** (`chat_completions_stream`)
- **工具调用** (Function Calling)
- **文件上传和处理** (Qwen-Long)
- **向量嵌入** (`embeddings`)

### API 兼容性

震坤行AI采用 OpenAI 兼容的 API 接口，因此可以直接使用 `ChatOpenAI` 类：

```python
ChatOpenAI(
    model="ep-20250429102651-hd5dd",
    base_url="https://ai-dev-gateway.zkh360.com/llm",
    api_key="your_api_key",
)
```

## 使用示例

### 示例1: 直接使用客户端

```python
from src.utils.zkh_client import ZKHAPIClient

# 初始化客户端
client = ZKHAPIClient(api_key="your_api_key")

# 简单对话
response = client.chat_completions(
    model="ep-20250429102651-hd5dd",
    messages=[
        {"role": "system", "content": "你是一个有帮助的AI助手。"},
        {"role": "user", "content": "你好，介绍一下自己"}
    ],
    temperature=0.6
)

print(response['choices'][0]['message']['content'])
```

### 示例2: 流式输出

```python
for chunk in client.chat_completions_stream(
    model="ep-20250429102651-hd5dd",
    messages=[
        {"role": "user", "content": "请写一个故事"}
    ]
):
    print(chunk, end="", flush=True)
```

### 示例3: 图像输入

```python
from src.utils.zkh_client import create_image_message_content

content = create_image_message_content(
    text="这张图片中有什么？",
    image_urls=["https://example.com/image.jpg"]
)

response = client.chat_completions(
    model="ep-20250429102651-hd5dd",
    messages=[
        {"role": "user", "content": content}
    ]
)
```

### 示例4: 文件处理 (Qwen-Long)

```python
# 上传文件
file_result = client.upload_file("document.pdf")
file_id = file_result['id']

# 基于文件进行对话
response = client.chat_completions(
    model="ep-20250429102651-hd5dd",
    messages=[
        {"role": "system", "content": f"fileid://{file_id}"},
        {"role": "user", "content": "这份文档讲了什么？"}
    ]
)

# 删除文件
client.delete_file(file_id)
```

### 示例5: 工具调用

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取天气信息",
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
```

## API 参考

### ChatOpenAI 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `model` | str | 推理接入点ID |
| `temperature` | float | 温度参数（0.0-2.0），越小越稳定 |
| `base_url` | str | API服务地址，默认为官方端点 |
| `api_key` | str | API密钥 |
| `max_tokens` | int | 最大输出tokens数 |
| `top_p` | float | 核采样参数（0.0-1.0） |

### ZKHAPIClient 方法

#### chat_completions()
调用对话模型进行单轮对话

**参数:**
- `model` (str): 推理接入点ID
- `messages` (List[Dict]): 消息列表
- `temperature` (float): 温度参数
- `max_tokens` (Optional[int]): 最大输出tokens
- `top_p` (float): Top-P采样
- `tools` (Optional[List]): 工具定义（函数调用）
- `stream` (bool): 是否流式输出

**返回:** API响应字典

#### chat_completions_stream()
流式调用对话模型

**参数:** 同 `chat_completions()`

**返回:** 生成器，逐个返回内容片段

#### upload_file()
上传文件用于文档处理

**参数:**
- `file_path` (str): 本地文件路径
- `purpose` (str): 文件用途，默认 "file-extract"

**返回:** 上传结果，包含文件ID

#### list_files()
查询已上传的文件列表

**返回:** 文件列表

#### delete_file()
删除已上传的文件

**参数:**
- `file_id` (str): 文件ID

#### embeddings()
获取文本的向量表示

**参数:**
- `model` (str): 嵌入模型ID
- `input_text` (str): 输入文本

**返回:** 嵌入向量结果

## 高级功能

### 视觉理解

震坤行支持多模态输入，可以处理包含图像的问询：

```python
response = client.chat_completions(
    model="ep-20250429102651-hd5dd",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.jpg",
                        "detail": "high"  # low | auto | high
                    }
                },
                {
                    "type": "text",
                    "text": "这是什么？"
                }
            ]
        }
    ]
)
```

### 文档处理 (Qwen-Long)

支持超长上下文的文档处理，最高可处理1,000万Token：

```python
# 上传多个文档
files = ["doc1.pdf", "doc2.docx", "doc3.txt"]
file_ids = []
for file_path in files:
    result = client.upload_file(file_path)
    file_ids.append(result['id'])

# 基于多个文档进行分析
response = client.chat_completions(
    model="ep-20250429102651-hd5dd",
    messages=[
        {
            "role": "system",
            "content": ",".join([f"fileid://{fid}" for fid in file_ids])
        },
        {
            "role": "user",
            "content": "这些文档的主要内容是什么？"
        }
    ]
)

# 清理文件
for file_id in file_ids:
    client.delete_file(file_id)
```

### 工具链调用

与Browser Agent结合使用，实现自动化的浏览器任务：

```python
# 在 CustomController 中集成ZKH工具
from src.utils.zkh_client import ZKHAPIClient

class CustomController(Controller):
    def __init__(self, zkh_client: ZKHAPIClient = None):
        super().__init__()
        self.zkh_client = zkh_client
        self._register_custom_actions()
    
    def _register_custom_actions(self):
        @self.registry.action("使用AI分析页面内容")
        async def analyze_with_zkh(content: str, analysis_type: str, browser: BrowserContext):
            if not self.zkh_client:
                return ActionResult(error="ZKH客户端未初始化")
            
            response = self.zkh_client.chat_completions(
                model="ep-20250429102651-hd5dd",
                messages=[
                    {
                        "role": "user",
                        "content": f"请分析以下内容（分析类型：{analysis_type}）：\n{content}"
                    }
                ]
            )
            
            return ActionResult(
                extracted_content=response['choices'][0]['message']['content'],
                include_in_memory=True
            )
```

## 故障排除

### 常见问题

**Q1: API密钥验证失败**
```
错误: 💥 震坤行API Key未找到！🔑 请设置 `ZKH_API_KEY` 环境变量或在UI中提供。
```
**解决方案:**
- 确保在 `.env` 中正确设置了 `ZKH_API_KEY`
- 或在Web UI的"Agent Settings"中输入API密钥
- 确保API密钥有效且未过期

**Q2: 连接超时**
```
错误: Connection timeout to https://ai-dev-gateway.zkh360.com/llm
```
**解决方案:**
- 检查网络连接
- 确认 `ZKH_ENDPOINT` URL正确
- 检查防火墙设置

**Q3: 模型ID无效**
```
错误: Model not found: ep-xxx
```
**解决方案:**
- 确认推理接入点ID正确
- 访问平台检查该端点是否已启用
- 检查是否有权限使用该模型

**Q4: 请求超出配额**
```
错误: Rate limit exceeded
```
**解决方案:**
- 检查API使用配额
- 增加等待时间
- 联系震坤行技术支持升级配额

## 性能优化建议

1. **使用合适的温度值**
   - 精确任务：temperature = 0.0-0.3
   - 创意任务：temperature = 0.7-1.0

2. **上下文优化**
   - 只发送必要的消息历史
   - 利用 `max_tokens` 限制输出长度

3. **流式处理**
   - 对于长输出，使用流式API提高响应速度

4. **并发请求**
   ```python
   import asyncio
   
   async def concurrent_requests():
       tasks = [
           asyncio.to_thread(client.chat_completions, **params)
           for params in requests_list
       ]
       results = await asyncio.gather(*tasks)
   ```

## 与Browser Agent集成

完整的集成示例：

```python
from src.agent.browser_use.browser_use_agent import BrowserUseAgent
from src.utils import llm_provider

# 创建ZKH LLM实例
llm = llm_provider.get_llm_model(
    provider="zkh",
    model_name="ep-20250429102651-hd5dd",
    temperature=0.6,
    api_key="your_api_key"  # 或从环境变量自动加载
)

# 创建Agent
agent = BrowserUseAgent(
    task="访问Google并搜索'Python教程'",
    llm=llm,
    browser=browser,
    browser_context=browser_context,
    controller=controller,
    use_vision=True
)

# 运行任务
result = await agent.run(max_steps=100)
```

## 支持的文件格式

文档处理支持以下格式：
- 文本文件：TXT、DOCX、PDF、XLSX、EPUB、MOBI、MD、CSV
- 图片文件：BMP、PNG、JPG/JPEG、GIF（以及PDF扫描件）

**限制说明：**
- 图片文件最大20MB
- 其他格式最大150MB
- 单个账号最多上传10,000个文件
- 总文件大小不超过100GB

## 更新日志

### v1.0 (2025-02-04)
- 初始版本
- 支持基础对话功能
- 集成OpenAI兼容API
- 支持工具调用和文件处理

## 联系支持

- 技术文档：https://ai-dev.zkh360.com/docs
- API问题：support@zkh360.com
- GitHub Issue：在项目中提交Issue

## 许可证

本集成代码遵循项目主许可证。
